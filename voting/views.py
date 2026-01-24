"""
Updated views.py - Fixed admin access and login redirect issues
"""

import logging
import json
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.utils import timezone

from .models import OTP, VoterProfile, Candidate, Vote, Constituency
from .forms import VoterRegistrationForm
from .utils import generate_otp, send_otp_email, verify_otp

logger = logging.getLogger(__name__)


# ---------------- HOME ----------------
def home(request):
    """Home page view"""
    return render(request, "voting/home.html")


# ---------------- ADMIN CHOICE ----------------
def admin_choice(request):
    """
    Admin login page - allows admin to login with username/password
    Regular users use OTP login, admins can use this page
    """
    # If already logged in as admin, redirect to home (they'll see admin dashboard)
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('home')
    
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        
        if not username or not password:
            messages.error(request, "Both username and password are required")
            return render(request, "voting/admin_choice.html")
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            messages.error(request, "Invalid username or password")
            return render(request, "voting/admin_choice.html")
        
        # Check if user is admin
        if not (user.is_staff or user.is_superuser):
            messages.error(request, "Admin access required. Please use voter login.")
            return render(request, "voting/admin_choice.html")
        
        # Login the admin user
        login(request, user)
        messages.success(request, f"Welcome back, {user.username}!")
        logger.info(f"Admin {user.username} logged in successfully")
        
        # Redirect to home - they'll see admin dashboard
        return redirect('home')
    
    return render(request, 'voting/admin_choice.html')


# ---------------- REGISTER ----------------
def register(request):
    """Voter registration with OTP verification"""
    if request.method == "POST":
        form = VoterRegistrationForm(request.POST)
        voter_id = request.POST.get("voter_id", "").strip()
        constituency_id = request.POST.get("constituency", "").strip()

        if not voter_id or not constituency_id:
            messages.error(request, "All fields are required")
            return render(request, "voting/register.html", {
                "form": form,
                "constituencies": Constituency.objects.all()
            })

        if not form.is_valid():
            messages.error(request, "Please correct the errors in the form")
            return render(request, "voting/register.html", {
                "form": form,
                "constituencies": Constituency.objects.all()
            })

        try:
            if VoterProfile.objects.filter(voter_id=voter_id).exists():
                messages.error(request, "Voter ID already registered")
                return render(request, "voting/register.html", {
                    "form": form,
                    "constituencies": Constituency.objects.all()
                })

            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered")
                return render(request, "voting/register.html", {
                    "form": form,
                    "constituencies": Constituency.objects.all()
                })

            user = form.save(commit=False)
            user.is_active = False
            user.save()

            try:
                constituency = Constituency.objects.get(id=constituency_id)
            except Constituency.DoesNotExist:
                user.delete()
                messages.error(request, "Invalid constituency selected")
                return render(request, "voting/register.html", {
                    "form": form,
                    "constituencies": Constituency.objects.all()
                })

            VoterProfile.objects.create(
                user=user,
                voter_id=voter_id,
                constituency=constituency
            )

            otp_code = generate_otp()
            
            OTP.objects.update_or_create(
                user=user,
                defaults={
                    "code": otp_code,
                    "created_at": timezone.now()
                }
            )

            success, message = send_otp_email(user.email, otp_code, "registration")
            
            if success:
                request.session["otp_user"] = user.username
                request.session["otp_purpose"] = "registration"
                
                messages.success(request, f"Registration successful! {message}")
                logger.info(f"User {user.username} registered successfully, OTP sent to {user.email}")
                return redirect("verify_otp")
            else:
                user.delete()
                messages.error(request, f"Registration failed: {message}")
                logger.error(f"Failed to send OTP to {user.email}: {message}")
                return render(request, "voting/register.html", {
                    "form": form,
                    "constituencies": Constituency.objects.all()
                })

        except Exception as e:
            logger.exception(f"Error during registration: {str(e)}")
            messages.error(request, "An error occurred during registration. Please try again.")
            return render(request, "voting/register.html", {
                "form": form,
                "constituencies": Constituency.objects.all()
            })

    else:
        form = VoterRegistrationForm()

    return render(request, "voting/register.html", {
        "form": form,
        "constituencies": Constituency.objects.all()
    })


