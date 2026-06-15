# forms/views.py - Comprehensive version with all data saving properly
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.forms import modelformset_factory, inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect
from users.context_processors import user_permissions
from django.contrib.auth.decorators import login_required, user_passes_test
# Delete PrintEvent (admin/staff only)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from datetime import date, datetime
from decimal import Decimal

# ...existing code...

# Import at the bottom to avoid circular import issues and cover all usages
from users.views import log_action as log_audit
from forms.notifications import send_form_printed_notification, send_form_created_notification
from django.utils import timezone
from functools import lru_cache
from pathlib import Path
from collections import OrderedDict
from .models import AffidavitOfService, CaseFile, DivorceOrder, DivorceOrderA25A
from .forms import (
    AffidavitOfServiceForm,
    AffidavitServicePage1Form,
    AffidavitServicePage2Form,
    AffidavitServicePage3Form,
    DivorceOrderForm,
    DivorceOrderA25AForm,
)
from .models import (
    # Base single-page models
    NetFamilyPropertyStatement,
    FinancialStatement,

    # 13B models
    NetFamilyProperty13B,
    NetFamilyProperty13BAsset,
    NetFamilyProperty13BDebt,
    NetFamilyProperty13BMarriageProperty,
    NetFamilyProperty13BMarriageDebt,
    NetFamilyProperty13BExcluded,
    NetFamilyProperty13BFinalTotals,

    # Comparison NFP (your multi-page starter model)
    ComparisonNetFamilyProperty,
    ComparisonNetFamilyPropertyHouseholdItem,
    ComparisonNetFamilyPropertyBankAccount,
    ComparisonNetFamilyPropertyInsurance,
    ComparisonNetFamilyPropertyBusiness,

    # Form 13C models (comparison pages 3 & 4)
    Form13CComparison,
    Form13CAsset,
    Form13CMoneyOwed,
    Form13COtherProperty,
    Form13CDebtLiability,
    Form13CMarriageProperty,
    Form13CExcludedProperty,
    Form13CFinalTotals,
    ApplicationDivorce8A,
    CertificateOfDivorce,
    # Billing & Print tracking
    PrintEvent,
    CaseFile,
)

import re
from decimal import Decimal, ROUND_HALF_UP


