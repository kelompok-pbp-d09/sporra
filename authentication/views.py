from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile
import json

@csrf_exempt
def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            # Login status successful.
            return JsonResponse({
                "username": user.username,
                "status": True,
                "message": "Login successful!"
                # Add other data if you want to send data to Flutter.
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
def register(request):
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
def logout(request):
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