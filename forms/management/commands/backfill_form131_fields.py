from django.core.management.base import BaseCommand
from forms.models import Form131FinancialStatement

class Command(BaseCommand):
    help = 'Backfill Form131FinancialStatement fields from page 1 data.'

    def handle(self, *args, **options):
        count = 0
        for statement in Form131FinancialStatement.objects.all():
            page1 = statement.get_page_data(1) or {}
            changed = False
            if page1:
                cfnum = page1.get('court_file_number', '')
                appname = page1.get('applicant_name', '')
                respname = page1.get('respondent_name', '')
                if cfnum and statement.court_file_number != cfnum:
                    statement.court_file_number = cfnum
                    changed = True
                if appname and statement.applicant_name != appname:
                    statement.applicant_name = appname
                    changed = True
                if respname and getattr(statement, 'respondent_name', None) != respname:
                    statement.respondent_name = respname
                    changed = True
                if changed:
                    statement.save()
                    count += 1
        self.stdout.write(self.style.SUCCESS(f'Backfilled {count} Form131FinancialStatement records.'))
