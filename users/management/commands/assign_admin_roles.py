from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Role, Permission, UserProfile


class Command(BaseCommand):
    help = 'Assign Administrator role to all superusers and staff'

    def handle(self, *args, **options):
        # Get Administrator role
        try:
            admin_role = Role.objects.get(name='Administrator')
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR('Administrator role not found. Run setup_modules first.'))
            return

        # Update Administrator role to have all permissions
        admin_role.permissions.set(Permission.objects.all())
        self.stdout.write(f'Administrator role now has {admin_role.permissions.count()} permissions')

        # Ensure all users have a profile
        for user in User.objects.all():
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                self.stdout.write(f'Created profile for {user.username}')

        # Assign Administrator role to superusers and staff
        admin_users = User.objects.filter(is_superuser=True) | User.objects.filter(is_staff=True)
        for user in admin_users.distinct():
            profile = user.profile
            profile.role = admin_role
            profile.save()
            self.stdout.write(self.style.SUCCESS(f'Assigned Administrator role to {user.username}'))

        self.stdout.write(self.style.SUCCESS('Done!'))
