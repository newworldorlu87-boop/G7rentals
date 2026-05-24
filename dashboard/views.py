from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from accounts.models import User
from listings.models import Property
from bookings.models import Booking


@login_required
def admin_dashboard(request):

    # Allow only superusers/admins
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access denied")

    landlords = User.objects.filter(user_type='landlord')
    tenants = User.objects.filter(user_type='tenant')

    properties = Property.objects.all().order_by('-created_at')

    bookings = Booking.objects.all()
    context = {
        'landlords': landlords,
        'tenants': tenants,
        'properties': properties,
        'bookings': bookings,

        'total_landlords': landlords.count(),
        'total_tenants': tenants.count(),
        'total_properties': properties.count(),
        'total_bookings': bookings.count(),
    }

    return render(request, 'dashboard/admin_dashboard.html', context)