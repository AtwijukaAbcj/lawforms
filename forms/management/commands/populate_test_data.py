"""
Management command to populate test data for all form types.
Usage: python manage.py populate_test_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import date
from forms.models import (
    # Financial Statement
    FinancialStatement,
    # Net Family Property 13B
    NetFamilyProperty13B,
    NetFamilyProperty13BAsset,
    NetFamilyProperty13BDebt,
    NetFamilyProperty13BMarriageProperty,
    NetFamilyProperty13BMarriageDebt,
    NetFamilyProperty13BExcluded,
    NetFamilyProperty13BFinalTotals,
    # Comparison NFP
    ComparisonNetFamilyProperty,
    ComparisonNetFamilyPropertyHouseholdItem,
    ComparisonNetFamilyPropertyBankAccount,
    ComparisonNetFamilyPropertyInsurance,
    ComparisonNetFamilyPropertyBusiness,
    # Form 13C
    Form13CComparison,
    Form13CAsset,
    Form13CMoneyOwed,
    Form13COtherProperty,
    Form13CDebtLiability,
    Form13CMarriageProperty,
    Form13CExcludedProperty,
    Form13CFinalTotals,
)


class Command(BaseCommand):
    help = 'Populate the database with test data for all form types'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...\n')
        
        # Create Financial Statement
        self.create_financial_statement()
        
        # Create Net Family Property 13B
        self.create_net_family_property_13b()
        
        # Create Comparison NFP with Form 13C
        self.create_comparison_nfp()
        
        self.stdout.write(self.style.SUCCESS('\nTest data created successfully!'))

    def create_financial_statement(self):
        self.stdout.write('Creating Financial Statement...')
        
        fs = FinancialStatement.objects.create(
            # Court Info
            court_file_number='FC-2026-12345',
            court_name='Ontario Superior Court of Justice (Family Court)',
            court_office_address='161 Elgin Street, Ottawa, ON K2P 2K1',
            prepared_by='applicant',
            
            # Applicant Info
            applicant_name='John Michael Smith',
            applicant_address='123 Maple Street, Unit 5\nOttawa, ON K1A 0A1',
            applicant_phone='(613) 555-1234',
            applicant_fax='(613) 555-1235',
            applicant_email='john.smith@email.com',
            
            # Applicant Lawyer
            applicant_lawyer_name='Sarah Johnson, Barrister & Solicitor',
            applicant_lawyer_address='500 Bank Street, Suite 200\nOttawa, ON K1S 3S8',
            applicant_lawyer_phone='(613) 555-9876',
            applicant_lawyer_fax='(613) 555-9877',
            applicant_lawyer_email='sjohnson@lawfirm.ca',
            
            # Respondent Info
            respondent_name='Mary Elizabeth Smith',
            respondent_address='456 Oak Avenue\nOttawa, ON K1N 6N5',
            respondent_phone='(613) 555-4321',
            respondent_fax='(613) 555-4322',
            respondent_email='mary.smith@email.com',
            
            # Respondent Lawyer
            respondent_lawyer_name='Robert Chen, Barrister & Solicitor',
            respondent_lawyer_address='100 Queen Street, Suite 400\nOttawa, ON K1P 1J9',
            respondent_lawyer_phone='(613) 555-6789',
            respondent_lawyer_fax='(613) 555-6780',
            respondent_lawyer_email='rchen@familylaw.ca',
            
            # Dates
            valuation_date=date(2025, 6, 15),
            statement_date=date(2026, 1, 28),
            
            # Part 1 - Income (Page 1)
            my_name='John Michael Smith',
            my_location='Ottawa, Ontario',
            is_employed=True,
            employer_name_address='Tech Solutions Inc.\n200 Laurier Ave W, Ottawa, ON K1P 5V5',
            is_self_employed=False,
            is_unemployed=False,
            
            # Page 2 - Proof of income
            pay_cheque_stub=True,
            social_assistance_stub=False,
            pension_stub=False,
            workers_comp_stub=False,
            ei_stub=False,
            statement_of_income=True,
            other_income_proof=False,
            last_year_gross_income=Decimal('95000.00'),
            indian_status=False,
            
            # Page 2 - Income table (monthly)
            income_employment=Decimal('6500.00'),
            income_commissions=Decimal('500.00'),
            income_self_employment_before_expenses=Decimal('0.00'),
            income_self_employment=Decimal('0.00'),
            income_ei=Decimal('0.00'),
            income_workers_comp=Decimal('0.00'),
            income_social_assistance=Decimal('0.00'),
            income_investment=Decimal('150.00'),
            income_pension=Decimal('0.00'),
            income_spousal_support=Decimal('0.00'),
            income_tax_benefits=Decimal('350.00'),
            income_other=Decimal('0.00'),
            income_total_monthly=Decimal('7500.00'),
            income_total_annual=Decimal('90000.00'),
            
            # Page 3 - Other Benefits
            benefit_item_1='Company Health Insurance',
            benefit_details_1='Extended health and dental coverage for family',
            benefit_value_1=Decimal('4800.00'),
            benefit_item_2='Company Car',
            benefit_details_2='2023 Honda Accord for business and personal use',
            benefit_value_2=Decimal('6000.00'),
            benefit_item_3='RRSP Matching',
            benefit_details_3='Employer matches 5% of salary',
            benefit_value_3=Decimal('4750.00'),
            benefit_item_4='',
            benefit_details_4='',
            benefit_value_4=None,
            
            # Automatic Deductions
            cpp_contributions=Decimal('320.00'),
            ei_premiums=Decimal('85.00'),
            income_taxes=Decimal('1800.00'),
            employee_pension_contributions=Decimal('325.00'),
            union_dues=Decimal('0.00'),
            automatic_deductions_subtotal=Decimal('2530.00'),
            
            # Housing
            rent_or_mortgage=Decimal('1800.00'),
            property_taxes=Decimal('350.00'),
            property_insurance=Decimal('120.00'),
            condo_fees=Decimal('0.00'),
            repairs_maintenance=Decimal('100.00'),
            housing_subtotal=Decimal('2370.00'),
            
            # Utilities
            water=Decimal('45.00'),
            heat=Decimal('120.00'),
            electricity=Decimal('95.00'),
            telephone=Decimal('55.00'),
            cell_phone=Decimal('85.00'),
            cable=Decimal('65.00'),
            internet=Decimal('75.00'),
            utilities_subtotal=Decimal('540.00'),
            
            # Transportation
            public_transit_taxis=Decimal('50.00'),
            gas_oil=Decimal('200.00'),
            car_insurance_license=Decimal('180.00'),
            car_repairs_maintenance=Decimal('75.00'),
            parking=Decimal('150.00'),
            car_loan_lease_payments=Decimal('450.00'),
            transportation_subtotal=Decimal('1105.00'),
            
            # Health
            health_insurance_premiums=Decimal('0.00'),
            dental_expenses=Decimal('50.00'),
            medicine_drugs=Decimal('40.00'),
            eye_care=Decimal('25.00'),
            health_subtotal=Decimal('115.00'),
            
            # Personal
            clothing=Decimal('150.00'),
            hair_care_beauty=Decimal('50.00'),
            alcohol_tobacco=Decimal('60.00'),
            education=Decimal('0.00'),
            entertainment=Decimal('200.00'),
            gifts=Decimal('75.00'),
            personal_subtotal=Decimal('535.00'),
            
            # Household
            groceries=Decimal('600.00'),
            household_supplies=Decimal('100.00'),
            meals_outside=Decimal('250.00'),
            pet_care=Decimal('75.00'),
            laundry_dry_cleaning=Decimal('40.00'),
            household_subtotal=Decimal('1065.00'),
            
            # Childcare
            daycare_expense=Decimal('800.00'),
            babysitting_costs=Decimal('100.00'),
            childcare_subtotal=Decimal('900.00'),
            
            # Other expenses
            life_insurance_premiums=Decimal('85.00'),
            rrsp_resp_withdrawals=Decimal('0.00'),
            vacations=Decimal('200.00'),
            school_fees_supplies=Decimal('50.00'),
            clothing_for_children=Decimal('100.00'),
            children_activities=Decimal('150.00'),
            summer_camp_expenses=Decimal('50.00'),
            debt_payments=Decimal('200.00'),
            support_paid_for_other_children=Decimal('0.00'),
            other_expenses_specify='Pet insurance',
            other_expenses_amount=Decimal('45.00'),
            other_expenses_subtotal=Decimal('880.00'),
            
            # Total expenses
            total_monthly_expenses=Decimal('10040.00'),
            total_yearly_expenses=Decimal('120480.00'),
            
            # Part 3 - Assets (Page 4-5)
            real_estate=[
                {'address': '123 Maple Street, Ottawa, ON K1A 0A1', 'value': '450000.00'},
                {'address': 'Cottage at 789 Lake Road, Bancroft, ON', 'value': '180000.00'},
            ],
            vehicles=[
                {'year_make': '2021 Toyota RAV4', 'value': '32000.00'},
                {'year_make': '2019 Honda Civic', 'value': '18000.00'},
            ],
            other_possessions=[
                {'description': 'Furniture and appliances', 'value': '25000.00'},
                {'description': 'Electronics (computers, TVs)', 'value': '8000.00'},
                {'description': 'Jewelry collection', 'value': '12000.00'},
            ],
            investments=[
                {'type_issuer_due_date_shares': 'TD Bank GIC - matures Dec 2026', 'value': '25000.00'},
                {'type_issuer_due_date_shares': 'RBC Mutual Funds', 'value': '45000.00'},
            ],
            bank_accounts=[
                {'name_address': 'TD Bank, 150 Bank St Ottawa', 'account_number': '1234567', 'value': '15000.00'},
                {'name_address': 'RBC, 200 Sparks St Ottawa', 'account_number': '8765432', 'value': '8500.00'},
                {'name_address': 'Tangerine Savings', 'account_number': '555-1234', 'value': '22000.00'},
            ],
            savings_plans=[
                {'type_issuer': 'RRSP - TD Waterhouse', 'account_number': 'RR-12345', 'value': '125000.00'},
                {'type_issuer': 'RESP for children - RBC', 'account_number': 'RE-67890', 'value': '35000.00'},
                {'type_issuer': 'TFSA - Tangerine', 'account_number': 'TF-11111', 'value': '45000.00'},
            ],
            life_insurance=[
                {'type_beneficiary_face_amount': 'Term Life - Spouse - $500,000', 'cash_surrender_value': '0.00'},
                {'type_beneficiary_face_amount': 'Whole Life - Children - $100,000', 'cash_surrender_value': '15000.00'},
            ],
            interest_in_business=[],
            money_owed_to_you=[
                {'name_address': 'Brother - James Smith', 'value': '5000.00'},
            ],
            other_assets=[
                {'description': 'Art collection', 'value': '8000.00'},
            ],
            total_value_all_property=Decimal('1073500.00'),
            
            # Part 4 - Debts (Page 6)
            debts=[
                {'type': 'Mortgage', 'creditor': 'TD Bank', 'full_amount': '280000.00', 'monthly_payment': '1800.00', 'payments_being_made': 'yes'},
                {'type': 'Car Loan', 'creditor': 'Honda Financial', 'full_amount': '18000.00', 'monthly_payment': '450.00', 'payments_being_made': 'yes'},
                {'type': 'Line of Credit', 'creditor': 'RBC', 'full_amount': '15000.00', 'monthly_payment': '200.00', 'payments_being_made': 'yes'},
                {'type': 'Credit Card', 'creditor': 'VISA TD', 'full_amount': '3500.00', 'monthly_payment': '150.00', 'payments_being_made': 'yes'},
            ],
            total_debts_outstanding=Decimal('316500.00'),
            
            # Part 5 - Summary
            total_assets=Decimal('1073500.00'),
            total_debts=Decimal('316500.00'),
            net_worth=Decimal('757000.00'),
            
            # Signature section
            sworn_municipality='Ottawa',
            sworn_province_country='Ontario, Canada',
            sworn_date=date(2026, 1, 28),
            commissioner_signature='Commissioner John Doe',
            
            # Schedule A - Additional Income
            schedule_a_partnership_income=Decimal('0.00'),
            schedule_a_rental_income_gross=Decimal('0.00'),
            schedule_a_rental_income_net=Decimal('0.00'),
            schedule_a_dividends=Decimal('350.00'),
            schedule_a_capital_gains=Decimal('1200.00'),
            schedule_a_capital_losses=Decimal('0.00'),
            schedule_a_rrsp_withdrawals=Decimal('0.00'),
            schedule_a_rrif_annuity=Decimal('0.00'),
            schedule_a_other_income_source='Stock dividends from employer shares',
            schedule_a_other_income_amount=Decimal('800.00'),
            schedule_a_subtotal=Decimal('2350.00'),
            
            # Schedule B - Other Income Earners
            lives_alone=False,
            living_with_someone=True,
            living_with_name='',
            lives_with_other_adults=False,
            other_adults_names='',
            has_children_in_home=True,
            number_of_children_in_home=2,
            spouse_works=False,
            spouse_work_place='',
            spouse_does_not_work=True,
            spouse_earns_income=False,
            spouse_income_amount=None,
            spouse_income_period='',
            spouse_no_income=True,
            household_contribution=False,
            household_contribution_amount=None,
            household_contribution_period='',
            
            # Schedule C - Children Expenses
            schedule_c_expenses=[
                {'child_name': 'Emma Smith', 'expense': 'Private School Tuition', 'amount_per_year': '15000.00', 'tax_credits': '0.00'},
                {'child_name': 'Emma Smith', 'expense': 'Piano Lessons', 'amount_per_year': '2400.00', 'tax_credits': '500.00'},
                {'child_name': 'Lucas Smith', 'expense': 'Hockey League Fees', 'amount_per_year': '3600.00', 'tax_credits': '500.00'},
                {'child_name': 'Lucas Smith', 'expense': 'Summer Camp', 'amount_per_year': '2500.00', 'tax_credits': '0.00'},
                {'child_name': 'Both Children', 'expense': 'Orthodontics', 'amount_per_year': '4800.00', 'tax_credits': '1200.00'},
            ],
            schedule_c_total_annual=Decimal('28300.00'),
            schedule_c_total_monthly=Decimal('2358.33'),
            schedule_c_my_income_for_share=Decimal('95000.00'),
        )
        
        self.stdout.write(self.style.SUCCESS(f'  Created Financial Statement #{fs.pk}'))

    def create_net_family_property_13b(self):
        self.stdout.write('Creating Net Family Property 13B...')
        
        nfp = NetFamilyProperty13B.objects.create(
            court_file_number='FC-2026-54321',
            court_name='Ontario Superior Court of Justice (Family Court)',
            court_address='161 Elgin Street, Ottawa, ON K2P 2K1',
            
            applicant_name='Jennifer Anne Williams',
            applicant_address='789 Pine Street\nOttawa, ON K1S 2T4',
            applicant_phone='(613) 555-2222',
            applicant_email='jennifer.williams@email.com',
            
            applicant_lawyer_name='Michelle Lee, Family Law Specialist',
            applicant_lawyer_address='300 Slater Street, Suite 100\nOttawa, ON K1P 5H9',
            applicant_lawyer_phone='(613) 555-3333',
            applicant_lawyer_email='mlee@ottawalaw.ca',
            
            respondent_name='David Robert Williams',
            respondent_address='456 Cedar Lane\nOttawa, ON K1N 8H2',
            respondent_phone='(613) 555-4444',
            respondent_email='david.williams@email.com',
            
            respondent_lawyer_name='Thomas Brown, Barrister',
            respondent_lawyer_address='150 Metcalfe Street, Suite 800\nOttawa, ON K2P 1P1',
            respondent_lawyer_phone='(613) 555-5555',
            respondent_lawyer_email='tbrown@familylegal.ca',
            
            my_name='Jennifer Anne Williams',
            valuation_date=date(2025, 9, 1),
        )
        
        # Create Assets
        assets_data = [
            ('Matrimonial Home - 789 Pine St, Ottawa', Decimal('525000.00'), Decimal('525000.00')),
            ('2022 BMW X5', Decimal('55000.00'), Decimal('55000.00')),
            ('2020 Mercedes C300', Decimal('38000.00'), Decimal('38000.00')),
            ('RRSP - TD Wealth Management', Decimal('185000.00'), Decimal('0.00')),
            ('RRSP - RBC Direct Investing', Decimal('0.00'), Decimal('145000.00')),
            ('TFSA - Scotiabank', Decimal('65000.00'), Decimal('0.00')),
            ('TFSA - BMO', Decimal('0.00'), Decimal('58000.00')),
            ('Joint Bank Account - TD', Decimal('12500.00'), Decimal('12500.00')),
            ('Personal Savings - CIBC', Decimal('35000.00'), Decimal('0.00')),
            ('Personal Savings - RBC', Decimal('0.00'), Decimal('42000.00')),
            ('Investment Portfolio - Edward Jones', Decimal('95000.00'), Decimal('0.00')),
            ('Cottage - Lake Muskoka', Decimal('320000.00'), Decimal('320000.00')),
            ('Furniture & Household Items', Decimal('45000.00'), Decimal('45000.00')),
            ('Jewelry & Watches', Decimal('18000.00'), Decimal('8000.00')),
            ('Art Collection', Decimal('25000.00'), Decimal('25000.00')),
        ]
        for item, app_val, resp_val in assets_data:
            NetFamilyProperty13BAsset.objects.create(
                statement=nfp, item=item, applicant_value=app_val, respondent_value=resp_val
            )
        
        # Create Debts
        debts_data = [
            ('Mortgage - 789 Pine St', Decimal('225000.00'), Decimal('225000.00')),
            ('Mortgage - Cottage', Decimal('85000.00'), Decimal('85000.00')),
            ('BMW Financing', Decimal('28000.00'), Decimal('28000.00')),
            ('Mercedes Financing', Decimal('15000.00'), Decimal('15000.00')),
            ('Line of Credit - TD', Decimal('18000.00'), Decimal('18000.00')),
            ('VISA - RBC', Decimal('5500.00'), Decimal('0.00')),
            ('MasterCard - BMO', Decimal('0.00'), Decimal('7200.00')),
        ]
        for item, app_val, resp_val in debts_data:
            NetFamilyProperty13BDebt.objects.create(
                statement=nfp, item=item, applicant_value=app_val, respondent_value=resp_val
            )
        
        # Create Marriage Property
        marriage_props = [
            ('Wedding Gifts - Cash', Decimal('15000.00'), Decimal('15000.00')),
            ('Wedding Gifts - Items', Decimal('8000.00'), Decimal('8000.00')),
            ('Inheritance from Grandmother (Wife)', Decimal('50000.00'), Decimal('0.00')),
        ]
        for item, app_val, resp_val in marriage_props:
            NetFamilyProperty13BMarriageProperty.objects.create(
                statement=nfp, item=item, applicant_value=app_val, respondent_value=resp_val
            )
        
        # Create Marriage Debts
        marriage_debts = [
            ('Student Loan (Wife) at marriage', Decimal('12000.00'), Decimal('0.00')),
            ('Car Loan (Husband) at marriage', Decimal('0.00'), Decimal('8500.00')),
        ]
        for item, app_val, resp_val in marriage_debts:
            NetFamilyProperty13BMarriageDebt.objects.create(
                statement=nfp, item=item, applicant_value=app_val, respondent_value=resp_val
            )
        
        # Create Excluded Properties
        excluded = [
            ('Inheritance - Grandmother (received during marriage)', Decimal('75000.00'), Decimal('0.00')),
            ('Gift from parents (Husband)', Decimal('0.00'), Decimal('25000.00')),
            ('Personal injury settlement (Wife)', Decimal('35000.00'), Decimal('0.00')),
        ]
        for item, app_val, resp_val in excluded:
            NetFamilyProperty13BExcluded.objects.create(
                statement=nfp, item=item, applicant_value=app_val, respondent_value=resp_val
            )
        
        # Create Final Totals
        NetFamilyProperty13BFinalTotals.objects.create(
            statement=nfp,
            total1=Decimal('1418500.00'),  # Total Assets
            total2=Decimal('376700.00'),   # Total Debts
            total3=Decimal('60500.00'),    # Net Property at Marriage (Assets - Debts)
            total4=Decimal('110000.00'),   # Excluded Property
            total5=Decimal('871300.00'),   # NFP Calculation
            total6=Decimal('435650.00'),   # Equalization Amount
            date_of_signature=date(2026, 1, 28),
            signature='Jennifer Anne Williams',
        )
        
        self.stdout.write(self.style.SUCCESS(f'  Created Net Family Property 13B #{nfp.pk}'))

    def create_comparison_nfp(self):
        self.stdout.write('Creating Comparison NFP with Form 13C...')
        
        # Create parent Comparison NFP
        comp = ComparisonNetFamilyProperty.objects.create(
            court_file_number='FC-2026-99999',
            court_name='Ontario Superior Court of Justice (Family Court)',
            court_office_address='161 Elgin Street, Ottawa, ON K2P 2K1',
            prepared_by='joint',
            
            applicant_name='Michael James Thompson',
            applicant_address='100 Wellington Street, Ottawa, ON K1A 0A2',
            applicant_phone='(613) 555-7777',
            applicant_email='m.thompson@email.com',
            applicant_lawyer_name='Patricia Wong, QC',
            applicant_lawyer_address='50 O\'Connor Street, Suite 1500, Ottawa, ON K1P 6L2',
            applicant_lawyer_phone='(613) 555-8888',
            applicant_lawyer_email='pwong@wonglaw.ca',
            
            respondent_name='Susan Marie Thompson',
            respondent_address='200 Rideau Street, Unit 10, Ottawa, ON K1N 5Y1',
            respondent_phone='(613) 555-9999',
            respondent_email='s.thompson@email.com',
            respondent_lawyer_name='Kevin O\'Brien',
            respondent_lawyer_address='75 Albert Street, Suite 900, Ottawa, ON K1P 5E7',
            respondent_lawyer_phone='(613) 555-1111',
            respondent_lawyer_email='kobrien@obrienlaw.ca',
            
            valuation_date=date(2025, 12, 1),
            statement_date=date(2026, 1, 28),
        )
        
        # Create Page 2 items - Household Items
        household_items = [
            ('Living Room Furniture', 'Sofa set, coffee tables, entertainment center', 'Purchased together 2020', 'D1', 
             Decimal('8500.00'), Decimal('8500.00'), Decimal('7000.00'), Decimal('7000.00')),
            ('Bedroom Furniture', 'King bed, dressers, nightstands', 'Master bedroom set', 'D2',
             Decimal('6000.00'), Decimal('6000.00'), Decimal('5500.00'), Decimal('5500.00')),
            ('Kitchen Appliances', 'Refrigerator, stove, dishwasher', 'Stainless steel set', 'D3',
             Decimal('4500.00'), Decimal('4500.00'), Decimal('4000.00'), Decimal('4000.00')),
            ('Electronics', 'TVs, sound system, computers', 'Various purchases', 'D4',
             Decimal('5000.00'), Decimal('3000.00'), Decimal('4000.00'), Decimal('2500.00')),
            ('Dining Room Set', 'Table, 8 chairs, china cabinet', 'Antique inherited by wife', 'D5',
             Decimal('12000.00'), Decimal('0.00'), Decimal('0.00'), Decimal('12000.00')),
        ]
        for item, desc, comments, doc, app_app, app_resp, resp_app, resp_resp in household_items:
            ComparisonNetFamilyPropertyHouseholdItem.objects.create(
                parent=comp, item=item, description=desc, comments=comments, document_number=doc,
                applicant_position_applicant=app_app, applicant_position_respondent=app_resp,
                respondent_position_applicant=resp_app, respondent_position_respondent=resp_resp
            )
        
        # Bank Accounts
        bank_accounts = [
            ('Chequing', 'RBC Royal Bank', '12345-678', 'Joint account', 'D6',
             Decimal('15000.00'), Decimal('15000.00'), Decimal('15000.00'), Decimal('15000.00')),
            ('Savings', 'TD Canada Trust', '98765-432', 'Husband personal', 'D7',
             Decimal('45000.00'), Decimal('0.00'), Decimal('45000.00'), Decimal('0.00')),
            ('Savings', 'Scotiabank', '55555-111', 'Wife personal', 'D8',
             Decimal('0.00'), Decimal('38000.00'), Decimal('0.00'), Decimal('38000.00')),
        ]
        for cat, inst, acc, comments, doc, app_app, app_resp, resp_app, resp_resp in bank_accounts:
            ComparisonNetFamilyPropertyBankAccount.objects.create(
                parent=comp, category=cat, institution=inst, account_number=acc,
                comments=comments, document_number=doc,
                applicant_position_applicant=app_app, applicant_position_respondent=app_resp,
                respondent_position_applicant=resp_app, respondent_position_respondent=resp_resp
            )
        
        # Insurance
        insurances = [
            ('Sun Life Policy #123456', 'Husband', 'Wife', Decimal('500000.00'), 'Term life', 'D9',
             Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00')),
            ('Manulife Whole Life #789', 'Wife', 'Children', Decimal('250000.00'), 'Cash value policy', 'D10',
             Decimal('0.00'), Decimal('25000.00'), Decimal('0.00'), Decimal('25000.00')),
        ]
        for policy, owner, bene, face, comments, doc, app_app, app_resp, resp_app, resp_resp in insurances:
            ComparisonNetFamilyPropertyInsurance.objects.create(
                parent=comp, company_policy=policy, owner=owner, beneficiary=bene,
                face_amount=face, comments=comments, document_number=doc,
                applicant_position_applicant=app_app, applicant_position_respondent=app_resp,
                respondent_position_applicant=resp_app, respondent_position_respondent=resp_resp
            )
        
        # Businesses
        businesses = [
            ('Thompson Consulting Inc.', '100% shares owned by husband', 'Incorporated 2018', 'D11',
             Decimal('150000.00'), Decimal('0.00'), Decimal('125000.00'), Decimal('0.00')),
        ]
        for firm, interests, comments, doc, app_app, app_resp, resp_app, resp_resp in businesses:
            ComparisonNetFamilyPropertyBusiness.objects.create(
                parent=comp, firm_name=firm, interests=interests, comments=comments, document_number=doc,
                applicant_position_applicant=app_app, applicant_position_respondent=app_resp,
                respondent_position_applicant=resp_app, respondent_position_respondent=resp_resp
            )
        
        # Create Form 13C linked to this comparison
        form13c = Form13CComparison.objects.create(
            parent=comp,
            court_file_number=comp.court_file_number,
            court_name=comp.court_name,
            court_office_address=comp.court_office_address,
            prepared_by=comp.prepared_by,
            applicant_name=comp.applicant_name,
            applicant_address=comp.applicant_address,
            applicant_phone=comp.applicant_phone,
            applicant_email=comp.applicant_email,
            applicant_lawyer_name=comp.applicant_lawyer_name,
            applicant_lawyer_address=comp.applicant_lawyer_address,
            applicant_lawyer_phone=comp.applicant_lawyer_phone,
            applicant_lawyer_email=comp.applicant_lawyer_email,
            respondent_name=comp.respondent_name,
            respondent_address=comp.respondent_address,
            respondent_phone=comp.respondent_phone,
            respondent_email=comp.respondent_email,
            respondent_lawyer_name=comp.respondent_lawyer_name,
            respondent_lawyer_address=comp.respondent_lawyer_address,
            respondent_lawyer_phone=comp.respondent_lawyer_phone,
            respondent_lawyer_email=comp.respondent_lawyer_email,
            valuation_date=comp.valuation_date,
            statement_date=comp.statement_date,
        )
        
        # Page 3 - Assets
        assets = [
            ('Matrimonial Home', '100 Wellington Street, Ottawa', 'Purchased 2015', 'D12',
             Decimal('650000.00'), Decimal('650000.00'), Decimal('650000.00'), Decimal('650000.00')),
            ('Vacation Property', 'Cottage at 500 Lake Road, Muskoka', 'Purchased 2019', 'D13',
             Decimal('380000.00'), Decimal('380000.00'), Decimal('350000.00'), Decimal('350000.00')),
            ('Investment Property', '25 Rental Ave, Unit 5', 'Rental income property', 'D14',
             Decimal('425000.00'), Decimal('0.00'), Decimal('425000.00'), Decimal('0.00')),
        ]
        for nature, addr, comments, doc, app_app, app_resp, resp_app, resp_resp in assets:
            Form13CAsset.objects.create(
                form13c=form13c, nature_type_of_ownership=nature, nature_address_of_ownership=addr,
                comments=comments, document_number=doc,
                applicant_position_applicant=app_app, applicant_position_respondent=app_resp,
                respondent_position_applicant=resp_app, respondent_position_respondent=resp_resp
            )
        
        # Money Owed
        money_owed = [
            ('Loan to brother - John Thompson', 'Lent in 2023, due 2026', 'D15',
             Decimal('20000.00'), Decimal('0.00'), Decimal('20000.00'), Decimal('0.00')),
            ('Security deposit - Rental property', 'Held by tenant', 'D16',
             Decimal('2500.00'), Decimal('0.00'), Decimal('2500.00'), Decimal('0.00')),
        ]
        for details, comments, doc, app_app, app_resp, resp_app, resp_resp in money_owed:
            Form13CMoneyOwed.objects.create(
                form13c=form13c, details=details, comments=comments, document_number=doc,
                applicant_position_applicant=app_app, applicant_position_respondent=app_resp,
                respondent_position_applicant=resp_app, respondent_position_respondent=resp_resp
            )
        
        # Other Property
        other_props = [
            ('Vehicles', '2023 Tesla Model Y', 'Husband primary vehicle', 'D17',
             Decimal('58000.00'), Decimal('0.00'), Decimal('55000.00'), Decimal('0.00')),
            ('Vehicles', '2022 Audi Q5', 'Wife primary vehicle', 'D18',
             Decimal('0.00'), Decimal('48000.00'), Decimal('0.00'), Decimal('46000.00')),
            ('RRSP', 'Husband RRSP - Fidelity', 'Retirement savings', 'D19',
             Decimal('225000.00'), Decimal('0.00'), Decimal('225000.00'), Decimal('0.00')),
            ('RRSP', 'Wife RRSP - Manulife', 'Retirement savings', 'D20',
             Decimal('0.00'), Decimal('185000.00'), Decimal('0.00'), Decimal('185000.00')),
        ]
        for cat, details, comments, doc, app_app, app_resp, resp_app, resp_resp in other_props:
            Form13COtherProperty.objects.create(
                form13c=form13c, category=cat, details=details, comments=comments, document_number=doc,
                applicant_position_applicant=app_app, applicant_position_respondent=app_resp,
                respondent_position_applicant=resp_app, respondent_position_respondent=resp_resp
            )
        
        # Debts/Liabilities
        debts = [
            ('Mortgage', 'Matrimonial Home - RBC', 'Principal balance', 'D21',
             Decimal('320000.00'), Decimal('320000.00'), Decimal('320000.00'), Decimal('320000.00')),
            ('Mortgage', 'Cottage - TD', 'Principal balance', 'D22',
             Decimal('125000.00'), Decimal('125000.00'), Decimal('125000.00'), Decimal('125000.00')),
            ('Line of Credit', 'CIBC LOC', 'Home renovation loan', 'D23',
             Decimal('45000.00'), Decimal('45000.00'), Decimal('45000.00'), Decimal('45000.00')),
            ('Car Loan', 'Tesla Financing', 'Husband vehicle', 'D24',
             Decimal('28000.00'), Decimal('0.00'), Decimal('28000.00'), Decimal('0.00')),
            ('Credit Card', 'AMEX Platinum', 'Joint card', 'D25',
             Decimal('8500.00'), Decimal('8500.00'), Decimal('8500.00'), Decimal('8500.00')),
        ]
        for cat, details, comments, doc, app_app, app_resp, resp_app, resp_resp in debts:
            Form13CDebtLiability.objects.create(
                form13c=form13c, category=cat, details=details, comments=comments, document_number=doc,
                applicant_position_applicant=app_app, applicant_position_respondent=app_resp,
                respondent_position_applicant=resp_app, respondent_position_respondent=resp_resp
            )
        
        # Page 4 - Marriage Property
        marriage_props = [
            ('Cash wedding gifts', 'Received at wedding 2012', 'D26',
             Decimal('12000.00'), Decimal('12000.00'), Decimal('12000.00'), Decimal('12000.00')),
            ('Household items from wedding', 'Gifts from family', 'D27',
             Decimal('5000.00'), Decimal('5000.00'), Decimal('5000.00'), Decimal('5000.00')),
            ('Wife inheritance (received before marriage)', 'From grandmother', 'D28',
             Decimal('0.00'), Decimal('45000.00'), Decimal('0.00'), Decimal('45000.00')),
        ]
        for details, comments, doc, app_app, app_resp, resp_app, resp_resp in marriage_props:
            Form13CMarriageProperty.objects.create(
                form13c=form13c, category_details=details, comments=comments, document_number=doc,
                applicant_position_applicant=app_app, applicant_position_respondent=app_resp,
                respondent_position_applicant=resp_app, respondent_position_respondent=resp_resp,
                is_debt=False
            )
        
        # Marriage Debts
        marriage_debts = [
            ('Husband student loan at marriage', 'Law school debt', 'D29',
             Decimal('35000.00'), Decimal('0.00'), Decimal('35000.00'), Decimal('0.00')),
            ('Wife car loan at marriage', 'Previous vehicle', 'D30',
             Decimal('0.00'), Decimal('8000.00'), Decimal('0.00'), Decimal('8000.00')),
        ]
        for details, comments, doc, app_app, app_resp, resp_app, resp_resp in marriage_debts:
            Form13CMarriageProperty.objects.create(
                form13c=form13c, category_details=details, comments=comments, document_number=doc,
                applicant_position_applicant=app_app, applicant_position_respondent=app_resp,
                respondent_position_applicant=resp_app, respondent_position_respondent=resp_resp,
                is_debt=True
            )
        
        # Excluded Property
        excluded = [
            ('Inheritance during marriage - Husband', 'From father 2020', 'D31',
             Decimal('75000.00'), Decimal('0.00'), Decimal('75000.00'), Decimal('0.00')),
            ('Inheritance during marriage - Wife', 'From aunt 2022', 'D32',
             Decimal('0.00'), Decimal('55000.00'), Decimal('0.00'), Decimal('55000.00')),
            ('Personal injury settlement - Husband', 'Car accident 2021', 'D33',
             Decimal('42000.00'), Decimal('0.00'), Decimal('42000.00'), Decimal('0.00')),
            ('Gift from wife\'s parents', 'Down payment help 2015', 'D34',
             Decimal('0.00'), Decimal('50000.00'), Decimal('0.00'), Decimal('50000.00')),
        ]
        for item, comments, doc, app_app, app_resp, resp_app, resp_resp in excluded:
            Form13CExcludedProperty.objects.create(
                form13c=form13c, item=item, comments=comments, document_number=doc,
                applicant_position_applicant=app_app, applicant_position_respondent=app_resp,
                respondent_position_applicant=resp_app, respondent_position_respondent=resp_resp
            )
        
        # Page 5 - Final Totals
        Form13CFinalTotals.objects.create(
            form13c=form13c,
            total1_valuation_date=Decimal('2150000.00'),
            total2_debts_liabilities=Decimal('526500.00'),
            total3_property_on_marriage=Decimal('62000.00'),
            total4_excluded_property=Decimal('222000.00'),
            total5_sum=Decimal('810500.00'),
            total6_net_family_property=Decimal('1339500.00'),
            applicant_pays_to_respondent_app=Decimal('0.00'),
            respondent_pays_to_applicant_app=Decimal('125750.00'),
            applicant_pays_to_respondent_resp=Decimal('0.00'),
            respondent_pays_to_applicant_resp=Decimal('98500.00'),
        )
        
        self.stdout.write(self.style.SUCCESS(f'  Created Comparison NFP #{comp.pk} with Form 13C #{form13c.pk}'))
