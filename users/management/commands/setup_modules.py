from django.core.management.base import BaseCommand
from users.models import Module, Permission, Role


class Command(BaseCommand):
    help = 'Setup default modules and roles for the Family Law Forms application'

    def handle(self, *args, **options):
        # Define default modules
        modules_data = [
            {
                'name': 'Dashboard',
                'code': 'dashboard',
                'description': 'Main dashboard with overview and statistics',
                'icon': '📊',
            },
            {
                'name': 'Financial Statement (Form 13)',
                'code': 'financial_statement',
                'description': 'Create and manage Financial Statements (Form 13)',
                'icon': '📄',
            },
            {
                'name': 'Net Family Property (13B)',
                'code': 'net_family_property_13b',
                'description': 'Create and manage Net Family Property Statements (Form 13B)',
                'icon': '📋',
            },
            {
                'name': 'Comparison of NFP',
                'code': 'comparison_nfp',
                'description': 'Create and manage Comparison of Net Family Property forms',
                'icon': '⚖️',
            },
            {
                'name': 'User Management',
                'code': 'user_management',
                'description': 'Manage users, roles, and permissions',
                'icon': '👥',
            },
        ]

        permission_types = ['view', 'create', 'edit', 'delete', 'print', 'export']

        # Create modules and permissions
        for module_data in modules_data:
            module, created = Module.objects.get_or_create(
                code=module_data['code'],
                defaults={
                    'name': module_data['name'],
                    'description': module_data['description'],
                    'icon': module_data['icon'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created module: {module.name}'))
                
                # Create permissions for the module
                for perm_type in permission_types:
                    Permission.objects.get_or_create(
                        module=module,
                        permission_type=perm_type
                    )
                self.stdout.write(f'  - Created {len(permission_types)} permissions')
            else:
                self.stdout.write(f'Module already exists: {module.name}')

        # Create default roles
        roles_data = [
            {
                'name': 'Administrator',
                'description': 'Full access to all modules and features',
                'permissions': 'all',  # Special case: grant all permissions
            },
            {
                'name': 'Staff',
                'description': 'Can view, create, and edit forms but cannot delete',
                'permissions': ['view', 'create', 'edit', 'print', 'export'],
            },
            {
                'name': 'Viewer',
                'description': 'Read-only access to view and print forms',
                'permissions': ['view', 'print'],
            },
        ]

        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created role: {role.name}'))
                
                # Assign permissions
                if role_data['permissions'] == 'all':
                    role.permissions.set(Permission.objects.all())
                else:
                    permissions = Permission.objects.filter(permission_type__in=role_data['permissions'])
                    role.permissions.set(permissions)
                
                self.stdout.write(f'  - Assigned {role.permissions.count()} permissions')
            else:
                self.stdout.write(f'Role already exists: {role.name}')

        self.stdout.write(self.style.SUCCESS('\nSetup complete!'))
