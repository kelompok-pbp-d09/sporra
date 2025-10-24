from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.template.defaultfilters import date as date_filter
from event.models import Event
from event.forms import EventForm
from ticketing.models import Ticket

def home_event(request):
    current_time = timezone.localtime(timezone.now())
    category = request.GET.get("category")

    if category:
        events = Event.objects.filter(kategori=category)
    else:
        events = Event.objects.all()

    upcoming_events = events.filter(date__gte=current_time).order_by('date')
    past_events = events.filter(date__lt=current_time).order_by("-date")
    form = EventForm()

    context = {
        "categories": Event.CATEGORY_CHOICES,
        "current_category": category,
        "upcoming_events": upcoming_events,
        "past_events": past_events,
        "form": form,
    }
    return render(request, "home_event.html", context)

def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    event.increment_views()

    event_time = event.date
    if timezone.is_naive(event_time):
        event_time = timezone.make_aware(event_time, timezone.utc)

    current_time_utc = timezone.now()
    has_ended = event_time < current_time_utc

    tickets = Ticket.objects.filter(event=event)

    context = {
        'event': event,
        'has_ended': has_ended,
        'tickets': tickets,
    }
    return render(request, 'event_detail.html', context)

def create_event(request):
    form = EventForm(request.POST or None, request.FILES or None)
    
    if request.method == "POST":
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if form.is_valid():
            event_entry = form.save(commit=False)
            event_entry.user = request.user if request.user.is_authenticated else None
            event_entry.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('event:home_event'),
                    'message': 'Acara berhasil dibuat!'
                })
            messages.success(request, 'Acara berhasil dibuat!')
            return redirect('event:home_event')
        else:
            if is_ajax:
                errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors})

    context = {'form': form}
    return render(request, 'create_event.html', context)

def edit_event(request, id):
    event = get_object_or_404(Event, id=id)

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({
                "success": False,
                "errors": form.errors
            }, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

def delete_event(request, id):
    event = get_object_or_404(Event, pk=id)
    event.delete()
    return HttpResponseRedirect(reverse('event:home_event'))

def get_event_ajax(request, id):
    event = get_object_or_404(Event, id=id)

    try:
        local_time = timezone.localtime(event.date)
        bulan_indo = {
            1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
            5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
        }
        
        formatted_date = f"{local_time.day} {bulan_indo[local_time.month]} {local_time.year} {local_time.strftime('%H.%M')}"
        
        initial_data = {
            'judul': event.judul,
            'deskripsi': event.deskripsi,
            'lokasi': event.lokasi,
            'kategori': event.kategori,
            'date': formatted_date
        }

        form = EventForm(initial=initial_data)
        
        form_html_parts = []
        for field in form:
            help_text_html = ''
            if field.help_text:
                help_text_html = f'<p class="mt-1.5 text-xs text-gray-400">{field.help_text}</p>'
            
            errors_html = ''
            if field.errors:
                error_items = ''.join([f'<p>{error}</p>' for error in field.errors])
                errors_html = f'<div class="field-errors text-sm text-red-400 mt-1">{error_items}</div>'

            field_html = f'''
            <div class="mb-4">
                <label for="{field.id_for_label}" class="block text-sm font-medium text-gray-300 mb-2">
                    {field.label}
                </label>
                <div class="w-full">{field}</div>
                {help_text_html}
                {errors_html}
            </div>
            '''
            form_html_parts.append(field_html)
        
        form_html = ''.join(form_html_parts)

        return JsonResponse({
            'success': True,
            'form_html': form_html,
        })
    except Exception as e:
        import logging
        logging.error(f"Error in get_event_ajax: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

def get_events_ajax(request):
    category = request.GET.get('category', '')
    now = timezone.now()
    queryset = Event.objects.all()

    if category:
        queryset = queryset.filter(kategori=category)

    upcoming_events = queryset.filter(date__gte=now).order_by('date')
    past_events = queryset.filter(date__lt=now).order_by('-date')

    def serialize_event(event):
        local_date = timezone.localtime(event.date)
        return {
            'id': str(event.id),
            'judul': event.judul,
            'lokasi': event.lokasi,
            'kategori_display': event.get_kategori_display(),
            'date_formatted': date_filter(local_date, "d M Y, H:i"),
            'detail_url': reverse('event:event_detail', args=[event.id]),
            'user_id': event.user.id if event.user else None
        }

    return JsonResponse({
        'upcoming_events': [serialize_event(e) for e in upcoming_events],
        'past_events': [serialize_event(e) for e in past_events],
    })