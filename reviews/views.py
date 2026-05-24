def dashboard(request):
    if request.user.user_type == 'landlord':
        properties = Property.objects.filter(owner=request.user)
        return render(request, 'dashboard/landlord.html', {'properties': properties})

    bookings = Booking.objects.filter(user=request.user)
    return render(request, 'dashboard/tenant.html', {'bookings': bookings})