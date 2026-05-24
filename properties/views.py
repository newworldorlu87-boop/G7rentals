from django.shortcuts import render, redirect
from .models import Property
from .forms import PropertyForm
from django.contrib.auth.decorators import login_required

def property_list(request):
    query = request.GET.get('q')
    properties = Property.objects.all()

    if query:
        properties = properties.filter(location__icontains=query)

    return render(request, 'properties/list.html', {'properties': properties})


@login_required
def add_property(request):
    form = PropertyForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        prop = form.save(commit=False)
        prop.owner = request.user
        prop.save()
        return redirect('dashboard')

    return render(request, 'properties/add.html', {'form': form})