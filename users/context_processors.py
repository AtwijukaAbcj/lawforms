"""
Context processor to provide user permissions in templates
"""
from users.models import Module, UserProfile


def user_permissions(request):
    """
    Add user permissions to template context.
    This allows templates to check module access with:
    {% if user_modules.dashboard %} ... {% endif %}
    """
    context = {
        'user_modules': {},
        'user_permissions': {},
    }
    
    if not request.user.is_authenticated:
        return context
    
    # Superusers have access to everything
    if request.user.is_superuser:
        modules = Module.objects.filter(is_active=True)
        context['user_modules'] = {m.code: True for m in modules}
        context['user_permissions'] = {
            m.code: {
                'view': True,
                'create': True,
                'edit': True,
                'delete': True,
                'print': True,
                'export': True,
            } for m in modules
        }
        return context
    
    # Get user profile
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Create a profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user)
    
    # Get accessible modules
    accessible_modules = profile.get_accessible_modules()
    context['user_modules'] = {m.code: True for m in accessible_modules}
    
    # Get granular permissions
    if profile.role:
        perms = profile.role.permissions.select_related('module').all()
        for perm in perms:
            if perm.module.code not in context['user_permissions']:
                context['user_permissions'][perm.module.code] = {}
            context['user_permissions'][perm.module.code][perm.permission_type] = True
    
    return context
