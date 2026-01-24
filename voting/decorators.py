# voting/decorators.py
"""
Custom decorators for access control
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_required(function):
    """
    Decorator to check if user is admin/staff
    Only admins can access analytics pages
    Redirects to ADMIN LOGIN (not regular user login)
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        # Check if user is logged in
        if not request.user.is_authenticated:
            messages.error(request, "Please login as admin to access analytics.")
            # FIXED: Redirect to admin login instead of otp_login
            return redirect(f'/admin/login/?next={request.path}')
        
        # Check if user is admin or staff
        if request.user.is_staff or request.user.is_superuser:
            return function(request, *args, **kwargs)
        else:
            messages.error(request, "Access Denied! Only election officials can view analytics.")
            return redirect('home')
    
    return wrap


def voter_required(function):
    """
    Decorator to check if user is a voter (not admin)
    Only voters can vote
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please login to vote.")
            return redirect('otp_login')
        
        # Voters should NOT be staff/admin
        if not request.user.is_staff and not request.user.is_superuser:
            return function(request, *args, **kwargs)
        else:
            messages.warning(request, "Admins cannot vote. Please use a voter account.")
            return redirect('home')
    
    return wrap