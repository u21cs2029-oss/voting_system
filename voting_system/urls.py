from django.contrib import admin
from django.urls import path
from voting import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),                     # Landing page
    path('admin/', admin.site.urls),

    path('register/', views.register, name='register'),

    # ✅ USE OTP LOGIN AS MAIN LOGIN
    path('login/', views.otp_login, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    path('logout/', LogoutView.as_view(), name='logout'),

    path('vote/', views.vote, name='vote'),
    path('result/', views.result, name='result'),
]
