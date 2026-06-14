from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods

from listings.models import Property, Message as ListingMessage, Favorite
from bookings.models import Booking
from .models import User, Profile, EmailVerification, PasswordReset, Notification
from .forms import RegisterForm


# =========================
# ADMIN DASHBOARD
# =========================
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('accounts:tenant_dashboard')

    landlords = User.objects.filter(user_type='landlord')
    tenants = User.objects.filter(user_type='tenant')
    properties = Property.objects.all().order_by('-created_at')
    bookings = Booking.objects.all()
    favorites = Favorite.objects.all()
    messages_list = ListingMessage.objects.all().order_by('-created_at')

    all_users = User.objects.filter(
        Q(user_type='landlord') | Q(user_type='tenant')
    )
    sent_notifications = Notification.objects.filter(
        sender=request.user
    ).select_related('recipient')[:20]

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
        'all_users': all_users,
        'sent_notifications': sent_notifications,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


# =========================
# SEND NOTIFICATION (ADMIN ONLY)
# =========================
@login_required
def send_notification(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('accounts:tenant_dashboard')

    if request.method != 'POST':
        return redirect('accounts:admin_dashboard')

    target_group = request.POST.get('target_group')
    title = request.POST.get('title', '').strip()
    message_body = request.POST.get('message', '').strip()
    priority = request.POST.get('priority', 'NORMAL')
    recipient_id = request.POST.get('recipient')

    if not title or not message_body:
        messages.error(request, 'Title and message are required.')
        return redirect('accounts:admin_dashboard')

    recipients = []
    if target_group == 'ALL':
        recipients = list(User.objects.filter(
            Q(user_type='landlord') | Q(user_type='tenant')
        ))
    elif target_group == 'LANDLORDS':
        recipients = list(User.objects.filter(user_type='landlord'))
    elif target_group == 'TENANTS':
        recipients = list(User.objects.filter(user_type='tenant'))
    elif target_group == 'SPECIFIC':
        if not recipient_id:
            messages.error(request, 'Please select a specific user.')
            return redirect('accounts:admin_dashboard')
        try:
            recipient = User.objects.get(id=recipient_id)
            recipients = [recipient]
        except User.DoesNotExist:
            messages.error(request, 'Selected user not found.')
            return redirect('accounts:admin_dashboard')
    else:
        messages.error(request, 'Invalid target group.')
        return redirect('accounts:admin_dashboard')

    created_count = 0
    for recipient in recipients:
        Notification.objects.create(
            sender=request.user,
            recipient=recipient if target_group == 'SPECIFIC' else None,
            target_group=target_group,
            title=title,
            message=message_body,
            priority=priority
        )
        created_count += 1

    messages.success(
        request,
        f'Notification sent successfully to {created_count} user{"s" if created_count > 1 else ""}.'
    )
    return redirect('accounts:admin_dashboard')


# =========================
# USER NOTIFICATIONS
# =========================
@login_required
def user_notifications(request):
    user = request.user
    user_notifications = Notification.objects.filter(
        Q(target_group='ALL') |
        Q(target_group='LANDLORDS', recipient__user_type='landlord') |
        Q(target_group='TENANTS', recipient__user_type='tenant') |
        Q(recipient=user)
    ).distinct().order_by('-created_at')

    unread_count = user_notifications.filter(is_read=False).count()

    context = {
        'notifications': user_notifications,
        'unread_count': unread_count,
    }
    return render(request, 'accounts/notifications.html', context)


# =========================
# MARK NOTIFICATION AS READ
# =========================
@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save()
    return redirect('accounts:user_notifications')


# =========================
# TENANT DASHBOARD
# =========================
@login_required
def tenant_dashboard(request):
    bookings = request.user.tenant_bookings.select_related('property')
    recommended_properties = Property.objects.order_by('-created_at')[:6]
    favorites = Favorite.objects.filter(user=request.user)

    chats = ListingMessage.objects.filter(
        sender=request.user
    ).select_related('receiver', 'property').order_by('-created_at')

    unread_messages = ListingMessage.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    unread_notifications = Notification.objects.filter(
        Q(target_group='ALL') |
        Q(target_group='TENANTS') |
        Q(recipient=request.user),
        is_read=False
    ).distinct().count()

    return render(request, 'accounts/tenant_dashboard.html', {
        'bookings': bookings,
        'recommended_properties': recommended_properties,
        'favorites': favorites,
        'chats': chats,
        'unread_messages': unread_messages,
        'unread_notifications': unread_notifications,
    })


# ============================================
# LANDLORD DASHBOARD
# ============================================
@login_required
def landlord_dashboard(request):
    if request.user.user_type == 'tenant':
        return redirect('accounts:tenant_dashboard')

    properties = Property.objects.filter(owner=request.user).order_by('-created_at')
    recent_properties = properties[:5]

    bookings = Booking.objects.filter(
        property__owner=request.user
    ).select_related('tenant', 'property').order_by('-id')

    total_value = properties.aggregate(total=Sum('price'))['total'] or 0
    approved_bookings = bookings.filter(status='Approved').count()
    pending_bookings = bookings.filter(status='Pending').count()

    vacant_count = properties.filter(status='vacant').count()
    occupied_count = properties.filter(status='occupied').count()
    maintenance_count = properties.filter(status='maintenance').count()

    monthly_income = properties.filter(
        status='occupied'
    ).aggregate(total=Sum('price'))['total'] or 0

    chats = ListingMessage.objects.filter(
        receiver=request.user
    ).select_related('sender', 'property').order_by('-created_at')

    unread_messages = ListingMessage.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    unread_notifications = Notification.objects.filter(
        Q(target_group='ALL') |
        Q(target_group='LANDLORDS') |
        Q(recipient=request.user),
        is_read=False
    ).distinct().count()

    context = {
        'properties': recent_properties,
        'all_properties_count': properties.count(),
        'bookings': bookings,
        'total_value': total_value,
        'approved_bookings': approved_bookings,
        'pending_bookings': pending_bookings,
        'vacant_count': vacant_count,
        'occupied_count': occupied_count,
        'maintenance_count': maintenance_count,
        'monthly_income': monthly_income,
        'chats': chats,
        'unread_messages': unread_messages,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'accounts/landlord_dashboard.html', context)
@login_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        property__owner=request.user
    )

    booking.status = 'approved'
    booking.save()

    return redirect('accounts:landlord_dashboard')


