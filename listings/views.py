from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q, Count, Max, Prefetch, Sum  # ← ADD Sum here
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator

from accounts.models import User
from .models import Property, Favorite, Message
from .forms import PropertyForm, ContactLandlordForm, MessageForm
from bookings.models import Booking  # ← ADD THIS IMPORT

# =========================
# HOME PAGE
# =========================
def index(request):
    """Homepage with featured properties."""
    properties = Property.objects.all().order_by('-created_at')[:6]
    return render(request, 'listings/index.html', {'properties': properties})


# =========================
# PROPERTY LIST + SEARCH
# =========================
@login_required
def property_list(request):
    """List all properties with search functionality."""
    query = request.GET.get('q')
    properties = Property.objects.all().order_by('-created_at')

    if query:
        properties = properties.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query) |
            Q(property_type__icontains=query)
        )

    # Get favorites for heart icons
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(
            Favorite.objects.filter(user=request.user)
            .values_list('property_id', flat=True)
        )

    return render(request, 'listings/property_list.html', {
        'properties': properties,
        'favorite_ids': favorite_ids,
        'query': query
    })


# =========================
# CREATE PROPERTY
# =========================
@login_required
def create_property(request):
    """Create a new property listing (landlord only)."""
    if request.user.user_type != 'landlord':
        return HttpResponseForbidden("Only landlords can add properties.")

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.save()
            messages.success(request, "Property created successfully!")
            return redirect('listings:property_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PropertyForm()

    return render(request, 'listings/create_property.html', {
        'form': form,
        'is_edit': False
    })


# =========================
# UPDATE PROPERTY
# =========================
@login_required
def update_property(request, id):
    """Update an existing property (owner only)."""
    property_obj = get_object_or_404(Property, id=id, owner=request.user)

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Property updated successfully!")
            return redirect('listings:property_detail', id=property_obj.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PropertyForm(instance=property_obj)

    return render(request, 'listings/property_update.html', {
        'form': form,
        'property': property_obj,
        'is_edit': True
    })


# =========================
# DELETE PROPERTY
# =========================
@login_required
def delete_property(request, id):
    """Delete a property (owner only)."""
    property_obj = get_object_or_404(Property, id=id, owner=request.user)

    if request.method == "POST":
        property_obj.delete()
        messages.success(request, "Property deleted successfully!")
        return redirect('listings:property_list')

    return render(request, 'listings/property_confirm_delete.html', {
        'property': property_obj
    })


# =========================
# PROPERTY DETAIL
# =========================
@login_required
def property_detail(request, id):
    """View property details and contact landlord."""
    property_obj = get_object_or_404(Property, id=id)

    # Check if favorited
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(
            user=request.user, property=property_obj
        ).exists()

    # Contact form
    form = ContactLandlordForm()
    if request.method == "POST":
        form = ContactLandlordForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = property_obj.owner
            msg.property = property_obj
            msg.save()
            messages.success(request, "Message sent to landlord!")
            return redirect('listings:property_detail', id=property_obj.id)

    return render(request, 'listings/property_detail.html', {
        'property': property_obj,
        'is_favorite': is_favorite,
        'form': form
    })


# =========================
# BOOK PROPERTY
# =========================
@login_required
def book_property(request, property_id):
    """Book a property (tenant only)."""
    property_obj = get_object_or_404(Property, id=property_id)

    if request.user.user_type != 'tenant':
        return HttpResponseForbidden("Only tenants can book properties.")

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        notes = request.POST.get('notes', '')

        # Validate dates
        from datetime import datetime
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Please provide valid dates.")
            return redirect('listings:property_detail', id=property_obj.id)

        if start >= end:
            messages.error(request, "Check-out date must be after check-in date.")
            return redirect('listings:property_detail', id=property_obj.id)

        if start < timezone.now().date():
            messages.error(request, "Check-in date cannot be in the past.")
            return redirect('listings:property_detail', id=property_obj.id)

        # Calculate total price (daily rate * days)
        days = (end - start).days
        total = property_obj.price * days

        # Check for overlapping approved bookings
        overlapping = Booking.objects.filter(
            property=property_obj,
            status='approved',
            start_date__lt=end,
            end_date__gt=start
        ).exists()

        if overlapping:
            messages.error(request, "This property is not available for the selected dates.")
            return redirect('listings:property_detail', id=property_obj.id)

        # Create booking
        booking = Booking.objects.create(
            property=property_obj,
            tenant=request.user,
            landlord=property_obj.owner,
            start_date=start,
            end_date=end,
            total_price=total,
            notes=notes
        )

        messages.success(
            request,
            f"Booking request sent for {property_obj.title}! "
            f"Dates: {start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}. "
            f"Waiting for landlord approval."
        )
        return redirect('listings:my_bookings')  # Tenant's booking page

    # GET request - show booking form
    return render(request, 'listings/book_property.html', {
        'property': property_obj
    })
# =========================
# LANDLORD: VIEW ALL BOOKINGS
# =========================
@login_required
def landlord_bookings(request):
    """Landlord sees all bookings for their properties."""
    if request.user.user_type != 'landlord':
        return HttpResponseForbidden("Only landlords can access this page.")

    bookings = Booking.objects.filter(
        property__owner=request.user
    ).select_related('property', 'tenant').order_by('-created_at')

    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        bookings = bookings.filter(status=status_filter)

    # Stats
    pending_count = bookings.filter(status='pending').count()
    total_earnings = bookings.filter(status='approved').aggregate(
        total=Sum('total_price')
    )['total'] or 0

    return render(request, 'listings/landlord_bookings.html', {
        'bookings': bookings,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'total_earnings': total_earnings,
        'status_choices': Booking.STATUS_CHOICES,
    })


# =========================
# LANDLORD: APPROVE/REJECT BOOKING
# =========================
@login_required
def update_booking_status(request, booking_id):
    """Landlord approves or rejects a booking."""
    if request.user.user_type != 'landlord':
        return HttpResponseForbidden("Only landlords can update bookings.")

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        property__owner=request.user  # Must own the property
    )

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['approved', 'rejected', 'cancelled']:
            old_status = booking.status
            booking.status = new_status
            booking.save()

            # If approved, reject overlapping pending bookings
            if new_status == 'approved':
                Booking.objects.filter(
                    property=booking.property,
                    status='pending',
                    start_date__lt=booking.end_date,
                    end_date__gt=booking.start_date
                ).exclude(id=booking.id).update(status='rejected')

                # Mark property as occupied
                booking.property.status = 'occupied'
                booking.property.is_available = False
                booking.property.save()

            action = "approved" if new_status == 'approved' else "rejected"
            messages.success(
                request,
                f"Booking #{booking.id} has been {action}. "
                f"Tenant: {booking.tenant.get_full_name() or booking.tenant.username}"
            )

        return redirect('listings:landlord_bookings')

    return render(request, 'listings/booking_action.html', {
        'booking': booking
    })


# =========================
# TENANT: MY BOOKINGS
# =========================
@login_required
def my_bookings(request):
    """Tenant sees their own bookings."""
    if request.user.user_type != 'tenant':
        return HttpResponseForbidden("Only tenants can view their bookings.")

    bookings = Booking.objects.filter(
        tenant=request.user
    ).select_related('property', 'landlord').order_by('-created_at')

    return render(request, 'listings/my_bookings.html', {
        'bookings': bookings
    })

# =========================
# CHAT VIEW
# =========================
@login_required
def chat_view(request, user_id, property_id):
    """
    Real-time chat between tenant and landlord about a specific property.
    Both parties can view and send messages.
    """
    other_user = get_object_or_404(User, id=user_id)
    property_obj = get_object_or_404(Property, id=property_id)

    # Security check: must be involved in this conversation
    is_owner = request.user == property_obj.owner
    is_other = request.user == other_user

    # Must be either the property owner or the other party
    if not is_owner and not is_other:
        # Check if they have any existing messages
        has_messages = Message.objects.filter(
            Q(sender=request.user, receiver=other_user) |
            Q(sender=other_user, receiver=request.user),
            property=property_obj
        ).exists()

        if not has_messages:
            return HttpResponseForbidden("You are not authorized to view this chat.")

    # Handle message submission
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = other_user
            msg.property = property_obj
            msg.name = request.user.get_full_name() or request.user.username
            msg.email = request.user.email
            msg.save()
            messages.success(request, "Message sent!")
            return redirect('listings:chat', user_id=other_user.id, property_id=property_obj.id)
    else:
        form = MessageForm()

    # Get all messages between these two users about this property
    chats = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user),
        property=property_obj
    ).select_related('sender', 'receiver').order_by('created_at')

    # Mark messages as read
    Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        property=property_obj,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())

    return render(request, 'listings/chat.html', {
        'other_user': other_user,
        'property': property_obj,
        'chats': chats,
        'form': form,
        'is_owner': is_owner,
    })


