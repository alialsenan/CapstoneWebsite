from django.conf.urls import url
from . import views

app_name = 'flintstone'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login_handler$', views.login_handler, name='login_handler'),
    url(r'^logout/$', views.manage_logout, name='logout'),
    url(r'^map/$', views.map, name='map'),
    url(r'^map/set_ride_form/', views.set_ride_form, name='set_ride_form'),
    url(r'^map/set_ride/', views.set_ride, name='set_ride'),
    url(r'^map/currentpath/', views.path, name='path'),
    url(r'^map/status/', views.status, name='status'),
    url(r'^map/wait/', views.wait, name='wait'),
    url(r'^map/arrived/', views.arrived, name='arrived'),
]
