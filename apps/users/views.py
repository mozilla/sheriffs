import logging
from django import http
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
import django.contrib.auth.views
from django.conf import settings
import jingo
import forms
from models import get_user_profile
from django.shortcuts import render_to_response as django_render_to_response


#@anonymous_csrf
def login(request):
    # mostly copied from zamboni
    logout(request)

    #if 'to' in request.GET:
    #    request = _clean_next_url(request)

    from monkeypatch_template_engine import jinja_for_django as jfd
    django.contrib.auth.views.render_to_response = jfd
    r = django.contrib.auth.views.login(request,
                         template_name='users/login.html',
                         redirect_field_name=REDIRECT_FIELD_NAME,
                         authentication_form=forms.AuthenticationForm)

    if isinstance(r, http.HttpResponseRedirect):
        # Succsesful log in according to django. Now we do our checks. I do
        # the checks here instead of the form's clean() because I want to use
        # the messages framework and it's not available in the request there
        user = get_user_profile(request.user)
        rememberme = request.POST.get('rememberme', None)
        if rememberme:
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            logging.debug((u'User (%s) logged in successfully with '
                                        '"remember me" set') % user)

    return r


def logout(request):
    django.contrib.auth.views.render_to_response = django_render_to_response
    django.contrib.auth.views.logout(request)
    #if 'to' in request.GET:
    #    request = _clean_next_url(request)
    next = request.GET.get('next') or settings.LOGOUT_REDIRECT_URL
    response = http.HttpResponseRedirect(next)
    return response


@login_required
def settings_page(request):
    data = {}
    return jingo.render(request, 'users/settings.html', data)