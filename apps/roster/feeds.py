import datetime
import jingo
from django.core.urlresolvers import reverse
from django.utils.feedgenerator import Atom1Feed
from django.conf import settings
from django.contrib.syndication.views import Feed
from .models import Slot
from utils import get_user_name


class GCalAtom1Feed(Atom1Feed):

    def root_attributes(self):
        attrs = super(GCalAtom1Feed, self).root_attributes()
        attrs['xmlns:gCal'] = 'http://schemas.google.com/gCal/2005'
        return attrs


class AtomRosterFeed(Feed):
    feed_type = GCalAtom1Feed
    title = "Mozilla Sheriff Duty"
    link = "/"
    subtitle = "Atom roster feed adhering to Google Calendar queries"

    def get_object(self, request):
        return request

    def items(self, request):
        # because this is a G(oogle)CalAtom1Feed we can pick up certain query
        # string variables that dictate what dates to return
        if request.GET.get('start-min'):
            min_date = datetime.datetime.strptime(
              request.GET.get('start-min'),
              '%Y-%m-%d'
            ).date()
        else:
            min_date = datetime.date.today()

        if request.GET.get('max-results'):
            limit = int(request.GET.get('max-results'))
        else:
            limit = 10

        future_slots = (Slot.objects
                        .filter(date__gte=min_date)
                        .count())
        dates = []
        possible_dates = [min_date + datetime.timedelta(days=x)
                          for x in range(min(future_slots, limit))]
        for date in possible_dates:
            # only add it if it has slots in it
            if Slot.objects.filter(date=date).exists():
                dates.append(date)
        return dates

    def item_link(self, date):
        return '/' + '#' + date.strftime('%Y-%m-%d')

    def item_guid(self, date):
        return date.isoformat()

    def item_title(self, date):
        slots = Slot.objects.filter(date=date).select_related('user')
        title = [get_user_name(x.user) for x in slots]
        return ' & '.join(title)


def test_atom_feed(request):  # pragma: no cover
    # this is not a unit test
    data = {'url': reverse('roster.feed.atom')}
    return jingo.render(request, 'roster/test_atom_feed.html', data)
