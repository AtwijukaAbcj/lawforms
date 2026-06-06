# forms/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal


# ============================================================
# SOFT DELETE MIXIN - For Recycle Bin Functionality
# ============================================================
class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted objects by default."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Manager that includes all objects (including soft-deleted)."""
    pass


class DeletedObjectsManager(models.Manager):
    """Manager that only returns soft-deleted objects."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=True)


class SoftDeleteMixin(models.Model):
    """Mixin that adds soft delete functionality to models."""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()
    deleted_objects = DeletedObjectsManager()
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Mark the object as deleted."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore the soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()
    
    def hard_delete(self):
        """Permanently delete the object."""
        super().delete()


# ============================================================
# 1) SIMPLE FORM: NetFamilyPropertyStatement (Standalone Root)
# ============================================================
class NetFamilyPropertyStatement(models.Model):
    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_office_address = models.CharField(max_length=255, blank=True, null=True)
    case_file = models.ForeignKey(
        'CaseFile',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='net_family_property_statements'
    )

    prepared_by = models.CharField(
        max_length=50,
        choices=[
            ("applicant", "Applicant"),
            ("respondent", "Respondent"),
            ("joint", "Joint"),
        ],
        blank=True,
        null=True,
    )

    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_address = models.TextField(blank=True, null=True)
    applicant_phone = models.CharField(max_length=30, blank=True, null=True)
    applicant_email = models.EmailField(blank=True, null=True)

    applicant_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_address = models.TextField(blank=True, null=True)
    applicant_lawyer_phone = models.CharField(max_length=30, blank=True, null=True)
    applicant_lawyer_email = models.EmailField(blank=True, null=True)

    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_address = models.TextField(blank=True, null=True)
    respondent_phone = models.CharField(max_length=30, blank=True, null=True)
    respondent_email = models.EmailField(blank=True, null=True)

    respondent_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_address = models.TextField(blank=True, null=True)
    respondent_lawyer_phone = models.CharField(max_length=30, blank=True, null=True)
    respondent_lawyer_email = models.EmailField(blank=True, null=True)

    valuation_date = models.DateField(blank=True, null=True)
    statement_date = models.DateField(blank=True, null=True)
    draft = models.JSONField(blank=True, null=True)
    draft = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"Net Family Property Statement: {self.court_file_number or self.id}"


class NetFamilyPropertyAsset(models.Model):
    statement = models.ForeignKey(
        NetFamilyPropertyStatement,
        related_name="assets",
        on_delete=models.CASCADE,
        db_index=True,
    )
    item = models.CharField(max_length=255, blank=True, null=True)
    applicant_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Asset: {self.item or self.id} (Statement {self.statement_id})"


# ============================================================
# Shared Case/Client master record
# ============================================================
class CaseFile(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='case_files')
    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_office_address = models.TextField(blank=True, null=True)

    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_address = models.TextField(blank=True, null=True)
    applicant_phone = models.CharField(max_length=100, blank=True, null=True)
    applicant_email = models.EmailField(blank=True, null=True)

    applicant_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_address = models.TextField(blank=True, null=True)
    applicant_lawyer_phone = models.CharField(max_length=100, blank=True, null=True)
    applicant_lawyer_email = models.EmailField(blank=True, null=True)

    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_address = models.TextField(blank=True, null=True)
    respondent_phone = models.CharField(max_length=100, blank=True, null=True)
    respondent_email = models.EmailField(blank=True, null=True)

    respondent_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_address = models.TextField(blank=True, null=True)
    respondent_lawyer_phone = models.CharField(max_length=100, blank=True, null=True)
    respondent_lawyer_email = models.EmailField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    valuation_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"Case: {self.court_file_number or self.applicant_name or self.id}"


# ============================================================
# 2) SIMPLE FORM: FinancialStatement (Standalone Root)
# ============================================================
class FinancialStatement(SoftDeleteMixin, models.Model):
    # Draft field for storing extra dynamic data
    draft = models.JSONField(blank=True, null=True)
    
    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_office_address = models.CharField(max_length=255, blank=True, null=True)
    case_file = models.ForeignKey(
        'CaseFile',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='financial_statements'
    )

    prepared_by = models.CharField(
        max_length=50,
        choices=[
            ("applicant", "Applicant"),
            ("respondent", "Respondent"),
            ("joint", "Joint"),
        ],
        blank=True,
        null=True,
    )

    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_address = models.TextField(blank=True, null=True)
    applicant_phone = models.CharField(max_length=30, blank=True, null=True)
    applicant_fax = models.CharField(max_length=30, blank=True, null=True)
    applicant_email = models.EmailField(blank=True, null=True)

    applicant_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_address = models.TextField(blank=True, null=True)
    applicant_lawyer_phone = models.CharField(max_length=30, blank=True, null=True)
    applicant_lawyer_fax = models.CharField(max_length=30, blank=True, null=True)
    applicant_lawyer_email = models.EmailField(blank=True, null=True)

    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_address = models.TextField(blank=True, null=True)
    respondent_phone = models.CharField(max_length=30, blank=True, null=True)
    respondent_fax = models.CharField(max_length=30, blank=True, null=True)
    respondent_email = models.EmailField(blank=True, null=True)

    respondent_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_address = models.TextField(blank=True, null=True)
    respondent_lawyer_phone = models.CharField(max_length=30, blank=True, null=True)
    respondent_lawyer_fax = models.CharField(max_length=30, blank=True, null=True)
    respondent_lawyer_email = models.EmailField(blank=True, null=True)

    valuation_date = models.DateField(blank=True, null=True)
    statement_date = models.DateField(blank=True, null=True)

    # Part 1 - Income fields (Page 1)
    my_name = models.CharField(max_length=255, blank=True, null=True)
    my_location = models.CharField(max_length=255, blank=True, null=True)
    
    # Employment status (checkboxes)
    is_employed = models.BooleanField(default=False)
    employer_name_address = models.TextField(blank=True, null=True)
    
    is_self_employed = models.BooleanField(default=False)
    business_name_address = models.TextField(blank=True, null=True)
    
    is_unemployed = models.BooleanField(default=False)
    unemployed_since = models.DateField(blank=True, null=True)

    # Page 2 - Proof of income checkboxes
    pay_cheque_stub = models.BooleanField(default=False)
    social_assistance_stub = models.BooleanField(default=False)
    pension_stub = models.BooleanField(default=False)
    workers_comp_stub = models.BooleanField(default=False)
    ei_stub = models.BooleanField(default=False)
    statement_of_income = models.BooleanField(default=False)
    other_income_proof = models.BooleanField(default=False)
    
    # Page 2 - Last year gross income
    last_year_gross_income = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Page 2 - Indian status option
    indian_status = models.BooleanField(default=False)
    indian_status_docs = models.TextField(blank=True, null=True)
    
    # Page 2 - Income table (monthly amounts)
    income_employment = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_commissions = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_self_employment_before_expenses = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_self_employment = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_ei = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_workers_comp = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_social_assistance = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_investment = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_pension = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_spousal_support = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_tax_benefits = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_other = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_total_monthly = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_total_annual = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # Page 3 - Other Benefits (14)
    benefit_item_1 = models.CharField(max_length=255, blank=True, null=True)
    benefit_details_1 = models.TextField(blank=True, null=True)
    benefit_value_1 = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    benefit_item_2 = models.CharField(max_length=255, blank=True, null=True)
    benefit_details_2 = models.TextField(blank=True, null=True)
    benefit_value_2 = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    benefit_item_3 = models.CharField(max_length=255, blank=True, null=True)
    benefit_details_3 = models.TextField(blank=True, null=True)
    benefit_value_3 = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    benefit_item_4 = models.CharField(max_length=255, blank=True, null=True)
    benefit_details_4 = models.TextField(blank=True, null=True)
    benefit_value_4 = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # Part 2 - Expenses (Pages 3-4) - All monthly amounts
    # Automatic Deductions
    cpp_contributions = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    ei_premiums = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    income_taxes = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    employee_pension_contributions = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    union_dues = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    automatic_deductions_subtotal = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Housing
    rent_or_mortgage = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    property_taxes = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    property_insurance = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    condo_fees = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    repairs_maintenance = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    housing_subtotal = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Utilities
    water = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    heat = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    electricity = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    telephone = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    cell_phone = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    cable = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    internet = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    utilities_subtotal = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Transportation
    public_transit_taxis = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    gas_oil = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    car_insurance_license = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    car_repairs_maintenance = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    parking = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    car_loan_lease_payments = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    transportation_subtotal = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Health
    health_insurance_premiums = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    dental_expenses = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    medicine_drugs = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    eye_care = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    health_subtotal = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Personal
    clothing = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    hair_care_beauty = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    alcohol_tobacco = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    education = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    entertainment = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    gifts = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    personal_subtotal = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Household Expenses
    groceries = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    household_supplies = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    meals_outside = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    pet_care = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    laundry_dry_cleaning = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    household_subtotal = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Childcare Costs
    daycare_expense = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    babysitting_costs = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    childcare_subtotal = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Other expenses
    life_insurance_premiums = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    rrsp_resp_withdrawals = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    vacations = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    school_fees_supplies = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    clothing_for_children = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    children_activities = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    summer_camp_expenses = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    debt_payments = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    support_paid_for_other_children = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    other_expenses_specify = models.TextField(blank=True, null=True)
    other_expenses_amount = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    other_expenses_subtotal = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Total expenses
    total_monthly_expenses = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total_yearly_expenses = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # Part 3 - Assets (Pages 4-5) - JSON fields for variable number of entries
    real_estate = models.JSONField(blank=True, null=True)  # list of {address, value}
    vehicles = models.JSONField(blank=True, null=True)  # list of {year_make, value}
    other_possessions = models.JSONField(blank=True, null=True)  # list of {address_where_located, value}
    investments = models.JSONField(blank=True, null=True)  # list of {type_issuer_due_date_shares, value}
    bank_accounts = models.JSONField(blank=True, null=True)  # list of {name_address_institution, account_number, value}
    savings_plans = models.JSONField(blank=True, null=True)  # list of {type_issuer, account_number, value}
    life_insurance = models.JSONField(blank=True, null=True)  # list of {type_beneficiary_face_amount, cash_surrender_value}
    interest_in_business = models.JSONField(blank=True, null=True)  # list of {name_address_of_business, value}
    money_owed_to_you = models.JSONField(blank=True, null=True)  # list of {name_address_of_debtors, value}
    other_assets = models.JSONField(blank=True, null=True)  # list of {description, value}
    total_value_all_property = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # Part 4 - Debts (Page 6) - JSON field for variable number of entries
    debts = models.JSONField(blank=True, null=True)  # list of {type, creditor, full_amount, monthly_payment, payments_being_made}
    total_debts_outstanding = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Part 5 - Summary of Assets and Liabilities
    total_assets = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total_debts = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    net_worth = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    
    # Signature section (Page 6)
    sworn_municipality = models.CharField(max_length=255, blank=True, null=True)
    sworn_province_country = models.CharField(max_length=255, blank=True, null=True)
    sworn_date = models.DateField(blank=True, null=True)
    commissioner_signature = models.CharField(max_length=255, blank=True, null=True)

    # Schedule A - Additional Sources of Income (Page 7)
    schedule_a_partnership_income = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    schedule_a_rental_income_gross = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    schedule_a_rental_income_net = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    schedule_a_dividends = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    schedule_a_capital_gains = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    schedule_a_capital_losses = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    schedule_a_rrsp_withdrawals = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    schedule_a_rrif_annuity = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    schedule_a_other_income_source = models.TextField(blank=True, null=True)
    schedule_a_other_income_amount = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    schedule_a_subtotal = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # Schedule B - Other Income Earners in the Home (Page 7)
    lives_alone = models.BooleanField(default=False)
    
    living_with_someone = models.BooleanField(default=False)
    living_with_name = models.CharField(max_length=255, blank=True, null=True)
    
    lives_with_other_adults = models.BooleanField(default=False)
    other_adults_names = models.TextField(blank=True, null=True)
    
    has_children_in_home = models.BooleanField(default=False)
    number_of_children_in_home = models.IntegerField(blank=True, null=True)
    
    spouse_works = models.BooleanField(default=False)
    spouse_work_place = models.CharField(max_length=255, blank=True, null=True)
    spouse_does_not_work = models.BooleanField(default=False)
    
    spouse_earns_income = models.BooleanField(default=False)
    spouse_income_amount = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    spouse_income_period = models.CharField(max_length=50, blank=True, null=True)
    spouse_no_income = models.BooleanField(default=False)
    
    household_contribution = models.BooleanField(default=False)
    household_contribution_amount = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    household_contribution_period = models.CharField(max_length=100, blank=True, null=True)

    # Schedule C - Special or Extraordinary Expenses for Children (Page 8)
    schedule_c_expenses = models.JSONField(blank=True, null=True)  # list of {child_name, expense, amount_per_year, tax_credits}
    schedule_c_total_annual = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    schedule_c_total_monthly = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    schedule_c_my_income_for_share = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"Financial Statement: {self.court_file_number or self.id}"


# ============================================================
# 3) FORM 13B (Multi-page Root + Child Tables + Totals)
# ============================================================
class NetFamilyProperty13B(SoftDeleteMixin, models.Model):
    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_address = models.CharField(max_length=255, blank=True, null=True)
    case_file = models.ForeignKey(
        'CaseFile',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='net_family_property_13b_forms'
    )

    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_address = models.TextField(blank=True, null=True)
    applicant_phone = models.CharField(max_length=100, blank=True, null=True)
    applicant_email = models.EmailField(blank=True, null=True)

    applicant_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_address = models.TextField(blank=True, null=True)
    applicant_lawyer_phone = models.CharField(max_length=100, blank=True, null=True)
    applicant_lawyer_email = models.EmailField(blank=True, null=True)

    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_address = models.TextField(blank=True, null=True)
    respondent_phone = models.CharField(max_length=100, blank=True, null=True)
    respondent_email = models.EmailField(blank=True, null=True)

    respondent_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_address = models.TextField(blank=True, null=True)
    respondent_lawyer_phone = models.CharField(max_length=100, blank=True, null=True)
    respondent_lawyer_email = models.EmailField(blank=True, null=True)

    my_name = models.CharField(max_length=255, blank=True, null=True)
    valuation_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"13B Net Family Property: {self.court_file_number or self.id}"


class NetFamilyProperty13BAsset(models.Model):
    statement = models.ForeignKey(NetFamilyProperty13B, related_name="assets", on_delete=models.CASCADE, db_index=True)
    item = models.CharField(max_length=255, blank=True, null=True)
    applicant_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13B Asset: {self.item or self.id}"


class NetFamilyProperty13BDebt(models.Model):
    statement = models.ForeignKey(NetFamilyProperty13B, related_name="debts", on_delete=models.CASCADE, db_index=True)
    item = models.CharField(max_length=255, blank=True, null=True)
    applicant_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13B Debt: {self.item or self.id}"


class NetFamilyProperty13BMarriageProperty(models.Model):
    statement = models.ForeignKey(NetFamilyProperty13B, related_name="marriage_properties", on_delete=models.CASCADE)
    item = models.CharField(max_length=255, blank=True, null=True)  # ✅ item (NOT property_item)
    applicant_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13B Marriage Property: {self.item or self.id}"


class NetFamilyProperty13BMarriageDebt(models.Model):
    statement = models.ForeignKey(NetFamilyProperty13B, related_name="marriage_debts", on_delete=models.CASCADE)
    item = models.CharField(max_length=255, blank=True, null=True)  # ✅ item (NOT debt_item)
    applicant_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13B Marriage Debt: {self.item or self.id}"


class NetFamilyProperty13BExcluded(models.Model):
    statement = models.ForeignKey(
        NetFamilyProperty13B,
        related_name="excluded_properties",
        on_delete=models.CASCADE,
        db_index=True,
    )
    item = models.CharField(max_length=255, blank=True, null=True)
    applicant_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13B Excluded: {self.item or self.id}"


class NetFamilyProperty13BFinalTotals(models.Model):
    statement = models.OneToOneField(
        NetFamilyProperty13B,
        related_name="final_totals",
        on_delete=models.CASCADE
    )

    total1 = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total2 = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total3 = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total4 = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total5 = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total6 = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # NEW FIELD
    equalisation_note = models.TextField(blank=True, null=True)

    date_of_signature = models.DateField(blank=True, null=True)
    signature = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13B Final Totals for Statement {self.statement_id}"


# ============================================================
# 4) COMPARISON (Page 1 & Page 2 parent models)
# ============================================================
class ComparisonNetFamilyProperty(SoftDeleteMixin, models.Model):
    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_office_address = models.CharField(max_length=255, blank=True, null=True)
    case_file = models.ForeignKey(
        'CaseFile',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='comparison_net_family_properties'
    )

    prepared_by = models.CharField(
        max_length=50,
        choices=[
            ("applicant", "Applicant"),
            ("respondent", "Respondent"),
            ("joint", "Applicant and Respondent jointly"),
        ],
        blank=True,
        null=True,
    )

    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_address = models.CharField(max_length=255, blank=True, null=True)
    applicant_phone = models.CharField(max_length=100, blank=True, null=True)
    applicant_email = models.EmailField(blank=True, null=True)
    applicant_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_address = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_phone = models.CharField(max_length=100, blank=True, null=True)
    applicant_lawyer_email = models.EmailField(blank=True, null=True)

    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_address = models.CharField(max_length=255, blank=True, null=True)
    respondent_phone = models.CharField(max_length=100, blank=True, null=True)
    respondent_email = models.EmailField(blank=True, null=True)
    respondent_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_address = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_phone = models.CharField(max_length=100, blank=True, null=True)
    respondent_lawyer_email = models.EmailField(blank=True, null=True)

    valuation_date = models.DateField(blank=True, null=True)
    statement_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"Comparison NFP: {self.court_file_number or self.id}"


class AffidavitOfService(SoftDeleteMixin, models.Model):
    FORM_VARIANT_6B = "form_6b"
    FORM_VARIANT_8A = "form_8a"

    FORM_VARIANT_CHOICES = [
        (FORM_VARIANT_6B, "Form 6B"),
        (FORM_VARIANT_8A, "Form 8A"),
    ]

    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    court_office_address = models.CharField(max_length=255, blank=True, null=True)
    court_phone_number = models.CharField(max_length=50, blank=True, null=True)

    form_variant = models.CharField(
        max_length=20,
        choices=FORM_VARIANT_CHOICES,
        default=FORM_VARIANT_6B,
    )

    case_file = models.ForeignKey(
        "CaseFile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="affidavits_of_service",
    )

    plaintiff_name = models.CharField(max_length=255, blank=True, null=True)
    defendant_name = models.CharField(max_length=255, blank=True, null=True)

    affiant_name = models.CharField(max_length=255, blank=True, null=True)
    affiant_address = models.CharField(max_length=255, blank=True, null=True)
    server_name = models.CharField(max_length=255, blank=True, null=True)
    server_city = models.CharField(max_length=255, blank=True, null=True)

    served_name = models.CharField(max_length=255, blank=True, null=True)
    served_date = models.DateField(blank=True, null=True)
    served_at_address = models.CharField(max_length=512, blank=True, null=True)
    served_address_type = models.CharField(max_length=255, blank=True, null=True)
    documents_served = models.TextField(blank=True, null=True)

    address_person_home = models.BooleanField(default=False)
    address_corporation_business = models.BooleanField(default=False)
    address_representative_on_record = models.BooleanField(default=False)
    address_recent_document = models.BooleanField(default=False)
    address_corporation_attorney = models.BooleanField(default=False)
    address_other = models.BooleanField(default=False)
    address_other_details = models.CharField(max_length=255, blank=True, null=True)

    personal_service_person = models.BooleanField(default=False)
    personal_service_corporation_officer = models.BooleanField(default=False)
    personal_service_corporation_officer_position = models.CharField(max_length=255, blank=True, null=True)
    personal_service_other_person = models.BooleanField(default=False)
    personal_service_other_person_details = models.CharField(max_length=255, blank=True, null=True)

    service_place_residence = models.BooleanField(default=False)
    service_place_residence_regular_mail = models.BooleanField(default=False)
    service_place_residence_registered_mail = models.BooleanField(default=False)
    service_place_residence_courier = models.BooleanField(default=False)
    service_registered_mail = models.BooleanField(default=False)
    service_courier = models.BooleanField(default=False)
    service_lawyer_or_paralegal = models.BooleanField(default=False)
    service_regular_lettermail = models.BooleanField(default=False)
    service_by_fax = models.BooleanField(default=False)
    service_fax_time = models.CharField(max_length=50, blank=True, null=True)
    service_fax_number = models.CharField(max_length=50, blank=True, null=True)

    service_to_corporation = models.BooleanField(default=False)
    corporation_director_name = models.CharField(max_length=255, blank=True, null=True)
    corporation_director_address = models.CharField(max_length=512, blank=True, null=True)

    substituted_service = models.BooleanField(default=False)
    substituted_service_order_date = models.DateField(blank=True, null=True)
    substituted_service_details = models.TextField(blank=True, null=True)
    # Page 1 — Official Form 6B party/lawyer service boxes
    applicant_lawyer_details = models.TextField(blank=True, null=True)
    respondent_lawyer_details = models.TextField(blank=True, null=True)

    # Page 1 — Time served
    served_time = models.TimeField(blank=True, null=True)

    # Page 1 — Document table
    document_1_name = models.CharField(max_length=255, blank=True, null=True)
    document_1_author = models.CharField(max_length=255, blank=True, null=True)
    document_1_date = models.DateField(blank=True, null=True)

    document_2_name = models.CharField(max_length=255, blank=True, null=True)
    document_2_author = models.CharField(max_length=255, blank=True, null=True)
    document_2_date = models.DateField(blank=True, null=True)

    document_3_name = models.CharField(max_length=255, blank=True, null=True)
    document_3_author = models.CharField(max_length=255, blank=True, null=True)
    document_3_date = models.DateField(blank=True, null=True)

    document_4_name = models.CharField(max_length=255, blank=True, null=True)
    document_4_author = models.CharField(max_length=255, blank=True, null=True)
    document_4_date = models.DateField(blank=True, null=True)

    document_5_name = models.CharField(max_length=255, blank=True, null=True)
    document_5_author = models.CharField(max_length=255, blank=True, null=True)
    document_5_date = models.DateField(blank=True, null=True)

    # Page 1 — Main service method checkboxes
    service_special = models.BooleanField(default=False)
    service_mail = models.BooleanField(default=False)
    service_same_day_courier = models.BooleanField(default=False)
    service_next_day_courier = models.BooleanField(default=False)
    service_document_exchange = models.BooleanField(default=False)
    service_electronic_document_exchange = models.BooleanField(default=False)
    service_fax = models.BooleanField(default=False)
    service_email = models.BooleanField(default=False)
    service_substituted = models.BooleanField(default=False)

    # Page 2 — Special Service
    special_service_place = models.CharField(max_length=255, blank=True, null=True)
    special_service_left_with_person = models.BooleanField(default=False)
    special_service_left_with_named_person = models.BooleanField(default=False)
    special_service_named_person = models.CharField(max_length=255, blank=True, null=True)
    special_service_accepted_in_writing = models.BooleanField(default=False)
    special_service_lawyer_of_record = models.BooleanField(default=False)
    special_service_officer_position = models.BooleanField(default=False)
    special_service_officer_position_details = models.CharField(max_length=255, blank=True, null=True)
    special_service_corporation_named = models.BooleanField(default=False)
    special_service_prepaid_return_postcard = models.BooleanField(default=False)
    special_service_sealed_envelope_residence = models.BooleanField(default=False)
    special_service_adult_resident_name = models.CharField(max_length=255, blank=True, null=True)
    special_service_other = models.BooleanField(default=False)
    special_service_other_details = models.TextField(blank=True, null=True)

    # Page 2 — Mail Service
    mail_service_address = models.TextField(blank=True, null=True)
    mail_address_place_of_business = models.BooleanField(default=False)
    mail_address_lawyer_accepted = models.BooleanField(default=False)
    mail_address_lawyer_record = models.BooleanField(default=False)
    mail_address_home = models.BooleanField(default=False)
    mail_address_recent_document = models.BooleanField(default=False)
    mail_address_other = models.BooleanField(default=False)
    mail_address_other_details = models.CharField(max_length=255, blank=True, null=True)

    # Page 2 — Courier Service
    courier_pickup_time = models.TimeField(blank=True, null=True)
    courier_pickup_date = models.DateField(blank=True, null=True)
    courier_service_name = models.CharField(max_length=255, blank=True, null=True)
    courier_service_address = models.TextField(blank=True, null=True)
    courier_address_place_of_business = models.BooleanField(default=False)
    courier_address_lawyer_accepted = models.BooleanField(default=False)
    courier_address_lawyer_record = models.BooleanField(default=False)
    courier_address_home = models.BooleanField(default=False)
    courier_address_recent_document = models.BooleanField(default=False)
    courier_address_other = models.BooleanField(default=False)
    courier_address_other_details = models.CharField(max_length=255, blank=True, null=True)

    # Page 3 — Electronic / Alternative Service
    document_exchange_service = models.BooleanField(default=False)
    document_exchange_details = models.TextField(blank=True, null=True)
    electronic_document_exchange_service = models.BooleanField(default=False)
    electronic_document_exchange_details = models.TextField(blank=True, null=True)
    fax_service = models.BooleanField(default=False)
    fax_service_details = models.TextField(blank=True, null=True)
    email_service = models.BooleanField(default=False)
    email_service_details = models.TextField(blank=True, null=True)

    # Page 3 — Court Order Service
    service_order_date = models.DateField(blank=True, null=True)
    service_order_substituted_service = models.BooleanField(default=False)
    service_order_advertisement = models.BooleanField(default=False)
    service_order_details = models.TextField(blank=True, null=True)

    relationship_to_party = models.TextField(blank=True, null=True)
    is_at_least_18 = models.BooleanField(default=False)
    kilometres_travelled = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    service_fee = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    travel_fee = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    commissioner_municipality = models.CharField(max_length=255, blank=True, null=True)
    commissioner_province = models.CharField(max_length=255, blank=True, null=True)
    sworn_date = models.DateField(blank=True, null=True)
    commissioner_name = models.CharField(max_length=255, blank=True, null=True)
    signature = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]


# ============================================================
# FORM 36B — CERTIFICATE OF DIVORCE (SINGLE PAGE)
# ============================================================
class CertificateOfDivorce(SoftDeleteMixin, models.Model):
    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    court_office_address = models.CharField(max_length=255, blank=True, null=True)
    case_file = models.ForeignKey(
        'CaseFile', on_delete=models.SET_NULL, blank=True, null=True,
        related_name='certificates_of_divorce'
    )

    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_address = models.TextField(blank=True, null=True)
    applicant_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_address = models.TextField(blank=True, null=True)

    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_address = models.TextField(blank=True, null=True)
    respondent_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_address = models.TextField(blank=True, null=True)

    marriage_place = models.CharField(max_length=255, blank=True, null=True)
    marriage_date = models.DateField(blank=True, null=True)

    divorce_order_date = models.DateField(blank=True, null=True)
    divorce_effective_date = models.DateField(blank=True, null=True)

    date_of_signature = models.DateField(blank=True, null=True)
    clerk_signature = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"Certificate of Divorce: {self.court_file_number or self.id}"


class DivorceOrder(SoftDeleteMixin, models.Model):
    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    court_office_address = models.CharField(max_length=255, blank=True, null=True)

    case_file = models.ForeignKey(
        'CaseFile',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='divorce_orders'
    )

    judge_name = models.CharField(max_length=255, blank=True, null=True)
    judge_title = models.CharField(max_length=255, blank=True, null=True)

    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_address = models.TextField(blank=True, null=True)
    applicant_phone = models.CharField(max_length=100, blank=True, null=True)
    applicant_email = models.EmailField(blank=True, null=True)

    applicant_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_address = models.TextField(blank=True, null=True)
    applicant_lawyer_phone = models.CharField(max_length=100, blank=True, null=True)
    applicant_lawyer_email = models.EmailField(blank=True, null=True)

    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_address = models.TextField(blank=True, null=True)
    respondent_phone = models.CharField(max_length=100, blank=True, null=True)
    respondent_email = models.EmailField(blank=True, null=True)

    respondent_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_address = models.TextField(blank=True, null=True)
    respondent_lawyer_phone = models.CharField(max_length=100, blank=True, null=True)
    respondent_lawyer_email = models.EmailField(blank=True, null=True)

    application_of_name = models.CharField(max_length=255, blank=True, null=True)
    persons_in_court = models.TextField(blank=True, null=True)
    evidence_submissions = models.TextField(blank=True, null=True)

    marriage_place = models.CharField(max_length=255, blank=True, null=True)
    marriage_date = models.DateField(blank=True, null=True)
    divorce_effective_days = models.PositiveIntegerField(default=31, blank=True, null=True)
    other_relief_details = models.TextField(blank=True, null=True)

    date_of_order = models.DateField(blank=True, null=True)
    date_of_signature = models.DateField(blank=True, null=True)
    judge_or_clerk_signature = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"Divorce Order (Form 25A): {self.court_file_number or self.id}"
    
class DivorceOrderA25A(SoftDeleteMixin, models.Model):
    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    court_office_address = models.CharField(max_length=255, blank=True, null=True)
    case_file = models.ForeignKey(
        'CaseFile', on_delete=models.SET_NULL, blank=True, null=True,
        related_name='divorce_order_a25as'
    )

    judge_name = models.CharField(max_length=255, blank=True, null=True)
    judge_title = models.CharField(max_length=255, blank=True, null=True)

    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_address = models.TextField(blank=True, null=True)
    applicant_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_address = models.TextField(blank=True, null=True)

    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_address = models.TextField(blank=True, null=True)
    respondent_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_address = models.TextField(blank=True, null=True)

    application_of_name = models.CharField(max_length=255, blank=True, null=True)
    persons_in_court = models.TextField(blank=True, null=True)
    evidence_submissions = models.TextField(blank=True, null=True)

    marriage_place = models.CharField(max_length=255, blank=True, null=True)
    marriage_date = models.DateField(blank=True, null=True)
    divorce_effective_days = models.PositiveIntegerField(default=31, blank=True, null=True)
    other_relief_details = models.TextField(blank=True, null=True)

    date_of_order = models.DateField(blank=True, null=True)
    date_of_signature = models.DateField(blank=True, null=True)
    judge_or_clerk_signature = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"Divorce Order (Form A-25A): {self.court_file_number or self.id}"


class ComparisonNetFamilyPropertyHouseholdItem(models.Model):
    parent = models.ForeignKey(ComparisonNetFamilyProperty, on_delete=models.CASCADE, related_name="household_items")
    item = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    document_number = models.CharField(max_length=100, blank=True)

    # These 4 fields match the form columns (Applicant/Respondent x Applicant/Respondent)
    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Household Item: {self.item or self.id}"


class ComparisonNetFamilyPropertyBankAccount(models.Model):
    parent = models.ForeignKey(ComparisonNetFamilyProperty, on_delete=models.CASCADE, related_name="bank_accounts")
    category = models.CharField(max_length=255, blank=True)
    institution = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    comments = models.TextField(blank=True)
    document_number = models.CharField(max_length=100, blank=True)

    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Bank Account: {self.institution or self.id}"


class ComparisonNetFamilyPropertyInsurance(models.Model):
    parent = models.ForeignKey(ComparisonNetFamilyProperty, on_delete=models.CASCADE, related_name="insurances")
    company_policy = models.CharField(max_length=255, blank=True)
    owner = models.CharField(max_length=255, blank=True)
    beneficiary = models.CharField(max_length=255, blank=True)
    face_amount = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    comments = models.TextField(blank=True)
    document_number = models.CharField(max_length=100, blank=True)

    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Insurance: {self.company_policy or self.id}"


class ComparisonNetFamilyPropertyBusiness(models.Model):
    parent = models.ForeignKey(ComparisonNetFamilyProperty, on_delete=models.CASCADE, related_name="businesses")
    firm_name = models.CharField(max_length=255, blank=True)
    interests = models.CharField(max_length=255, blank=True)
    comments = models.TextField(blank=True)
    document_number = models.CharField(max_length=100, blank=True)

    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Business: {self.firm_name or self.id}"


# ============================================================
# 5) FORM 13C (Comparison) + CHILD TABLES (Page 3+)
# ============================================================
class Form13CComparison(models.Model):
    parent = models.OneToOneField(
        ComparisonNetFamilyProperty,
        related_name="form13c",
        on_delete=models.CASCADE,
    )

    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_office_address = models.CharField(max_length=255, blank=True, null=True)

    prepared_by = models.CharField(
        max_length=50,
        choices=[
            ("applicant", "Applicant"),
            ("respondent", "Respondent"),
            ("joint", "Applicant and Respondent jointly"),
        ],
        blank=True,
        null=True,
    )

    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_address = models.CharField(max_length=255, blank=True, null=True)
    applicant_phone = models.CharField(max_length=100, blank=True, null=True)
    applicant_email = models.EmailField(blank=True, null=True)
    applicant_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_address = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_phone = models.CharField(max_length=100, blank=True, null=True)
    applicant_lawyer_email = models.EmailField(blank=True, null=True)

    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_address = models.CharField(max_length=255, blank=True, null=True)
    respondent_phone = models.CharField(max_length=100, blank=True, null=True)
    respondent_email = models.EmailField(blank=True, null=True)
    respondent_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_address = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_phone = models.CharField(max_length=100, blank=True, null=True)
    respondent_lawyer_email = models.EmailField(blank=True, null=True)

    valuation_date = models.DateField(blank=True, null=True)
    statement_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"Form 13C Comparison: {self.court_file_number or self.id}"


# -------------------------------
# Form 13C Child Tables (FK -> form13c)
# -------------------------------
class Form13CAsset(models.Model):
    form13c = models.ForeignKey(Form13CComparison, related_name="assets", on_delete=models.CASCADE)

    nature_type_of_ownership = models.CharField(max_length=255, blank=True, null=True)
    nature_address_of_ownership = models.CharField(max_length=255, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13C Asset: {self.nature_type_of_ownership or self.id}"


class Form13CGeneralHouseholdItem(models.Model):
    form13c = models.ForeignKey(Form13CComparison, related_name="general_household_items", on_delete=models.CASCADE)

    item = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13C Household Item: {self.item or self.id}"


class Form13CBusinessInterest(models.Model):
    form13c = models.ForeignKey(Form13CComparison, related_name="business_interests", on_delete=models.CASCADE)

    name_of_firm = models.CharField(max_length=255, blank=True, null=True)
    interests = models.CharField(max_length=255, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13C Business: {self.name_of_firm or self.id}"


class Form13CMoneyOwed(models.Model):
    form13c = models.ForeignKey(Form13CComparison, related_name="money_owed", on_delete=models.CASCADE)

    details = models.CharField(max_length=255, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13C Money Owed: {self.details or self.id}"


class Form13COtherProperty(models.Model):
    form13c = models.ForeignKey(Form13CComparison, related_name="other_properties", on_delete=models.CASCADE)

    category = models.CharField(max_length=255, blank=True, null=True)
    details = models.CharField(max_length=255, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13C Other Property: {self.category or self.id}"


class Form13CDebtLiability(models.Model):
    form13c = models.ForeignKey(Form13CComparison, related_name="debts_liabilities", on_delete=models.CASCADE)

    category = models.CharField(max_length=255, blank=True, null=True)
    details = models.CharField(max_length=255, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13C Debt/Liability: {self.category or self.id}"


class Form13CMarriageProperty(models.Model):
    form13c = models.ForeignKey(Form13CComparison, related_name="marriage_properties", on_delete=models.CASCADE)

    category_details = models.CharField(max_length=255, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    is_debt = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13C Marriage Property: {self.category_details or self.id}"


class Form13CExcludedProperty(models.Model):
    form13c = models.ForeignKey(Form13CComparison, related_name="excluded_properties", on_delete=models.CASCADE)

    item = models.CharField(max_length=255, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    applicant_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13C Excluded Property: {self.item or self.id}"
class Form13CFinalTotals(models.Model):
    form13c = models.OneToOneField(
        Form13CComparison,
        related_name="final_totals",
        on_delete=models.CASCADE
    )

    # TOTAL 1
    total1_app_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total1_app_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total1_resp_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total1_resp_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # TOTAL 2
    total2_app_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total2_app_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total2_resp_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total2_resp_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # TOTAL 3
    total3_app_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total3_app_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total3_resp_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total3_resp_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # TOTAL 4
    total4_app_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total4_app_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total4_resp_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total4_resp_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # TOTAL 5
    total5_app_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total5_app_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total5_resp_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total5_resp_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # TOTAL 5B
    total5b_app_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total5b_app_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total5b_resp_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total5b_resp_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # TOTAL 6
    total6_app_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total6_app_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total6_resp_pos_applicant = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    total6_resp_pos_respondent = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    # Equalization Payments
    eq_app_pos_applicant_pays = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    eq_app_pos_respondent_pays = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    eq_resp_pos_applicant_pays = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)
    eq_resp_pos_respondent_pays = models.DecimalField(max_digits=30, decimal_places=3, blank=True, null=True)

    def __str__(self):
        return f"13C Final Totals for Form13C {self.form13c_id}"

# ============================================================
# BILLING & PRINT TRACKING
# ============================================================
class BillingSetting(models.Model):
    """Global billing settings for print charges."""
    form_type = models.CharField(max_length=100, unique=True)
    form_display_name = models.CharField(max_length=200)
    price_per_print = models.DecimalField(max_digits=30, decimal_places=3, default=Decimal('1.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['form_display_name']

    def __str__(self):
        return f"{self.form_display_name} - ${self.price_per_print}/print"


class PrintEvent(models.Model):
    """Track each print event for billing purposes."""
    FORM_TYPE_CHOICES = [
        ('financial_statement', 'Financial Statement (Form 13)'),
        ('financial_statement_131', 'Financial Statement - Property & Support (Form 13.1)'),
        ('net_family_property_13b', 'Net Family Property (Form 13B)'),
        ('comparison_nfp', 'Comparison of Net Family Property (Form 13C)'),
        ('application_divorce_8a', 'Form 8A — Application (Divorce)'),
        ('affidavit_service', 'Affidavit of Service (Form 6B)'),
        ('certificate_of_divorce', 'Certificate of Divorce (Form 36B)'),
        ('divorce_order', 'Divorce Order (Form 25A)'),
        ('divorce_order_onepage', 'Divorce Order (one page)'),
        ('divorce_order_a25a', 'Divorce Order (Form A-25A)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='print_events')
    form_type = models.CharField(max_length=100, choices=FORM_TYPE_CHOICES)
    form_id = models.IntegerField()  # The pk of the printed form
    form_identifier = models.CharField(max_length=255, blank=True)  # Court file number or name
    printed_at = models.DateTimeField(auto_now_add=True)
    price_charged = models.DecimalField(max_digits=30, decimal_places=3, default=Decimal('0.00'))
    is_billed = models.BooleanField(default=False)
    billed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-printed_at']
        indexes = [
            models.Index(fields=['user', 'printed_at']),
            models.Index(fields=['form_type', 'printed_at']),
            models.Index(fields=['is_billed']),
        ]

    def __str__(self):
        return f"{self.user.username} printed {self.get_form_type_display()} #{self.form_id} at {self.printed_at}"

    @classmethod
    def log_print(cls, user, form_type, form_id, form_identifier=''):
        """Convenience method to log a print event with auto-pricing."""
        # Get the price from BillingSetting
        try:
            setting = BillingSetting.objects.get(form_type=form_type, is_active=True)
            price = setting.price_per_print
        except BillingSetting.DoesNotExist:
            price = Decimal('1.00')  # Default price
        
        return cls.objects.create(
            user=user,
            form_type=form_type,
            form_id=form_id,
            form_identifier=form_identifier,
            price_charged=price
        )


class Invoice(models.Model):
    """Invoice for billing clients based on print events."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    print_events = models.ManyToManyField(PrintEvent, related_name='invoices')
    subtotal = models.DecimalField(max_digits=30, decimal_places=3, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=30, decimal_places=3, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=30, decimal_places=3, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=30, decimal_places=3, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.user.username}"

    def calculate_totals(self):
        """Recalculate invoice totals based on print events."""
        self.subtotal = sum(pe.price_charged for pe in self.print_events.all())
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total = self.subtotal + self.tax_amount
        self.save()

    def mark_as_paid(self):
        """Mark invoice and associated print events as paid."""
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()
        self.print_events.update(is_billed=True, billed_at=timezone.now())
