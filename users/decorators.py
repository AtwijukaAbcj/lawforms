"""
Permission decorators for view-level access control
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden

from users.models import UserProfile


def module_permission_required(module_code, permission_type='view'):
    """
    Decorator to check if user has permission for a specific module.
    
    Usage:
        @module_permission_required('financial_statement', 'edit')
        def edit_financial_statement(request, pk):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Not authenticated
            if not user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')
            
            # Superusers always have access
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user has profile
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)
            
            # Check permission
            if profile.has_module_permission(module_code, permission_type):
                return view_func(request, *args, **kwargs)
            
            # No permission
            messages.error(request, f"You don't have permission to access this feature.")
            return redirect('dashboard')
        
        return _wrapped_view
    return decorator


def any_module_permission(module_code):
    """
    Decorator to check if user has ANY permission for a module.
    Useful for general module access checks.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            if not user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')
            
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)
            
            # Check if module is in accessible modules
            accessible = profile.get_accessible_modules()
            if accessible.filter(code=module_code).exists():
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f"You don't have permission to access this module.")
            return redirect('dashboard')
        
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """
    Decorator to restrict access to admin/staff only.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        
        if not user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        
        if user.is_superuser or user.is_staff:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "Admin access required.")
        return redirect('dashboard')
    
    return _wrapped_view
