#!/usr/bin/env python
"""
Submit Full Data Sample - Create complete FinancialStatement for UI testing
"""

import os
import django
from decimal import Decimal
from datetime import datetime, date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_law.settings')
django.setup()

from django.contrib.auth.models import User
from forms.models import FinancialStatement

print("\n" + "="*80)
print("SUBMITTING FULL DATA SAMPLE FOR UI TESTING")
print("="*80)

# Create test user (or reuse existing)
try:
    user = User.objects.get(username='testuser')
    print(f"\n✓ Using existing test user: testuser")
except User.DoesNotExist:
    user = User.objects.create_user(username='testuser', password='test123')
    print(f"\n✓ Created new test user: testuser")

print(f"  Password: test123")
print(f"  Login at: http://localhost:8000/admin/")

# Delete any existing test statements
FinancialStatement.objects.filter(applicant_name__icontains="Test User").delete()

# Create comprehensive financial statement
statement = FinancialStatement.objects.create(
    # ========== PAGE 1: COURT INFO & PERSONAL DETAILS ==========
    court_name="Ontario Superior Court of Justice",
    court_file_number="FAM-2024-001234",
    court_office_address="393 University Ave, Toronto, ON M5G 1E6",
    
    prepared_by="applicant",
    applicant_name="Sarah Johnson",
    applicant_address="123 Main Street, Toronto, Ontario M5H 2R2",
    applicant_phone="416-555-0123",
    applicant_fax="416-555-0124",
    applicant_email="sarah.johnson@email.com",
    applicant_lawyer_name="John Smith",
    applicant_lawyer_address="456 Bay Street, Toronto, ON M5J 2R2",
    applicant_lawyer_phone="416-555-5555",
    applicant_lawyer_fax="416-555-5556",
    applicant_lawyer_email="john.smith@lawfirm.ca",
    
    respondent_name="Michael Johnson",
    respondent_address="789 King Street West, Toronto, Ontario M5H 2Y9",
    respondent_phone="416-555-9999",
    respondent_fax="416-555-9998",
    respondent_email="michael.johnson@email.com",
    respondent_lawyer_name="Jane Doe",
    respondent_lawyer_address="321 Church Street, Toronto, ON M5B 1Y7",
    respondent_lawyer_phone="416-555-7777",
    respondent_lawyer_fax="416-555-7778",
    respondent_lawyer_email="jane.doe@lawfirm.ca",
    
    my_name="Sarah Johnson",
    my_location="Toronto, Ontario",
    sworn_affidavit="I solemnly swear/affirm that the contents of this Financial Statement are true.",
    
    is_employed=True,
    is_self_employed=False,
    is_unemployed=False,
    employer_name_address="ABC Corporation, 100 Front Street, Toronto, ON",
    
    # ========== PAGE 2: INCOME & PROOF OF INCOME ==========
    pay_cheque_stub=True,
    social_assistance_stub=False,
    pension_stub=False,
    workers_comp_stub=False,
    ei_stub=False,
    statement_of_income=False,
    
    last_year_gross_income=Decimal('85000.00'),
    income_employment=Decimal('7083.33'),
    income_commissions=Decimal('0.00'),
    income_self_employment_before_expenses=Decimal('0.00'),
    income_self_employment=Decimal('0.00'),
    income_ei=Decimal('0.00'),
    income_workers_comp=Decimal('0.00'),
    income_social_assistance=Decimal('0.00'),
    income_investment=Decimal('125.00'),
    income_pension=Decimal('0.00'),
    income_spousal_support=Decimal('0.00'),
    income_tax_benefits=Decimal('200.00'),
    income_other=Decimal('0.00'),
    income_total_monthly=Decimal('7408.33'),
    income_total_annual=Decimal('88900.00'),
    
    # ========== PAGE 3: OTHER INCOME & DEDUCTIONS ==========
    benefit_item_1="Investment Income",
    benefit_value_1=Decimal('125.00'),
    benefit_item_2="Tax Benefit",
    benefit_value_2=Decimal('200.00'),
    cpp_contributions=Decimal('450.00'),
    ei_premiums=Decimal('320.00'),
    income_taxes=Decimal('1200.00'),
    
    # ========== PAGE 4: MONTHLY EXPENSES ==========
    rent_or_mortgage=Decimal('1800.00'),
    property_taxes=Decimal('150.00'),
    repairs_maintenance=Decimal('150.00'),
    water=Decimal('50.00'),
    heat=Decimal('80.00'),
    electricity=Decimal('120.00'),
    telephone=Decimal('50.00'),
    cell_phone=Decimal('100.00'),
    internet=Decimal('75.00'),
    public_transit_taxis=Decimal('100.00'),
    gas_oil=Decimal('300.00'),
    car_insurance_license=Decimal('180.00'),
    car_repairs_maintenance=Decimal('100.00'),
    car_loan_lease_payments=Decimal('350.00'),
    health_insurance_premiums=Decimal('100.00'),
    dental_expenses=Decimal('50.00'),
    medicine_drugs=Decimal('25.00'),
    clothing=Decimal('150.00'),
    hair_care_beauty=Decimal('50.00'),
    education=Decimal('0.00'),
    entertainment=Decimal('200.00'),
    gifts=Decimal('100.00'),
    groceries=Decimal('600.00'),
    household_supplies=Decimal('75.00'),
    meals_outside=Decimal('200.00'),
    pet_care=Decimal('50.00'),
    laundry_dry_cleaning=Decimal('30.00'),
    daycare_expense=Decimal('0.00'),
    life_insurance_premiums=Decimal('50.00'),
    vacations=Decimal('200.00'),
    debt_payments=Decimal('300.00'),
    support_paid_for_other_children=Decimal('0.00'),
    other_expenses_specify="",
    other_expenses_amount=Decimal('0.00'),
    total_monthly_expenses=Decimal('6285.00'),
    
    # ========== PAGE 5: ASSETS & PROPERTY ==========
    real_estate=[
        {
            "details": "Principal Residence - House in Toronto",
            "value": "650000"
        }
    ],
    
    vehicles=[
        {
            "description": "2019 Honda Accord",
            "value": "18000"
        }
    ],
    
    bank_accounts=[
        {
            "name_address_institution": "Royal Bank of Canada - Chequings",
            "account_number": "123-456789",
            "value": "5000"
        },
        {
            "name_address_institution": "TD Bank - Savings",
            "account_number": "987-654321",
            "value": "15000"
        }
    ],
    
    investments=[
        {
            "type_issuer_due_date_shares": "RRSP - Vanguard Index Fund",
            "value": "85000"
        },
        {
            "type_issuer_due_date_shares": "TFSA - Dividend Growth ETF",
            "value": "25000"
        }
    ],
    
    savings_plans=[
        {
            "type_issuer": "Employer Pension Plan - ABC Corp",
            "value": "120000"
        }
    ],
    
    total_value_all_property=Decimal('898000.00'),
    
    # ========== PAGE 6: DEBTS & LIABILITIES ==========
    total_assets=Decimal('898000.00'),
    debts=[
        {
            "type": "Mortgage",
            "creditor": "Royal Bank of Canada",
            "full_amount": "450000",
            "monthly_payment": "2400",
            "payments_being_made": "Yes"
        },
        {
            "type": "Credit Card - Visa",
            "creditor": "Visa",
            "full_amount": "2500",
            "monthly_payment": "100",
            "payments_being_made": "Yes"
        },
        {
            "type": "Credit Card - Mastercard",
            "creditor": "Mastercard",
            "full_amount": "1200",
            "monthly_payment": "50",
            "payments_being_made": "Yes"
        },
        {
            "type": "Line of Credit",
            "creditor": "Royal Bank",
            "full_amount": "5000",
            "monthly_payment": "150",
            "payments_being_made": "Yes"
        },
        {
            "type": "Personal Loan",
            "creditor": "Finance Company",
            "full_amount": "8000",
            "monthly_payment": "300",
            "payments_being_made": "Yes"
        }
    ],
    total_debts_outstanding=Decimal('466700.00'),
    total_debts=Decimal('466700.00'),
    net_worth=Decimal('431300.00'),
    
    sworn_municipality="Toronto",
    sworn_province_country="Ontario, Canada",
    sworn_date=date.today(),
    commissioner_signature="Mary Smith, Commissioner for Oaths",
    signature="Sarah Johnson",
    
    # ========== PAGE 7: OTHER INFO ==========
    schedule_a_partnership_income=Decimal('0.00'),
    schedule_a_rental_income_gross=Decimal('0.00'),
    lives_alone=False,
    living_with_someone=True,
    living_with_name="Michael Johnson",
    has_children_in_home=False,
    spouse_works=False,
    spouse_does_not_work=True,
    
    # ========== PAGE 8: SCHEDULE C ==========
    schedule_c_total_annual=Decimal('0.00'),
    schedule_c_total_monthly=Decimal('0.00'),
)

