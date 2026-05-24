from django.shortcuts import render, redirect, get_object_or_404
from .models import Booking
from django.contrib.auth.decorators import login_required
from listings.models import Property


@login_required
def book_property(request, pk):

    property = get_object_or_404(
        Property,
        id=pk
    )

    if request.method == "POST":

        Booking.objects.create(
            property=property,
            user=request.user,
            start_date=request.POST['start_date'],
            end_date=request.POST['end_date']
        )

        return redirect('tenant_dashboard')

    return render(
        request,
        'bookings/book.html',
        {
            'property': property
        }
    )


# ✅ ACCEPT BOOKING
@login_required
def accept_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    # 🔥 SECURITY CHECK
    if booking.property.owner != request.user:
        return redirect('landlord_dashboard')

    booking.status = 'Approved'
    booking.save()

    return redirect('landlord_dashboard')


# ❌ REJECT BOOKING
@login_required
def reject_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    # 🔥 SECURITY CHECK
    if booking.property.owner != request.user:
        return redirect('landlord_dashboard')

    booking.status = 'Rejected'
    booking.save()

    return redirect('landlord_dashboard')