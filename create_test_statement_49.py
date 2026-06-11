#!/usr/bin/env python
import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_law.settings')
django.setup()

from forms.models import FinancialStatement

# Delete the old test statements if they exist
FinancialStatement.objects.filter(pk__in=[52, 53, 54]).delete()

print("\n" + "="*80)
print("Creating new full-data test statement #1")
print("="*80)

statement = FinancialStatement(
    # Page 1
    court_name="Ontario Superior Court of Justice",
    court_file_number="FAM-2024-001234",
    court_office_address="123 Queen St W, Toronto, ON M5H 2N2",
    prepared_by="applicant",
    applicant_name="Sarah Johnson",
    applicant_address="123 Elm Street, Toronto, ON M5H 1A1",
    applicant_phone="416-555-0101",
    applicant_fax="416-555-0102",
    applicant_email="sarah.johnson@example.com",
    applicant_lawyer_name="Taylor Law LLP",
    applicant_lawyer_address="45 Bay Street, Suite 400, Toronto, ON M5J 2S1",
    applicant_lawyer_phone="416-555-0200",
    applicant_lawyer_fax="416-555-0201",
    applicant_lawyer_email="lawyer@sarahjohnsonlaw.com",
    respondent_name="Daniel Smith",
    respondent_address="18 King Street, Toronto, ON M5H 2L2",
    respondent_phone="416-555-0303",
    respondent_fax="416-555-0304",
    respondent_email="daniel.smith@example.com",
    respondent_lawyer_name="Maple & Co. Legal",
    respondent_lawyer_address="78 Dundas St W, Toronto, ON M5G 2C9",
    respondent_lawyer_phone="416-555-0400",
    respondent_lawyer_fax="416-555-0401",
    respondent_lawyer_email="contact@maplelegal.com",
    valuation_date=date(2026, 6, 1),
    statement_date=date(2026, 6, 9),
    my_name="Sarah Johnson",
    my_location="Toronto, Ontario",
    is_employed=True,
    employer_name_address="Acme Corporation, 500 King St W, Toronto, ON",
    is_self_employed=False,
    business_name_address="",
    is_unemployed=False,
    unemployed_since=None,
    sworn_affidavit="I solemnly swear/affirm that the contents are true.",
    sworn_municipality="Toronto",
    sworn_province_country="Ontario",
    sworn_date=date(2026, 6, 9),
    signature="Sarah Johnson",
    commissioner_signature="M. Brown",
)

statement.save()
print(f"✓ Created statement #{statement.id}")

# Page 2
statement.pay_cheque_stub = True
statement.social_assistance_stub = False
statement.pension_stub = True
statement.workers_comp_stub = False
statement.ei_stub = False
statement.statement_of_income = True
statement.other_income_proof = False
statement.last_year_gross_income = Decimal('85000.00')
statement.indian_status = False
statement.indian_status_docs = ""
statement.income_employment = Decimal('7083.33')
statement.income_commissions = Decimal('400.00')
statement.income_self_employment_before_expenses = Decimal('0.00')
statement.income_self_employment = Decimal('0.00')
statement.income_ei = Decimal('0.00')
statement.income_workers_comp = Decimal('0.00')
statement.income_social_assistance = Decimal('0.00')
statement.income_investment = Decimal('125.00')
statement.income_pension = Decimal('250.00')
statement.income_spousal_support = Decimal('0.00')
statement.income_tax_benefits = Decimal('200.00')
statement.income_other = Decimal('150.00')
statement.income_total_monthly = Decimal('798.33')
statement.income_total_annual = Decimal('9579.96')
statement.draft = {
    "extra_income_rows": [
        {"label": "Freelance", "value": "550.00"},
        {"label": "Rental income", "value": "1200.00"}
    ],
}

# Page 3
statement.benefit_item_1 = "Child support received"
statement.benefit_details_1 = "Child support from previous relationship"
statement.benefit_value_1 = Decimal('400.00')
statement.benefit_item_2 = "Disability benefit"
statement.benefit_details_2 = "Monthly disability payment"
statement.benefit_value_2 = Decimal('300.00')
statement.benefit_item_3 = ""
statement.benefit_details_3 = ""
statement.benefit_value_3 = None
statement.benefit_item_4 = ""
statement.benefit_details_4 = ""
statement.benefit_value_4 = None
statement.draft["extra_benefits"] = [
    {"item": "Freelance consulting", "details": "Project-based income", "value": "1200.00"}
]

