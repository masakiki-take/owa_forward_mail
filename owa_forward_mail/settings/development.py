from .base import *  # NOQA

SECRET_KEY = 'dummy'
TASK_EXE_AUTH_KEY = 'dummy'
PERSONAL_CRYPTO_KEY = 'WlAzb2t0VWViU1ZlSnhuMXo2VE0yTzh5Z3pQV096TDg='  # 32byte to Base64
EMAIL_AUTH_CRYPTO_KEY = 'bDVYUXlDenNVMjEzYnlvV1J2U2NqdzAyNWwzT0NCNXc='  # 32byte to Base64

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'owa_db',
        'USER': 'owa_user',
        'PASSWORD': 'owa_password',
        'HOST': '127.0.0.1',
        'POST': '5432'
    }
}

DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = './'
