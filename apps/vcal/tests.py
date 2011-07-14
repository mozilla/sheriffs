import datetime
from urllib import quote as url_quote
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from roster.models import Slot
from nose.tools import eq_, ok_
from utils import get_user_name
import vobject


def fmt(date):
    return date.strftime(settings.DEFAULT_DATE_FORMAT)

class VCalTest(TestCase):

    def test_vcal_home_page(self):
        url = reverse('vcal.vcal')
        response = self.client.get(url)
        eq_(response.status_code, 200)

        my_url = reverse('vcal.my_dates')
        all_url = reverse('vcal.all_dates')
        ok_(my_url not in response.content)
        ok_(all_url in response.content)

        tom = User.objects.create_user(
          'tom',
          'tom@mozilla.com',
          password='secret',
        )
        assert self.client.login(username='tom', password='secret')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_(my_url in response.content)
        ok_(all_url in response.content)

        my_url_with_email = my_url + '?user=%s' % url_quote(tom.email)
        ok_(my_url_with_email in response.content)

    def test_all_dates(self):
        url = reverse('vcal.all_dates')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        eq_(response['Content-Type'], 'text/calendar;charset=utf-8')
        ok_('Sheriff Duty.ics' in response['Content-Disposition'])

        # add some slots and stuff
        tom = User.objects.create(
          username='tom',
          first_name='Tom',
          last_name='smith',
          email='tom@mozilla.com'
        )
        dick = User.objects.create(
          username='dick',
        )

        today = datetime.date.today()
        Slot.objects.create(
          user=tom,
          date=today
        )
        Slot.objects.create(
          user=dick,
          date=today + datetime.timedelta(days=1)
        )

        url = reverse('vcal.all_dates')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        payload = response.content
        ok_(-1 < payload.find(get_user_name(tom)) <
                 payload.find(get_user_name(dick)))

        parsed = vobject.readComponents(payload)
        first = parsed.next()
        eq_(first.vevent.dtstart.value, today)
        ok_(get_user_name(tom) in first.vevent.summary.value)
        ok_(fmt(today) in first.vevent.description.value)

        url = first.vevent.url.value
        ok_(url.startswith('http'))
        response = self.client.get(url)
        eq_(response.status_code, 200)

    def test_my_dates(self):
        url = reverse('vcal.my_dates')
        response = self.client.get(url)
        eq_(response.status_code, 404)

        response = self.client.get(url, {'user': 'xxx'})
        eq_(response.status_code, 404)

        # add some slots and stuff
        tom = User.objects.create(
          username='tom',
          first_name='Tom',
          last_name='smith',
          email='tom@mozilla.com'
        )
        dick = User.objects.create(
          username='dick',
        )

        today = datetime.date.today()
        Slot.objects.create(
          user=tom,
          date=today - datetime.timedelta(days=7),
        )
        Slot.objects.create(
          user=tom,
          date=today
        )
        Slot.objects.create(
          user=dick,
          date=today + datetime.timedelta(days=1)
        )
        Slot.objects.create(
          user=tom,
          date=today + datetime.timedelta(days=7),
        )

        response = self.client.get(url, {'user': tom.email})
        eq_(response.status_code, 200)

        eq_(response['Content-Type'], 'text/calendar;charset=utf-8')
        ok_('My Sheriff Duty.ics' in response['Content-Disposition'])

        payload = response.content
        parsed = vobject.readComponents(payload)
