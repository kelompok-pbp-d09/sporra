from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Ticket, Booking ,Event
from .forms import BookingForm

@login_required
def list_tickets(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    tickets = Ticket.objects.filter(event=event)
    return render(request, "ticket_list.html", {"event": event, "tickets": tickets})

@login_required
def book_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']

            # Cek apakah stok tiket cukup
            if ticket.available < quantity:
                return JsonResponse({"error": "Tiket tidak cukup"}, status=400)

            # Cek apakah user sudah pernah pesan tiket ini
            if Booking.objects.filter(user=request.user, ticket=ticket).exists():
                return JsonResponse({"error": "Kamu sudah memesan tiket ini"}, status=400)

            # Simpan booking
            Booking.objects.create(user=request.user, ticket=ticket, quantity=quantity)
            ticket.available -= quantity
            ticket.save()
            return JsonResponse({"success": True})
    else:
        form = BookingForm(initial={'ticket': ticket})
    return render(request, "book_ticket.html", {"form": form, "ticket": ticket})

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('ticket__event')
    return render(request, "my_bookings.html", {"bookings": bookings})
