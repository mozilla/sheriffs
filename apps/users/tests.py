import re
from urlparse import urlparse
import datetime
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import REDIRECT_FIELD_NAME
from nose.tools import eq_, ok_

class UsersTest(TestCase):

    def test_login(self):
        url = reverse('users.login')
        response = self.client.get(url)
        eq_(response.status_code, 200)

        mortal = User.objects.create(
          username='mortal',
          first_name='Mortal',
          last_name='Joe'
        )
        mortal.set_password('secret')
        mortal.save()

        response = self.client.post(url, {'username': 'mortal',
                                          'password': 'wrong'})
        eq_(response.status_code, 200)
        ok_('errorlist' in response.content)

        response = self.client.post(url, {'username': 'mortal',
                                          'password': 'secret'})
        eq_(response.status_code, 302)
        path = urlparse(response['location']).path
        eq_(path, settings.LOGIN_REDIRECT_URL)

        response = self.client.get('/')
        eq_(response.status_code, 200)
        ok_('Mortal' in response.content)

        url = reverse('users.logout')
        response = self.client.get(url)
        eq_(response.status_code, 302)
        path = urlparse(response['location']).path
        eq_(path, settings.LOGOUT_REDIRECT_URL)

        response = self.client.get('/')
        eq_(response.status_code, 200)
        ok_('Mortal' not in response.content)

    def _get_all_inputs(self, html):
        _input_regex = re.compile('<input (.*?)>', re.M|re.DOTALL)
        _attrs_regex = re.compile('(\w+)="([^"]+)"')
        all_attrs = {}
        for input in _input_regex.findall(html):
            attrs = dict(_attrs_regex.findall(input))
            all_attrs[attrs.get('name', attrs.get('id', ''))] = attrs
        return all_attrs

    def test_login_next_redirect(self):
        url = reverse('users.login')
        response = self.client.get(url, {'next':'/foo/bar'})
        eq_(response.status_code, 200)
        attrs = self._get_all_inputs(response.content)
        ok_(attrs[REDIRECT_FIELD_NAME])
        eq_(attrs[REDIRECT_FIELD_NAME]['value'], '/foo/bar')

        mortal = User.objects.create_user(
          'mortal', 'mortal', password='secret'
        )
        mortal.set_password('secret')
        mortal.save()

        response = self.client.post(url, {'username': 'mortal',
                                          'password': 'secret',
                                          'next': '/foo/bar'})
        eq_(response.status_code, 302)
        path = urlparse(response['location']).path
        eq_(path, '/foo/bar')


    def test_login_rememberme(self):
        url = reverse('users.login')
        mortal = User.objects.create(
          username='mortal',
          first_name='Mortal',
          last_name='Joe'
        )
        mortal.set_password('secret')
        mortal.save()

        response = self.client.post(url, {'username': 'mortal',
                                          'password': 'secret',
                                          'rememberme': 'yes'})
        eq_(response.status_code, 302)
        expires = self.client.cookies['sessionid']['expires']
        date = expires.split()[1]
        then = datetime.datetime.strptime(date, '%d-%b-%Y')
        today = datetime.datetime.today()
        days = settings.SESSION_COOKIE_AGE / 24 / 3600
        eq_((then - today).days + 1, days)


    def test_login_by_email(self):
        url = reverse('users.login')

        mortal = User.objects.create(
          username='mortal',
          email='mortal@hotmail.com',
          first_name='Mortal',
          last_name='Joe'
        )
        mortal.set_password('secret')
        mortal.save()

        response = self.client.post(url, {'username': 'Mortal@hotmail.com',
                                          'password': 'secret'})
        eq_(response.status_code, 302)

        response = self.client.get('/')
        eq_(response.status_code, 200)
        ok_('Mortal' in response.content)
