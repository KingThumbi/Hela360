"""
Password Service

Centralized password hashing and verification for Hela360.

This service is responsible for all password-related cryptographic
operations and password policy enforcement.

Features
--------
- Argon2 password hashing
- Legacy Werkzeug hash verification
- Automatic hash migration detection
- Configurable enterprise password policy
- Timing-safe verification
- Stateless service

The AuthenticationService is responsible for persisting upgraded
password hashes after successful verification.

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError
from flask import current_app
from werkzeug.security import check_password_hash


# ============================================================================
# Type Aliases
# ============================================================================

PasswordHash = str


# ============================================================================
# Argon2 Configuration
# ============================================================================

_password_hasher = PasswordHasher()


# ============================================================================
# Compiled Password Rules
# ============================================================================

_UPPERCASE_RE = re.compile(r"[A-Z]")
_LOWERCASE_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"\d")
_SPECIAL_RE = re.compile(r"[!@#$%^&*()_\-+=\[\]{};:'\",.<>?/\\|`~]")


# ============================================================================
# Password Policy
# ============================================================================


class PasswordPolicy:
    """
    Enterprise password policy.
    """

    DEFAULT_MIN_LENGTH: Final[int] = 8

    REQUIRE_UPPERCASE: Final[bool] = True
    REQUIRE_LOWERCASE: Final[bool] = True
    REQUIRE_DIGIT: Final[bool] = True
    REQUIRE_SPECIAL: Final[bool] = True


# ============================================================================
# Validation Result
# ============================================================================


@dataclass(slots=True, frozen=True)
class PasswordValidationResult:
    """
    Result returned after validating a password.
    """

    valid: bool
    errors: list[str]


# ============================================================================
# Password Service
# ============================================================================


class PasswordService:
    """
    Stateless enterprise password service.
    """

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def minimum_length(self) -> int:
        """
        Minimum password length.
        """

        return current_app.config.get(
            "PASSWORD_MIN_LENGTH",
            PasswordPolicy.DEFAULT_MIN_LENGTH,
        )

    # ------------------------------------------------------------------
    # Hashing
    # ------------------------------------------------------------------

    def hash_password(
        self,
        password: str,
    ) -> PasswordHash:
        """
        Hash a plaintext password using Argon2.
        """

        return _password_hasher.hash(password)

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify_password(
        self,
        password: str,
        password_hash: PasswordHash,
    ) -> bool:
        """
        Verify a password against either an Argon2 hash or a legacy
        Werkzeug hash.
        """

        if not password_hash:
            return False

        if password_hash.startswith("$argon2"):

            try:
                return _password_hasher.verify(
                    password_hash,
                    password,
                )

            except (VerifyMismatchError, InvalidHash):
                return False

        return check_password_hash(
            password_hash,
            password,
        )

    # ------------------------------------------------------------------
    # Hash Upgrade
    # ------------------------------------------------------------------

    def needs_rehash(
        self,
        password_hash: PasswordHash,
    ) -> bool:
        """
        Determine whether a stored password hash should be upgraded.
        """

        if not password_hash:
            return True

        if not password_hash.startswith("$argon2"):
            return True

        try:
            return _password_hasher.check_needs_rehash(password_hash)

        except InvalidHash:
            return True

    def upgrade_hash_if_needed(
        self,
        password: str,
        existing_hash: PasswordHash,
    ) -> PasswordHash | None:
        """
        Upgrade a password hash if required.

        Returns
        -------
        PasswordHash
            Newly generated Argon2 hash.

        None
            Existing hash is already current or verification failed.
        """

        if not self.verify_password(
            password,
            existing_hash,
        ):
            return None

        if not self.needs_rehash(existing_hash):
            return None

        return self.hash_password(password)

    # ------------------------------------------------------------------
    # Password Policy
    # ------------------------------------------------------------------

    def validate_password(
        self,
        password: str,
    ) -> PasswordValidationResult:
        """
        Validate a password against the enterprise password policy.
        """

        errors: list[str] = []

        if len(password) < self.minimum_length():
            errors.append(
                f"Password must contain at least "
                f"{self.minimum_length()} characters."
            )

        if (
            PasswordPolicy.REQUIRE_UPPERCASE
            and not _UPPERCASE_RE.search(password)
        ):
            errors.append(
                "Password must contain an uppercase letter."
            )

        if (
            PasswordPolicy.REQUIRE_LOWERCASE
            and not _LOWERCASE_RE.search(password)
        ):
            errors.append(
                "Password must contain a lowercase letter."
            )

        if (
            PasswordPolicy.REQUIRE_DIGIT
            and not _DIGIT_RE.search(password)
        ):
            errors.append(
                "Password must contain a number."
            )

        if (
            PasswordPolicy.REQUIRE_SPECIAL
            and not _SPECIAL_RE.search(password)
        ):
            errors.append(
                "Password must contain a special character."
            )

        return PasswordValidationResult(
            valid=not errors,
            errors=errors,
        )

    def is_valid_password(
        self,
        password: str,
    ) -> bool:
        """
        Return True if the password satisfies the enterprise password
        policy.
        """

        return self.validate_password(password).valid

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def mask_password(
        password: str | None,
    ) -> str:
        """
        Return a masked password suitable for logging.

        Passwords themselves must never be logged.
        """

        if not password:
            return ""

        return "*" * len(password)


# ============================================================================
# Singleton
# ============================================================================

password_service = PasswordService()


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "PasswordHash",
    "PasswordPolicy",
    "PasswordValidationResult",
    "PasswordService",
    "password_service",
]