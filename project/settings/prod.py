# -*- coding: utf-8 -*-

# MINIMAL CONFIGURATION FOR PRODUCTION ENV

# Create your own prod_local.py
# import * this module there and use it like this:
# python manage.py runserver --settings=project.settings.prod_local

from __future__ import unicode_literals

from .base import *


DEBUG = False

# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (('sirex', 'sirexas@gmail.com'), )

# Secret key generator: https://djskgen.herokuapp.com/
# You should set your key as an environ variable
SECRET_KEY = os.environ.get("SECRET_KEY", "35135gsdfg5sd3g5e35e1rg3w5r1g51313")

# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['demo.ubuntu.lt', ]

DEFAULT_FROM_EMAIL = 'sirexas@gmail.com'  # 'MyForum <noreply@example.com>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL  # For error notifications

# Extend the Spirit installed apps
# Check out the .base.py file for more examples
INSTALLED_APPS.extend([
    # 'my_app1',
])

# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ubuntult',
        'USER': 'ubuntult',
    }
}

# These are all the languages Spirit provides.
# https://www.transifex.com/projects/p/spirit/
gettext_noop = lambda s: s
LANGUAGES = [
    ('lt', gettext_noop('Lithuanian')),
    ('en', gettext_noop('English')),
]

# Default language
LANGUAGE_CODE = 'lt'

# Keep templates in memory
del TEMPLATES[0]['APP_DIRS']
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
]

# Append the MD5 hash of the file’s content to the filename
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
