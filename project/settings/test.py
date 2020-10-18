# -*- coding: utf-8 -*-

# THIS IS FOR DEVELOPMENT ENVIRONMENT
# DO NOT USE IT IN PRODUCTION

# This is used to test settings and urls from example directory
# with `./runtests.py example`

from __future__ import unicode_literals

from .base import *  # noqa

SECRET_KEY = "TEST"

INSTALLED_APPS.extend([
    'spirit.core.tests',
])

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': '127.0.0.1',
        'NAME': 'ubuntult',
        'USER': 'postgres',
        'PASSWORD': 'secret',
    }
}

CACHES.update({
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'st_rate_limit': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'spirit_rl_cache',
        'TIMEOUT': None
    }
})

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

TEMPLATES[0]['OPTIONS']['debug'] = True

MEDIA_ROOT = os.path.join(BASE_DIR, 'media_test')

STATIC_ROOT = os.path.join(BASE_DIR, 'static_test')

ST_TOPIC_PRIVATE_CATEGORY_PK = 1
ST_EXTENDED_FONT = True
ST_RATELIMIT_CACHE = 'st_rate_limit'
ST_UPLOAD_FILE_ENABLED = bool(int(os.getenv('ST_UPLOAD_FILE_ENABLED', True)))
ST_ORDERED_CATEGORIES = True
ST_TASK_MANAGER = os.getenv('ST_TASK_MANAGER', None)
HUEY = {
    'name': 'test',
    'immediate': True
}
CELERY_ALWAYS_EAGER = True
CELERY_TASK_ALWAYS_EAGER = True

HAYSTACK_CONNECTIONS['default']['STORAGE'] = 'ram'
HAYSTACK_LIMIT_TO_REGISTERED_MODELS = False

LOGGING['loggers']['celery']['level'] = 'ERROR'
LOGGING['loggers']['huey']['level'] = 'ERROR'