print(f"\n✓ Created Financial Statement #{statement.id}")
print(f"\n📋 FORM DATA SUMMARY:")
print(f"   Court: {statement.court_name}")
print(f"   Court File: {statement.court_file_number}")
print(f"   Applicant: {statement.applicant_name}")
print(f"   Respondent: {statement.respondent_name}")
print(f"   Monthly Income: ${statement.income_total_monthly:,.2f}")
print(f"   Monthly Expenses: ${statement.total_monthly_expenses:,.2f}")
print(f"   Total Assets: ${statement.total_assets:,.2f}")
print(f"   Total Debts: ${statement.total_debts:,.2f}")
print(f"   Net Worth: ${statement.net_worth:,.2f}")
print(f"   Real Estate: {len(statement.real_estate)} property")
print(f"   Investments: {len(statement.investments)} accounts")
print(f"   Bank Accounts: {len(statement.bank_accounts)} accounts")

print(f"\n" + "="*80)
print(f"✓✓✓ READY FOR UI TESTING")
print(f"="*80)
print(f"\nStatement ID: {statement.id}")
print(f"Login Username: testuser")
print(f"Login Password: test123")
print(f"\nYou can now:")
print(f"1. Go to http://localhost:8000/admin/")
print(f"2. Login with testuser / test123")
print(f"3. Navigate to Forms > Financial Statements")
print(f"4. Open Statement #{statement.id}")
print(f"5. Edit any page and verify data persistence")
print(f"="*80 + "\n")
