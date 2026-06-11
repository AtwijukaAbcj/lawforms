from decimal import Decimal

from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import CaseFile, FinancialStatement, NetFamilyPropertyStatement, NetFamilyProperty13B, ComparisonNetFamilyProperty


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
