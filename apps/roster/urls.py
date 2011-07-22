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

from django.conf.urls.defaults import patterns, url
import views

urlpatterns = patterns('',
    url(r'^initialize/$', views.initialize, name='roster.initialize'),
    url(r'^replace/$', views.replace, name='roster.replace'),
    url(r'^slot/(?P<pk>\d+)/replace/$', views.replace_slot,
        name='roster.replace_slot'),
    url(r'^info.json$', views.info_json, name='roster.info_json'),
    url(r'^swap/offer/$', views.offer_swap, name='roster.offer_swap'),
    url(r'^swap/request/$', views.request_swap, name='roster.request_swap'),
    url(r'^(?P<uuid>\w{32})/accept/$', views.accept_swap,
        name='roster.accept_swap'),
    url(r'^(?P<uuid>\w{32})/decline/$', views.decline_swap,
        name='roster.decline_swap'),
    url(r'^api/documentation/$', views.api_documentation,
        name='roster.api_documentation'),
    url(r'^widget/$', views.widget_factory, name='roster.widget_factory'),
    url(r'^$', views.index, name='roster.index'),
)
