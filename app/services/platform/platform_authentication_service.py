"""
Hela360 Platform Authentication Service
=======================================

Login orchestration for Hela360 Office identities.

Architectural boundaries
------------------------
* Authenticates PlatformUser identities only.
* Never authenticates tenant User identities.
* Carries no tenant or branch scope.
* Requires canonical Hela360 Office authorization before session creation.
* Composes Platform session, JWT, refresh-token and login-attempt services.
* Performs no HTTP request/response handling.
* Never commits or rolls back implicitly.

Transaction ownership remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select

from app.auth.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    InvalidCredentialsError,
    PermissionDeniedError,
    UserNotFoundError,
)
from app.models import (
    PlatformRefreshToken,
    PlatformSession,
    PlatformUser,
)
from app.models.security import (
    TokenRevocationReason,
)
from app.services.platform.platform_authorization_service import (
    PlatformAuthorizationContext,
    PlatformAuthorizationService,
)
from app.services.platform.platform_jwt_service import (
    PlatformJWTService,
)
from app.services.platform.platform_login_attempt_service import (
    PlatformLoginAttemptService,
)
from app.services.platform.platform_refresh_token_service import (
    PlatformRefreshTokenService,
)
from app.services.platform.platform_session_service import (
    PlatformSessionService,
)
from app.services.tenant.auth.password_service import (
    PasswordService,
    password_service,
)


PLATFORM_OFFICE_ACCESS_PERMISSION = (
    "platform.office.access"
)


@dataclass(
    frozen=True,
    slots=True,
)
class PlatformAuthenticationResult:
    """
    Result of one successful Hela360 Office authentication.
    """

    user: PlatformUser
    authorization: PlatformAuthorizationContext
    access_token: str
    refresh_token: str
    session: PlatformSession
    refresh_token_record: PlatformRefreshToken


@dataclass(
    frozen=True,
    slots=True,
)
class PlatformRefreshResult:
    """
    Result of one successful Hela360 Office refresh-token rotation.
    """

    user: PlatformUser
    authorization: PlatformAuthorizationContext
    access_token: str
    refresh_token: str
    session: PlatformSession
    refresh_token_record: PlatformRefreshToken


class PlatformAuthenticationService:
    """
    Authenticate Hela360 Office users.

    All persistence performed through this service is flushed but not
    committed. The caller owns the enclosing transaction.
    """

    def __init__(
        self,
        session,
        *,
        passwords: PasswordService | None = None,
        login_attempts: PlatformLoginAttemptService | None = None,
    ) -> None:
        self.session = session

        self.passwords = (
            passwords
            or password_service
        )

        self.login_attempts = (
            login_attempts
            or PlatformLoginAttemptService(
                session
            )
        )

        self.authorization = (
            PlatformAuthorizationService(
                session
            )
        )

        self.sessions = (
            PlatformSessionService(
                session
            )
        )

        self.refresh_tokens = (
            PlatformRefreshTokenService(
                session
            )
        )

        self.jwt = PlatformJWTService()

    def login(
        self,
        *,
        username_or_email: str,
        password: str,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PlatformAuthenticationResult:
        """
        Authenticate one PlatformUser for Hela360 Office.

        Workflow
        --------
        1. Normalize the submitted identifier.
        2. Enforce identifier/IP throttling.
        3. Resolve a PlatformUser by email or username.
        4. Enforce canonical account throttling.
        5. Verify the password.
        6. Validate active account state.
        7. Upgrade the password hash when required.
        8. Require Hela360 Office authorization.
        9. Create a PlatformSession.
        10. Issue the authoritative platform JWT pair.
        11. Synchronize session lifetime to refresh-token expiry.
        12. Persist refresh-token metadata.
        13. Record successful authentication.
        14. Return the authenticated Platform context.
        """

        identifier = (
            self.login_attempts
            .normalize_identifier(
                username_or_email
            )
        )

        if not identifier:
            raise InvalidCredentialsError()

        if not self.login_attempts.can_attempt(
            identifier=identifier,
            ip_address=ip_address,
        ):
            raise AccountLockedError(
                "Platform authentication temporarily "
                "locked due to repeated failures."
            )

        user = self._resolve_user(
            identifier
        )

        if user is None:
            self.login_attempts.record_failure(
                identifier=identifier,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=(
                    "Unknown account"
                ),
            )

            raise InvalidCredentialsError()

        canonical_identifier = (
            self._canonical_identifier(
                user
            )
        )

        if (
            canonical_identifier
            != identifier
            and not self.login_attempts
            .can_attempt(
                identifier=(
                    canonical_identifier
                ),
                ip_address=ip_address,
            )
        ):
            raise AccountLockedError(
                "Platform authentication temporarily "
                "locked due to repeated failures."
            )

        if not self.passwords.verify_password(
            password,
            user.password_hash,
        ):
            self.login_attempts.record_failure(
                identifier=(
                    canonical_identifier
                ),
                platform_user_id=(
                    str(user.id)
                ),
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=(
                    "Incorrect password"
                ),
            )

            raise InvalidCredentialsError()

        if user.is_active is not True:
            self.login_attempts.record_failure(
                identifier=(
                    canonical_identifier
                ),
                platform_user_id=(
                    str(user.id)
                ),
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=(
                    "Account inactive"
                ),
            )

            raise AccountInactiveError(
                "Platform user is inactive."
            )

        self._upgrade_password_hash_if_required(
            user=user,
            plaintext_password=password,
        )

        try:
            authorization = (
                self.authorization
                .require_permission(
                    str(user.id),
                    PLATFORM_OFFICE_ACCESS_PERMISSION,
                )
            )

        except PermissionDeniedError:
            self.login_attempts.record_failure(
                identifier=(
                    canonical_identifier
                ),
                platform_user_id=(
                    str(user.id)
                ),
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=(
                    "Hela360 Office access denied"
                ),
            )

            raise

        provisional_session_expiry = (
            datetime.now(UTC)
            + timedelta(
                seconds=(
                    self.jwt
                    .refresh_token_expires_in()
                )
            )
        )

        auth_session = (
            self.sessions.create(
                platform_user_id=(
                    str(user.id)
                ),
                expires_at=(
                    provisional_session_expiry
                ),
                device_name=device_name,
                ip_address=ip_address,
                user_agent=user_agent,
                authentication_method=(
                    "password"
                ),
                authentication_level=(
                    "normal"
                ),
            )
        )

        token_pair = (
            self.jwt.issue_token_pair(
                platform_user_id=(
                    str(user.id)
                ),
                permissions=list(
                    authorization.permissions
                ),
                session_id=str(
                    auth_session.id
                ),
            )
        )

        auth_session.expires_at = (
            token_pair.refresh_expires_at
        )

        self.session.flush()

        refresh_record = (
            self.refresh_tokens.create(
                platform_user_id=(
                    str(user.id)
                ),
                platform_session_id=(
                    str(auth_session.id)
                ),
                jwt_id=(
                    token_pair.refresh_jti
                ),
                expires_at=(
                    token_pair
                    .refresh_expires_at
                ),
                ip_address=ip_address,
                user_agent=user_agent,
                device_name=device_name,
            )
        )

        self.login_attempts.record_success(
            identifier=(
                canonical_identifier
            ),
            platform_user_id=(
                str(user.id)
            ),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return PlatformAuthenticationResult(
            user=user,
            authorization=(
                authorization
            ),
            access_token=(
                token_pair.access_token
            ),
            refresh_token=(
                token_pair.refresh_token
            ),
            session=auth_session,
            refresh_token_record=(
                refresh_record
            ),
        )

    def refresh(
        self,
        *,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PlatformRefreshResult:
        """
        Rotate one valid Hela360 Office refresh token.

        Authorization is resolved again from persisted Platform IAM state so
        newly issued access tokens always carry the user's current effective
        permissions.

        Replay of a rotated token revokes the surviving token family and the
        associated PlatformSession.
        """

        payload = (
            self.jwt.decode_refresh_token(
                refresh_token
            )
        )

        jwt_id = self.jwt.token_id(
            payload
        )

        platform_user_id = (
            self.jwt
            .extract_platform_user_id(
                payload
            )
        )

        platform_session_id = (
            self.jwt
            .extract_session_id(
                payload
            )
        )

        current_refresh = (
            self.refresh_tokens
            .get_by_jwt_id(
                jwt_id
            )
        )

        if current_refresh is None:
            raise InvalidCredentialsError(
                "Platform refresh token not found."
            )

        if (
            str(
                current_refresh
                .platform_user_id
            )
            != str(
                platform_user_id
            )
            or str(
                current_refresh
                .platform_session_id
            )
            != str(
                platform_session_id
            )
        ):
            self.refresh_tokens.revoke_family(
                token_family=(
                    current_refresh
                    .token_family
                ),
                reason=(
                    TokenRevocationReason
                    .SECURITY_EVENT
                ),
            )

            compromised_session = (
                self.sessions.get(
                    str(
                        current_refresh
                        .platform_session_id
                    )
                )
            )

            if compromised_session is not None:
                self.sessions.revoke(
                    compromised_session,
                    reason=(
                        TokenRevocationReason
                        .SECURITY_EVENT
                    ),
                )

            raise InvalidCredentialsError(
                "Platform refresh token "
                "authentication context is invalid."
            )

        if current_refresh.is_rotated:
            self.refresh_tokens.handle_reuse(
                current_refresh
            )

            replay_session = (
                self.sessions.get(
                    str(
                        current_refresh
                        .platform_session_id
                    )
                )
            )

            if replay_session is not None:
                self.sessions.revoke(
                    replay_session,
                    reason=(
                        TokenRevocationReason
                        .REUSE_DETECTED
                    ),
                )

            raise InvalidCredentialsError(
                "Platform refresh token "
                "has already been used."
            )

        if not current_refresh.is_active:
            raise InvalidCredentialsError(
                "Platform refresh token "
                "is no longer valid."
            )

        auth_session = (
            self.sessions.get_active(
                str(
                    platform_session_id
                )
            )
        )

        if auth_session is None:
            self.refresh_tokens.revoke(
                current_refresh,
                reason=(
                    TokenRevocationReason
                    .SESSION_EXPIRED
                ),
            )

            raise AccountInactiveError(
                "Platform authentication "
                "session has expired."
            )

        if (
            str(
                auth_session
                .platform_user_id
            )
            != str(
                platform_user_id
            )
        ):
            self.refresh_tokens.revoke_family(
                token_family=(
                    current_refresh
                    .token_family
                ),
                reason=(
                    TokenRevocationReason
                    .SECURITY_EVENT
                ),
            )

            self.sessions.revoke(
                auth_session,
                reason=(
                    TokenRevocationReason
                    .SECURITY_EVENT
                ),
            )

            raise InvalidCredentialsError(
                "Platform authentication "
                "session ownership is invalid."
            )

        user = self.session.get(
            PlatformUser,
            str(
                platform_user_id
            ),
        )

        if user is None:
            self.refresh_tokens.revoke_family(
                token_family=(
                    current_refresh
                    .token_family
                ),
                reason=(
                    TokenRevocationReason
                    .USER_DELETED
                ),
            )

            self.sessions.revoke(
                auth_session,
                reason=(
                    TokenRevocationReason
                    .USER_DELETED
                ),
            )

            raise UserNotFoundError(
                "Platform user not found."
            )

        if user.is_active is not True:
            self.refresh_tokens.revoke_family(
                token_family=(
                    current_refresh
                    .token_family
                ),
                reason=(
                    TokenRevocationReason
                    .ACCOUNT_DISABLED
                ),
            )

            self.sessions.revoke(
                auth_session,
                reason=(
                    TokenRevocationReason
                    .ACCOUNT_DISABLED
                ),
            )

            raise AccountInactiveError(
                "Platform user is inactive."
            )

        try:
            authorization = (
                self.authorization
                .require_permission(
                    str(user.id),
                    PLATFORM_OFFICE_ACCESS_PERMISSION,
                )
            )

        except PermissionDeniedError:
            self.refresh_tokens.revoke_family(
                token_family=(
                    current_refresh
                    .token_family
                ),
                reason=(
                    TokenRevocationReason
                    .ADMIN_REVOKED
                ),
            )

            self.sessions.revoke(
                auth_session,
                reason=(
                    TokenRevocationReason
                    .ADMIN_REVOKED
                ),
            )

            raise

        replacement_refresh_token = (
            self.jwt.issue_refresh_token(
                platform_user_id=(
                    str(user.id)
                ),
                session_id=(
                    str(auth_session.id)
                ),
            )
        )

        replacement_payload = (
            self.jwt.decode_refresh_token(
                replacement_refresh_token
            )
        )

        replacement_jwt_id = (
            self.jwt.token_id(
                replacement_payload
            )
        )

        replacement_expires_at = (
            self.jwt.token_expiry(
                replacement_payload
            )
        )

        replacement_record = (
            self.refresh_tokens.rotate(
                old_token=(
                    current_refresh
                ),
                new_jwt_id=(
                    replacement_jwt_id
                ),
                expires_at=(
                    replacement_expires_at
                ),
                ip_address=ip_address,
                user_agent=user_agent,
                device_name=(
                    current_refresh
                    .device_name
                ),
                device_fingerprint=(
                    current_refresh
                    .device_fingerprint
                ),
            )
        )

        access_token = (
            self.jwt.issue_access_token(
                platform_user_id=(
                    str(user.id)
                ),
                permissions=list(
                    authorization.permissions
                ),
                session_id=(
                    str(auth_session.id)
                ),
            )
        )

        auth_session.expires_at = (
            replacement_expires_at
        )

        self.sessions.touch(
            auth_session,
            ip_address=ip_address,
        )

        self.session.flush()

        return PlatformRefreshResult(
            user=user,
            authorization=(
                authorization
            ),
            access_token=(
                access_token
            ),
            refresh_token=(
                replacement_refresh_token
            ),
            session=auth_session,
            refresh_token_record=(
                replacement_record
            ),
        )

    def _resolve_user(
        self,
        identifier: str,
    ) -> PlatformUser | None:
        """
        Resolve one PlatformUser case-insensitively by email or username.

        Ambiguous cross-field matches are rejected rather than guessed.
        """

        normalized = str(
            identifier or ""
        ).strip().lower()

        users = list(
            self.session.scalars(
                select(PlatformUser)
                .where(
                    or_(
                        func.lower(
                            PlatformUser.email
                        ) == normalized,
                        func.lower(
                            PlatformUser.username
                        ) == normalized,
                    )
                )
                .limit(2)
            ).all()
        )

        if not users:
            return None

        if len(users) > 1:
            return None

        return users[0]

    @staticmethod
    def _canonical_identifier(
        user: PlatformUser,
    ) -> str:
        """
        Return the canonical lockout/audit identifier for a known account.

        Email is used so username/email login variants share one account-level
        failure counter.
        """

        return str(
            user.email
        ).strip().lower()

    def _upgrade_password_hash_if_required(
        self,
        *,
        user: PlatformUser,
        plaintext_password: str,
    ) -> bool:
        """
        Transparently upgrade legacy/outdated password hashes.

        Returns True when the persisted hash changed.
        """

        upgraded_hash = (
            self.passwords
            .upgrade_hash_if_needed(
                plaintext_password,
                user.password_hash,
            )
        )

        if upgraded_hash is None:
            return False

        user.password_hash = (
            upgraded_hash
        )

        self.session.flush()

        return True


__all__ = [
    "PLATFORM_OFFICE_ACCESS_PERMISSION",
    "PlatformAuthenticationResult",
    "PlatformAuthenticationService",
    "PlatformRefreshResult",
]