statement.cpp_contributions = Decimal('120.00')
statement.ei_premiums = Decimal('75.00')
statement.income_taxes = Decimal('900.00')
statement.employee_pension_contributions = Decimal('200.00')
statement.union_dues = Decimal('50.00')
statement.automatic_deductions_subtotal = Decimal('1345.00')
statement.rent_or_mortgage = Decimal('1800.00')
statement.property_taxes = Decimal('250.00')
statement.property_insurance = Decimal('150.00')
statement.condo_fees = Decimal('0.00')
statement.repairs_maintenance = Decimal('150.00')
statement.housing_subtotal = Decimal('2350.00')
statement.water = Decimal('50.00')
statement.heat = Decimal('120.00')
statement.electricity = Decimal('90.00')
statement.public_transit_taxis = Decimal('160.00')
statement.gas_oil = Decimal('120.00')
statement.car_insurance_license = Decimal('130.00')
statement.car_repairs_maintenance = Decimal('80.00')
statement.parking = Decimal('60.00')
statement.car_loan_lease_payments = Decimal('450.00')
statement.transportation_subtotal = Decimal('1000.00')
statement.health_insurance_premiums = Decimal('180.00')
statement.dental_expenses = Decimal('40.00')
statement.medicine_drugs = Decimal('60.00')
statement.eye_care = Decimal('20.00')
statement.health_subtotal = Decimal('300.00')
statement.clothing = Decimal('180.00')
statement.hair_care_beauty = Decimal('70.00')
statement.alcohol_tobacco = Decimal('35.00')
statement.education = Decimal('90.00')
statement.entertainment = Decimal('80.00')
statement.gifts = Decimal('40.00')
statement.personal_subtotal = Decimal('515.00')
statement.groceries = Decimal('500.00')
statement.household_supplies = Decimal('90.00')
statement.meals_outside = Decimal('120.00')
statement.pet_care = Decimal('60.00')
statement.laundry_dry_cleaning = Decimal('30.00')
statement.household_subtotal = Decimal('800.00')
statement.daycare_expense = Decimal('600.00')
statement.babysitting_costs = Decimal('200.00')
statement.childcare_subtotal = Decimal('800.00')
statement.life_insurance_premiums = Decimal('65.00')
statement.rrsp_resp_withdrawals = Decimal('75.00')
statement.vacations = Decimal('100.00')
statement.school_fees_supplies = Decimal('90.00')
statement.clothing_for_children = Decimal('110.00')
statement.children_activities = Decimal('85.00')
statement.summer_camp_expenses = Decimal('120.00')
statement.debt_payments = Decimal('310.00')
statement.support_paid_for_other_children = Decimal('0.00')
statement.other_expenses_specify = "Phone and internet bundle"
statement.other_expenses_amount = Decimal('120.00')
statement.other_expenses_subtotal = Decimal('120.00')
statement.total_monthly_expenses = Decimal('5790.00')
statement.total_yearly_expenses = Decimal('69480.00')

# Page 4 assets
statement.real_estate = [
    {"details": "Family home", "value": "650000"},
    {"details": "Vacation condo", "value": "210000"}
]
statement.vehicles = [
    {"details": "2019 Honda Civic", "value": "18000"},
    {"details": "2016 Toyota RAV4", "value": "14000"}
]