# ---------------- VERIFY OTP ----------------
def verify_otp_view(request):
    """Verify OTP entered by user"""
    username = request.session.get("otp_user")
    
    if not username:
        messages.error(request, "No pending OTP verification found")
        return redirect("otp_login")

    try:
        user = User.objects.get(username=username)
        otp_obj = OTP.objects.get(user=user)
    except User.DoesNotExist:
        messages.error(request, "User not found")
        return redirect("otp_login")
    except OTP.DoesNotExist:
        messages.error(request, "OTP not found. Please request a new one.")
        return redirect("otp_login")

    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()

        if not entered_otp:
            messages.error(request, "Please enter the OTP")
            return render(request, "voting/verify_otp.html", {
                "email": user.email,
                "expiry_minutes": settings.OTP_EXPIRY_MINUTES
            })

        is_valid, message = verify_otp(
            otp_obj.code,
            entered_otp,
            otp_obj.created_at,
            settings.OTP_EXPIRY_MINUTES
        )

        if is_valid:
            user.is_active = True
            user.save()
            
            otp_obj.delete()
            
            if "otp_user" in request.session:
                del request.session["otp_user"]
            if "otp_purpose" in request.session:
                del request.session["otp_purpose"]
            
            login(request, user)
            
            messages.success(request, "Email verified successfully! You can now vote.")
            logger.info(f"User {user.username} verified OTP successfully")
            return redirect("vote")
        else:
            messages.error(request, message)
            logger.warning(f"Failed OTP verification for user {user.username}")
            return render(request, "voting/verify_otp.html", {
                "email": user.email,
                "expiry_minutes": settings.OTP_EXPIRY_MINUTES
            })

    return render(request, "voting/verify_otp.html", {
        "email": user.email,
        "expiry_minutes": settings.OTP_EXPIRY_MINUTES
    })


# ---------------- RESEND OTP ----------------
def resend_otp(request):
    """Resend OTP to user's email"""
    if request.method != "POST":
        return redirect("verify_otp")
    
    username = request.session.get("otp_user")
    
    if not username:
        messages.error(request, "No pending OTP verification found")
        return redirect("otp_login")

    try:
        user = User.objects.get(username=username)
        new_otp = generate_otp()
        
        OTP.objects.update_or_create(
            user=user,
            defaults={
                "code": new_otp,
                "created_at": timezone.now()
            }
        )
        
        success, message = send_otp_email(user.email, new_otp, "verification")
        
        if success:
            messages.success(request, "New OTP sent successfully! Please check your email.")
            logger.info(f"OTP resent to {user.email}")
        else:
            messages.error(request, f"Failed to resend OTP: {message}")
            logger.error(f"Failed to resend OTP to {user.email}")
    
    except User.DoesNotExist:
        messages.error(request, "User not found")
        return redirect("otp_login")
    except Exception as e:
        logger.exception(f"Error resending OTP: {str(e)}")
        messages.error(request, "Error resending OTP. Please try again.")
    
    return redirect("verify_otp")


# ---------------- OTP LOGIN ----------------
def otp_login(request):
    """Login with username, password, and voter ID"""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        voter_id = request.POST.get("voter_id", "").strip()

        if not username or not password or not voter_id:
            messages.error(request, "All fields are required")
            return render(request, "voting/otp_login.html")

        user = authenticate(request, username=username, password=password)
        
        if not user:
            messages.error(request, "Invalid username or password")
            return render(request, "voting/otp_login.html")

        try:
            profile = VoterProfile.objects.get(user=user)
        except VoterProfile.DoesNotExist:
            messages.error(request, "Voter profile not found")
            return render(request, "voting/otp_login.html")

        if profile.voter_id != voter_id:
            messages.error(request, "Invalid Voter ID")
            return render(request, "voting/otp_login.html")

        otp_code = generate_otp()
        
        OTP.objects.update_or_create(
            user=user,
            defaults={
                "code": otp_code,
                "created_at": timezone.now()
            }
        )

        success, message = send_otp_email(user.email, otp_code, "login")
        
        if success:
            request.session["otp_user"] = user.username
            request.session["otp_purpose"] = "login"
            messages.success(request, message)
            logger.info(f"OTP sent to {user.email} for login")
            return redirect("verify_otp")
        else:
            messages.error(request, f"Failed to send OTP: {message}")
            logger.error(f"Failed to send OTP to {user.email}")
            return render(request, "voting/otp_login.html")

    return render(request, "voting/otp_login.html")


