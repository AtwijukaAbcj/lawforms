"""
Script to populate a complete Financial Statement (Form 13) with test data using new page-based storage.
Run with: python manage.py shell < populate_financial_statement_form13.py
Includes all fields: Pages 1-8, Schedules A, B, C, and all model fields.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_law.settings')
django.setup()

from forms.models import FinancialStatement
from datetime import date
from decimal import Decimal

# Create a new Financial Statement with FULL test data for ALL fields
statement = FinancialStatement.objects.create(
    # Basic info
    court_file_number="FC-2026-00789",
    court_name="Ontario Superior Court of Justice (Family Court)",
    court_office_address="393 University Avenue, Toronto, ON M5G 1E6",
    prepared_by="applicant",
    valuation_date=date(2026, 6, 1),
    statement_date=date(2026, 6, 10),
    
    # Applicant Info
    applicant_name="Sarah Jane Johnson",
    applicant_address="456 Oak Street, Unit 200, Toronto, ON M5K 2N4",
    applicant_phone="(416) 555-5678",
    applicant_fax="(416) 555-5679",
    applicant_email="sarah.johnson@email.com",
    
    # Applicant Lawyer Info
    applicant_lawyer_name="Robert Thompson, QC",
    applicant_lawyer_address="789 King Street West, Suite 500, Toronto, ON M5H 2Z7",
    applicant_lawyer_phone="(416) 555-7890",
    applicant_lawyer_fax="(416) 555-7891",
    applicant_lawyer_email="rthompson@lawfirm.ca",
    
    # Respondent Info
    respondent_name="Michael David Johnson",
    respondent_address="789 Maple Avenue, Toronto, ON M5J 1K5",
    respondent_phone="(416) 555-9012",
    respondent_fax="(416) 555-9013",
    respondent_email="michael.johnson@email.com",
    
    # Respondent Lawyer Info
    respondent_lawyer_name="Jennifer Walsh",
    respondent_lawyer_address="321 Bay Street, Suite 300, Toronto, ON M5H 2R2",
    respondent_lawyer_phone="(416) 555-4567",
    respondent_lawyer_fax="(416) 555-4568",
    respondent_lawyer_email="jwalsh@lawfirm.ca",
    
    # Part 1 - Identification (Page 1)
    my_name="Sarah Jane Johnson",
    my_location="Toronto, Ontario",
    
    # Employment status (Page 1)
    is_employed=True,
    employer_name_address="TechCorp Solutions, 123 Bay Street, Toronto, ON M5H 2T1",
    is_self_employed=False,
    is_unemployed=False,
    
    # Page 2 - Proof of Income
    pay_cheque_stub=True,
    social_assistance_stub=False,
    pension_stub=False,
    workers_comp_stub=False,
    ei_stub=False,
    statement_of_income=True,
    other_income_proof=False,
    indian_status=False,
    indian_status_docs="",
    last_year_gross_income=Decimal('85000.00'),
    
    # Income table (Page 2)
    income_employment=Decimal('6500.00'),
    income_commissions=Decimal('500.00'),
    income_self_employment_before_expenses=Decimal('0.00'),
    income_self_employment=Decimal('0.00'),
    income_ei=Decimal('0.00'),
    income_workers_comp=Decimal('0.00'),
    income_social_assistance=Decimal('0.00'),
    income_investment=Decimal('125.50'),
    income_pension=Decimal('0.00'),
    income_spousal_support=Decimal('0.00'),
    income_tax_benefits=Decimal('250.00'),
    income_other=Decimal('0.00'),
    income_total_monthly=Decimal('7375.50'),
    income_total_annual=Decimal('88506.00'),
    
    # Page 3 - Other Benefits (Page 3)
    benefit_item_1="Car Allowance",
    benefit_details_1="Monthly car allowance from employer",
    benefit_value_1=Decimal('250.00'),
    benefit_item_2="Bonus",
    benefit_details_2="Annual bonus paid quarterly",
    benefit_value_2=Decimal('500.00'),
    benefit_item_3="Matching RRSP",
    benefit_details_3="Employer RRSP matching program (5% of salary)",
    benefit_value_3=Decimal('325.00'),
    benefit_item_4="Professional Development",
    benefit_details_4="Annual professional development allowance",
    benefit_value_4=Decimal('100.00'),
    
    # Page 3 - Automatic Deductions
    cpp_contributions=Decimal('375.00'),
    ei_premiums=Decimal('285.00'),
    income_taxes=Decimal('1200.00'),
    employee_pension_contributions=Decimal('400.00'),
    union_dues=Decimal('0.00'),
    automatic_deductions_subtotal=Decimal('2260.00'),
    
    # Page 3 - Housing Expenses
    rent_or_mortgage=Decimal('1800.00'),
    property_taxes=Decimal('0.00'),
    property_insurance=Decimal('50.00'),
    condo_fees=Decimal('0.00'),
    repairs_maintenance=Decimal('100.00'),
    housing_subtotal=Decimal('1950.00'),
    
    # Page 3 - Utilities
    water=Decimal('80.00'),
    heat=Decimal('120.00'),
    electricity=Decimal('150.00'),
    telephone=Decimal('60.00'),
    cell_phone=Decimal('80.00'),
    cable=Decimal('75.00'),
    internet=Decimal('60.00'),
    utilities_subtotal=Decimal('625.00'),
    
    # Page 3 - Transportation
    public_transit_taxis=Decimal('50.00'),
    gas_oil=Decimal('200.00'),
    car_insurance_license=Decimal('180.00'),
    car_repairs_maintenance=Decimal('100.00'),
    parking=Decimal('50.00'),
    car_loan_lease_payments=Decimal('350.00'),
    transportation_subtotal=Decimal('930.00'),
    
    # Page 3 - Health
    health_insurance_premiums=Decimal('150.00'),
    dental_expenses=Decimal('75.00'),
    medicine_drugs=Decimal('50.00'),
    eye_care=Decimal('25.00'),
    health_subtotal=Decimal('300.00'),
    
    # Page 3 - Personal
    clothing=Decimal('100.00'),
    hair_care_beauty=Decimal('60.00'),
    alcohol_tobacco=Decimal('30.00'),
    education=Decimal('50.00'),
    entertainment=Decimal('80.00'),
    gifts=Decimal('50.00'),
    personal_subtotal=Decimal('320.00'),
    
    # Page 4 - Household Expenses
    groceries=Decimal('400.00'),
    household_supplies=Decimal('75.00'),
    meals_outside=Decimal('150.00'),
    pet_care=Decimal('0.00'),
    laundry_dry_cleaning=Decimal('50.00'),
    household_subtotal=Decimal('675.00'),
    
    # Page 4 - Childcare Costs
    daycare_expense=Decimal('0.00'),
    babysitting_costs=Decimal('0.00'),
    childcare_subtotal=Decimal('0.00'),
    
    # Page 4 - Other Expenses
    life_insurance_premiums=Decimal('75.00'),
    rrsp_resp_withdrawals=Decimal('0.00'),
    vacations=Decimal('200.00'),
    school_fees_supplies=Decimal('0.00'),
    clothing_for_children=Decimal('0.00'),
    children_activities=Decimal('0.00'),
    summer_camp_expenses=Decimal('0.00'),
    debt_payments=Decimal('150.00'),
    support_paid_for_other_children=Decimal('0.00'),
    other_expenses_specify="Professional development courses, books, certifications",
    other_expenses_amount=Decimal('100.00'),
    other_expenses_subtotal=Decimal('525.00'),
    
    # Total Expenses
    total_monthly_expenses=Decimal('8210.00'),
    total_yearly_expenses=Decimal('98520.00'),
    
    # Page 5/6 - Summary and Signature
    total_assets=Decimal('520000.00'),
    total_debts=Decimal('355500.00'),
    net_worth=Decimal('164500.00'),
    total_debts_outstanding=Decimal('355500.00'),
    
    # Signature section (Page 1 & 6)
    sworn_municipality="Toronto",
    sworn_province_country="Ontario",
    sworn_date=date(2026, 6, 10),
    signature="Sarah Jane Johnson",
    commissioner_signature="Jane Smith, Commissioner",
    
    # Page 7 - Schedule A - Additional Sources of Income
    schedule_a_partnership_income=Decimal('0.00'),
    schedule_a_rental_income_gross=Decimal('0.00'),
    schedule_a_rental_income_net=Decimal('0.00'),
    schedule_a_dividends=Decimal('125.00'),
    schedule_a_capital_gains=Decimal('0.00'),
    schedule_a_capital_losses=Decimal('0.00'),
    schedule_a_rrsp_withdrawals=Decimal('0.00'),
    schedule_a_rrif_annuity=Decimal('0.00'),
    schedule_a_other_income_source="Investment income from mutual funds",
    schedule_a_other_income_amount=Decimal('0.50'),
    schedule_a_subtotal=Decimal('125.50'),
    
    # Page 7 - Schedule B - Other Income Earners in Home
    lives_alone=False,
    living_with_someone=True,
    living_with_name="No spouse living with applicant",
    lives_with_other_adults=False,
    other_adults_names="",
    has_children_in_home=False,
    number_of_children_in_home=0,
    spouse_works=False,
    spouse_work_place="",
    spouse_does_not_work=True,
    spouse_earns_income=False,
    spouse_income_amount=Decimal('0.00'),
    spouse_income_period="",
    spouse_no_income=True,
    household_contribution=False,
    household_contribution_amount=Decimal('0.00'),
    household_contribution_period="",
    
    # Page 8 - Schedule C - Special/Extraordinary Expenses for Children (empty for this example)
    schedule_c_total_annual=Decimal('0.00'),
    schedule_c_total_monthly=Decimal('0.00'),
    schedule_c_my_income_for_share=Decimal('0.00'),
)


print(f"✓ Created Financial Statement #{statement.id}")

# PAGE 2 - Income Proof and Income Table (Complete)
page2_data = {
    'pay_cheque_stub': True,
    'social_assistance_stub': False,
    'pension_stub': False,
    'workers_comp_stub': False,
    'ei_stub': False,
    'statement_of_income': True,
    'other_income_proof': False,
    'indian_status': False,
    'indian_status_docs': '',
    'last_year_gross_income': '85000.00',
    'income_employment': '6500.00',
    'income_commissions': '500.00',
    'income_self_employment_before_expenses': '0.00',
    'income_self_employment': '0.00',
    'income_ei': '0.00',
    'income_workers_comp': '0.00',
    'income_social_assistance': '0.00',
    'income_investment': '125.50',
    'income_pension': '0.00',
    'income_spousal_support': '0.00',
    'income_tax_benefits': '250.00',
    'income_other': '0.00',
    'income_total_monthly': '7375.50',
    'income_total_annual': '88506.00',
}
statement.save_page_data(2, page2_data)
print(f"✓ Saved Page 2 data (income proof & table)")

# PAGE 3 - Other Benefits and Expenses (Complete)
page3_data = {
    'benefit_item_1': 'Car Allowance',
    'benefit_details_1': 'Monthly car allowance from employer',
    'benefit_value_1': '250.00',
    'benefit_item_2': 'Bonus',
    'benefit_details_2': 'Annual bonus paid quarterly',
    'benefit_value_2': '500.00',
    'benefit_item_3': 'Matching RRSP',
    'benefit_details_3': 'Employer RRSP matching program (5% of salary)',
    'benefit_value_3': '325.00',
    'benefit_item_4': 'Professional Development',
    'benefit_details_4': 'Annual professional development allowance',
    'benefit_value_4': '100.00',
    # Automatic Deductions
    'cpp_contributions': '375.00',
    'ei_premiums': '285.00',
    'income_taxes': '1200.00',
    'employee_pension_contributions': '400.00',
    'union_dues': '0.00',
    'automatic_deductions_subtotal': '2260.00',
    # Housing
    'rent_or_mortgage': '1800.00',
    'property_taxes': '0.00',
    'property_insurance': '50.00',
    'condo_fees': '0.00',
    'repairs_maintenance': '100.00',
    'housing_subtotal': '1950.00',
    # Utilities
    'water': '80.00',
    'heat': '120.00',
    'electricity': '150.00',
    'telephone': '60.00',
    'cell_phone': '80.00',
    'cable': '75.00',
    'internet': '60.00',
    'utilities_subtotal': '625.00',
    # Transportation
    'public_transit_taxis': '50.00',
    'gas_oil': '200.00',
    'car_insurance_license': '180.00',
    'car_repairs_maintenance': '100.00',
    'parking': '50.00',
    'car_loan_lease_payments': '350.00',
    'transportation_subtotal': '930.00',
    # Health
    'health_insurance_premiums': '150.00',
    'dental_expenses': '75.00',
    'medicine_drugs': '50.00',
    'eye_care': '25.00',
    'health_subtotal': '300.00',
    # Personal
    'clothing': '100.00',
    'hair_care_beauty': '60.00',
    'alcohol_tobacco': '30.00',
    'education': '50.00',
    'entertainment': '80.00',
    'gifts': '50.00',
    'personal_subtotal': '320.00',
    # Household
    'groceries': '400.00',
    'household_supplies': '75.00',
    'meals_outside': '150.00',
    'pet_care': '0.00',
    'laundry_dry_cleaning': '50.00',
    'household_subtotal': '675.00',
    # Childcare
    'daycare_expense': '0.00',
    'babysitting_costs': '0.00',
    'childcare_subtotal': '0.00',
    # Other Expenses
    'life_insurance_premiums': '75.00',
    'rrsp_resp_withdrawals': '0.00',
    'vacations': '200.00',
    'school_fees_supplies': '0.00',
    'clothing_for_children': '0.00',
    'children_activities': '0.00',
    'summer_camp_expenses': '0.00',
    'debt_payments': '150.00',
    'support_paid_for_other_children': '0.00',
    'other_expenses_specify': 'Professional development courses, books, certifications',
    'other_expenses_amount': '100.00',
    'other_expenses_subtotal': '525.00',
    'total_monthly_expenses': '8210.00',
    'total_yearly_expenses': '98520.00',
}
statement.save_page_data(3, page3_data)
print(f"✓ Saved Page 3 data (benefits & expenses)")

# PAGE 4 - Assets: Real Estate, Vehicles
page4_data = {
    'real_estate_1': '456 Oak Street, Unit 200, Toronto, ON - Primary Residence',
    'real_estate_value_1': '450000.00',
    'vehicles_1': '2021 Toyota Camry - Blue Sedan',
    'vehicles_value_1': '22000.00',
}

# Add JSON arrays for assets
statement.real_estate = [
    {
        'details': '456 Oak Street, Unit 200, Toronto, ON - Primary Residence',
        'value': '450000.00'
    }
]

statement.vehicles = [
    {
        'details': '2021 Toyota Camry - Blue Sedan',
        'value': '22000.00'
    }
]

statement.save_page_data(4, page4_data)
print(f"✓ Saved Page 4 data (real estate & vehicles)")

# PAGE 5 - Assets: Bank Accounts, Investments, Insurance
page5_data = {
    'total_value_all_property': '520000.00',
}

# Bank Accounts
statement.bank_accounts = [
    {
        'name_address_institution': 'TD Bank - Toronto',
        'account_number': 'xxxxx2345',
        'value': '15000.00'
    },
    {
        'name_address_institution': 'Royal Bank - Toronto',
        'account_number': 'xxxxx6789',
        'value': '8500.00'
    }
]

# TFSA/Savings Plans
statement.savings_plans = [
    {
        'type_issuer': 'TFSA - Royal Bank',
        'account_number': 'TFSA-2024',
        'value': '12000.00'
    }
]

# Investments
statement.investments = [
    {
        'type_issuer_due_date_shares': 'Mutual Fund - RRSP (Vanguard Index Fund)',
        'value': '25000.00'
    },
    {
        'type_issuer_due_date_shares': 'GIC - 5-Year (TD Bank)',
        'value': '10000.00'
    }
]

# Life Insurance (cash surrender value)
statement.life_insurance = [
    {
        'type_beneficiary_face_amount': 'Term Life - Face Amount $200,000',
        'cash_surrender_value': '3500.00'
    }
]

# Money Owed to You
statement.money_owed_to_you = [
    {
        'name_address_of_debtors': 'John Smith - Personal Loan (Family friend)',
        'value': '2000.00'
    }
]

# Other Possessions
statement.other_possessions = [
    {
        'address_where_located': 'Home',
        'value': '5000.00'
    }
]

statement.total_value_all_property = Decimal('520000.00')

statement.save_page_data(5, page5_data)
print(f"✓ Saved Page 5 data (bank accounts, investments, insurance)")

# PAGE 6 - Debts and Summary
page6_data = {
    'mortgage_creditor_1': 'TD Mortgage',
    'mortgage_amount_1': '350000.00',
    'mortgage_monthly_1': '1800.00',
    'mortgage_payment_1': 'Yes',
    'mortgage_creditor_2': '',
    'mortgage_amount_2': '',
    'mortgage_monthly_2': '',
    'mortgage_payment_2': '',
    'mortgage_creditor_3': '',
    'mortgage_amount_3': '',
    'mortgage_monthly_3': '',
    'mortgage_payment_3': '',
    'mortgage_creditor_4': '',
    'mortgage_amount_4': '',
    'mortgage_monthly_4': '',
    'mortgage_payment_4': '',
    'credit_card_creditor_1': 'Visa',
    'credit_card_amount_1': '3500.00',
    'credit_card_monthly_1': '250.00',
    'credit_card_payment_1': 'Yes',
    'credit_card_creditor_2': 'MasterCard',
    'credit_card_amount_2': '2000.00',
    'credit_card_monthly_2': '150.00',
    'credit_card_payment_2': 'Yes',
    'unpaid_support_creditor': '',
    'unpaid_support_amount': '',
    'unpaid_support_monthly': '',
    'unpaid_support_payment': '',
    'total_debts_outstanding': '355500.00',
    'total_assets': '520000.00',
    'subtract_total_debts': '355500.00',
    'net_worth': '164500.00',
    'municipality': 'Toronto',
    'province': 'Ontario',
    'date': str(date.today()),
    'signature': 'Sarah Jane Johnson',
    'commissioner': 'Jane Smith, Commissioner',
}

# Add JSON array for debts
statement.debts = [
    {
        'type': 'Mortgage',
        'creditor': 'TD Mortgage',
        'full_amount': '350000.00',
        'monthly_payment': '1800.00',
        'payments_being_made': 'Yes'
    },
    {
        'type': 'Credit Card',
        'creditor': 'Visa',
        'full_amount': '3500.00',
        'monthly_payment': '250.00',
        'payments_being_made': 'Yes'
    },
    {
        'type': 'Credit Card',
        'creditor': 'MasterCard',
        'full_amount': '2000.00',
        'monthly_payment': '150.00',
        'payments_being_made': 'Yes'
    }
]

statement.save_page_data(6, page6_data)
print(f"✓ Saved Page 6 data (debts & summary)")

# PAGE 7 - Schedule A & B (Additional Income and Other Income Earners)
page7_data = {
    'schedule_a_partnership_income': '0.00',
    'schedule_a_rental_income_gross': '0.00',
    'schedule_a_rental_income_net': '0.00',
    'schedule_a_dividends': '125.00',
    'schedule_a_capital_gains': '0.00',
    'schedule_a_capital_losses': '0.00',
    'schedule_a_rrsp_withdrawals': '0.00',
    'schedule_a_rrif_annuity': '0.00',
    'schedule_a_other_income_source': 'Investment income from mutual funds and GIC interest',
    'schedule_a_other_income_amount': '0.50',
    'schedule_a_subtotal': '125.50',
    # Schedule B
    'lives_alone': False,
    'living_with_someone': True,
    'living_with_name': 'Lives in home alone (own household)',
    'lives_with_other_adults': False,
    'other_adults_names': '',
    'has_children_in_home': False,
    'number_of_children_in_home': '0',
    'spouse_works': False,
    'spouse_work_place': '',
    'spouse_does_not_work': True,
    'spouse_earns_income': False,
    'spouse_income_amount': '0.00',
    'spouse_income_period': '',
    'spouse_no_income': True,
    'household_contribution': False,
    'household_contribution_amount': '0.00',
    'household_contribution_period': '',
}
statement.save_page_data(7, page7_data)
print(f"✓ Saved Page 7 data (Schedule A & B)")

# PAGE 8 - Schedule C (Special/Extraordinary Expenses for Children)
page8_data = {
    'schedule_c_total_annual': '0.00',
    'schedule_c_total_monthly': '0.00',
    'schedule_c_my_income_for_share': '0.00',
}

# Add JSON array for Schedule C expenses (empty for this example)
statement.schedule_c_expenses = []

statement.save_page_data(8, page8_data)
print(f"✓ Saved Page 8 data (Schedule C)")

# Final comprehensive save
statement.save()
print(f"\n" + "="*60)
print(f"✅ Financial Statement #{statement.id} COMPLETE!")
print(f"="*60)
print(f"Court File: {statement.court_file_number}")
print(f"Applicant: {statement.applicant_name}")
print(f"Prepared By: {statement.prepared_by.upper()}")
print(f"\nAll Pages and Schedules Populated:")
print(f"  ✓ Page 1 - Identification & Employment Status")
print(f"  ✓ Page 2 - Income Proof & Income Table")
print(f"  ✓ Page 3 - Benefits & Expenses (Auto Deductions, Housing, Utilities)")
print(f"  ✓ Page 4 - Expenses Continued (Transportation, Health, Personal, Household, Childcare, Other)")
print(f"  ✓ Page 4 - Assets (Real Estate, Vehicles)")
print(f"  ✓ Page 5 - Assets (Bank Accounts, Investments, Insurance, Other)")
print(f"  ✓ Page 6 - Debts & Summary of Assets/Liabilities")
print(f"  ✓ Page 7 - Schedule A & B (Additional Income & Other Income Earners)")
print(f"  ✓ Page 8 - Schedule C (Special/Extraordinary Expenses)")
print(f"\nFinancial Summary:")
print(f"  Monthly Income:        ${statement.income_total_monthly:>12}")
print(f"  Monthly Expenses:      ${statement.total_monthly_expenses:>12}")
print(f"  Monthly Surplus:       ${statement.income_total_monthly - statement.total_monthly_expenses:>12}")
print(f"  Annual Income:         ${statement.income_total_annual:>12}")
print(f"  Annual Expenses:       ${statement.total_yearly_expenses:>12}")
print(f"\nAsset Summary:")
print(f"  Total Assets:          ${statement.total_assets:>12}")
print(f"  Total Debts:           ${statement.total_debts:>12}")
print(f"  Net Worth:             ${statement.net_worth:>12}")
print(f"\nLawyer Info:")
print(f"  Applicant's Lawyer: {statement.applicant_lawyer_name}")
print(f"  Respondent's Lawyer: {statement.respondent_lawyer_name}")
print(f"="*60)
