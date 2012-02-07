# Django settings file for a project based on the playdoh template.

from funfactory.settings_base import *

import os

from django.utils.functional import lazy

# Make file paths relative to settings.
#ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
#path = lambda *a: os.path.join(ROOT, *a)

#ROOT_PACKAGE = os.path.basename(ROOT)

# Is this a dev instance?
#DEV = False

#DEBUG = False
#TEMPLATE_DEBUG = DEBUG

#ADMINS = ()
#MANAGERS = ADMINS
SEND_EMAIL_FROM = 'Mozilla Sheriff Duty <sheriff@mozilla.com>'

DATABASES = {}  # See settings/local.py-dist


## Internationalization.

USE_I18N = False
USE_L10N = True

SECRET_KEY = 'change me in settings/local.py'

LOG_LEVEL = logging.INFO
SYSLOG_TAG = "sheriffs"

TEMPLATE_CONTEXT_PROCESSORS += (
    'cal.context_processors.formatters',
    'cal.context_processors.active_tab',
)


# Bundles is a dictionary of two dictionaries, css and js, which list css files
# and js files that can be bundled together by the minify app.
MINIFY_BUNDLES = {
    'css': {
        'common_css': (
            'css/common.css',
            'css/notifications.css',
            'css/cal/cal.css',
        ),
        'roster.index': (
          'css/roster/index.css',
        ),
        'roster.api_documentation': (
          'css/roster/api_documentation.css',
        ),
        'jquery_ui.datepicker': (
            'css/jquery_ui/pepper-grinder/jquery-ui-1.8.14.datepicker.css',
        ),
    },
    'js': {
        'core': (
            'js/libs/jquery-1.6.2.min.js',
            'js/notifications.js',
            'js/calendar.js',
            'js/common.js',
        ),
        'roster.initialize': (
            'js/roster/initialize.js',
        ),
        'roster.insert': (
            'js/roster/insert.js',
        ),
        'jquery_ui.datepicker': (
            'js/libs/jquery-ui-1.8.14.datepicker.min.js',
            'js/form-datepickers.js',
        ),
    }
}


## Middlewares, apps, URL configs.

#MIDDLEWARE_CLASSES = (
#    #'commons.middleware.LocaleURLMiddleware',
#    'django.middleware.common.CommonMiddleware',
#    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.messages.middleware.MessageMiddleware',
#    #'session_csrf.CsrfMiddleware',
#    'commonware.middleware.FrameOptionsHeader',
#    'commonware.middleware.HidePasswordOnException',
#)
MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
MIDDLEWARE_CLASSES.remove('funfactory.middleware.LocaleURLMiddleware')
MIDDLEWARE_CLASSES.append('commonware.middleware.HidePasswordOnException')


AUTH_PROFILE_MODULE = 'users.UserProfile'


INSTALLED_APPS += (
#    # Local apps
#    'commons',  # Content common to most playdoh-based apps.
#    'jingo_minify',
#    'tower',  # for ./manage.py extract (L10n)

#    # We need this so the jsi18n view will pick up our locale directory.
#    ROOT_PACKAGE,

#    # Third-party apps
#    'commonware.response.cookies',
#    #'djcelery',
#    'django_nose',

    # Django contrib apps
#    'django.contrib.auth',
#    'django_sha2',  # Load after auth to monkey-patch it.

#    'django.contrib.contenttypes',
#    'django.contrib.sessions',
#    # 'django.contrib.sites',
#    # 'django.contrib.messages',
#    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
#    # Uncomment the next line to enable admin documentation:
#    # 'django.contrib.admindocs',

#    # L10n
#    'product_details',

    # sheriffs specific
    'users',
    'cal',
    'roster',
    'vcal',

    # vendor-local
    'uuidfield',

)


# Path to Java. Used for compress_assets.
JAVA_BIN = '/usr/bin/java'

## Auth
PWD_ALGORITHM = 'bcrypt'
HMAC_KEYS = {  # for bcrypt only
    '2011-07-08': 'foobaring',
}

## Misc

LOGIN_URL = '/users/login/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'

DEFAULT_DATE_FORMAT = '%A, %B %d, %Y'
EMAIL_SIGNATURE = """Mozilla Sheriff Duty
https://sheriffs.mozilla.org
"""


# If you don't have a MAILINGLIST_EMAIL email address all emails will instead
# be sent to all active and future sheriffs
#MAILINGLIST_EMAIL = 'sheriffs@mozilla.com'

## Sessioning
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_AGE = 365 * (24 * 3600)   # default was 14, changed to 365 days


## Memcache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'sheriffs',
    }
}


try:
    ## LDAP
    import ldap

    AUTHENTICATION_BACKENDS = (
       'users.email_auth_backend.EmailOrUsernameModelBackend',
       'users.auth.backends.MozillaLDAPBackend',
       'django.contrib.auth.backends.ModelBackend',
    )

    # these must be set in settings/local.py!
    AUTH_LDAP_SERVER_URI = ''
    AUTH_LDAP_BIND_DN = ''
    AUTH_LDAP_BIND_PASSWORD = ''

    AUTH_LDAP_START_TLS = True
    AUTH_LDAP_USER_ATTR_MAP = {
      "first_name": "givenName",
      "last_name": "sn",
      "email": "mail",
    }
    from django_auth_ldap.config import LDAPSearch
    AUTH_LDAP_USER_SEARCH = LDAPSearch(
      "dc=mozilla",
      ldap.SCOPE_SUBTREE,
      "mail=%(user)s"
    )

except ImportError:
    AUTHENTICATION_BACKENDS = (
       'users.email_auth_backend.EmailOrUsernameModelBackend',
       'django.contrib.auth.backends.ModelBackend',
    )
