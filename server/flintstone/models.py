from django.contrib.gis.db import models
from django.forms import fields
from django.contrib.auth.models import User

# Profile of the current user
class Profile(models.Model):
    # The authentication model of the user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # The current path the user is waiting beside
    path = models.ForeignKey('GeoPath', on_delete=models.SET_NULL, null=True)

    # Car the user is currently within (null if user is not in a car)
    current_car = models.ForeignKey('Car', on_delete=models.SET_NULL, null=True, blank=True)

    # Estimated time of arrival of current car in seconds
    wait_time = models.PositiveIntegerField(default=0)

    USER_STATES = (
        ('r', 'Ride Request (Not active)'),
        ('w', 'Waiting for ride'),
        ('a', 'Car has arrived'),
        ('p', 'User is passenger'),
    )
    
    # User state
    user_state = models.CharField(max_length=1, choices=USER_STATES, blank=True, default='r')

    def __str__(self):
        return self.user.username

# Defines a path which one or more cars can follow
class GeoPath(models.Model):
    
    display_name = models.CharField(max_length=200, null=True, default="Unknown")

    # Stores the points in EPSG:4326
    points = models.LineStringField(null=True)

    def __str__(self):
        return self.display_name

# Point of interest along a path
class GeoPOI(models.Model):
    verbose_name = "POI"
    location = models.PointField()
    display_name = models.CharField(max_length=200, null=True, default="POI")

    # The path which the POI is along
    path = models.ForeignKey(GeoPath, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.display_name + ':' + str(self.location) 

# A car model represents the current state of the car such as which passenger
# is occupying the car, their destination, and the car's current route
class Car(models.Model):
    display_name = models.CharField(max_length=200, null=True, default="Unknown")

    # Location to drop off the passenger
    destination = models.ForeignKey(GeoPOI, on_delete=models.SET_NULL, null=True, related_name='poi_destination')

    # Location to pick up the passenger
    start = models.ForeignKey(GeoPOI, on_delete=models.SET_NULL, null=True, related_name='poi_start')

    # Current position of the car
    car_position = models.PointField()

    # The path/network which the car is able to navigate
    path = models.ForeignKey(GeoPath, on_delete=models.SET_NULL, null=True)

    # The car has an associated account to authenicate cars which log in
    car_account = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.display_name
