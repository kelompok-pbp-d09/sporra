from django import forms
from .models import Ticket, Booking
from event.models import Event

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

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # safe check userprofile
        is_admin = getattr(getattr(user, 'userprofile', None), 'is_admin', False)

        if user and not is_admin:
            self.fields['event'].queryset = Event.objects.filter(user=user)
        else:
            self.fields['event'].queryset = Event.objects.all()

        self.fields['event'].label_from_instance = lambda obj: obj.judul


class TicketSelectionForm(forms.Form):
    ticket = forms.ModelChoiceField(
        queryset=Ticket.objects.none(),
        widget=forms.RadioSelect,
        empty_label=None,
        label="Pilih Tipe Tiket"
    )
    
    quantity = forms.IntegerField(
        min_value=1, 
        initial=1, 
        label="Jumlah"
    )

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super().__init__(*args, **kwargs)
        self.fields['ticket'].queryset = Ticket.objects.filter(event=event, available__gt=0)
        self.fields['ticket'].label_from_instance = lambda obj: (
            f"{obj.get_ticket_type_display()} "
            f"(Rp {obj.price:,.0f}) - "
            f"Sisa {obj.available}"
        )
