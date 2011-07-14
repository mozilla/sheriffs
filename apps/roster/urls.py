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
