from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['ticket', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
        }
