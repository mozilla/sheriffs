import re
from urlparse import urlparse
import datetime
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import simplejson as json
from django.core import mail
from roster.models import Slot, Swap
from nose.tools import eq_, ok_
from roster.views import get_next_starting_date
from utils import get_user_name


class RosterTest(TestCase):

    def test_initialize_roster(self):
        url = reverse('roster.initialize')
        response = self.client.get(url)
        eq_(response.status_code, 302)
        path = urlparse(response['location']).path
        eq_(path, settings.LOGIN_URL)

        admin = User.objects.create(
          username='admin',
          first_name='God',
          last_name='',
          is_staff=False,
          is_superuser=False,
        )
        admin.set_password('secret')
        admin.save()
        assert self.client.login(username='admin', password='secret')

        response = self.client.get(url)
        eq_(response.status_code, 302)
        path = urlparse(response['location']).path
        eq_(path, settings.LOGIN_URL)

        admin.is_staff = True
        admin.save()

        response = self.client.get(url)
        eq_(response.status_code, 200)

        # deliberatly chosing a Thursday
        today = datetime.date(2011, 7, 7)
        assert today.strftime('%A') == 'Thursday'

        data = {
          # starting on the Thursday
          'starting': today.strftime(settings.DEFAULT_DATE_FORMAT),
          # repeat for 1 week plus 1 day
          # so end on the next Friday
          'until': ((today + datetime.timedelta(days=7 + 1))
                           .strftime(settings.DEFAULT_DATE_FORMAT)),
          'usernames': ''
        }
        response = self.client.post(url, data)
        eq_(response.status_code, 200)
        ok_('errorlist' in response.content)

        # need at least 6 names we keep to make sure it proves
        # how it skips the weekends
        names = ('tom', 'dick', 'harry', 'ignored', 'barbara', 'mary', 'bob')
        assert len(names) >= 6
        for username in names:
            User.objects.create_user(
              username,
              '%s@mozilla.com' % username,
              password='secret',
            )
        # note how we skip user 'ignored'
        data['usernames'] = """
        dick
        harry
        tom
        barbara
          mary
        bob
        """
        response = self.client.post(url, data)
        eq_(response.status_code, 302)
        eq_(urlparse(response['location']).path, reverse('roster.index'))

        # Almost paradoxically, we expect to create 7 slots even though we
        # start on a Thursday and loop until the Friday *next* week.
        # 1) Thursday
        # 2) Friday
        # 3) Monday
        # 4) Tuesday
        # 5) Wednesday
        # 6) Thursday
        # 7) Friday
        eq_(Slot.objects.all().count(), 7)
        slot = Slot.objects.all().order_by('date')[0]
        eq_(slot.user.username, 'dick')
        eq_(slot.date, today)

        slot = Slot.objects.all().order_by('date')[1]
        eq_(slot.user.username, 'harry')
        eq_(slot.date, today + datetime.timedelta(days=1))

        slot = Slot.objects.all().order_by('date')[2]
        eq_(slot.user.username, 'tom')
        # today was a thursday, so the next non-weekend is +4
        eq_(slot.date, today + datetime.timedelta(days=2 + 2))

        slot = Slot.objects.all().order_by('date')[3]
        eq_(slot.user.username, 'barbara')
        eq_(slot.date, today + datetime.timedelta(days=3 + 2))

        slot = Slot.objects.all().order_by('date')[4]
        eq_(slot.user.username, 'mary')
        eq_(slot.date, today + datetime.timedelta(days=4 + 2))

        slot = Slot.objects.all().order_by('date')[5]
        eq_(slot.user.username, 'bob')
        eq_(slot.date, today + datetime.timedelta(days=5 + 2))

        slot = Slot.objects.all().order_by('date')[6]
        eq_(slot.user.username, 'dick')
        eq_(slot.date, today + datetime.timedelta(days=6 + 2))

    def test_initialize_roster_again(self):
        # the second time it should default to the order of the usernames
        # already in the last couple of slots
        for username in 'tom', 'dick', 'harry':
            User.objects.create_user(
              username,
              '%s@mozilla.com' % username,
              password='secret',
            )
        tom = User.objects.get(username='tom')
        dick = User.objects.get(username='dick')
        harry = User.objects.get(username='harry')

        friday = datetime.date(2012, 7, 1)
        monday = datetime.date(2012, 7, 4)
        tuesday = datetime.date(2012, 7, 5)
        wednesday = datetime.date(2012, 7, 6)
        thursday = datetime.date(2012, 7, 7)
        next_friday = datetime.date(2012, 7, 8)

        Slot.objects.create(user=tom, date=friday)
        Slot.objects.create(user=dick, date=monday)
        Slot.objects.create(user=harry, date=tuesday)
        Slot.objects.create(user=tom, date=wednesday)
        Slot.objects.create(user=dick, date=thursday)
        Slot.objects.create(user=harry, date=next_friday)

        admin = User.objects.create(
          username='admin',
          first_name='God',
          last_name='',
          is_staff=True,
        )
        admin.set_password('secret')
        admin.save()
        assert self.client.login(username='admin', password='secret')

        url = reverse('roster.initialize')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        regex = re.compile('<textarea.*>(.*?)</textarea>', re.DOTALL | re.M)
        names = regex.findall(response.content)[0]
        names = names.splitlines()
        eq_(names, ['tom', 'dick', 'harry'])
        regex = re.compile('<input .*?>', re.DOTALL | re.M)
        date_inputs = {}
        for each in regex.findall(response.content):
            try:
                name = re.findall('name="(\w+)"', each)[0]
                value = re.findall('value="(.*?)"', each)[0]
                date_inputs[name] = value
            except IndexError:
                pass
        starting = date_inputs['starting']
        starting = (datetime.datetime
          .strptime(starting, settings.DEFAULT_DATE_FORMAT))
        until = date_inputs['until']
        until = datetime.datetime.strptime(until, settings.DEFAULT_DATE_FORMAT)

        eq_(starting.strftime('%Y%m%d'),
            (next_friday + datetime.timedelta(days=1)).strftime('%Y%m%d'))
        eq_(until.strftime('%Y%m%d'),
            (next_friday + datetime.timedelta(days=1 + 3)).strftime('%Y%m%d'))

    def test_info_json(self):
        url = reverse('roster.info_json')
        response = self.client.get(url)
        eq_(response.status_code, 404)

        response = self.client.get(url, {'pk': ''})
        eq_(response.status_code, 404)

        response = self.client.get(url, {'pk': 999})
        eq_(response.status_code, 404)

        admin = User.objects.create_user(
          'admin',
          'admin@mozilla.com',
          password='secret',
        )

        peter = User.objects.create_user(
          'peter',
          'peter@mozilla.com',
          password='secret',
        )
        peter.first_name = 'Peter'
        peter.last_name = 'Bengtsson'
        peter.save()

        today = datetime.date.today()
        slot = Slot.objects.create(
          user=admin,
          date=today,
        )

        response = self.client.get(url, {'pk': slot.pk})
        eq_(response.status_code, 200)
        struct = json.loads(response.content)
        eq_(struct['pk'], slot.pk)
        eq_(struct['date'], today.strftime('%A, %B %d, %Y'))
        eq_(struct['name'], 'admin')
        eq_(struct['swap_needed'], False)

        slot = Slot.objects.create(
          user=peter,
          date=today,
          swap_needed=1
        )

        response = self.client.get(url, {'pk': slot.pk})
        eq_(response.status_code, 200)
        struct = json.loads(response.content)
        eq_(struct['pk'], slot.pk)
        eq_(struct['date'], today.strftime('%A, %B %d, %Y'))
        eq_(struct['name'], 'Peter Bengtsson (peter)')
        eq_(struct['swap_needed'], True)

    def test_offer_swap(self):
        admin = User.objects.create_user(
          'admin',
          'admin@mozilla.com',
          password='secret',
        )

        peter = User.objects.create_user(
          'peter',
          'peter@mozilla.com',
          password='secret',
        )
        peter.first_name = 'Peter'
        peter.last_name = 'Bengtsson'
        peter.save()

        today = datetime.date.today()
        slot = Slot.objects.create(
          user=admin,
          date=today,
          swap_needed=True,
        )
        eq_(slot.user, admin)

        url = reverse('roster.offer_swap')
        response = self.client.get(url)
        # GET not allowed
        eq_(response.status_code, 405)

        response = self.client.post(url, {})
        eq_(response.status_code, 302)
        eq_(urlparse(response['location']).path,
            settings.LOGIN_URL)

        assert self.client.login(username='peter', password='secret')
        response = self.client.post(url, {'pk': ''})
        eq_(response.status_code, 404)
        response = self.client.post(url, {'pk': 9999})
        eq_(response.status_code, 404)

        data = {
          'pk': slot.pk,
          'comment': """Please please please
          <script>alert('xss')</script>
          """.strip()
        }
        response = self.client.post(url, data)
        eq_(response.status_code, 302)

        # that should have sent an email to admin@mozilla.com
        assert 1 == len(mail.outbox)
        email = mail.outbox[-1]
        eq_(email.to, [admin.email])
        ok_('offer' in email.subject.lower())
        ok_('swap' in email.subject.lower())
        eq_(email.from_email, settings.SEND_EMAIL_FROM)
        ok_(slot.date.strftime(settings.DEFAULT_DATE_FORMAT) in email.body)
        ok_(peter.first_name in email.body)
        ok_(admin.username in email.body)
        ok_(settings.EMAIL_SIGNATURE.strip() in email.body)
        ok_(data['comment'] in email.body)

        # find the accept and decline urls and follow them
        urls = [x for x in email.body.split()
                if '://' in x]
        accept_url = [x for x in urls if 'accept' in x][0]
        decline_url = [x for x in urls if 'decline' in x][0]

        # anonymously click on accept
        self.client.logout()
        assert 'Peter' not in self.client.get('/').content

        uuid = [x for x in accept_url.split('/')
                if len(x) == 32][0]
        swap = Swap.objects.get(uuid=uuid)
        eq_(swap.state, Swap.STATE_UNANSWERED)
        eq_(swap.comment, data['comment'].strip())

        response = self.client.get(accept_url)
        eq_(response.status_code, 302)
        swap = Swap.objects.get(uuid=uuid)
        eq_(swap.state, Swap.STATE_ACCEPTED)
        slot = Slot.objects.get(pk=slot.pk)
        ok_(not slot.swap_needed)

        assert 2 == len(mail.outbox)
        email = mail.outbox[-1]
        eq_(email.from_email, settings.SEND_EMAIL_FROM)
        eq_(email.to, [peter.email])
        ok_('accepted' in email.body.lower())
        ok_('offer' in email.body.lower())
        ok_(settings.EMAIL_SIGNATURE.strip() in email.body)

        # change your mind!
        response = self.client.get(decline_url)
        # ...which you can't
        eq_(response.status_code, 200)
        ok_('too late' in response.content.lower())

        slot = Slot.objects.get(pk=slot.pk)
        eq_(slot.user, peter)

    def test_decline_offer_swap(self):
        admin = User.objects.create_user(
          'admin',
          'admin@mozilla.com',
          password='secret',
        )

        peter = User.objects.create_user(
          'peter',
          'peter@mozilla.com',
          password='secret',
        )
        peter.first_name = 'Peter'
        peter.last_name = 'Bengtsson'
        peter.save()

        today = datetime.date.today()
        slot = Slot.objects.create(
          user=admin,
          date=today,
        )

        assert self.client.login(username='peter', password='secret')
        url = reverse('roster.offer_swap')
        response = self.client.post(url, {'pk': slot.pk})
        eq_(response.status_code, 302)

        # that should have sent an email to admin@mozilla.com
        assert 1 == len(mail.outbox)
        email = mail.outbox[-1]
        # find the accept and decline urls and follow them
        urls = [x for x in email.body.split()
                if '://' in x]
        decline_url = [x for x in urls if 'decline' in x][0]
        accept_url = [x for x in urls if 'accept' in x][0]

        # anonymously click on accept
        self.client.logout()
        assert 'Peter' not in self.client.get('/').content

        uuid = [x for x in accept_url.split('/')
                if len(x) == 32][0]
        swap = Swap.objects.get(uuid=uuid)
        eq_(swap.state, Swap.STATE_UNANSWERED)
        response = self.client.get(decline_url)
        eq_(response.status_code, 302)
        swap = Swap.objects.get(uuid=uuid)
        eq_(swap.state, Swap.STATE_DECLINED)

        assert 2 == len(mail.outbox)
        email = mail.outbox[-1]
        eq_(email.from_email, settings.SEND_EMAIL_FROM)
        eq_(email.to, [peter.email])
        ok_('decline' in email.body.lower())
        ok_('offer' in email.body.lower())
        ok_(settings.EMAIL_SIGNATURE.strip() in email.body)

        response = self.client.get(accept_url)
        eq_(response.status_code, 200)
        ok_('too late' in response.content.lower())

    def test_request_swap(self):
        peter = User.objects.create_user(
          'peter',
          'peter@mozilla.com',
          password='secret',
        )
        today = datetime.date.today()
        slot = Slot.objects.create(
          user=peter,
          date=today,
        )

        url = reverse('roster.request_swap')
        response = self.client.get(url)
        # GET not allowed
        eq_(response.status_code, 405)
        response = self.client.post(url, {})
        eq_(response.status_code, 302)
        eq_(urlparse(response['location']).path,
            settings.LOGIN_URL)

        assert self.client.login(username='peter', password='secret')
        data = {'comment': 'Please please!'}
        response = self.client.post(url, data)
        eq_(response.status_code, 404)
        response = self.client.post(url, dict(data, pk=9999))
        eq_(response.status_code, 404)

        data['pk'] = slot.pk
        response = self.client.post(url, data)
        eq_(response.status_code, 302)

        slot, = Slot.objects.all()
        ok_(slot.swap_needed)

        # that should have sent an email to admin@mozilla.com
        assert 1 == len(mail.outbox)
        email = mail.outbox[-1]
        eq_(email.to, [settings.MAILINGLIST_EMAIL])
        ok_('request' in email.subject.lower())
        ok_('swap' in email.subject.lower())
        eq_(email.from_email, peter.email)
        ok_(slot.date.strftime(settings.DEFAULT_DATE_FORMAT) in email.body)
        ok_(peter.first_name in email.body)
        ok_(settings.EMAIL_SIGNATURE.strip() in email.body)
        ok_(data['comment'].strip() in email.body)

        # find the accept and decline urls and follow them
        urls = [x for x in email.body.split()
                if '://' in x]
        accept_url = [x for x in urls if 'accept' in x][0]
        #decline_url = [x for x in urls if 'decline' in x][0]

        # anonymously click on accept
        self.client.logout()
        assert 'Peter' not in self.client.get('/').content

        tom = User.objects.create_user(
          'tom', 'tom@mozilla.com', password='secret'
        )

        response = self.client.get(accept_url)
        eq_(response.status_code, 302)
        eq_(urlparse(response['location']).path,
            settings.LOGIN_URL)
        eq_(urlparse(response['location']).query,
            'next=%s' % urlparse(accept_url).path)

        data = {'username': 'tom', 'password': 'secret',
                'next': urlparse(accept_url).path}

        response = self.client.post(settings.LOGIN_URL, data, follow=True)
        eq_(response.status_code, 200)

        swap, = Swap.objects.all()
        eq_(swap.state, Swap.STATE_ACCEPTED)
        eq_(swap.user, tom)

        slot, = Slot.objects.all()
        eq_(slot.user, tom)
        ok_(not slot.swap_needed)

        User.objects.create_user(
          'dick', 'tom@mozilla.com', password='secret'
        )
        response = self.client.get(accept_url)
        eq_(response.status_code, 200)
        ok_('already accepted' in response.content.lower())

    def test_get_next_starting_date(self):
        # when no slots are set up, just return now
        r = get_next_starting_date()
        eq_(r, datetime.date.today())

        r = get_next_starting_date(today=datetime.date(2018, 1, 1))
        eq_(r, datetime.date(2018, 1, 1))

        for username in 'tom', 'dick', 'harry':
            User.objects.create_user(
              username,
              '%s@mozilla.com' % username,
              password='secret',
            )
        tom = User.objects.get(username='tom')
        dick = User.objects.get(username='dick')
        harry = User.objects.get(username='harry')

        friday = datetime.date(2011, 7, 1)
        monday = datetime.date(2011, 7, 4)
        tuesday = datetime.date(2011, 7, 5)
        wednesday = datetime.date(2011, 7, 6)
        thursday = datetime.date(2011, 7, 7)
        next_friday = datetime.date(2011, 7, 8)

        Slot.objects.create(user=tom, date=friday)
        Slot.objects.create(user=dick, date=monday)
        Slot.objects.create(user=harry, date=tuesday)
        Slot.objects.create(user=tom, date=wednesday)
        Slot.objects.create(user=dick, date=thursday)
        Slot.objects.create(user=harry, date=next_friday)

        r = get_next_starting_date(today=friday)
        eq_(r, wednesday)

    def test_replace_roster(self):
        url = reverse('roster.replace')
        response = self.client.get(url)
        eq_(response.status_code, 302)
        path = urlparse(response['location']).path
        eq_(path, settings.LOGIN_URL)

        admin = User.objects.create_user(
          'admin',
          'admin@mozilla.com',
          password='secret',
        )
        assert self.client.login(username='admin', password='secret')
        response = self.client.get(url)
        # not staff yet!
        eq_(response.status_code, 302)
        path = urlparse(response['location']).path
        eq_(path, settings.LOGIN_URL)

        admin.is_staff = True
        admin.save()

        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_("There are no users' slots to replace" in response.content)

        # We need some slots set up for the form to work
        for username in 'tom', 'dick', 'harry':
            User.objects.create_user(
              username,
              '%s@mozilla.com' % username,
              password='secret',
            )
        tom = User.objects.get(username='tom')
        dick = User.objects.get(username='dick')
        harry = User.objects.get(username='harry')

        tdelta = datetime.timedelta
        today = datetime.date.today()
        yesterday = today - tdelta(days=1)
        tomorrow = today + tdelta(days=1)

        Slot.objects.create(
          user=tom,
          date=yesterday,
        )
        Slot.objects.create(
          user=dick,
          date=today,
        )
        Slot.objects.create(
          user=harry,
          date=tomorrow,
        )
        Slot.objects.create(
          user=dick,
          date=tomorrow + tdelta(days=1),
        )
        Slot.objects.create(
          user=harry,
          date=tomorrow + tdelta(days=2),
        )

        response = self.client.get(url)
        from_usernames = response.content.split('name="from_username"')[1]
        from_usernames = from_usernames.split('</select>')[0]
        opt_regex = re.compile('<option value="(\w+)">(.*?)</option>', re.M)
        from_usernames = opt_regex.findall(from_usernames)
        eq_(len(from_usernames), 2)
        eq_(from_usernames[0], (dick.username, dick.username))
        eq_(from_usernames[1], (harry.username, harry.username))

        to_usernames = response.content.split('name="to_username"')[1]
        to_usernames = to_usernames.split('</select>')[0]
        to_usernames = opt_regex.findall(to_usernames)
        eq_(len(to_usernames), 4)
        eq_(to_usernames[0], (admin.username, admin.username))
        eq_(to_usernames[1], (dick.username, dick.username))
        eq_(to_usernames[2], (harry.username, harry.username))
        eq_(to_usernames[3], (tom.username, tom.username))

        data = {'from_username': 'junk',
                'to_username': 'junk',
                }
        response = self.client.post(url, data)
        eq_(response.status_code, 200)
        eq_(response.content.count('errorlist'), 2)

        # go ahead and make the switch
        data = {'from_username': harry.username,
                'to_username': tom.username,
                }
        response = self.client.post(url, data)
        eq_(response.status_code, 302)
        path = urlparse(response['location']).path
        eq_(path, reverse('roster.index'))

        # slot1
        ok_(Slot.objects.get(date=yesterday, user=tom))
        # slot2
        ok_(Slot.objects.get(date=today, user=dick))
        # slot3
        ok_(Slot.objects.get(date=tomorrow, user=tom))
        # slot4
        ok_(Slot.objects.get(date=tomorrow + tdelta(days=1), user=dick))
        # slot5
        ok_(Slot.objects.get(date=tomorrow + tdelta(days=2), user=tom))

        data = {'from_username': tom.username,
                'to_username': dick.username,
                'starting': tomorrow.strftime(settings.DEFAULT_DATE_FORMAT),
                'until': (tomorrow + tdelta(days=1))\
                  .strftime(settings.DEFAULT_DATE_FORMAT)
                }
        response = self.client.post(url, data)
        eq_(response.status_code, 302)

        # slot1
        ok_(Slot.objects.get(date=yesterday, user=tom))
        # slot2
        ok_(Slot.objects.get(date=today, user=dick))
        # slot3
        ok_(Slot.objects.get(date=tomorrow, user=dick))
        # slot4
        ok_(Slot.objects.get(date=tomorrow + tdelta(days=1), user=dick))
        # slot5
        ok_(Slot.objects.get(date=tomorrow + tdelta(days=2), user=tom))

    def test_replace_slot(self):
        admin = User.objects.create_user(
          'admin',
          'admin@mozilla.com',
          password='secret',
        )
        today = datetime.date.today()
        slot = Slot.objects.create(
          user=admin,
          date=today,
        )
        url = reverse('roster.replace_slot', args=[slot.pk])
        response = self.client.get(url)
        eq_(response.status_code, 302)
        path = urlparse(response['location']).path
        eq_(path, settings.LOGIN_URL)

        assert self.client.login(username='admin', password='secret')
        response = self.client.get(url)
        # not staff yet!
        eq_(response.status_code, 302)
        path = urlparse(response['location']).path
        eq_(path, settings.LOGIN_URL)

        admin.is_staff = True
        admin.save()

        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('There are no users to replace this with' in response.content)

        tom = User.objects.create_user(
          'tom',
          'tom@mozilla.com',
          password='secret',
        )
        tom.first_name = 'Tom'
        tom.last_name = 'Sawyer'
        tom.save()

        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('There are no users to replace this with' not in response.content)
        ok_('value="%s"' % tom.username in response.content)
        ok_(tom.first_name in response.content)

        data = {'to_username': 'junk'}
        response = self.client.post(url, data)
        eq_(response.status_code, 200)
        ok_('errorlist' in response.content)

        data = {'to_username': tom.username}
        response = self.client.post(url, data)
        eq_(response.status_code, 302)

        slot, = Slot.objects.all()
        eq_(slot.user, tom)

    def test_roster_index(self):
        url = reverse('roster.index')
        response = self.client.get(url)
        eq_(response.status_code, 200)

        names = ('tom', 'dick', 'harry')
        for username in names:
            User.objects.create_user(
              username,
              '%s@mozilla.com' % username,
              password='secret',
            )
        tom = User.objects.get(username='tom')
        tom.first_name = 'Tom'
        tom.last_name = 'Tom'
        tom.save()

        today = datetime.date.today()
        for i, name in enumerate(names):
            Slot.objects.create(
              user=User.objects.get(username=name),
              date=today + datetime.timedelta(days=i)
            )

        yesterday = today - datetime.timedelta(days=1)
        chris = User.objects.create_user(
          'chris',
          'chris@mozilla.com',
          password='secret'
        )
        Slot.objects.create(
          user=chris,
          date=yesterday
        )
        fmt = lambda x: x.strftime(settings.DEFAULT_DATE_FORMAT)
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_(get_user_name(tom) in response.content)
        for i, name in enumerate(names):
            ok_(get_user_name(User.objects.get(username=name))
                in response.content)
            date = today + datetime.timedelta(days=i)
            ok_(fmt(date) in response.content)

        ok_(get_user_name(chris) not in response.content)
        ok_(fmt(yesterday) not in response.content)

        response = self.client.get(url, {'include_past': 1})
        eq_(response.status_code, 200)
        ok_(get_user_name(chris) in response.content)
        ok_(fmt(yesterday) in response.content)

        response = self.client.get(url, {'page': 100})
        eq_(response.status_code, 200)
        for i, name in enumerate(names):
            date = today + datetime.timedelta(days=i)
            ok_(fmt(date) in response.content)

        response = self.client.get(url, {'page': 0})
        eq_(response.status_code, 200)
        for i, name in enumerate(names):
            date = today + datetime.timedelta(days=i)
            ok_(fmt(date) in response.content)

        response = self.client.get(url, {'page': 'xxx'})
        eq_(response.status_code, 404)
