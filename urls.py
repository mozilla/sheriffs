from django.conf import settings
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^users/', include('users.urls')),
    (r'^roster/', include('roster.urls')),
    (r'^vcal/', include('vcal.urls')),
    (r'', include('cal.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)

from tastypie.api import Api
from roster.api import SlotResource, TodayResource, TomorrowResource
from django.http import HttpResponseRedirect
from django.views.generic.simple import redirect_to

v1_api = Api(api_name='v1')
v1_api.register(SlotResource())
v1_api.register(TodayResource())
v1_api.register(TomorrowResource())

urlpatterns += patterns('',
    (r'^api/', include(v1_api.urls)),
#    (r'^api/', lambda x: HttpResponseRedirect('/roster/api/documentation/')),
    (r'^api/$', redirect_to, {'url': '/roster/api/documentation/'}),
)


handler404 = 'cal.views.handler404'

## In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    # Remove leading and trailing slashes so the regex matches.
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )


## Monkey patches

# Monkey-patch django forms to avoid having to use Jinja2's |safe everywhere.
import safe_django_forms
safe_django_forms.monkeypatch()