# =========================
# INBOX
# =========================
@login_required
def inbox(request):
    """
    Show all conversations grouped by (other_user, property) pair.
    Displays last message, unread count, and property info.
    """
    # Get all messages involving current user
    user_messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver', 'property').order_by('-created_at')

    # Group into conversations
    conversations_dict = {}
    for msg in user_messages:
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        key = (other_user.id, msg.property.id)

        if key not in conversations_dict:
            conversations_dict[key] = {
                'other_user': other_user,
                'property': msg.property,
                'last_message': msg,
                'unread_count': 0,
            }

        # Count unread messages where current user is receiver
        if msg.receiver == request.user and not msg.is_read:
            conversations_dict[key]['unread_count'] += 1

    conversations_list = list(conversations_dict.values())

    return render(request, 'listings/inbox.html', {
        'conversations': conversations_list,
        'total_unread': sum(c['unread_count'] for c in conversations_list)
    })


# =========================
# CONVERSATIONS (alias)
# =========================
@login_required
def conversations(request):
    """Redirect to inbox."""
    return redirect('listings:inbox')


# =========================
# MY PROPERTIES
# =========================
@login_required
def my_properties(request):
    """List properties owned by current user."""
    properties = Property.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'listings/my_properties.html', {
        'properties': properties
    })


