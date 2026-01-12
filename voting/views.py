from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Count
import random
import logging

from .models import OTP, VoterProfile, Candidate, Vote, Constituency
from .forms import VoterRegistrationForm

logger = logging.getLogger(__name__)

# ---------------- HOME ----------------
def home(request):
    return render(request, 'home.html')


# ---------------- REGISTER ----------------
def register(request):
    if request.method == 'POST':
        form = VoterRegistrationForm(request.POST)
        voter_id = request.POST.get('voter_id')
        constituency_id = request.POST.get('constituency')

        if form.is_valid():
            if VoterProfile.objects.filter(voter_id=voter_id).exists():
                return render(request, 'register.html', {
                    'form': form,
                    'constituencies': Constituency.objects.all(),
                    'error': 'Voter ID already exists'
                })

            user = form.save(commit=False)
            user.is_active = True
            user.save()

            constituency = Constituency.objects.get(id=constituency_id)
            VoterProfile.objects.create(
                user=user,
                voter_id=voter_id,
                constituency=constituency
            )

            # OTP
            otp_code = str(random.randint(100000, 999999))
            OTP.objects.update_or_create(user=user, defaults={'code': otp_code})

            # 🔐 SAFE EMAIL SEND
            try:
                send_mail(
                    subject='Your Voting OTP',
                    message=f'Your OTP is: {otp_code}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,  # ✅ IMPORTANT
                )
            except Exception as e:
                logger.error(f"OTP Email failed: {e}")

            # ✅ LOG OTP FOR DEMO
            print("OTP FOR USER:", user.username, otp_code)

            request.session['otp_user'] = user.username
            return redirect('verify_otp')

    else:
        form = VoterRegistrationForm()

    return render(request, 'register.html', {
        'form': form,
        'constituencies': Constituency.objects.all()
    })


# ---------------- VERIFY OTP ----------------
def verify_otp(request):
    username = request.session.get('otp_user')
    if not username:
        return redirect('login')

    user = User.objects.get(username=username)
    otp_obj = OTP.objects.get(user=user)

    if request.method == 'POST':
        if request.POST.get('otp') == otp_obj.code:
            login(request, user)
            otp_obj.delete()
            return redirect('vote')
        else:
            return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})

    return render(request, 'verify_otp.html')
