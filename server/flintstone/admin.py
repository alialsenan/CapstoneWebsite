from django.contrib import admin

from .models import Car, GeoPath, GeoPOI, Profile

admin.site.register(Car)
admin.site.register(GeoPath)
admin.site.register(GeoPOI)
admin.site.register(Profile)
