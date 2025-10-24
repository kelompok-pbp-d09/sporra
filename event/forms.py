from django import forms
from django.utils.html import strip_tags
from datetime import datetime
from django.utils import timezone
from event.models import Event

class EventForm(forms.ModelForm):
    date = forms.CharField(
        label='Tanggal dan Waktu',
        widget=forms.TextInput(attrs={
            'placeholder': 'Contoh: 12 Juli 2025 15.00'
        })
    )

    class Meta:
        model = Event
        fields = ["judul", "deskripsi", "date", "lokasi", "kategori"]

    def clean_date(self):
        date_str = self.cleaned_data.get("date", "").strip()
        date_str_lower = date_str.lower()
        
        bulan_map = {
            "januari": "January", "februari": "February", "maret": "March",
            "april": "April", "mei": "May", "juni": "June", "juli": "July",
            "agustus": "August", "september": "September", "oktober": "October",
            "november": "November", "desember": "December"
        }

        for indo, eng in bulan_map.items():
            if indo in date_str_lower:
                date_str = date_str_lower.replace(indo, eng)
                break

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

        if timezone.is_naive(parsed_date):
            parsed_date = timezone.make_aware(parsed_date, timezone.get_current_timezone())

        return parsed_date

    def clean_judul(self):
        judul = self.cleaned_data.get("judul", "")
        return strip_tags(judul)

    def clean_deskripsi(self):
        deskripsi = self.cleaned_data.get("deskripsi", "")
        return strip_tags(deskripsi)