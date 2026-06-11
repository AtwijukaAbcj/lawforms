#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_law.settings')
django.setup()

from forms.models import FinancialStatement

statement = FinancialStatement.objects.get(pk=49)

print("\n" + "="*80)
print(f"Statement #{statement.id} - Data Verification")
print("="*80)

print("\nPAGE 1 FIELDS:")
print(f"  court_name: {statement.court_name}")
print(f"  my_name: {statement.my_name}")
print(f"  sworn_affidavit: {statement.sworn_affidavit}")

print("\nPAGE 2 FIELDS:")
print(f"  pay_cheque_stub: {statement.pay_cheque_stub}")
print(f"  last_year_gross_income: {statement.last_year_gross_income}")
print(f"  income_employment: {statement.income_employment}")
print(f"  income_total_monthly: {statement.income_total_monthly}")

print("\nPAGE 5 FIELDS:")
print(f"  real_estate: {statement.real_estate}")
print(f"  bank_accounts: {statement.bank_accounts}")
print(f"  total_value_all_property: {statement.total_value_all_property}")

print("\n" + "="*80)
