"""
Management command to initialize default billing settings.
Run with: python manage.py init_billing_settings
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from forms.models import BillingSetting, PrintEvent


class Command(BaseCommand):
    help = 'Initialize default billing settings for form types'

    def add_arguments(self, parser):
        parser.add_argument(
            '--price',
            type=float,
            default=1.00,
            help='Default price per print (default: 1.00)',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all prices to the specified default',
        )

    def handle(self, *args, **options):
        default_price = Decimal(str(options['price']))
        reset = options['reset']

        form_types = PrintEvent.FORM_TYPE_CHOICES
        
        created_count = 0
        updated_count = 0

        for form_type, display_name in form_types:
            if reset:
                setting, created = BillingSetting.objects.update_or_create(
                    form_type=form_type,
                    defaults={
                        'form_display_name': display_name,
                        'price_per_print': default_price,
                        'is_active': True,
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'Created: {display_name} @ ${default_price}')
                else:
                    updated_count += 1
                    self.stdout.write(f'Updated: {display_name} @ ${default_price}')
            else:
                setting, created = BillingSetting.objects.get_or_create(
                    form_type=form_type,
                    defaults={
                        'form_display_name': display_name,
                        'price_per_print': default_price,
                        'is_active': True,
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'Created: {display_name} @ ${default_price}')
                else:
                    self.stdout.write(f'Exists: {display_name} @ ${setting.price_per_print}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {created_count}, Updated: {updated_count}'
        ))
