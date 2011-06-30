from django.conf import settings
from utils import get_user_name

def _format_date(date, fmt=None):
    if fmt is None:
        fmt = settings.DEFAULT_DATE_FORMAT
    return date.strftime(fmt)

def formatters(requests):
    return {
       'get_user_name': get_user_name,
       'format_date': _format_date,
    }

def active_tab(request):
    if '/roster/' in request.path:
        return {'active_tab': 'roster'}

    return {'active_tab': 'calendar'}