# ---------------- VOTE ----------------
@login_required(login_url='otp_login')
def vote(request):
    """Voting page - allows user to cast vote"""
    try:
        profile = VoterProfile.objects.get(user=request.user)
    except VoterProfile.DoesNotExist:
        messages.error(request, "Voter profile not found. Please contact administrator.")
        return redirect("home")

    # Check if already voted
    if Vote.objects.filter(user=request.user).exists():
        return render(request, "voting/already_voted.html")

    candidates = Candidate.objects.filter(constituency=profile.constituency)

    if request.method == "POST":
        candidate_id = request.POST.get("candidate")
        
        if not candidate_id:
            messages.error(request, "Please select a candidate")
            return render(request, "voting/vote.html", {
                "candidates": candidates,
                "constituency": profile.constituency
            })

        try:
            candidate = Candidate.objects.get(id=candidate_id)
            
            if candidate.constituency != profile.constituency:
                messages.error(request, "Invalid candidate selection")
                return render(request, "voting/vote.html", {
                    "candidates": candidates,
                    "constituency": profile.constituency
                })

            # Double check - prevent duplicate voting
            if Vote.objects.filter(user=request.user).exists():
                return render(request, "voting/already_voted.html")

            # Create the vote
            Vote.objects.create(
                user=request.user,
                candidate=candidate
            )
            
            logger.info(f"User {request.user.username} voted for {candidate.name}")
            
            # Pass data to success page
            return render(request, "voting/vote_success.html", {
                "constituency": profile.constituency.name,
                "candidate": candidate,
                "user": request.user
            })

        except Candidate.DoesNotExist:
            messages.error(request, "Invalid candidate selected")
            return render(request, "voting/vote.html", {
                "candidates": candidates,
                "constituency": profile.constituency
            })
        except Exception as e:
            logger.exception(f"Error during voting: {str(e)}")
            messages.error(request, "An error occurred. Please try again.")
            return render(request, "voting/vote.html", {
                "candidates": candidates,
                "constituency": profile.constituency
            })

    return render(request, "voting/vote.html", {
        "candidates": candidates,
        "constituency": profile.constituency
    })


# ---------------- RESULTS ----------------
def result(request):
    """
    Display voting results - PUBLIC ACCESS (no login required)
    Shows all candidates with vote counts
    """
    try:
        # Get all constituencies
        all_constituencies = Constituency.objects.all()
        
        # Calculate overall statistics
        total_votes_overall = Vote.objects.count()
        total_voters = User.objects.filter(voterprofile__isnull=False).count()
        voter_turnout = round((total_votes_overall / total_voters * 100), 2) if total_voters > 0 else 0
        
        # Initialize variables for user constituency (if logged in)
        user_constituency = None
        my_constituency_results = []
        my_total_votes = 0
        has_voted = False
        
        # If user is logged in, get their constituency info
        if request.user.is_authenticated:
            try:
                user_profile = VoterProfile.objects.get(user=request.user)
                user_constituency = user_profile.constituency
                has_voted = Vote.objects.filter(user=request.user).exists()
                
                # Get results for user's constituency
                my_constituency_results = Vote.objects.filter(
                    candidate__constituency=user_constituency
                ).values(
                    "candidate__name",
                    "candidate__party"
                ).annotate(
                    total=Count("candidate")
                ).order_by("-total")
                
                my_total_votes = Vote.objects.filter(
                    candidate__constituency=user_constituency
                ).count()
            except VoterProfile.DoesNotExist:
                pass  # User doesn't have a voter profile
        
        # Get all constituency results
        constituency_stats = []
        for const in all_constituencies:
            # Get vote count for this constituency
            const_votes = Vote.objects.filter(
                candidate__constituency=const
            ).count()
            
            # Get ALL candidates and their votes in this constituency
            const_results = Vote.objects.filter(
                candidate__constituency=const
            ).values(
                "candidate__name",
                "candidate__party"
            ).annotate(
                total=Count("candidate")
            ).order_by("-total")
            
            # Get winner (candidate with most votes)
            winner = const_results.first() if const_results else None
            
            constituency_stats.append({
                'constituency': const,
                'total_votes': const_votes,
                'results': list(const_results),
                'winner': winner
            })
        
        context = {
            'total_votes_overall': total_votes_overall,
            'voter_turnout': voter_turnout,
            'constituency_stats': constituency_stats,
            'user_constituency': user_constituency,
            'my_constituency_results': my_constituency_results,
            'my_total_votes': my_total_votes,
            'has_voted': has_voted,
        }
        
        return render(request, "voting/result.html", context)
        
    except Exception as e:
        logger.exception(f"Error displaying results: {str(e)}")
        messages.error(request, "Error loading results")
        return redirect("home")


# ---------------- LOGOUT ----------------
def logout_view(request):
    """Logout user"""
    logout(request)
    messages.success(request, "You have been logged out successfully")
    return redirect("home")


# ---------------- ALREADY VOTED ----------------
@login_required(login_url='otp_login')
def already_voted(request):
    """Page shown to users who have already voted"""
    return render(request, "voting/already_voted.html")