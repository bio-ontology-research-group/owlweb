"""
WSGI config for aberowlweb project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""
from configurations.wsgi import get_wsgi_application
import os

os.environ.setdefault("DJANGO_CONFIGURATION", "Production")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aberowlweb.settings")

application = get_wsgi_application()