# Page 5 assets continued
statement.other_possessions = [
    {"address_where_located": "123 Elm Street, Toronto", "value": "5000"}
]
statement.investments = [
    {"type_issuer_due_date_shares": "TD Mutual Funds", "value": "12000"}
]
statement.bank_accounts = [
    {"name_address_institution": "RBC", "account_number": "123456789", "value": "8000"},
    {"name_address_institution": "BMO", "account_number": "987654321", "value": "12000"}
]
statement.savings_plans = [
    {"type_issuer": "RRSP", "account_number": "RRSP123", "value": "22000"}
]
statement.life_insurance = [
    {"type_beneficiary_face_amount": "Term life - 20 years", "cash_surrender_value": "0"}
]
statement.interest_in_business = [
    {"name_address_of_business": "Freelance Design Studio", "value": "15000"}
]
statement.money_owed_to_you = [
    {"name_address_of_debtors": "Friend loan", "value": "3000"}
]
statement.other_assets = [
    {"description": "Art collection", "value": "7500"}
]
statement.total_value_all_property = Decimal('1007500.00')

# Page 6 debts and summary
statement.debts = {
    "mortgage_creditor_1": "TD Bank",
    "mortgage_amount_1": "450000",
    "mortgage_monthly_1": "2200",
    "mortgage_payment_1": "2200",
    "mortgage_creditor_2": "",
    "mortgage_amount_2": "",
    "mortgage_monthly_2": "",
    "mortgage_payment_2": "",
    "mortgage_creditor_3": "",
    "mortgage_amount_3": "",
    "mortgage_monthly_3": "",
    "mortgage_payment_3": "",
    "mortgage_creditor_4": "",
    "mortgage_amount_4": "",
    "mortgage_monthly_4": "",
    "mortgage_payment_4": "",
    "credit_card_creditor_1": "Visa",
    "credit_card_amount_1": "15000",
    "credit_card_monthly_1": "450",
    "credit_card_payment_1": "450",
    "credit_card_creditor_2": "Mastercard",
    "credit_card_amount_2": "6200",
    "credit_card_monthly_2": "180",
    "credit_card_payment_2": "180",
    "unpaid_support_creditor": "",
    "unpaid_support_amount": "",
    "unpaid_support_monthly": "",
    "unpaid_support_payment": "",
    "other_debt_creditor_1": "Student loan",
    "other_debt_amount_1": "12000",
    "other_debt_monthly_1": "200",
    "other_debt_payment_1": "200",
}
statement.total_debts_outstanding = Decimal('483400.00')
statement.total_assets = Decimal('1015070.00')
statement.total_debts = Decimal('483400.00')
statement.net_worth = Decimal('531670.00')
statement.signature = "Sarah Johnson"
statement.commissioner_signature = "M. Brown"

# Page 7 schedule A and B
statement.schedule_a_partnership_income = Decimal('0.00')
statement.schedule_a_rental_income_gross = Decimal('24000.00')
statement.schedule_a_rental_income_net = Decimal('18000.00')
statement.schedule_a_dividends = Decimal('1200.00')
statement.schedule_a_capital_gains = Decimal('3000.00')
statement.schedule_a_capital_losses = Decimal('0.00')
statement.schedule_a_rrsp_withdrawals = Decimal('2500.00')
statement.schedule_a_rrif_annuity = Decimal('0.00')
statement.schedule_a_other_income_source = "Government grant"
statement.schedule_a_other_income_amount = Decimal('600.00')
statement.schedule_a_subtotal = Decimal('22300.00')
statement.lives_alone = False
statement.living_with_someone = True
statement.living_with_name = "Daniel Smith"
statement.lives_with_other_adults = True
statement.other_adults_names = "Daniel Smith"
statement.has_children_in_home = True
statement.number_of_children_in_home = 2
statement.spouse_works = True
statement.spouse_work_place = "Retail Services Corp"
statement.spouse_does_not_work = False
statement.spouse_earns_income = True
statement.spouse_income_amount = Decimal('3200.00')
statement.spouse_income_period = "monthly"
statement.spouse_no_income = False
statement.household_contribution = True
statement.household_contribution_amount = Decimal('800.00')
statement.household_contribution_period = "monthly"

# Page 8 schedule C
statement.schedule_c_expenses = [
    {"child_name": "Ava Johnson", "expense": "Piano lessons", "amount_per_year": "1200", "tax_credits": "120"},
    {"child_name": "Noah Johnson", "expense": "Soccer club fees", "amount_per_year": "900", "tax_credits": "90"}
]
statement.schedule_c_total_annual = Decimal('2100.00')
statement.schedule_c_total_monthly = Decimal('175.00')
statement.schedule_c_my_income_for_share = Decimal('3000.00')

