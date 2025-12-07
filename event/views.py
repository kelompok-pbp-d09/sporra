from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.template.defaultfilters import date as date_filter
from event.models import Event
from event.forms import EventForm
from ticketing.models import Ticket
from django.contrib.auth.decorators import login_required
from django.utils.html import strip_tags
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
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

@csrf_exempt
def delete_event(request, id):
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return JsonResponse({'status': 'success', 'message': 'Event berhasil dihapus!'}, status=200)
    return JsonResponse({'status': 'error', 'message': 'Metode tidak diizinkan'}, status=405)

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
            'deskripsi': event.deskripsi,
            'lokasi': event.lokasi,
            'kategori': event.kategori,
            'kategori_display': event.get_kategori_display(),
            'date_formatted': date_filter(local_date, "d M Y, H:i"),
            'detail_url': reverse('event:event_detail', args=[event.id]),
            'user_id': event.user.id if event.user else None,
            'username': event.user.username if event.user else 'Anonymous',
        }

    return JsonResponse({
        'upcoming_events': [serialize_event(e) for e in upcoming_events],
        'past_events': [serialize_event(e) for e in past_events],
        'current_user_id': request.user.id if request.user.is_authenticated else None,
    })

@csrf_exempt
def create_event_flutter(request):
    if request.method == 'POST':
        if request.POST:
            data = request.POST
        else:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"status": "error", "message": "Invalid JSON data"}, status=400)

        judul = strip_tags(data.get("judul", ""))
        lokasi = strip_tags(data.get("lokasi", ""))
        kategori = data.get("kategori", "lainnya")
        deskripsi = strip_tags(data.get("deskripsi", ""))
        date = data.get("date", "")
        bulan_map = {
            "januari": "January", "februari": "February", "maret": "March",
            "april": "April", "mei": "May", "juni": "June", "juli": "July",
            "agustus": "August", "september": "September", "oktober": "October",
            "november": "November", "desember": "December"
        }

        date_str = date.lower()
        for indo, eng in bulan_map.items():
            if indo in date_str:
                date_str = date_str.replace(indo, eng)
                break

        parsed_date = None
        for fmt in ["%d %B %Y %H.%M", "%d %B %Y %H:%M"]:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        if not parsed_date:
            return JsonResponse({
                "status": "error",
                "message": f"Format tanggal salah: {date}. Gunakan format: 12 Juli 2025 15.00"
            }, status=400)

        if timezone.is_naive(parsed_date):
            parsed_date = timezone.make_aware(parsed_date)
        
        # --- Simpan Data ---
        try:
            new_event = Event(
                judul=judul,
                lokasi=lokasi,
                kategori=kategori,
                deskripsi=deskripsi,
                date=parsed_date,
                user=request.user if request.user.is_authenticated else None
            )
            new_event.save()
            
            return JsonResponse({"status": "success", "message": "Acara berhasil dibuat!"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=401)

@csrf_exempt
def edit_event_flutter(request, id):
    if request.method == 'POST':
        try:
            event = Event.objects.get(pk=id)
        except Event.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event tidak ditemukan'}, status=404)

        if event.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Anda tidak memiliki izin mengedit event ini'}, status=403)

        if request.POST:
            data = request.POST
        else:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"status": "error", "message": "Invalid JSON data"}, status=400)

        judul = strip_tags(data.get("judul", ""))
        lokasi = strip_tags(data.get("lokasi", ""))
        kategori = data.get("kategori", "lainnya")
        deskripsi = strip_tags(data.get("deskripsi", ""))
        date = data.get("date", "")

        bulan_map = {
            "januari": "January", "februari": "February", "maret": "March",
            "april": "April", "mei": "May", "juni": "June", "juli": "July",
            "agustus": "August", "september": "September", "oktober": "October",
            "november": "November", "desember": "December",
            
            "jan": "January", "feb": "February", "mar": "March",
            "apr": "April", "mei": "May", "jun": "June", "jul": "July",
            "agu": "August", "agt": "August", "sep": "September", "okt": "October", 
            "nov": "November", "des": "December",
        }

        date_str = date.lower().replace(',', '')
        
        for indo, eng in bulan_map.items():
            if indo in date_str:
                date_str = date_str.replace(indo, eng)
                break

        parsed_date = None
        for fmt in ["%d %B %Y %H.%M", "%d %B %Y %H:%M"]:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        if not parsed_date:
            return JsonResponse({
                "status": "error",
                "message": f"Format tanggal salah: {date}. Gunakan format: 12 Juli 2025 15.00"
            }, status=400)

        if timezone.is_naive(parsed_date):
            parsed_date = timezone.make_aware(parsed_date)
        
        try:
            event.judul = judul
            event.lokasi = lokasi
            event.kategori = kategori
            event.deskripsi = deskripsi
            event.date = parsed_date
            event.save()
            
            return JsonResponse({"status": "success", "message": "Acara berhasil diperbarui!"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=401)