import datetime
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
    title = "Atom roster feed"
    link = "/"
    subtitle = "Hi"

    def items(self, limit=None):
        today = datetime.date.today()
        future_slots = (Slot.objects
                        .filter(date__gte=today)
                        .count())
        if limit is None:
            limit = 10
        dates = []
        possible_dates = [today + datetime.timedelta(days=x)
                          for x in range(min(future_slots, limit))]
        for date in possible_dates:
            # only add it if it has slots in it
            if Slot.objects.filter(date=date).exists():
                dates.append(date)
        return dates

    def item_link(self, date):
#        print dir(date)
        return date.strftime(settings.DEFAULT_DATE_FORMAT)
        # there isn't really a URL for a Slot
        return '/#slot:%s' % item.pk

    def item_guid(self, date):
        return date.isoformat()
        return date.strftime(settings.DEFAULT_DATE_FORMAT)

    def item_title(self, date):
        slots = Slot.objects.filter(date=date).select_related('user')
        title = [get_user_name(x.user) for x in slots]
        return ' & '.join(title)
        print "DATE", repr(date)
        return "HI"
        return get_user_name(item.user)
