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
