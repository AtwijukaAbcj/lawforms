from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Dashboard
    path('', views.user_management_dashboard, name='dashboard'),
    
    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/reset-password/', views.user_reset_password, name='user_reset_password'),
    
    # Role Management
    path('roles/', views.role_list, name='role_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:pk>/edit/', views.role_edit, name='role_edit'),
    path('roles/<int:pk>/delete/', views.role_delete, name='role_delete'),
    
    # Module Management
    path('modules/', views.module_list, name='module_list'),
    path('modules/create/', views.module_create, name='module_create'),
    path('modules/<int:pk>/edit/', views.module_edit, name='module_edit'),
    path('modules/<int:pk>/delete/', views.module_delete, name='module_delete'),
    
    # Audit Log
    path('audit-logs/', views.audit_log_list, name='audit_log_list'),
    
    # User Profile
    path('profile/', views.my_profile, name='my_profile'),
    path('change-password/', views.change_password, name='change_password'),
]
