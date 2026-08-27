from app.auth.jwt import get_current_identity
from app.auth.exceptions import AuthenticationError


def current_identity():
    """
    Return the authenticated identity.

    The request is expected to have already passed the authentication
    and authorization decorators.
    """

    identity = get_current_identity()

    if identity is None:
        raise AuthenticationError(
            "Authenticated identity is unavailable."
        )

    return identity