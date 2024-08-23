import logging
import hashlib

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header

logger = logging.getLogger('log')


class BasicAuthentication(BaseAuthentication):
    """
    HTTP Basic authentication against username/password.
    """
    www_authenticate_realm = 'api'

    def authenticate(self, request):
        """
        Returns a `User` if a correct username and password have been supplied
        using HTTP Basic authentication.  Otherwise returns `None`.
        """
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'basic':
            return None

        if len(auth) == 1:
            msg = _('Invalid basic header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid basic header. Credentials string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        if auth[1] != hashlib.md5(settings.QUERY_TOKEN.encode()).hexdigest():
            msg = _('Invalid token')
            raise exceptions.AuthenticationFailed(msg)

        return True

    def authenticate_header(self, request):
        return 'Basic realm="%s"' % self.www_authenticate_realm