statement.save()
print(f"✓ Populated all fields for statement #{statement.id}")

print("\n" + "="*80)
print("Creating new full-data test statement #2")
print("="*80)

statement2 = FinancialStatement(
    court_name="Ontario Superior Court of Justice",
    court_file_number="FAM-2024-001235",
    court_office_address="456 King St W, Toronto, ON M5V 1L7",
    prepared_by="joint",
    applicant_name="Alicia Green",
    applicant_address="22 Church Street, Toronto, ON M5E 1M2",
    applicant_phone="416-555-0505",
    applicant_fax="416-555-0506",
    applicant_email="alicia.green@example.com",
    applicant_lawyer_name="Green & Partners",
    applicant_lawyer_address="99 Adelaide St W, Toronto, ON M5H 0A1",
    applicant_lawyer_phone="416-555-0600",
    applicant_lawyer_fax="416-555-0601",
    applicant_lawyer_email="alicia.law@greenpartners.com",
    respondent_name="Peter Davis",
    respondent_address="34 King Street, Toronto, ON M5H 4G2",
    respondent_phone="416-555-0707",
    respondent_fax="416-555-0708",
    respondent_email="peter.davis@example.com",
    respondent_lawyer_name="Davis Legal",
    respondent_lawyer_address="10 Wellington St W, Toronto, ON M5V 1G9",
    respondent_lawyer_phone="416-555-0800",
    respondent_lawyer_fax="416-555-0801",
    respondent_lawyer_email="contact@davislegal.com",
    valuation_date=date(2026, 6, 2),
    statement_date=date(2026, 6, 9),
    my_name="Alicia Green",
    my_location="Toronto, Ontario",
    is_employed=True,
    employer_name_address="Nova Tech Solutions, 101 Front St W, Toronto, ON",
    is_self_employed=False,
    business_name_address="",
    is_unemployed=False,
    unemployed_since=None,
    sworn_affidavit="I affirm that the contents of this statement are true.",
    sworn_municipality="Toronto",
    sworn_province_country="Ontario",
    sworn_date=date(2026, 6, 9),
    signature="Alicia Green",
    commissioner_signature="L. Edwards",
)
statement2.save()
print(f"✓ Created statement #{statement2.id}")

statement2.pay_cheque_stub = False
statement2.social_assistance_stub = False
statement2.pension_stub = False
statement2.workers_comp_stub = True
statement2.ei_stub = False
statement2.statement_of_income = True
statement2.other_income_proof = False
statement2.last_year_gross_income = Decimal('56000.00')
statement2.indian_status = False
statement2.indian_status_docs = ""
statement2.income_employment = Decimal('4500.00')
statement2.income_commissions = Decimal('250.00')
statement2.income_self_employment_before_expenses = Decimal('0.00')
statement2.income_self_employment = Decimal('0.00')
statement2.income_ei = Decimal('0.00')
statement2.income_workers_comp = Decimal('350.00')
statement2.income_social_assistance = Decimal('0.00')
statement2.income_investment = Decimal('175.00')
statement2.income_pension = Decimal('0.00')
statement2.income_spousal_support = Decimal('0.00')
statement2.income_tax_benefits = Decimal('150.00')
statement2.income_other = Decimal('75.00')
statement2.income_total_monthly = Decimal('5350.00')
statement2.income_total_annual = Decimal('64200.00')
statement2.draft = {
    "extra_income_rows": [
        {"label": "Consulting", "value": "900.00"}
    ],
}

statement2.benefit_item_1 = "None"
statement2.benefit_details_1 = ""
statement2.benefit_value_1 = None
statement2.benefit_item_2 = "Employee health benefit"
statement2.benefit_details_2 = "Monthly employer-provided health premium"
statement2.benefit_value_2 = Decimal('220.00')
statement2.benefit_item_3 = ""
statement2.benefit_details_3 = ""
statement2.benefit_value_3 = None
statement2.benefit_item_4 = ""
statement2.benefit_details_4 = ""
statement2.benefit_value_4 = None
statement2.draft["extra_benefits"] = []