class Form131FinancialStatement(SoftDeleteMixin, models.Model):
    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    case_file = models.ForeignKey(
        'CaseFile',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='form_131_financial_statements'
    )
    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    draft = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"Form 13.1: {self.court_file_number or self.id}"

    def save_page_data(self, page_number, data):
        if not self.draft:
            self.draft = {}
        self.draft[f"page{page_number}"] = data
        self.save()

    def get_page_data(self, page_number):
        if not self.draft:
            return {}
        return self.draft.get(f"page{page_number}", {})


# ============================================================
# EMAIL SETTINGS - Configurable email notifications
# ============================================================
class EmailSettings(models.Model):
    """
    Singleton model for email configuration.
    Only one instance should exist.
    """
    # Toggle for notifications
    notifications_enabled = models.BooleanField(default=True, help_text="Enable/disable all email notifications")
    
    # SMTP Settings
    email_host = models.CharField(max_length=255, blank=True, help_text="SMTP server hostname")
    email_port = models.PositiveIntegerField(default=587, help_text="SMTP port (usually 587 for TLS, 465 for SSL)")
    email_use_ssl = models.BooleanField(default=False, help_text="Use SSL connection")
    email_use_tls = models.BooleanField(default=True, help_text="Use TLS connection")
    email_host_user = models.CharField(max_length=255, blank=True, help_text="SMTP username")
    email_host_password = models.CharField(max_length=255, blank=True, help_text="SMTP password")
    
    # From and notification emails
    default_from_email = models.CharField(max_length=255, blank=True, help_text="Default sender email")
    admin_notification_email = models.CharField(max_length=255, blank=True, help_text="Email to receive notifications")
    
    # Notification toggles
    notify_on_login = models.BooleanField(default=True, help_text="Send notification when users log in")
    notify_on_form_create = models.BooleanField(default=True, help_text="Send notification when forms are created")
    notify_on_form_print = models.BooleanField(default=True, help_text="Send notification when forms are printed")
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Email Settings"
        verbose_name_plural = "Email Settings"

    def __str__(self):
        status = "Enabled" if self.notifications_enabled else "Disabled"
        return f"Email Settings ({status})"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def is_enabled(cls, notification_type='all'):
        """Check if a specific notification type is enabled."""
        try:
            settings = cls.objects.get(pk=1)
            if not settings.notifications_enabled:
                return False
            if notification_type == 'login':
                return settings.notify_on_login
            elif notification_type == 'form_create':
                return settings.notify_on_form_create
            elif notification_type == 'form_print':
                return settings.notify_on_form_print
            return True
        except cls.DoesNotExist:
            return True  # Default to enabled if not configured
        
