from django.urls import path
from . import views

urlpatterns = [
    path('book/<int:pk>/', views.book_property, name='book_property'),
    path('booking/<int:booking_id>/accept/',views.accept_booking,name='accept_booking'),
    path('booking/<int:booking_id>/reject/',views.reject_booking,name='reject_booking'),
]