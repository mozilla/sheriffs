from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
   url('^login/', views.login, name='users.login'),
   url('^logout/', views.logout, name='users.logout'),
   url('^settings/', views.settings_page, name='users.settings'),
)