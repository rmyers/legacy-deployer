
import os

from cannula.conf import *


DEBUG = config.getboolean('django', 'debug')
TEMPLATE_DEBUG = DEBUG

ADMINS = config.items('djangoadmins')

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': config.get('database', 'engine'), 
        'NAME': config.get('database', 'name'),                      # Or path to database file if using sqlite3.
        'USER': config.get('database', 'user'),                      # Not used with sqlite3.
        'PASSWORD': config.get('database', 'password'),                  # Not used with sqlite3.
        'HOST': config.get('database', 'host'),                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': config.get('database', 'port'),                      # Set to empty string for default. Not used with sqlite3.
        'TEST_NAME': config.get('database', 'testname'),
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = config.get('django', 'time_zone')

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = config.get('django', 'language_code')

SITE_ID = config.getint('django', 'site_id')

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = config.getboolean('django', 'use_i18n')

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = config.getboolean('django', 'use_l10n')

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"

MEDIA_ROOT = os.path.join(CANNULA_MODULE_DIR, 'static')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = config.get('django', 'media_url')

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = config.get('django', 'admin_media_prefix')

# Make this unique, and don't share it with anybody.
SECRET_KEY = config.get('django', 'secret_key')

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'cannula.urls'

TEMPLATE_DIRS = [
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    config.get('cannula', 'template_dir')
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    #'django.contrib.messages',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'cannula',
)

AUTHENTICATION_BACKENDS = ['cannula.auth.CannulaBackend']