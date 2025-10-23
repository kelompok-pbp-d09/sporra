from django.contrib import admin
from .models import Event, Ticket, Booking

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('judul', 'date')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('event', 'ticket_type', 'price', 'available')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'ticket', 'quantity', 'booked_at')