def _money(value):
    try:
        return Decimal(str(value or 0)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
    except Exception:
        return Decimal("0.00")


def _num(data, key):
    if not isinstance(data, dict):
        return Decimal("0.00")
    return _money(data.get(key))


def _sum_keys(data, keys):
    total = Decimal("0.00")

    if not isinstance(data, dict):
        return total

    for key in keys:
        total += _num(data, key)

    return _money(total)


def _normalize_financial_statement_debts(debts):
    if debts is None:
        return {}
    if isinstance(debts, dict):
        return debts
    if not isinstance(debts, list):
        return {}

    normalized = {}
    mortgage_index = 1
    credit_card_index = 1
    other_index = 1

    for item in debts:
        if not isinstance(item, dict):
            continue

        type_value = str(item.get('type', '')).strip().lower()
        creditor = item.get('creditor', '') or item.get('name_address_of_creditor', '')
        amount = item.get('full_amount', '') or item.get('amount', '')
        monthly = item.get('monthly_payment', '') or item.get('monthly', '')
        payment = item.get('payments_being_made', item.get('payment', ''))

        if 'mortgage' in type_value:
            prefix = f'mortgage_{mortgage_index}'
            mortgage_index += 1
        elif 'credit card' in type_value or 'visa' in type_value or 'mastercard' in type_value or 'amex' in type_value:
            prefix = f'credit_card_{credit_card_index}'
            credit_card_index += 1
        elif 'unpaid' in type_value or 'support' in type_value:
            prefix = 'unpaid_support'
        else:
            prefix = f'other_debt_{other_index}'
            other_index += 1

        normalized[f'{prefix}_creditor'] = creditor or ''
        normalized[f'{prefix}_amount'] = amount or ''
        normalized[f'{prefix}_monthly'] = monthly or ''
        if isinstance(payment, bool):
            normalized[f'{prefix}_payment'] = 'yes' if payment else ''
        else:
            normalized[f'{prefix}_payment'] = payment or ''

    return normalized


def _calculate_form131_totals(pages):
    """
    Calculate Form 13.1 totals for Page 9.
    Item 22 = value of all property owned on valuation date.
    Item 25 = total deductions.
    Item 26 = excluded property.
    """

    pages = pages or {}

    page5 = pages.get("page5", {}) or {}
    page6 = pages.get("page6", {}) or {}
    page7 = pages.get("page7", {}) or {}
    page8 = pages.get("page8", {}) or {}
    page9 = pages.get("page9", {}) or {}

    # ITEM 22: Value of all property owned on valuation date
    item22 = Decimal("0.00")

    item22 += _sum_keys(page5, [
        "land_total",
        "real_estate_total",
        "general_household_items_total",
        "household_items_total",
        "bank_accounts_total",
        "savings_total",
        "rrsp_total",
        "vehicles_total",
        "pension_total",
        "life_insurance_total",
        "business_interests_total",
        "money_owed_total",
        "other_property_total",
        "total_value_all_property",
        "total_assets",
        "item22_total",
    ])

    item22 += _sum_keys(page6, [
        "land_total",
        "real_estate_total",
        "vehicles_total",
        "bank_accounts_total",
        "business_interests_total",
        "money_owed_total",
        "other_property_total",
        "total_value_all_property",
        "total_assets",
        "item22_total",
    ])

    item22 += _sum_keys(page7, [
        "land_total",
        "real_estate_total",
        "vehicles_total",
        "bank_accounts_total",
        "business_interests_total",
        "money_owed_total",
        "other_property_total",
        "total_value_all_property",
        "total_assets",
        "item22_total",
    ])

    item22 = _money(item22)

    # ITEM 25: Total deductions
    item25 = Decimal("0.00")

    item25 += _sum_keys(page7, [
        "total_debts",
        "total_liabilities",
        "total_deductions",
        "deductions_total",
        "item25_total",
    ])

    item25 += _sum_keys(page8, [
        "total_debts",
        "total_liabilities",
        "total_deductions",
        "total_value_deductions",
        "deductions_total",
        "item25_total",
    ])

    item25 = _money(item25)

    # ITEM 26: Excluded property
    item26 = Decimal("0.00")

    item26 += _sum_keys(page7, [
        "total_excluded_property",
        "excluded_property_total",
        "item26_total",
    ])

    item26 += _sum_keys(page8, [
        "total_excluded_property",
        "excluded_property_total",
        "item26_total",
    ])

    item26 = _money(item26)

    balance1 = _money(item22 - item25)
    balance2 = _money(balance1 - item26)

    page9["nfp_item22"] = str(item22)
    page9["nfp_item25"] = str(item25)
    page9["nfp_item26"] = str(item26)
    page9["nfp_balance1"] = str(balance1)
    page9["nfp_balance2"] = str(balance2)
    page9["net_family_property"] = str(balance2)

    pages["page9"] = page9

    return pages


def _calculate_form131_missing_totals(pages):
    """
    Fill totals/subtotals that the existing _calculate_form131_totals()
    does not currently calculate:
      - page 2 income totals
      - page 3 subtotals
      - page 4 subtotals + total monthly/yearly expenses
      - page 10 Schedule A and Schedule B totals
    """
    # ...existing code for _calculate_form131_missing_totals...
    # (Copy the full function body from your file above)
    # ...
    return pages

@login_required
def financial_statement_131_print(request, pk):
    import json
    from .models import Form131FinancialStatement

    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    merged_data = get_all_form131_data(form)

    pages = form.draft or {}

    page1 = _get_form131_page1_data(form, persist=True)
    pages["page1"] = page1

    pages = _calculate_form131_totals(pages)
    pages = _calculate_form131_missing_totals(pages)

    page4 = form.get_page_data(4) or pages.get("page4", {}) or {}

    def truthy(value):
        return str(value).strip().lower() in [
            "true", "on", "1", "yes", "checked"
        ]

    def get_first(*keys):
        for key in keys:
            value = page4.get(key)
            if value not in [None, "", False]:
                return value
        return ""

    # Page 4 Part 3 - exact values from saved data
    page4["live_alone"] = truthy(get_first(
        "live_alone",
        "lives_alone"
    ))

    page4["living_with_someone"] = truthy(get_first(
        "living_with_someone",
        "living_with_spouse",
        "living_with_partner"
    ))

    page4["living_with_name"] = get_first(
        "living_with_name",
        "spouse_name",
        "partner_name"
    )

    page4["lives_with_other_adults"] = truthy(get_first(
        "lives_with_other_adults",
        "living_with_others",
        "has_other_adults"
    )) or bool(get_first(
        "other_adults_names",
        "other_adults"
    ))

    page4["other_adults_names"] = get_first(
        "other_adults_names",
        "other_adults"
    )

    page4["has_children_in_home"] = truthy(get_first(
        "has_children_in_home",
        "has_children_home",
        "has_children",
        "children_in_home",
        "has_children_living_home"
    )) or bool(get_first(
        "number_of_children_in_home",
        "num_children_home",
        "num_children",
        "children_count",
        "child_count",
        "children_home_count",
        "number_children_home"
    ))

    page4["number_of_children_in_home"] = get_first(
        "number_of_children_in_home",
        "num_children_home",
        "num_children",
        "children_count",
        "child_count",
        "children_home_count",
        "number_children_home"
    )

    page4["spouse_works"] = truthy(get_first(
        "spouse_works",
        "partner_works"
    )) or bool(get_first(
        "spouse_work_place",
        "spouse_workplace",
        "partner_workplace",
        "partner_work_place"
    ))

    page4["spouse_work_place"] = get_first(
        "spouse_work_place",
        "spouse_workplace",
        "partner_workplace",
        "partner_work_place"
    )

    page4["spouse_does_not_work"] = truthy(get_first(
        "spouse_does_not_work",
        "spouse_not_work",
        "partner_not_work"
    ))

    page4["spouse_earns_income"] = truthy(get_first(
        "spouse_earns_income",
        "spouse_earns",
        "partner_earns"
    )) or bool(get_first(
        "spouse_income_amount",
        "spouse_income",
        "partner_income",
        "spouse_earnings",
        "partner_earnings",
        "partner_earn_amount",
        "partner_earns_amount",
        "spouse_earn_amount",
        "spouse_earns_amount"
    ))

    page4["spouse_income_amount"] = get_first(
        "spouse_income_amount",
        "spouse_income",
        "partner_income",
        "spouse_earnings",
        "partner_earnings",
        "partner_earn_amount",
        "partner_earns_amount",
        "spouse_earn_amount",
        "spouse_earns_amount"
    )

    page4["spouse_income_period"] = get_first(
        "spouse_income_period",
        "partner_income_period",
        "spouse_earnings_period",
        "partner_earnings_period",
        "partner_earn_period",
        "spouse_earn_period"
    )

    page4["spouse_no_income"] = truthy(get_first(
        "spouse_no_income",
        "partner_no_income"
    ))

    page4["household_contribution_amount"] = get_first(
        "household_contribution_amount",
        "household_contribution",
        "contribution_amount"
    )

    page4["household_contribution_period"] = get_first(
        "household_contribution_period",
        "contribution_period"
    )

    pages["page4"] = page4

    print_event = PrintEvent.log_print(
        user=request.user,
        form_type="financial_statement_131",
        form_id=pk,
        form_identifier=page1.get("court_file_number") or form.court_file_number or f"Form 13.1 #{pk}",
    )

    log_audit(
        request,
        "export",
        "financial_statement_131",
        pk,
        f"Form 13.1 #{pk}",
        f"Printed - Price: ${print_event.price_charged}",
    )

    send_form_printed_notification(
        "financial_statement_131",
        form,
        request.user,
        print_event.price_charged,
    )

    return render(request, "forms/financial_statement_131_print.html", {
        "form": form,
        "pages": pages,
        "pages_json": json.dumps(pages, default=str),
        "court_file_number": page1.get("court_file_number") or form.court_file_number or "",
        "applicant_name": page1.get("applicant_name") or form.applicant_name or "",
        "respondent_name": page1.get("respondent_name") or form.respondent_name or "",
        **merged_data,
    })

def _user_has_permission_or_owner(user, module_code, permission_type, instance=None):
    """Return True if user is superuser, owner of associated CaseFile, or has role permission."""
    if user.is_superuser:
        return True

    # Owner check for instance that links to CaseFile
    try:
        profile = user.profile
    except Exception:
        profile = None

    # If instance provided and links to a case_file with owner, allow owner
    if instance is not None:
        case = getattr(instance, 'case_file', None)
        if case and getattr(case, 'owner', None) == user:
            return True

    if profile and profile.has_module_permission(module_code, permission_type):
        return True

    return False


@login_required
def case_list(request):
    """List CaseFiles belonging to the current user."""
    cases = CaseFile.objects.filter(owner=request.user).order_by('-updated_at')
    return render(request, 'forms/case_list.html', {'cases': cases})

@login_required
def case_create(request, pk=None):
    """
    Create or Edit a CaseFile.
    """

    case = None

    if pk:
        case = get_object_or_404(
            CaseFile,
            pk=pk,
            owner=request.user
        )

    if request.method == "POST":

        data = request.POST

        if case:
            # EDIT EXISTING
            case.court_file_number = data.get('court_file_number', '')
            case.court_name = data.get('court_name', '')
            case.court_office_address = data.get('court_office_address', '')

            case.applicant_name = data.get('applicant_name', '')
            case.applicant_address = data.get('applicant_address', '')
            case.applicant_phone = data.get('applicant_phone', '')
            case.applicant_email = data.get('applicant_email', '')

            case.applicant_lawyer_name = data.get('applicant_lawyer_name', '')
            case.applicant_lawyer_address = data.get('applicant_lawyer_address', '')
            case.applicant_lawyer_phone = data.get('applicant_lawyer_phone', '')
            case.applicant_lawyer_email = data.get('applicant_lawyer_email', '')

            case.respondent_name = data.get('respondent_name', '')
            case.respondent_address = data.get('respondent_address', '')
            case.respondent_phone = data.get('respondent_phone', '')
            case.respondent_email = data.get('respondent_email', '')

            case.respondent_lawyer_name = data.get('respondent_lawyer_name', '')
            case.respondent_lawyer_address = data.get('respondent_lawyer_address', '')
            case.respondent_lawyer_phone = data.get('respondent_lawyer_phone', '')
            case.respondent_lawyer_email = data.get('respondent_lawyer_email', '')

            case.valuation_date = data.get('valuation_date') or None

            case.save()

        else:
            # CREATE NEW
            case = CaseFile.objects.create(
                owner=request.user,
                court_file_number=data.get('court_file_number', ''),
                court_name=data.get('court_name', ''),
                court_office_address=data.get('court_office_address', ''),
                applicant_name=data.get('applicant_name', ''),
                applicant_address=data.get('applicant_address', ''),
                applicant_phone=data.get('applicant_phone', ''),
                applicant_email=data.get('applicant_email', ''),
                applicant_lawyer_name=data.get('applicant_lawyer_name', ''),
                applicant_lawyer_address=data.get('applicant_lawyer_address', ''),
                applicant_lawyer_phone=data.get('applicant_lawyer_phone', ''),
                applicant_lawyer_email=data.get('applicant_lawyer_email', ''),
                respondent_name=data.get('respondent_name', ''),
                respondent_address=data.get('respondent_address', ''),
                respondent_phone=data.get('respondent_phone', ''),
                respondent_email=data.get('respondent_email', ''),
                respondent_lawyer_name=data.get('respondent_lawyer_name', ''),
                respondent_lawyer_address=data.get('respondent_lawyer_address', ''),
                respondent_lawyer_phone=data.get('respondent_lawyer_phone', ''),
                respondent_lawyer_email=data.get('respondent_lawyer_email', ''),
                valuation_date=data.get('valuation_date') or None,
            )

        return redirect('case_detail', pk=case.pk)

    return render(
        request,
        'forms/case_create.html',
        {
            'case': case
        }
    )

@login_required
def case_detail(request, pk):
    """View a CaseFile (only owner may view)."""
    case = get_object_or_404(CaseFile, pk=pk, owner=request.user)
    return render(request, 'forms/case_detail.html', {'case': case})


@login_required
@require_http_methods(["POST"])
def case_push_to_forms(request, pk):
    """Push CaseFile top-level fields to all related forms (explicit action).

    Only the case owner may perform this action. This performs a whitelist
    update of common top-level fields on related form records.
    """
    case = get_object_or_404(CaseFile, pk=pk, owner=request.user)

    field_map = [
        'court_file_number', 'court_name', 'court_office_address',
        'applicant_name', 'applicant_address', 'applicant_phone', 'applicant_email',
        'applicant_lawyer_name', 'applicant_lawyer_address', 'applicant_lawyer_phone', 'applicant_lawyer_email',
        'respondent_name', 'respondent_address', 'respondent_phone', 'respondent_email',
        'respondent_lawyer_name', 'respondent_lawyer_address', 'respondent_lawyer_phone', 'respondent_lawyer_email',
    ]

    updated = 0
    with transaction.atomic():
        # FinancialStatement
        for stmt in case.financial_statements.all():
            if _apply_case_fields_to_instance(stmt, case, overwrite=True):
                stmt.save()
                updated += 1

        # NetFamilyPropertyStatement
        for stmt in case.net_family_property_statements.all():
            if _apply_case_fields_to_instance(stmt, case, overwrite=True):
                stmt.save()
                updated += 1

        # NetFamilyProperty13B
        for stmt in case.net_family_property_13b_forms.all():
            if _apply_case_fields_to_instance(stmt, case, overwrite=True):
                stmt.save()
                updated += 1

        # ComparisonNetFamilyProperty
        for stmt in case.comparison_net_family_properties.all():
            if _apply_case_fields_to_instance(stmt, case, overwrite=True):
                stmt.save()
                updated += 1

        # Form131FinancialStatement
        for stmt in case.form_131_financial_statements.all():
            if _apply_case_fields_to_instance(stmt, case, overwrite=True):
                stmt.save()
                updated += 1

        # CertificateOfDivorce
        # Attach any existing CertificateOfDivorce records that aren't linked to this case
        attached_ids = []
        if case.court_file_number:
            matches = CertificateOfDivorce.objects.filter(case_file__isnull=True, court_file_number=case.court_file_number)
            for a in matches:
                a.case_file = case
                a.save()
                attached_ids.append(a.pk)
                updated += 1

        # Apply case fields to already-linked certificates (exclude ones we just attached to avoid double-counting)
        for stmt in case.certificates_of_divorce.exclude(pk__in=attached_ids):
            if _apply_case_fields_to_instance(stmt, case, overwrite=True):
                stmt.save()
                updated += 1

        # DivorceOrder
        attached_ids = []
        if case.court_file_number:
            matches = DivorceOrder.objects.filter(case_file__isnull=True, court_file_number=case.court_file_number)
            for a in matches:
                a.case_file = case
                a.save()
                attached_ids.append(a.pk)
                updated += 1

        for stmt in case.divorce_orders.exclude(pk__in=attached_ids):
            if _apply_case_fields_to_instance(stmt, case, overwrite=True):
                stmt.save()
                updated += 1

        # AffidavitOfService
        # Attach any existing AffidavitOfService records that aren't linked to this case
        attached_ids = []
        if case.court_file_number:
            matches = AffidavitOfService.objects.filter(case_file__isnull=True, court_file_number=case.court_file_number)
            for a in matches:
                a.case_file = case
                a.save()
                attached_ids.append(a.pk)
                updated += 1

        # Apply case fields to already-linked affidavits (exclude ones we just attached to avoid double-counting)
        for stmt in case.affidavits_of_service.exclude(pk__in=attached_ids):
            if _apply_case_fields_to_instance(stmt, case, overwrite=True):
                stmt.save()
                updated += 1

    messages.success(request, f"Pushed case data to {updated} related forms.")
    log_audit(request, 'update', 'case', case.pk, f"Push Case #{case.pk}", f"Pushed data to {updated} related forms")
    return redirect('case_detail', pk=case.pk)
from django.contrib.auth.decorators import login_required
from .forms import (
    # Single-page forms
    NetFamilyPropertyStatementForm,
    FinancialStatementForm,

    # 13B forms
    NetFamilyProperty13BForm,
    NetFamilyProperty13BAssetForm,
    NetFamilyProperty13BDebtForm,
    NetFamilyProperty13BMarriagePropertyForm,
    NetFamilyProperty13BMarriageDebtForm,
    NetFamilyProperty13BExcludedForm,
    NetFamilyProperty13BFinalTotalsForm,

    # Comparison NFP (page 1 + page 2)
    ComparisonNetFamilyPropertyForm,
    ComparisonNetFamilyPropertyHouseholdItemForm,
    ComparisonNetFamilyPropertyBankAccountForm,
    ComparisonNetFamilyPropertyInsuranceForm,
    ComparisonNetFamilyPropertyBusinessForm,

    # Form 13C forms (page 3 & 4)
    Form13CAssetForm,
    Form13CMoneyOwedForm,
    Form13COtherPropertyForm,
    Form13CDebtLiabilityForm,
    Form13CMarriagePropertyForm,
    Form13CExcludedPropertyForm,
    Form13CFinalTotalsForm,
    Form13CComparisonForm,
    Form13CGeneralHouseholdItemForm,
    Form13CBusinessInterestForm,
    AffidavitOfServiceForm,
    CertificateOfDivorceForm,
    ApplicationDivorce8APage1Form,
    ApplicationDivorce8APage2Form,
    ApplicationDivorce8APage3Form,
    ApplicationDivorce8APage4Form,
    ApplicationDivorce8APage5Form,
    ApplicationDivorce8APage6Form,
)


from decimal import Decimal, InvalidOperation

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def parse_decimal(value):
    """Safely parse a decimal value from form input."""
    if value is None or value == '':
        return None
    try:
        # Remove any commas and dollar signs
        clean_value = str(value).replace(',', '').replace('$', '').strip()
        if clean_value == '':
            return None
        return Decimal(clean_value)
    except (InvalidOperation, ValueError):
        return None


def parse_date(value):
    """Safely parse a date value from form input."""
    if value is None or value == '':
        return None
    return value

def calculate_equalisation(total6_app, total6_resp):
    """
    Equalisation = (Highest Net Family Property - Lowest Net Family Property) / 2
    """
    total6_app = float(total6_app or 0)
    total6_resp = float(total6_resp or 0)

    highest = max(total6_app, total6_resp)
    lowest = min(total6_app, total6_resp)

    amount = round((highest - lowest) / 2, 2)

    if total6_app > total6_resp:
        payer = "Applicant"
        receiver = "Respondent"
    elif total6_resp > total6_app:
        payer = "Respondent"
        receiver = "Applicant"
    else:
        payer = "None"
        receiver = "None"

    return {
        "amount": amount,
        "payer": payer,
        "receiver": receiver,
    }


# ============================================================
# DASHBOARD
# ============================================================
@login_required
def dashboard(request):
    """Main dashboard showing all form types."""

    from .models import (
        FinancialStatement,
        Form131FinancialStatement,
        NetFamilyProperty13B,
        ComparisonNetFamilyProperty,
        AffidavitOfService,
        ApplicationDivorce8A,
        CertificateOfDivorce,
        DivorceOrder,
    )

    # =========================
    # FORM QUERIES
    # =========================

    financial_statements = FinancialStatement.objects.all().order_by("-updated_at")

    financial_statements_131 = (
        Form131FinancialStatement.objects.all()
        .order_by("-updated_at")
    )

    net_family_13b = (
        NetFamilyProperty13B.objects.all()
        .order_by("-updated_at")
    )

    comparison_nfp = (
        ComparisonNetFamilyProperty.objects.all()
        .order_by("-updated_at")
    )

    affidavits = (
        AffidavitOfService.objects.all()
        .order_by("-updated_at")
    )

    application_divorce_8a = (
        ApplicationDivorce8A.objects.all()
        .order_by("-updated_at")
    )

    certificates = (
        CertificateOfDivorce.objects.all()
        .order_by("-updated_at")
    )

    divorce_orders = (
        DivorceOrder.objects.all()
        .order_by("-updated_at")
    )

    # =========================
    # CONTEXT
    # =========================

    context = {

        # -------------------------
        # Financial Statement (13)
        # -------------------------
        "financial_statements": financial_statements[:5],
        "financial_statements_count": financial_statements.count(),

        # -------------------------
        # Financial Statement (13.1)
        # -------------------------
        "financial_statements_131": financial_statements_131[:5],
        "financial_statements_131_count": financial_statements_131.count(),

        # -------------------------
        # Net Family Property (13B)
        # -------------------------
        "net_family_13b": net_family_13b[:5],
        "net_family_13b_count": net_family_13b.count(),

        # -------------------------
        # Comparison NFP (13C)
        # -------------------------
        "comparison_nfp": comparison_nfp[:5],
        "comparison_nfp_count": comparison_nfp.count(),

        # -------------------------
        # Affidavit of Service (6B)
        # -------------------------
        "affidavits": affidavits[:5],
        "affidavits_count": affidavits.count(),

        # -------------------------
        # Divorce Application (8A)
        # -------------------------
        "application_divorce_8a": application_divorce_8a[:5],
        "application_divorce_8a_count": application_divorce_8a.count(),

        # -------------------------
        # Certificate of Divorce (36B)
        # -------------------------
        "certificates": certificates[:5],
        "certificates_count": certificates.count(),

        # -------------------------
        # Divorce Order (25A)
        # -------------------------
        "divorce_orders": divorce_orders[:5],
        "divorce_orders_count": divorce_orders.count(),

        # -------------------------
        # Total Forms
        # -------------------------
        "total_forms": (

            financial_statements.count()

            + financial_statements_131.count()

            + net_family_13b.count()

            + comparison_nfp.count()

            + affidavits.count()

            + application_divorce_8a.count()

            + certificates.count()

            + divorce_orders.count()

        ),
    }

    return render(
        request,
        "forms/dashboard.html",
        context
    )



# ============================================================
# FINANCIAL STATEMENT (FORM 13.1) - Property & Support Claims (Page 1)
# ============================================================

@csrf_exempt
@login_required
def financial_statement_131_page1_new(request):
    """View for Form 13.1 - Page 1 (new form creation)."""
    # Support prefill from CaseFile via ?case_id=
    case = None
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    if case_id:
        try:
            case = CaseFile.objects.get(pk=case_id, owner=request.user)
        except CaseFile.DoesNotExist:
            case = None

    if request.method == "POST":
        from .models import Form131FinancialStatement
        statement = Form131FinancialStatement.objects.create(draft={})
        posted_data = request.POST
        resolved_court_file_number = _resolve_form131_court_file_number(
            statement,
            posted_data.get('court_file_number', ''),
        )
        # Save all page1 fields from POST
        data = {k: v for k, v in posted_data.items() if k != 'csrfmiddlewaretoken'}
        data['court_file_number'] = resolved_court_file_number
        # Handle checkboxes
        for cb in ['filed_by_applicant', 'filed_by_respondent', 'employed', 'self_employed', 'unemployed']:
            data[cb] = cb in posted_data
        statement.court_file_number = data['court_file_number']
        statement.applicant_name = data.get('applicant_name', '')
        statement.respondent_name = data.get('respondent_name', '')
        # Attach case if provided and copy case fields where blank
        if case:
            statement.case_file = case
            changed = _apply_case_fields_to_instance(statement, case, overwrite=False)
            if changed or statement.case_file_id != case.pk:
                statement.save()
        statement.save_page_data(1, data)
        
        # Send email notification for new form
        send_form_created_notification('financial_statement_131', statement, request.user)
        
        # Audit log for creation
        log_audit(request, 'create', 'financial_statement_131', statement.pk, 
                  f"Form 13.1 #{statement.pk}", 
                  f"Created - Applicant: {statement.applicant_name or 'N/A'}")
        
        return redirect("financial_statement_131_page2", pk=statement.id)
    # For GET, provide page_data initial values from case if present
    page_data = {}
    if case:
        page_data = _build_case_initial(case)

    case_list = CaseFile.objects.filter(owner=request.user)
    return render(request, "forms/financial_statement_131_page1.html", {
        "page_data": page_data,
        "case_list": case_list,
        "selected_case": case,
    })


# ============================================================
# FINANCIAL STATEMENT (FORM 13.1) - List, Edit, Print (Placeholders)
# ============================================================
@login_required
def financial_statement_131_list(request):

    statements = Form131FinancialStatement.objects.filter(
        is_deleted=False
    ).order_by("-updated_at")

    perms = user_permissions(request).get(
        "user_permissions",
        {}
    ).get(
        "financial_statement_131",
        {}
    )

    for s in statements:
        s.can_view = request.user.is_superuser or perms.get("view", False)
        s.can_edit = request.user.is_superuser or perms.get("edit", False)
        s.can_print = request.user.is_superuser or perms.get("print", False)
        s.can_delete = request.user.is_superuser or perms.get("delete", False)

    return render(
        request,
        "forms/financial_statement_131_list.html",
        {
            "statements": statements
        }
    )
@csrf_exempt
@login_required
def financial_statement_131_page1(request, pk):
    """Form 13.1 page 1 - Instructions."""
    from .models import Form131FinancialStatement
    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    page_data = _get_form131_page1_data(form, persist=True)
    if request.method == "POST":
        posted_data = request.POST
        resolved_court_file_number = _resolve_form131_court_file_number(
            form,
            posted_data.get('court_file_number', ''),
        )
        # Save all page1 fields from POST
        data = {k: v for k, v in posted_data.items() if k != 'csrfmiddlewaretoken'}
        data['court_file_number'] = resolved_court_file_number
        # Handle checkboxes (they're absent from POST when unchecked)
        for cb in ['filed_by_applicant', 'filed_by_respondent', 'employed', 'self_employed', 'unemployed']:
            data[cb] = cb in posted_data
        # Sync top-level fields for list/summary
        form.court_file_number = resolved_court_file_number
        form.applicant_name = posted_data.get('applicant_name', '')
        form.respondent_name = posted_data.get('respondent_name', '')
        form.save()
        form.save_page_data(1, data)
        return redirect("financial_statement_131_page2", pk=pk)
    return render(request, "forms/financial_statement_131_page1.html", {
        "pk": pk,
        "form": form,
        "statement": form,
        "page_data": page_data,
    })
def get_all_form131_data(form):
    """Merge all page data from draft into a single dict for print/view."""
    merged = {}
    if not form.draft:
        return merged
    for k, v in form.draft.items():
        if isinstance(v, dict):
            merged.update(v)
    return merged


def _resolve_form131_court_file_number(statement, posted_value):
    """Use manual court file number if provided, otherwise keep existing or return empty."""
    manual_value = (posted_value or "").strip()
    if manual_value:
        return manual_value

    existing = (statement.court_file_number or "").strip()
    return existing


def _resolve_application_court_file_number(instance, posted_value=None):
    """Resolve the court file number from POST, existing instance, or associated CaseFile."""
    manual_value = (posted_value or "").strip()
    if manual_value:
        return manual_value

    existing = (getattr(instance, "court_file_number", "") or "").strip()
    if existing:
        return existing

    case_file = getattr(instance, "case_file", None)
    if case_file:
        return (getattr(case_file, "court_file_number", "") or "").strip()

    return ""


CASE_FIELD_TARGETS = {
    "court_file_number": ["court_file_number"],
    "court_name": ["court_name"],
    "court_office_address": ["court_office_address", "court_address"],

    "applicant_name": ["applicant_name"],
    "applicant_address": ["applicant_address"],
    "applicant_phone": ["applicant_phone", "applicant_phone_fax"],
    "applicant_email": ["applicant_email"],

    "applicant_lawyer_name": ["applicant_lawyer_name"],
    "applicant_lawyer_address": ["applicant_lawyer_address"],
    "applicant_lawyer_phone": ["applicant_lawyer_phone", "applicant_lawyer_phone_fax"],
    "applicant_lawyer_email": ["applicant_lawyer_email"],

    "respondent_name": ["respondent_name"],
    "respondent_address": ["respondent_address"],
    "respondent_phone": ["respondent_phone", "respondent_phone_fax"],
    "respondent_email": ["respondent_email"],

    "respondent_lawyer_name": ["respondent_lawyer_name"],
    "respondent_lawyer_address": ["respondent_lawyer_address"],
    "respondent_lawyer_phone": ["respondent_lawyer_phone", "respondent_lawyer_phone_fax"],
    "respondent_lawyer_email": ["respondent_lawyer_email"],

    "valuation_date": ["valuation_date"],
}


def _build_case_initial(case):
    if not case:
        return {}

    initial = {}

    for case_field, targets in CASE_FIELD_TARGETS.items():
        value = getattr(case, case_field, None)

        if value is None:
            value = ""

        for target in targets:
            initial[target] = value

    return initial


def _apply_case_fields_to_instance(instance, case, overwrite=False):
    if not instance or not case:
        return False

    changed = False

    for case_field, targets in CASE_FIELD_TARGETS.items():
        value = getattr(case, case_field, None)

        if value is None:
            value = ""

        for target in targets:
            if not hasattr(instance, target):
                continue

            existing = getattr(instance, target)

            if overwrite:
                if existing != value:
                    setattr(instance, target, value)
                    changed = True
            else:
                if existing in (None, "") and value not in (None, ""):
                    setattr(instance, target, value)
                    changed = True

    return changed

def _remove_div_block(html, class_name):
    """Remove an entire <div class="...class_name..."> block including all nested content.
    Tracks only <div> / </div> depth so other tags don't corrupt the counter.
    """
    start_pat = re.compile(
        r'<div[^>]*\bclass="[^"]*\b' + re.escape(class_name) + r'\b[^"]*"[^>]*>',
        re.IGNORECASE,
    )
    div_open = re.compile(r'<div[\s>]', re.IGNORECASE)
    div_close = re.compile(r'</div\s*>', re.IGNORECASE)
    result = []
    pos = 0
    for m in start_pat.finditer(html):
        if m.start() < pos:
            continue  # already consumed by a previous removal
        result.append(html[pos:m.start()])
        depth = 1
        inner = m.end()
        while inner < len(html) and depth > 0:
            next_open = div_open.search(html, inner)
            next_close = div_close.search(html, inner)
            if next_close is None:
                inner = len(html)
                break
            if next_open is not None and next_open.start() < next_close.start():
                depth += 1
                inner = next_open.end()
            else:
                depth -= 1
                inner = next_close.end()
        pos = inner
    result.append(html[pos:])
    return ''.join(result)


@lru_cache(maxsize=10)
def _get_form131_page_block_html(page_number):
    """Return the pre-processed (style/nav/script stripped) block content for a page template."""
    templates_dir = Path(__file__).resolve().parent / "templates" / "forms"
    template_file = templates_dir / f"financial_statement_131_page{page_number}.html"
    if not template_file.exists():
        return ""
    text = template_file.read_text(encoding="utf-8", errors="ignore")
    # Extract {% block content %} ... {% endblock %}
    m = re.search(r'\{%-?\s*block content\s*-?%\}([\s\S]*?)\{%-?\s*endblock\s*-?%\}', text, re.IGNORECASE)
    html = m.group(1) if m else text
    # Remove style and script blocks
    html = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
    # Remove page-specific chrome (nav, buttons, repeated form header)
    for cls in ('page-nav', 'actions-131', 'form-footer-131', 'form-header-131'):
        html = _remove_div_block(html, cls)
    # Remove form wrapper and csrf token
    html = re.sub(r'<form[^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'</form>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'\{%-?\s*csrf_token\s*-?%\}', '', html)
    html = re.sub(r'<!--[\s\S]*?-->', '', html)
    return html.strip()


def _is_truthy(value):
    """Return True when a saved value represents checked/true."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "on", "checked"}


def _format_form131_value(name, value):
    """Normalize values loaded from JSON draft for cleaner read-only rendering."""
    if value in (None, ""):
        return ""

    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(items)

    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            item_text = str(item).strip()
            if item_text:
                parts.append(f"{key}: {item_text}")
        return "\n".join(parts)

    text = str(value).strip()
    if not text:
        return ""

    # Show DB value exactly as saved - no filtering.
    return text


def _apply_page_data_to_block(block_html, page_data):
    """Substitute actual data values and replace form inputs with read-only divs."""
    page_data = page_data or {}
    html = block_html

    # Replace {{ page_data.field|filter }} with actual values
    def _sub_var(m):
        expr = m.group(1).strip()
        var_part = re.split(r'\|', expr)[0].strip()
        parts = var_part.split('.')
        if len(parts) == 2 and parts[0] == 'page_data':
            val = _format_form131_value(parts[1], page_data.get(parts[1], ''))
            return val if val not in (None, '') else ''
        return ''
    html = re.sub(r'\{\{(.*?)\}\}', _sub_var, html, flags=re.DOTALL)

    # Remove remaining Django template tags
    html = re.sub(r'\{%[^%]*%\}', '', html)

    # Replace checkbox inputs — preserve checked state as disabled checkbox
    def _replace_checkbox(m):
        attrs_str = m.group(1)
        name_m = re.search(r'name="([^"]+)"', attrs_str)
        if not name_m:
            return m.group(0)
        name = name_m.group(1)
        val = page_data.get(name, '')
        checked = _is_truthy(val)
        chk = ' checked' if checked else ''
        return f'<input type="checkbox"{chk} disabled class="readonly-checkbox">'
    html = re.sub(
        r'<input\s([^>]*type=["\']checkbox["\'][^>]*)(/?)>',
        _replace_checkbox, html, flags=re.IGNORECASE,
    )

    # Remove hidden/submit inputs
    html = re.sub(
        r'<input\s[^>]*type=["\'](?:hidden|submit)["\'][^>]*/?>',
        '', html, flags=re.IGNORECASE,
    )

    # Replace radio inputs as disabled radios preserving selected option
    def _replace_radio(m):
        attrs_str = m.group(1)
        name_m = re.search(r'name="([^"]+)"', attrs_str)
        value_m = re.search(r'value="([^"]*)"', attrs_str)
        if not name_m:
            return ''
        name = name_m.group(1)
        option_value = value_m.group(1) if value_m else ''
        selected = str(page_data.get(name, '')).strip() == option_value
        chk = ' checked' if selected else ''
        return f'<input type="radio"{chk} disabled class="readonly-checkbox">'
    html = re.sub(
        r'<input\s([^>]*type=["\']radio["\'][^>]*)(/?)>',
        _replace_radio, html, flags=re.IGNORECASE,
    )

    # Replace remaining inputs with readonly value divs
    def _replace_input(m):
        attrs_str = m.group(1)
        name_m = re.search(r'name="([^"]+)"', attrs_str)
        if not name_m:
            return ''
        name = name_m.group(1)
        if name in ('csrfmiddlewaretoken', 'prev', 'next', 'save'):
            return ''
        val = _format_form131_value(name, page_data.get(name, ''))
        display = val if val not in (None, '') else ''
        cls = 'readonly-value' if display else 'readonly-value empty'
        return f'<div class="{cls}">{display or "—"}</div>'
    html = re.sub(r'<input\s([^>]*)/?>', _replace_input, html, flags=re.IGNORECASE)

    # Replace textarea with readonly div
    def _replace_textarea(m):
        attrs_str = m.group(1)
        name_m = re.search(r'name="([^"]+)"', attrs_str)
        if not name_m:
            return ''
        name = name_m.group(1)
        val = _format_form131_value(name, page_data.get(name, ''))
        display = val if val not in (None, '') else ''
        cls = 'readonly-value' if display else 'readonly-value empty'
        return f'<div class="{cls}" style="min-height:56px;white-space:pre-wrap;">{display or "—"}</div>'
    html = re.sub(
        r'<textarea\s([^>]*)>[\s\S]*?</textarea>',
        _replace_textarea, html, flags=re.IGNORECASE,
    )

    # Replace select with readonly div
    def _replace_select(m):
        attrs_str = m.group(1)
        name_m = re.search(r'name="([^"]+)"', attrs_str)
        if not name_m:
            return ''
        name = name_m.group(1)
        val = _format_form131_value(name, page_data.get(name, ''))
        display = val if val not in (None, '') else ''
        cls = 'readonly-value' if display else 'readonly-value empty'
        return f'<div class="{cls}">{display or "—"}</div>'
    html = re.sub(
        r'<select\s([^>]*)>[\s\S]*?</select>',
        _replace_select, html, flags=re.IGNORECASE,
    )

    return html


@lru_cache(maxsize=1)
def _get_form131_template_meta():
    """Extract expected fields and page headers/subheaders for each Form 13.1 page."""
    templates_dir = Path(__file__).resolve().parent / "templates" / "forms"
    field_pattern = re.compile(r'name="([^"]+)"')
    page_pattern = re.compile(r'_page(\d+)\.html$')

    def _extract_block_text(template_text, block_name):
        pattern = (
            r'\{%-?\s*block\s+' + re.escape(block_name) +
            r'\s*-?%\}([\s\S]*?)\{%-?\s*endblock\s*-?%\}'
        )
        m = re.search(pattern, template_text, re.IGNORECASE)
        if not m:
            return ""
        raw = m.group(1)
        raw = re.sub(r'<[^>]+>', ' ', raw)
        raw = re.sub(r'\{\{[\s\S]*?\}\}|\{%[\s\S]*?%\}', ' ', raw)
        raw = re.sub(r'\s+', ' ', raw).strip()
        return raw

    meta_by_page = {}
    for template_file in sorted(templates_dir.glob("financial_statement_131_page*.html")):
        match = page_pattern.search(template_file.name)
        if not match:
            continue
        page_number = int(match.group(1))
        text = template_file.read_text(encoding="utf-8", errors="ignore")
        names = [
            name
            for name in field_pattern.findall(text)
            if name not in {"csrfmiddlewaretoken", "prev", "next", "save", "submit"}
            and not name.startswith("__prefix__")
            and "${" not in name
        ]
        page_header = _extract_block_text(text, "header")
        page_subheader = _extract_block_text(text, "subheader")
        meta_by_page[page_number] = {
            "fields": list(OrderedDict.fromkeys(names)),
            "header": page_header,
            "subheader": page_subheader,
        }
    return meta_by_page


def _build_form131_page_display_data(page_number, data, expected_fields, page_html="", page_header="", page_subheader=""):
    """Build complete display metadata for a Form 13.1 page."""
    data = data or {}
    expected_fields = expected_fields or []
    populated_count = sum(1 for f in expected_fields if _format_form131_value(f, data.get(f)) not in (None, ''))
    missing_count = max(len(expected_fields) - populated_count, 0)
    extra_saved_count = max(len(data) - len(expected_fields), 0)
    return {
        "number": page_number,
        "key": f"page{page_number}",
        "data": data,
        "has_data": bool(data),
        "field_count": len(data),
        "expected_field_count": len(expected_fields),
        "populated_count": populated_count,
        "missing_count": missing_count,
        "extra_saved_count": extra_saved_count,
        "page_header": page_header,
        "page_subheader": page_subheader,
        "html": page_html,
    }


def _get_form131_page1_data(statement, persist=False):
    """Return page1 data with fallback to top-level fields for legacy records."""
    page1 = statement.get_page_data(1) or {}
    merged = dict(page1)
    changed = False

    # Only use fields that exist on Form131FinancialStatement model
    fallback_fields = [
        "court_file_number",
        "applicant_name",
        "respondent_name",
    ]

    for field_name in fallback_fields:
        if not merged.get(field_name):
            value = getattr(statement, field_name, None)
            if value:
                merged[field_name] = value
                changed = True

    if persist and changed:
        statement.save_page_data(1, merged)

    return merged

@csrf_exempt
@login_required
def financial_statement_131_page2(request, pk):
    """Form 13.1 page 2."""
    from .models import Form131FinancialStatement
    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    page_data = form.get_page_data(2)
    if request.method == "POST":
        # Example: save all POSTed fields for page 2
        data = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
        form.save_page_data(2, data)
        if "prev" in request.POST:
            return redirect("financial_statement_131_page1", pk=pk)
        return redirect("financial_statement_131_page3", pk=pk)
    return render(request, "forms/financial_statement_131_page2.html", {"pk": pk, "form": form, "statement": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

@csrf_exempt
@login_required
def financial_statement_131_page3(request, pk):
    """Form 13.1 page 3."""
    from .models import Form131FinancialStatement
    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    page_data = form.get_page_data(3)
    if request.method == "POST":
        data = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
        form.save_page_data(3, data)
        if "prev" in request.POST:
            return redirect("financial_statement_131_page2", pk=pk)
        return redirect("financial_statement_131_page4", pk=pk)
    return render(request, "forms/financial_statement_131_page3.html", {"pk": pk, "form": form, "statement": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

@csrf_exempt
@login_required
def financial_statement_131_page4(request, pk):
    """Form 13.1 page 4."""
    from .models import Form131FinancialStatement
    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    page_data = form.get_page_data(4)
    if request.method == "POST":
        data = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
        form.save_page_data(4, data)
        if "prev" in request.POST:
            return redirect("financial_statement_131_page3", pk=pk)
        return redirect("financial_statement_131_page5", pk=pk)
    return render(request, "forms/financial_statement_131_page4.html", {"pk": pk, "form": form, "statement": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

@csrf_exempt
@login_required
def financial_statement_131_page5(request, pk):
    """Form 13.1 page 5."""
    from .models import Form131FinancialStatement
    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    page_data = form.get_page_data(5)
    if request.method == "POST":
        data = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
        form.save_page_data(5, data)
        if "prev" in request.POST:
            return redirect("financial_statement_131_page4", pk=pk)
        return redirect("financial_statement_131_page6", pk=pk)
    return render(request, "forms/financial_statement_131_page5.html", {"pk": pk, "form": form, "statement": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

@csrf_exempt
@login_required
def financial_statement_131_page6(request, pk):
    """Form 13.1 page 6."""
    from .models import Form131FinancialStatement
    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    page_data = form.get_page_data(6)
    if request.method == "POST":
        data = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
        form.save_page_data(6, data)
        if "prev" in request.POST:
            return redirect("financial_statement_131_page5", pk=pk)
        return redirect("financial_statement_131_page7", pk=pk)
    return render(request, "forms/financial_statement_131_page6.html", {"pk": pk, "form": form, "statement": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

@csrf_exempt
@login_required
def financial_statement_131_page7(request, pk):
    """Form 13.1 page 7."""
    from .models import Form131FinancialStatement
    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    page_data = form.get_page_data(7)
    if request.method == "POST":
        data = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
        form.save_page_data(7, data)
        if "prev" in request.POST:
            return redirect("financial_statement_131_page6", pk=pk)
        return redirect("financial_statement_131_page8", pk=pk)
    return render(request, "forms/financial_statement_131_page7.html", {"pk": pk, "form": form, "statement": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

@csrf_exempt
@login_required
def financial_statement_131_page8(request, pk):
    """Form 13.1 page 8."""
    from .models import Form131FinancialStatement
    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    page_data = form.get_page_data(8)
    if request.method == "POST":
        data = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
        form.save_page_data(8, data)
        if "prev" in request.POST:
            return redirect("financial_statement_131_page7", pk=pk)
        return redirect("financial_statement_131_page9", pk=pk)
    return render(request, "forms/financial_statement_131_page8.html", {"pk": pk, "form": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

@csrf_exempt
@login_required
def financial_statement_131_page9(request, pk):
    """Form 13.1 page 9."""
    from .models import Form131FinancialStatement

    form = get_object_or_404(Form131FinancialStatement, pk=pk)

    pages = _calculate_form131_totals(form.draft or {})
    page_data = pages.get("page9", {}) or {}

    # Save calculated Page 9 values back into draft
    form.draft = pages
    form.save()

    if request.method == "POST":
        data = {
            k: v
            for k, v in request.POST.items()
            if k != "csrfmiddlewaretoken"
        }

        # Force calculated values, not manual/browser values
        data["nfp_item22"] = page_data.get("nfp_item22", "0.00")
        data["nfp_item25"] = page_data.get("nfp_item25", "0.00")
        data["nfp_item26"] = page_data.get("nfp_item26", "0.00")
        data["nfp_balance1"] = page_data.get("nfp_balance1", "0.00")
        data["nfp_balance2"] = page_data.get("nfp_balance2", "0.00")
        data["net_family_property"] = page_data.get("net_family_property", "0.00")

        form.save_page_data(9, data)

        if "prev" in request.POST:
            return redirect("financial_statement_131_page8", pk=pk)

        return redirect("financial_statement_131_page10", pk=pk)

    return render(request, "forms/financial_statement_131_page9.html", {
        "pk": pk,
        "form": form,
        "page_data": page_data,
        "page1_data": form.get_page_data(1),
    })

@csrf_exempt
@login_required
def financial_statement_131_page10(request, pk):
    """Form 13.1 page 10 - Schedule A & B."""
    from .models import Form131FinancialStatement

    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    page_data = form.get_page_data(10) or {}

    if request.method == "POST":
        data = {
            k: v
            for k, v in request.POST.items()
            if k != "csrfmiddlewaretoken"
        }

        data["schedule_b_i_earn_checked"] = (
            "on" if "schedule_b_i_earn_checked" in request.POST else ""
        )

        data["schedule_b_i_earn_amount"] = request.POST.get(
            "schedule_b_i_earn_amount",
            ""
        )

        form.save_page_data(10, data)

        if "prev" in request.POST:
            return redirect("financial_statement_131_page9", pk=pk)

        return redirect("financial_statement_131_list")

    return render(request, "forms/financial_statement_131_page10.html", {
        "pk": pk,
        "form": form,
        "page_data": page_data,
        "page1_data": form.get_page_data(1),
    })

@login_required
def financial_statement_list(request):
    """List all financial statements."""
    # require module view permission
    if not _user_has_permission_or_owner(request.user, 'financial_statement', 'view'):
        messages.error(request, "You don't have permission to view Financial Statements.")
        return redirect('dashboard')

    statements = FinancialStatement.objects.all().order_by('-updated_at')
    
    # Pre-calculate permissions for each statement
    perms = user_permissions(request).get('user_permissions', {}).get('financial_statement', {})
    for stmt in statements:
        stmt.can_view = request.user.is_superuser or perms.get('view', False)
        stmt.can_edit = request.user.is_superuser or perms.get('edit', False)
        stmt.can_print = request.user.is_superuser or perms.get('print', False)
        stmt.can_delete = request.user.is_superuser or perms.get('delete', False)
    
    return render(request, "forms/financial_statement_list.html", {"statements": statements})


@login_required
@require_http_methods(["GET", "POST"])
def financial_statement_delete(request, pk):
    """Soft delete a financial statement (move to recycle bin)."""
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)
    # enforce delete permission or staff/superuser or owner
    if not (request.user.is_superuser or request.user.is_staff or _user_has_permission_or_owner(request.user, 'financial_statement', 'delete', instance=statement)):
        messages.error(request, "You don't have permission to delete this Financial Statement.")
        return redirect('financial_statement_view', pk=pk)

    if request.method == "POST":
        statement.soft_delete()
        log_audit(request, 'delete', 'financial_statement', pk, 
              f"Financial Statement #{pk}", 
              f"Moved to recycle bin - Applicant: {statement.applicant_name or 'N/A'}")
        return redirect("financial_statement_list")
    return render(request, "forms/confirm_delete.html", {
        "object": statement,
        "object_name": f"Financial Statement #{statement.id}",
        "cancel_url": "financial_statement_list",
    })


def financial_statement_page1_redirect(request):
    """Redirect old URL to dashboard."""
    return HttpResponseRedirect('/forms/dashboard/')

@login_required
def financial_statement_page1_new(request):
    """
    Create a new Financial Statement Form 13.
    Saves Page 1 into FinancialStatement.draft["page1"].
    Does not call old _save_page1_fields().
    """

    case = None
    case_id = request.GET.get("case_id") or request.POST.get("case_id")

    if case_id:
        case = CaseFile.objects.filter(
            pk=case_id,
            owner=request.user
        ).first()

    if not _user_has_permission_or_owner(request.user, "financial_statement", "create"):
        messages.error(request, "You don't have permission to create Financial Statements.")
        return redirect("financial_statement_list")

    checkbox_fields = [
        "is_employed",
        "is_self_employed",
        "is_unemployed",
    ]

    if request.method == "POST":
        statement = FinancialStatement.objects.create()

        if case:
            statement.case_file = case

        data = clean_form13_post(request, checkbox_fields)

        if case:
            case_data = _build_case_initial(case)

            for key, value in case_data.items():
                if not data.get(key):
                    data[key] = value

        statement.save_page_data(1, data)

        statement.court_file_number = data.get("court_file_number") or statement.court_file_number
        statement.court_name = data.get("court_name") or statement.court_name
        statement.court_office_address = data.get("court_office_address") or statement.court_office_address
        statement.applicant_name = data.get("applicant_name") or statement.applicant_name
        statement.respondent_name = data.get("respondent_name") or statement.respondent_name
        statement.save()

        send_form_created_notification(
            "financial_statement",
            statement,
            request.user
        )

        log_audit(
            request,
            "create",
            "financial_statement",
            statement.pk,
            f"Form 13 #{statement.pk}",
            f"Created - Applicant: {statement.applicant_name or 'N/A'}"
        )

        return redirect("financial_statement_page2", pk=statement.pk)

    page_data = {}

    if case:
        page_data = _build_case_initial(case)

    case_list = CaseFile.objects.filter(
        owner=request.user
    ).order_by("-updated_at")

    return render(request, "forms/financial_statement_page1.html", {
        "statement": None,
        "page_data": page_data,
        "case_list": case_list,
        "selected_case": case,
    })


# ============================================================
# SAFE EDIT HELPERS — DO NOT DELETE SAVED DATA ON EDIT
# ============================================================

def update_if_present(obj, post_data, field, parser=None):
    if field in post_data:
        value = post_data.get(field)

        if parser:
            value = parser(value)

        setattr(obj, field, value)


def update_checkbox(obj, post_data, field):
    setattr(obj, field, field in post_data)


def _ajax_or_redirect(request, redirect_url):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect(redirect_url)


def _json_rows_from_post(request, prefix, fields, max_rows=20):
    rows = []

    for i in range(1, max_rows + 1):
        row = {}
        has_data = False
        row_was_posted = False

        for form_field, json_key in fields.items():
            key = f"{prefix}_{form_field}_{i}"

            if key in request.POST:
                row_was_posted = True
                value = request.POST.get(key, "")
                row[json_key] = value

                if value not in ("", None):
                    has_data = True

        if row_was_posted and has_data:
            rows.append(row)

    return rows


def save_json_if_rows_posted(obj, request, model_field, prefix, fields, max_rows=20):
    any_key_posted = False

    for i in range(1, max_rows + 1):
        for form_field in fields.keys():
            if f"{prefix}_{form_field}_{i}" in request.POST:
                any_key_posted = True
                break

        if any_key_posted:
            break

    if any_key_posted:
        rows = _json_rows_from_post(request, prefix, fields, max_rows=max_rows)
        setattr(obj, model_field, rows)


def unpack_json_rows(context, json_data, prefix, fields, max_rows=20):
    if not json_data:
        return context

    for i, row in enumerate(json_data[:max_rows], 1):
        for form_field, json_key in fields.items():
            context[f"{prefix}_{form_field}_{i}"] = row.get(json_key, "")

    return context

def make_json_safe(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if value is None:
        return ""

    return value


def clean_form13_post(request, checkbox_fields=None):
    data = request.POST.dict()

    data.pop("csrfmiddlewaretoken", None)
    data.pop("prev", None)
    data.pop("next", None)

    checkbox_fields = checkbox_fields or []

    for field in checkbox_fields:
        data[field] = field in request.POST

    safe_data = {}

    for key, value in data.items():
        safe_data[key] = make_json_safe(value)

    return safe_data


@login_required
def financial_statement_page1(request, pk):
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)

    checkbox_fields = [
        "is_employed",
        "is_self_employed",
        "is_unemployed",
    ]

    if request.method == "POST":
        data = clean_form13_post(request, checkbox_fields)
        statement.save_page_data(1, data)

        statement.court_file_number = data.get("court_file_number") or statement.court_file_number
        statement.court_name = data.get("court_name") or statement.court_name
        statement.court_office_address = data.get("court_office_address") or statement.court_office_address
        statement.applicant_name = data.get("applicant_name") or statement.applicant_name
        statement.respondent_name = data.get("respondent_name") or statement.respondent_name
        statement.save()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Page 1 saved"})

        return redirect("financial_statement_page2", pk=statement.pk)

    return render(request, "forms/financial_statement_page1.html", {
        "statement": statement,
        "page_data": statement.get_page_data(1),
        "pk": statement.pk,
    })


@login_required
def financial_statement_page2(request, pk):
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)

    checkbox_fields = [
        "pay_cheque_stub",
        "social_assistance_stub",
        "pension_stub",
        "workers_comp_stub",
        "ei_stub",
        "statement_of_income",
        "other_income_proof",
        "indian_status",
    ]

    if request.method == "POST":
        data = clean_form13_post(request, checkbox_fields)
        statement.save_page_data(2, data)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Page 2 saved"})

        if "prev" in request.POST:
            return redirect("financial_statement_page1", pk=statement.pk)

        return redirect("financial_statement_page3", pk=statement.pk)

    return render(request, "forms/financial_statement_page2.html", {
        "statement": statement,
        "page_data": statement.get_page_data(2),
        "pk": statement.pk,
    })


@login_required
def financial_statement_page3(request, pk):
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)

    if request.method == "POST":
        data = clean_form13_post(request)
        statement.save_page_data(3, data)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Page 3 saved"})

        if "prev" in request.POST:
            return redirect("financial_statement_page2", pk=statement.pk)

        return redirect("financial_statement_page4", pk=statement.pk)

    return render(request, "forms/financial_statement_page3.html", {
        "statement": statement,
        "page_data": statement.get_page_data(3),
        "pk": statement.pk,
    })


@login_required
def financial_statement_page4(request, pk):
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)

    if request.method == "POST":
        data = clean_form13_post(request)
        statement.save_page_data(4, data)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Page 4 saved"})

        if "prev" in request.POST:
            return redirect("financial_statement_page3", pk=statement.pk)

        return redirect("financial_statement_page5", pk=statement.pk)

    return render(request, "forms/financial_statement_page4.html", {
        "statement": statement,
        "page_data": statement.get_page_data(4),
        "pk": statement.pk,
    })


@login_required
def financial_statement_page5(request, pk):
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)

    if request.method == "POST":
        data = clean_form13_post(request)
        statement.save_page_data(5, data)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Page 5 saved"})

        if "prev" in request.POST:
            return redirect("financial_statement_page4", pk=statement.pk)

        return redirect("financial_statement_page6", pk=statement.pk)

    return render(request, "forms/financial_statement_page5.html", {
        "statement": statement,
        "page_data": statement.get_page_data(5),
        "pk": statement.pk,
    })


@login_required
def financial_statement_page6(request, pk):
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)

    if request.method == "POST":
        data = clean_form13_post(request)
        statement.save_page_data(6, data)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Page 6 saved"})

        if "prev" in request.POST:
            return redirect("financial_statement_page5", pk=statement.pk)

        return redirect("financial_statement_page7", pk=statement.pk)

    return render(request, "forms/financial_statement_page6.html", {
        "statement": statement,
        "page_data": statement.get_page_data(6),
        "pk": statement.pk,
    })


@login_required
def financial_statement_page7(request, pk):
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)

    checkbox_fields = [
        "lives_alone",
        "living_with_someone",
        "lives_with_other_adults",
        "has_children_in_home",
        "spouse_works",
        "spouse_does_not_work",
        "spouse_earns_income",
        "spouse_no_income",
        "household_contribution",
    ]

    if request.method == "POST":
        data = clean_form13_post(request, checkbox_fields)
        statement.save_page_data(7, data)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Page 7 saved"})

        if "prev" in request.POST:
            return redirect("financial_statement_page6", pk=statement.pk)

        return redirect("financial_statement_page8", pk=statement.pk)

    return render(request, "forms/financial_statement_page7.html", {
        "statement": statement,
        "page_data": statement.get_page_data(7),
        "pk": statement.pk,
    })


@login_required
def financial_statement_page8(request, pk):
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)

    checkbox_fields = [
        "schedule_c_income_share_checked",
    ]

    if request.method == "POST":
        data = clean_form13_post(request, checkbox_fields)
        statement.save_page_data(8, data)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Page 8 saved"})

        if "prev" in request.POST:
            return redirect("financial_statement_page7", pk=statement.pk)

        return redirect("financial_statement_list")

    return render(request, "forms/financial_statement_page8.html", {
        "statement": statement,
        "page_data": statement.get_page_data(8),
        "pk": statement.pk,
    })

@login_required
def financial_statement_view(request, pk):
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)

    draft = statement.draft or {}

    context = {
        "statement": statement,

        "page1": draft.get("page1", {}),
        "page2": draft.get("page2", {}),
        "page3": draft.get("page3", {}),
        "page4": draft.get("page4", {}),
        "page5": draft.get("page5", {}),
        "page6": draft.get("page6", {}),
        "page7": draft.get("page7", {}),
        "page8": draft.get("page8", {}),
    }

    return render(
        request,
        "forms/financial_statement_view.html",
        context
    )
@login_required
def financial_statement_print(request, pk):
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)

    draft = statement.draft or {}

    page1 = draft.get("page1", {})
    page2 = draft.get("page2", {})
    page3 = draft.get("page3", {})
    page4 = draft.get("page4", {})
    page5 = draft.get("page5", {})
    page6 = draft.get("page6", {})
    page7 = draft.get("page7", {})
    page8 = draft.get("page8", {})

    pages = {
        "page1": page1,
        "page2": page2,
        "page3": page3,
        "page4": page4,
        "page5": page5,
        "page6": page6,
        "page7": page7,
        "page8": page8,
    }

    def money(value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0

    real_estate = [
        {"details": page4.get("real_estate_details_1", ""), "value": money(page4.get("real_estate_value_1"))},
        {"details": page4.get("real_estate_details_2", ""), "value": money(page4.get("real_estate_value_2"))},
        {"details": page4.get("real_estate_details_3", ""), "value": money(page4.get("real_estate_value_3"))},
    ]

    vehicles = [
        {"details": page4.get("vehicle_details_1", ""), "value": money(page4.get("vehicle_value_1"))},
        {"details": page4.get("vehicle_details_2", ""), "value": money(page4.get("vehicle_value_2"))},
        {"details": page4.get("vehicle_details_3", ""), "value": money(page4.get("vehicle_value_3"))},
    ]

    other_possessions = [
        {"address_where_located": page5.get("possession_address_1", ""), "value": money(page5.get("possession_value_1"))},
        {"address_where_located": page5.get("possession_address_2", ""), "value": money(page5.get("possession_value_2"))},
        {"address_where_located": page5.get("possession_address_3", ""), "value": money(page5.get("possession_value_3"))},
    ]

    investments = [
        {"type_issuer_due_date_shares": page5.get("investment_details_1", ""), "value": money(page5.get("investment_value_1"))},
        {"type_issuer_due_date_shares": page5.get("investment_details_2", ""), "value": money(page5.get("investment_value_2"))},
        {"type_issuer_due_date_shares": page5.get("investment_details_3", ""), "value": money(page5.get("investment_value_3"))},
    ]

    bank_accounts = [
        {"name_address_institution": page5.get("bank_institution_1", ""), "account_number": page5.get("bank_account_number_1", ""), "value": money(page5.get("bank_value_1"))},
        {"name_address_institution": page5.get("bank_institution_2", ""), "account_number": page5.get("bank_account_number_2", ""), "value": money(page5.get("bank_value_2"))},
        {"name_address_institution": page5.get("bank_institution_3", ""), "account_number": page5.get("bank_account_number_3", ""), "value": money(page5.get("bank_value_3"))},
    ]

    savings_plans = [
        {"type_issuer": page5.get("savings_type_1", ""), "account_number": page5.get("savings_account_1", ""), "value": money(page5.get("savings_value_1"))},
        {"type_issuer": page5.get("savings_type_2", ""), "account_number": page5.get("savings_account_2", ""), "value": money(page5.get("savings_value_2"))},
        {"type_issuer": page5.get("savings_type_3", ""), "account_number": page5.get("savings_account_3", ""), "value": money(page5.get("savings_value_3"))},
    ]

    life_insurance = [
        {"type_beneficiary_face_amount": page5.get("insurance_details_1", ""), "cash_surrender_value": money(page5.get("insurance_cash_value_1"))},
        {"type_beneficiary_face_amount": page5.get("insurance_details_2", ""), "cash_surrender_value": money(page5.get("insurance_cash_value_2"))},
        {"type_beneficiary_face_amount": page5.get("insurance_details_3", ""), "cash_surrender_value": money(page5.get("insurance_cash_value_3"))},
    ]

    interest_in_business = [
        {"name_address_of_business": page5.get("business_name_address_1", ""), "value": money(page5.get("business_value_1"))},
        {"name_address_of_business": page5.get("business_name_address_2", ""), "value": money(page5.get("business_value_2"))},
        {"name_address_of_business": page5.get("business_name_address_3", ""), "value": money(page5.get("business_value_3"))},
    ]

    money_owed_to_you = [
        {"name_address_of_debtors": page5.get("money_owed_debtor_1", ""), "value": money(page5.get("money_owed_value_1"))},
        {"name_address_of_debtors": page5.get("money_owed_debtor_2", ""), "value": money(page5.get("money_owed_value_2"))},
        {"name_address_of_debtors": page5.get("money_owed_debtor_3", ""), "value": money(page5.get("money_owed_value_3"))},
    ]

    other_assets = [
        {"description": page5.get("other_asset_description_1", ""), "value": money(page5.get("other_asset_value_1"))},
        {"description": page5.get("other_asset_description_2", ""), "value": money(page5.get("other_asset_value_2"))},
        {"description": page5.get("other_asset_description_3", ""), "value": money(page5.get("other_asset_value_3"))},
    ]

    mortgages_loans = [
        {"creditor": page6.get("mortgage_creditor_1", ""), "full_amount": money(page6.get("mortgage_amount_1")), "monthly_payment": money(page6.get("mortgage_monthly_1")), "payments_made": page6.get("mortgage_payment_1") == "yes"},
        {"creditor": page6.get("mortgage_creditor_2", ""), "full_amount": money(page6.get("mortgage_amount_2")), "monthly_payment": money(page6.get("mortgage_monthly_2")), "payments_made": page6.get("mortgage_payment_2") == "yes"},
        {"creditor": page6.get("mortgage_creditor_3", ""), "full_amount": money(page6.get("mortgage_amount_3")), "monthly_payment": money(page6.get("mortgage_monthly_3")), "payments_made": page6.get("mortgage_payment_3") == "yes"},
        {"creditor": page6.get("mortgage_creditor_4", ""), "full_amount": money(page6.get("mortgage_amount_4")), "monthly_payment": money(page6.get("mortgage_monthly_4")), "payments_made": page6.get("mortgage_payment_4") == "yes"},
    ]

    credit_cards = [
        {"creditor": page6.get("credit_card_creditor_1", ""), "full_amount": money(page6.get("credit_card_amount_1")), "monthly_payment": money(page6.get("credit_card_monthly_1")), "payments_made": page6.get("credit_card_payment_1") == "yes"},
        {"creditor": page6.get("credit_card_creditor_2", ""), "full_amount": money(page6.get("credit_card_amount_2")), "monthly_payment": money(page6.get("credit_card_monthly_2")), "payments_made": page6.get("credit_card_payment_2") == "yes"},
    ]

    unpaid_support = [
        {"creditor": page6.get("unpaid_support_creditor", ""), "full_amount": money(page6.get("unpaid_support_amount")), "monthly_payment": money(page6.get("unpaid_support_monthly")), "payments_made": page6.get("unpaid_support_payment") == "yes"},
    ]

    schedule_c_expenses = []
    for i in range(1, 11):
        schedule_c_expenses.append({
            "child_name": page8.get(f"schedule_c_child_name_{i}", ""),
            "expense": page8.get(f"schedule_c_expense_{i}", ""),
            "amount_per_year": money(page8.get(f"schedule_c_amount_year_{i}")),
            "tax_credits": money(page8.get(f"schedule_c_tax_credit_{i}")),
        })

    return render(request, "forms/financial_statement_print.html", {
        "statement": statement,
        "pk": statement.pk,
        "pages": pages,
        "page1": page1,
        "page2": page2,
        "page3": page3,
        "page4": page4,
        "page5": page5,
        "page6": page6,
        "page7": page7,
        "page8": page8,

        "real_estate": real_estate,
        "vehicles": vehicles,
        "other_possessions": other_possessions,
        "investments": investments,
        "bank_accounts": bank_accounts,
        "savings_plans": savings_plans,
        "life_insurance": life_insurance,
        "interest_in_business": interest_in_business,
        "money_owed_to_you": money_owed_to_you,
        "other_assets": other_assets,

        "mortgages_loans": mortgages_loans,
        "credit_cards": credit_cards,
        "unpaid_support": unpaid_support,
        "other_debts": [],

        "schedule_c_expenses": schedule_c_expenses,
        "total_monthly_debt_payments": (
            money(page6.get("mortgage_monthly_1")) +
            money(page6.get("mortgage_monthly_2")) +
            money(page6.get("mortgage_monthly_3")) +
            money(page6.get("mortgage_monthly_4")) +
            money(page6.get("credit_card_monthly_1")) +
            money(page6.get("credit_card_monthly_2")) +
            money(page6.get("unpaid_support_monthly"))
        ),
    })
# ============================================================
# NET FAMILY PROPERTY 13B - 3 PAGES
# ============================================================
@login_required
def net_family_property_13b_list(request):
    forms = NetFamilyProperty13B.objects.filter(
        is_deleted=False
    ).order_by("-updated_at")

    perms = user_permissions(request).get(
        "user_permissions",
        {}
    ).get(
        "net_family_property_13b",
        {}
    )

    for form in forms:
        form.can_view = request.user.is_superuser or perms.get("view", False)
        form.can_edit = request.user.is_superuser or perms.get("edit", False)
        form.can_print = request.user.is_superuser or perms.get("print", False)
        form.can_delete = request.user.is_superuser or perms.get("delete", False)

    return render(request, "forms/net_family_property_13b_list.html", {
        "forms": forms,
    })

@login_required
@require_http_methods(["GET", "POST"])
def net_family_property_13b_delete(request, pk):
    """Soft delete a 13B form (move to recycle bin)."""
    form = get_object_or_404(NetFamilyProperty13B.all_objects, pk=pk)
    if request.method == "POST":
        form.soft_delete()
        log_audit(request, 'delete', 'net_family_property_13b', pk, 
                  f"Net Family Property 13B #{pk}", 
                  f"Moved to recycle bin - Applicant: {form.applicant_name or 'N/A'}")
        return redirect("net_family_property_13b_list")
    return render(request, "forms/confirm_delete.html", {
        "object": form,
        "object_name": f"Net Family Property (13B) #{form.id}",
        "cancel_url": "net_family_property_13b_list",
    })


@login_required
def net_family_property_13b_create_page1(request, pk=None):
    """13B Page 1 - Basic info and Assets."""
    statement = get_object_or_404(NetFamilyProperty13B, pk=pk) if pk else None
    is_new = statement is None  # Track if this is a new form

    AssetFormSet = inlineformset_factory(
        NetFamilyProperty13B,
        NetFamilyProperty13BAsset,
        form=NetFamilyProperty13BAssetForm,
        extra=5,
        can_delete=True,
    )

    # Support pre-filling from an existing CaseFile via ?case_id=<id>
    case = None
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    if case_id:
        try:
            case = CaseFile.objects.get(pk=case_id, owner=request.user)
        except CaseFile.DoesNotExist:
            case = None

    if request.method == "POST":
        form = NetFamilyProperty13BForm(request.POST, instance=statement)
        asset_formset = AssetFormSet(request.POST, instance=statement)

        if form.is_valid() and asset_formset.is_valid():
            statement = form.save()
            if case:
                changed = False
                if not statement.case_file:
                    statement.case_file = case
                    changed = True
                if _apply_case_fields_to_instance(statement, case, overwrite=False):
                    changed = True
                if changed:
                    statement.save()
            asset_formset.instance = statement
            asset_formset.save()
            
            # Send email notification for new form only
            if is_new:
                send_form_created_notification('net_family_property_13b', statement, request.user)
                # Audit log for creation
                log_audit(request, 'create', 'net_family_property_13b', statement.pk, 
                          f"Form 13B #{statement.pk}", 
                          f"Created - Applicant: {statement.applicant_name or 'N/A'}")
            else:
                # Audit log for update
                log_audit(request, 'update', 'net_family_property_13b', statement.pk, 
                          f"Form 13B #{statement.pk}", "Updated Page 1")
            
            return redirect("net_family_property_13b_page2", pk=statement.pk)
    else:
        # If creating a new statement and a case is provided, prefill initial data
        if statement is None and case:
            form = NetFamilyProperty13BForm(instance=statement, initial=_build_case_initial(case))
            asset_formset = AssetFormSet(instance=statement)
        else:
            form = NetFamilyProperty13BForm(instance=statement)
            asset_formset = AssetFormSet(instance=statement)

    # Calculate Total 1 from saved assets
    def sum_field(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total
    
    assets = list(statement.assets.all()) if statement else []
    totals = {
        'total1_app': sum_field(assets, 'applicant_value'),
        'total1_resp': sum_field(assets, 'respondent_value'),
    }

    # Provide case list and selected case to the template for selection/UI
    case_list = CaseFile.objects.filter(owner=request.user) if statement is None else None

    return render(request, "forms/net_family_property_13b_page1.html", {
        "form": form,
        "asset_formset": asset_formset,
        "statement": statement,
        "totals": totals,
        "case_list": case_list,
        "selected_case": case,
    })


@login_required
def net_family_property_13b_create_page2(request, pk):
    """13B Page 2 - Debts and Marriage Property."""
    statement = get_object_or_404(NetFamilyProperty13B, pk=pk)

    DebtFormSet = inlineformset_factory(
        NetFamilyProperty13B,
        NetFamilyProperty13BDebt,
        form=NetFamilyProperty13BDebtForm,
        extra=5,
        can_delete=True,
    )
    MarriagePropertyFormSet = inlineformset_factory(
        NetFamilyProperty13B,
        NetFamilyProperty13BMarriageProperty,
        form=NetFamilyProperty13BMarriagePropertyForm,
        extra=5,
        can_delete=True,
    )
    MarriageDebtFormSet = inlineformset_factory(
        NetFamilyProperty13B,
        NetFamilyProperty13BMarriageDebt,
        form=NetFamilyProperty13BMarriageDebtForm,
        extra=5,
        can_delete=True,
    )

    if request.method == "POST":
        if "prev" in request.POST:
            return redirect("net_family_property_13b_page1_edit", pk=statement.pk)

        debt_formset = DebtFormSet(request.POST, instance=statement, prefix="debt")
        marriage_property_formset = MarriagePropertyFormSet(request.POST, instance=statement, prefix="mprop")
        marriage_debt_formset = MarriageDebtFormSet(request.POST, instance=statement, prefix="mdebt")

        if debt_formset.is_valid() and marriage_property_formset.is_valid() and marriage_debt_formset.is_valid():
            debt_formset.save()
            marriage_property_formset.save()
            marriage_debt_formset.save()
            return redirect("net_family_property_13b_page3", pk=statement.pk)
    else:
        debt_formset = DebtFormSet(instance=statement, prefix="debt")
        marriage_property_formset = MarriagePropertyFormSet(instance=statement, prefix="mprop")
        marriage_debt_formset = MarriageDebtFormSet(instance=statement, prefix="mdebt")

    # Calculate totals from saved data
    def sum_field(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total
    
    debts = list(statement.debts.all())
    marriage_properties = list(statement.marriage_properties.all())
    marriage_debts = list(statement.marriage_debts.all())
    
    marriage_prop_app = sum_field(marriage_properties, 'applicant_value')
    marriage_prop_resp = sum_field(marriage_properties, 'respondent_value')
    marriage_debt_app = sum_field(marriage_debts, 'applicant_value')
    marriage_debt_resp = sum_field(marriage_debts, 'respondent_value')
    
    totals = {
        'total2_app': sum_field(debts, 'applicant_value'),
        'total2_resp': sum_field(debts, 'respondent_value'),
        'mprop_app': marriage_prop_app,
        'mprop_resp': marriage_prop_resp,
        'mdebt_app': marriage_debt_app,
        'mdebt_resp': marriage_debt_resp,
        'total3_app': marriage_prop_app - marriage_debt_app,
        'total3_resp': marriage_prop_resp - marriage_debt_resp,
    }

    return render(request, "forms/net_family_property_13b_page2.html", {
        "debt_formset": debt_formset,
        "marriage_property_formset": marriage_property_formset,
        "marriage_debt_formset": marriage_debt_formset,
        "statement": statement,
        "totals": totals,
        "pk": pk
    })



@login_required
def net_family_property_13b_create_page3(request, pk):
    """13B Page 3 - Excluded Property, Final Totals, and Equalisation Note."""
    statement = get_object_or_404(NetFamilyProperty13B, pk=pk)

    ExcludedFormSet = inlineformset_factory(
        NetFamilyProperty13B,
        NetFamilyProperty13BExcluded,
        form=NetFamilyProperty13BExcludedForm,
        extra=5,
        can_delete=True,
    )

    try:
        final_totals = statement.final_totals
    except Exception:
        final_totals = NetFamilyProperty13BFinalTotals(statement=statement)

    if request.method == "POST":
        if "prev" in request.POST:
            return redirect("net_family_property_13b_page2", pk=pk)

        excluded_formset = ExcludedFormSet(request.POST, instance=statement)

        if excluded_formset.is_valid():
            excluded_formset.save()

            # Save the editable Equalisation textarea note
            final_totals.equalisation_note = request.POST.get("equalisation_note", "")
            final_totals.save()

            return redirect("net_family_property_13b_list")
    else:
        excluded_formset = ExcludedFormSet(instance=statement)

    assets = list(statement.assets.all())
    debts = list(statement.debts.all())
    marriage_properties = list(statement.marriage_properties.all())
    marriage_debts = list(statement.marriage_debts.all())
    excluded_properties = list(statement.excluded_properties.all())

    def sum_field(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total

    totals = {
        "total1_app": sum_field(assets, "applicant_value"),
        "total1_resp": sum_field(assets, "respondent_value"),
        "total2_app": sum_field(debts, "applicant_value"),
        "total2_resp": sum_field(debts, "respondent_value"),
    }

    marriage_prop_app = sum_field(marriage_properties, "applicant_value")
    marriage_prop_resp = sum_field(marriage_properties, "respondent_value")
    marriage_debt_app = sum_field(marriage_debts, "applicant_value")
    marriage_debt_resp = sum_field(marriage_debts, "respondent_value")

    totals["total3_app"] = marriage_prop_app - marriage_debt_app
    totals["total3_resp"] = marriage_prop_resp - marriage_debt_resp
    totals["total4_app"] = sum_field(excluded_properties, "applicant_value")
    totals["total4_resp"] = sum_field(excluded_properties, "respondent_value")
    totals["total5_app"] = totals["total2_app"] + totals["total3_app"] + totals["total4_app"]
    totals["total5_resp"] = totals["total2_resp"] + totals["total3_resp"] + totals["total4_resp"]
    totals["total6_app"] = totals["total1_app"] - totals["total5_app"]
    totals["total6_resp"] = totals["total1_resp"] - totals["total5_resp"]

    equalisation_amount = calculate_equalisation(
        totals["total6_app"],
        totals["total6_resp"]
    )

    return render(request, "forms/net_family_property_13b_page3.html", {
        "excluded_formset": excluded_formset,
        "statement": statement,
        "final_totals": final_totals,
        "totals": totals,
        "equalisation_amount": equalisation_amount,
        "pk": pk,
    })

@login_required
def net_family_property_13b_view(request, pk):
    """Full view of a Net Family Property 13B form."""
    statement = get_object_or_404(NetFamilyProperty13B, pk=pk)

    assets = list(statement.assets.all())
    debts = list(statement.debts.all())
    marriage_properties = list(statement.marriage_properties.all())
    marriage_debts = list(statement.marriage_debts.all())
    excluded_properties = list(statement.excluded_properties.all())

    try:
        final_totals = statement.final_totals
    except Exception:
        final_totals = None

    def sum_field(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total

    totals = {
        "total1_app": sum_field(assets, "applicant_value"),
        "total1_resp": sum_field(assets, "respondent_value"),
        "total2_app": sum_field(debts, "applicant_value"),
        "total2_resp": sum_field(debts, "respondent_value"),
    }

    marriage_prop_app = sum_field(marriage_properties, "applicant_value")
    marriage_prop_resp = sum_field(marriage_properties, "respondent_value")
    marriage_debt_app = sum_field(marriage_debts, "applicant_value")
    marriage_debt_resp = sum_field(marriage_debts, "respondent_value")

    totals["total3_app"] = marriage_prop_app - marriage_debt_app
    totals["total3_resp"] = marriage_prop_resp - marriage_debt_resp
    totals["total4_app"] = sum_field(excluded_properties, "applicant_value")
    totals["total4_resp"] = sum_field(excluded_properties, "respondent_value")
    totals["total5_app"] = totals["total2_app"] + totals["total3_app"] + totals["total4_app"]
    totals["total5_resp"] = totals["total2_resp"] + totals["total3_resp"] + totals["total4_resp"]
    totals["total6_app"] = totals["total1_app"] - totals["total5_app"]
    totals["total6_resp"] = totals["total1_resp"] - totals["total5_resp"]

    equalisation = calculate_equalisation(
    totals["total6_app"],
    totals["total6_resp"]
    )

    return render(request, "forms/net_family_property_13b_view.html", {
        "statement": statement,
        "assets": assets,
        "debts": debts,
        "marriage_properties": marriage_properties,
        "marriage_debts": marriage_debts,
        "excluded_properties": excluded_properties,
        "final_totals": final_totals,
        "totals": totals,
        "equalisation": equalisation,
        "pk": pk,
    })

@login_required
def net_family_property_13b_print(request, pk):
    """Printable version of 13B form."""
    statement = get_object_or_404(NetFamilyProperty13B, pk=pk)

    assets = list(statement.assets.all())
    debts = list(statement.debts.all())
    marriage_properties = list(statement.marriage_properties.all())
    marriage_debts = list(statement.marriage_debts.all())
    excluded_properties = list(statement.excluded_properties.all())

    try:
        final_totals = statement.final_totals
    except Exception:
        final_totals = None

    def sum_field(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total

    totals = {
        "total1_app": sum_field(assets, "applicant_value"),
        "total1_resp": sum_field(assets, "respondent_value"),
        "total2_app": sum_field(debts, "applicant_value"),
        "total2_resp": sum_field(debts, "respondent_value"),
    }

    marriage_prop_app = sum_field(marriage_properties, "applicant_value")
    marriage_prop_resp = sum_field(marriage_properties, "respondent_value")
    marriage_debt_app = sum_field(marriage_debts, "applicant_value")
    marriage_debt_resp = sum_field(marriage_debts, "respondent_value")

    totals["total3_app"] = marriage_prop_app - marriage_debt_app
    totals["total3_resp"] = marriage_prop_resp - marriage_debt_resp
    totals["total4_app"] = sum_field(excluded_properties, "applicant_value")
    totals["total4_resp"] = sum_field(excluded_properties, "respondent_value")
    totals["total5_app"] = totals["total2_app"] + totals["total3_app"] + totals["total4_app"]
    totals["total5_resp"] = totals["total2_resp"] + totals["total3_resp"] + totals["total4_resp"]
    totals["total6_app"] = totals["total1_app"] - totals["total5_app"]
    totals["total6_resp"] = totals["total1_resp"] - totals["total5_resp"]

    equalisation = calculate_equalisation(
        totals["total6_app"],
        totals["total6_resp"]
    )

    print_event = PrintEvent.log_print(
        user=request.user,
        form_type="net_family_property_13b",
        form_id=pk,
        form_identifier=statement.court_file_number or f"Form 13B #{pk}"
    )

    log_audit(
        request,
        "export",
        "net_family_property_13b",
        pk,
        f"Form 13B #{pk}",
        f"Printed - Price: ${print_event.price_charged}"
    )

    send_form_printed_notification(
        "net_family_property_13b",
        statement,
        request.user,
        print_event.price_charged
    )

    return render(request, "forms/net_family_property_13b_print.html", {
        "statement": statement,
        "assets": assets,
        "debts": debts,
        "marriage_properties": marriage_properties,
        "marriage_debts": marriage_debts,
        "excluded_properties": excluded_properties,
        "final_totals": final_totals,
        "totals": totals,
        "equalisation": equalisation,
        "pk": pk,
    })
# ============================================================
# COMPARISON NFP (FORM 13C) - 5 PAGES
# ============================================================
@login_required
def net_family_property_create(request):
    """Simple NFP form."""
    # Support prefill from CaseFile
    case = None
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    if case_id:
        try:
            case = CaseFile.objects.get(pk=case_id, owner=request.user)
        except CaseFile.DoesNotExist:
            case = None

    if request.method == "POST":
        form = NetFamilyPropertyStatementForm(request.POST)
        if form.is_valid():
            statement = form.save()
            if case:
                changed = False
                if not getattr(statement, 'case_file', None):
                    statement.case_file = case
                    changed = True
                if _apply_case_fields_to_instance(statement, case, overwrite=False):
                    changed = True
                if changed:
                    statement.save()
            messages.success(request, "Net Family Property Statement saved.")
            return redirect("dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        if case:
            form = NetFamilyPropertyStatementForm(initial=_build_case_initial(case))
        else:
            form = NetFamilyPropertyStatementForm()

    case_list = CaseFile.objects.filter(owner=request.user)
    return render(request, "forms/net_family_property_form.html", {"form": form, "case_list": case_list, "selected_case": case})


@login_required
def financial_statement_create(request):
    """Create a new financial statement."""
    # Support prefill from CaseFile
    case = None
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    if case_id:
        try:
            case = CaseFile.objects.get(pk=case_id, owner=request.user)
        except CaseFile.DoesNotExist:
            case = None

    if request.method == "POST":
        form = FinancialStatementForm(request.POST)
        if form.is_valid():
            statement = form.save()
            if case:
                changed = False
                if not getattr(statement, 'case_file', None):
                    statement.case_file = case
                    changed = True
                if _apply_case_fields_to_instance(statement, case, overwrite=False):
                    changed = True
                if changed:
                    statement.save()
            messages.success(request, "Financial Statement created.")
            return redirect("financial_statement_page1", pk=statement.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        if case:
            form = FinancialStatementForm(initial=_build_case_initial(case))
        else:
            form = FinancialStatementForm()

    case_list = CaseFile.objects.filter(owner=request.user)
    return render(request, "forms/financial_statement_page1.html", {"form": form, "case_list": case_list, "selected_case": case})


class ComparisonNetFamilyPropertyListView(ListView):
    model = ComparisonNetFamilyProperty
    template_name = "forms/comparison_nfp_list.html"
    context_object_name = "nfp_list"

    def get_queryset(self):
        return ComparisonNetFamilyProperty.objects.filter(
            is_deleted=False
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        perms = user_permissions(self.request).get(
            "user_permissions",
            {}
        ).get(
            "comparison_nfp",
            {}
        )

        for nfp in context["nfp_list"]:
            nfp.can_view = self.request.user.is_superuser or perms.get("view", False)
            nfp.can_edit = self.request.user.is_superuser or perms.get("edit", False)
            nfp.can_print = self.request.user.is_superuser or perms.get("print", False)
            nfp.can_delete = self.request.user.is_superuser or perms.get("delete", False)

        return context

class ComparisonNetFamilyPropertyDetailView(DetailView):
    model = ComparisonNetFamilyProperty
    template_name = "forms/comparison_nfp_detail.html"
    context_object_name = "nfp"


@login_required
@require_http_methods(["GET", "POST"])
def comparison_nfp_delete(request, pk):
    """Soft delete a Comparison NFP form (move to recycle bin)."""
    nfp = get_object_or_404(ComparisonNetFamilyProperty.all_objects, pk=pk)
    if request.method == "POST":
        nfp.soft_delete()
        log_audit(request, 'delete', 'comparison_nfp', pk, 
                  f"Comparison NFP #{pk}", 
                  f"Moved to recycle bin - Court File: {nfp.court_file_number or 'N/A'}")
        return redirect("comparison_nfp_list")
    return render(request, "forms/confirm_delete.html", {
        "object": nfp,
        "object_name": f"Comparison of NFP #{nfp.id}",
        "cancel_url": "comparison_nfp_list",
    })


# ============================================================
# RECYCLE BIN - View and restore deleted forms
# ============================================================
@login_required
def recycle_bin(request):
    """View all soft-deleted forms."""
    deleted_financial = FinancialStatement.deleted_objects.all().order_by('-deleted_at')
    deleted_13b = NetFamilyProperty13B.deleted_objects.all().order_by('-deleted_at')
    deleted_comparison = ComparisonNetFamilyProperty.deleted_objects.all().order_by('-deleted_at')
    
    return render(request, "forms/recycle_bin.html", {
        "deleted_financial": deleted_financial,
        "deleted_13b": deleted_13b,
        "deleted_comparison": deleted_comparison,
    })


@login_required
@require_http_methods(["POST"])
def restore_form(request, form_type, pk):
    """Restore a soft-deleted form."""
    if form_type == "financial":
        obj = get_object_or_404(FinancialStatement.deleted_objects, pk=pk)
        obj.restore()
        log_audit(request, 'update', 'financial_statement', pk, 
                  f"Financial Statement #{pk}", "Restored from recycle bin")
        return redirect("recycle_bin")
    elif form_type == "13b":
        obj = get_object_or_404(NetFamilyProperty13B.deleted_objects, pk=pk)
        obj.restore()
        log_audit(request, 'update', 'net_family_property_13b', pk, 
                  f"Net Family Property 13B #{pk}", "Restored from recycle bin")
        return redirect("recycle_bin")
    elif form_type == "comparison":
        obj = get_object_or_404(ComparisonNetFamilyProperty.deleted_objects, pk=pk)
        obj.restore()
        log_audit(request, 'update', 'comparison_nfp', pk, 
                  f"Comparison NFP #{pk}", "Restored from recycle bin")
        return redirect("recycle_bin")
    return redirect("recycle_bin")


@login_required
@require_http_methods(["GET", "POST"])
def permanent_delete(request, form_type, pk):
    """Permanently delete a form from recycle bin."""
    if form_type == "financial":
        obj = get_object_or_404(FinancialStatement.deleted_objects, pk=pk)
        object_name = f"Financial Statement #{obj.id}"
        module_name = 'financial_statement'
    elif form_type == "13b":
        obj = get_object_or_404(NetFamilyProperty13B.deleted_objects, pk=pk)
        object_name = f"Net Family Property (13B) #{obj.id}"
        module_name = 'net_family_property_13b'
    elif form_type == "comparison":
        obj = get_object_or_404(ComparisonNetFamilyProperty.deleted_objects, pk=pk)
        object_name = f"Comparison of NFP #{obj.id}"
        module_name = 'comparison_nfp'
    else:
        return redirect("recycle_bin")
    
    if request.method == "POST":
        log_audit(request, 'delete', module_name, pk, object_name, 
                  f"Permanently deleted from recycle bin")
        obj.hard_delete()
        return redirect("recycle_bin")
    
    return render(request, "forms/confirm_permanent_delete.html", {
        "item": obj,
        "object_name": object_name,
        "form_type": form_type,
    })


@login_required
@require_http_methods(["POST"])
def empty_recycle_bin(request):
    """Permanently delete all forms in recycle bin."""
    # Count items before deleting
    financial_count = FinancialStatement.deleted_objects.count()
    nfp13b_count = NetFamilyProperty13B.deleted_objects.count()
    comparison_count = ComparisonNetFamilyProperty.deleted_objects.count()
    
    FinancialStatement.deleted_objects.all().delete()
    NetFamilyProperty13B.deleted_objects.all().delete()
    ComparisonNetFamilyProperty.deleted_objects.all().delete()
    
    # Audit log for emptying recycle bin
    log_audit(request, 'delete', 'recycle_bin', '', 'Recycle Bin', 
              f"Emptied recycle bin - Deleted: {financial_count} Form 13, {nfp13b_count} Form 13B, {comparison_count} Form 13C")
    
    return redirect("recycle_bin")


@login_required
def comparison_nfp_create(request):
    """Create a new Comparison NFP and redirect to page 1."""
    # Allow creating with a CaseFile via ?case_id=
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    if case_id:
        try:
            case = CaseFile.objects.get(pk=case_id, owner=request.user)
        except CaseFile.DoesNotExist:
            case = None
    else:
        case = None

    nfp = ComparisonNetFamilyProperty.objects.create()
    if case:
        nfp.case_file = case
        _apply_case_fields_to_instance(nfp, case, overwrite=False)
        nfp.save()
    return redirect("comparison_nfp_page1_edit", pk=nfp.pk)


@login_required
def comparison_nfp_success(request):
    return render(request, "forms/comparison_nfp_success.html")


@login_required
def comparison_nfp_page1(request, pk=None):
    """Comparison NFP Page 1 - Basic info, case autofill, and land."""

    instance = get_object_or_404(ComparisonNetFamilyProperty, pk=pk) if pk else None
    is_new = instance is None

    case_list = CaseFile.objects.filter(owner=request.user).order_by("-updated_at")
    selected_case = None

    case_id = request.GET.get("case_id") or request.POST.get("case_id")

    if case_id:
        selected_case = CaseFile.objects.filter(
            pk=case_id,
            owner=request.user
        ).first()

    AssetFormSet = modelformset_factory(
        Form13CAsset,
        form=Form13CAssetForm,
        extra=5,
        can_delete=True,
    )

    if request.method == "POST":
        form = ComparisonNetFamilyPropertyForm(
            request.POST,
            instance=instance
        )

        land_formset = AssetFormSet(
            request.POST,
            queryset=Form13CAsset.objects.filter(
                form13c__parent=instance
            ) if instance else Form13CAsset.objects.none(),
            prefix="land",
        )

        if form.is_valid() and land_formset.is_valid():
            obj = form.save(commit=False)

            if selected_case:
                obj.case_file = selected_case

            obj.save()

            if selected_case:
                _apply_case_fields_to_instance(
                    obj,
                    selected_case,
                    overwrite=False
                )
                obj.save()

            form13c, created = Form13CComparison.objects.get_or_create(
                parent=obj
            )

            for form_instance in land_formset.forms:
                if form_instance.cleaned_data.get("DELETE", False):
                    inst = form_instance.instance
                    if inst and getattr(inst, "pk", None):
                        inst.delete()
                    continue

                data_present = False

                for k, v in form_instance.cleaned_data.items():
                    if k in ("id", "DELETE"):
                        continue
                    if v not in (None, "", []):
                        data_present = True
                        break

                if not data_present:
                    continue

                inst = form_instance.save(commit=False)
                inst.form13c = form13c
                inst.save()

            if is_new:
                send_form_created_notification(
                    "comparison_nfp",
                    obj,
                    request.user
                )

                log_audit(
                    request,
                    "create",
                    "comparison_nfp",
                    obj.pk,
                    f"Form 13C #{obj.pk}",
                    f"Created - Court File: {obj.court_file_number or 'N/A'}"
                )
            else:
                log_audit(
                    request,
                    "update",
                    "comparison_nfp",
                    obj.pk,
                    f"Form 13C #{obj.pk}",
                    "Updated Page 1"
                )

            return redirect("comparison_nfp_page2", pk=obj.pk)

        return render(request, "forms/comparison_nfp_page1.html", {
            "form": form,
            "pk": pk,
            "land_formset": land_formset,
            "case_list": case_list,
            "selected_case": selected_case,
        })

    initial_data = {}

    if selected_case:
        initial_data = _build_case_initial(selected_case)

    form = ComparisonNetFamilyPropertyForm(
        instance=instance,
        initial=initial_data
    )

    land_formset = AssetFormSet(
        queryset=Form13CAsset.objects.filter(
            form13c__parent=instance
        ) if instance else Form13CAsset.objects.none(),
        prefix="land",
    )

    return render(request, "forms/comparison_nfp_page1.html", {
        "form": form,
        "pk": pk,
        "land_formset": land_formset,
        "case_list": case_list,
        "selected_case": selected_case,
    })

@login_required
def comparison_nfp_page2(request, pk):
    """Comparison NFP Page 2 - Household Items, Bank Accounts, Insurance, Business."""
    instance = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)

    HouseholdItemFormSet = inlineformset_factory(
        ComparisonNetFamilyProperty,
        ComparisonNetFamilyPropertyHouseholdItem,
        form=ComparisonNetFamilyPropertyHouseholdItemForm,
        extra=5,
        can_delete=True,
    )
    BankAccountFormSet = inlineformset_factory(
        ComparisonNetFamilyProperty,
        ComparisonNetFamilyPropertyBankAccount,
        form=ComparisonNetFamilyPropertyBankAccountForm,
        extra=5,
        can_delete=True,
    )
    InsuranceFormSet = inlineformset_factory(
        ComparisonNetFamilyProperty,
        ComparisonNetFamilyPropertyInsurance,
        form=ComparisonNetFamilyPropertyInsuranceForm,
        extra=5,
        can_delete=True,
    )
    BusinessFormSet = inlineformset_factory(
        ComparisonNetFamilyProperty,
        ComparisonNetFamilyPropertyBusiness,
        form=ComparisonNetFamilyPropertyBusinessForm,
        extra=5,
        can_delete=True,
    )

    if request.method == "POST":
        household_items_formset = HouseholdItemFormSet(request.POST, instance=instance, prefix="household_items")
        bank_accounts_formset = BankAccountFormSet(request.POST, instance=instance, prefix="bank_accounts")
        insurance_formset = InsuranceFormSet(request.POST, instance=instance, prefix="insurances")
        business_formset = BusinessFormSet(request.POST, instance=instance, prefix="businesses")

        if (household_items_formset.is_valid() and bank_accounts_formset.is_valid() 
            and insurance_formset.is_valid() and business_formset.is_valid()):
            household_items_formset.save()
            bank_accounts_formset.save()
            insurance_formset.save()
            business_formset.save()

            if "prev" in request.POST:
                return redirect("comparison_nfp_page1_edit", pk=instance.pk)
            return redirect("comparison_nfp_page3", pk=instance.pk)
    else:
        household_items_formset = HouseholdItemFormSet(instance=instance, prefix="household_items")
        bank_accounts_formset = BankAccountFormSet(instance=instance, prefix="bank_accounts")
        insurance_formset = InsuranceFormSet(instance=instance, prefix="insurances")
        business_formset = BusinessFormSet(instance=instance, prefix="businesses")

    return render(request, "forms/comparison_nfp_page2.html", {
        "household_items_formset": household_items_formset,
        "bank_accounts_formset": bank_accounts_formset,
        "insurance_formset": insurance_formset,
        "business_formset": business_formset,
        "pk": instance.pk,
        "comparison": instance,
    })


@login_required
def comparison_nfp_page3(request, pk):
    """Comparison NFP Page 3 - Money Owed, Other Property, Debts."""
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    form13c, _ = Form13CComparison.objects.get_or_create(parent=comparison)

    MoneyOwedFormSet = inlineformset_factory(Form13CComparison, Form13CMoneyOwed, form=Form13CMoneyOwedForm, extra=3, can_delete=True)
    OtherPropertyFormSet = inlineformset_factory(Form13CComparison, Form13COtherProperty, form=Form13COtherPropertyForm, extra=3, can_delete=True)
    DebtLiabilityFormSet = inlineformset_factory(Form13CComparison, Form13CDebtLiability, form=Form13CDebtLiabilityForm, extra=3, can_delete=True)

    if request.method == "POST":
        if "prev" in request.POST:
            return redirect("comparison_nfp_page2", pk=comparison.pk)

        money_owed_formset = MoneyOwedFormSet(request.POST, instance=form13c, prefix="money_owed")
        other_property_formset = OtherPropertyFormSet(request.POST, instance=form13c, prefix="other_property")
        debt_liability_formset = DebtLiabilityFormSet(request.POST, instance=form13c, prefix="debt_liability")

        if (money_owed_formset.is_valid() 
            and other_property_formset.is_valid() and debt_liability_formset.is_valid()):
            money_owed_formset.save()
            other_property_formset.save()
            debt_liability_formset.save()
            if "save_draft" in request.POST:
                return redirect("comparison_nfp_page3", pk=comparison.pk)
            return redirect("comparison_nfp_page4", pk=comparison.pk)
    else:
        money_owed_formset = MoneyOwedFormSet(instance=form13c, prefix="money_owed")
        other_property_formset = OtherPropertyFormSet(instance=form13c, prefix="other_property")
        debt_liability_formset = DebtLiabilityFormSet(instance=form13c, prefix="debt_liability")

    return render(request, "forms/comparison_nfp_page3.html", {
        "pk": comparison.pk,
        "comparison": comparison,
        "money_owed_formset": money_owed_formset,
        "other_property_formset": other_property_formset,
        "debt_liability_formset": debt_liability_formset,
    })


@login_required
def comparison_nfp_page4(request, pk):
    """Comparison NFP Page 4 - Marriage Property and Excluded Property."""
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    form13c, _ = Form13CComparison.objects.get_or_create(parent=comparison)

    MarriagePropertyFormSet = modelformset_factory(
        Form13CMarriageProperty, form=Form13CMarriagePropertyForm, extra=3, can_delete=True
    )
    MarriageDebtFormSet = modelformset_factory(
        Form13CMarriageProperty, form=Form13CMarriagePropertyForm, extra=3, can_delete=True
    )
    ExcludedPropertyFormSet = modelformset_factory(
        Form13CExcludedProperty, form=Form13CExcludedPropertyForm, extra=3, can_delete=True
    )

    if request.method == "POST":
        if "prev" in request.POST:
            return redirect("comparison_nfp_page3", pk=pk)

        marriage_property_formset = MarriagePropertyFormSet(
            request.POST,
            queryset=Form13CMarriageProperty.objects.filter(form13c=form13c, is_debt=False),
            prefix="marriage_property",
        )
        marriage_debt_formset = MarriageDebtFormSet(
            request.POST,
            queryset=Form13CMarriageProperty.objects.filter(form13c=form13c, is_debt=True),
            prefix="marriage_debt",
        )
        excluded_property_formset = ExcludedPropertyFormSet(
            request.POST,
            queryset=Form13CExcludedProperty.objects.filter(form13c=form13c),
            prefix="excluded_property",
        )

        if (marriage_property_formset.is_valid() and marriage_debt_formset.is_valid() 
            and excluded_property_formset.is_valid()):
            
            def save_safe(formset, is_debt=False):
                for f in formset.forms:
                    if f.cleaned_data.get('DELETE', False):
                        inst = f.instance
                        if inst and getattr(inst, 'pk', None):
                            inst.delete()
                        continue
                    
                    data_present = False
                    for k, v in f.cleaned_data.items():
                        if k in ('id', 'DELETE'):
                            continue
                        if v not in (None, '', []):
                            data_present = True
                            break
                    if not data_present:
                        continue
                    
                    inst = f.save(commit=False)
                    inst.form13c = form13c
                    if is_debt:
                        inst.is_debt = True
                    inst.save()

            save_safe(marriage_property_formset, is_debt=False)
            save_safe(marriage_debt_formset, is_debt=True)
            save_safe(excluded_property_formset)

            return redirect("comparison_nfp_page5", pk=pk)
    else:
        marriage_property_formset = MarriagePropertyFormSet(
            queryset=Form13CMarriageProperty.objects.filter(form13c=form13c, is_debt=False),
            prefix="marriage_property",
        )
        marriage_debt_formset = MarriageDebtFormSet(
            queryset=Form13CMarriageProperty.objects.filter(form13c=form13c, is_debt=True),
            prefix="marriage_debt",
        )
        excluded_property_formset = ExcludedPropertyFormSet(
            queryset=Form13CExcludedProperty.objects.filter(form13c=form13c),
            prefix="excluded_property",
        )

    return render(request, "forms/comparison_nfp_page4.html", {
        "pk": pk,
        "comparison": comparison,
        "marriage_property_formset": marriage_property_formset,
        "marriage_debt_formset": marriage_debt_formset,
        "excluded_property_formset": excluded_property_formset,
    })


@login_required
def comparison_nfp_page5(request, pk):
    """Comparison NFP Page 5 - Final totals and equalization."""
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    form13c, _ = Form13CComparison.objects.get_or_create(parent=comparison)

    try:
        final_totals = form13c.final_totals
    except Form13CFinalTotals.DoesNotExist:
        final_totals = None

    from django.db.models import Sum
    from decimal import Decimal, ROUND_HALF_UP

    MONEY = Decimal("0.01")

    def money(value):
        value = Decimal(str(value or 0))
        return value.quantize(MONEY, rounding=ROUND_HALF_UP)

    def sum_field(qs, field):
        agg = qs.aggregate(total=Sum(field))["total"]
        return money(agg)

    cols = [
        "applicant_position_applicant",
        "applicant_position_respondent",
        "respondent_position_applicant",
        "respondent_position_respondent",
    ]

    suffixes = [
        "_app_pos_applicant",
        "_app_pos_respondent",
        "_resp_pos_applicant",
        "_resp_pos_respondent",
    ]

    totals = {
        "total1": [Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")],
        "total2": [Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")],
        "total3": [Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")],
        "total4": [Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")],
        "total5": [Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")],
        "total6": [Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")],
    }

    for i, col in enumerate(cols):
        totals["total2"][i] = sum_field(
            Form13CDebtLiability.objects.filter(form13c=form13c),
            col
        )

        totals["total3"][i] = sum_field(
            Form13CMarriageProperty.objects.filter(
                form13c=form13c,
                is_debt=False
            ),
            col
        )

        totals["total4"][i] = sum_field(
            Form13CExcludedProperty.objects.filter(form13c=form13c),
            col
        )

        comp_household = sum_field(
            ComparisonNetFamilyPropertyHouseholdItem.objects.filter(parent=comparison),
            col
        )

        comp_bank = sum_field(
            ComparisonNetFamilyPropertyBankAccount.objects.filter(parent=comparison),
            col
        )

        comp_insurance = sum_field(
            ComparisonNetFamilyPropertyInsurance.objects.filter(parent=comparison),
            col
        )

        comp_business = sum_field(
            ComparisonNetFamilyPropertyBusiness.objects.filter(parent=comparison),
            col
        )

        form13c_assets = sum_field(
            Form13CAsset.objects.filter(form13c=form13c),
            col
        )

        form13c_money_owed = sum_field(
            Form13CMoneyOwed.objects.filter(form13c=form13c),
            col
        )

        form13c_other_property = sum_field(
            Form13COtherProperty.objects.filter(form13c=form13c),
            col
        )

        totals["total1"][i] = money(
            comp_household
            + comp_bank
            + comp_insurance
            + comp_business
            + form13c_assets
            + form13c_money_owed
            + form13c_other_property
        )

        totals["total5"][i] = money(
            totals["total2"][i]
            + totals["total3"][i]
            + totals["total4"][i]
        )

        totals["total6"][i] = money(
            totals["total1"][i]
            - totals["total5"][i]
        )

    initial_data = {}

    for key in ["total1", "total2", "total3", "total4", "total5", "total6"]:
        for i, suffix in enumerate(suffixes):
            initial_data[key + suffix] = totals[key][i]

    for i, suffix in enumerate(suffixes):
        initial_data["total5b" + suffix] = totals["total5"][i]

    t6_app_app = totals["total6"][0]
    t6_app_resp = totals["total6"][1]

    if t6_app_app > t6_app_resp:
        initial_data["eq_app_pos_applicant_pays"] = money(
            (t6_app_app - t6_app_resp) / Decimal("2")
        )
        initial_data["eq_app_pos_respondent_pays"] = Decimal("0.00")
    else:
        initial_data["eq_app_pos_applicant_pays"] = Decimal("0.00")
        initial_data["eq_app_pos_respondent_pays"] = money(
            (t6_app_resp - t6_app_app) / Decimal("2")
        )

    t6_resp_app = totals["total6"][2]
    t6_resp_resp = totals["total6"][3]

    if t6_resp_app > t6_resp_resp:
        initial_data["eq_resp_pos_applicant_pays"] = money(
            (t6_resp_app - t6_resp_resp) / Decimal("2")
        )
        initial_data["eq_resp_pos_respondent_pays"] = Decimal("0.00")
    else:
        initial_data["eq_resp_pos_applicant_pays"] = Decimal("0.00")
        initial_data["eq_resp_pos_respondent_pays"] = money(
            (t6_resp_resp - t6_resp_app) / Decimal("2")
        )

    numeric_fields = [
        "total1_app_pos_applicant",
        "total1_app_pos_respondent",
        "total1_resp_pos_applicant",
        "total1_resp_pos_respondent",
        "total2_app_pos_applicant",
        "total2_app_pos_respondent",
        "total2_resp_pos_applicant",
        "total2_resp_pos_respondent",
        "total3_app_pos_applicant",
        "total3_app_pos_respondent",
        "total3_resp_pos_applicant",
        "total3_resp_pos_respondent",
        "total4_app_pos_applicant",
        "total4_app_pos_respondent",
        "total4_resp_pos_applicant",
        "total4_resp_pos_respondent",
        "total5_app_pos_applicant",
        "total5_app_pos_respondent",
        "total5_resp_pos_applicant",
        "total5_resp_pos_respondent",
        "total5b_app_pos_applicant",
        "total5b_app_pos_respondent",
        "total5b_resp_pos_applicant",
        "total5b_resp_pos_respondent",
        "total6_app_pos_applicant",
        "total6_app_pos_respondent",
        "total6_resp_pos_applicant",
        "total6_resp_pos_respondent",
        "eq_app_pos_applicant_pays",
        "eq_app_pos_respondent_pays",
        "eq_resp_pos_applicant_pays",
        "eq_resp_pos_respondent_pays",
    ]

    if request.method == "POST":
        post_data = request.POST.copy()

        for field in numeric_fields:
            value = post_data.get(field)

            if value not in [None, ""]:
                post_data[field] = str(money(value))

        form = Form13CFinalTotalsForm(post_data, instance=final_totals)

        if form.is_valid():
            ft = form.save(commit=False)
            ft.form13c = form13c

            # overwrite old saved values with the latest calculated values
            for field, value in initial_data.items():
                setattr(ft, field, value)

            ft.save()


            if "prev" in request.POST:
                return redirect("comparison_nfp_page4", pk=pk)

            if "save_draft" in request.POST:
                messages.success(request, "Draft saved successfully.")
                return redirect("comparison_nfp_page5", pk=pk)

            if "finish" in request.POST:
                messages.success(request, "Comparison NFP saved successfully.")
                return redirect("comparison_nfp_list")

            messages.success(request, "Comparison NFP saved successfully.")
            return redirect("comparison_nfp_list")

        print(form.errors)

    else:
        form = Form13CFinalTotalsForm(
            instance=final_totals,
            initial=initial_data
        )

    for field_name in form.fields:
        if field_name != "court_file_number":
            form.fields[field_name].widget.attrs.update({
                "step": "0.01",
                "inputmode": "decimal",
            })

    totals_json = json.dumps({
        key: [str(money(v)) for v in values]
        for key, values in totals.items()
    })

    return render(request, "forms/comparison_nfp_page5.html", {
        "form": form,
        "pk": pk,
        "comparison": comparison,
        "totals_json": totals_json,
    })

    
@login_required
@require_http_methods(["GET", "POST"])
def comparison_nfp_draft(request, pk):
    """API endpoint to save/load JSON drafts.
    
    Note: Server-side draft storage was removed. Using localStorage only.
    This endpoint exists for compatibility but returns empty data.
    """
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    
    if request.method == "POST":
        # Draft field was removed from model, just return OK
        # The client uses localStorage for draft storage
        return JsonResponse({"status": "ok"})

    # Return empty draft - client should use localStorage
    return JsonResponse({"draft": None})

@login_required
def comparison_nfp_full_view(request, pk):
    """Full view of a Comparison NFP form."""
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    form13c = getattr(comparison, "form13c", None)

    land_assets = []
    household_items = list(comparison.household_items.all())
    bank_accounts = list(comparison.bank_accounts.all())
    insurances = list(comparison.insurances.all())
    businesses = list(comparison.businesses.all())

    money_owed_list = []
    other_properties = []
    debts_liabilities = []
    marriage_properties = []
    marriage_debts = []
    excluded_properties = []
    final_totals = None

    if form13c:
        land_assets = list(form13c.assets.all())
        money_owed_list = list(form13c.money_owed.all())
        other_properties = list(form13c.other_properties.all())
        debts_liabilities = list(form13c.debts_liabilities.all())
        marriage_properties = list(form13c.marriage_properties.filter(is_debt=False))
        marriage_debts = list(form13c.marriage_properties.filter(is_debt=True))
        excluded_properties = list(form13c.excluded_properties.all())

        try:
            final_totals = form13c.final_totals
        except Form13CFinalTotals.DoesNotExist:
            final_totals = None

    def sum_field(items, field):
        total = 0
        for item in items:
            value = getattr(item, field, None)
            if value not in [None, ""]:
                total += float(value)
        return total

    cols = [
        "applicant_position_applicant",
        "applicant_position_respondent",
        "respondent_position_applicant",
        "respondent_position_respondent",
    ]

    totals = {
        "land": [sum_field(land_assets, c) for c in cols],
        "household": [sum_field(household_items, c) for c in cols],
        "bank": [sum_field(bank_accounts, c) for c in cols],
        "insurance": [sum_field(insurances, c) for c in cols],
        "business": [sum_field(businesses, c) for c in cols],
        "money_owed": [sum_field(money_owed_list, c) for c in cols],
        "other": [sum_field(other_properties, c) for c in cols],
        "debts": [sum_field(debts_liabilities, c) for c in cols],
        "marriage_property": [sum_field(marriage_properties, c) for c in cols],
        "marriage_debt": [sum_field(marriage_debts, c) for c in cols],
        "excluded": [sum_field(excluded_properties, c) for c in cols],

        "total1": [0, 0, 0, 0],
        "total2": [0, 0, 0, 0],
        "total3": [0, 0, 0, 0],
        "total4": [0, 0, 0, 0],
        "total5": [0, 0, 0, 0],
        "total6": [0, 0, 0, 0],
    }

    # Use saved Page 5 values as the source of truth
    if final_totals:
        totals["total1"] = [
            final_totals.total1_app_pos_applicant,
            final_totals.total1_app_pos_respondent,
            final_totals.total1_resp_pos_applicant,
            final_totals.total1_resp_pos_respondent,
        ]

        totals["total2"] = [
            final_totals.total2_app_pos_applicant,
            final_totals.total2_app_pos_respondent,
            final_totals.total2_resp_pos_applicant,
            final_totals.total2_resp_pos_respondent,
        ]

        totals["total3"] = [
            final_totals.total3_app_pos_applicant,
            final_totals.total3_app_pos_respondent,
            final_totals.total3_resp_pos_applicant,
            final_totals.total3_resp_pos_respondent,
        ]

        totals["total4"] = [
            final_totals.total4_app_pos_applicant,
            final_totals.total4_app_pos_respondent,
            final_totals.total4_resp_pos_applicant,
            final_totals.total4_resp_pos_respondent,
        ]

        totals["total5"] = [
            final_totals.total5_app_pos_applicant,
            final_totals.total5_app_pos_respondent,
            final_totals.total5_resp_pos_applicant,
            final_totals.total5_resp_pos_respondent,
        ]

        totals["total6"] = [
            final_totals.total6_app_pos_applicant,
            final_totals.total6_app_pos_respondent,
            final_totals.total6_resp_pos_applicant,
            final_totals.total6_resp_pos_respondent,
        ]

        equalization = {
            "app_pays_resp_app": final_totals.eq_app_pos_applicant_pays,
            "resp_pays_app_app": final_totals.eq_app_pos_respondent_pays,
            "app_pays_resp_resp": final_totals.eq_resp_pos_applicant_pays,
            "resp_pays_app_resp": final_totals.eq_resp_pos_respondent_pays,
        }

    else:
        equalization = {
            "app_pays_resp_app": 0,
            "resp_pays_app_app": 0,
            "app_pays_resp_resp": 0,
            "resp_pays_app_resp": 0,
        }

    return render(request, "forms/comparison_nfp_full_view.html", {
        "comparison": comparison,
        "form13c": form13c,

        "land_assets": land_assets,
        "household_items": household_items,
        "bank_accounts": bank_accounts,
        "insurances": insurances,
        "businesses": businesses,

        "money_owed": money_owed_list,
        "other_properties": other_properties,
        "debts_liabilities": debts_liabilities,
        "marriage_properties": marriage_properties,
        "marriage_debts": marriage_debts,
        "excluded_properties": excluded_properties,

        "final_totals": final_totals,
        "totals": totals,
        "equalization": equalization,
        "pk": pk,
    })

@login_required
def comparison_nfp_print(request, pk):
    """Official printable format for Comparison NFP."""
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    form13c = getattr(comparison, "form13c", None)

    household_items = list(comparison.household_items.all())
    bank_accounts = list(comparison.bank_accounts.all())
    insurances = list(comparison.insurances.all())
    businesses = list(comparison.businesses.all())

    assets = []
    money_owed = []
    other_property = []
    debts = []
    marriage_property = []
    marriage_debts = []
    excluded_property = []
    final_totals = None

    if form13c:
        assets = list(form13c.assets.all())
        money_owed = list(form13c.money_owed.all())
        other_property = list(form13c.other_properties.all())
        debts = list(form13c.debts_liabilities.all())
        marriage_property = list(form13c.marriage_properties.filter(is_debt=False))
        marriage_debts = list(form13c.marriage_properties.filter(is_debt=True))
        excluded_property = list(form13c.excluded_properties.all())

        try:
            final_totals = form13c.final_totals
        except Form13CFinalTotals.DoesNotExist:
            final_totals = None

    total_a = [0, 0, 0, 0]
    total_b = [0, 0, 0, 0]
    total_c = [0, 0, 0, 0]
    total_d = [0, 0, 0, 0]
    total_e = [0, 0, 0, 0]
    total_f = [0, 0, 0, 0]
    total_g = [0, 0, 0, 0]

    total_1 = [0, 0, 0, 0]
    total_2 = [0, 0, 0, 0]
    total_3 = [0, 0, 0, 0]
    total_4 = [0, 0, 0, 0]
    total_5 = [0, 0, 0, 0]
    total_6 = [0, 0, 0, 0]

    total_marriage_property = [0, 0, 0, 0]
    total_marriage_debts = [0, 0, 0, 0]

    equalization = {
        "app_pays_resp_app": "",
        "resp_pays_app_app": "",
        "app_pays_resp_resp": "",
        "resp_pays_app_resp": "",
    }

    if final_totals:
        total_1 = [
            final_totals.total1_app_pos_applicant,
            final_totals.total1_app_pos_respondent,
            final_totals.total1_resp_pos_applicant,
            final_totals.total1_resp_pos_respondent,
        ]

        total_2 = [
            final_totals.total2_app_pos_applicant,
            final_totals.total2_app_pos_respondent,
            final_totals.total2_resp_pos_applicant,
            final_totals.total2_resp_pos_respondent,
        ]

        total_3 = [
            final_totals.total3_app_pos_applicant,
            final_totals.total3_app_pos_respondent,
            final_totals.total3_resp_pos_applicant,
            final_totals.total3_resp_pos_respondent,
        ]

        total_4 = [
            final_totals.total4_app_pos_applicant,
            final_totals.total4_app_pos_respondent,
            final_totals.total4_resp_pos_applicant,
            final_totals.total4_resp_pos_respondent,
        ]

        total_5 = [
            final_totals.total5_app_pos_applicant,
            final_totals.total5_app_pos_respondent,
            final_totals.total5_resp_pos_applicant,
            final_totals.total5_resp_pos_respondent,
        ]

        total_6 = [
            final_totals.total6_app_pos_applicant,
            final_totals.total6_app_pos_respondent,
            final_totals.total6_resp_pos_applicant,
            final_totals.total6_resp_pos_respondent,
        ]

        equalization = {
            "app_pays_resp_app": final_totals.eq_app_pos_applicant_pays,
            "resp_pays_app_app": final_totals.eq_app_pos_respondent_pays,
            "app_pays_resp_resp": final_totals.eq_resp_pos_applicant_pays,
            "resp_pays_app_resp": final_totals.eq_resp_pos_respondent_pays,
        }

    print_event = PrintEvent.log_print(
        user=request.user,
        form_type="comparison_nfp",
        form_id=pk,
        form_identifier=comparison.court_file_number or f"Form 13C #{pk}"
    )

    log_audit(
        request,
        "export",
        "comparison_nfp",
        pk,
        f"Form 13C #{pk}",
        f"Printed - Price: ${print_event.price_charged}"
    )

    send_form_printed_notification(
        "comparison_nfp",
        comparison,
        request.user,
        print_event.price_charged
    )

    return render(request, "forms/comparison_nfp_print.html", {
        "comparison": comparison,
        "pk": pk,
        "assets": assets,
        "household_items": household_items,
        "bank_accounts": bank_accounts,
        "insurance_policies": insurances,
        "business_interests": businesses,
        "money_owed": money_owed,
        "other_property": other_property,
        "debts": debts,
        "marriage_property": marriage_property,
        "marriage_debts": marriage_debts,
        "excluded_property": excluded_property,
        "total_a": total_a,
        "total_b": total_b,
        "total_c": total_c,
        "total_d": total_d,
        "total_e": total_e,
        "total_f": total_f,
        "total_g": total_g,
        "total_1": total_1,
        "total_2": total_2,
        "total_3": total_3,
        "total_4": total_4,
        "total_5": total_5,
        "total_6": total_6,
        "total_marriage_property": total_marriage_property,
        "total_marriage_debts": total_marriage_debts,
        "equalization": equalization,
        "final_totals": final_totals,
    })
# ============================================================
# BILLING & PRINT TRACKING
# ============================================================
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth
from datetime import datetime, timedelta
from .models import BillingSetting


@login_required
def billing_dashboard(request):
    """Dashboard showing print statistics and billing information."""
    user = request.user
    
    # Check if user has billing view permission
    has_billing_permission = user.is_staff or user.is_superuser
    if not has_billing_permission:
        try:
            has_billing_permission = user.profile.has_module_permission('billing', 'view')
        except:
            has_billing_permission = False
    
    # Staff/superusers/users with billing permission see ALL prints by default
    view_all = request.GET.get('view') == 'all' or has_billing_permission
    view_mine = request.GET.get('view') == 'mine'
    
    if view_mine:
        user_prints = PrintEvent.objects.filter(user=user)
        showing_all = False
    elif view_all and has_billing_permission:
        user_prints = PrintEvent.objects.all()
        showing_all = True
    else:
        user_prints = PrintEvent.objects.filter(user=user)
        showing_all = False
    
    # Get date range (default: current month)
    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    this_month_prints = user_prints.filter(printed_at__date__gte=start_of_month)
    
    # Statistics
    stats = {
        'total_prints': user_prints.count(),
        'month_prints': this_month_prints.count(),
        'total_charges': user_prints.aggregate(Sum('price_charged'))['price_charged__sum'] or 0,
        'month_charges': this_month_prints.aggregate(Sum('price_charged'))['price_charged__sum'] or 0,
        'unbilled_prints': user_prints.filter(is_billed=False).count(),
        'unbilled_amount': user_prints.filter(is_billed=False).aggregate(Sum('price_charged'))['price_charged__sum'] or 0,
    }
    
    # Recent print events
    recent_prints = user_prints.order_by('-printed_at')[:20]
    
    # Prints by form type
    prints_by_type = user_prints.values('form_type').annotate(
        count=Count('id'),
        total=Sum('price_charged')
    )
    
    # Daily prints for chart (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    daily_prints = user_prints.filter(
        printed_at__date__gte=thirty_days_ago
    ).annotate(
        date=TruncDate('printed_at')
    ).values('date').annotate(
        count=Count('id'),
        total=Sum('price_charged')
    ).order_by('date')
    
    # Get billing settings for price display
    billing_settings = BillingSetting.objects.filter(is_active=True)
    

    
    context = {
        'stats': stats,
        'recent_prints': recent_prints,
        'prints_by_type': prints_by_type,
        'daily_prints': list(daily_prints),
        'billing_settings': billing_settings,
        # 'invoices': invoices,  # Invoice model does not exist
        'showing_all': showing_all,
        'can_view_all': has_billing_permission,
    }
    
    return render(request, 'forms/billing_dashboard.html', context)


@login_required
def billing_history(request):
    """Full history of print events for the user."""
    user = request.user
    
    # Check if user has billing view permission
    has_billing_permission = user.is_staff or user.is_superuser
    if not has_billing_permission:
        try:
            has_billing_permission = user.profile.has_module_permission('billing', 'view')
        except:
            has_billing_permission = False
    
    # Staff/superusers/users with billing permission can view ALL prints
    view_all = request.GET.get('view') == 'all' or has_billing_permission
    view_mine = request.GET.get('view') == 'mine'
    
    if view_mine:
        prints = PrintEvent.objects.filter(user=user)
        showing_all = False
    elif view_all and has_billing_permission:
        prints = PrintEvent.objects.all()
        showing_all = True
    else:
        prints = PrintEvent.objects.filter(user=user)
        showing_all = False
    
    # Filter parameters
    form_type = request.GET.get('form_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    billed_status = request.GET.get('billed', '')
    
    if form_type:
        prints = prints.filter(form_type=form_type)
    if date_from:
        prints = prints.filter(printed_at__date__gte=date_from)
    if date_to:
        prints = prints.filter(printed_at__date__lte=date_to)
    if billed_status == 'billed':
        prints = prints.filter(is_billed=True)
    elif billed_status == 'unbilled':
        prints = prints.filter(is_billed=False)
    
    # Calculate totals
    totals = prints.aggregate(
        count=Count('id'),
        total_amount=Sum('price_charged')
    )
    
    context = {
        'prints': prints.order_by('-printed_at'),
        'totals': totals,
        'form_types': PrintEvent.FORM_TYPE_CHOICES,
        'filters': {
            'form_type': form_type,
            'date_from': date_from,
            'date_to': date_to,
            'billed': billed_status,
        },
        'showing_all': showing_all,
        'can_view_all': has_billing_permission,
    }
    
    return render(request, 'forms/billing_history.html', context)


@login_required  
def billing_settings_view(request):
    """Admin view to manage billing settings (staff only)."""
    if not request.user.is_staff:
        return redirect('billing_dashboard')
    
    settings = BillingSetting.objects.all()
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        price = request.POST.get('price')
        
        if form_type and price:
            old_setting = BillingSetting.objects.filter(form_type=form_type).first()
            old_price = old_setting.price_per_print if old_setting else None
            
            setting, created = BillingSetting.objects.update_or_create(
                form_type=form_type,
                defaults={
                    'price_per_print': Decimal(price),
                    'form_display_name': dict(PrintEvent.FORM_TYPE_CHOICES).get(form_type, form_type)
                }
            )
            
            # Audit log for price update
            action = 'create' if created else 'update'
            details = f"Price set to ${price}" if created else f"Price changed from ${old_price} to ${price}"
            log_audit(request, action, 'billing_settings', form_type, 
                      f"Billing Setting - {setting.form_display_name}", details)
    
    # Ensure all form types have billing settings (add any missing ones)
    for form_type, display_name in PrintEvent.FORM_TYPE_CHOICES:
        BillingSetting.objects.get_or_create(
            form_type=form_type,
            defaults={
                'form_display_name': display_name,
                'price_per_print': Decimal('1.00')
            }
        )
    settings = BillingSetting.objects.all()
    
    context = {
        'settings': settings,
        'form_types': PrintEvent.FORM_TYPE_CHOICES,
    }
    
    return render(request, 'forms/billing_settings.html', context)


@login_required
def admin_billing_report(request):
    """Admin report showing all users' print activity (staff only)."""
    if not request.user.is_staff:
        return redirect('billing_dashboard')
    
    from django.contrib.auth.models import User
    from django.db.models import Q
    
    # Get date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    prints = PrintEvent.objects.all()
    
    if date_from:
        prints = prints.filter(printed_at__date__gte=date_from)
    if date_to:
        prints = prints.filter(printed_at__date__lte=date_to)
    
    # User summary
    user_summary = prints.values('user__username', 'user__id').annotate(
        total_prints=Count('id'),
        total_amount=Sum('price_charged'),
        unbilled_prints=Count('id', filter=Q(is_billed=False)),
        unbilled_amount=Sum('price_charged', filter=Q(is_billed=False))
    ).order_by('-total_amount')
    
    # Overall totals
    totals = prints.aggregate(
        total_prints=Count('id'),
        total_amount=Sum('price_charged'),
        unbilled_prints=Count('id', filter=Q(is_billed=False)),
        unbilled_amount=Sum('price_charged', filter=Q(is_billed=False))
    )
    
    # Monthly breakdown
    monthly_data = prints.annotate(
        month=TruncMonth('printed_at')
    ).values('month').annotate(
        count=Count('id'),
        total=Sum('price_charged')
    ).order_by('-month')[:12]
    
    context = {
        'user_summary': user_summary,
        'totals': totals,
        'monthly_data': monthly_data,
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'forms/admin_billing_report.html', context)

# ============================================================
# FINANCIAL STATEMENT (FORM 13.1) - View Page (for /view/<int:pk>/)
# ============================================================
def normalize_form131_page4_for_print(pages):
    # Normalize Page 4 / Part 3 data for print
# Form 13.1 stores these values inside draft["page4"], not direct model fields.

# -------------------------------------------------
# Normalize Page 4 / Part 3 values for print
# IMPORTANT: Form 13.1 stores these inside draft["page4"]
# -------------------------------------------------

# -------------------------------------------------
# Normalize Page 4 / Part 3 values for print
# IMPORTANT: Form131FinancialStatement stores these in draft["page4"]
# -------------------------------------------------

    page4 = pages.get("page4", {}) or {}

    page4["live_alone"] = (
        page4.get("live_alone")
        or page4.get("lives_alone")
        or False
    )

    page4["living_with_someone"] = (
        page4.get("living_with_someone")
        or page4.get("living_with_spouse")
        or page4.get("living_with_partner")
        or False
    )

    page4["living_with_name"] = (
        page4.get("living_with_name")
        or page4.get("spouse_name")
        or page4.get("partner_name")
        or ""
    )

    page4["lives_with_other_adults"] = (
        page4.get("lives_with_other_adults")
        or page4.get("has_other_adults")
        or bool(page4.get("other_adults_names"))
        or bool(page4.get("other_adults"))
    )

    page4["other_adults_names"] = (
        page4.get("other_adults_names")
        or page4.get("other_adults")
        or ""
    )

    page4["has_children_in_home"] = (
        page4.get("has_children_in_home")
        or page4.get("has_children")
        or page4.get("children_in_home")
        or False
    )

    page4["number_of_children_in_home"] = (
        page4.get("number_of_children_in_home")
        or page4.get("num_children")
        or page4.get("children_count")
        or ""
    )

    page4["spouse_works"] = (
        page4.get("spouse_works")
        or page4.get("partner_works")
        or False
    )

    page4["spouse_work_place"] = (
        page4.get("spouse_work_place")
        or page4.get("spouse_workplace")
        or page4.get("partner_workplace")
        or ""
    )

    page4["spouse_does_not_work"] = (
        page4.get("spouse_does_not_work")
        or page4.get("spouse_not_work")
        or page4.get("partner_not_work")
        or False
    )

    page4["spouse_earns_income"] = (
        page4.get("spouse_earns_income")
        or page4.get("spouse_earns")
        or page4.get("partner_earns")
        or False
    )

    page4["spouse_income_amount"] = (
        page4.get("spouse_income_amount")
        or page4.get("spouse_income")
        or page4.get("partner_income")
        or ""
    )

    page4["spouse_income_period"] = (
        page4.get("spouse_income_period")
        or page4.get("partner_income_period")
        or ""
    )

    page4["spouse_no_income"] = (
        page4.get("spouse_no_income")
        or page4.get("partner_no_income")
        or False
    )

    page4["household_contribution_amount"] = (
        page4.get("household_contribution_amount")
        or page4.get("household_contribution")
        or ""
    )

    page4["household_contribution_period"] = (
        page4.get("household_contribution_period")
        or page4.get("contribution_period")
        or ""
    )

    pages["page4"] = page4
    return pages


@login_required
def financial_statement_131_view(request, pk):
    """Read-only view for Form 13.1 Financial Statement."""
    from .models import Form131FinancialStatement

    statement = get_object_or_404(Form131FinancialStatement, pk=pk)

    pages = statement.draft or {}

    # Always make sure all page keys exist.
    for page_num in range(1, 11):
        pages.setdefault(f"page{page_num}", statement.get_page_data(page_num) or {})

    # Always use proper Page 1 fallback data.
    page1 = _get_form131_page1_data(statement, persist=True)
    pages["page1"] = page1

    # Apply same calculations used by print.
    pages = _calculate_form131_totals(pages)
    pages = _calculate_form131_missing_totals(pages)

    # Make sure Page 10 exists.
    page10 = pages.get("page10", {}) or {}

    # Normalize the "I earn" fields for the view.
    page10["schedule_b_i_earn_checked"] = (
        page10.get("schedule_b_i_earn_checked")
        or page10.get("i_earn_checked")
        or page10.get("i_earn")
        or page10.get("earn_checked")
        or ""
    )

    page10["schedule_b_i_earn_amount"] = (
        page10.get("schedule_b_i_earn_amount")
        or page10.get("i_earn_amount")
        or page10.get("earn_amount")
        or page10.get("my_income_for_share")
        or ""
    )

    pages["page10"] = page10

    # Save calculated/normalized values back to draft so view and print stay aligned.
    statement.draft = pages
    statement.save(update_fields=["draft", "updated_at"])

    template_meta_by_page = _get_form131_template_meta()

    ordered_pages = []

    for page_num in range(1, 11):
        page_key = f"page{page_num}"
        page_data = pages.get(page_key, {}) or {}

        block_html = _get_form131_page_block_html(page_num)
        page_html = _apply_page_data_to_block(block_html, page_data) if block_html else ""

        page_meta = template_meta_by_page.get(page_num, {})

        ordered_pages.append(
            _build_form131_page_display_data(
                page_num,
                page_data,
                page_meta.get("fields", []),
                page_html=page_html,
                page_header=page_meta.get("header", ""),
                page_subheader=page_meta.get("subheader", ""),
            )
        )

    return render(request, "forms/financial_statement_131_view.html", {
        "statement": statement,
        "form": statement,
        "pages": pages,
        "ordered_pages": ordered_pages,
        "court_file_number": page1.get("court_file_number") or statement.court_file_number or "",
        "applicant_name": page1.get("applicant_name") or statement.applicant_name or "",
        "respondent_name": page1.get("respondent_name") or statement.respondent_name or "",
    })

@login_required
def financial_statement_131_delete(request, pk):
    """Soft delete a Form 13.1 Financial Statement (move to recycle bin)."""
    from .models import Form131FinancialStatement
    statement = get_object_or_404(Form131FinancialStatement.all_objects, pk=pk)
    if request.method == "POST":
        statement.soft_delete()
        log_audit(request, 'delete', 'financial_statement_131', pk, 
                  f"Form 13.1 Financial Statement #{pk}", 
                  f"Moved to recycle bin - Applicant: {statement.applicant_name or 'N/A'}")
        return redirect("financial_statement_131_list")
    return render(request, "forms/confirm_delete.html", {
        "object": statement,
        "object_name": f"Form 13.1 Financial Statement #{statement.id}",
        "cancel_url": "financial_statement_131_list",
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def delete_print_event(request, pk):
    print_event = get_object_or_404(PrintEvent, pk=pk)
    if request.method == "POST":
        log_audit(request, 'delete', 'print_event', pk, 
                  f"Print Event #{pk}", 
                  f"Deleted print event - Form: {print_event.form_type}, Price: ${print_event.price_charged}")
        print_event.delete()
        return redirect("billing_history")
    return render(request, "forms/confirm_delete.html", {
        "object": print_event,
        "object_name": f"Print Event #{print_event.id}",
        "cancel_url": reverse("billing_history"),
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def settings_page_view(request):
    """Admin settings dashboard with links to various settings."""
    return render(request, 'forms/settings_page.html')


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def email_settings_view(request):
    """Admin view to manage email settings."""
    from django.conf import settings as django_settings
    from django.contrib import messages
    from .models import EmailSettings
    
    # Get or create email settings
    email_settings = EmailSettings.get_settings()
    
    # Default values from Django settings (fallback)
    default_config = {
        'email_host': getattr(django_settings, 'EMAIL_HOST', ''),
        'email_port': getattr(django_settings, 'EMAIL_PORT', 587),
        'email_use_ssl': getattr(django_settings, 'EMAIL_USE_SSL', False),
        'email_use_tls': getattr(django_settings, 'EMAIL_USE_TLS', True),
        'email_host_user': getattr(django_settings, 'EMAIL_HOST_USER', ''),
        'default_from_email': getattr(django_settings, 'DEFAULT_FROM_EMAIL', ''),
        'admin_notification_email': getattr(django_settings, 'ADMIN_NOTIFICATION_EMAIL', ''),
    }
    
    test_result = None
    
    if request.method == 'POST':
        if 'save_settings' in request.POST:
            # Save email settings
            email_settings.notifications_enabled = request.POST.get('notifications_enabled') == 'on'
            email_settings.email_host = request.POST.get('email_host', '').strip()
            email_settings.email_port = int(request.POST.get('email_port', 587))
            email_settings.email_use_ssl = request.POST.get('email_use_ssl') == 'on'
            email_settings.email_use_tls = request.POST.get('email_use_tls') == 'on'
            email_settings.email_host_user = request.POST.get('email_host_user', '').strip()
            
            # Only update password if provided
            new_password = request.POST.get('email_host_password', '').strip()
            if new_password:
                email_settings.email_host_password = new_password
            
            email_settings.default_from_email = request.POST.get('default_from_email', '').strip()
            email_settings.admin_notification_email = request.POST.get('admin_notification_email', '').strip()
            
            # Notification toggles
            email_settings.notify_on_login = request.POST.get('notify_on_login') == 'on'
            email_settings.notify_on_form_create = request.POST.get('notify_on_form_create') == 'on'
            email_settings.notify_on_form_print = request.POST.get('notify_on_form_print') == 'on'
            
            email_settings.updated_by = request.user
            email_settings.save()
            
            log_audit(request, 'update', 'email_settings', '', 'Email Settings', 
                      f'Email settings updated - Notifications: {"Enabled" if email_settings.notifications_enabled else "Disabled"}')
            
            messages.success(request, 'Email settings saved successfully!')
            return redirect('email_settings')
        
        elif 'toggle_notifications' in request.POST:
            # Quick toggle for notifications
            email_settings.notifications_enabled = not email_settings.notifications_enabled
            email_settings.updated_by = request.user
            email_settings.save()
            
            status = "enabled" if email_settings.notifications_enabled else "disabled"
            log_audit(request, 'update', 'email_settings', '', 'Email Settings', 
                      f'Email notifications {status}')
            
            messages.success(request, f'Email notifications {status}!')
            return redirect('email_settings')
        
        elif 'test_email' in request.POST:
            test_to = request.POST.get('test_to', request.user.email)
            if test_to:
                try:
                    from .notifications import get_email_connection, get_from_email
                    from django.core.mail import send_mail
                    
                    connection = get_email_connection()
                    from_email = get_from_email() or django_settings.DEFAULT_FROM_EMAIL
                    
                    send_mail(
                        subject='Test Email from Family Law Forms',
                        message='This is a test email to verify your email configuration is working correctly.',
                        from_email=from_email,
                        recipient_list=[test_to],
                        fail_silently=False,
                        connection=connection,
                    )
                    test_result = {'success': True, 'message': f'Test email sent successfully to {test_to}'}
                    log_audit(request, 'update', 'email_settings', '', 'Email Settings', 
                              f'Test email sent to {test_to}')
                except Exception as e:
                    test_result = {'success': False, 'message': f'Failed to send test email: {str(e)}'}
            else:
                test_result = {'success': False, 'message': 'Please provide an email address'}
    
    context = {
        'email_settings': email_settings,
        'default_config': default_config,
        'test_result': test_result,
    }
    
    return render(request, 'forms/email_settings.html', context)

from django.contrib.auth.decorators import login_required
from .models import ApplicationDivorce8A, AffidavitOfService, PrintEvent, FinancialStatement, Form131FinancialStatement, NetFamilyProperty13B, ComparisonNetFamilyProperty

@login_required
def view_printed_copy(request, print_event_id):
    """
    Secure view-only page for a printed form. Blocks printing and screenshots.
    Shows the form as it was at print time.
    """
    print_event = get_object_or_404(PrintEvent, pk=print_event_id)
    # Map form_type to model
    form_obj = None
    if print_event.form_type == 'financial_statement':
        form_obj = FinancialStatement.objects.filter(pk=print_event.form_id).first()
        template = 'forms/financial_statement_131_printed_view.html'
        context = {
            'form': form_obj,
            'print_event': print_event,
            'view_only': True,
        }
    elif print_event.form_type == 'financial_statement_131':
        form_obj = Form131FinancialStatement.objects.filter(pk=print_event.form_id).first()
        template = 'forms/financial_statement_131_printed_view.html'
        # Build context as in print view
        pages = form_obj.draft or {}
        page1 = getattr(form_obj, 'draft', {}).get('page1', {})
        context = {
            'form': form_obj,
            'print_event': print_event,
            'view_only': True,
            'pages': pages,
            'court_file_number': page1.get('court_file_number') or getattr(form_obj, 'court_file_number', ''),
            'applicant_name': page1.get('applicant_name') or getattr(form_obj, 'applicant_name', ''),
            'respondent_name': page1.get('respondent_name') or getattr(form_obj, 'respondent_name', ''),
        }
    elif print_event.form_type == 'net_family_property_13b':
        form_obj = NetFamilyProperty13B.objects.filter(pk=print_event.form_id).first()
        template = 'forms/net_family_property_13b_printed_view.html'
        if form_obj:
            assets = list(form_obj.assets.all())
            debts = list(form_obj.debts.all())
            marriage_properties = list(form_obj.marriage_properties.all())
            marriage_debts = list(form_obj.marriage_debts.all())
            excluded_properties = list(form_obj.excluded_properties.all())
            try:
                final_totals = form_obj.final_totals
            except Exception:
                final_totals = None

            def _sum(items, field):
                return sum(float(getattr(i, field) or 0) for i in items)

            m_prop_app = _sum(marriage_properties, 'applicant_value')
            m_prop_resp = _sum(marriage_properties, 'respondent_value')
            m_debt_app = _sum(marriage_debts, 'applicant_value')
            m_debt_resp = _sum(marriage_debts, 'respondent_value')
            t1a = _sum(assets, 'applicant_value')
            t1r = _sum(assets, 'respondent_value')
            t2a = _sum(debts, 'applicant_value')
            t2r = _sum(debts, 'respondent_value')
            totals = {
                'total1_app': t1a, 'total1_resp': t1r,
                'total2_app': t2a, 'total2_resp': t2r,
                'total3_app': m_prop_app - m_debt_app,
                'total3_resp': m_prop_resp - m_debt_resp,
                'total4_app': _sum(excluded_properties, 'applicant_value'),
                'total4_resp': _sum(excluded_properties, 'respondent_value'),
            }
            totals['total5_app'] = totals['total2_app'] + totals['total3_app'] + totals['total4_app']
            totals['total5_resp'] = totals['total2_resp'] + totals['total3_resp'] + totals['total4_resp']
            totals['total6_app'] = t1a - totals['total5_app']
            totals['total6_resp'] = t1r - totals['total5_resp']
            equalisation = calculate_equalisation(
                totals.get("total6_app", 0),
                totals.get("total6_resp", 0)
            )
        else:
            assets = debts = marriage_properties = marriage_debts = excluded_properties = []
            final_totals = None
            totals = {}
        context = {
            'form': form_obj,
            'statement': form_obj,
            'assets': assets,
            'debts': debts,
            'marriage_properties': marriage_properties,
            'marriage_debts': marriage_debts,
            'excluded_properties': excluded_properties,
            'final_totals': final_totals,
            'totals': totals,
            'print_event': print_event,
            "equalisation": equalisation,
            'view_only': True,
        }
    elif print_event.form_type == 'comparison_nfp':
        form_obj = ComparisonNetFamilyProperty.objects.filter(pk=print_event.form_id).first()
        template = 'forms/comparison_nfp_printed_view.html'
        context = {
            'form': form_obj,
            'print_event': print_event,
            'view_only': True,
            'pk': form_obj.pk if form_obj else None,
        }
    elif print_event.form_type == 'application_divorce_8a':
        form_obj = ApplicationDivorce8A.objects.filter(pk=print_event.form_id).first()
        template = 'forms/application_divorce_8a_print_view.html'
        context = {
            'application': form_obj,
            'print_event': print_event,
            'view_only': True,
        }
    elif print_event.form_type == 'affidavit_service':
        form_obj = AffidavitOfService.objects.filter(pk=print_event.form_id).first()
        template = 'forms/affidavit_service_print_view.html'
        context = {
            'affidavit': form_obj,
            'print_event': print_event,
            'view_only': True,
        }
    else:
        return render(request, 'forms/printed_copy_not_supported.html', {'print_event': print_event})

    if not form_obj:
        return render(request, 'forms/printed_copy_not_found.html', {'print_event': print_event})

    return render(request, template, context)

@login_required
def affidavit_service_create(request):
    case_id = request.GET.get("case_id")
    case_file = CaseFile.objects.filter(pk=case_id, owner=request.user).first() if case_id else None

    initial = {}

    if case_file:
        initial = {
            "case_file": case_file,
            "court_name": case_file.court_name,
            "court_file_number": case_file.court_file_number,
            "court_office_address": case_file.court_office_address,
            "plaintiff_name": case_file.applicant_name,
            "defendant_name": case_file.respondent_name,
        }

    if request.method == "POST":
        form = AffidavitOfServiceForm(request.POST)

        if form.is_valid():
            affidavit = form.save()
            return redirect("affidavit_service_view", pk=affidavit.pk)
    else:
        form = AffidavitOfServiceForm(initial=initial)

    return render(request, "forms/affidavit_service_create.html", {
        "form": form,
        "case_file": case_file,
    })


@login_required
def affidavit_service_page1(request, pk=None):
    affidavit = get_object_or_404(AffidavitOfService, pk=pk) if pk else None

    case = None
    case_id = request.GET.get("case_id") or request.POST.get("case_id")
    initial = {}

    def service_block(name="", address="", phone="", email=""):
        parts = []

        if name:
            parts.append(str(name).strip())

        if address:
            parts.append(str(address).strip())

        if phone:
            parts.append(f"Phone / fax: {phone}")

        if email:
            parts.append(f"Email: {email}")

        return "\n".join(parts)

    if case_id and not affidavit:
        case = CaseFile.objects.filter(
            pk=case_id,
            owner=request.user
        ).first()

        if case:
            initial = {
                "court_name": case.court_name or "",
                "court_file_number": case.court_file_number or "",
                "court_office_address": case.court_office_address or "",

                "plaintiff_name": service_block(
                    case.applicant_name,
                    case.applicant_address,
                    case.applicant_phone,
                    case.applicant_email,
                ),

                "applicant_lawyer_details": service_block(
                    case.applicant_lawyer_name,
                    case.applicant_lawyer_address,
                    case.applicant_lawyer_phone,
                    case.applicant_lawyer_email,
                ),

                "defendant_name": service_block(
                    case.respondent_name,
                    case.respondent_address,
                    case.respondent_phone,
                    case.respondent_email,
                ),

                "respondent_lawyer_details": service_block(
                    case.respondent_lawyer_name,
                    case.respondent_lawyer_address,
                    case.respondent_lawyer_phone,
                    case.respondent_lawyer_email,
                ),
            }

    variant = request.GET.get("variant") or request.POST.get("variant")

    if variant not in (
        AffidavitOfService.FORM_VARIANT_6B,
        AffidavitOfService.FORM_VARIANT_8A,
    ):
        variant = AffidavitOfService.FORM_VARIANT_6B

    if request.method == "POST":
        form = AffidavitServicePage1Form(
            request.POST,
            instance=affidavit
        )

        if form.is_valid():
            affidavit = form.save(commit=False)

            if case_id and not affidavit.case_file_id:
                case = CaseFile.objects.filter(
                    pk=case_id,
                    owner=request.user
                ).first()

                if case:
                    affidavit.case_file = case

            affidavit.form_variant = variant
            affidavit.save()

            return redirect("affidavit_service_page2", pk=affidavit.pk)

    else:
        form = AffidavitServicePage1Form(
            instance=affidavit,
            initial=initial
        )

    case_list = CaseFile.objects.filter(
        owner=request.user
    ).order_by("-updated_at") if not affidavit else None

    return render(request, "forms/affidavit_service_page1.html", {
        "form": form,
        "affidavit": affidavit,
        "case_list": case_list,
        "selected_case": case,
        "variant": variant,
    })

@login_required
def affidavit_service_page2(request, pk):
    affidavit = get_object_or_404(AffidavitOfService, pk=pk)

    if request.method == "POST":
        form = AffidavitServicePage2Form(
            request.POST,
            instance=affidavit
        )

        if form.is_valid():
            affidavit = form.save()
            return redirect("affidavit_service_page3", pk=affidavit.pk)

    else:
        form = AffidavitServicePage2Form(instance=affidavit)

    return render(request, "forms/affidavit_service_page2.html", {
        "form": form,
        "affidavit": affidavit,
    })

@login_required
def affidavit_service_page3(request, pk):
    affidavit = get_object_or_404(AffidavitOfService, pk=pk)

    if request.method == "POST":
        form = AffidavitServicePage3Form(
            request.POST,
            instance=affidavit
        )

        if form.is_valid():
            affidavit = form.save()
            return redirect("affidavit_service_view", pk=affidavit.pk)

    else:
        form = AffidavitServicePage3Form(instance=affidavit)

    return render(request, "forms/affidavit_service_page3.html", {
        "form": form,
        "affidavit": affidavit,
    })


@login_required
def affidavit_service_view(request, pk):

    affidavit = get_object_or_404(
        AffidavitOfService,
        pk=pk
    )

    return render(
        request,
        "forms/affidavit_service_view.html",
        {
            "affidavit": affidavit
        }
    )


@login_required
def affidavit_service_print(request, pk):

    affidavit = get_object_or_404(
        AffidavitOfService,
        pk=pk
    )

    print_event = PrintEvent.log_print(
        user=request.user,
        form_type='affidavit_service',
        form_id=pk,
        form_identifier=affidavit.court_file_number or f'Affidavit of Service #{pk}'
    )

    log_audit(
        request,
        'export',
        'affidavit_service',
        pk,
        f'Affidavit of Service #{pk}',
        f'Printed - Price: ${print_event.price_charged}'
    )

    send_form_printed_notification(
        'affidavit_service',
        affidavit,
        request.user,
        print_event.price_charged
    )

    return render(
        request,
        "forms/affidavit_service_print.html",
        {
            "affidavit": affidavit
        }
    )


@login_required
def affidavit_service_list(request):
    affidavits = AffidavitOfService.objects.filter(
        is_deleted=False
    ).order_by("-updated_at")

    perms = user_permissions(request).get(
        "user_permissions",
        {}
    ).get(
        "affidavit_service",
        {}
    )

    for affidavit in affidavits:
        affidavit.can_view = request.user.is_superuser or perms.get("view", False)
        affidavit.can_edit = request.user.is_superuser or perms.get("edit", False)
        affidavit.can_print = request.user.is_superuser or perms.get("print", False)
        affidavit.can_delete = request.user.is_superuser or perms.get("delete", False)

    return render(request, "forms/affidavit_service_list.html", {
        "affidavits": affidavits,
    })


@login_required
def affidavit_service_print_view(request, pk):

    affidavit = get_object_or_404(
        AffidavitOfService,
        pk=pk
    )

    return render(
        request,
        "forms/affidavit_service_print_view.html",
        {
            "affidavit": affidavit
        }
    )


@login_required
def affidavit_service_delete(request, pk):
    item = get_object_or_404(AffidavitOfService, pk=pk)

    if request.method == "POST":
        item.soft_delete()
        messages.success(request, "Affidavit of Service deleted successfully.")
        return redirect("affidavit_service_list")

    return render(request, "forms/confirm_delete.html", {
        "object": item,
        "object_label": "Affidavit of Service",
        "cancel_url": "affidavit_service_list",
    })

@login_required
def certificate_of_divorce_delete(request, pk):

    item = get_object_or_404(
        CertificateOfDivorce,
        pk=pk
    )

    if request.method == "POST":

        item.soft_delete()

        messages.success(
            request,
            "Certificate of Divorce deleted successfully."
        )

        return redirect("certificate_of_divorce_list")

    return render(
        request,
        "forms/confirm_delete.html",
        {
            "object": item,
            "object_label": "Certificate of Divorce",
            "cancel_url": "certificate_of_divorce_list",
        }
    )

def _build_certificate_case_initial(case):
    if not case:
        return {}

    def service_block(address="", phone="", email=""):
        parts = []
        if address:
            parts.append(str(address).strip())
        if phone:
            parts.append(f"Phone / fax: {phone}")
        if email:
            parts.append(f"Email: {email}")
        return "\n".join(parts)

    return {
        "court_name": case.court_name or "",
        "court_file_number": case.court_file_number or "",
        "court_office_address": case.court_office_address or "",

        "applicant_name": case.applicant_name or "",
        "applicant_address": service_block(case.applicant_address, case.applicant_phone, case.applicant_email),

        "applicant_lawyer_name": case.applicant_lawyer_name or "",
        "applicant_lawyer_address": service_block(case.applicant_lawyer_address, case.applicant_lawyer_phone, case.applicant_lawyer_email),

        "respondent_name": case.respondent_name or "",
        "respondent_address": service_block(case.respondent_address, case.respondent_phone, case.respondent_email),

        "respondent_lawyer_name": case.respondent_lawyer_name or "",
        "respondent_lawyer_address": service_block(case.respondent_lawyer_address, case.respondent_lawyer_phone, case.respondent_lawyer_email),
    }


@login_required
def certificate_of_divorce_create(request):
    case_file = None
    case_id = request.GET.get("case_id") or request.POST.get("case_id")

    if case_id:
        case_file = CaseFile.objects.filter(pk=case_id, owner=request.user).first()

    initial = _build_certificate_case_initial(case_file) if case_file else {}

    if request.method == "POST":
        form = CertificateOfDivorceForm(request.POST)

        if form.is_valid():
            cert = form.save(commit=False)

            if case_file:
                cert.case_file = case_file

            cert.save()
            send_form_created_notification("certificate_of_divorce", cert, request.user)

            return redirect("certificate_of_divorce_view", pk=cert.pk)
    else:
        form = CertificateOfDivorceForm(initial=initial)

    case_list = CaseFile.objects.filter(owner=request.user).order_by("-updated_at")

    return render(request, "forms/certificate_of_divorce_create.html", {
        "form": form,
        "case_list": case_list,
        "selected_case": case_file,
    })


@login_required
def certificate_of_divorce_page1(request, pk=None):
    certificate = get_object_or_404(CertificateOfDivorce, pk=pk) if pk else None

    case_id = request.GET.get("case_id") or request.POST.get("case_id")
    selected_case = None

    if case_id:
        selected_case = CaseFile.objects.filter(pk=case_id, owner=request.user).first()
    elif certificate and certificate.case_file:
        selected_case = certificate.case_file

    initial = _build_certificate_case_initial(selected_case) if selected_case and not certificate else {}

    if request.method == "POST":
        form = CertificateOfDivorceForm(request.POST, instance=certificate)

        if form.is_valid():
            obj = form.save(commit=False)

            if selected_case:
                obj.case_file = selected_case

            obj.save()
            return redirect("certificate_of_divorce_view", pk=obj.pk)
    else:
        form = CertificateOfDivorceForm(instance=certificate, initial=initial)

    case_list = CaseFile.objects.filter(owner=request.user).order_by("-updated_at")

    return render(request, "forms/certificate_of_divorce_page1.html", {
        "form": form,
        "certificate": certificate,
        "case_list": case_list,
        "selected_case": selected_case,
    })


def _build_certificate_case_initial(case):
    if not case:
        return {}

    def service_block(address="", phone="", email=""):
        parts = []
        if address:
            parts.append(str(address).strip())
        if phone:
            parts.append(f"Phone / fax: {phone}")
        if email:
            parts.append(f"Email: {email}")
        return "\n".join(parts)

    return {
        "court_name": case.court_name or "",
        "court_file_number": case.court_file_number or "",
        "court_office_address": case.court_office_address or "",

        "applicant_name": case.applicant_name or "",
        "applicant_address": service_block(
            case.applicant_address,
            case.applicant_phone,
            case.applicant_email,
        ),

        "applicant_lawyer_name": case.applicant_lawyer_name or "",
        "applicant_lawyer_address": service_block(
            case.applicant_lawyer_address,
            case.applicant_lawyer_phone,
            case.applicant_lawyer_email,
        ),

        "respondent_name": case.respondent_name or "",
        "respondent_address": service_block(
            case.respondent_address,
            case.respondent_phone,
            case.respondent_email,
        ),

        "respondent_lawyer_name": case.respondent_lawyer_name or "",
        "respondent_lawyer_address": service_block(
            case.respondent_lawyer_address,
            case.respondent_lawyer_phone,
            case.respondent_lawyer_email,
        ),
    }

@login_required
def divorce_order_page(request, pk=None):
    order = get_object_or_404(DivorceOrder, pk=pk)

    case = None
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    initial = {}
    if case_id and not order.case_file:
        case = CaseFile.objects.filter(pk=case_id, owner=request.user).first()
        if case:
            initial = _build_case_initial(case)

    if request.method == 'POST':
        form = DivorceOrderForm(request.POST, instance=order)
        if form.is_valid():
            if case_id and not order.case_file:
                case = CaseFile.objects.filter(pk=case_id, owner=request.user).first()
                if case:
                    form.instance.case_file = case
                    _apply_case_fields_to_instance(form.instance, case, overwrite=False)
            order = form.save()
            return redirect('divorce_order_view', pk=order.pk)
    else:
        form = DivorceOrderForm(instance=order, initial=initial)

    case_list = CaseFile.objects.filter(owner=request.user) if not order.case_file else None
    return render(request, 'forms/divorce_order_page.html', {
        'form': form,
        'order': order,
        'case_list': case_list,
        'selected_case': case,
    })


@login_required
def certificate_of_divorce_view(request, pk):
    cert = get_object_or_404(CertificateOfDivorce, pk=pk)
    return render(request, 'forms/certificate_of_divorce_view.html', {'certificate': cert})


@login_required
def divorce_order_list(request):

    orders = DivorceOrder.objects.all().order_by("-updated_at")

    perms = user_permissions(request).get(
        "user_permissions",
        {}
    ).get(
        "divorce_order",
        {}
    )

    for order in orders:
        order.can_view = request.user.is_superuser or perms.get("view", False)
        order.can_edit = request.user.is_superuser or perms.get("edit", False)
        order.can_print = request.user.is_superuser or perms.get("print", False)
        order.can_delete = request.user.is_superuser or perms.get("delete", False)

    return render(
        request,
        "forms/divorce_order_list.html",
        {
            "orders": orders,
        }
    )


@login_required
def divorce_order_onepage_list(request):
    """List view for A-25A Divorce Orders.

    This is a separate form model and rendering path from the standard
    Form 25A Divorce Order.
    """
    orders = DivorceOrderA25A.objects.all().order_by("-updated_at")

    perms = user_permissions(request).get(
        "user_permissions",
        {}
    ).get(
        "divorce_order",
        {}
    )

    for order in orders:
        order.can_view = request.user.is_superuser or perms.get("view", False)
        order.can_edit = request.user.is_superuser or perms.get("edit", False)
        order.can_print = request.user.is_superuser or perms.get("print", False)
        order.can_delete = request.user.is_superuser or perms.get("delete", False)

    return render(request, "forms/divorce_order_onepage_list.html", {"orders": orders})


@login_required
def divorce_order_a25a_create(request):
    case = None
    case_id = request.GET.get("case_id") or request.POST.get("case_id")

    if case_id:
        case = CaseFile.objects.filter(
            pk=case_id,
            owner=request.user
        ).first()

    initial = _build_divorce_order_case_initial(case) if case else {}

    if request.method == "POST":
        form = DivorceOrderA25AForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False)

            if case:
                order.case_file = case

            order.save()

            send_form_created_notification(
                "divorce_order_a25a",
                order,
                request.user
            )

            return redirect("divorce_order_a25a_view", pk=order.pk)

    else:
        form = DivorceOrderA25AForm(initial=initial)

    case_list = CaseFile.objects.filter(
        owner=request.user
    ).order_by("-updated_at")

    return render(request, "forms/divorce_order_a25a_create.html", {
        "form": form,
        "case_list": case_list,
        "selected_case": case,
    })


@login_required
def divorce_order_a25a_page(request, pk=None):
    order = get_object_or_404(DivorceOrderA25A, pk=pk)
    case = order.case_file
    case_id = request.GET.get("case_id") or request.POST.get("case_id")

    if case_id:
        case = CaseFile.objects.filter(
            pk=case_id,
            owner=request.user
        ).first()

    initial = _build_divorce_order_case_initial(case) if case else {}

    if request.method == "POST":
        form = DivorceOrderA25AForm(request.POST, instance=order)

        if form.is_valid():
            order = form.save(commit=False)

            if case:
                order.case_file = case

            order.save()
            return redirect('divorce_order_a25a_view', pk=order.pk)

    else:
        form = DivorceOrderA25AForm(instance=order, initial=initial)

    case_list = CaseFile.objects.filter(
        owner=request.user
    ).order_by("-updated_at")

    return render(request, 'forms/divorce_order_a25a_page.html', {
        'form': form,
        'order': order,
        'case_list': case_list,
        'selected_case': case,
    })


@login_required
def divorce_order_a25a_view(request, pk):
    order = get_object_or_404(DivorceOrderA25A, pk=pk)
    return render(request, 'forms/divorce_order_a25a_view.html', {'order': order})


@login_required
def divorce_order_a25a_print(request, pk):
    order = get_object_or_404(DivorceOrderA25A, pk=pk)

    print_event = PrintEvent.log_print(
        user=request.user,
        form_type='divorce_order_a25a',
        form_id=pk,
        form_identifier=order.court_file_number or f'Divorce Order A-25A #{pk}'
    )

    log_audit(request, 'export', 'divorce_order_a25a', pk, f'Divorce Order A-25A #{pk}', f'Printed - Price: ${print_event.price_charged}')
    send_form_printed_notification('divorce_order_a25a', order, request.user, print_event.price_charged)

    return render(request, 'forms/divorce_order_a25a_print.html', {'order': order})


@login_required
def divorce_order_a25a_print_view(request, pk):
    order = get_object_or_404(DivorceOrderA25A, pk=pk)
    return render(request, 'forms/divorce_order_a25a_print_view.html', {'order': order})


@login_required
def divorce_order_a25a_delete(request, pk):
    order = get_object_or_404(DivorceOrderA25A, pk=pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, "Divorce Order A-25A deleted successfully.")
        return redirect('divorce_order_onepage_list')

    return render(request, 'forms/confirm_delete.html', {
        'object': order,
        'object_label': 'Divorce Order A-25A',
        'cancel_url': 'divorce_order_onepage_list',
    })


def _build_divorce_order_case_initial(case):
    if not case:
        return {}

    def service_block(address="", phone="", email=""):
        parts = []

        if address:
            parts.append(str(address).strip())

        if phone:
            parts.append(f"Phone / fax: {phone}")

        if email:
            parts.append(f"Email: {email}")

        return "\n".join(parts)

    return {
        "court_name": case.court_name or "",
        "court_file_number": case.court_file_number or "",
        "court_office_address": case.court_office_address or "",

        "applicant_name": case.applicant_name or "",
        "applicant_address": service_block(
            case.applicant_address,
            case.applicant_phone,
            case.applicant_email,
        ),

        "applicant_lawyer_name": case.applicant_lawyer_name or "",
        "applicant_lawyer_address": service_block(
            case.applicant_lawyer_address,
            case.applicant_lawyer_phone,
            case.applicant_lawyer_email,
        ),

        "respondent_name": case.respondent_name or "",
        "respondent_address": service_block(
            case.respondent_address,
            case.respondent_phone,
            case.respondent_email,
        ),

        "respondent_lawyer_name": case.respondent_lawyer_name or "",
        "respondent_lawyer_address": service_block(
            case.respondent_lawyer_address,
            case.respondent_lawyer_phone,
            case.respondent_lawyer_email,
        ),
    }


@login_required
def divorce_order_create(request):
    case = None
    case_id = request.GET.get("case_id") or request.POST.get("case_id")

    if case_id:
        case = CaseFile.objects.filter(
            pk=case_id,
            owner=request.user
        ).first()

    initial = _build_divorce_order_case_initial(case) if case else {}

    if request.method == "POST":
        form = DivorceOrderForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False)

            if case:
                order.case_file = case

            order.save()

            send_form_created_notification(
                "divorce_order",
                order,
                request.user
            )

            return redirect("divorce_order_view", pk=order.pk)

    else:
        form = DivorceOrderForm(initial=initial)

    case_list = CaseFile.objects.filter(
        owner=request.user
    ).order_by("-updated_at")

    return render(request, "forms/divorce_order_create.html", {
        "form": form,
        "case_list": case_list,
        "selected_case": case,
    })
@login_required
def divorce_order_view(request, pk):
    order = get_object_or_404(DivorceOrder, pk=pk)
    return render(request, 'forms/divorce_order_view.html', {'order': order})


@login_required
def divorce_order_print(request, pk):
    order = get_object_or_404(DivorceOrder, pk=pk)

    print_event = PrintEvent.log_print(
        user=request.user,
        form_type='divorce_order',
        form_id=pk,
        form_identifier=order.court_file_number or f'Divorce Order #{pk}'
    )

    log_audit(request, 'export', 'divorce_order', pk, f'Divorce Order #{pk}', f'Printed - Price: ${print_event.price_charged}')
    send_form_printed_notification('divorce_order', order, request.user, print_event.price_charged)

    return render(request, 'forms/divorce_order_print.html', {'order': order})


@login_required
def divorce_order_print_view(request, pk):
    order = get_object_or_404(DivorceOrder, pk=pk)
    return render(request, 'forms/divorce_order_print_view.html', {'order': order})


@login_required
def divorce_order_print_onepage(request, pk):
    """Render a one-page print-friendly version of the divorce order.

    This logs a print event and sends the same notifications as the
    multi-page print view but uses the single-page template.
    """
    order = get_object_or_404(DivorceOrder, pk=pk)

    print_event = PrintEvent.log_print(
        user=request.user,
        form_type='divorce_order_onepage',
        form_id=pk,
        form_identifier=order.court_file_number or f'Divorce Order #{pk}'
    )

    log_audit(request, 'export', 'divorce_order', pk, f'Divorce Order (onepage) #{pk}', f'Printed - Price: ${print_event.price_charged}')
    send_form_printed_notification('divorce_order', order, request.user, print_event.price_charged)

    return render(request, 'forms/divorce_order_onepage.html', {'order': order})


@login_required
def divorce_order_delete(request, pk):
    order = get_object_or_404(DivorceOrder, pk=pk)

    if request.method == "POST":
        order.soft_delete()
        messages.success(request, "Divorce Order deleted successfully.")
        return redirect("divorce_order_list")

    return render(request, "forms/confirm_delete.html", {
        "object": order,
        "object_label": "Divorce Order",
        "cancel_url": "divorce_order_list",
    })


@login_required
def certificate_of_divorce_print(request, pk):
    cert = get_object_or_404(CertificateOfDivorce, pk=pk)

    print_event = PrintEvent.log_print(
        user=request.user,
        form_type='certificate_of_divorce',
        form_id=pk,
        form_identifier=cert.court_file_number or f'Certificate of Divorce #{pk}'
    )

    log_audit(request, 'export', 'certificate_of_divorce', pk, f'Certificate of Divorce #{pk}', f'Printed - Price: ${print_event.price_charged}')

    send_form_printed_notification('certificate_of_divorce', cert, request.user, print_event.price_charged)

    return render(request, 'forms/certificate_of_divorce_print.html', {'certificate': cert})


@login_required
def certificate_of_divorce_list(request):
    certs = CertificateOfDivorce.objects.all().order_by('-updated_at')
    
    # Pre-calculate permissions for each certificate
    perms = user_permissions(request).get('user_permissions', {}).get('certificate_of_divorce', {})
    for cert in certs:
        cert.can_view = request.user.is_superuser or perms.get('view', False)
        cert.can_edit = request.user.is_superuser or perms.get('edit', False)
        cert.can_print = request.user.is_superuser or perms.get('print', False)
        cert.can_delete = request.user.is_superuser or perms.get('delete', False)
    
    return render(request, 'forms/certificate_of_divorce_list.html', {'certificates': certs})


@login_required
def certificate_of_divorce_print_view(request, pk):
    cert = get_object_or_404(CertificateOfDivorce, pk=pk)
    return render(request, 'forms/certificate_of_divorce_print_view.html', {'certificate': cert})


@login_required
def divorce_order_delete(request, pk):
    item = get_object_or_404(DivorceOrder, pk=pk)

    if request.method == "POST":
        item.soft_delete()
        messages.success(request, "Divorce Order deleted successfully.")
        return redirect("divorce_order_list")

    return render(request, "forms/confirm_delete.html", {
        "object": item,
        "object_label": "Divorce Order",
        "cancel_url": "divorce_order_list",
    })

@login_required
def application_divorce_8a_list(request):
    applications = ApplicationDivorce8A.objects.all().order_by("-updated_at")
    
    # Pre-calculate permissions for each application
    for app in applications:
        app.can_view = request.user.is_superuser or user_permissions(request).get('user_permissions', {}).get('application_divorce_8a', {}).get('view', False)
        app.can_edit = request.user.is_superuser or user_permissions(request).get('user_permissions', {}).get('application_divorce_8a', {}).get('edit', False)
        app.can_print = request.user.is_superuser or user_permissions(request).get('user_permissions', {}).get('application_divorce_8a', {}).get('print', False)
        app.can_delete = request.user.is_superuser or user_permissions(request).get('user_permissions', {}).get('application_divorce_8a', {}).get('delete', False)
    
    return render(request, "forms/application_divorce_8a_list.html", {
        "applications": applications
    })


@login_required
def application_divorce_8a_create(request):
    # Allow creating with a CaseFile via ?case_id=
    case = None
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    if case_id:
        case = CaseFile.objects.filter(pk=case_id, owner=request.user).first()

    application = ApplicationDivorce8A.objects.create()
    if case:
        _apply_case_fields_to_instance(application, case, overwrite=True)
        application.case_file = case
        application.save()

    return redirect("application_divorce_8a_page1", pk=application.pk)


@login_required
def application_divorce_8a_page1(request, pk):
    application = get_object_or_404(ApplicationDivorce8A, pk=pk)
    # Support prefill from CaseFile via ?case_id=
    case = None
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    initial = {}
    if case_id:
        case = CaseFile.objects.filter(pk=case_id, owner=request.user).first()
        if case:
            initial = _build_case_initial(case)
            # Apply case fields to the instance for display (don't save)
            if not application.case_file:
                _apply_case_fields_to_instance(application, case, overwrite=False)
    elif application.case_file:
        case = application.case_file
        if not application.court_file_number:
            application.court_file_number = application.case_file.court_file_number or ""

    if request.method == "POST":
        form = ApplicationDivorce8APage1Form(request.POST, instance=application)
        if form.is_valid():
            if case_id and not application.case_file:
                case = CaseFile.objects.filter(pk=case_id, owner=request.user).first()
                if case:
                    form.instance.case_file = case
                    _apply_case_fields_to_instance(form.instance, case, overwrite=False)
            form.save()
            return redirect("application_divorce_8a_page2", pk=application.pk)
    else:
        form = ApplicationDivorce8APage1Form(instance=application, initial=initial)

    case_list = CaseFile.objects.filter(owner=request.user)
    return render(request, "forms/application_divorce_8a_page1.html", {
        "form": form,
        "application": application,
        "case_list": case_list,
        "selected_case": case,
    })

@login_required
def application_divorce_8a_page2(request, pk):
    application = get_object_or_404(ApplicationDivorce8A, pk=pk)

    case = None
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    initial = {}
    if case_id and not application.case_file:
        case = CaseFile.objects.filter(pk=case_id, owner=request.user).first()
        if case:
            initial = _build_case_initial(case)
            # Apply case fields to the instance for display (don't save)
            _apply_case_fields_to_instance(application, case, overwrite=False)

    if not application.court_file_number and application.case_file:
        application.court_file_number = application.case_file.court_file_number or ""

    if request.method == "POST":
        form = ApplicationDivorce8APage2Form(
            request.POST,
            instance=application
        )

        if form.is_valid():
            if case_id and not application.case_file:
                case = CaseFile.objects.filter(pk=case_id, owner=request.user).first()
                if case:
                    form.instance.case_file = case
                    _apply_case_fields_to_instance(form.instance, case, overwrite=False)
            form.instance.court_file_number = _resolve_application_court_file_number(
                application,
                request.POST.get("court_file_number")
            )
            form.save()
            return redirect("application_divorce_8a_page3", pk=application.pk)

    else:
        form = ApplicationDivorce8APage2Form(instance=application, initial=initial)

    case_list = CaseFile.objects.filter(owner=request.user) if not application.case_file else None
    return render(request, "forms/application_divorce_8a_page2.html", {
        "form": form,
        "application": application,
        "pk": pk,
        "case_list": case_list,
        "selected_case": case,
    })


@login_required
def application_divorce_8a_page3(request, pk):
    application = get_object_or_404(ApplicationDivorce8A, pk=pk)

    case = None
    case_id = request.GET.get('case_id') or request.POST.get('case_id')
    initial = {}
    if case_id and not application.case_file:
        case = CaseFile.objects.filter(pk=case_id, owner=request.user).first()
        if case:
            initial = _build_case_initial(case)

    if not application.court_file_number and application.case_file:
        application.court_file_number = application.case_file.court_file_number or ""

    if request.method == "POST":
        form = ApplicationDivorce8APage3Form(request.POST, instance=application)
        if form.is_valid():
            if case_id and not application.case_file:
                case = CaseFile.objects.filter(pk=case_id, owner=request.user).first()
                if case:
                    form.instance.case_file = case
                    _apply_case_fields_to_instance(form.instance, case, overwrite=False)
            form.instance.court_file_number = _resolve_application_court_file_number(
                application,
                request.POST.get("court_file_number")
            )
            form.save()
            return redirect("application_divorce_8a_page4", pk=application.pk)
    else:
        form = ApplicationDivorce8APage3Form(instance=application, initial=initial)

    case_list = CaseFile.objects.filter(owner=request.user) if not application.case_file else None
    return render(request, "forms/application_divorce_8a_page3.html", {
        "form": form,
        "application": application,
        "case_list": case_list,
        "selected_case": case,
    })


@login_required
def application_divorce_8a_page4(request, pk):
    application = get_object_or_404(ApplicationDivorce8A, pk=pk)

    checkbox_fields = [
        # All checkbox/boolean fields used on Page 4 & related facts
        "claim_divorce",
        "claim_spousal_support",
        "claim_child_support_table",
        "claim_child_support_other",
        "claim_decision_making",
        "claim_parenting_time",

        # Family Law specific child support
        "claim_support_child_table_family_law",
        "claim_support_child_other_family_law",

        "claim_restraining_order",
        "claim_indexing_spousal_support",
        "claim_declaration_parentage",
        "claim_guardianship_child_property",

        # Property
        "claim_property_equalization",
        "claim_exclusive_possession_home",
        "claim_exclusive_possession_contents",
        "claim_freezing_assets",
        "claim_sale_family_property",

        # Other claims
        "claim_costs",
        "claim_annulment",
        "claim_prejudgment_interest",
        "claim_other",

        # Simple divorce frame
        "simple_claim_divorce",
        "simple_claim_costs",

        # Divorce facts
        "divorce_ground_separation",
        "not_lived_together_since",
        "lived_together_attempt_reconcile",
        "divorce_ground_adultery",
        # divorce_ground_cruelty is handled on page 5, not page 4
    ]

    if not application.court_file_number and application.case_file:
        application.court_file_number = application.case_file.court_file_number or ""

    if request.method == "POST":
        form = ApplicationDivorce8APage4Form(request.POST, instance=application)

        if form.is_valid():
            obj = form.save(commit=False)

            # Keep court file number from Page 1 if Page 4 field is empty
            obj.court_file_number = _resolve_application_court_file_number(
                application,
                request.POST.get("court_file_number")
            )

            # Manually save all checkboxes
            for field in checkbox_fields:
                if hasattr(obj, field):
                    setattr(obj, field, field in request.POST)

            obj.save()

            return redirect("application_divorce_8a_page5", pk=obj.pk)

    else:
        form = ApplicationDivorce8APage4Form(instance=application)

    return render(request, "forms/application_divorce_8a_page4.html", {
        "form": form,
        "application": application,
        "selected_case": application.case_file,
    })
@login_required
def application_divorce_8a_page5(request, pk):
    application = get_object_or_404(ApplicationDivorce8A, pk=pk)
    missing_certificate = bool(request.GET.get("missing_certificate"))

    if request.method == "POST":
        form = ApplicationDivorce8APage5Form(request.POST, instance=application)
        if form.is_valid():
            obj = form.save(commit=False)

            # Preserve court file number
            obj.court_file_number = _resolve_application_court_file_number(
                application,
                request.POST.get("court_file_number")
            )

            # Ensure cruelty fields save even if template rendering varied
            obj.divorce_ground_cruelty = "divorce_ground_cruelty" in request.POST
            obj.cruelty_spouse_name = request.POST.get("cruelty_spouse_name") or obj.cruelty_spouse_name
            obj.cruelty_victim_name = request.POST.get("cruelty_victim_name") or obj.cruelty_victim_name
            obj.cruelty_details = request.POST.get("cruelty_details") or obj.cruelty_details

            # Applicant certificate
            obj.applicant_certificate_confirmed = "applicant_certificate_confirmed" in request.POST

            obj.save()
            return redirect("application_divorce_8a_page6", pk=application.pk)
    else:
        if not application.court_file_number and application.case_file:
            application.court_file_number = application.case_file.court_file_number or ""
        form = ApplicationDivorce8APage5Form(instance=application)

    return render(request, "forms/application_divorce_8a_page5.html", {
        "form": form,
        "application": application,
        "missing_certificate": missing_certificate,
    })


@login_required
def application_divorce_8a_page6(request, pk):
    application = get_object_or_404(ApplicationDivorce8A, pk=pk)

    if request.method == "POST":
        form = ApplicationDivorce8APage6Form(request.POST, request.FILES, instance=application)
        if form.is_valid():
            # Preserve court file number
            form.instance.court_file_number = _resolve_application_court_file_number(
                application,
                request.POST.get("court_file_number")
            )

            # Require applicant certificate (Page 5) before final submission
            if not application.applicant_certificate_confirmed and not form.instance.applicant_certificate_confirmed:
                messages.error(request, "You must confirm the applicant's certificate on Page 5 before submitting the form.")
                # Redirect back to page 5 and show inline warning
                return HttpResponseRedirect(reverse("application_divorce_8a_page5", kwargs={"pk": application.pk}) + "?missing_certificate=1")

            form.save()
            # mark completed
            application.is_completed = True
            application.save()
            messages.success(request, "Form 8A submitted successfully.")
            return redirect("application_divorce_8a_view", pk=application.pk)
    else:
        if not application.court_file_number and application.case_file:
            application.court_file_number = application.case_file.court_file_number or ""
        form = ApplicationDivorce8APage6Form(instance=application)

    return render(request, "forms/application_divorce_8a_page6.html", {
        "form": form,
        "application": application,
    })


@login_required
def application_divorce_8a_view(request, pk):
    application = get_object_or_404(ApplicationDivorce8A, pk=pk)
    return render(request, "forms/application_divorce_8a_view.html", {
        "application": application,
        "pk": pk,
    })


@login_required
def application_divorce_8a_print(request, pk):
    application = get_object_or_404(ApplicationDivorce8A, pk=pk)

    print_event = PrintEvent.log_print(
        user=request.user,
        form_type="application_divorce_8a",
        form_id=pk,
        form_identifier=application.court_file_number or f"Form 8A #{pk}"
    )

    log_audit(
        request,
        "export",
        "application_divorce_8a",
        pk,
        f"Form 8A #{pk}",
        f"Printed - Price: ${print_event.price_charged}"
    )

    send_form_printed_notification(
        "application_divorce_8a",
        application,
        request.user,
        print_event.price_charged
    )

    children = []
    if application.children_details:
        try:
            parsed_children = json.loads(application.children_details)
            if isinstance(parsed_children, dict):
                children = [parsed_children]
            elif isinstance(parsed_children, list):
                children = parsed_children
        except (ValueError, TypeError):
            children = []

    return render(request, "forms/application_divorce_8a_print.html", {
        "application": application,
        "pk": pk,
        "children": children,
    })

@login_required
def application_divorce_8a_delete(request, pk):
    item = get_object_or_404(ApplicationDivorce8A, pk=pk)

    if request.method == "POST":
        item.soft_delete()
        messages.success(request, "Form 8A Divorce Application deleted successfully.")
        return redirect("application_divorce_8a_list")

    return render(request, "forms/confirm_delete.html", {
        "object": item,
        "object_label": "Form 8A Divorce Application",
        "cancel_url": "application_divorce_8a_list",
    })