@login_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        property__owner=request.user
    )

    booking.status = 'rejected'
    booking.save()

    return redirect('accounts:landlord_dashboard')


# ============================================
# PROPERTY CRUD — LANDLORD ONLY (ACCOUNTS APP)
# ============================================

@login_required
def property_list(request):
    """List all properties owned by the current landlord."""
    if request.user.user_type != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect('accounts:tenant_dashboard')

    properties = Property.objects.filter(
        owner=request.user
    ).order_by('-created_at')

    total_properties = properties.count()
    occupied_count = properties.filter(status='occupied').count()
    vacant_count = properties.filter(status='vacant').count()
    maintenance_count = properties.filter(status='maintenance').count()
    total_monthly_income = properties.filter(
        status='occupied'
    ).aggregate(total=Sum('price'))['total'] or 0

    context = {
        'properties': properties,
        'total_properties': total_properties,
        'occupied_count': occupied_count,
        'vacant_count': vacant_count,
        'maintenance_count': maintenance_count,
        'total_monthly_income': total_monthly_income,
    }
    return render(request, 'accounts/property_list.html', context)


@login_required
def property_create(request):
    """Create a new property listing."""
    if request.user.user_type != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect('accounts:tenant_dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        zip_code = request.POST.get('zip_code', '').strip()
        location = request.POST.get('location', '').strip()
        property_type = request.POST.get('property_type', 'apartment')
        bedrooms = request.POST.get('bedrooms', 1)
        bathrooms = request.POST.get('bathrooms', 1)
        sqft = request.POST.get('sqft', 0)
        price = request.POST.get('price', 0)
        description = request.POST.get('description', '').strip()
        status = request.POST.get('status', 'vacant')
        amenities = request.POST.get('amenities', '').strip()
        is_available = request.POST.get('is_available') == 'on'

        if not title or not address or not city:
            messages.error(request, "Title, address, and city are required.")
            return redirect('accounts:property_create')

        try:
            property_obj = Property.objects.create(
                owner=request.user,
                title=title,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                location=location,
                property_type=property_type,
                bedrooms=int(bedrooms) if bedrooms else 1,
                bathrooms=float(bathrooms) if bathrooms else 1.0,
                sqft=int(sqft) if sqft else 0,
                price=float(price) if price else 0,
                description=description,
                status=status,
                amenities=amenities,
                is_available=is_available,
            )

            if 'image' in request.FILES:
                property_obj.image = request.FILES['image']
                property_obj.save()

            messages.success(request, f"Property '{title}' created successfully!")
            return redirect('accounts:property_detail', pk=property_obj.pk)

        except Exception as e:
            messages.error(request, f"Error creating property: {str(e)}")
            return redirect('accounts:property_create')

    context = {
        'property_types': Property.PROPERTY_TYPE_CHOICES,
        'status_choices': Property.STATUS_CHOICES,
    }
    return render(request, 'accounts/property_form.html', context)


@login_required
def property_detail(request, pk):
    """View detailed property information (landlord's own property)."""
    if request.user.user_type != 'landlord':
        messages.error(request, "Access denied.")
        return redirect('accounts:tenant_dashboard')

    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)

    bookings = Booking.objects.filter(property=property_obj).order_by('-id')
    favorites_count = Favorite.objects.filter(property=property_obj).count()

    current_tenant = None
    current_booking = None
    if property_obj.status == 'occupied':
        current_booking = Booking.objects.filter(
            property=property_obj,
            status='Approved'
        ).select_related('tenant').first()
        if current_booking:
            current_tenant = current_booking.user

    context = {
        'property': property_obj,
        'bookings': bookings,
        'favorites_count': favorites_count,
        'current_tenant': current_tenant,
        'current_booking': current_booking,
    }
    return render(request, 'accounts/property_detail.html', context)


