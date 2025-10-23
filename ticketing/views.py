from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Ticket, Booking
from .forms import BookingForm, TicketForm ,TicketSelectionForm
from event.models import Event
from django.db import IntegrityError  


@login_required
def book_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = TicketSelectionForm(request.POST, event=event)
        
        if form.is_valid():
            ticket = form.cleaned_data['ticket']
            quantity = form.cleaned_data['quantity']

            if quantity > ticket.available:
                messages.error(request, f'Maaf, stok tiket {ticket.get_ticket_type_display()} hanya tersisa {ticket.available}.')
            elif quantity <= 0:
                 messages.error(request, 'Jumlah tiket harus lebih dari 0.')
            else:
                booking, created = Booking.objects.get_or_create(
                    user=request.user,
                    ticket=ticket,
                    # 'defaults' hanya dipakai jika booking BARU dibuat
                    defaults={'quantity': 0, 'total_price': 0} 
                )

                # Tambahkan jumlah baru ke booking yang ada (atau yang baru dibuat)
                booking.quantity += quantity
                # Hitung ulang total harga
                booking.total_price = ticket.price * booking.quantity 
                booking.save() # Simpan perubahan booking
                ticket.available -= quantity
                ticket.save()

                if created:
                    messages.success(request, 'Tiket berhasil dipesan!')
                else:
                    messages.success(request, f'Jumlah tiket berhasil diperbarui. Anda sekarang memiliki {booking.quantity}.')
                
                return redirect('event:home_event') 

    else: 
        form = TicketSelectionForm(event=event) 

    context = {
        'event': event,
        'form': form
    }
    return render(request, 'book_ticket.html', context)

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('ticket__event')
    return render(request, "my_bookings.html", {"bookings": bookings})

def all_tickets(request):
    tickets = Ticket.objects.select_related('event').all()
    return render(request, "all_tickets.html", {"tickets": tickets})


@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        
        # DEBUG: Print data yang diterima
        print("=== POST Data ===")
        print(f"Event ID dari form: {request.POST.get('event')}")
    
        event_id = request.POST.get('event')
        try:
            event = Event.objects.get(id=event_id)
            print(f"Event found: {event.id} - {event.judul}")
        except Event.DoesNotExist:
            print(f"Event NOT FOUND: {event_id}")
            messages.error(request, f'Event dengan ID {event_id} tidak ditemukan!')
            events = Event.objects.all()
            return render(request, 'create_ticket.html', {
                'form': form,
                'events': events,
                'event_count': events.count()
            })
        
        if form.is_valid():
            try:
                # Manual create untuk debug
                ticket = Ticket(
                    event_id=event_id,
                    ticket_type=form.cleaned_data['ticket_type'],
                    price=form.cleaned_data['price'],
                    available=form.cleaned_data['available']
                )
                ticket.save()
                messages.success(request, f'Ticket berhasil dibuat untuk {event.judul}!')
                return redirect('ticketing:all_tickets')
                
            except IntegrityError as e:
                print(f"IntegrityError detail: {e}")
                messages.error(request, f'Database error: {str(e)}')
            except Exception as e:
                print(f"Exception detail: {e}")
                messages.error(request, f'Error: {str(e)}')
        else:
            messages.error(request, 'Form tidak valid!')
            print(f"Form errors: {form.errors}")
    else:
        form = TicketForm()
    
    events = Event.objects.all()
    return render(request, 'create_ticket.html', {
        'form': form,
        'events': events,
        'event_count': events.count()
    })