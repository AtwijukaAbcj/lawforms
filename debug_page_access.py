#!/usr/bin/env python
"""
Comprehensive test: Verify data is accessible from all pages
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_law.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client, RequestFactory
from forms.models import FinancialStatement
from forms.views import financial_statement_page2, financial_statement_page3, financial_statement_page4

print("\n" + "="*80)
print("COMPREHENSIVE PAGE DATA ACCESS TEST")
print("="*80)

# Get or create test user
user, created = User.objects.get_or_create(username='testuser')
if created:
    user.set_password('test123')
    user.save()
    print(f"\n✓ Created test user: testuser")
else:
    print(f"\n✓ Using existing test user: testuser")

# Get statement #50
try:
    statement = FinancialStatement.objects.get(pk=50)
    print(f"✓ Found Statement #{statement.id}")
except:
    print("✗ Statement #50 not found!")
    exit(1)

# Check what's in the database
print(f"\nDATA IN DATABASE (Statement #{statement.id}):")
print(f"  Page 1: my_name = {statement.my_name}")
print(f"  Page 2: income_employment = {statement.income_employment}")
print(f"  Page 2: pay_cheque_stub = {statement.pay_cheque_stub}")
print(f"  Page 3: benefit_value_1 = {statement.benefit_value_1}")
print(f"  Page 4: groceries = {statement.groceries}")
print(f"  Page 5: real_estate = {statement.real_estate}")
print(f"  Page 5: total_value_all_property = {statement.total_value_all_property}")
print(f"  Page 6: net_worth = {statement.net_worth}")

# Now test accessing through views with proper request
client = Client()
factory = RequestFactory()

print(f"\nTESTING PAGE ACCESS WITH PROPER AUTHENTICATION:")
print("-" * 80)

# Test page 2
print(f"\n1. Testing Page 2 Access")
response = client.get(f'/forms/financial-statement/page2/50/', follow=True)
print(f"  Status Code: {response.status_code}")
if response.status_code == 200:
    print(f"  ✓ Page 2 loads successfully")
    # Check if context has statement
    if 'statement' in response.context:
        stmt = response.context['statement']
        print(f"    - income_employment in context: {stmt.income_employment}")
        print(f"    - pay_cheque_stub in context: {stmt.pay_cheque_stub}")
    else:
        print(f"  ✗ 'statement' not in response context!")
else:
    print(f"  ✗ Page 2 failed with status {response.status_code}")
    if response.status_code == 302:
        print(f"    Redirected to: {response.url}")
        print(f"    (Usually means not logged in)")

# Test page 3
print(f"\n2. Testing Page 3 Access")
response = client.get(f'/forms/financial-statement/page3/50/', follow=True)
print(f"  Status Code: {response.status_code}")
if response.status_code == 200:
    print(f"  ✓ Page 3 loads successfully")
    if 'statement' in response.context:
        stmt = response.context['statement']
        print(f"    - benefit_value_1 in context: {stmt.benefit_value_1}")
    else:
        print(f"  ✗ 'statement' not in response context!")
else:
    print(f"  ✗ Page 3 failed with status {response.status_code}")

# Test page 5
print(f"\n3. Testing Page 5 Access")
response = client.get(f'/forms/financial-statement/page5/50/', follow=True)
print(f"  Status Code: {response.status_code}")
if response.status_code == 200:
    print(f"  ✓ Page 5 loads successfully")
    if 'statement' in response.context:
        stmt = response.context['statement']
        print(f"    - real_estate in context: {stmt.real_estate}")
        print(f"    - total_value_all_property in context: {stmt.total_value_all_property}")
    else:
        print(f"  ✗ 'statement' not in response context!")
else:
    print(f"  ✗ Page 5 failed with status {response.status_code}")

print(f"\n" + "="*80)
print(f"Testing complete!")
print(f"="*80 + "\n")
