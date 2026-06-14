from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .analytics import track_event
from .models import MemberProfile


@require_http_methods(["GET", "POST"])
def member_login(request):
    if request.user.is_authenticated:
        return redirect("member_dashboard")
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            profile, _ = MemberProfile.objects.get_or_create(user=user)
            profile.last_login_ip = request.META.get("REMOTE_ADDR")
            profile.save(update_fields=["last_login_ip", "updated_at"])
            track_event(request, "login", path="/member/login/")
            next_url = request.GET.get("next") or request.POST.get("next") or "/member/"
            return redirect(next_url)
        error = "帳號或密碼錯誤"
    return render(request, "showroom/member/login.html", {"error": error})


@require_http_methods(["GET", "POST"])
def member_register(request):
    if request.user.is_authenticated:
        return redirect("member_dashboard")
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        company = request.POST.get("company", "").strip()
        phone = request.POST.get("phone", "").strip()
        if not username or not email or not password:
            error = "請填寫帳號、Email 與密碼"
        elif password != password2:
            error = "兩次密碼不一致"
        elif User.objects.filter(username=username).exists():
            error = "帳號已存在"
        elif User.objects.filter(email=email).exists():
            error = "Email 已註冊"
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            MemberProfile.objects.create(user=user, company=company, phone=phone)
            login(request, user)
            track_event(request, "login", path="/member/register/")
            return redirect("member_dashboard")
    return render(request, "showroom/member/register.html", {"error": error})


@login_required
def member_dashboard(request):
    profile, _ = MemberProfile.objects.get_or_create(user=request.user)
    from .models import Inquiry
    inquiries = Inquiry.objects.filter(email=request.user.email).order_by("-created_at")[:10]
    return render(request, "showroom/member/dashboard.html", {
        "profile": profile,
        "inquiries": inquiries,
    })


def member_logout(request):
    logout(request)
    return redirect("home")
