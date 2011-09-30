import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# this does all the site.addsitedir(...) stuff
import manage

# don't assume that playdoh's manage.py has called setup_environ()
import settings
from django.core.management import setup_environ
setup_environ(settings)

from django.conf import settings

config = settings.DATABASES['default']
config['HOST'] = config.get('HOST', 'localhost')
config['PORT'] = config.get('PORT', '3306')

if not config['HOST'] or config['HOST'].endswith('.sock'):
    """Oh, you meant 'localhost'!"""
    config['HOST'] = 'localhost'

s = 'mysql --silent {NAME} -h{HOST} -u{USER}'

if config['PASSWORD']:
    s += ' -p{PASSWORD}'
else:
    del config['PASSWORD']
if config['PORT']:
    s += ' -P{PORT}'
else:
    del config['PORT']

db = s.format(**config)
table = 'schema_version'
