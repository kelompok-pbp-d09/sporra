from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages

def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Akun {user.username} berhasil dibuat!')
            return redirect('news:article-list')
    else:
        form = UserCreationForm()
        
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