statement2.cpp_contributions = Decimal('95.00')
statement2.ei_premiums = Decimal('60.00')
statement2.income_taxes = Decimal('650.00')
statement2.employee_pension_contributions = Decimal('120.00')
statement2.union_dues = Decimal('40.00')
statement2.automatic_deductions_subtotal = Decimal('965.00')
statement2.rent_or_mortgage = Decimal('1700.00')
statement2.property_taxes = Decimal('220.00')
statement2.property_insurance = Decimal('140.00')
statement2.condo_fees = Decimal('0.00')
statement2.repairs_maintenance = Decimal('110.00')
statement2.housing_subtotal = Decimal('2170.00')
statement2.water = Decimal('45.00')
statement2.heat = Decimal('110.00')
statement2.electricity = Decimal('85.00')
statement2.public_transit_taxis = Decimal('130.00')
statement2.gas_oil = Decimal('100.00')
statement2.car_insurance_license = Decimal('115.00')
statement2.car_repairs_maintenance = Decimal('70.00')
statement2.parking = Decimal('55.00')
statement2.car_loan_lease_payments = Decimal('420.00')
statement2.transportation_subtotal = Decimal('790.00')
statement2.health_insurance_premiums = Decimal('150.00')
statement2.dental_expenses = Decimal('35.00')
statement2.medicine_drugs = Decimal('55.00')
statement2.eye_care = Decimal('18.00')
statement2.health_subtotal = Decimal('258.00')
statement2.clothing = Decimal('160.00')
statement2.hair_care_beauty = Decimal('65.00')
statement2.alcohol_tobacco = Decimal('30.00')
statement2.education = Decimal('85.00')
statement2.entertainment = Decimal('75.00')
statement2.gifts = Decimal('35.00')
statement2.personal_subtotal = Decimal('450.00')
statement2.groceries = Decimal('480.00')
statement2.household_supplies = Decimal('85.00')
statement2.meals_outside = Decimal('110.00')
statement2.pet_care = Decimal('55.00')
statement2.laundry_dry_cleaning = Decimal('28.00')
statement2.household_subtotal = Decimal('758.00')
statement2.daycare_expense = Decimal('0.00')
statement2.babysitting_costs = Decimal('0.00')
statement2.childcare_subtotal = Decimal('0.00')
statement2.life_insurance_premiums = Decimal('55.00')
statement2.rrsp_resp_withdrawals = Decimal('65.00')
statement2.vacations = Decimal('90.00')
statement2.school_fees_supplies = Decimal('80.00')
statement2.clothing_for_children = Decimal('100.00')
statement2.children_activities = Decimal('70.00')
statement2.summer_camp_expenses = Decimal('100.00')
statement2.debt_payments = Decimal('290.00')
statement2.support_paid_for_other_children = Decimal('0.00')
statement2.other_expenses_specify = "Phone and internet bundle"
statement2.other_expenses_amount = Decimal('110.00')
statement2.other_expenses_subtotal = Decimal('110.00')
statement2.total_monthly_expenses = Decimal('5113.00')
statement2.total_yearly_expenses = Decimal('61356.00')

statement2.real_estate = [
    {"details": "Townhouse", "value": "450000"}
]
statement2.vehicles = [
    {"details": "2021 Subaru Crosstrek", "value": "25000"}
]
statement2.other_possessions = [
    {"address_where_located": "22 Church Street, Toronto", "value": "3000"}
]
statement2.investments = [
    {"type_issuer_due_date_shares": "S&P 500 ETF", "value": "8000"}
]
statement2.bank_accounts = [
    {"name_address_institution": "Scotiabank", "account_number": "555555555", "value": "7000"}
]
statement2.savings_plans = [
    {"type_issuer": "TFSA", "account_number": "TFSA456", "value": "15000"}
]
statement2.life_insurance = [
    {"type_beneficiary_face_amount": "Whole life", "cash_surrender_value": "2500"}
]
statement2.interest_in_business = []
statement2.money_owed_to_you = [
    {"name_address_of_debtors": "Client receivable", "value": "1800"}
]
statement2.other_assets = [
    {"description": "Jewellery", "value": "6000"}
]
statement2.total_value_all_property = Decimal('506300.00')

