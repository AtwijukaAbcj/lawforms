from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import Role, Module, Permission, UserProfile, AuditLog
from .forms import UserForm, RoleForm, ModuleForm, AdminPasswordResetForm, UserPasswordChangeForm


def is_admin(user):
    """Check if user is admin or superuser"""
    return user.is_superuser or user.is_staff


def log_action(request, action, module='', object_id='', object_repr='', details=''):
    """Helper to log user actions"""
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        module=module,
        object_id=str(object_id),
        object_repr=object_repr[:255] if object_repr else '',
        details=details,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============== Dashboard ==============

@login_required
@user_passes_test(is_admin)
def user_management_dashboard(request):
    """User management dashboard with rich statistics"""
    from datetime import timedelta
    
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = total_users - active_users
    
    # Users created in the last 30 days
    new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    # Users needing password reset
    users_need_reset = UserProfile.objects.filter(password_reset_required=True).count()
    
    # Recent logins (last 7 days)
    recent_logins = AuditLog.objects.filter(
        action='login',
        timestamp__gte=seven_days_ago
    ).values('user').distinct().count()
    
    # Activity breakdown by type for chart
    activity_breakdown = {}
    for action_code, action_name in AuditLog.ACTION_TYPES:
        count = AuditLog.objects.filter(
            action=action_code,
            timestamp__gte=thirty_days_ago
        ).count()
        if count > 0:
            activity_breakdown[action_name] = count
    
    # Top active users (by audit log entries in last 30 days)
    from django.db.models import Count
    top_users = User.objects.filter(
        audit_logs__timestamp__gte=thirty_days_ago
    ).annotate(
        action_count=Count('audit_logs')
    ).order_by('-action_count')[:5]
    
    # Role distribution
    role_distribution = Role.objects.filter(is_active=True).annotate(
        user_count=Count('users')
    ).values('name', 'user_count').order_by('-user_count')
    
    context = {
        # Core stats
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'total_roles': Role.objects.filter(is_active=True).count(),
        'total_modules': Module.objects.filter(is_active=True).count(),
        
        # Extended stats
        'new_users_30d': new_users_30d,
        'users_need_reset': users_need_reset,
        'recent_logins': recent_logins,
        
        # For charts/visualizations
        'activity_breakdown': activity_breakdown,
        'top_users': top_users,
        'role_distribution': list(role_distribution),
        
        # Recent activity
        'recent_logs': AuditLog.objects.select_related('user')[:8],
        
        # All roles for quick reference
        'roles': Role.objects.filter(is_active=True)[:5],
    }
    return render(request, 'users/dashboard.html', context)


# ============== User Management ==============

