from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from flintstone.models import Car, GeoPath, Profile
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.geos import LineString, Point
import json

global user

# Retrieve and validate the current user's profile. Do not use as a view.
def get_car_from_user(user):
    # From user, get the profile
    car = Car.objects.filter(car_account__id = user.id)

    # Only expecting one profile per vehicle
    print("NUMBER OF CARS",len(car))
    if len(car) == 1:
        return car[0]
    return None

@csrf_exempt
def car_login(request):
    global user
    if 'username' in request.POST and 'password' in request.POST:
        username = request.POST['username']
        password = request.POST['password']
            
        # Check if the user is in the database
        user = authenticate(request, username=username, password=password)

        # Check if there is a car connected to the user
        if user != None and get_car_from_user(user) != None:
            login(request, user)
            return HttpResponse("success")
        
    return HttpResponse("failure")  

#@login_required
@csrf_exempt         
def set_waypoints(request, path_name):
    global user
    print("INSETWAYPOINT")
    # Parse JSON
    waypoints_set = json.loads(request.body.decode("utf-8"))

    if 'points' in waypoints_set:
        # Get matching paths
        paths = GeoPath.objects.filter(display_name = path_name)

        if len(paths) >= 1:
            # Update path
            target_path = paths[0]
        else:
            # Create a new geopath
            target_path = GeoPath()
            target_path.display_name = path_name

        # Update the points and save
        target_path.points = LineString(tuple(waypoints_set['points']))
        target_path.save()

        return HttpResponse("success")
        
    return HttpResponse("failure")

@csrf_exempt
#@login_required#FIXME 
def get_waypoints(request, path_name):
    global user
    print("GETWAYPOINTS")
    response = {
        'name': None,
        'points': None,
    }

    # Only cars can request paths
    if get_car_from_user(user) != None:

        # Get matching paths
        paths = GeoPath.objects.filter(display_name = path_name)

        if len(paths) >= 1:

            path = paths[0]

            # Update path
            response['name'] = path.display_name
            response['points'] = path.points[:]

    return JsonResponse(response)

@csrf_exempt
#@login_required
def set_location(request):
    # Parse JSON
    print("Updating Cart Postition")
    location = json.loads(request.body.decode("utf-8"))

    related_car = get_car_from_user(request.user)

    if 'point' in location and related_car != None:
        # Update the points and save
        related_car.car_position = Point(location['point'])
        related_car.save()
        return HttpResponse("success")

    return HttpResponse("failure")

@csrf_exempt
#@login_required#FIXME
def set_status(request):
    global user
    # Parse JSON
    status = json.loads(request.body.decode("utf-8"))

    related_car = get_car_from_user(user)
    
    if 'status' in status and related_car != None:
        # Update the points and save
        profiles = Profile.objects.filter(current_car = related_car)

        # Update for all the people in the car
        for prf in profiles:
            prf.user_state = status['status']
            prf.save()

        return HttpResponse("success")

    return HttpResponse("failure")

#@login_required #FIXME
def get_task(request):
    global user
    car = get_car_from_user(user)#request.user)
    
    # Retrieve the position of the POI the user is going to
    destination_loc = list(car.destination.location.coords)

    # Retrieve the position of the POI the user is coming from
    start_loc = list(car.start.location.coords)

    profiles = Profile.objects.filter(current_car = car)

    # Update for all the people associated with the car
    rider_waiting = False
    for prf in profiles:
        if prf.user_state == 'w':
            rider_waiting = True

    response = { 
        'destination': destination_loc, 
        'start': start_loc,
        'rider_waiting': rider_waiting,
    }

    # Generate and return JSON
    return JsonResponse(response)
