from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Ticket, Booking
from .forms import BookingForm, TicketForm ,TicketSelectionForm
from event.models import Event
from django.db import IntegrityError  
from django.urls import reverse
import json


@login_required
def book_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = TicketSelectionForm(request.POST, event=event)

        if form.is_valid():
            ticket = form.cleaned_data['ticket']
            quantity = form.cleaned_data['quantity']

            if quantity > ticket.available:
                msg = f'Maaf, stok tiket {ticket.get_ticket_type_display()} hanya tersisa {ticket.available}.'
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': msg})
                messages.error(request, msg)

            elif quantity <= 0:
                msg = 'Jumlah tiket harus lebih dari 0.'
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': msg})
                messages.error(request, msg)

            else:
                booking, created = Booking.objects.get_or_create(
                    user=request.user,
                    ticket=ticket,
                    defaults={'quantity': 0, 'total_price': 0}
                )

                booking.quantity += quantity
                booking.total_price = ticket.price * booking.quantity
                booking.save()

                ticket.available -= quantity
                ticket.save()

                msg = (
                    'Tiket berhasil dipesan!' if created
                    else f'Jumlah tiket diperbarui. Sekarang kamu punya {booking.quantity}.'
                )

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': msg,
                        'redirect_url': reverse('event:home_event')
                    })
                
                messages.success(request, msg)
                return redirect('event:home_event')

        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Form tidak valid'})

    else:
        form = TicketSelectionForm(event=event)

    return render(request, 'book_ticket.html', {'event': event, 'form': form})

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('ticket__event')
    return render(request, "my_bookings.html", {"bookings": bookings})

def all_tickets(request):
        tickets = Ticket.objects.select_related('event').all()
        return render(request, "all_tickets.html", {"tickets": tickets})

def get_tickets_ajax(request):
    tickets = Ticket.objects.select_related('event').all()
    data = []
    for t in tickets:
        can_edit = False
        if request.user.is_authenticated:
            try:
                can_edit = request.user == t.event.user or request.user.userprofile.is_admin
            except:
                can_edit = request.user == t.event.user
        
        data.append({
            "id": t.id,
            "event_title": t.event.judul,
            "ticket_type": t.get_ticket_type_display(),
            "price": float(t.price),
            "available": t.available,
            "event_id": t.event.id,
            "can_edit": can_edit,
        })
    return JsonResponse({"tickets": data})

@login_required
def create_ticket(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error':'Invalid JSON'}, status=400)

        event_id = data.get('event')
        ticket_type = data.get('ticket_type')
        price = data.get('price')
        available = data.get('available')

        if not all([event_id, ticket_type, price, available]):
            return JsonResponse({'error':'Missing fields'}, status=400)

        # Ambil event
        try:
            if request.user.userprofile.is_admin:
                event = Event.objects.get(id=event_id)
            else:
                event = Event.objects.get(id=event_id, user=request.user)
        except Event.DoesNotExist:
            return JsonResponse({'error':'Event not found or forbidden'}, status=403)

        ticket = Ticket.objects.create(
            event=event,
            ticket_type=ticket_type,
            price=price,
            available=available
        )

        return JsonResponse({
            'success': True,
            'ticket': {
                'id': ticket.id,
                'event_title': ticket.event.judul,
                'ticket_type': ticket.get_ticket_type_display(),
                'price': float(ticket.price),
                'available': ticket.available,
                'event_id': ticket.event.id,
                'can_edit': True
            }
        })


@login_required
def get_my_bookings_ajax(request):
    bookings = Booking.objects.filter(user=request.user).select_related('ticket__event')
    data = []

    for b in bookings:
        data.append({
            "event_id": b.ticket.event.id,
            "event_title": b.ticket.event.judul,
            "date": b.ticket.event.date.strftime("%d %b %Y") if b.ticket.event.date else "-",
            "location": b.ticket.event.lokasi or "Lokasi belum ditentukan",
            "quantity": b.quantity,
            "total_price": int(b.total_price),
            "booked_at": b.booked_at.strftime("%d %b %Y, %H:%M") if b.booked_at else "-",
            "event_url": reverse('event:event_detail', args=[b.ticket.event.id])  # ← TAMBAHKAN BARIS INI
        })

    return JsonResponse({"bookings": data})

@login_required
def edit_ticket_ajax(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if not (request.user == ticket.event.user or request.user.userprofile.is_admin):
        return JsonResponse({'error':'Forbidden'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error':'Invalid JSON'}, status=400)

        ticket.ticket_type = data.get('ticket_type', ticket.ticket_type)
        ticket.price = data.get('price', ticket.price)
        ticket.available = data.get('available', ticket.available)
        ticket.save()

        return JsonResponse({'success': True})
    
@login_required
def delete_ticket_ajax(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if not (request.user == ticket.event.user or request.user.userprofile.is_admin):
        return JsonResponse({"error": "Forbidden"}, status=403)
    if request.method == "POST":
        ticket.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid method"}, status=405)