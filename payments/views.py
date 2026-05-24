from django.conf import settings
from django.shortcuts import redirect, get_object_or_404, render
from bookings.models import Booking


def pay(request, booking_id):
    booking = Booking.objects.get(id=booking_id)

    url = "https://api.paystack.co/transaction/initialize"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    data = {
        "email": request.user.email,
        "amount": int(booking.property.price * 100)
    }

    res = request.post(url, json=data, headers=headers).json()
    return redirect(res['data']['authorization_url'])