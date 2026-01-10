from django.contrib import admin
from django.urls import path
from voting import views
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

def home(request):
    return redirect('login')

urlpatterns = [
    path('', home),  # 👈 ADD THIS LINE
    path('admin/', admin.site.urls),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('vote/', views.vote, name='vote'),
    path('result/', views.result, name='result'),
    path('otp-login/', views.otp_login, name='otp_login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

]
