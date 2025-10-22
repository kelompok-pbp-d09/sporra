from main.models import Event
from main.forms import EventForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.core import serializers
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.utils import timezone

# Create your views here.
def home_event(request):
    current_time = timezone.localtime(timezone.now())
    category = request.GET.get("category")
    if category:
        events = Event.objects.filter(category=category)
    else:
        events = Event.objects.all()

    upcoming_events = events.filter(date__gte=current_time).order_by("date")
    past_events = events.filter(date__lt=current_time).order_by("-date")

    context = {
        "categories": Event.CATEGORY_CHOICES,
        "current_category": category,
        "upcoming_events": upcoming_events,
        "past_events": past_events,
    }
    return render(request, "home_event.html", context)

def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    event.increment_views()
    event_time = event.date
    if timezone.is_naive(event_time):
        print("[LANGKAH 2] Waktu terdeteksi 'NAIVE', diubah menjadi UTC.")
        event_time = timezone.make_aware(event_time, timezone.utc)

    current_time_utc = timezone.now()
    has_ended = event_time < current_time_utc

    context = {
        'event': event,
        'has_ended': has_ended,
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

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Event berhasil diperbarui!")
            return redirect('main:home_event')
    else:
        local_time = timezone.localtime(event.date)
        formatted_date = local_time.strftime("%d %B %Y %H.%M")
        form = EventForm(instance=event, initial={'date': formatted_date})

    context = {'form': form, 'event': event}
    return render(request, 'edit_event.html', context)
