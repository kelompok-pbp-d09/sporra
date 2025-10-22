from django import forms
from django.utils.html import strip_tags
from datetime import datetime
from django.utils import timezone
from main.models import Event

class EventForm(forms.ModelForm):
    date = forms.CharField(
        label='Tanggal dan Waktu',
        widget=forms.TextInput(attrs={
            'placeholder': 'Contoh: 12 Juli 2025 15.00'
        })
    )

    class Meta:
        model = Event
        fields = ["title", "description", "date", "location", "category", "Max_participants", "price"]

    def clean_date(self):
        date_str = self.cleaned_data.get("date", "").strip()

        # Peta bulan Indonesia ke Inggris
        bulan_map = {
            "januari": "January", "februari": "February", "maret": "March",
            "april": "April", "mei": "May", "juni": "June", "juli": "July",
            "agustus": "August", "september": "September", "oktober": "October",
            "november": "November", "desember": "December"
        }

        for indo, eng in bulan_map.items():
            if indo in date_str.lower():
                date_str = date_str.lower().replace(indo, eng)
                break

        # Coba parsing
        parsed_date = None
        for fmt in ["%d %B %Y %H.%M", "%d %B %Y %H:%M"]:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        if not parsed_date:
            raise forms.ValidationError(
                "Masukkan tanggal/waktu yang valid. Contoh: 12 Juli 2025 15.00"
            )

        # Jadikan timezone-aware
        if timezone.is_naive(parsed_date):
            parsed_date = timezone.make_aware(parsed_date, timezone.get_current_timezone())

        return parsed_date

    def clean_title(self):
        return strip_tags(self.cleaned_data.get("title", ""))

    def clean_description(self):
        return strip_tags(self.cleaned_data.get("description", ""))
