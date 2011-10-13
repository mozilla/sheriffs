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
from collections import defaultdict
from django.shortcuts import redirect
from django import http
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import Max, Min
from django.shortcuts import render
from roster.models import Slot


def handler404(request):
    data = {}
    return render(request, '404.html', data, status=404)


def home(request):
    """Main calendar view."""

    # special shortcuts based on calendar filtering
    if request.GET.get('cal_today'):
        return redirect(reverse('cal.home'))
    elif request.GET.get('cal_month'):
        try:
            year, month = [int(x) for x
              in request.GET['cal_month'].split(',')]
            as_date = datetime.date(year, month, 1)
        except:
            raise http.Http404("Invalid month")
        return redirect(reverse('cal.home') +
              '?cal_y=%s&cal_m=%s' % (as_date.year, as_date.month))
    elif request.GET.get('cal_m_diff'):
        m_diff = int(request.GET.get('cal_m_diff'))
        cal_m = request.GET.get('cal_m')
        if cal_m:
            cal_m = int(cal_m)
        else:
            cal_m = datetime.date.today().month
        cal_y = request.GET.get('cal_y')
        if cal_y:
            cal_y = int(cal_y)
        else:
            cal_y = datetime.date.today().year
        if m_diff < 0 and (cal_m + m_diff) <= 0:
            # trouble
            cal_m += m_diff + 12
            cal_y -= 1
        elif m_diff > 0 and (cal_m + m_diff) > 12:
            # trouble
            cal_m += m_diff - 12
            cal_y += 1
        else:
            cal_m += m_diff

        return redirect(reverse('cal.home') +
              '?cal_y=%s&cal_m=%s' % (cal_y, cal_m))

    data = {}  # You'd add data here that you're sending to the template.
    on_duty_next = []

    today = datetime.date.today()

    def label(date):
        if date == today - datetime.timedelta(days=1):
            return 'Yesterday'
        if date == today:
            return 'Today'
        if date == (today + datetime.timedelta(days=1)):
            return 'Tomorrow'
        return date.strftime('%A')

    extra_i = 0
    def is_weekend(date):
        return date.strftime('%A') in ('Saturday', 'Sunday')

    for i in -1, 0, 1, 2, 3:
        date = today + datetime.timedelta(days=i + extra_i)
        #while date.strftime('%A') in ('Saturday', 'Sunday'):
        #    extra_i += 1
        #    date = today + datetime.timedelta(days=i + extra_i)

        remarks = []
        users = []
        try:
            slot = (Slot.objects
                        .select_related('user')
                      .get(date__gte=date,
                           date__lt=date + datetime.timedelta(days=1))
                      )
            pk = slot.pk
            users.append(slot.user)
            if slot.swap_needed:
                remarks.append('swap-needed')
            if slot.user == request.user:
                remarks.append('self')
        except Slot.DoesNotExist:
            pk = None
            if date >= today:
                if is_weekend(date):
                    remarks.append('weekend')
                else:
                    remarks.append('offer-needed')
        if date == today:
            remarks.append('today')
        elif date < today:
            remarks.append('past')

        on_duty_next.append({
          'label': label(date),
          'users': users,
          'remarks': remarks,
          'pk': pk,
          'date': date,
        })

    my_duty_dates = []
    if request.user.is_authenticated():
        try:
            last_past = (Slot.objects
              .filter(user=request.user, date__lt=today)
              .order_by('-date'))[0]
            my_duty_dates.append({
              'pk': last_past.pk,
              'date': last_past.date,
              'remarks': ['last']
            })
        except IndexError:
            last_past = None
        next_slots = (Slot.objects
              .filter(user=request.user, date__gte=today)
              .order_by('date'))[:last_past and 4 or 5]

        _first_next = None
        for slot in next_slots:
            remarks = []
            if _first_next is None:
                _first_next = slot.date
                remarks.append('next')
            my_duty_dates.append({
              'pk': slot.pk,
              'date': slot.date,
              'remarks': remarks
            })
    data['my_duty_dates'] = my_duty_dates
    data['on_duty_next'] = on_duty_next
    data['date_format'] = settings.DEFAULT_DATE_FORMAT

    month, year = request.GET.get('cal_m'), request.GET.get('cal_y')
    if month:
        month = int(month)
        data['cal_m'] = month
    if year:
        year = int(year)
        data['cal_y'] = year
    week = None
    if request.GET.get('cal_w'):
        week = int(request.GET.get('cal_w'))
        data['cal_w'] = week
    data['weeks'] = _get_calendar_data(year, month, week, request.user,
                                   sunday_first=True, weeks=6)
    data['month_options'] = _get_month_options(year, month, week, weeks=6)
    return render(request, 'cal/home.html', data)


