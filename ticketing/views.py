import json
from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt  # <--- WAJIB untuk API Mobile
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.db import IntegrityError

from .models import Ticket, Booking
from .forms import TicketSelectionForm
from event.models import Event

# ==============================================================================
#  PART 1: BOOKING TICKET (User Buys Ticket)
# ==============================================================================

@csrf_exempt  
def book_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        
        # Insert POST data into form
        form = TicketSelectionForm(request.POST, event=event)

        if form.is_valid():
            ticket = form.cleaned_data['ticket']
            quantity = form.cleaned_data['quantity']
            
            # 1. Limit ticket quantity per transaction
            MAX_TICKET_QUANTITY = 500
            if quantity > MAX_TICKET_QUANTITY:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Maximum {MAX_TICKET_QUANTITY} tickets per order.' # EN
                })

            # 2. Basic input validation
            if quantity <= 0:
                return JsonResponse({'status': 'error', 'message': "Ticket quantity must be greater than 0."}) # EN

            # 3. Validate ticket stock
            if quantity > ticket.available:
                msg = f"Only {ticket.available} tickets left for {ticket.get_ticket_type_display()}." # EN
                return JsonResponse({'status': 'error', 'message': msg})

            # 4. Process Booking (Get or Create)
            booking, created = Booking.objects.get_or_create(
                user=request.user,
                ticket=ticket,
                defaults={'quantity': 0, 'total_price': Decimal("0.00")}
            )

            # Update existing booking
            booking.quantity += quantity
            booking.total_price = Decimal(ticket.price) * booking.quantity
            booking.save()

            # Reduce ticket stock
            ticket.available -= quantity
            ticket.save()

            msg = "Ticket booked successfully! Thank you!" # EN
            
            # Return JSON success
            return JsonResponse({
                'status': 'success',
                'message': msg,
                'redirect_url': reverse('event:home_event') 
            })

        # If Form is Invalid
        else:
            try:
                # Get first error message
                error_msg = form.errors.as_data().popitem()[1][0].message
            except:
                error_msg = "Invalid form. Please select a ticket." # EN
                
            return JsonResponse({'status': 'error', 'message': error_msg})

    # If GET (direct browser access), redirect to event detail
    messages.info(request, "Please book tickets directly from the event page.") # EN
    return redirect('event:event_detail', id=event.id)


# ==============================================================================
#  PART 2: DISPLAY USER TICKETS (My Bookings)
# ==============================================================================

# HTML Version (For Django Web)
@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('ticket__event')
    return render(request, "my_bookings.html", {"bookings": bookings})

# JSON Version (For Flutter / API)
@csrf_exempt
@login_required
def get_my_bookings_ajax(request):
    bookings = Booking.objects.filter(user=request.user).select_related('ticket__event')
    
    data = []
    for b in bookings:
        data.append({
            "id": b.id, 
            "event_id": b.ticket.event.id,
            "event_title": b.ticket.event.judul,
            "date": b.ticket.event.date.strftime("%d %b %Y") if b.ticket.event.date else "-",
            "location": b.ticket.event.lokasi or "Location not set", # EN
            "quantity": b.quantity,
            "total_price": int(b.total_price),
            "ticket_type": b.ticket.get_ticket_type_display(),
            "booked_at": b.booked_at.strftime("%d %b %Y, %H:%M") if b.booked_at else "-",
            "event_url": reverse('event:event_detail', args=[b.ticket.event.id])
        })

    return JsonResponse({"bookings": data})


# ==============================================================================
#  PART 3: VIEW ALL TICKETS (Web & API)
# ==============================================================================

# HTML Version (For Django Web)
def all_tickets(request):
    tickets = Ticket.objects.select_related('event').all()

    if request.user.is_authenticated:
        try:
            if getattr(request.user, 'userprofile', None) and request.user.userprofile.is_admin:
                events = Event.objects.all()
            else:
                events = request.user.event_set.all()
        except:
            events = request.user.event_set.all()
    else:
        events = Event.objects.none()

    return render(request, "all_tickets.html", {
        "tickets": tickets,
        "events": events
    })

