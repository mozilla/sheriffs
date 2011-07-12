import datetime
from django.shortcuts import redirect
from pprint import pprint
from django import http
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import Max, Min
from roster.models import Slot
import jingo

def handler404(request):
    data = {}
    return jingo.render(request, '404.html', data, status=404)


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
    def label(i):
        if i == -1:
            return 'Yesterday'
        if i == 0:
            return 'Today'
        if i == 1:
            return 'Tomorrow'
        return (today + datetime.timedelta(days=i)).strftime('%A')

    for i in -1, 0, 1, 2, 3:
        date = today + datetime.timedelta(days=i)
        remarks = []
        users = []
        try:
            slot = (Slot.objects
                        .select_related('user')
                      .get(date__gte=today + datetime.timedelta(days=i),
                           date__lt=today + datetime.timedelta(days=i+1))
                      )
            pk = slot.pk
            users.append(slot.user)
            if slot.swap_needed:
                remarks.append('swap-needed')
            if slot.user == request.user:
                remarks.append('self')
        except Slot.DoesNotExist:
            names = []
            pk = None
            if i >= 0:
                remarks.append('offer-needed')
        if i == 0:
            remarks.append('today')
        elif i < 0:
            remarks.append('past')

        on_duty_next.append({
          'label': label(i),
          'users': users,
          'remarks': remarks,
          'pk': pk,
          'date': date,
        })
    #
    #pprint(on_duty_next)

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
    return jingo.render(request, 'cal/home.html', data)


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
    today = datetime.date.today()
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
    today = datetime.date.today()
    #print (year, month, week)
    if year is None or month is None:
        date = datetime.date.today()
    else:
        date = datetime.date(year, month, 1)
    if week:
        date += datetime.timedelta(days=week * 7)
    #print repr(date)
    no_weeks = weeks
    weeks = []
    #_current_month = date.month
    _months = []
    _rowspans = {}
    _is_authenticated = user.is_authenticated()
    _today = datetime.date.today()
    while len(weeks) < no_weeks:
        days = []

        for day_date in _get_day_dates(date, sunday_first=sunday_first):
            remarks = []
            if day_date < _today:
                remarks.append('past')
            slots = Slot.objects.filter(date=day_date).select_related('user')

            if slots.filter(swap_needed=True).exists():
                remarks.append('unclaimed')
            elif day_date == _today:
                remarks.append('today')
            elif _is_authenticated and slots.filter(user=user).exists():
                remarks.append('self')
            day = {'date': day_date,
                   'remarks': remarks,
                   'slots': slots}
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
            #_current_month = date.month
        else:
            _rowspans[date.month] += 1
            week['month'] = None
        #pprint(week)
        weeks.append(Dict(week))
        # if the week ended on 'noday' days, move those into a new week

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
