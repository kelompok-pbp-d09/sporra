from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import *
from .models import UserProfile
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Status
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
import json

@login_required
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

@csrf_exempt
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

@csrf_exempt
@login_required
@require_POST
def delete_status(request, status_id):
    status = get_object_or_404(Status, id=status_id)
    user_profile = request.user.userprofile

    if status.user == user_profile or user_profile.is_admin:
        status.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Anda tidak memiliki izin'}, status=403)

@csrf_exempt
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


@csrf_exempt
def login_flutter(request):
    username = request.POST['username']
    password = request.POST['password']
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            
            pfp_url = ""
            try:
                # Ambil URL foto profil jika ada
                if hasattr(user, 'userprofile'):
                    pfp_url = user.userprofile.profile_picture or ""
            except Exception as e:
                pfp_url = ""

            return JsonResponse({
                "username": user.username,
                "status": True,
                "message": "Login successful!",
                "profile_picture": pfp_url, 
                "is_superuser": user.is_superuser, 
            }, status=200)
        else:
            return JsonResponse({
                "status": False,
                "message": "Login failed, account is disabled."
            }, status=401)
    else:
        return JsonResponse({
            "status": False,
            "message": "Login failed, please check your username or password."
        }, status=401)

# Create your views here.
@csrf_exempt
def register_flutter(request):
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Invalid request"}, status=400)

    data = {}

    # JSON
    if request.content_type == "application/json":
        try:
            body = request.body.decode("utf-8")
            if body.strip():
                data = json.loads(body)
        except:
            pass

    # Cookie Req
    if not data:
        if request.POST:
            data = request.POST.dict()

    if not data:
        return JsonResponse({
            "status": False,
            "message": "Request body kosong atau tidak valid."
        }, status=400)

    username = data.get('username')
    full_name = data.get('full_name')
    phone = data.get('phone')
    password1 = data.get('password1')
    password2 = data.get('password2')

    if not username or not full_name or not phone or not password1 or not password2:
        return JsonResponse({"status": False, "message": "Semua field harus diisi"}, status=400)

    if password1 != password2:
        return JsonResponse({"status": False, "message": "Password tidak cocok"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"status": False, "message": "Username sudah terpakai"}, status=400)

    if UserProfile.objects.filter(phone=phone).exists():
        return JsonResponse({"status": False, "message": "Nomor telepon sudah digunakan"}, status=400)

    user = User.objects.create_user(username=username, password=password1)
    UserProfile.objects.create(user=user, full_name=full_name, phone=phone)

    auth_login(request, user)

    return JsonResponse({
        "status": True,
        "message": f"Akun {username} berhasil dibuat!",
        "username": username
    }, status=200)
    
@csrf_exempt
def logout_flutter(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "status": False,
            "message": "User not logged in."
        }, status=400)

    username = request.user.username
    auth_logout(request)

    return JsonResponse({
        "status": True,
        "message": "Kamu telah berhasil logout",
        "username": username,
    }, status=200)

def user_profile_json(request, username=None):
    # Jika username diberikan, cari user tersebut. 
    # Jika tidak (None), gunakan request.user (user yang sedang login).
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user

    try:
        profile = UserProfile.objects.get(user=user)
        
        pfp_url = ""
        if profile.profile_picture:
            # Jika profile_picture adalah URL string, pakai langsung.
            # Jika ImageField, gunakan .url
            pfp_url = str(profile.profile_picture) 

        statuses = profile.get_statuses().order_by('-created_at')
        status_list = []
        for s in statuses:
            status_list.append({
                "id": s.id,
                "content": s.content,
                # Format tanggal agar mudah dibaca di Flutter
                "created_at": s.created_at.strftime("%d %b %Y"), 
            })

        is_own_profile = (request.user == user)

        data = {
            "status": True,
            "username": user.username,
            "full_name": profile.full_name or user.username,
            "bio": profile.bio or "-",
            "phone": profile.phone or "-",
            "profile_picture": pfp_url or "",
            "role": profile.role or "user",
            "is_superuser": user.is_superuser, # Untuk status Admin
            "news_created": profile.total_news, 
            "total_comments": profile.komentar_created, 
            "total_news_realtime": profile.total_news,
            "events_created": profile.events_created,
            "is_own_profile": is_own_profile,
            
            "statuses": status_list, 
        }
        
        return JsonResponse(data, status=200)

    except UserProfile.DoesNotExist:
        return JsonResponse({
            "status": False,
            "message": "Profile not found"
        }, status=404)

@csrf_exempt
def edit_profile_flutter(request):
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)

    user_profile = request.user.userprofile
    data = {}

    # Handle input JSON atau Form Data
    try:
        if request.content_type == "application/json":
            data = json.loads(request.body)
        else:
            data = request.POST
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "Invalid JSON"}, status=400)

    # Ambil data dari request
    full_name = data.get('full_name')
    bio = data.get('bio')
    phone = data.get('phone')
    profile_picture = data.get('profile_picture')

    # Update data profile
    if full_name:
        user_profile.full_name = full_name
    if bio:
        user_profile.bio = bio
    if phone:
        user_profile.phone = phone
    if profile_picture:
        # Asumsi profile_picture dari Flutter dikirim sebagai URL String
        user_profile.profile_picture = profile_picture

    try:
        user_profile.save()
        return JsonResponse({
            "status": True, 
            "message": "Profile updated successfully!",
            "data": {
                "full_name": user_profile.full_name,
                "bio": user_profile.bio,
                "phone": user_profile.phone,
                "profile_picture": str(user_profile.profile_picture)
            }
        }, status=200)
    except Exception as e:
        return JsonResponse({"status": False, "message": str(e)}, status=500)