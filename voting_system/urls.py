from django.contrib import admin
from django.urls import path
from voting import views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),

    path('register/', views.register, name='register'),

    path('login/', views.otp_login, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    # ✅ LOGOUT (POST ONLY)
    path(
        'logout/',
        LogoutView.as_view(next_page='login'),
        name='logout'
    ),

    path('vote/', views.vote, name='vote'),
    path('result/', views.result, name='result'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