@login_required
def property_update(request, pk):
    """Edit/update an existing property."""
    if request.user.user_type != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect('accounts:tenant_dashboard')

    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)

    if request.method == 'POST':
        property_obj.title = request.POST.get('title', property_obj.title).strip()
        property_obj.address = request.POST.get('address', property_obj.address).strip()
        property_obj.city = request.POST.get('city', property_obj.city).strip()
        property_obj.state = request.POST.get('state', property_obj.state).strip()
        property_obj.zip_code = request.POST.get('zip_code', property_obj.zip_code).strip()
        property_obj.location = request.POST.get('location', property_obj.location).strip()
        property_obj.property_type = request.POST.get('property_type', property_obj.property_type)
        property_obj.bedrooms = int(request.POST.get('bedrooms', property_obj.bedrooms) or 1)
        property_obj.bathrooms = float(request.POST.get('bathrooms', property_obj.bathrooms) or 1.0)
        property_obj.sqft = int(request.POST.get('sqft', property_obj.sqft) or 0)
        property_obj.price = float(request.POST.get('price', property_obj.price) or 0)
        property_obj.description = request.POST.get('description', property_obj.description).strip()
        property_obj.status = request.POST.get('status', property_obj.status)
        property_obj.amenities = request.POST.get('amenities', property_obj.amenities).strip()
        property_obj.is_available = request.POST.get('is_available') == 'on'

        if 'image' in request.FILES:
            if property_obj.image:
                try:
                    property_obj.image.delete(save=False)
                except:
                    pass
            property_obj.image = request.FILES['image']

        if request.POST.get('remove_image') == 'on' and property_obj.image:
            try:
                property_obj.image.delete(save=False)
                property_obj.image = None
            except:
                pass

        try:
            property_obj.save()
            messages.success(request, f"Property '{property_obj.title}' updated successfully!")
            return redirect('accounts:property_detail', pk=property_obj.pk)
        except Exception as e:
            messages.error(request, f"Error updating property: {str(e)}")

    context = {
        'property': property_obj,
        'property_types': Property.PROPERTY_TYPE_CHOICES,
        'status_choices': Property.STATUS_CHOICES,
        'is_edit': True,
    }
    return render(request, 'accounts/property_form.html', context)


