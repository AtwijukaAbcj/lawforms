from django.core.management.base import BaseCommand
from forms.models import Form131FinancialStatement
from django.utils import timezone

class Command(BaseCommand):
    help = 'Populate Form131FinancialStatement with dummy data.'

    def handle(self, *args, **options):
        dummy = Form131FinancialStatement.objects.create(
            court_file_number='CV-2026-123456',
            applicant_name='Jane Doe',
            respondent_name='John Smith',
            draft={
                'page1': {
                    'date': str(timezone.now().date()),
                    'applicant_address': '123 Main St, Toronto, ON',
                    'respondent_address': '456 Queen St, Toronto, ON',
                    'income': 75000,
                },
                'page2': {
                    'employment_status': 'Employed',
                    'employer': 'Acme Corp',
                    'salary': 75000,
                },
                'page3': {
                    'assets': [
                        {'type': 'Car', 'value': 15000},
                        {'type': 'Bank Account', 'value': 5000},
                    ],
                },
                'page4': {
                    'debts': [
                        {'type': 'Credit Card', 'amount': 2000},
                    ],
                },
                'page5': {
                    'signature': 'Jane Doe',
                    'date_signed': str(timezone.now().date()),
                },
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Dummy Form131FinancialStatement created with id {dummy.id}'))
