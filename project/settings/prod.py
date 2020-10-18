# -*- coding: utf-8 -*-

# MINIMAL CONFIGURATION FOR PRODUCTION ENV

# Create your own prod_local.py
# import * this module there and use it like this:
# python manage.py runserver --settings=project.settings.prod_local

from __future__ import unicode_literals

from .base import *  # noqa


DEBUG = False

# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (('sirex', 'sirexas@gmail.com'), )

# Secret key generator: https://djskgen.herokuapp.com/
# You should set your key as an environ variable
SECRET_KEY = os.environ.get("SECRET_KEY", "35135gsdfg5sd3g5e35e1rg3w5r1g51313")

# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['ubuntu.lt', 'www.ubuntu.lt']

DEFAULT_FROM_EMAIL = 'no-reply@ubuntu.lt'  # 'MyForum <noreply@example.com>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL  # For error notifications

# Email sending timeout
EMAIL_TIMEOUT = 20  # Default is None (infinite)

# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ubuntult',
        'USER': 'ubuntult',
    }
}

# Append the MD5 hash of the file’s content to the filename
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

WSGI_APPLICATION = 'project.wsgi.prod.application'
