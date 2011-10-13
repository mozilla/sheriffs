# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla Sheriff Duty.
#
# The Initial Developer of the Original Code is Mozilla Corporation.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import datetime
import vobject
from urllib import quote as url_quote
from django import http
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.sites.models import RequestSite
from django.shortcuts import render
from roster.models import Slot
from utils import get_user_name

def vcal(request):
    data = {}
    data['page_title'] = "vCal exports"
    authenticated_user_string = None
    if request.user.is_authenticated():
        authenticated_user_string = (request.user.email and
                                     url_quote(request.user.email)
                                     or request.user.username)
    data['authenticated_user_string'] = authenticated_user_string
    return render(request, 'vcal/vcal.html', data)

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
            break
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
    slots = (Slot.objects.filter(date__gte=first)
              .order_by('date')
              .select_related('user'))
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
