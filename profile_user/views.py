from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import CustomUserCreationForm
from .models import UserProfile
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


def show_profile(request, username=None):
    if username:
        # Jika username diberikan, tampilkan profile user tersebut
        user = get_object_or_404(User, username=username)
    else:
        # Jika tidak, tampilkan profile user yang sedang login
        user = request.user
    
    try:
        user_profile = user.userprofile
    except UserProfile.DoesNotExist:
        # Jika profile belum ada, buat baru
        user_profile = UserProfile.objects.create(
            user=user,
            full_name=user.get_full_name() or user.username
        )
    
    context = {
        'user_profile': user_profile,
        'is_own_profile': user == request.user
    }
    
    return render(request, 'show_profile.html', context)

def register_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Buat UserProfile untuk user baru
            UserProfile.objects.create(
                user=user,
                full_name=form.cleaned_data['full_name'],
                phone=form.cleaned_data['phone']
            )
            login(request, user)
            messages.success(request, f'Akun {user.username} berhasil dibuat! Selamat datang!')
            return redirect('news:article-list')
    else:
        form = CustomUserCreationForm()
        
    context = {'form': form}
    return render(request, 'register.html', context)


def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Selamat datang kembali, {username}!")
                return redirect('news:article-list')
            else:
                messages.error(request, "Username atau password salah.")
        else:
            messages.error(request, "Username atau password salah.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'login.html', {'form': form})


def logout_user(request):
    logout(request)
    messages.info(request, "Kamu telah berhasil logout.")
    return redirect('landing-page')