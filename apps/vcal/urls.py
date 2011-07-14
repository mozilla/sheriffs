from django.conf.urls.defaults import patterns, url
import views

urlpatterns = patterns('',
    url(r'^vcal/$', views.vcal, name='vcal.vcal'),
    url(r'^My-Sheriff-duty.ics$', views.my_dates, name='vcal.my_dates'),
    url(r'^Sheriff-Duty.ics$', views.all_dates, name='vcal.all_dates'),
)
