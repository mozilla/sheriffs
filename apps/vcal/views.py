import datetime
import vobject
from urllib import quote as url_quote
from django import http
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.sites.models import RequestSite
from roster.models import Slot
from utils import get_user_name
import jingo

def vcal(request):
    data = {}
    data['page_title'] = "vCal exports"
    authenticated_user_string = None
    if request.user.is_authenticated():
        authenticated_user_string = (request.user.email and
                                     url_quote(request.user.email)
                                     or request.user.username)
    data['authenticated_user_string'] = authenticated_user_string
    return jingo.render(request, 'vcal/vcal.html', data)

def my_dates(request):
    if not request.GET.get('user'):
        raise http.Http404("Must supply a 'user' query argument")
    user_str = request.GET.get('user').strip()
    searches = ('username', 'username__iexact',
                'email', 'email__iexact')

    user = None
    for search in searches:
        try:
            user = User.objects.get(**{search: user_str})
        except User.DoesNotExist:
            # try another search
            pass
    if not user:
        raise http.Http404("User not found")

    return all_dates(request, extra_filter={'user': user},
                     filename='My Sheriff Duty.ics',
                     summary='Sheriff Duty')

def all_dates(request, extra_filter=None, filename="Sheriff Duty.ics",
              summary=None):
    # by giving it a verbose filnema like 'Sheriff Duty.css' means it's
    # going to appear very nicely automatically on peoples iCal.
    cal = vobject.iCalendar()

    # always start on the first of this month
    today = datetime.date.today()
    first = datetime.date(today.year, today.month, 1)
    slots = Slot.objects.filter(date__gte=first).order_by('date')
    if extra_filter:
        slots = slots.filter(**extra_filter)
    base_url = '%s://%s' % (request.is_secure() and 'https' or 'http',
                            RequestSite(request).domain)
    home_url = base_url + reverse('cal.home')
    for slot in slots[:31]:
        event = cal.add('vevent')
        event.add('summary').value = (summary and summary or get_user_name(slot.user))
        event.add('dtstart').value = slot.date
        event.add('dtend').value = slot.date
        url = (home_url + '?cal_y=%d&cal_m=%d' %
               (slot.date.year, slot.date.month))
        event.add('url').value = url
        event.add('description').value = ('Sheriff Duty on %s' %
         slot.date.strftime(settings.DEFAULT_DATE_FORMAT))

    resp = http.HttpResponse(cal.serialize(),
                             mimetype='text/calendar;charset=utf-8')
    resp['Content-Disposition'] = 'inline; filename="%s"' % filename
    return resp
