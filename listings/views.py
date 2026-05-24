from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages

from .models import Property, Favorite, Message
from .forms import PropertyForm, ContactLandlordForm

# 🏠 HOME PAGE
def index(request):

    properties = Property.objects.all().order_by(
        '-created_at'
    )[:6]

    return render(
    request,
    'listings/index.html',
        {
            'properties': properties
        }
    )
# 🏠 PROPERTY LIST + SEARCH
@login_required
def property_list(request):

    query = request.GET.get('q')

    properties = Property.objects.all().order_by('-created_at')

    # 🔍 SEARCH
    if query:
        properties = properties.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query) |
            Q(property_type__icontains=query)
        )

    favorites = []

    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(
            user=request.user
        ).values_list('property_id', flat=True)

    return render(request, 'listings/property_list.html', {
        'properties': properties,
        'favorites': favorites,
        'query': query
    })


# ➕ CREATE PROPERTY
@login_required
def create_property(request):

    # BLOCK TENANTS
    if request.user.user_type != 'landlord':
        return HttpResponseForbidden(
            "Only landlords can add properties."
        )

    if request.method == "POST":

        form = PropertyForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            property = form.save(commit=False)

            # SAVE OWNER
            property.owner = request.user

            property.save()

            messages.success(
                request,
                "Property created successfully!"
            )

            return redirect('property_list')

        else:
            print(form.errors)

    else:
        form = PropertyForm()

    return render(
        request,
        'listings/create_property.html',
        {
            'form': form
        }
    )


# 🏡 PROPERTY DETAIL
@login_required
def property_detail(request, id):

    property = get_object_or_404(
        Property,
        id=id
    )

    favorites = []

    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(
            user=request.user
        ).values_list(
            'property_id',
            flat=True
        )

    form = ContactLandlordForm()

    # 📩 SEND MESSAGE
    if request.method == "POST":

        if request.user.is_authenticated:

            form = ContactLandlordForm(
                request.POST
            )

            if form.is_valid():

                msg = form.save(commit=False)

                msg.sender = request.user
                msg.receiver = property.owner
                msg.property = property

                msg.save()

                messages.success(
                    request,
                    "Message sent successfully!"
                )

                return redirect(
                    'detail',
                    pk=property.pk
                )

        else:
            return redirect('login')

    return render(
        request,
        'listings/property_detail.html',
        {
            'property': property,
            'favorites': favorites,
            'form': form
        }
    )

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from accounts.models import User
from .models import Message, Property
from .forms import MessageForm


@login_required
def chat_view(request, user_id, property_id):

    other_user = get_object_or_404(
        User,
        id=user_id
    )

    property = get_object_or_404(
        Property,
        id=property_id
    )

    # ALLOW ONLY:
    # 1. PROPERTY OWNER
    # 2. USERS WHO HAVE CHATTED ABOUT PROPERTY

    is_owner = request.user == property.owner

    has_chat = Message.objects.filter(
        property=property,
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user]
    ).exists()

    if not is_owner and not has_chat:
        return redirect('property_list')

    # GET CHAT THREAD
    chats = Message.objects.filter(
        property=property,
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user]
    ).order_by('created_at')

    form = MessageForm()

    # SEND MESSAGE
    if request.method == 'POST':

        form = MessageForm(request.POST)

        if form.is_valid():

            msg = form.save(commit=False)

            msg.sender = request.user
            msg.receiver = other_user
            msg.property = property

            msg.name = request.user.username
            msg.email = request.user.email

            msg.save()

            return redirect(
                'chat',
                user_id=other_user.id,
                property_id=property.id
            )
        # MARK RECEIVED MESSAGES AS READ
    Message.objects.filter(
        property=property,
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)
    
    return render(request, 'listings/chat.html', {
        'other_user': other_user,
        'property': property,
        'chats': chats,
        'form': form
    })

# 👤 MY PROPERTIES
@login_required
def my_properties(request):

    properties = Property.objects.filter(
        owner=request.user
    )

    return render(
        request,
        'listings/my_properties.html',
        {
            'properties': properties
        }
    )


# ❤️ TOGGLE FAVORITES
@login_required
def toggle_favorite(request, property_id):

    property = get_object_or_404(
        Property,
        id=property_id
    )

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        property=property
    )

    # REMOVE IF EXISTS
    if not created:
        favorite.delete()

    return redirect(
        request.META.get(
            'HTTP_REFERER',
            'property_list'
        )
    )


@login_required
def inbox(request):

    messages_received = Message.objects.filter(
        receiver=request.user
    ).select_related(
        'sender',
        'property'
    ).order_by('-created_at')

    return render(
        request,
        'listings/inbox.html',
        {
            'messages_received': messages_received
        }
    )
from django.db.models import Q


@login_required
def conversations(request):

    messages_list = Message.objects.filter(
        Q(sender=request.user) |
        Q(receiver=request.user)
    ).select_related(
        'sender',
        'receiver',
        'property'
    ).order_by('-created_at')

    conversations = []

    seen = set()

    for msg in messages_list:

        if msg.sender == request.user:
            other_user = msg.receiver
        else:
            other_user = msg.sender

        key = (other_user.id, msg.property.id)

        if key not in seen:

            seen.add(key)

            conversations.append({
                'user': other_user,
                'property': msg.property,
                'last_message': msg,
            })

    return render(
        request,
        'listings/conversations.html',
        {
            'conversations': conversations
        }
    )