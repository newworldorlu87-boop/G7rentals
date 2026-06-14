from bookings.models import Booking


def pending_bookings_count(request):
    count = 0
    if request.user.is_authenticated and getattr(request.user, 'user_type', None) == 'landlord':
        count = Booking.objects.filter(
            property__owner=request.user,
            status='pending'
        ).count()
    return {'pending_bookings_count': count}