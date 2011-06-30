import datetime
from pprint import pprint
from django import http
from django.core.urlresolvers import reverse
from django.conf import settings
from roster.models import Slot
import jingo

def handler404(request):
    data = {}
    return jingo.render(request, '404.html', data, status=404)


def home(request):
    """Main calendar view."""
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
    return jingo.render(request, 'cal/home.html', data)
