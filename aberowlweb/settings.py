import os
import sys
from configurations import Configuration
from kombu import Queue, Exchange
from django.contrib import messages

import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rel(*x):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)


env = environ.Env()

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

sys.path.insert(0, rel('apps'))


class BaseConfiguration(Configuration):

    # SECURITY WARNING: keep the secret key used in production secret!
    # SECRET_KEY = 'm^a2@&q12j-t1$*sf+@5#mqbd3b6inp)w)y&)sgalm0g*)^)&q'
    SECRET_KEY = env('DJANGO_SECRET_KEY', default='m^a2@&q12j-t1$*sf+@5#mqbd3b6inp)w)y&)sgalm0g*)^)&q')

    DEBUG = env.bool('DJANGO_DEBUG', True)

    ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=['localhost', '127.0.0.1'])

    ADMINS = [
        ('Maxat Kulmanov', 'coolmaksat@gmail.com'),
    ]

    DJANGO_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.sites',
        'django.forms',
    ]

    THIRD_PARTY_APPS = [
        'crispy_forms',
        'crispy_bootstrap5',
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'rest_framework',
        'rest_framework_swagger',
        'widget_tweaks',
        'debug_toolbar',
    ]

    LOCAL_APPS = [
        'accounts',
        'aberowl',
    ]

    INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        ],
        'URL_FORMAT_OVERRIDE': 'drf_fromat'
    }

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'aberowl.dl_query_logger.DLQueryLogger',
        'aberowl.cors_middleware.CorsMiddleware'
    ]

    INTERNAL_IPS = [
        # ...
        "127.0.0.1",
        # ...
    ]
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    }

    ROOT_URLCONF = 'aberowlweb.urls'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [rel('templates'), ],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.template.context_processors.i18n",
                    "django.template.context_processors.media",
                    "django.template.context_processors.static",
                    "django.template.context_processors.tz",
                    "django.contrib.messages.context_processors.messages",
                ]
            },
        },
    ]

    AUTHENTICATION_BACKENDS = [
        # Needed to login by username in Django admin, regardless of `allauth`
        'django.contrib.auth.backends.ModelBackend',
        # `allauth` specific authentication methods, such as login by e-mail
        'allauth.account.auth_backends.AuthenticationBackend',
    ]

    WSGI_APPLICATION = 'aberowlweb.wsgi.application'

    # Database
    # https://docs.djangoproject.com/en/1.11/ref/settings/#databases

    DATABASES = {
        'default': env.db("DATABASE_URL",
                          default='postgres://owl:owl@127.0.0.1:5432/owl', )
    }
    DATABASES["default"]["ATOMIC_REQUESTS"] = True
    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
    # Memcached
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',  # Adjust the Redis server location as needed
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }

    SESSION_ENGINE = "django.contrib.sessions.backends.cache"

    # Password validation
    # https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'console': {
                'format': '%(name)-12s %(levelname)-2s %(message)s'
            },
            'file': {
                'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
            }
        },
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': env('LOGS_PATH', default='/tmp/aberowl.log'),
                'formatter': 'file'
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'console'
            }
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'aberowlweb': {
                'handlers': ['file', 'console'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'aberowl': {
                'handlers': ['file', 'console'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'account': {
                'handlers': ['file', 'console'],
                'level': 'DEBUG',
                'propagate': True,
            }
        },
    }

    # Internationalization
    # https://docs.djangoproject.com/en/1.11/topics/i18n/

    LANGUAGE_CODE = 'en-us'

    TIME_ZONE = 'UTC'

    USE_I18N = True

    USE_L10N = True

    USE_TZ = True

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/1.11/howto/static-files/

    STATIC_URL = '/static/'
    STATIC_ROOT = 'public/'
    MEDIA_ROOT = 'media/'
    MEDIA_URL = '/media/'

    # User profile module
    AUTH_PROFILE_MODULE = 'accounts.models.UserProfile'
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_AUTHENTICATION_METHOD = "username_email"
    ACCOUNT_EMAIL_VERIFICATION = "none"
    ACCOUNT_PRESERVE_USERNAME_CASING = "False"
    # https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
    FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

    # http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
    CRISPY_TEMPLATE_PACK = "bootstrap5"
    CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

    STATICFILES_DIRS = (
        rel('static'),)

    SITE_ID = 1
    SITE_DOMAIN = 'localhost:8000'
    SERVER_EMAIL = 'info@aber-owl.net'

    # Celery configuration
    RABBIT_HOST = 'localhost'
    RABBIT_PORT = 5672

    CELERY_BROKER_URL = 'redis://localhost:6379/0'

    CELERY_RESULT_BACKEND = 'rpc://'
    CELERY_WORKER_CONCURRENCY = 24
    CELERY_BROKER_POOL_LIMIT = 100
    CELERY_BROKER_CONNECTION_TIMEOUT = 10

    # configure queues, currently we have only one
    CELERY_DEFAULT_QUEUE = 'default'
    CELERY_QUEUES = (
        Queue('default', Exchange('default'), routing_key='default'),
    )

    # Sensible settings for celery
    CELERY_ALWAYS_EAGER = False
    CELERY_ACKS_LATE = True
    CELERY_TASK_PUBLISH_RETRY = True
    CELERY_DISABLE_RATE_LIMITS = False

    # By default we will ignore result
    # If you want to see results and try out tasks interactively, change it to False
    # Or change this setting on tasks level
    CELERY_IGNORE_RESULT = True
    CELERY_SEND_TASK_ERROR_EMAILS = False
    CELERY_TASK_RESULT_EXPIRES = 600

    # AberOWL setttings
    ABEROWL_API_URL = 'http://localhost:8080/api/'
    ABEROWL_SERVER_URL = 'http://localhost:8000/'

    ABEROWL_API_WORKERS = [
        'http://localhost:8080/api/']

    FILE_UPLOAD_HANDLERS = [
        # 'django.core.files.uploadhandler.MemoryFileUploadHandler',
        'django.core.files.uploadhandler.TemporaryFileUploadHandler',
    ]

    RECAPTCHA_PRIVATE_KEY = '6LefajoUAAAAAEiswDUvk1quNKpTJCg49gwrLXpb'
    RECAPTCHA_PUBLIC_KEY = '6LefajoUAAAAAOAWkZnaz-M2lgJOIR9OF5sylXmm'
    # ACCOUNT_SIGNUP_FORM_CLASS = 'accounts.forms.SignupForm'
    # ACCOUNT_FORMS = {
    #     'login': 'accounts.forms.CaptchaLoginForm',
    #     'signup': 'accounts.forms.CaptchaSignupForm'}

    MESSAGE_TAGS = {
        messages.INFO: 'list-group-item-info',
        messages.DEBUG: 'list-group-item-info',
        messages.SUCCESS: 'list-group-item-success',
        messages.WARNING: 'list-group-item-warning',
        messages.ERROR: 'list-group-item-danger',
    }

    ELASTIC_SEARCH_URL = env('ELASTIC_SEARCH_URL', default='http://localhost:9100/')
    ELASTIC_SEARCH_USERNAME = env('ELASTIC_SEARCH_USERNAME', default='elastic')
    ELASTIC_SEARCH_PASSWORD = env('ELASTIC_SEARCH_PASSWORD', default='test123')
    ELASTIC_ONTOLOGY_INDEX_NAME = env('ELASTIC_ONTOLOGY_INDEX_NAME', default='aberowl_ontology')
    ELASTIC_CLASS_INDEX_NAME = env('ELASTIC_CLASS_INDEX_NAME', default='aberowl_owlclass')

    DLQUERY_LOGS_FOLDER = 'dl'


class Development(BaseConfiguration):
    pass


class Production(BaseConfiguration):
    DEBUG = env.bool('DJANGO_DEBUG', True)

    SITE_DOMAIN = 'aber-owl.net'
    ABEROWL_API_URL = 'http://10.254.145.20:8080/api/'  # TODO: update to LB ip
    ABEROWL_API_WORKERS = [
        'http://10.254.145.20:8080/api/']
    ABEROWL_SERVER_URL = 'http://10.254.145.20/'
    DLQUERY_LOGS_FOLDER = 'dl'
    # SESSION_COOKIE_SECURE=True
    # SESSION_COOKIE_HTTPONLY=True
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')


class ProductionCelery(BaseConfiguration):
    DEBUG = env.bool('DJANGO_DEBUG', True)
    SITE_DOMAIN = 'aber-owl.net'
    ABEROWL_API_URL = 'http://10.254.145.20:8080/api/'
    ABEROWL_API_WORKERS = [
        'http://10.254.145.20:8080/api/']
    ABEROWL_SERVER_URL = 'http://10.254.145.20/'


class TestConfiguration(BaseConfiguration):
    DATABASES = {
        'default': env.db("TEST_DATABASE_URL",
                          default='postgres://owl:owl@127.0.0.1:5432/owl', )
    }
    DATABASES["default"]["ATOMIC_REQUESTS"] = True
