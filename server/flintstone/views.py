from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import logging, json

from .models import Profile, GeoPath, GeoPOI

def manage_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('flintstone:index'))

# Retrieve and validate the current user's profile. Do not use as a view.
def get_user_profile(request):
    # From user, get the profile
    profile = Profile.objects.filter(user__id = request.user.id)

    # Only expecting one profile per user
    if len(profile) == 1:
        return profile[0]

    return manage_logout(request)

def index(request):
    if not request.user.is_authenticated:
        context = {}
        return render(request, 'flintstone/login.html', context)
    else:
        # Don't allow the user to login twice
        return HttpResponseRedirect(reverse('flintstone:map'))

def login_handler(request):
    if 'username' in request.POST and 'password' in request.POST:
        username = request.POST['username']
        password = request.POST['password']

        # Check if the user is in the database
        user = authenticate(request, username=username, password=password)

        # Check if the user is in the database
        if user is not None:
            # Log in the user
            login(request, user)
            return HttpResponseRedirect(reverse('flintstone:map'))
        else:
            # Return an 'invalid login' error message.
            context = {'error_message': 'Username or password is incorrect.'}
            return render(request, 'flintstone/login.html', context)
    else:
        return HttpResponseRedirect(reverse('flintstone:index'))

@login_required 
def map(request):
    context = {}
    return render(request, 'flintstone/basemap.html', context)

@login_required         
def set_ride_form(request):
    # From user, get the profile
    profile = get_user_profile(request)

    # Update user state
    profile.user_state = 'r'
    profile.save()

    # From the profile.path, get points of interest
    poi = GeoPOI.objects.filter(path = profile.path)

    print(poi)

    context = {
        'poi': poi,
    }

    return render(request, 'flintstone/set_ride.html', context)

@login_required
@csrf_exempt         
def set_ride(request):
    # From user, get the profile
    profile = get_user_profile(request)

    response = {
        'status': 'ok',
    }

    ride_request = json.loads(request.body.decode("utf-8"))

    if 'start' in ride_request and 'destination' in ride_request:
        # Parse JSON
        if ride_request['destination'] != ride_request['start']:

            # Determine if the start and destinations exist
            try:
                destination = GeoPOI.objects.get(pk=ride_request['destination'])
                start = GeoPOI.objects.get(pk=ride_request['start'])

                # What other users are using the car?
                profiles = Profile.objects.filter(current_car = profile.current_car)

                has_to_wait = False

                # Update for all the people in the car
                for prf in profiles:
                    if prf.user_state != 'r' and prf != profile:
                        # Setup Error Response
                        response = {
                            'status': 'error',
                            'error_message':'Another user is riding. Please wait until they arrive.',
                        }
                        has_to_wait = True

                if not has_to_wait:
                    # Update the goals of the current car
                    profile.current_car.destination = destination
                    profile.current_car.start = start
                    profile.current_car.save()

                    # Update user profile
                    profile.user_state = 'w'
                    profile.save()

            except GeoPOI.DoesNotExist:
                # Setup Error Response
                response = {
                    'status': 'error',
                    'error_message':'Unable to start trip. <br>Perhaps try refreshing?',
                }
        else:
            # Setup Error Response
            response = {
                'status': 'error',
                'error_message':'Please change the destination or start. <br> (they should not match)',
            }
    else:
        response = {
            'status': 'error',
            'error_message':'Unable to parse request.',
        }

    return JsonResponse(response)

@login_required
def path(request):
    profile = get_user_profile(request)
    
    # Retrieve the position of the POI the user is going to
    destination_loc = list(profile.current_car.destination.location.coords)

    # Retrieve the position of the POI the user is coming from
    start_loc = list(profile.current_car.start.location.coords)

    response = {
        'points':profile.path.points[:], 
        'destination_loc':destination_loc, 
        'start_loc':start_loc,
    }

    # Generate and return JSON
    return JsonResponse(response)

@login_required         
def status(request):
    profile = get_user_profile(request)
    context = dict()

    context['user_state'] = profile.user_state

    if profile.user_state == 'w':
        if profile.current_car != None:
            context['car_location'] =  list(profile.current_car.car_position.coords) 
        else:
            context['car_location'] = None
        
        context['wait_time'] = profile.wait_time
    
    return JsonResponse(context)

@login_required         
def wait(request):
    context = {}
    return render(request, 'flintstone/wait.html', context)

@login_required         
def arrived(request):
    context = {}
    return render(request, 'flintstone/arrived.html', context)
