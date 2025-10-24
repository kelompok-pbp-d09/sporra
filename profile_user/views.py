from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import *
from .models import UserProfile
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Status

@login_required(login_url='profile_user/login')
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

@login_required
def edit_profile(request):
    user_profile = request.user.userprofile
    
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_user:show_profile')
    else:
        form = EditProfileForm(instance=user_profile)
    
    return render(request, 'edit_profile.html', {'form': form})

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

@login_required
@require_POST
def add_status(request):
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Status tidak boleh kosong'}, status=400)

    status = request.user.userprofile.add_status(content)
    
    return JsonResponse({
        'id': status.id,
        'content': status.content,
        'created_at': status.created_at.strftime("%d %b %Y"),
    })

@login_required
@require_POST
def delete_status(request, status_id):
    status = get_object_or_404(Status, id=status_id)
    user_profile = request.user.userprofile

    if status.user == user_profile or user_profile.is_admin:
        status.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Anda tidak memiliki izin'}, status=403)

@login_required
@require_POST
def edit_status(request, status_id):
    status = get_object_or_404(Status, id=status_id)
    user_profile = request.user.userprofile

    if status.user != user_profile and not user_profile.is_admin:
        return JsonResponse({'error': 'Anda tidak memiliki izin'}, status=403)

    new_content = request.POST.get('content', '').strip()
    if not new_content:
        return JsonResponse({'error': 'Status tidak boleh kosong'}, status=400)

    status.content = new_content
    status.save()

    return JsonResponse({'success': True, 'new_content': status.content})