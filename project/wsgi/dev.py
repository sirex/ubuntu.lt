import os

os.environ["DJANGO_SETTINGS_MODULE"] = "project.settings.dev"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
