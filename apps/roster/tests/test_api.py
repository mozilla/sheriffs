import re
import datetime
from django.utils import simplejson as json
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from nose.tools import eq_, ok_
from roster.models import Slot
from utils import get_user_name


class APITest(TestCase):

    def test_get_slot_by_id(self):
        url = '/api/v1/slot/1/'
        response = self.client.get(url)
        eq_(response.status_code, 404)

        tom = User.objects.create_user(
          'tom',
          'tom@mozilla.com',
          password='secret',
        )
        tom.first_name = 'Tom'
        tom.last_name = 'Sawyer'
        tom.save()

        today = datetime.date.today()
        slot = Slot.objects.create(
          user=tom,
          date=today
        )

        url = '/api/v1/slot/%s/' % slot.pk
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('application/json' in response['content-type'])
        response = self.client.get(url, {'format': 'json'})
        eq_(response.status_code, 200)
        ok_('application/json' in response['content-type'])
        response = self.client.get(url, {'format': 'html'})
        eq_(response.status_code, 200)
        ok_('text/html' in response['content-type'])

    def test_get_slots(self):
        url = '/api/v1/slot/'
        response = self.client.get(url)
        eq_(response.status_code, 200)
        struct = json.loads(response.content)
        ok_(struct['meta'])
        ok_(not struct['objects'])

        tom = User.objects.create_user(
          'tom',
          'tom@mozilla.com',
          password='secret',
        )
        tom.first_name = 'Tom'
        tom.last_name = 'Sawyer'
        tom.save()
        dick = User.objects.create_user(
          'dick',
          'dick@mozilla.com',
          password='secret',
        )

        today = datetime.date.today()
        slot1 = Slot.objects.create(
          user=tom,
          date=today
        )
        tomorrow = today + datetime.timedelta(days=1)
        slot2 = Slot.objects.create(
          user=dick,
          date=tomorrow,
          swap_needed=True,
        )

        response = self.client.get(url)
        eq_(response.status_code, 200)
        struct = json.loads(response.content)
        ok_(struct['meta'])
        ok_(struct['objects'])
        eq_(len(struct['objects']), 2)

        first = struct['objects'][0]
        eq_(first['id'], slot1.pk)
        eq_(first['date_iso'], today.isoformat())
        eq_(first['swap_needed'], False)
        eq_(first['user'], 'Tom Sawyer (tom)')
        eq_(first['date'], today.strftime(settings.DEFAULT_DATE_FORMAT))
        eq_(first['email'], 'tom@mozilla.com')

        second = struct['objects'][1]
        eq_(second['id'], slot2.pk)
        eq_(second['date_iso'], tomorrow.isoformat())
        eq_(second['swap_needed'], True)
        eq_(second['user'], 'dick')
        eq_(second['date'], tomorrow.strftime(settings.DEFAULT_DATE_FORMAT))
        eq_(second['email'], 'dick@mozilla.com')

        response = self.client.get(second['resource_uri'])
        eq_(response.status_code, 200)
        struct = json.loads(response.content)
        eq_(struct, second)

        tomorrow = today + datetime.timedelta(days=1)
        Slot.objects.create(
          user=tom,
          date=tomorrow + datetime.timedelta(days=1),
          swap_needed=True,
        )
        response = self.client.get(url)
        eq_(response.status_code, 200)
        struct = json.loads(response.content)
        ok_(struct['meta'])
        ok_(struct['objects'])
        eq_(len(struct['objects']), 3)
        last = struct['objects'][-1]

        eq_(last['email'], 'tom@mozilla.com')
        eq_(last['date_label'],
          (tomorrow + datetime.timedelta(days=1)).strftime('%A')
        )

    def test_get_slots_as_html(self):
        url = '/api/v1/slot/'
        response = self.client.get(url, {'format': 'html'})
        eq_(response.status_code, 200)
        ok_('text/html' in response['content-type'])

        tom = User.objects.create_user(
          'tom',
          'tom@mozilla.com',
          password='secret',
        )
        tom.first_name = 'Tom'
        tom.last_name = 'Sawyer'
        tom.save()
        dick = User.objects.create_user(
          'dick',
          'dick@mozilla.com',
          password='secret',
        )

        today = datetime.date.today()
        Slot.objects.create(
          user=tom,
          date=today
        )
        tomorrow = today + datetime.timedelta(days=1)
        Slot.objects.create(
          user=dick,
          date=tomorrow,
          swap_needed=True,
        )

        response = self.client.get(url, {'format': 'html'})
        eq_(response.status_code, 200)
        ok_(today.strftime(settings.DEFAULT_DATE_FORMAT)
            in response.content)
        ok_('Today' in response.content)
        ok_(get_user_name(tom) in response.content)

        ok_(tomorrow.strftime(settings.DEFAULT_DATE_FORMAT)
            in response.content)
        ok_('Tomorrow' in response.content)
        ok_(get_user_name(dick) in response.content)

    def test_special_shortcuts(self):
        tom = User.objects.create_user(
          'tom',
          'tom@mozilla.com',
          password='secret',
        )
        tom.first_name = 'Tom'
        tom.last_name = 'Sawyer'
        tom.save()

        dick = User.objects.create_user(
          'dick',
          'dick@mozilla.com',
          password='secret',
        )
        harry = User.objects.create_user(
          'harry',
          'harry@mozilla.com',
          password='secret',
        )

        today = datetime.date.today()
        slot1 = Slot.objects.create(
          user=tom,
          date=today
        )

        Slot.objects.create(
          user=dick,
          date=today - datetime.timedelta(days=1)
        )

        slot2 = Slot.objects.create(
          user=harry,
          date=today + datetime.timedelta(days=1)
        )

        url = '/api/v1/today/'
        response = self.client.get(url)
        eq_(response.status_code, 200)

        struct = json.loads(response.content)
        ok_(struct['meta'])
        ok_(struct['objects'])
        eq_(len(struct['objects']), 1)

        first = struct['objects'][0]
        eq_(first['id'], slot1.pk)
        eq_(first['date_iso'], today.isoformat())
        eq_(first['swap_needed'], False)
        eq_(first['user'], 'Tom Sawyer (tom)')
        eq_(first['date'], today.strftime(settings.DEFAULT_DATE_FORMAT))
        eq_(first['email'], 'tom@mozilla.com')

        response = self.client.get(url, {'format': 'html'})
        eq_(response.status_code, 200)
        ok_(today
          .strftime(settings.DEFAULT_DATE_FORMAT) in response.content)

        url = '/api/v1/tomorrow/'
        response = self.client.get(url)
        eq_(response.status_code, 200)

        struct = json.loads(response.content)
        ok_(struct['meta'])
        ok_(struct['objects'])
        eq_(len(struct['objects']), 1)

        first = struct['objects'][0]
        eq_(first['id'], slot2.pk)
        eq_(first['date_iso'], (today +
          datetime.timedelta(days=1)).isoformat())
        eq_(first['user'], 'harry')
        eq_(first['date'], ((today + datetime.timedelta(days=1))
          .strftime(settings.DEFAULT_DATE_FORMAT)))
        eq_(first['email'], 'harry@mozilla.com')

        response = self.client.get(url, {'format': 'html'})
        eq_(response.status_code, 200)
        ok_((today + datetime.timedelta(days=1))
          .strftime(settings.DEFAULT_DATE_FORMAT) in response.content)

    def test_api_documentation(self):
        url = reverse('roster.api_documentation')
        response = self.client.get(url)
        eq_(response.status_code, 200)

        # create a dummy slot so that the example URLS work
        tom = User.objects.create_user(
          'tom',
          'tom@mozilla.com',
          password='secret',
        )
        today = datetime.date.today()
        Slot.objects.create(
          user=tom,
          date=today
        )

        response = self.client.get(url)
        eq_(response.status_code, 200)

        # check all examples
        regex = re.compile('<p.*?class="examples".*?>(.*?)</p>',
                           re.DOTALL | re.M)
        url_regex = re.compile('href="([^"]+)"')
        for html in regex.findall(response.content):
            for url in url_regex.findall(html):
                ok_(url.startswith('http'))
                r = self.client.get(url)
                eq_(r.status_code, 200)
