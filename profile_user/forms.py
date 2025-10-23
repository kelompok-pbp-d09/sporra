from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'full_name', 'phone', 'password1', 'password2')

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'full_name', 'bio', 'phone']
        widgets = {
            'profile_picture': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg bg-gray-700 text-white border border-gray-600',
                'placeholder': 'Enter image URL'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg bg-gray-700 text-white border border-gray-600',
                'placeholder': 'Enter your full name'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 rounded-lg bg-gray-700 text-white border border-gray-600',
                'placeholder': 'Write something about yourself',
                'rows': 4
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg bg-gray-700 text-white border border-gray-600',
                'placeholder': 'Enter your phone number'
            })
       }