from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from .models import AuthToken


class CookieAuthentication(BaseAuthentication):
    """
    Custom DRF authentication class.
    Reads the auth_token from the HTTP-only cookie instead of Authorization header.

    How it works:
    1. Every request arrives with cookies attached by the browser
    2. We read the 'auth_token' cookie value
    3. We look it up in the AuthToken database table
    4. If found, we return the associated user — DRF sets request.user
    5. If not found or missing, return None (anonymous user)
    """

    def authenticate(self, request):
        cookie_name = getattr(settings, 'AUTH_COOKIE_NAME', 'auth_token')
        token_key = request.COOKIES.get(cookie_name)

        if not token_key:
            return None  # No cookie — anonymous request

        try:
            token = AuthToken.objects.select_related('user').get(key=token_key)
        except AuthToken.DoesNotExist:
            raise AuthenticationFailed('Invalid or expired token.')

        if not token.user.is_active:
            raise AuthenticationFailed('User account is disabled.')

        return (token.user, token)  # (user, auth) tuple that DRF expects

    def authenticate_header(self, request):
        # Tells clients what auth scheme to use (shown in 401 responses)
        return 'Cookie auth_token=<token>'
