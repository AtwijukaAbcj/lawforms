from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import CaseFile, EstateAccounting, FinancialStatement, NetFamilyPropertyStatement, NetFamilyProperty13B, ComparisonNetFamilyProperty, PrintEvent
from users.models import Module, Role


class CaseFileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('tester', 't@test.com', 'pass')
        self.other = User.objects.create_user('other', 'o@test.com', 'pass')
        self.case = CaseFile.objects.create(owner=self.user, court_file_number='CF-1', applicant_name='A', respondent_name='B')

    def test_case_owner_access(self):
        resp = self.client.get(f'/forms/cases/{self.case.pk}/')
        self.assertEqual(resp.status_code, 302)

        self.client.login(username='other', password='pass')
        resp = self.client.get(f'/forms/cases/{self.case.pk}/')
        self.assertEqual(resp.status_code, 404)

        self.client.login(username='tester', password='pass')
        resp = self.client.get(f'/forms/cases/{self.case.pk}/')
        self.assertEqual(resp.status_code, 200)

    def test_case_create_and_links(self):
        self.client.login(username='tester', password='pass')
        resp = self.client.post('/forms/cases/new/', {'court_file_number': 'X', 'applicant_name': 'A', 'respondent_name': 'B'})
        self.assertEqual(resp.status_code, 302)

        new_case = CaseFile.objects.get(court_file_number='X')
        resp = self.client.get(f'/forms/cases/{new_case.pk}/')
        self.assertContains(resp, '?case_id=')

    def test_push_case_updates_forms(self):
        self.client.login(username='tester', password='pass')
        fs = FinancialStatement.objects.create(case_file=self.case, court_file_number='OLD', applicant_name='Old', respondent_name='Old')
        resp = self.client.post(f'/forms/cases/{self.case.pk}/push/')
        self.assertEqual(resp.status_code, 302)

        fs.refresh_from_db()
        self.assertEqual(fs.court_file_number, self.case.court_file_number)
        self.assertEqual(fs.applicant_name, self.case.applicant_name)
        self.assertEqual(fs.respondent_name, self.case.respondent_name)

    def test_financial_statement_page1_new_prefills_case(self):
        self.client.login(username='tester', password='pass')
        resp = self.client.get(f'/forms/financial-statement/new/?case_id={self.case.pk}')
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        self.assertEqual(form.initial['court_file_number'], self.case.court_file_number)
        self.assertEqual(form.initial['court_name'], self.case.court_name)
        self.assertEqual(form.initial['applicant_name'], self.case.applicant_name)
        self.assertEqual(form.initial['respondent_name'], self.case.respondent_name)

    def test_net_family_property_create_prefills_case(self):
        self.client.login(username='tester', password='pass')
        resp = self.client.get(f'/forms/net-family-property/?case_id={self.case.pk}')
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        self.assertEqual(form.initial['court_file_number'], self.case.court_file_number)
        self.assertEqual(form.initial['applicant_name'], self.case.applicant_name)
        self.assertEqual(form.initial['respondent_name'], self.case.respondent_name)

    def test_net_family_property_13b_page1_prefills_case(self):
        self.client.login(username='tester', password='pass')
        resp = self.client.get(f'/forms/net-family-property-13b/?case_id={self.case.pk}')
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        self.assertEqual(form.initial['court_file_number'], self.case.court_file_number)
        self.assertEqual(form.initial['court_name'], self.case.court_name)
        self.assertEqual(form.initial['court_address'], self.case.court_office_address)
        self.assertEqual(form.initial['applicant_name'], self.case.applicant_name)
        self.assertEqual(form.initial['respondent_name'], self.case.respondent_name)

    def test_comparison_nfp_create_copies_case_fields(self):
        self.client.login(username='tester', password='pass')
        resp = self.client.post(f'/forms/comparison-nfp/new/?case_id={self.case.pk}')
        self.assertEqual(resp.status_code, 302)
        comparison = ComparisonNetFamilyProperty.objects.filter(case_file=self.case).first()
        self.assertIsNotNone(comparison)
        self.assertEqual(comparison.court_file_number, self.case.court_file_number)
        self.assertEqual(comparison.court_name, self.case.court_name)
        self.assertEqual(comparison.applicant_name, self.case.applicant_name)
        self.assertEqual(comparison.respondent_name, self.case.respondent_name)


    def test_financial_statement_page6_renders_saved_debts(self):
        self.client.login(username='tester', password='pass')
        statement = FinancialStatement.objects.create(
            case_file=self.case,
            court_file_number='TEST-1',
            applicant_name='A',
            respondent_name='B',
            total_assets='1000.00',
            total_debts='500.00',
            total_debts_outstanding='450.00',
            net_worth='500.00',
            debts={
                'other_debt_creditor_1': 'Creditor 1',
                'other_debt_amount_1': '123.45',
                'other_debt_monthly_1': '12.34',
                'other_debt_payment_1': 'yes',
            }
        )

        resp = self.client.get(f'/forms/financial-statement/page6/{statement.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="other_debt_creditor_1"')
        self.assertContains(resp, 'value="Creditor 1"')
        self.assertContains(resp, 'value="123.45"')
        self.assertContains(resp, 'value="12.34"')
        self.assertContains(resp, 'name="subtract_total_debts"')
        self.assertContains(resp, 'value="500.000"')

    def test_financial_statement_page6_handles_list_formatted_debts(self):
        self.client.login(username='tester', password='pass')
        statement = FinancialStatement.objects.create(
            case_file=self.case,
            court_file_number='TEST-2',
            applicant_name='A',
            respondent_name='B',
            debts=[
                {'type': 'Mortgage', 'creditor': 'RBC Mortgage', 'full_amount': '450000.00', 'monthly_payment': '2100.00', 'payments_being_made': True},
                {'type': 'Visa', 'creditor': 'Visa Card', 'full_amount': '3200.00', 'monthly_payment': '120.00', 'payments_being_made': True},
            ]
        )

        resp = self.client.get(f'/forms/financial-statement/page6/{statement.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'value="RBC Mortgage"')
        self.assertContains(resp, 'value="Visa Card"')

    def test_financial_statement_view_handles_list_formatted_debts(self):
        self.client.login(username='tester', password='pass')
        statement = FinancialStatement.objects.create(
            case_file=self.case,
            court_file_number='TEST-6',
            applicant_name='A',
            respondent_name='B',
            debts=[
                {'type': 'Mortgage', 'creditor': 'RBC Mortgage', 'full_amount': '450000.00', 'monthly_payment': '2100.00', 'payments_being_made': True},
                {'type': 'Visa', 'creditor': 'Visa Card', 'full_amount': '3200.00', 'monthly_payment': '120.00', 'payments_being_made': True},
            ]
        )

        resp = self.client.get(f'/forms/financial-statement/view/{statement.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'RBC Mortgage')
        self.assertContains(resp, 'Visa Card')

    def test_financial_statement_page6_loads_page6_draft_fallback(self):
        self.client.login(username='tester', password='pass')
        statement = FinancialStatement.objects.create(
            case_file=self.case,
            court_file_number='TEST-4',
            applicant_name='A',
            respondent_name='B',
            draft={
                'page6': {
                    'other_debt_creditor_1': 'Fallback Creditor',
                    'other_debt_amount_1': '123.45',
                    'other_debt_monthly_1': '12.34',
                    'other_debt_payment_1': 'yes',
                    'total_assets': '2000.00',
                    'subtract_total_debts': '400.00',
                    'net_worth': '1600.00',
                    'total_debts_outstanding': '400.00',
                    'municipality': 'City',
                    'province': 'Province',
                    'signature': 'Sig',
                    'commissioner': 'Comm',
                }
            }
        )

        resp = self.client.get(f'/forms/financial-statement/page6/{statement.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'value="Fallback Creditor"')
        self.assertContains(resp, 'value="2000.00"')
        self.assertContains(resp, 'value="400.00"')
        self.assertContains(resp, 'value="1600.00"')

    def test_financial_statement_page6_edit_updates_same_statement(self):
        self.client.login(username='tester', password='pass')
        statement = FinancialStatement.objects.create(
            case_file=self.case,
            court_file_number='TEST-3',
            applicant_name='A',
            respondent_name='B',
            total_assets='1000.00',
            total_debts='500.00',
            total_debts_outstanding='500.00',
            net_worth='500.00',
            debts={
                'other_debt_creditor_1': 'Creditor 1',
                'other_debt_amount_1': '123.45',
                'other_debt_monthly_1': '12.34',
                'other_debt_payment_1': 'yes',
            }
        )
        original_count = FinancialStatement.objects.count()

        resp = self.client.post(
            f'/forms/financial-statement/page6/{statement.pk}/',
            {
                'total_assets': '2000.00',
                'subtract_total_debts': '400.00',
                'net_worth': '1600.00',
                'total_debts_outstanding': '400.00',
                'mortgage_creditor_1': '',
                'mortgage_amount_1': '',
                'mortgage_monthly_1': '',
                'mortgage_payment_1': '',
                'credit_card_creditor_1': '',
                'credit_card_amount_1': '',
                'credit_card_monthly_1': '',
                'credit_card_payment_1': '',
                'unpaid_support_creditor': '',
                'unpaid_support_amount': '',
                'unpaid_support_monthly': '',
                'unpaid_support_payment': '',
                'other_debt_creditor_1': 'Creditor 1',
                'other_debt_amount_1': '123.45',
                'other_debt_monthly_1': '12.34',
                'other_debt_payment_1': 'yes',
                'municipality': 'City',
                'province': 'Province',
                'date': '2026-01-01',
                'signature': 'Sig',
                'commissioner': 'Comm',
            }
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(FinancialStatement.objects.count(), original_count)

        statement.refresh_from_db()
        self.assertEqual(statement.total_assets, Decimal('2000.000'))
        self.assertEqual(statement.total_debts, Decimal('400.000'))
        self.assertEqual(statement.net_worth, Decimal('1600.000'))
        self.assertEqual(statement.sworn_municipality, 'City')
        self.assertEqual(statement.sworn_province_country, 'Province')

    def test_financial_statement_page1_edit_updates_same_statement(self):
        self.client.login(username='tester', password='pass')
        statement = FinancialStatement.objects.create(
            case_file=self.case,
            court_name='Old Court',
            court_file_number='EDIT-1',
            court_office_address='100 Old St',
            sworn_affidavit='Old Affidavit',
            applicant_name='A',
            applicant_address='1 Old Applicant Ave',
            applicant_phone='111-1111',
            applicant_fax='111-1112',
            applicant_email='a@test.com',
            applicant_lawyer_name='Old Lawyer',
            applicant_lawyer_address='3 Old Lawyer Rd',
            applicant_lawyer_phone='333-3333',
            applicant_lawyer_fax='333-3334',
            applicant_lawyer_email='lawyer@test.com',
            respondent_name='B',
            respondent_address='2 Old Respondent Ave',
            respondent_phone='222-2222',
            respondent_fax='222-2223',
            respondent_email='b@test.com',
            respondent_lawyer_name='Other Lawyer',
            respondent_lawyer_address='4 Old Lawyer Ln',
            respondent_lawyer_phone='444-4444',
            respondent_lawyer_fax='444-4445',
            respondent_lawyer_email='respondentlaw@test.com',
            my_name='Old My Name',
            my_location='Old My Location',
            is_employed=True,
            employer_name_address='Old Employer Address',
            is_self_employed=False,
            business_name_address='Old Business Address',
            is_unemployed=False,
            unemployed_since='2025-01-01',
        )
        original_count = FinancialStatement.objects.count()

        resp = self.client.post(
            f'/forms/financial-statement/page1/{statement.pk}/',
            {
                'court_name': 'Updated Court',
                'court_file_number': 'EDIT-UPDATED',
                'court_office_address': '200 Updated St',
                'sworn_affidavit': 'Updated Affidavit',
                'applicant_name': 'Applicant Updated',
                'applicant_address': '1 Updated Applicant Ave',
                'applicant_phone': '999-9999',
                'applicant_fax': '999-9998',
                'applicant_email': 'updated@test.com',
                'applicant_lawyer_name': 'Updated Lawyer',
                'applicant_lawyer_address': '3 Updated Lawyer Rd',
                'applicant_lawyer_phone': '777-7777',
                'applicant_lawyer_fax': '777-7776',
                'applicant_lawyer_email': 'updatedlawyer@test.com',
                'respondent_name': 'Respondent Updated',
                'respondent_address': '2 Updated Respondent Ave',
                'respondent_phone': '888-8888',
                'respondent_fax': '888-8887',
                'respondent_email': 'respondent@test.com',
                'respondent_lawyer_name': 'Updated Respondent Lawyer',
                'respondent_lawyer_address': '4 Updated Lawyer Ln',
                'respondent_lawyer_phone': '666-6666',
                'respondent_lawyer_fax': '666-6665',
                'respondent_lawyer_email': 'respondentlawupdated@test.com',
                'my_name': 'Updated My Name',
                'my_location': 'Updated My Location',
                'is_employed': 'on',
                'employer_name_address': 'Updated Employer Address',
                'is_self_employed': 'on',
                'business_name_address': 'Updated Business Address',
                'is_unemployed': '',
                'unemployed_since': '2025-12-31',
                'filed_by': 'applicant',
            }
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(FinancialStatement.objects.count(), original_count)

        statement.refresh_from_db()
        self.assertEqual(statement.court_name, 'Updated Court')
        self.assertEqual(statement.court_file_number, 'EDIT-UPDATED')
        self.assertEqual(statement.court_office_address, '200 Updated St')
        self.assertEqual(statement.sworn_affidavit, 'Updated Affidavit')
        self.assertEqual(statement.applicant_name, 'Applicant Updated')
        self.assertEqual(statement.applicant_address, '1 Updated Applicant Ave')
        self.assertEqual(statement.applicant_phone, '999-9999')
        self.assertEqual(statement.applicant_fax, '999-9998')
        self.assertEqual(statement.applicant_email, 'updated@test.com')
        self.assertEqual(statement.applicant_lawyer_name, 'Updated Lawyer')
        self.assertEqual(statement.applicant_lawyer_address, '3 Updated Lawyer Rd')
        self.assertEqual(statement.applicant_lawyer_phone, '777-7777')
        self.assertEqual(statement.applicant_lawyer_fax, '777-7776')
        self.assertEqual(statement.applicant_lawyer_email, 'updatedlawyer@test.com')
        self.assertEqual(statement.respondent_name, 'Respondent Updated')
        self.assertEqual(statement.respondent_address, '2 Updated Respondent Ave')
        self.assertEqual(statement.respondent_phone, '888-8888')
        self.assertEqual(statement.respondent_fax, '888-8887')
        self.assertEqual(statement.respondent_email, 'respondent@test.com')
        self.assertEqual(statement.respondent_lawyer_name, 'Updated Respondent Lawyer')
        self.assertEqual(statement.respondent_lawyer_address, '4 Updated Lawyer Ln')
        self.assertEqual(statement.respondent_lawyer_phone, '666-6666')
        self.assertEqual(statement.respondent_lawyer_fax, '666-6665')
        self.assertEqual(statement.respondent_lawyer_email, 'respondentlawupdated@test.com')
        self.assertEqual(statement.my_name, 'Updated My Name')
        self.assertEqual(statement.my_location, 'Updated My Location')
        self.assertTrue(statement.is_employed)
        self.assertTrue(statement.is_self_employed)
        self.assertFalse(statement.is_unemployed)
        self.assertEqual(statement.employer_name_address, 'Updated Employer Address')
        self.assertEqual(statement.business_name_address, 'Updated Business Address')
        self.assertEqual(str(statement.unemployed_since), '2025-12-31')

    def test_financial_statement_page7_view_exists(self):
        self.client.login(username='tester', password='pass')
        statement = FinancialStatement.objects.create(
            case_file=self.case,
            court_file_number='TEST-2',
            applicant_name='A',
            respondent_name='B',
        )

        resp = self.client.get(f'/forms/financial-statement/page7/{statement.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Schedule A')


class EstateAccountingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="estate-admin",
            email="estate@example.com",
            password="pass",
        )
        self.client.login(username="estate-admin", password="pass")

    def test_module_setup_grants_estate_permissions_to_default_roles(self):
        call_command("setup_modules", verbosity=0)
        call_command("setup_modules", verbosity=0)
        estate_module = Module.objects.get(code="estate_accounting")
        expected = {
            "Administrator": {"view", "create", "edit", "delete", "print", "export"},
            "Staff": {"view", "create", "edit", "print", "export"},
            "Viewer": {"view", "print"},
        }
        for role_name, permission_types in expected.items():
            role = Role.objects.get(name=role_name)
            actual = set(role.permissions.filter(module=estate_module).values_list("permission_type", flat=True))
            self.assertEqual(actual, permission_types)

    def test_create_form_and_dashboard_render(self):
        response = self.client.get("/forms/estate-accounting/new/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1. Estate Assets")
        self.assertContains(response, "5. Beneficiary Distributions")

        response = self.client.get("/forms/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estate Accounting")

    def test_estate_accounting_saves_schedules_and_reconciles(self):
        response = self.client.post("/forms/estate-accounting/new/", {
            "deceased_name": "Alex Estate",
            "date_of_death": "2025-01-15",
            "personal_representative": "Jamie Executor",
            "accounting_period_start": "2025-01-15",
            "accounting_period_end": "2025-12-31",
            "assets_count": "1",
            "assets_0_description": "House",
            "assets_0_proceeds": "100000.00",
            "assets_0_expenses": "500.00",
            "expenses_count": "1",
            "expenses_0_description": "Funeral",
            "expenses_0_amount": "2500.00",
            "receipts_count": "1",
            "receipts_0_description": "Bank interest",
            "receipts_0_amount": "100.00",
            "distributions_count": "1",
            "distributions_0_beneficiary": "Taylor",
            "distributions_0_entitlement": "50000.00",
            "distributions_0_amount_paid": "20000.00",
        })

        self.assertEqual(response.status_code, 302)
        accounting = EstateAccounting.objects.get()
        self.assertEqual(accounting.created_by, self.user)
        self.assertEqual(accounting.schedules["assets"][0]["proceeds"], "100000.00")
        self.assertRedirects(response, f"/forms/estate-accounting/{accounting.pk}/view/")

        response = self.client.get(f"/forms/estate-accounting/{accounting.pk}/view/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Balance remaining in Estate Account")
        self.assertContains(response, "$77600.00")
        self.assertContains(response, "$30000.00")
        self.assertContains(response, "$99500.00")

    def test_estate_accounting_rejects_invalid_amount_without_saving(self):
        response = self.client.post("/forms/estate-accounting/new/", {
            "deceased_name": "Alex Estate",
            "assets_count": "1",
            "assets_0_description": "House",
            "assets_0_proceeds": "not-money",
            "expenses_count": "0",
            "receipts_count": "0",
            "distributions_count": "0",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(EstateAccounting.objects.count(), 0)
        self.assertContains(response, "enter a valid amount")

    def test_print_creates_billing_event(self):
        accounting = EstateAccounting.objects.create(
            created_by=self.user,
            deceased_name="Alex Estate",
            schedules={
                "assets": [
                    {
                        "description": "Bank account",
                        "institution": "Example Bank",
                        "death_value": "15000.00",
                        "proceeds": "15250.00",
                        "date_received": "",
                        "expenses": "0.00",
                    }
                ],
                "expenses": [],
                "receipts": [],
                "distributions": [],
            },
        )
        from .models import BillingSetting
        BillingSetting.objects.create(
            form_type="estate_accounting",
            form_display_name="Estate Accounting",
            price_per_print=Decimal("4.75"),
        )
        with patch("forms.views.send_form_printed_notification"):
            response = self.client.get(f"/forms/estate-accounting/{accounting.pk}/print/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estate Reconciliation")
        self.assertContains(response, "Example Bank")
        event = PrintEvent.objects.get(form_type="estate_accounting", form_id=accounting.pk)
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.price_charged, Decimal("4.75"))

        response = self.client.get("/forms/billing/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estate Accounting")
        self.assertContains(response, "$4.75")

        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        response = self.client.get("/forms/billing/settings/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estate Accounting")

        response = self.client.get("/forms/billing/history/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estate Accounting")
        self.assertContains(response, f"/forms/billing/printed-copy/{event.pk}/")

        response = self.client.get(f"/forms/billing/printed-copy/{event.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View Only")
        self.assertContains(response, "Example Bank")

    def test_edit_and_soft_delete_estate_accounting(self):
        accounting = EstateAccounting.objects.create(
            created_by=self.user,
            deceased_name="Original Name",
        )
        payload = {
            "deceased_name": "Updated Name",
            "assets_count": "0",
            "expenses_count": "0",
            "receipts_count": "0",
            "distributions_count": "0",
        }
        response = self.client.post(f"/forms/estate-accounting/{accounting.pk}/edit/", payload)
        self.assertRedirects(response, f"/forms/estate-accounting/{accounting.pk}/view/")
        accounting.refresh_from_db()
        self.assertEqual(accounting.deceased_name, "Updated Name")

        response = self.client.post(f"/forms/estate-accounting/{accounting.pk}/delete/")
        self.assertRedirects(response, "/forms/estate-accounting/")
        self.assertFalse(EstateAccounting.objects.filter(pk=accounting.pk).exists())
        self.assertTrue(EstateAccounting.all_objects.get(pk=accounting.pk).is_deleted)
        response = self.client.get("/forms/recycle-bin/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Updated Name")

        response = self.client.post(f"/forms/recycle-bin/restore/estate_accounting/{accounting.pk}/")
        self.assertRedirects(response, "/forms/recycle-bin/")
        accounting.refresh_from_db()
        self.assertFalse(accounting.is_deleted)

        accounting.soft_delete()
        response = self.client.post(f"/forms/recycle-bin/permanent-delete/estate_accounting/{accounting.pk}/")
        self.assertRedirects(response, "/forms/recycle-bin/")
        self.assertFalse(EstateAccounting.all_objects.filter(pk=accounting.pk).exists())
