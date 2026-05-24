from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def create_property(request):
    return render(request, 'listings/create.html')