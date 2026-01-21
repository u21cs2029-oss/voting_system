"""
voting/urls.py - URL configuration for voting app
"""
from . import analytics_views
from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Registration & OTP
    path('register/', views.register, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    
    # Login & Logout
    path('login/', views.otp_login, name='otp_login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Voting
    path('vote/', views.vote, name='vote'),
    path('already-voted/', views.already_voted, name='already_voted'),
    
    # Results
    path('result/', views.result, name='result'),

    # Analytics URLs (Admin only)
    path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/patterns/', analytics_views.pattern_analysis, name='pattern_analysis'),
    path('analytics/ml/', analytics_views.ml_predictions, name='ml_predictions'),
    path('analytics/anomalies/', analytics_views.anomaly_detection, name='anomaly_detection'),
]