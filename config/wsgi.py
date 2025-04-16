"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from dotenv import load_dotenv

# Muat file .env
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Run startup command before application starts
# try:
#     call_command('startup')
# except Exception as e:
#     print(f"Error during startup, 9999999999999999999: {e}")

application = get_wsgi_application()
