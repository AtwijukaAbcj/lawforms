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
		# unauthenticated cannot access case detail
		resp = self.client.get(f'/forms/cases/{self.case.pk}/')
		self.assertEqual(resp.status_code, 302)
		# login as other user -> 404
		self.client.login(username='other', password='pass')
		resp = self.client.get(f'/forms/cases/{self.case.pk}/')
		self.assertEqual(resp.status_code, 404)
		# owner can access
		self.client.login(username='tester', password='pass')
		resp = self.client.get(f'/forms/cases/{self.case.pk}/')
		self.assertEqual(resp.status_code, 200)

	def test_case_create_and_links(self):
		self.client.login(username='tester', password='pass')
		resp = self.client.post('/forms/cases/new/', {'court_file_number':'X','applicant_name':'A','respondent_name':'B'})
		# should redirect to detail
		self.assertEqual(resp.status_code, 302)
		new_case = CaseFile.objects.get(court_file_number='X')
		# detail includes create form links
		resp = self.client.get(f'/forms/cases/{new_case.pk}/')
		self.assertContains(resp, '?case_id=')

	def test_push_case_updates_forms(self):
		# create a related financial statement with different data
		self.client.login(username='tester', password='pass')
		fs = FinancialStatement.objects.create(case_file=self.case, court_file_number='OLD', applicant_name='Old', respondent_name='Old')
		# perform push
		resp = self.client.post(f'/forms/cases/{self.case.pk}/push/')
		self.assertEqual(resp.status_code, 302)
		fs.refresh_from_db()
		# after push, fields should match case
		self.assertEqual(fs.court_file_number, self.case.court_file_number)
		self.assertEqual(fs.applicant_name, self.case.applicant_name)        self.assertEqual(fs.respondent_name, self.case.respondent_name)

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