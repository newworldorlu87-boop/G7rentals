from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    # Home & Properties
    path('', views.index, name='index'),
    path('property-list/', views.property_list, name='property_list'),
    path('detail/<int:id>/', views.property_detail, name='detail'),
    path('property/<int:id>/', views.property_detail, name='property_detail'),
    
    # Property CRUD (Landlord)
    path('create/', views.create_property, name='property_create'),
    path('my-properties/', views.my_properties, name='my_properties'),
    path('my-properties/create/', views.create_property, name='my_property_create'),
    path('property/<int:id>/edit/', views.update_property, name='property_update'),
    path('property/<int:id>/delete/', views.delete_property, name='property_delete'),
    
     # Bookings & Favorites
    path('book/<int:property_id>/', views.book_property, name='book_property'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('landlord/bookings/', views.landlord_bookings, name='landlord_bookings'),
    path('booking/<int:booking_id>/update/', views.update_booking_status, name='update_booking_status'),
    path('favorite/<int:property_id>/', views.toggle_favorite, name='toggle_favorite'),
    
    
    
    # Messaging System
    path('inbox/', views.inbox, name='inbox'),
    path('messages/', views.conversations, name='conversations'),
    path('chat/<int:user_id>/<int:property_id>/', views.chat_view, name='chat'),
    
    # AJAX Endpoints for Real-time Chat
    path('ajax/messages/<int:user_id>/<int:property_id>/', views.get_new_messages, name='get_new_messages'),
    path('ajax/mark-read/<int:user_id>/<int:property_id>/', views.mark_read, name='mark_read'),

        # Static Pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),

    path('terms/', views.terms, name='terms'),
    path('cookies/', views.cookies, name='cookies'),
]