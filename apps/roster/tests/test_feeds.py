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


class FeedTest(TestCase):

    def test_atom_feed(self):
        url = reverse('roster.feed.atom')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        #struct = json.loads(response.content)
        eq_(response['content-type'], 'application/atom+xml; charset=utf8')

        # now let's add some content
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

        one_day = datetime.timedelta(days=1)
        yesterday = datetime.date.today() - one_day
        slot0 = Slot.objects.create(
          user=dick,
          date=yesterday
        )

        today = datetime.date.today()
        slot1 = Slot.objects.create(
          user=tom,
          date=today
        )
        tomorrow = today + one_day
        slot2 = Slot.objects.create(
          user=dick,
          date=tomorrow,
          swap_needed=True,
        )

        response = self.client.get(url)
        eq_(response.status_code, 200)
        eq_(response.content.count('<entry'), 2)
        content = response.content
        ok_(-1 < content.find('<title>%s</title>' % get_user_name(tom))
               < content.find('<title>%s</title>' % get_user_name(dick)))

        jane = User.objects.create(
          username='jane',
          email='jane@mozilla.com',
          first_name='Jane'
        )
        # double book her on todays slot
        slot1b = Slot.objects.create(
          user=jane,
          date=today
        )

        response = self.client.get(url)
        eq_(response.status_code, 200)
        eq_(response.content.count('<entry'), 2)
        content = response.content
        ok_(-1 < content.find('<title>%s</title>' % get_user_name(dick)))
        # the order of squashed names isn't guaranteed
        a, b = get_user_name(tom), get_user_name(jane)
        combined = [
          '<title>%s &amp; %s</title>' % (a, b),
          '<title>%s &amp; %s</title>' % (b, a)
        ]
        ok_(combined[0] in content or combined[1] in content)
