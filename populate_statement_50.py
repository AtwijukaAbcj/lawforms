#!/usr/bin/env python
"""
PROPERLY populate statement #50 with all 8 pages of complete data
"""

import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_law.settings')
django.setup()

from forms.models import FinancialStatement

print("\n" + "="*80)
print("POPULATING STATEMENT #50 WITH COMPLETE DATA")
print("="*80)

statement = FinancialStatement.objects.get(pk=50)

# ========== PAGE 1 ==========
statement.court_name = "Ontario Superior Court of Justice"
statement.court_file_number = "FAM-2024-001234"
statement.applicant_name = "Sarah Johnson"
statement.my_name = "Sarah Johnson"
statement.sworn_affidavit = "I swear that the information provided is true"
statement.is_employed = True

# ========== PAGE 2 ==========
statement.pay_cheque_stub = True
statement.last_year_gross_income = Decimal('85000.00')
statement.income_employment = Decimal('7083.33')
statement.income_commissions = Decimal('0.00')
statement.income_investment = Decimal('125.00')
statement.income_tax_benefits = Decimal('200.00')
statement.income_total_monthly = Decimal('7408.33')
statement.income_total_annual = Decimal('88900.00')

# ========== PAGE 3 ==========
statement.benefit_item_1 = "Investment Income"
statement.benefit_value_1 = Decimal('125.00')
statement.benefit_item_2 = "Tax Benefits"
statement.benefit_value_2 = Decimal('200.00')
statement.cpp_contributions = Decimal('450.00')
statement.ei_premiums = Decimal('320.00')
statement.income_taxes = Decimal('1200.00')

# ========== PAGE 4 ==========
statement.rent_or_mortgage = Decimal('1800.00')
statement.property_taxes = Decimal('150.00')
statement.repairs_maintenance = Decimal('150.00')
statement.water = Decimal('50.00')
statement.heat = Decimal('80.00')
statement.electricity = Decimal('120.00')
statement.telephone = Decimal('50.00')
statement.cell_phone = Decimal('100.00')
statement.internet = Decimal('75.00')
statement.public_transit_taxis = Decimal('100.00')
statement.gas_oil = Decimal('300.00')
statement.car_insurance_license = Decimal('180.00')
statement.car_repairs_maintenance = Decimal('100.00')
statement.car_loan_lease_payments = Decimal('350.00')
statement.health_insurance_premiums = Decimal('100.00')
statement.dental_expenses = Decimal('50.00')
statement.medicine_drugs = Decimal('25.00')
statement.clothing = Decimal('150.00')
statement.hair_care_beauty = Decimal('50.00')
statement.education = Decimal('0.00')
statement.entertainment = Decimal('200.00')
statement.gifts = Decimal('100.00')
statement.groceries = Decimal('600.00')
statement.household_supplies = Decimal('75.00')
statement.meals_outside = Decimal('200.00')
statement.pet_care = Decimal('50.00')
statement.laundry_dry_cleaning = Decimal('30.00')
statement.daycare_expense = Decimal('0.00')
statement.life_insurance_premiums = Decimal('50.00')
statement.vacations = Decimal('200.00')
statement.debt_payments = Decimal('300.00')
statement.total_monthly_expenses = Decimal('6285.00')
statement.total_yearly_expenses = Decimal('75420.00')

# ========== PAGE 5 ==========
statement.real_estate = [
    {"details": "House in Toronto", "value": "650000"}
]
statement.vehicles = [
    {"details": "2019 Honda Accord", "value": "18000"}
]
statement.bank_accounts = [
    {"name_address_institution": "RBC Chequings", "account_number": "123456", "value": "5000"},
    {"name_address_institution": "TD Savings", "account_number": "987654", "value": "15000"}
]
statement.investments = [
    {"type_issuer_due_date_shares": "RRSP - Vanguard", "value": "85000"},
    {"type_issuer_due_date_shares": "TFSA - Dividend ETF", "value": "25000"}
]
statement.savings_plans = [
    {"type_issuer": "Employer Pension", "value": "120000"}
]
statement.total_value_all_property = Decimal('898000.00')

# ========== PAGE 6 ==========
statement.total_assets = Decimal('898000.00')
statement.debts = [
    {
        "type": "Mortgage",
        "creditor": "RBC",
        "full_amount": "450000",
        "monthly_payment": "2400",
        "payments_being_made": "Yes"
    },
    {
        "type": "Credit Card",
        "creditor": "Visa",
        "full_amount": "2500",
        "monthly_payment": "100",
        "payments_being_made": "Yes"
    }
]
statement.total_debts = Decimal('466700.00')
statement.net_worth = Decimal('431300.00')
statement.sworn_municipality = "Toronto"
statement.sworn_province_country = "Ontario"
statement.sworn_date = date.today()
statement.signature = "Sarah Johnson"

# ========== PAGE 7 ==========
statement.schedule_a_partnership_income = Decimal('0.00')
statement.has_children_in_home = False
statement.living_with_someone = True
statement.living_with_name = "Michael Johnson"
statement.spouse_does_not_work = True

# ========== PAGE 8 ==========
statement.schedule_c_total_annual = Decimal('0.00')
statement.schedule_c_total_monthly = Decimal('0.00')

# NOW SAVE EVERYTHING - save each section to be sure
print("\nDEBUG: Saving statement...")
print(f"  Before save - income_employment = {statement.income_employment}")
print(f"  Before save - groceries = {statement.groceries}")
print(f"  Before save - net_worth = {statement.net_worth}")

statement.save()
statement.refresh_from_db()

print(f"  After save - income_employment = {statement.income_employment}")
print(f"  After save - groceries = {statement.groceries}")
print(f"  After save - net_worth = {statement.net_worth}")

# Verify
print(f"\n✓ Statement #50 populated successfully!")
print(f"\nVERIFICATION:")
print(f"  Page 1: my_name = {statement.my_name}")
print(f"  Page 2: income_employment = {statement.income_employment}")
print(f"  Page 3: benefit_value_1 = {statement.benefit_value_1}")
print(f"  Page 4: groceries = {statement.groceries}")
print(f"  Page 5: real_estate = {statement.real_estate}")
print(f"  Page 5: total_value_all_property = {statement.total_value_all_property}")
print(f"  Page 6: net_worth = {statement.net_worth}")
print(f"  Page 7: has_children_in_home = {statement.has_children_in_home}")
print(f"  Page 8: schedule_c_total_annual = {statement.schedule_c_total_annual}")

print(f"\n" + "="*80)
print(f"✓✓✓ ALL DATA SAVED - Ready for UI testing!")
print(f"="*80 + "\n")