# =========================
# TOGGLE FAVORITE
# =========================
@login_required
def toggle_favorite(request, property_id):
    """Add or remove property from favorites."""
    property_obj = get_object_or_404(Property, id=property_id)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user, property=property_obj
    )
    if not created:
        favorite.delete()
        messages.success(request, "Removed from favorites.")
    else:
        messages.success(request, "Added to favorites!")
    return redirect(request.META.get('HTTP_REFERER', 'listings:property_list'))


# =========================
# AJAX: GET NEW MESSAGES
# =========================
@login_required
def get_new_messages(request, user_id, property_id):
    """AJAX endpoint to fetch new messages since last ID."""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    other_user = get_object_or_404(User, id=user_id)
    property_obj = get_object_or_404(Property, id=property_id)
    last_id = request.GET.get('last_id', 0)

    new_messages = Message.objects.filter(
        Q(sender=other_user, receiver=request.user) |
        Q(sender=request.user, receiver=other_user),
        property=property_obj,
        id__gt=last_id
    ).select_related('sender').order_by('created_at')

    data = []
    for msg in new_messages:
        data.append({
            'id': msg.id,
            'message': msg.message,
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
            'sender_initial': (msg.sender.get_full_name() or msg.sender.username)[0].upper(),
            'created_at': msg.created_at.strftime('%g:%i A'),
            'is_me': msg.sender == request.user,
            'is_read': msg.is_read,
        })

    return JsonResponse({'messages': data})


# =========================
# AJAX: MARK AS READ
# =========================
@login_required
def mark_read(request, user_id, property_id):
    """AJAX endpoint to mark messages as read."""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    other_user = get_object_or_404(User, id=user_id)
    property_obj = get_object_or_404(Property, id=property_id)

    updated = Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        property=property_obj,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())

    return JsonResponse({'marked_read': updated})
# =========================
# STATIC PAGES
# =========================

def about(request):
    """About Us page."""
    return render(request, 'listings/about.html')


def contact(request):
    """Contact page with form."""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you can send email or save to database
        # For now, just show success message
        messages.success(request, f"Thank you {name}! Your message has been received. We'll respond to {email} within 24 hours.")
        return redirect('listings:contact')
    
    return render(request, 'listings/contact.html')


def privacy(request):
    """Privacy Policy page."""
    return render(request, 'listings/privacy.html')

def terms(request):
    """Terms of Service page."""
    return render(request, 'listings/terms.html')


def cookies(request):
    """Cookies Policy page."""
    return render(request, 'listings/cookies.html')