# JSON Version (For Flutter / API)
def get_tickets_ajax(request):
    tickets = Ticket.objects.select_related('event').all()
    data = []

    is_admin = False
    if request.user.is_authenticated:
        is_admin = getattr(getattr(request.user, 'userprofile', None), 'is_admin', False)

    for t in tickets:
        data.append({
            "id": t.id,
            "event_title": t.event.judul,
            "ticket_type": t.get_ticket_type_display(),
            "price": float(t.price),
            "available": t.available,
            "event_id": t.event.id,
            # Check if user can edit (Admin or Event Owner)
            "can_edit": request.user.is_authenticated and (is_admin or request.user == t.event.user),
        })

    return JsonResponse({"tickets": data})


# ==============================================================================
#  PART 4: TICKET CRUD (Create, Update, Delete)
# ==============================================================================

@csrf_exempt
@login_required
def create_ticket(request):
    if request.method == 'POST':
        try:
            # 1. Decode JSON
            data = json.loads(request.body)
            
            # 2. Get Data
            event_id = data.get('event')
            ticket_type = data.get('ticket_type')
            price = data.get('price')
            available = data.get('available')

            # 3. Validate Event ID
            if not event_id:
                return JsonResponse({'status': 'error', 'message': 'Event ID cannot be empty'}, status=400) # EN

            # Check Event
            event = Event.objects.filter(id=event_id).first()
            if not event:
                return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404) # EN

            # Check Permission (Only admin or event owner)
            is_admin = getattr(getattr(request.user, 'userprofile', None), 'is_admin', False)
            if not is_admin and event.user != request.user:
                return JsonResponse({'status': 'error', 'message': 'You do not have permission'}, status=403) # EN

            # 4. Create Ticket
            ticket = Ticket.objects.create(
                event=event,
                ticket_type=ticket_type,
                price=price,
                available=available
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Ticket created successfully!', # EN
                'ticket_id': ticket.id
            })

        except Exception as e:
            # IMPORTANT: Catch all errors and send as JSON
            print(f"SERVER ERROR: {e}") 
            return JsonResponse({'status': 'error', 'message': f'Server Error: {str(e)}'}, status=500) # EN

    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405) # EN

@csrf_exempt
@login_required
def edit_ticket_ajax(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Check Permission
    is_admin = getattr(getattr(request.user, 'userprofile', None), 'is_admin', False)
    if not (request.user == ticket.event.user or is_admin):
        return JsonResponse({'error': 'Forbidden'}, status=403) # EN

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400) # EN

        ticket.ticket_type = data.get('ticket_type', ticket.ticket_type)
        ticket.price = data.get('price', ticket.price)
        ticket.available = data.get('available', ticket.available)
        ticket.save()

        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405) # EN


@csrf_exempt
@login_required
def delete_ticket_ajax(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Check Permission
    is_admin = getattr(getattr(request.user, 'userprofile', None), 'is_admin', False)
    if not (request.user == ticket.event.user or is_admin):
        return JsonResponse({"error": "Forbidden"}, status=403) # EN

    if request.method == "POST":
        ticket.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid method"}, status=405) # EN



@csrf_exempt
@login_required
def get_user_events_dropdown(request):
    """
    API for Flutter: Get list of events owned by logged-in user
    to be selectable when creating a new ticket.
    """
    try:
        # Check if user is admin
        is_admin = getattr(getattr(request.user, 'userprofile', None), 'is_admin', False)

        if is_admin:
            # If admin, get all events
            events = Event.objects.all().order_by('-date')
        else:
            # If regular user, get ONLY events created by that user
            events = Event.objects.filter(user=request.user).order_by('-date')

        data = []
        for e in events:
            data.append({
                "id": e.id,
                "title": e.judul, # Ensure field name in Event model is 'judul'
            })

        return JsonResponse({"events": data})
    
    except Exception as e:
        print(e)
        return JsonResponse({"events": [], "error": str(e)})