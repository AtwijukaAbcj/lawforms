"""
Script to populate a complete Financial Statement (Form 13) with test data.
Run with: python manage.py shell < populate_financial_statement.py
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

# Create a new Financial Statement with full test data
statement = FinancialStatement.objects.create(
    # Page 1 - Court and Party Information
    court_file_number="FC-2026-00123",
    court_name="Ontario Superior Court of Justice (Family Court)",
    court_office_address="393 University Avenue, Toronto, ON M5G 1E6",
    
    prepared_by="applicant",
    
    # Applicant Info
    applicant_name="John Michael Smith",
    applicant_address="123 Main Street, Unit 456, Toronto, ON M5V 2T6",
    applicant_phone="(416) 555-1234",
    applicant_fax="(416) 555-1235",
    applicant_email="john.smith@email.com",
    
    # Applicant Lawyer
    applicant_lawyer_name="Sarah Johnson, Barrister & Solicitor",
    applicant_lawyer_address="100 King Street West, Suite 1500, Toronto, ON M5X 1C7",
    applicant_lawyer_phone="(416) 555-9876",
    applicant_lawyer_fax="(416) 555-9877",
    applicant_lawyer_email="sjohnson@lawfirm.com",
    
    # Respondent Info
    respondent_name="Jane Elizabeth Smith",
    respondent_address="789 Oak Avenue, Apartment 12, Mississauga, ON L5B 3C4",
    respondent_phone="(905) 555-4321",
    respondent_fax="",
    respondent_email="jane.smith@email.com",
    
    # Respondent Lawyer
    respondent_lawyer_name="Michael Wong, Barrister & Solicitor",
    respondent_lawyer_address="200 Bay Street, Suite 2800, Toronto, ON M5J 2J1",
    respondent_lawyer_phone="(416) 555-5555",
    respondent_lawyer_fax="(416) 555-5556",
    respondent_lawyer_email="mwong@familylaw.ca",
    
    # Part 1 - My Information
    my_name="John Michael Smith",
    my_location="Toronto, Ontario",
    
    # Employment Status
    is_employed=True,
    employer_name_address="ABC Technology Inc., 500 Front Street West, Toronto, ON M5V 1B8",
    is_self_employed=False,
    business_name_address="",
    is_unemployed=False,
    unemployed_since=None,
    
    # Page 2 - Proof of Income
    pay_cheque_stub=True,
    social_assistance_stub=False,
    pension_stub=False,
    workers_comp_stub=False,
    ei_stub=False,
    statement_of_income=False,
    other_income_proof=True,
    
    last_year_gross_income=Decimal("98500.00"),
    
    indian_status=False,
    indian_status_docs="",
    
    # Income Table (Monthly amounts)
    income_employment=Decimal("7500.00"),
    income_commissions=Decimal("250.00"),
    income_self_employment_before_expenses=Decimal("0.00"),
    income_self_employment=Decimal("0.00"),
    income_ei=Decimal("0.00"),
    income_workers_comp=Decimal("0.00"),
    income_social_assistance=Decimal("0.00"),
    income_investment=Decimal("125.00"),
    income_pension=Decimal("0.00"),
    income_spousal_support=Decimal("0.00"),
    income_tax_benefits=Decimal("450.00"),
    income_other=Decimal("100.00"),
    income_total_monthly=Decimal("8425.00"),
    income_total_annual=Decimal("101100.00"),
    
    # Page 3 - Other Benefits (14)
    benefit_item_1="Health Insurance",
    benefit_details_1="Extended health and dental coverage through employer",
    benefit_value_1=Decimal("3600.00"),
    benefit_item_2="Company Vehicle",
    benefit_details_2="2024 Honda Accord for business and personal use",
    benefit_value_2=Decimal("4800.00"),
    benefit_item_3="RRSP Matching",
    benefit_details_3="Employer matches up to 5% of salary",
    benefit_value_3=Decimal("4500.00"),
    benefit_item_4="",
    benefit_details_4="",
    benefit_value_4=None,
    
    # Part 2 - Expenses (Monthly amounts)
    # Automatic Deductions
    cpp_contributions=Decimal("295.00"),
    ei_premiums=Decimal("75.00"),
    income_taxes=Decimal("1850.00"),
    employee_pension_contributions=Decimal("375.00"),
    union_dues=Decimal("0.00"),
    automatic_deductions_subtotal=Decimal("2595.00"),
    
    # Housing
    rent_or_mortgage=Decimal("2200.00"),
    property_taxes=Decimal("0.00"),
    property_insurance=Decimal("45.00"),
    condo_fees=Decimal("450.00"),
    repairs_maintenance=Decimal("50.00"),
    housing_subtotal=Decimal("2745.00"),
    
    # Utilities
    water=Decimal("0.00"),
    heat=Decimal("0.00"),
    electricity=Decimal("85.00"),
    telephone=Decimal("45.00"),
    cell_phone=Decimal("95.00"),
    cable=Decimal("65.00"),
    internet=Decimal("75.00"),
    utilities_subtotal=Decimal("365.00"),
    
    # Transportation
    public_transit_taxis=Decimal("156.00"),
    gas_oil=Decimal("180.00"),
    car_insurance_license=Decimal("185.00"),
    car_repairs_maintenance=Decimal("75.00"),
    parking=Decimal("200.00"),
    car_loan_lease_payments=Decimal("0.00"),
    transportation_subtotal=Decimal("796.00"),
    
    # Health
    health_insurance_premiums=Decimal("0.00"),
    dental_expenses=Decimal("25.00"),
    medicine_drugs=Decimal("45.00"),
    eye_care=Decimal("15.00"),
    health_subtotal=Decimal("85.00"),
    
    # Personal
    clothing=Decimal("150.00"),
    hair_care_beauty=Decimal("60.00"),
    alcohol_tobacco=Decimal("50.00"),
    education=Decimal("0.00"),
    entertainment=Decimal("200.00"),
    gifts=Decimal("75.00"),
    personal_subtotal=Decimal("535.00"),
    
    # Household Expenses
    groceries=Decimal("600.00"),
    household_supplies=Decimal("75.00"),
    meals_outside=Decimal("250.00"),
    pet_care=Decimal("85.00"),
    laundry_dry_cleaning=Decimal("40.00"),
    household_subtotal=Decimal("1050.00"),
    
    # Childcare Costs
    daycare_expense=Decimal("0.00"),
    babysitting_costs=Decimal("150.00"),
    childcare_subtotal=Decimal("150.00"),
    
    # Other expenses
    life_insurance_premiums=Decimal("95.00"),
    rrsp_resp_withdrawals=Decimal("0.00"),
    vacations=Decimal("250.00"),
    school_fees_supplies=Decimal("75.00"),
    clothing_for_children=Decimal("100.00"),
    children_activities=Decimal("200.00"),
    summer_camp_expenses=Decimal("85.00"),
    debt_payments=Decimal("350.00"),
    support_paid_for_other_children=Decimal("0.00"),
    other_expenses_specify="Gym membership, streaming services",
    other_expenses_amount=Decimal("120.00"),
    other_expenses_subtotal=Decimal("1275.00"),
    
    # Total expenses
    total_monthly_expenses=Decimal("9596.00"),
    total_yearly_expenses=Decimal("115152.00"),
    
    # Part 3 - Assets (JSON fields)
    real_estate=[
        {"description": "123 Main Street, Unit 456, Toronto, ON M5V 2T6 - Condominium (Joint Tenancy)", "value": "650000.00"},
        {"description": "Cottage - 45 Lakeshore Road, Muskoka, ON P1L 1A1 (Sole Owner)", "value": "425000.00"}
    ],
    
    vehicles=[
        {"description": "2022 BMW X5 xDrive40i", "value": "65000.00"},
        {"description": "2019 Honda Civic LX", "value": "18500.00"}
    ],
    
    other_possessions=[
        {"description": "Jewelry collection (wedding rings, watches)", "value": "15000.00"},
        {"description": "Electronics (computers, TV, audio equipment)", "value": "8500.00"},
        {"description": "Artwork and collectibles", "value": "12000.00"}
    ],
    
    investments=[
        {"description": "TD Direct Investing - Stock Portfolio - Various Canadian stocks", "value": "85000.00"},
        {"description": "RBC Mutual Funds - Balanced Growth Fund", "value": "45000.00"},
        {"description": "GIC - Scotiabank - Matures Dec 2026", "value": "25000.00"}
    ],
    
    bank_accounts=[
        {"description": "TD Canada Trust - Main Chequing - 1234567", "value": "12500.00"},
        {"description": "TD Canada Trust - Savings - 7654321", "value": "35000.00"},
        {"description": "RBC Royal Bank - Joint Account - 9876543", "value": "8500.00"}
    ],
    
    savings_plans=[
        {"description": "RRSP - TD Waterhouse - 123-456-789", "value": "185000.00"},
        {"description": "TFSA - RBC Direct Investing - 987-654-321", "value": "75000.00"},
        {"description": "RESP - RBC - For children Emma & Jack - 456-789-123", "value": "42000.00"}
    ],
    
    life_insurance=[
        {"description": "Sun Life - Term Life - Beneficiary: Jane Smith - $500,000 face", "value": "0.00"},
        {"description": "Manulife - Whole Life - Beneficiary: Children - $100,000 face", "value": "15000.00"}
    ],
    
    interest_in_business=[
        {"description": "Smith Consulting Inc. - 25% ownership - 100 Business Park Drive, Toronto", "value": "75000.00"}
    ],
    
    money_owed_to_you=[
        {"description": "Personal loan to brother - James Smith - 456 Oak St, Hamilton", "value": "5000.00"},
        {"description": "Income tax refund expected (2025)", "value": "2800.00"}
    ],
    
    other_assets=[
        {"description": "Air Miles and travel points (approximate value)", "value": "1500.00"},
        {"description": "Season tickets - Toronto Maple Leafs", "value": "8000.00"}
    ],
    
    total_value_all_property=Decimal("1914300.00"),
    
    # Part 4 - Debts (JSON field)
    debts=[
        {"type": "mortgage_loan", "creditor": "TD Canada Trust - Mortgage - 123 Main St, Toronto", "amount": "380000.00", "monthly": "1850.00", "payments_made": True},
        {"type": "mortgage_loan", "creditor": "Scotiabank - Line of Credit - #12345", "amount": "25000.00", "monthly": "350.00", "payments_made": True},
        {"type": "credit_card", "creditor": "Visa - TD - ending 4567", "amount": "4500.00", "monthly": "200.00", "payments_made": True},
        {"type": "credit_card", "creditor": "Mastercard - RBC - ending 8901", "amount": "2800.00", "monthly": "150.00", "payments_made": True},
        {"type": "other_debt", "creditor": "Car Loan - BMW Financial - 2022 BMW X5", "amount": "35000.00", "monthly": "650.00", "payments_made": True},
    ],
    
    total_debts_outstanding=Decimal("447300.00"),
    
    # Part 5 - Summary
    total_assets=Decimal("1914300.00"),
    total_debts=Decimal("447300.00"),
    net_worth=Decimal("1467000.00"),
    
    # Signature Section
    sworn_municipality="Toronto",
    sworn_province_country="Ontario, Canada",
    sworn_date=date(2026, 1, 28),
    commissioner_signature="",
    
    # Schedule A - Additional Sources of Income
    schedule_a_partnership_income=Decimal("0.00"),
    schedule_a_rental_income_gross=Decimal("0.00"),
    schedule_a_rental_income_net=Decimal("0.00"),
    schedule_a_dividends=Decimal("2400.00"),
    schedule_a_capital_gains=Decimal("5000.00"),
    schedule_a_capital_losses=Decimal("1200.00"),
    schedule_a_rrsp_withdrawals=Decimal("0.00"),
    schedule_a_rrif_annuity=Decimal("0.00"),
    schedule_a_other_income_source="Occasional freelance IT consulting",
    schedule_a_other_income_amount=Decimal("1200.00"),
    schedule_a_subtotal=Decimal("7400.00"),
    
    # Schedule B - Other Income Earners in the Home
    lives_alone=False,
    living_with_someone=False,
    living_with_name="",
    lives_with_other_adults=False,
    other_adults_names="",
    has_children_in_home=True,
    number_of_children_in_home=2,
    spouse_works=False,
    spouse_work_place="",
    spouse_does_not_work=False,
    spouse_earns_income=False,
    spouse_income_amount=None,
    spouse_income_period="",
    spouse_no_income=False,
    household_contribution=False,
    household_contribution_amount=None,
    household_contribution_period="",
    
    # Schedule C - Special Expenses for Children
    schedule_c_expenses=[
        {"child_name": "Emma Smith", "expense": "Private school tuition - Upper Canada College", "amount": "32000.00", "tax_credits": "0.00"},
        {"child_name": "Emma Smith", "expense": "Piano lessons and music equipment", "amount": "3600.00", "tax_credits": "500.00"},
        {"child_name": "Jack Smith", "expense": "Hockey registration, equipment, travel", "amount": "8500.00", "tax_credits": "500.00"},
        {"child_name": "Jack Smith", "expense": "Tutoring - math and science", "amount": "4800.00", "tax_credits": "0.00"},
        {"child_name": "Both children", "expense": "Summer camp - Camp Tamakwa", "amount": "12000.00", "tax_credits": "0.00"},
        {"child_name": "Both children", "expense": "Orthodontics - braces", "amount": "6500.00", "tax_credits": "0.00"},
    ],
    schedule_c_total_annual=Decimal("67400.00"),
    schedule_c_total_monthly=Decimal("5616.67"),
    schedule_c_my_income_for_share=Decimal("101100.00"),
)

print(f"✅ Created Financial Statement ID: {statement.pk}")
print(f"   Court File Number: {statement.court_file_number}")
print(f"   Applicant: {statement.applicant_name}")
print(f"   Net Worth: ${statement.net_worth:,.2f}")
print(f"\n   View at: http://127.0.0.1:8000/forms/financial-statement/{statement.pk}/print/")
