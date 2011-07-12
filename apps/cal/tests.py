import datetime
from urlparse import urlparse
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User
from django.core.urlresolvers import reverse
from roster.models import Slot
from nose.tools import eq_, ok_

class CalTest(TestCase):

    def test_render_home_page(self):
        """Render the '/' view"""
        url = reverse('cal.views.home')
        response = self.client.get(url)
        eq_(response.status_code, 200)

    def test_home_page_calendar_redirect_jumps(self):
        # today
        url = reverse('cal.views.home')
        response = self.client.get(url, {'cal_today': '1'})
        eq_(response.status_code, 302)
        eq_(urlparse(response['location']).path, url)

        # particular month
        response = self.client.get(url, {'cal_month': '2011,8'})
        eq_(response.status_code, 302)
        eq_(urlparse(response['location']).path, url)
        eq_(urlparse(response['location']).query, 'cal_y=2011&cal_m=8')
        response = self.client.get(url, {'cal_month': '2011'})
        eq_(response.status_code, 404)
        response = self.client.get(url, {'cal_month': '2011,8,'})
        eq_(response.status_code, 404)
        response = self.client.get(url, {'cal_month': '2011,0'})
        eq_(response.status_code, 404)

        # month diff
        response = self.client.get(url, {'cal_m_diff': '-1'})
        eq_(response.status_code, 302)
        eq_(urlparse(response['location']).path, url)
        today = datetime.date.today()
        if today.month == 1:
            expect = 'cal_y=%d&cal_m=12' % (today.year - 1)
        else:
            expect = 'cal_y=%d&cal_m=%d' % (today.year, today.month - 1)
        eq_(urlparse(response['location']).query, expect)

        response = self.client.get(url, {'cal_m_diff': '1'})
        eq_(response.status_code, 302)
        eq_(urlparse(response['location']).path, url)
        today = datetime.date.today()
        if today.month == 12:
            expect = 'cal_y=%d&cal_m=1' % (today.year + 1)
        else:
            expect = 'cal_y=%d&cal_m=%d' % (today.year, today.month + 1)
        eq_(urlparse(response['location']).query, expect)

        # month diff with on specific month
        response = self.client.get(url, {
          'cal_m_diff': '-1',
          'cal_m': '1',
          'cal_y': '2011'
        })
        eq_(response.status_code, 302)
        eq_(urlparse(response['location']).path, url)
        eq_(urlparse(response['location']).query, 'cal_y=2010&cal_m=12')

        response = self.client.get(url, {
          'cal_m_diff': '1',
          'cal_m': '12',
          'cal_y': '2011'
        })
        eq_(response.status_code, 302)
        eq_(urlparse(response['location']).path, url)
        eq_(urlparse(response['location']).query, 'cal_y=2012&cal_m=1')

        response = self.client.get(url, {
          'cal_m_diff': '1',
          'cal_m': '10',
          'cal_y': '2011'
        })
        eq_(response.status_code, 302)
        eq_(urlparse(response['location']).path, url)
        eq_(urlparse(response['location']).query, 'cal_y=2011&cal_m=11')


    def test_get_calendar_data_basic(self):
        from cal.views import _get_calendar_data
        weeks = _get_calendar_data(None, None, None, AnonymousUser(),
                                  sunday_first=True, weeks=5)
        eq_(len(weeks), 5)
        first_week = weeks[0]

        eq_(len(first_week.days), 7)
        eq_(first_week.days[0].date.strftime('%A'), 'Sunday')
        eq_(first_week.days[-1].date.strftime('%A'), 'Saturday')
        ok_(datetime.date.today() in [x.date for x in first_week.days])

        # expect the first week to have some information about this month
        ok_(first_week.month)
        #print first_week.month
        #print first_week

    def test_get_calendar_data_with_me_in_it(self):
        peter = User.objects.create_user(
          'peter',
          'peter@mozilla.com',
           password='secret',
        )
        slot = Slot.objects.create(
          user=peter,
          date=datetime.date(2011, 7, 8) # a friday
        )

        from cal.views import _get_calendar_data
        weeks = _get_calendar_data(2011, 7, 1, peter,
                                  sunday_first=True, weeks=1)
        week1 = weeks[0]
        eq_(week1.days[0].date, datetime.date(2011, 7, 3))
        eq_(week1.days[-1].date, datetime.date(2011, 7, 9))

        friday = week1.days[5]
        ok_(slot in friday.slots)
        ok_('self' in friday.remarks)


    def test_get_day_dates(self):
        from cal.views import _get_day_dates

        expect = [datetime.date(2011, 7, 11),
                  datetime.date(2011, 7, 12),
                  datetime.date(2011, 7, 13),
                  datetime.date(2011, 7, 14),
                  datetime.date(2011, 7, 15),
                  datetime.date(2011, 7, 16),
                  datetime.date(2011, 7, 17)]
        eq_(_get_day_dates(datetime.date(2011, 7, 13)), expect)
        eq_(_get_day_dates(datetime.date(2011, 7, 11)), expect)
        eq_(_get_day_dates(datetime.date(2011, 7, 16)), expect)
        eq_(_get_day_dates(datetime.date(2011, 7, 17)), expect)

        expect = [datetime.date(2011, 7, 10),
                  datetime.date(2011, 7, 11),
                  datetime.date(2011, 7, 12),
                  datetime.date(2011, 7, 13),
                  datetime.date(2011, 7, 14),
                  datetime.date(2011, 7, 15),
                  datetime.date(2011, 7, 16)]
        eq_(_get_day_dates(datetime.date(2011, 7, 13), True), expect)
        eq_(_get_day_dates(datetime.date(2011, 7, 11), True), expect)
        eq_(_get_day_dates(datetime.date(2011, 7, 16), True), expect)
        eq_(_get_day_dates(datetime.date(2011, 7, 10), True), expect)

    def test_get_month_options(self):
        from cal.views import _get_month_options
        # first create a tonne of slots
        names = ('tom', 'dick', 'harry')
        for username in names:
            User.objects.create_user(
              username,
              '%s@mozilla.com' % username,
              password='secret',
            )
        date = datetime.date(2011, 6, 1)
        one_day = datetime.timedelta(days=1)
        c = 0
        while date < (datetime.date(2011, 9, 1) - one_day):
            Slot.objects.create(
              user=User.objects.get(username=names[c % len(names)]),
              date=date,
            )
            date += one_day
            c += 1

        options = _get_month_options(2011, 7, 0, weeks=4)
        assert len(options) == 3

        item = options[0]
        eq_(item.label, '2011 June')
        eq_(item.value, '2011,06')
        ok_(not item.today_month)
        ok_(not item.current)

        item = options[1]
        eq_(item.label, '2011 July')
        eq_(item.value, '2011,07')
        ok_(item.today_month)
        ok_(item.current)

        item = options[2]
        eq_(item.label, '2011 August')
        eq_(item.value, '2011,08')
        ok_(not item.today_month)
        ok_(not item.current)