#Application 8A

class ApplicationDivorce8A(SoftDeleteMixin, models.Model):
    case_file = models.ForeignKey(
        "CaseFile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="application_divorce_8a_forms"
    )

    # Page 1 — Court and parties
    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_file_number = models.CharField(max_length=255, blank=True, null=True)
    court_office_address = models.TextField(blank=True, null=True)

    is_simple_divorce = models.BooleanField(default=False)
    is_joint_application = models.BooleanField(default=False)

    applicant_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_address = models.TextField(blank=True, null=True)
    applicant_phone_fax = models.CharField(max_length=255, blank=True, null=True)
    applicant_email = models.EmailField(blank=True, null=True)

    applicant_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_address = models.TextField(blank=True, null=True)
    applicant_lawyer_phone_fax = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_email = models.EmailField(blank=True, null=True)

    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_address = models.TextField(blank=True, null=True)
    respondent_phone_fax = models.CharField(max_length=255, blank=True, null=True)
    respondent_email = models.EmailField(blank=True, null=True)

    respondent_lawyer_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_address = models.TextField(blank=True, null=True)
    respondent_lawyer_phone_fax = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_email = models.EmailField(blank=True, null=True)

    # Page 2
    date_of_issue = models.DateField(blank=True, null=True)
    joint_application_details = models.TextField(blank=True, null=True)
    clerk_name = models.CharField(max_length=255, blank=True, null=True)
    clerk_signature = models.CharField(max_length=255, blank=True, null=True)

    # Page 3 — Family history
    applicant_age = models.PositiveIntegerField(blank=True, null=True)
    applicant_birthdate = models.DateField(blank=True, null=True)
    applicant_resident_in = models.CharField(max_length=255, blank=True, null=True)
    applicant_first_name_before_marriage = models.CharField(max_length=255, blank=True, null=True)
    applicant_last_name_before_marriage = models.CharField(max_length=255, blank=True, null=True)
    applicant_gender = models.CharField(max_length=100, blank=True, null=True)
    applicant_divorced_before = models.BooleanField(default=False)
    applicant_previous_divorce_details = models.TextField(blank=True, null=True)
    applicant_resided_ontario_one_year = models.BooleanField(default=False)

    respondent_age = models.PositiveIntegerField(blank=True, null=True)
    respondent_birthdate = models.DateField(blank=True, null=True)
    respondent_resident_in = models.CharField(max_length=255, blank=True, null=True)
    respondent_first_name_before_marriage = models.CharField(max_length=255, blank=True, null=True)
    respondent_last_name_before_marriage = models.CharField(max_length=255, blank=True, null=True)
    respondent_gender = models.CharField(max_length=100, blank=True, null=True)
    respondent_divorced_before = models.BooleanField(default=False)
    respondent_previous_divorce_details = models.TextField(blank=True, null=True)
    respondent_resided_ontario_one_year = models.BooleanField(default=False)

    married_on = models.DateField(blank=True, null=True)
    started_living_together_on = models.DateField(blank=True, null=True)
    separated_on = models.DateField(blank=True, null=True)
    never_lived_together = models.BooleanField(default=False)

    children_details = models.TextField(blank=True, null=True)

    previous_court_case = models.BooleanField(default=False)
    previous_written_agreement = models.BooleanField(default=False)
    previous_agreement_details = models.TextField(blank=True, null=True)

    # Page 4 — Claims
    notice_of_calculation_issued = models.BooleanField(default=False)
    notice_of_calculation_details = models.TextField(blank=True, null=True)
    asking_different_child_support = models.BooleanField(default=False)
    different_child_support_explanation = models.TextField(blank=True, null=True)

    claim_divorce = models.BooleanField(default=False)
    claim_spousal_support = models.BooleanField(default=False)
    claim_child_support_table = models.BooleanField(default=False)
    claim_child_support_other = models.BooleanField(default=False)
    claim_decision_making = models.BooleanField(default=False)
    claim_parenting_time = models.BooleanField(default=False)

    claim_support_child_table_family_law = models.BooleanField(default=False)
    claim_support_child_other_family_law = models.BooleanField(default=False)
    claim_restraining_order = models.BooleanField(default=False)
    claim_indexing_spousal_support = models.BooleanField(default=False)
    claim_declaration_parentage = models.BooleanField(default=False)
    claim_guardianship_child_property = models.BooleanField(default=False)

    claim_property_equalization = models.BooleanField(default=False)
    claim_exclusive_possession_home = models.BooleanField(default=False)
    claim_exclusive_possession_contents = models.BooleanField(default=False)
    claim_freezing_assets = models.BooleanField(default=False)
    claim_sale_family_property = models.BooleanField(default=False)

    claim_costs = models.BooleanField(default=False)
    claim_annulment = models.BooleanField(default=False)
    claim_prejudgment_interest = models.BooleanField(default=False)
    claim_other = models.BooleanField(default=False)
    other_claims = models.TextField(blank=True, null=True)

    simple_claim_divorce = models.BooleanField(default=False)
    simple_claim_costs = models.BooleanField(default=False)

    divorce_ground_separation = models.BooleanField(default=False)
    separation_date = models.DateField(blank=True, null=True)
    not_lived_together_since = models.BooleanField(default=False)
    lived_together_attempt_reconcile = models.BooleanField(default=False)
    lived_together_periods = models.TextField(blank=True, null=True)

    divorce_ground_adultery = models.BooleanField(default=False)
    adultery_spouse_name = models.CharField(max_length=255, blank=True, null=True)
    adultery_details = models.TextField(blank=True, null=True)

    # Page 5
    divorce_ground_cruelty = models.BooleanField(default=False)
    cruelty_spouse_name = models.CharField(max_length=255, blank=True, null=True)
    cruelty_victim_name = models.CharField(max_length=255, blank=True, null=True)
    cruelty_details = models.TextField(blank=True, null=True)

    joint_orders_details = models.TextField(blank=True, null=True)
    important_facts_supporting_claims = models.TextField(blank=True, null=True)

    applicant_certificate_confirmed = models.BooleanField(default=False)
    applicant_signature = models.CharField(max_length=255, blank=True, null=True)
    applicant_signature_date = models.DateField(blank=True, null=True)

    joint_applicant_signature_1 = models.CharField(max_length=255, blank=True, null=True)
    joint_applicant_signature_1_date = models.DateField(blank=True, null=True)

    joint_applicant_signature_2 = models.CharField(max_length=255, blank=True, null=True)
    joint_applicant_signature_2_date = models.DateField(blank=True, null=True)

    # Page 6 — Lawyer certificate
    applicant_lawyer_certificate_name = models.CharField(max_length=255, blank=True, null=True)
    applicant_lawyer_certificate_date = models.DateField(blank=True, null=True)
    applicant_lawyer_certificate_signature = models.CharField(max_length=255, blank=True, null=True)

    respondent_lawyer_certificate_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_lawyer_certificate_date = models.DateField(blank=True, null=True)
    respondent_lawyer_certificate_signature = models.CharField(max_length=255, blank=True, null=True)

    # Extra/flexible fields
    filing_date = models.DateField(blank=True, null=True)
    place_of_filing = models.CharField(max_length=255, blank=True, null=True)
    filing_notes = models.TextField(blank=True, null=True)
    additional_notes = models.TextField(blank=True, null=True)
    special_filing_instructions = models.TextField(blank=True, null=True)

    marriage_certificate = models.FileField(upload_to="form8a/marriage_certificates/", blank=True, null=True)
    financial_statement_attachment = models.FileField(upload_to="form8a/financial_statements/", blank=True, null=True)
    other_supporting_documents = models.FileField(upload_to="form8a/supporting_documents/", blank=True, null=True)

    review_confirmed = models.BooleanField(default=False)
    documents_complete = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Form 8A Application Divorce"
        verbose_name_plural = "Form 8A Application Divorce"

    def __str__(self):
        return f"Form 8A - {self.applicant_name or 'Applicant'} v {self.respondent_name or 'Respondent'}"