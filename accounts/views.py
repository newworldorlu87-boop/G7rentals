from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum
from listings.models import Message

from .forms import RegisterForm
from .models import (
    User,
    Profile,
    EmailVerification,
    PasswordReset
)

from listings.models import Property, Favorite
from bookings.models import Booking


# =========================
# ADMIN DASHBOARD
# =========================
@login_required
def admin_dashboard(request):

    # ONLY ADMINS
    if not request.user.is_superuser:
        return redirect('tenant_dashboard')

    landlords = User.objects.filter(user_type='landlord')
    tenants = User.objects.filter(user_type='tenant')

    properties = Property.objects.all().order_by('-created_at')

    bookings = Booking.objects.all()

    favorites = Favorite.objects.all()

    messages_list = Message.objects.all().order_by('-created_at')

    context = {
        'landlords': landlords,
        'tenants': tenants,
        'properties': properties,
        'bookings': bookings,
        'favorites': favorites,

        'total_landlords': landlords.count(),
        'total_tenants': tenants.count(),
        'total_properties': properties.count(),
        'total_bookings': bookings.count(),
        'messages_list': messages_list,
    }

    return render(
        request,
        'accounts/admin_dashboard.html',
        context
    )


# =========================
# TENANT DASHBOARD
# =========================
@login_required
def tenant_dashboard(request):

    bookings = request.user.booking_set.all()

    recommended_properties = Property.objects.order_by(
        '-created_at'
    )[:6]

    favorites = Favorite.objects.filter(
        user=request.user
    )

    # TENANT CHATS
    chats = Message.objects.filter(
        sender=request.user
    ).select_related(
        'receiver',
        'property'
    ).order_by('-created_at')
    unread_messages = Message.objects.filter(
    receiver=request.user,
    is_read=False
    ).count()

    return render(
        request,
        'accounts/tenant_dashboard.html',
        {
            'bookings': bookings,
            'recommended_properties': recommended_properties,
            'favorites': favorites,
            'chats': chats,
            'unread_messages': unread_messages,
        }
    )



# =========================
# LANDLORD DASHBOARD
# =========================
@login_required
def landlord_dashboard(request):

    # PREVENT TENANTS
    if request.user.user_type == 'tenant':
        return redirect('tenant_dashboard')

    # LANDLORD PROPERTIES
    properties = Property.objects.filter(
        owner=request.user
    ).order_by('-created_at')

    # BOOKINGS FOR LANDLORD PROPERTIES
    bookings = Booking.objects.filter(
        property__owner=request.user
    ).select_related(
        'property',
        'user'
    ).order_by('-id')

    # TOTAL PROPERTY VALUE
    total_value = properties.aggregate(
        total=Sum('price')
    )['total'] or 0

    # APPROVED BOOKINGS
    approved_bookings = bookings.filter(
        status='Approved'
    ).count()

    # PENDING BOOKINGS
    pending_bookings = bookings.filter(
        status='Pending'
    ).count()

    # LANDLORD CHATS
    chats = Message.objects.filter(
        receiver=request.user
    ).select_related(
        'sender',
        'property'
    ).order_by('-created_at')
    unread_messages = Message.objects.filter(
    receiver=request.user,
    is_read=False
    ).count()
    context = {
        'properties': properties,
        'bookings': bookings,
        'total_value': total_value,
        'approved_bookings': approved_bookings,
        'pending_bookings': pending_bookings,
        'chats': chats,
        'unread_messages': unread_messages,
    }

    return render(
        request,
        'accounts/landlords.html',
        context
    )

# =========================
# REGISTER
# =========================
def register_view(request):

    form = RegisterForm(request.POST or None)

    if form.is_valid():

        user = form.save(commit=False)

        user.is_verified = True

        # IMPORTANT
        user.user_type = form.cleaned_data.get(
            'user_type'
        )

        user.save()

        messages.success(
            request,
            "Account created successfully!"
        )

        return redirect('login')

    return render(
        request,
        'accounts/register.html',
        {
            'form': form
        }
    )


# =========================
# LOGIN
# =========================
def login_view(request):

    # AUTO REDIRECT
    if request.user.is_authenticated:

        # ADMIN
        if request.user.is_superuser:
            return redirect('admin_dashboard')

        # LANDLORD
        elif request.user.user_type == 'landlord':
            return redirect('landlord_dashboard')

        # TENANT
        else:
            return redirect('tenant_dashboard')

    if request.method == "POST":

        email = request.POST.get('email')

        password = request.POST.get('password')

        if not email or not password:

            messages.error(
                request,
                "All fields are required"
            )

            return redirect('login')

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is None:

            messages.error(
                request,
                "Invalid credentials"
            )

            return redirect('login')

        login(request, user)

        # ROLE BASED REDIRECT

        # ADMIN
        if user.is_superuser:
            return redirect('admin_dashboard')

        # LANDLORD
        elif user.user_type == 'landlord':
            return redirect('landlord_dashboard')

        # TENANT
        elif user.user_type == 'tenant':
            return redirect('tenant_dashboard')

        return redirect('login')

    return render(
        request,
        'accounts/login.html'
    )


# =========================
# LOGOUT
# =========================
def logout_view(request):

    logout(request)

    return redirect('login')


# =========================
# PROFILE
# =========================
@login_required
def profile_view(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        # USER INFO
        request.user.username = request.POST.get(
            'username'
        )

        request.user.email = request.POST.get(
            'email'
        )

        request.user.phone = request.POST.get(
            'phone'
        )

        request.user.save()

        # PROFILE INFO
        profile.address = request.POST.get(
            'address'
        )

        profile.city = request.POST.get(
            'city'
        )

        profile.country = request.POST.get(
            'country'
        )

        profile.bio = request.POST.get(
            'bio'
        )

        # PROFILE IMAGE
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES[
                'avatar'
            ]

        profile.save()

        messages.success(
            request,
            "Profile updated successfully!"
        )

        return redirect('profile')

    return render(
        request,
        'accounts/profile.html',
        {
            'profile': profile
        }
    )

# =========================
# VERIFY EMAIL
# =========================
def verify_email(request, token):

    verification = get_object_or_404(
        EmailVerification,
        token=token,
        is_used=False
    )

    verification.user.is_verified = True

    verification.user.save()

    verification.is_used = True

    verification.save()

    messages.success(
        request,
        "Email verified! You can now login."
    )

    return redirect('login')


# =========================
# REQUEST PASSWORD RESET
# =========================
def request_password_reset(request):

    if request.method == "POST":

        email = request.POST.get('email')

        user = User.objects.filter(
            email=email
        ).first()

        if user:

            reset = PasswordReset.objects.create(
                user=user
            )

            reset_link = (
                f"http://127.0.0.1:8000/"
                f"reset-password/{reset.token}/"
            )

            send_mail(
                "Password Reset",
                f"Click to reset: {reset_link}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )

        messages.success(
            request,
            "If email exists, reset link sent"
        )

        return redirect('login')

    return render(
        request,
        'accounts/reset_request.html'
    )


# =========================
# RESET PASSWORD
# =========================
def reset_password(request, token):

    reset = get_object_or_404(
        PasswordReset,
        token=token,
        is_used=False
    )

    if request.method == "POST":

        password = request.POST.get('password')

        user = reset.user

        user.set_password(password)

        user.save()

        reset.is_used = True

        reset.save()

        messages.success(
            request,
            "Password reset successful"
        )

        return redirect('login')

    return render(
        request,
        'accounts/reset_password.html'
    )