statement2.debts = {
    "mortgage_creditor_1": "CIBC",
    "mortgage_amount_1": "280000",
    "mortgage_monthly_1": "1350",
    "mortgage_payment_1": "1350",
    "mortgage_creditor_2": "",
    "mortgage_amount_2": "",
    "mortgage_monthly_2": "",
    "mortgage_payment_2": "",
    "mortgage_creditor_3": "",
    "mortgage_amount_3": "",
    "mortgage_monthly_3": "",
    "mortgage_payment_3": "",
    "mortgage_creditor_4": "",
    "mortgage_amount_4": "",
    "mortgage_monthly_4": "",
    "mortgage_payment_4": "",
    "credit_card_creditor_1": "Amex",
    "credit_card_amount_1": "9000",
    "credit_card_monthly_1": "270",
    "credit_card_payment_1": "270",
    "credit_card_creditor_2": "",
    "credit_card_amount_2": "",
    "credit_card_monthly_2": "",
    "credit_card_payment_2": "",
    "unpaid_support_creditor": "",
    "unpaid_support_amount": "",
    "unpaid_support_monthly": "",
    "unpaid_support_payment": "",
}
statement2.total_debts_outstanding = Decimal('289000.00')
statement2.total_assets = Decimal('517100.00')
statement2.total_debts = Decimal('289000.00')
statement2.net_worth = Decimal('228100.00')
statement2.sworn_municipality = "Toronto"
statement2.sworn_province_country = "Ontario"
statement2.signature = "Alicia Green"
statement2.commissioner_signature = "L. Edwards"

statement2.schedule_a_partnership_income = Decimal('0.00')
statement2.schedule_a_rental_income_gross = Decimal('18000.00')
statement2.schedule_a_rental_income_net = Decimal('13000.00')
statement2.schedule_a_dividends = Decimal('900.00')
statement2.schedule_a_capital_gains = Decimal('1500.00')
statement2.schedule_a_capital_losses = Decimal('0.00')
statement2.schedule_a_rrsp_withdrawals = Decimal('1000.00')
statement2.schedule_a_rrif_annuity = Decimal('0.00')
statement2.schedule_a_other_income_source = "Childcare subsidy"
statement2.schedule_a_other_income_amount = Decimal('400.00')
statement2.schedule_a_subtotal = Decimal('15700.00')
statement2.lives_alone = False
statement2.living_with_someone = True
statement2.living_with_name = "Peter Davis"
statement2.lives_with_other_adults = False
statement2.other_adults_names = ""
statement2.has_children_in_home = True
statement2.number_of_children_in_home = 1
statement2.spouse_works = True
statement2.spouse_work_place = "Retail Services Corp"
statement2.spouse_does_not_work = False
statement2.spouse_earns_income = True
statement2.spouse_income_amount = Decimal('2600.00')
statement2.spouse_income_period = "monthly"
statement2.spouse_no_income = False
statement2.household_contribution = True
statement2.household_contribution_amount = Decimal('600.00')
statement2.household_contribution_period = "monthly"

statement2.schedule_c_expenses = [
    {"child_name": "Mia Green", "expense": "Art classes", "amount_per_year": "800", "tax_credits": "80"}
]
statement2.schedule_c_total_annual = Decimal('800.00')
statement2.schedule_c_total_monthly = Decimal('66.67')
statement2.schedule_c_my_income_for_share = Decimal('2500.00')

statement2.save()
print(f"✓ Populated all fields for statement #{statement2.id}")

# Verify statements
statement.refresh_from_db()
statement2.refresh_from_db()
print(f"\n" + "="*80)
print("VERIFICATION")
print("="*80)
print(f"\nStatement 1 ID: {statement.id} Applicant: {statement.applicant_name}")
print(f"Statement 2 ID: {statement2.id} Applicant: {statement2.applicant_name}")
print(f"Statement 2 Page 2 Last year gross income: {statement2.last_year_gross_income}")
print(f"Statement 2 Page 8 Schedule C annual: {statement2.schedule_c_total_annual}")
print(f"\n" + "="*80 + "\n")