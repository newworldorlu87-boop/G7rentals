from django.shortcuts import render, get_object_or_404, redirect
from .models import Property, Booking
from django.shortcuts import render, get_object_or_404
from .models import Property

def detail(request, pk):

    property = get_object_or_404(
        Property,
        id=pk
    )

    return render(
        request,
        'rentals/detail.html',
        {
            'property': property
        }
    )

def create_booking(request, pk):
    property = get_object_or_404(Property, pk=pk)

    if request.method == "POST":
        Booking.objects.create(
            property=property,
            customer_name=request.POST['name'],
            start_date=request.POST['start_date'],
            end_date=request.POST['end_date']
        )
        return redirect('index')

    return render(request, 'rentals/create.html', {'property': property})