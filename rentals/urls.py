from django.urls import path
from . import views

urlpatterns = [
    
    path('property/<int:pk>/', views.detail, name='detail'),
    path('property/<int:pk>/book/', views.create_booking, name='create_booking'),
    
]