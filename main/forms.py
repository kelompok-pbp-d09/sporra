from django import forms
from django.utils.html import strip_tags
from main.models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "date", "location", "category", "Max_participants", "price"]

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        return strip_tags(title)

    def clean_description(self):
        description = self.cleaned_data.get("description", "")
        return strip_tags(description)