@login_required
@user_passes_test(is_admin)
def user_list(request):
    """List all users with search and filter"""
    users = User.objects.select_related('profile', 'profile__role').all()
    
    # Search
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(profile__role_id=role_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'roles': Role.objects.filter(is_active=True),
        'search': search,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    return render(request, 'users/user_list.html', context)


@login_required
@user_passes_test(is_admin)
def user_create(request):
    """Create a new user"""
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(request, 'create', 'users', user.id, user.username, f'Created user: {user.username}')
            messages.success(request, f'User "{user.username}" created successfully.')
            return redirect('users:user_list')
    else:
        form = UserForm()
    
    return render(request, 'users/user_form.html', {
        'form': form,
        'title': 'Create User',
        'action': 'Create'
    })


@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    """Edit an existing user"""
    user = get_object_or_404(User, pk=pk)
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_action(request, 'update', 'users', user.id, user.username, f'Updated user: {user.username}')
            messages.success(request, f'User "{user.username}" updated successfully.')
            return redirect('users:user_list')
    else:
        form = UserForm(instance=user, initial={
            'role': profile.role,
            'phone': profile.phone,
            'department': profile.department,
        })
    
    return render(request, 'users/user_form.html', {
        'form': form,
        'title': f'Edit User: {user.username}',
        'action': 'Update',
        'user_obj': user
    })


@login_required
@user_passes_test(is_admin)
def user_delete(request, pk):
    """Delete a user"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        username = user.username
        log_action(request, 'delete', 'users', user.id, username, f'Deleted user: {username}')
        user.delete()
        messages.success(request, f'User "{username}" deleted successfully.')
        return redirect('users:user_list')
    
    return render(request, 'users/user_confirm_delete.html', {'user_obj': user})


@login_required
@user_passes_test(is_admin)
def user_reset_password(request, pk):
    """Admin reset user password"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = AdminPasswordResetForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            
            # Update profile for password reset requirement
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.password_reset_required = form.cleaned_data.get('require_change', True)
            profile.last_password_change = timezone.now()
            profile.save()
            
            log_action(request, 'password_reset', 'users', user.id, user.username, f'Password reset for: {user.username}')
            messages.success(request, f'Password reset for "{user.username}" successfully.')
            return redirect('users:user_list')
    else:
        form = AdminPasswordResetForm()
    
    return render(request, 'users/password_reset.html', {
        'form': form,
        'user_obj': user
    })


# ============== Role Management ==============

@login_required
@user_passes_test(is_admin)
def role_list(request):
    """List all roles"""
    roles = Role.objects.prefetch_related('permissions', 'users').all()
    return render(request, 'users/role_list.html', {'roles': roles})


@login_required
@user_passes_test(is_admin)
def role_create(request):
    """Create a new role"""
    modules = Module.objects.filter(is_active=True).prefetch_related('permissions')
    
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            
            # Save permissions
            permission_ids = request.POST.getlist('permissions')
            role.permissions.set(permission_ids)
            
            log_action(request, 'create', 'roles', role.id, role.name, f'Created role: {role.name}')
            messages.success(request, f'Role "{role.name}" created successfully.')
            return redirect('users:role_list')
    else:
        form = RoleForm()
    
    return render(request, 'users/role_form.html', {
        'form': form,
        'modules': modules,
        'title': 'Create Role',
        'action': 'Create'
    })


@login_required
@user_passes_test(is_admin)
def role_edit(request, pk):
    """Edit an existing role"""
    role = get_object_or_404(Role, pk=pk)
    modules = Module.objects.filter(is_active=True).prefetch_related('permissions')
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            role = form.save()
            
            # Save permissions
            permission_ids = request.POST.getlist('permissions')
            role.permissions.set(permission_ids)
            
            log_action(request, 'update', 'roles', role.id, role.name, f'Updated role: {role.name}')
            messages.success(request, f'Role "{role.name}" updated successfully.')
            return redirect('users:role_list')
    else:
        form = RoleForm(instance=role)
    
    return render(request, 'users/role_form.html', {
        'form': form,
        'modules': modules,
        'role': role,
        'title': f'Edit Role: {role.name}',
        'action': 'Update'
    })


@login_required
@user_passes_test(is_admin)
def role_delete(request, pk):
    """Delete a role"""
    role = get_object_or_404(Role, pk=pk)
    
    if request.method == 'POST':
        name = role.name
        log_action(request, 'delete', 'roles', role.id, name, f'Deleted role: {name}')
        role.delete()
        messages.success(request, f'Role "{name}" deleted successfully.')
        return redirect('users:role_list')
    
    return render(request, 'users/role_confirm_delete.html', {'role': role})


# ============== Module Management ==============

@login_required
@user_passes_test(is_admin)
def module_list(request):
    """List all modules"""
    modules = Module.objects.prefetch_related('permissions').all()
    return render(request, 'users/module_list.html', {'modules': modules})


@login_required
@user_passes_test(is_admin)
def module_create(request):
    """Create a new module"""
    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save()
            
            # Create default permissions for the module
            permission_types = ['view', 'create', 'edit', 'delete', 'print', 'export']
            for perm_type in permission_types:
                Permission.objects.create(module=module, permission_type=perm_type)
            
            log_action(request, 'create', 'modules', module.id, module.name, f'Created module: {module.name}')
            messages.success(request, f'Module "{module.name}" created successfully with default permissions.')
            return redirect('users:module_list')
    else:
        form = ModuleForm()
    
    return render(request, 'users/module_form.html', {
        'form': form,
        'title': 'Create Module',
        'action': 'Create'
    })


@login_required
@user_passes_test(is_admin)
def module_edit(request, pk):
    """Edit an existing module"""
    module = get_object_or_404(Module, pk=pk)
    
    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            log_action(request, 'update', 'modules', module.id, module.name, f'Updated module: {module.name}')
            messages.success(request, f'Module "{module.name}" updated successfully.')
            return redirect('users:module_list')
    else:
        form = ModuleForm(instance=module)
    
    return render(request, 'users/module_form.html', {
        'form': form,
        'module': module,
        'title': f'Edit Module: {module.name}',
        'action': 'Update'
    })


@login_required
@user_passes_test(is_admin)
def module_delete(request, pk):
    """Delete a module"""
    module = get_object_or_404(Module, pk=pk)
    
    if request.method == 'POST':
        name = module.name
        log_action(request, 'delete', 'modules', module.id, name, f'Deleted module: {name}')
        module.delete()
        messages.success(request, f'Module "{name}" deleted successfully.')
        return redirect('users:module_list')
    
    return render(request, 'users/module_confirm_delete.html', {'module': module})


# ============== Audit Log ==============

@login_required
@user_passes_test(is_admin)
def audit_log_list(request):
    """View audit logs"""
    logs = AuditLog.objects.select_related('user').all()
    
    # Filter by action
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    # Filter by user
    user_filter = request.GET.get('user', '')
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page = request.GET.get('page', 1)
    logs = paginator.get_page(page)
    
    context = {
        'logs': logs,
        'users': User.objects.all(),
        'action_choices': AuditLog.ACTION_TYPES,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'users/audit_log_list.html', context)


# ============== User Profile & Password Change ==============

@login_required
def my_profile(request):
    """View own profile"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'users/my_profile.html', {'profile': profile})


@login_required
def change_password(request):
    """User change own password"""
    if request.method == 'POST':
        form = UserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            
            # Update profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.last_password_change = timezone.now()
            profile.password_reset_required = False
            profile.save()
            
            log_action(request, 'password_change', 'users', user.id, user.username, 'User changed their password')
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:my_profile')
    else:
        form = UserPasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})
