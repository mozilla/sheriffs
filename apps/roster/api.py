import datetime
from django.conf import settings
from django.template import Context, loader
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer
from tastypie.bundle import Bundle
from models import Slot
from utils import get_user_name


class SlotSerializer(Serializer):

    def __init__(self, *args, **kwargs):
        self.use_date_labels = kwargs.pop('use_date_labels', True)
        super(SlotSerializer, self).__init__(*args, **kwargs)

    def to_html(self, data, options=None):
        # note that this method is used for single items as well as multiples
        if isinstance(data, dict) and data.get('error_message'):
            return ("<p><strong>Error:</strong><br><span>%s</span></p>" %
                    data['error_message'])
        if isinstance(data, Bundle):
            objects = [data.obj]
            total_count = 1
        else:
            objects = [x.obj for x in data['objects']]
            total_count = data['meta']['total_count']
        options = options or {}
        template = loader.get_template('roster/_html_serialize_slot.html')
        items = []
        today = datetime.date.today()
        for slot in objects:
            date_label = ''
            if self.use_date_labels:
                if slot.date == today:
                    date_label = 'Today'
                elif slot.date == (today + datetime.timedelta(days=1)):
                    date_label = 'Tomorrow'
                # api doesn't deal with past slots
                #elif slot.date == (today - datetime.timedelta(days=1)):
                #    date_label = 'Yesterday'

            date_formatted = slot.date.strftime(settings.DEFAULT_DATE_FORMAT)
            user_name = get_user_name(slot.user)
            items.append(dict(date_label=date_label,
                              date_formatted=date_formatted,
                              user_name=user_name))
        context = {
          'items': items,
          'total_count': total_count,
        }
        return template.render(Context(context))


class SlotResource(ModelResource):

    class Meta:
        queryset = Slot.objects
        fields = ['user', 'date', 'swap_needed', 'id', 'email', 'date_iso',
                  'date_label']
        resource_name = 'slot'
        allowed_methods = ['get']
        limit = 10
        serializer = SlotSerializer()

    def get_object_list(self, request):
        return Slot.objects.filter(date__gte=datetime.date.today())

    def dehydrate(self, bundle):
        bundle.data['user'] = get_user_name(bundle.obj.user)
        bundle.data['email'] = bundle.obj.user.email
        bundle.data['id'] = bundle.obj.pk
        bundle.data['date_iso'] = bundle.obj.date.isoformat()
        bundle.data['date'] = (bundle.obj.date
                               .strftime(settings.DEFAULT_DATE_FORMAT))
        bundle.data['date_label'] = self._get_date_label(bundle.obj.date)
        return bundle

    def _get_date_label(self, date):
        today = datetime.date.today()
        if date == today:
            return u'Today'
        elif date == today + datetime.timedelta(days=1):
            return u'Tomorrow'
        if (date - today).days < 7:
            return date.strftime('%A')
        return u''


class TodayResource(SlotResource):
    class Meta:
        resource_name = 'today'
        serializer = SlotSerializer(use_date_labels=False)

    def get_object_list(self, request):
        return Slot.objects.filter(date=datetime.date.today())


class TomorrowResource(SlotResource):
    class Meta:
        resource_name = 'tomorrow'
        serializer = SlotSerializer(use_date_labels=False)

    def get_object_list(self, request):
        tomorrow = (datetime.date.today()
                    + datetime.timedelta(days=1))
        return Slot.objects.filter(date=tomorrow)
