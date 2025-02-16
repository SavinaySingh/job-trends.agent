"""
ASGI config for job_trends_agent project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

# to handle asynchronous communication between the server and the application
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "job_trends_agent.settings")

application = get_asgi_application()
