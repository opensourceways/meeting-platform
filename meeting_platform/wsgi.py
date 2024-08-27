"""
WSGI config for community_meetings project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meeting_platform.settings.prod')

application = get_wsgi_application()
