from .prod import *  # noqa

ALLOWED_HOSTS = ['demo.ubuntu.lt']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ubuntultdemo',
        'USER': 'ubuntult',
    }
}

WSGI_APPLICATION = 'project.wsgi.demo.application'
