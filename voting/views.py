from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
import random
from django.contrib.auth import authenticate
from .models import OTP, VoterProfile
from django.shortcuts import render, redirect
from .forms import VoterRegistrationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Candidate, Vote
def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = VoterRegistrationForm(request.POST)
        voter_id = request.POST.get('voter_id')

        if form.is_valid():
            user = form.save()
            VoterProfile.objects.create(user=user, voter_id=voter_id)
            login(request, user)
            return redirect('vote')
    else:
        form = VoterRegistrationForm()

    return render(request, 'register.html', {'form': form})

@login_required
def vote(request):
    if Vote.objects.filter(user=request.user).exists():
        return render(request, 'already_voted.html')

    candidates = Candidate.objects.all()

    if request.method == 'POST':
        candidate_id = request.POST.get('candidate')
        candidate = Candidate.objects.get(id=candidate_id)
        Vote.objects.create(user=request.user, candidate=candidate)
        return redirect('result')

    return render(request, 'vote.html', {'candidates': candidates})


@login_required
def result(request):
    from django.db.models import Count
    results = Vote.objects.values('candidate__name').annotate(total=Count('candidate'))
    return render(request, 'result.html', {'results': results})
def otp_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        voter_id = request.POST.get('voter_id')

        user = authenticate(username=username, password=password)

        if user:
            try:
                profile = VoterProfile.objects.get(user=user)
                if profile.voter_id != voter_id:
                    return render(request, 'otp_login.html', {'error': 'Invalid Voter ID'})
            except VoterProfile.DoesNotExist:
                return render(request, 'otp_login.html', {'error': 'Voter profile not found'})

            otp_code = str(random.randint(100000, 999999))
            OTP.objects.update_or_create(user=user, defaults={'code': otp_code})

            # ✅ SEND OTP TO EMAIL
            send_mail(
                subject='Your Voting OTP',
                message=f'Your OTP is: {otp_code}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            request.session['otp_user'] = user.username
            return redirect('verify_otp')

        return render(request, 'otp_login.html', {'error': 'Invalid login details'})

    return render(request, 'otp_login.html')

def verify_otp(request):
    username = request.session.get('otp_user')
    if not username:
        return redirect('otp_login')

    user = User.objects.get(username=username)

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        otp_obj = OTP.objects.get(user=user)

        if otp_obj.code == entered_otp:
            login(request, user)
            otp_obj.delete()
            return redirect('vote')
        else:
            return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})

    return render(request, 'verify_otp.html')
