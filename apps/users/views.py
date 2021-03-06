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

from django import http
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
import django.contrib.auth.views
from django.conf import settings
from django.shortcuts import render
import forms
from session_csrf import anonymous_csrf


@anonymous_csrf
def login(request):
    logout(request)

    return django.contrib.auth.views.login(request,
                     template_name='users/login.html',
                     redirect_field_name=REDIRECT_FIELD_NAME,
                     authentication_form=forms.AuthenticationForm)


def logout(request):
    auth_logout(request)
    next = request.GET.get('next') or settings.LOGOUT_REDIRECT_URL
    response = http.HttpResponseRedirect(next)
    return response


@transaction.commit_on_success
@login_required
def settings_page(request):
    data = {}
    if request.method == 'POST':
        form = forms.SettingsForm(user=request.user, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            request.user.username = username
            request.user.save()

            messages.info(
              request,
              "Username changed to %s" % username
            )
            return redirect(reverse('cal.home'))

    else:
        initial = {'username': request.user.username}
        form = forms.SettingsForm(user=request.user, initial=initial)

    data['form'] = form
    return render(request, 'users/settings.html', data)
