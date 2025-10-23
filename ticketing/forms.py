from django import forms
from .models import Ticket, Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['quantity']

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['event', 'ticket_type', 'price', 'available']
        widgets = {
            'event': forms.Select(attrs={'class': 'border rounded p-2 w-full'}),
            'ticket_type': forms.Select(attrs={'class': 'border rounded p-2 w-full'}),
            'price': forms.NumberInput(attrs={'class': 'border rounded p-2 w-full', 'step': '0.01'}),
            'available': forms.NumberInput(attrs={'class': 'border rounded p-2 w-full'}),
        }