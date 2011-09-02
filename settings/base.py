# Django settings file for a project based on the playdoh template.

import os

from django.utils.functional import lazy

# Make file paths relative to settings.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
path = lambda *a: os.path.join(ROOT, *a)

ROOT_PACKAGE = os.path.basename(ROOT)

# Is this a dev instance?
DEV = False

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = ()
MANAGERS = ADMINS
SEND_EMAIL_FROM = 'Mozilla Sheriff Duty <sheriff@mozilla.com>'

DATABASES = {}  # See settings_local.

# Site ID is used by Django's Sites framework.
SITE_ID = 1


## Internationalization.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Gettext text domain
TEXT_DOMAIN = 'messages'
STANDALONE_DOMAINS = [TEXT_DOMAIN, 'javascript']
TOWER_KEYWORDS = {'_lazy': None}
TOWER_ADD_HEADERS = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-US'

## Accepted locales

# On dev instances, the list of accepted locales defaults to the contents of
# the `locale` directory.  A localizer can add their locale in the l10n
# repository (copy of which is checked out into `locale`) in order to start
# testing the localization on the dev server.
try:
    DEV_LANGUAGES = [
        loc.replace('_', '-') for loc in os.listdir(path('locale'))
        if os.path.isdir(path('locale', loc)) and loc != 'templates'
    ]
except OSError:
    DEV_LANGUAGES = ('en-US',)

# On stage/prod, the list of accepted locales is manually maintained.  Only
# locales whose localizers have signed off on their work should be listed here.
PROD_LANGUAGES = (
    'en-US',
)

def lazy_lang_url_map():
    from django.conf import settings
    langs = settings.DEV_LANGUAGES if settings.DEV else settings.PROD_LANGUAGES
    return dict([(i.lower(), i) for i in langs])

LANGUAGE_URL_MAP = lazy(lazy_lang_url_map, dict)()

# Override Django's built-in with our native names
def lazy_langs():
    from django.conf import settings
    from product_details import product_details
    langs = DEV_LANGUAGES if settings.DEV else PROD_LANGUAGES
    return dict([(lang.lower(), product_details.languages[lang]['native'])
                 for lang in langs])

# Where to store product details etc.
## Commented out temporarily PROD_DETAILS_DIR = path('lib/product_details_json')

LANGUAGES = lazy(lazy_langs, dict)()

# Paths that don't require a locale code in the URL.
SUPPORTED_NONLOCALES = ['media']


## Media and templates.

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin-media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '1iz#v0m55@h26^m6hxk3a7at*h$qj_2a$juu1#nv50548j(x1v'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.csrf',
    #'session_csrf.context_processor',

    'django.contrib.messages.context_processors.messages',

    'commons.context_processors.i18n',
    'jingo_minify.helpers.build_ids',
    'cal.context_processors.formatters',
    'cal.context_processors.active_tab',
)

TEMPLATE_DIRS = (
    path('templates'),
)

def JINJA_CONFIG():
    import jinja2
    from django.conf import settings
#    from caching.base import cache
    config = {'extensions': [# XXX: needed even though we don't do I18N :(
                             'tower.template.i18n',

                             'jinja2.ext.do',
                             'jinja2.ext.with_',
                             'jinja2.ext.loopcontrols'],
              'finalize': lambda x: x if x is not None else ''}
#    if 'memcached' in cache.scheme and not settings.DEBUG:
        # We're passing the _cache object directly to jinja because
        # Django can't store binary directly; it enforces unicode on it.
        # Details: http://jinja.pocoo.org/2/documentation/api#bytecode-cache
        # and in the errors you get when you try it the other way.
#        bc = jinja2.MemcachedBytecodeCache(cache._cache,
#                                           "%sj2:" % settings.CACHE_PREFIX)
#        config['cache_size'] = -1 # Never clear the cache
#        config['bytecode_cache'] = bc
    return config

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

MIDDLEWARE_CLASSES = (
    #'commons.middleware.LocaleURLMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    #'session_csrf.CsrfMiddleware',
    'commonware.middleware.FrameOptionsHeader',
    'commonware.middleware.HidePasswordOnException',
)

AUTH_PROFILE_MODULE = 'users.UserProfile'

ROOT_URLCONF = '%s.urls' % ROOT_PACKAGE

INSTALLED_APPS = (
    # Local apps
    'commons',  # Content common to most playdoh-based apps.
    'jingo_minify',
    'tower',  # for ./manage.py extract (L10n)

    # We need this so the jsi18n view will pick up our locale directory.
    ROOT_PACKAGE,

    # Third-party apps
    'commonware.response.cookies',
    #'djcelery',
    'django_nose',

    # Django contrib apps
    'django.contrib.auth',
    'django_sha2',  # Load after auth to monkey-patch it.

    'django.contrib.contenttypes',
    'django.contrib.sessions',
    # 'django.contrib.sites',
    # 'django.contrib.messages',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',

    # L10n
    'product_details',

    # sheriffs specific
    'users',
    'cal',
    'roster',
    'vcal',

    # vendor-local
    'uuidfield',

)

# Tells the extract script what files to look for L10n in and what function
# handles the extraction. The Tower library expects this.
DOMAIN_METHODS = {
    'messages': [
        ('apps/**.py',
            'tower.management.commands.extract.extract_tower_python'),
        ('**/templates/**.html',
            'tower.management.commands.extract.extract_tower_template'),
    ],

    ## Use this if you have localizable HTML files:
    #'lhtml': [
    #    ('**/templates/**.lhtml',
    #        'tower.management.commands.extract.extract_tower_template'),
    #],

    ## Use this if you have localizable JS files:
    #'javascript': [
        # Make sure that this won't pull in strings from external libraries you
        # may use.
    #    ('media/js/**.js', 'javascript'),
    #],
}



# Path to Java. Used for compress_assets.
JAVA_BIN = '/usr/bin/java'

## Auth
PWD_ALGORITHM = 'bcrypt'
HMAC_KEYS = {  # for bcrypt only
    '2011-07-08': 'foobaring',
}

## Tests
TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'

## Celery
BROKER_HOST = 'localhost'
BROKER_PORT = 5672
BROKER_USER = 'playdoh'
BROKER_PASSWORD = 'playdoh'
BROKER_VHOST = 'playdoh'
BROKER_CONNECTION_TIMEOUT = 0.1
CELERY_RESULT_BACKEND = 'amqp'
CELERY_IGNORE_RESULT = True

## Misc

LOGIN_URL = '/users/login/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'

DEFAULT_DATE_FORMAT = '%A, %B %d, %Y'
EMAIL_SIGNATURE = """Mozilla Sheriff Duty
https://sheriffs.mozilla.com
"""

SESSION_COOKIE_AGE = 365  # default was 14

# If you don't have a MAILINGLIST_EMAIL email address all emails will instead
# be sent to all active and future sheriffs
#MAILINGLIST_EMAIL = 'sheriffs@mozilla.com'

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
