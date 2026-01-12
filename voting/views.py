import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.db.models import Count

from .models import OTP, VoterProfile, Candidate, Vote, Constituency
from .forms import VoterRegistrationForm


# ---------------- HOME ----------------
def home(request):
    return render(request, "home.html")


# ---------------- REGISTER ----------------
def register(request):
    if request.method == "POST":
        form = VoterRegistrationForm(request.POST)
        voter_id = request.POST.get("voter_id")
        constituency_id = request.POST.get("constituency")

        if not voter_id or not constituency_id:
            return render(request, "register.html", {
                "form": form,
                "constituencies": Constituency.objects.all(),
                "error": "All fields are required"
            })

        if form.is_valid():
            if VoterProfile.objects.filter(voter_id=voter_id).exists():
                return render(request, "register.html", {
                    "form": form,
                    "constituencies": Constituency.objects.all(),
                    "error": "Voter ID already registered"
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

            otp_code = str(random.randint(100000, 999999))
            OTP.objects.update_or_create(
                user=user,
                defaults={"code": otp_code}
            )

            # ✅ SAFE EMAIL SEND (NO CRASH)
            try:
                send_mail(
                    subject="Your Voting OTP",
                    message=f"Your OTP is: {otp_code}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print("OTP email failed:", e)

            request.session["otp_user"] = user.username
            return redirect("verify_otp")

    else:
        form = VoterRegistrationForm()

    return render(request, "register.html", {
        "form": form,
        "constituencies": Constituency.objects.all()
    })


# ---------------- VERIFY OTP ----------------
def verify_otp(request):
    username = request.session.get("otp_user")
    if not username:
        return redirect("login")

    try:
        user = User.objects.get(username=username)
        otp_obj = OTP.objects.get(user=user)
    except (User.DoesNotExist, OTP.DoesNotExist):
        return redirect("login")

    if request.method == "POST":
        entered_otp = request.POST.get("otp")

        if entered_otp == otp_obj.code:
            login(request, user)
            otp_obj.delete()
            return redirect("vote")

        return render(request, "verify_otp.html", {
            "error": "Invalid OTP"
        })

    return render(request, "verify_otp.html")


# ---------------- OTP LOGIN ----------------
def otp_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        voter_id = request.POST.get("voter_id")

        user = authenticate(request, username=username, password=password)
        if not user:
            return render(request, "otp_login.html", {
                "error": "Invalid username or password"
            })

        try:
            profile = VoterProfile.objects.get(user=user)
        except VoterProfile.DoesNotExist:
            return render(request, "otp_login.html", {
                "error": "Voter profile not found"
            })

        if profile.voter_id != voter_id:
            return render(request, "otp_login.html", {
                "error": "Invalid Voter ID"
            })

        otp_code = str(random.randint(100000, 999999))
        OTP.objects.update_or_create(
            user=user,
            defaults={"code": otp_code}
        )

        try:
            send_mail(
                subject="Your Voting OTP",
                message=f"Your OTP is: {otp_code}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print("OTP email failed:", e)

        request.session["otp_user"] = user.username
        return redirect("verify_otp")

    return render(request, "otp_login.html")


# ---------------- VOTE ----------------
@login_required
def vote(request):
    profile = VoterProfile.objects.get(user=request.user)

    if Vote.objects.filter(user=request.user).exists():
        return render(request, "already_voted.html")

    candidates = Candidate.objects.filter(constituency=profile.constituency)

    if request.method == "POST":
        candidate_id = request.POST.get("candidate")
        candidate = Candidate.objects.get(id=candidate_id)

        Vote.objects.create(user=request.user, candidate=candidate)

        return render(request, "voting/vote_success.html", {
            "constituency": profile.constituency.name,
            "candidate": candidate
        })

    return render(request, "voting/vote.html", {
        "candidates": candidates
    })


# ---------------- RESULT ----------------
@login_required
def result(request):
    results = Vote.objects.values("candidate__name").annotate(
        total=Count("candidate")
    )
    return render(request, "result.html", {"results": results})
