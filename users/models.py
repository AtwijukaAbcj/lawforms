from django.db import models
from django.contrib.auth.models import User


class Module(models.Model):
    """Represents a module/feature in the application"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)  # e.g., 'financial_statement', 'comparison_nfp'
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='📁')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Granular permissions for modules"""
    PERMISSION_TYPES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('print', 'Print'),
        ('export', 'Export'),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='permissions')
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPES)
    
    class Meta:
        unique_together = ['module', 'permission_type']
        ordering = ['module', 'permission_type']

    def __str__(self):
        return f"{self.module.name} - {self.get_permission_type_display()}"


class Role(models.Model):
    """User roles with associated permissions"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_permissions_by_module(self):
        """Group permissions by module for display"""
        permissions_dict = {}
        for perm in self.permissions.select_related('module').all():
            module_name = perm.module.name
            if module_name not in permissions_dict:
                permissions_dict[module_name] = []
            permissions_dict[module_name].append(perm.get_permission_type_display())
        return permissions_dict


class UserProfile(models.Model):
    """Extended user profile with role assignment"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_password_change = models.DateTimeField(null=True, blank=True)
    password_reset_required = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def has_module_permission(self, module_code, permission_type):
        """Check if user has specific permission for a module"""
        if self.user.is_superuser:
            return True
        if not self.role:
            return False
        return self.role.permissions.filter(
            module__code=module_code,
            permission_type=permission_type
        ).exists()

    def get_accessible_modules(self):
        """Get list of modules user can access"""
        if self.user.is_superuser:
            return Module.objects.filter(is_active=True)
        if not self.role:
            return Module.objects.none()
        return Module.objects.filter(
            is_active=True,
            permissions__roles=self.role
        ).distinct()


class AuditLog(models.Model):
    """Track user actions for auditing"""
    ACTION_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Export'),
        ('password_change', 'Password Change'),
        ('password_reset', 'Password Reset'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    module = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
