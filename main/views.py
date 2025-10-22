from main.models import Event
from main.forms import EventForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.core import serializers
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
import datetime
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags

# Create your views here.
def home_event(request):
    event_list = Event.objects.all()
    context = {
        'event_list': event_list
    }
    return render(request, 'home_event.html', context)

def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    event.increment_views()
    context = {
        'event': event
    }
    return render(request, 'event_detail.html', context)

def create_event(request):
    form = EventForm(request.POST or None, request.FILES or None)
    if form.is_valid() and request.method == "POST":
        event_entry = form.save(commit=False)
        event_entry.user = request.user if request.user.is_authenticated else None
        event_entry.save()
        return redirect('main:home_event')
    context = {'form': form}
    return render(request, 'create_event.html', context)

def edit_event(request, id):
    event = get_object_or_404(Event, pk=id)
    form = EventForm(request.POST or None, request.FILES or None, instance=event)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('main:home_event')
    context = {
        'form': form
    }
    return render(request, 'main/edit_event.html', context)