class Dict(dict):
    def __getattr__(self, key):
        return self[key]


def _get_month_options(year, month, week, weeks=5):
    min_date = Slot.objects.aggregate(Min('date'))['date__min']
    max_date = Slot.objects.aggregate(Max('date'))['date__max']

    if year is None or month is None:
        date = datetime.date.today()
    else:
        date = datetime.date(year, month, 1)
    if week:
        date += datetime.timedelta(days=week * 7)
    one_day = datetime.timedelta(days=1)
    current_months = []
    first_on_calendar = date
    last_on_calendar = date + datetime.timedelta(days=7 * (weeks - 1))
    while first_on_calendar < last_on_calendar:
        first_on_calendar += one_day
        if (first_on_calendar.month,
            first_on_calendar.year) not in current_months:
            current_months.append((first_on_calendar.month,
                                   first_on_calendar.year))
    d = min_date
    months = []
    done = []
    while d < max_date:
        if (d.month, d.year) not in done:
            done.append((d.month, d.year))
            current = today_month = False
            if (d.month, d.year) == (date.month, date.year):
                today_month = True
            if (d.month, d.year) in current_months:
                current = True
            month = {
              'label': d.strftime('%Y %B'),
              'current': current,
              'today_month': today_month,
              'value': d.strftime('%Y,%m'),
            }
            months.append(Dict(month))
        d += one_day
    return months


def _get_calendar_data(year, month, week, user, sunday_first=False, weeks=5):
    if year is None or month is None:
        date = datetime.date.today()
    else:
        date = datetime.date(year, month, 1)
    if week:
        date += datetime.timedelta(days=week * 7)
    no_weeks = weeks
    weeks = []
    _months = []
    _rowspans = {}
    _is_authenticated = user.is_authenticated()
    _today = datetime.date.today()

    # the code below (with no_weeks==5) causes 100+ SQL queries so instead
    # we're going to use a dict to save lookups
    date_range = (
      date,
      date + datetime.timedelta(days=7 * no_weeks)
    )
    all_slots = defaultdict(list)
    unclaimed = []
    users = defaultdict(list)
    for slot in Slot.objects.filter(date__range=date_range).select_related('user'):
        all_slots[slot.date].append(slot)
        users[slot.date].append(slot.user)
        if slot.swap_needed:
            unclaimed.append(slot.date)

    while len(weeks) < no_weeks:
        days = []
        for day_date in _get_day_dates(date, sunday_first=sunday_first):
            remarks = []
            if day_date < _today:
                remarks.append('past')

            if day_date in unclaimed:
                remarks.append('unclaimed')
            elif day_date == _today:
                remarks.append('today')
            elif _is_authenticated and user in users.get(day_date, []):
                remarks.append('self')
            day = {'date': day_date,
                   'remarks': remarks,
                   'slots': all_slots[day_date]}
            days.append(Dict(day))
        week = {'days': days}
        if not _months or (_months and date.month != _months[-1]):
            week['month'] = Dict({
              'label': date.strftime('%b'),
              'month_number': date.month,
              'rowspan': None,
            })
            _rowspans[date.month] = 0
            _months.append(date.month)
        else:
            _rowspans[date.month] += 1
            week['month'] = None
        weeks.append(Dict(week))
        date += datetime.timedelta(days=7)

    for week in weeks:
        if getattr(week, 'month', None):
            week.month['rowspan'] = _rowspans[week.month.month_number] + 1

    return weeks


def _get_day_dates(this_date, sunday_first=False):
    """return 7 date instances that cover this week for any given date.

    If this_date is a Wednesday, return
    [<Monday's date>, <Tuesday's date>, this_date,
     ..., <Sunday's date>]

    However, if @sunday_first==True return this:
    [<Sunday's date>, <Monday's date>, <Tuesday's date>, this_date,
     ..., <Saturday's date>]

    """
    if sunday_first and this_date.strftime('%A') == 'Sunday':
        this_date += datetime.timedelta(days=1)
    this_week = this_date.strftime('%W')
    date = this_date - datetime.timedelta(days=7)
    dates = []
    while len(dates) < 7:
        if date.strftime('%W') == this_week:
            dates.append(date)
        date += datetime.timedelta(days=1)

    if sunday_first:
        one_day = datetime.timedelta(days=1)
        dates = [x - one_day for x in dates]
    return dates
