from django.urls import path
from . import views
from .views import profile_view

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards
    path('dashboard/tenant/', views.tenant_dashboard, name='tenant_dashboard'),
    path('dashboard/landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    
    # Verification & Password Reset
    path('verify/<uuid:token>/', views.verify_email, name='verify_email'),
    path('reset/', views.request_password_reset, name='reset_request'),
    path('reset-password/<uuid:token>/', views.reset_password, name='reset_password'),
    
    # ============================================
    # NOTIFICATIONS (NEW)
    # ============================================
    
    # Admin: send notification
    path('admin/send-notification/', views.send_notification, name='send_notification'),
    
    # User: view notifications inbox
    path('notifications/', views.user_notifications, name='user_notifications'),
    
    # User: mark notification as read
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]