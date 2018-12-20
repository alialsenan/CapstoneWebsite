from django.conf.urls import url
from . import views

app_name = 'vehicle'
urlpatterns = [
    url(r'^upload/path/(?P<path_name>\w+)/?$', views.set_waypoints, name='set_waypoints'),
    url(r'^upload/location$', views.set_location, name='set_location'),
    url(r'^upload/status$', views.set_status, name='set_status'),
    url(r'^task/$', views.get_task, name='get_task'),
    url(r'^login/$', views.car_login, name='car_login'),
    url(r'^path/(?P<path_name>\w+)/?$', views.get_waypoints, name='get_path'),
]
