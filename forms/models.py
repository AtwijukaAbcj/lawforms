# forms/models.py
from django.db import models
from django.utils import timezone


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
    applicant_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Asset: {self.item or self.id} (Statement {self.statement_id})"


# ============================================================
# 2) SIMPLE FORM: FinancialStatement (Standalone Root)
# ============================================================
class FinancialStatement(SoftDeleteMixin, models.Model):
    # Draft field for storing extra dynamic data
    draft = models.JSONField(blank=True, null=True)
    
    court_file_number = models.CharField(max_length=100, blank=True, null=True)
    court_name = models.CharField(max_length=255, blank=True, null=True)
    court_office_address = models.CharField(max_length=255, blank=True, null=True)

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
    last_year_gross_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Page 2 - Indian status option
    indian_status = models.BooleanField(default=False)
    indian_status_docs = models.TextField(blank=True, null=True)
    
    # Page 2 - Income table (monthly amounts)
    income_employment = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_commissions = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_self_employment_before_expenses = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_self_employment = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_ei = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_workers_comp = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_social_assistance = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_investment = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_pension = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_spousal_support = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_tax_benefits = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_other = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_total_monthly = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_total_annual = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # Page 3 - Other Benefits (14)
    benefit_item_1 = models.CharField(max_length=255, blank=True, null=True)
    benefit_details_1 = models.TextField(blank=True, null=True)
    benefit_value_1 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    benefit_item_2 = models.CharField(max_length=255, blank=True, null=True)
    benefit_details_2 = models.TextField(blank=True, null=True)
    benefit_value_2 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    benefit_item_3 = models.CharField(max_length=255, blank=True, null=True)
    benefit_details_3 = models.TextField(blank=True, null=True)
    benefit_value_3 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    benefit_item_4 = models.CharField(max_length=255, blank=True, null=True)
    benefit_details_4 = models.TextField(blank=True, null=True)
    benefit_value_4 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # Part 2 - Expenses (Pages 3-4) - All monthly amounts
    # Automatic Deductions
    cpp_contributions = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    ei_premiums = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    income_taxes = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    employee_pension_contributions = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    union_dues = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    automatic_deductions_subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Housing
    rent_or_mortgage = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    property_taxes = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    property_insurance = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    condo_fees = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    repairs_maintenance = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    housing_subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Utilities
    water = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    heat = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    electricity = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    telephone = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cell_phone = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cable = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    internet = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    utilities_subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Transportation
    public_transit_taxis = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    gas_oil = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    car_insurance_license = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    car_repairs_maintenance = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    parking = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    car_loan_lease_payments = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    transportation_subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Health
    health_insurance_premiums = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    dental_expenses = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    medicine_drugs = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    eye_care = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    health_subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Personal
    clothing = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    hair_care_beauty = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    alcohol_tobacco = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    education = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    entertainment = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    gifts = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    personal_subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Household Expenses
    groceries = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    household_supplies = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    meals_outside = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    pet_care = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    laundry_dry_cleaning = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    household_subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Childcare Costs
    daycare_expense = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    babysitting_costs = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    childcare_subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Other expenses
    life_insurance_premiums = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    rrsp_resp_withdrawals = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    vacations = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    school_fees_supplies = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    clothing_for_children = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    children_activities = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    summer_camp_expenses = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    debt_payments = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    support_paid_for_other_children = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    other_expenses_specify = models.TextField(blank=True, null=True)
    other_expenses_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    other_expenses_subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Total expenses
    total_monthly_expenses = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_yearly_expenses = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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
    total_value_all_property = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # Part 4 - Debts (Page 6) - JSON field for variable number of entries
    debts = models.JSONField(blank=True, null=True)  # list of {type, creditor, full_amount, monthly_payment, payments_being_made}
    total_debts_outstanding = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Part 5 - Summary of Assets and Liabilities
    total_assets = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_debts = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    net_worth = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Signature section (Page 6)
    sworn_municipality = models.CharField(max_length=255, blank=True, null=True)
    sworn_province_country = models.CharField(max_length=255, blank=True, null=True)
    sworn_date = models.DateField(blank=True, null=True)
    commissioner_signature = models.CharField(max_length=255, blank=True, null=True)

    # Schedule A - Additional Sources of Income (Page 7)
    schedule_a_partnership_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    schedule_a_rental_income_gross = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    schedule_a_rental_income_net = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    schedule_a_dividends = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    schedule_a_capital_gains = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    schedule_a_capital_losses = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    schedule_a_rrsp_withdrawals = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    schedule_a_rrif_annuity = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    schedule_a_other_income_source = models.TextField(blank=True, null=True)
    schedule_a_other_income_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    schedule_a_subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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
    spouse_income_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    spouse_income_period = models.CharField(max_length=50, blank=True, null=True)
    spouse_no_income = models.BooleanField(default=False)
    
    household_contribution = models.BooleanField(default=False)
    household_contribution_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    household_contribution_period = models.CharField(max_length=100, blank=True, null=True)

    # Schedule C - Special or Extraordinary Expenses for Children (Page 8)
    schedule_c_expenses = models.JSONField(blank=True, null=True)  # list of {child_name, expense, amount_per_year, tax_credits}
    schedule_c_total_annual = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    schedule_c_total_monthly = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    schedule_c_my_income_for_share = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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
    applicant_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13B Asset: {self.item or self.id}"