@login_required
@require_http_methods(["POST", "GET"])
def property_delete(request, pk):
    """Delete a property with confirmation."""
    if request.user.user_type != 'landlord':
        messages.error(request, "Access denied. Landlords only.")
        return redirect('accounts:tenant_dashboard')

    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)

    if request.method == 'POST':
        property_title = property_obj.title
        try:
            if property_obj.image:
                property_obj.image.delete(save=False)
            property_obj.delete()
            messages.success(request, f"Property '{property_title}' deleted successfully.")
            return redirect('accounts:property_list')
        except Exception as e:
            messages.error(request, f"Error deleting property: {str(e)}")
            return redirect('accounts:property_detail', pk=pk)

    context = {'property': property_obj}
    return render(request, 'accounts/property_confirm_delete.html', context)

@login_required
def toggle_favorite(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        property=property_obj
    )

    if not created:
        favorite.delete()

    return redirect('accounts:tenant_dashboard')

@login_required
def property_toggle_status(request, pk):
    """Quick toggle property status (AJAX endpoint)."""
    if request.user.user_type != 'landlord':
        return JsonResponse({'error': 'Access denied'}, status=403)

    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['vacant', 'occupied', 'maintenance']:
            property_obj.status = new_status
            property_obj.save()
            return JsonResponse({
                'success': True,
                'status': new_status,
                'status_display': property_obj.get_status_display()
            })

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('accounts:admin_dashboard')
    elif request.user.user_type == 'landlord':
        return redirect('accounts:landlord_dashboard')
    else:
        return redirect('accounts:tenant_dashboard')


# =========================
# REGISTER
# =========================
def register_view(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.is_verified = True
        user.user_type = form.cleaned_data.get('user_type')
        user.save()
        messages.success(request, "Account created successfully!")
        return redirect('accounts:login')
    return render(request, 'accounts/register.html', {'form': form})


# =========================
# LOGIN
# =========================
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('accounts:admin_dashboard')
        elif request.user.user_type == 'landlord':
            return redirect('accounts:landlord_dashboard')
        else:
            return redirect('accounts:tenant_dashboard')

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, "All fields are required")
            return redirect('accounts:login')

        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, "Invalid credentials")
            return redirect('accounts:login')

        login(request, user)

        if user.is_superuser:
            return redirect('accounts:admin_dashboard')
        elif user.user_type == 'landlord':
            return redirect('accounts:landlord_dashboard')
        elif user.user_type == 'tenant':
            return redirect('accounts:tenant_dashboard')

        return redirect('accounts:login')

    return render(request, 'accounts/login.html')


# =========================
# LOGOUT
# =========================
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('accounts:login')


# =========================
# PROFILE
# =========================
@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        request.user.username = request.POST.get('username')
        request.user.email = request.POST.get('email')
        request.user.phone = request.POST.get('phone')
        request.user.save()

        profile.address = request.POST.get('address')
        profile.city = request.POST.get('city')
        profile.country = request.POST.get('country')
        profile.bio = request.POST.get('bio')

        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'profile': profile})


# =========================
# VERIFY EMAIL
# =========================
def verify_email(request, token):
    verification = get_object_or_404(EmailVerification, token=token, is_used=False)
    verification.user.is_verified = True
    verification.user.save()
    verification.is_used = True
    verification.save()
    messages.success(request, "Email verified! You can now login.")
    return redirect('accounts:login')


# =========================
# REQUEST PASSWORD RESET
# =========================
def request_password_reset(request):
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            reset = PasswordReset.objects.create(user=user)
            reset_link = f"http://127.0.0.1:8000/reset-password/{reset.token}/"
            send_mail(
                "Password Reset",
                f"Click to reset: {reset_link}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )

        messages.success(request, "If email exists, reset link sent")
        return redirect('accounts:login')

    return render(request, 'accounts/reset_request.html')


# =========================
# RESET PASSWORD
# =========================
def reset_password(request, token):
    reset = get_object_or_404(PasswordReset, token=token, is_used=False)

    if request.method == "POST":
        password = request.POST.get('password')
        user = reset.user
        user.set_password(password)
        user.save()
        reset.is_used = True
        reset.save()
        messages.success(request, "Password reset successful")
        return redirect('accounts:login')

    return render(request, 'accounts/reset_password.html')