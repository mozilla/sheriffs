from django.test import TestCase
from django.core.urlresolvers import reverse
from nose.tools import eq_, ok_

class CalTest(TestCase):

    def test_render_home_page(self):
        """Render the '/' view"""
        url = reverse('cal.views.home')
        response = self.client.get(url)
        eq_(response.status_code, 200)