class NetFamilyProperty13BDebt(models.Model):
    statement = models.ForeignKey(NetFamilyProperty13B, related_name="debts", on_delete=models.CASCADE, db_index=True)
    item = models.CharField(max_length=255, blank=True, null=True)
    applicant_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13B Debt: {self.item or self.id}"


class NetFamilyProperty13BMarriageProperty(models.Model):
    statement = models.ForeignKey(NetFamilyProperty13B, related_name="marriage_properties", on_delete=models.CASCADE)
    item = models.CharField(max_length=255, blank=True, null=True)  # ✅ item (NOT property_item)
    applicant_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13B Marriage Property: {self.item or self.id}"


class NetFamilyProperty13BMarriageDebt(models.Model):
    statement = models.ForeignKey(NetFamilyProperty13B, related_name="marriage_debts", on_delete=models.CASCADE)
    item = models.CharField(max_length=255, blank=True, null=True)  # ✅ item (NOT debt_item)
    applicant_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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
    applicant_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13B Excluded: {self.item or self.id}"


class NetFamilyProperty13BFinalTotals(models.Model):
    statement = models.OneToOneField(NetFamilyProperty13B, related_name="final_totals", on_delete=models.CASCADE)

    total1 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total2 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total3 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total4 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total5 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total6 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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


class ComparisonNetFamilyPropertyHouseholdItem(models.Model):
    parent = models.ForeignKey(ComparisonNetFamilyProperty, on_delete=models.CASCADE, related_name="household_items")
    item = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    document_number = models.CharField(max_length=100, blank=True)

    # These 4 fields match the form columns (Applicant/Respondent x Applicant/Respondent)
    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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

    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Bank Account: {self.institution or self.id}"


class ComparisonNetFamilyPropertyInsurance(models.Model):
    parent = models.ForeignKey(ComparisonNetFamilyProperty, on_delete=models.CASCADE, related_name="insurances")
    company_policy = models.CharField(max_length=255, blank=True)
    owner = models.CharField(max_length=255, blank=True)
    beneficiary = models.CharField(max_length=255, blank=True)
    face_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    comments = models.TextField(blank=True)
    document_number = models.CharField(max_length=100, blank=True)

    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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

    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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

    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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

    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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

    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13C Business: {self.name_of_firm or self.id}"


class Form13CMoneyOwed(models.Model):
    form13c = models.ForeignKey(Form13CComparison, related_name="money_owed", on_delete=models.CASCADE)

    details = models.CharField(max_length=255, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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

    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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

    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13C Debt/Liability: {self.category or self.id}"


class Form13CMarriageProperty(models.Model):
    form13c = models.ForeignKey(Form13CComparison, related_name="marriage_properties", on_delete=models.CASCADE)

    category_details = models.CharField(max_length=255, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

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

    applicant_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    applicant_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    respondent_position_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"13C Excluded Property: {self.item or self.id}"


class Form13CFinalTotals(models.Model):
    form13c = models.OneToOneField(Form13CComparison, related_name="final_totals", on_delete=models.CASCADE)

    # TOTAL 1: Value of Property Owned on Valuation Date
    total1_app_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total1_app_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total1_resp_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total1_resp_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # TOTAL 2: Debts and Other Liabilities
    total2_app_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total2_app_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total2_resp_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total2_resp_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # TOTAL 3: Value of Property Owned on the Date of Marriage
    total3_app_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total3_app_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total3_resp_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total3_resp_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # TOTAL 4: Value of Excluded Property
    total4_app_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total4_app_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total4_resp_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total4_resp_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # TOTAL 5: Sum of TOTAL 2 + TOTAL 3 + TOTAL 4
    total5_app_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total5_app_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total5_resp_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total5_resp_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # TOTAL 5b (duplicate for second table)
    total5b_app_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total5b_app_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total5b_resp_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total5b_resp_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # TOTAL 6: Net Family Property (TOTAL 1 - TOTAL 5)
    total6_app_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total6_app_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total6_resp_pos_applicant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total6_resp_pos_respondent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # Equalization Payments
    eq_app_pos_applicant_pays = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    eq_app_pos_respondent_pays = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    eq_resp_pos_applicant_pays = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    eq_resp_pos_respondent_pays = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"13C Final Totals for Form13C {self.form13c_id}"
