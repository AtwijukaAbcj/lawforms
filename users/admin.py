from django.contrib import admin
from .models import Module, Permission, Role, UserProfile, AuditLog


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'icon', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['module', 'permission_type']
    list_filter = ['module', 'permission_type']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    filter_horizontal = ['permissions']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['user__username', 'user__email', 'department']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'module', 'timestamp', 'ip_address']
    list_filter = ['action', 'module', 'timestamp']
    search_fields = ['user__username', 'object_repr', 'details']
    readonly_fields = ['user', 'action', 'module', 'object_id', 'object_repr', 'details', 'ip_address', 'user_agent', 'timestamp']
