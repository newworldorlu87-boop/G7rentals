from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/tenant/', views.tenant_dashboard, name='tenant_dashboard'),
    path('dashboard/landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('favorite/<int:property_id>/', views.toggle_favorite, name='toggle_favorite'),
    
    # Property Management (landlord backend)
    path('my-properties/', views.property_list, name='property_list'),
    path('my-properties/create/', views.property_create, name='property_create'),
    path('my-properties/<int:pk>/', views.property_detail, name='property_detail'),
    path('my-properties/<int:pk>/edit/', views.property_update, name='property_update'),
    path('my-properties/<int:pk>/delete/', views.property_delete, name='property_delete'),
    path('my-properties/<int:pk>/toggle-status/', views.property_toggle_status, name='property_toggle_status'),
    
    # Verification & Password Reset
    path('verify/<uuid:token>/', views.verify_email, name='verify_email'),
    path('reset/', views.request_password_reset, name='reset_request'),
    path('reset-password/<uuid:token>/', views.reset_password, name='reset_password'),
    
    # Notifications
    path('admin/send-notification/', views.send_notification, name='send_notification'),
    path('notifications/', views.user_notifications, name='user_notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),

    path(
    'booking/<int:booking_id>/approve/',
    views.approve_booking,
    name='approve_booking'
),

path(
    'booking/<int:booking_id>/reject/',
    views.reject_booking,
    name='reject_booking'
),
]
