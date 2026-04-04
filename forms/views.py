# forms/views.py - Comprehensive version with all data saving properly
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.forms import modelformset_factory, inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from functools import lru_cache
from pathlib import Path
from collections import OrderedDict
import re
import json
from decimal import Decimal, InvalidOperation
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

# Email notifications
from .notifications import send_form_created_notification, send_form_printed_notification

# Audit logging
from users.models import AuditLog


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit(request, action, module, object_id='', object_repr='', details=''):
    """
    Helper to log user actions to AuditLog.
    
    Args:
        request: The HTTP request
        action: Action type (create, update, delete, view, export)
        module: Module name (e.g., 'financial_statement_131', 'comparison_nfp')
        object_id: ID of the object being acted upon
        object_repr: Human-readable representation of the object
        details: Additional details about the action
    """
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        module=module,
        object_id=str(object_id) if object_id else '',
        object_repr=object_repr[:255] if object_repr else '',
        details=details,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
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

    # Billing & Print tracking
    PrintEvent,
)
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


# ============================================================
# DASHBOARD
# ============================================================
@login_required
def dashboard(request):
    """Main dashboard showing all form types."""
    financial_statements = FinancialStatement.objects.all().order_by('-updated_at')
    net_family_13b = NetFamilyProperty13B.objects.all().order_by('-updated_at')
    comparison_nfp = ComparisonNetFamilyProperty.objects.all().order_by('-updated_at')
    
    context = {
        'financial_statements': financial_statements[:5],
        'financial_statements_count': financial_statements.count(),
        'net_family_13b': net_family_13b[:5],
        'net_family_13b_count': net_family_13b.count(),
        'comparison_nfp': comparison_nfp[:5],
        'comparison_nfp_count': comparison_nfp.count(),
        'total_forms': financial_statements.count() + net_family_13b.count() + comparison_nfp.count(),
    }
    return render(request, "forms/dashboard.html", context)


# ============================================================
# FINANCIAL STATEMENT (FORM 13) - 8 PAGES
# ============================================================

# ============================================================
# FINANCIAL STATEMENT (FORM 13.1) - Property & Support Claims (Page 1)
# ============================================================

@csrf_exempt
@login_required
def financial_statement_131_page1_new(request):
    """View for Form 13.1 - Page 1 (new form creation)."""
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
        statement.save()
        statement.save_page_data(1, data)
        
        # Send email notification for new form
        send_form_created_notification('financial_statement_131', statement, request.user)
        
        # Audit log for creation
        log_audit(request, 'create', 'financial_statement_131', statement.pk, 
                  f"Form 13.1 #{statement.pk}", 
                  f"Created - Applicant: {statement.applicant_name or 'N/A'}")
        
        return redirect("financial_statement_131_page2", pk=statement.id)
    return render(request, "forms/financial_statement_131_page1.html", {
        "page_data": {},
    })


# ============================================================
# FINANCIAL STATEMENT (FORM 13.1) - List, Edit, Print (Placeholders)
# ============================================================
@login_required
def financial_statement_131_list(request):
    """List view for Form 13.1 Financial Statements."""
    from .models import Form131FinancialStatement
    statements = Form131FinancialStatement.objects.filter(is_deleted=False).order_by('-updated_at')
    return render(request, "forms/financial_statement_131_list.html", {"statements": statements})

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
    """Use manual court file number if provided, otherwise generate one."""
    manual_value = (posted_value or "").strip()
    if manual_value:
        return manual_value

    existing = (statement.court_file_number or "").strip()
    if existing:
        return existing

    year = statement.created_at.year if statement.created_at else timezone.now().year
    return f"AUTO-{year}-{statement.id:06d}"


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

    fallbacks = {
        "court_file_number": statement.court_file_number or "",
        "applicant_name": statement.applicant_name or "",
        "respondent_name": statement.respondent_name or "",
    }

    for key, value in fallbacks.items():
        if not merged.get(key) and value:
            merged[key] = value
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
    return render(request, "forms/financial_statement_131_page2.html", {"pk": pk, "form": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

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
    return render(request, "forms/financial_statement_131_page3.html", {"pk": pk, "form": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

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
    return render(request, "forms/financial_statement_131_page4.html", {"pk": pk, "form": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

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
    return render(request, "forms/financial_statement_131_page5.html", {"pk": pk, "form": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

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
    return render(request, "forms/financial_statement_131_page6.html", {"pk": pk, "form": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

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
    return render(request, "forms/financial_statement_131_page7.html", {"pk": pk, "form": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

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
    page_data = form.get_page_data(9)
    if request.method == "POST":
        data = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
        form.save_page_data(9, data)
        if "prev" in request.POST:
            return redirect("financial_statement_131_page8", pk=pk)
        return redirect("financial_statement_131_page10", pk=pk)
    return render(request, "forms/financial_statement_131_page9.html", {"pk": pk, "form": form, "page_data": page_data, "page1_data": form.get_page_data(1)})

@csrf_exempt
@login_required
def financial_statement_131_page10(request, pk):
    """Form 13.1 page 10 - Schedule A & B (Final page)."""
    from .models import Form131FinancialStatement
    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    page_data = form.get_page_data(10)
    if request.method == "POST":
        data = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
        form.save_page_data(10, data)
        if "prev" in request.POST:
            return redirect("financial_statement_131_page9", pk=pk)
        return redirect("financial_statement_131_list")
    return render(request, "forms/financial_statement_131_page10.html", {"pk": pk, "form": form, "page_data": page_data, "page1_data": form.get_page_data(1)})


def _calculate_form131_totals(pages):
    """Calculate all totals for Form 13.1 print view."""
    def safe_float(val):
        try:
            return float(val) if val else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    # Get page data
    page5 = pages.get("page5", {})
    page6 = pages.get("page6", {})
    page7 = pages.get("page7", {})
    page8 = pages.get("page8", {})
    page9 = pages.get("page9", {})
    
    # Page 9: Disposed property total
    disposed_total = sum(safe_float(page9.get(f"disposed_{i}_value")) for i in range(1, 6))
    page9["total_disposed"] = f"{disposed_total:.2f}" if disposed_total else ""
    
    # ============ CALCULATE ITEM 22: TOTAL PROPERTY ON VALUATION DATE ============
    # Item 15: Land (page 5) - land_X_valuation
    land_val = sum(safe_float(page5.get(f"land_{i}_valuation")) for i in range(1, 4))
    land_marriage = sum(safe_float(page5.get(f"land_{i}_marriage")) for i in range(1, 4))
    land_today = sum(safe_float(page5.get(f"land_{i}_today")) for i in range(1, 4))
    
    # Item 16: Household items & vehicles (page 5)
    items_val = (safe_float(page5.get("household_goods_valuation")) + 
                 safe_float(page5.get("vehicles_valuation")) + 
                 safe_float(page5.get("jewellery_valuation")) + 
                 safe_float(page5.get("other_items_valuation")))
    items_marriage = (safe_float(page5.get("household_goods_marriage")) + 
                      safe_float(page5.get("vehicles_marriage")) + 
                      safe_float(page5.get("jewellery_marriage")) + 
                      safe_float(page5.get("other_items_marriage")))
    items_today = (safe_float(page5.get("household_goods_today")) + 
                   safe_float(page5.get("vehicles_today")) + 
                   safe_float(page5.get("jewellery_today")) + 
                   safe_float(page5.get("other_items_today")))
    
    # Item 17: Bank accounts (page 6) - bank_X_valuation
    bank_val = sum(safe_float(page6.get(f"bank_{i}_valuation")) for i in range(1, 7))
    bank_marriage = sum(safe_float(page6.get(f"bank_{i}_marriage")) for i in range(1, 7))
    bank_today = sum(safe_float(page6.get(f"bank_{i}_today")) for i in range(1, 7))
    
    # Item 18: Insurance (page 6) - insurance_X_valuation
    insurance_val = sum(safe_float(page6.get(f"insurance_{i}_valuation")) for i in range(1, 4))
    insurance_marriage = sum(safe_float(page6.get(f"insurance_{i}_marriage")) for i in range(1, 4))
    insurance_today = sum(safe_float(page6.get(f"insurance_{i}_today")) for i in range(1, 4))
    
    # Item 19: Business interests (page 6) - business_X_valuation
    business_val = sum(safe_float(page6.get(f"business_{i}_valuation")) for i in range(1, 4))
    business_marriage = sum(safe_float(page6.get(f"business_{i}_marriage")) for i in range(1, 4))
    business_today = sum(safe_float(page6.get(f"business_{i}_today")) for i in range(1, 4))
    
    # Item 20: Money owed to you (page 7) - owed_X_valuation  
    owed_val = sum(safe_float(page7.get(f"owed_{i}_valuation")) for i in range(1, 5))
    owed_marriage = sum(safe_float(page7.get(f"owed_{i}_marriage")) for i in range(1, 5))
    owed_today = sum(safe_float(page7.get(f"owed_{i}_today")) for i in range(1, 5))
    
    # Item 21: Other property (page 7) - other_prop_X_valuation
    other_val = sum(safe_float(page7.get(f"other_prop_{i}_valuation")) for i in range(1, 5))
    other_marriage = sum(safe_float(page7.get(f"other_prop_{i}_marriage")) for i in range(1, 5))
    other_today = sum(safe_float(page7.get(f"other_prop_{i}_today")) for i in range(1, 5))
    
    # Item 22 total
    item_22_total = land_val + items_val + bank_val + insurance_val + business_val + owed_val + other_val
    
    # ============ CALCULATE ITEM 23: TOTAL DEBTS ============
    # Debts (page 7) - debt_X_valuation
    debt_val = sum(safe_float(page7.get(f"debt_{i}_valuation")) for i in range(1, 7))
    debt_marriage = sum(safe_float(page7.get(f"debt_{i}_marriage")) for i in range(1, 7))
    debt_today = sum(safe_float(page7.get(f"debt_{i}_today")) for i in range(1, 7))
    
    # ============ CALCULATE ITEM 24: NET VALUE ON DATE OF MARRIAGE ============
    # DOM assets properties
    dom_asset_keys = ['dom_land_assets', 'dom_items_assets', 'dom_bank_assets', 
                      'dom_insurance_assets', 'dom_business_assets', 'dom_owed_assets', 
                      'dom_other_assets', 'dom_debts_assets']
    dom_liab_keys = ['dom_land_liab', 'dom_items_liab', 'dom_bank_liab', 
                     'dom_insurance_liab', 'dom_business_liab', 'dom_owed_liab', 
                     'dom_other_liab', 'dom_debts_liab']
    
    dom_assets = sum(safe_float(page8.get(k)) for k in dom_asset_keys)
    dom_liab = sum(safe_float(page8.get(k)) for k in dom_liab_keys)
    net_dom = dom_assets - dom_liab  # Item 24
    
    # ============ CALCULATE ITEM 25: VALUE OF ALL DEDUCTIONS ============
    # Item 25 = Item 23 (debts) + Item 24 (net DOM value)
    item_25_total = debt_val + net_dom
    
    # ============ CALCULATE ITEM 26: EXCLUDED PROPERTY ============
    excluded_total = sum(safe_float(page8.get(f"excluded_{i}_value")) for i in range(1, 6))
    
    # ============ NFP CALCULATION ============
    # Always use calculated values for accurate print output
    nfp_item22 = item_22_total
    nfp_item25 = item_25_total
    nfp_item26 = excluded_total
    
    nfp_balance1 = nfp_item22 - nfp_item25
    nfp_balance2 = nfp_balance1 - nfp_item26
    
    # Update page9 with all calculated values
    page9["nfp_item22"] = f"{nfp_item22:.2f}" if nfp_item22 else ""
    page9["nfp_item25"] = f"{nfp_item25:.2f}" if nfp_item25 else ""
    page9["nfp_item26"] = f"{nfp_item26:.2f}" if nfp_item26 else ""
    page9["nfp_balance1"] = f"{nfp_balance1:.2f}"
    page9["nfp_balance2"] = f"{nfp_balance2:.2f}"
    page9["net_family_property"] = f"{nfp_balance2:.2f}"
    
    # Store intermediate totals for debugging/display
    page5["total_land_valuation"] = f"{land_val:.2f}" if land_val else ""
    page5["total_land_marriage"] = f"{land_marriage:.2f}" if land_marriage else ""
    page5["total_land_today"] = f"{land_today:.2f}" if land_today else ""
    page5["total_items_valuation"] = f"{items_val:.2f}" if items_val else ""
    page5["total_items_marriage"] = f"{items_marriage:.2f}" if items_marriage else ""
    page5["total_items_today"] = f"{items_today:.2f}" if items_today else ""
    page6["total_bank_valuation"] = f"{bank_val:.2f}" if bank_val else ""
    page6["total_bank_marriage"] = f"{bank_marriage:.2f}" if bank_marriage else ""
    page6["total_bank_today"] = f"{bank_today:.2f}" if bank_today else ""
    page6["total_insurance_valuation"] = f"{insurance_val:.2f}" if insurance_val else ""
    page6["total_insurance_marriage"] = f"{insurance_marriage:.2f}" if insurance_marriage else ""
    page6["total_insurance_today"] = f"{insurance_today:.2f}" if insurance_today else ""
    page6["total_business_valuation"] = f"{business_val:.2f}" if business_val else ""
    page6["total_business_marriage"] = f"{business_marriage:.2f}" if business_marriage else ""
    page6["total_business_today"] = f"{business_today:.2f}" if business_today else ""
    page7["total_owed_valuation"] = f"{owed_val:.2f}" if owed_val else ""
    page7["total_owed_marriage"] = f"{owed_marriage:.2f}" if owed_marriage else ""
    page7["total_owed_today"] = f"{owed_today:.2f}" if owed_today else ""
    page7["total_other_prop_valuation"] = f"{other_val:.2f}" if other_val else ""
    page7["total_other_prop_marriage"] = f"{other_marriage:.2f}" if other_marriage else ""
    page7["total_other_prop_today"] = f"{other_today:.2f}" if other_today else ""
    page7["total_debt_valuation"] = f"{debt_val:.2f}" if debt_val else ""
    page7["total_debt_marriage"] = f"{debt_marriage:.2f}" if debt_marriage else ""
    page7["total_debt_today"] = f"{debt_today:.2f}" if debt_today else ""
    page7["grand_total_valuation"] = f"{item_22_total:.2f}" if item_22_total else ""  # Item 22
    page8["total_dom_assets"] = f"{dom_assets:.2f}" if dom_assets else ""
    page8["total_dom_liab"] = f"{dom_liab:.2f}" if dom_liab else ""
    page8["net_dom_value"] = f"{net_dom:.2f}"  # Item 24
    page8["total_deductions"] = f"{item_25_total:.2f}" if item_25_total else ""  # Item 25
    page8["total_excluded"] = f"{excluded_total:.2f}" if excluded_total else ""  # Item 26
    
    pages["page5"] = page5
    pages["page6"] = page6
    pages["page7"] = page7
    pages["page8"] = page8
    pages["page9"] = page9
    
    return pages

def _money_decimal(value):
    """
    Convert user-entered money-like values to Decimal safely.
    Handles '', None, commas, dollar signs, and spaces.
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))

    text = str(value).strip()
    if not text:
        return Decimal("0")

    text = text.replace(",", "").replace("$", "").strip()
    if not text:
        return Decimal("0")

    try:
        return Decimal(text)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _money_str(value):
    """
    Return '' for zero/empty values to match your current display style,
    otherwise return 2-decimal text.
    """
    dec = _money_decimal(value)
    return f"{dec:.2f}" if dec != 0 else ""


def _sum_money_fields(data, field_names):
    total = Decimal("0")
    for name in field_names:
        total += _money_decimal(data.get(name))
    return total


def _calculate_form131_missing_totals(pages):
    """
    Fill totals/subtotals that the existing _calculate_form131_totals()
    does not currently calculate:
      - page 2 income totals
      - page 3 subtotals
      - page 4 subtotals + total monthly/yearly expenses
      - page 10 Schedule A and Schedule B totals
    """
    pages = pages or {}

    page2 = pages.get("page2", {}) or {}
    page3 = pages.get("page3", {}) or {}
    page4 = pages.get("page4", {}) or {}
    page10 = pages.get("page10", {}) or {}

    # --------------------------------------------------
    # PAGE 2: income totals
    # Your print template should use:
    # income_self_employment_before_expenses
    # income_investment
    # income_tax_benefits
    # not self_emp_gross / income_interest / income_child_tax
    # --------------------------------------------------
    income_monthly_fields = [
        "income_employment",
        "income_commissions",
        "income_self_employment",
        "income_ei",
        "income_workers_comp",
        "income_social_assistance",
        "income_investment",
        "income_pension",
        "income_spousal_support",
        "income_tax_benefits",
        "income_other",
    ]
    income_total_monthly = _sum_money_fields(page2, income_monthly_fields)
    income_total_annual = income_total_monthly * Decimal("12")

    page2["income_total_monthly"] = _money_str(income_total_monthly)
    page2["income_total_annual"] = _money_str(income_total_annual)

    # Backward-compatible aliases in case old template lines still exist
    if not page2.get("self_emp_gross"):
        page2["self_emp_gross"] = page2.get("income_self_employment_before_expenses", "")
    if not page2.get("income_interest"):
        page2["income_interest"] = page2.get("income_investment", "")
    if not page2.get("income_child_tax"):
        page2["income_child_tax"] = page2.get("income_tax_benefits", "")

    # --------------------------------------------------
    # PAGE 3: subtotals
    # --------------------------------------------------
    subtotal_deductions = _sum_money_fields(page3, [
        "exp_cpp",
        "exp_ei",
        "exp_income_tax",
        "exp_pension_contrib",
        "exp_union_dues",
    ])

    subtotal_housing = _sum_money_fields(page3, [
        "exp_rent_mortgage",
        "exp_property_tax",
        "exp_property_insurance",
        "exp_condo_fees",
        "exp_repairs",
    ])

    subtotal_utilities_page3 = _sum_money_fields(page3, [
        "exp_water",
        "exp_heat",
        "exp_electricity",
    ])

    subtotal_transportation = _sum_money_fields(page3, [
        "exp_transit",
        "exp_gas",
        "exp_car_insurance",
        "exp_car_repairs",
        "exp_parking",
        "exp_car_loan",
    ])

    subtotal_health = _sum_money_fields(page3, [
        "exp_health_insurance",
        "exp_dental",
        "exp_medicine",
        "exp_eye_care",
    ])

    subtotal_personal_page3 = _sum_money_fields(page3, [
        "exp_clothing",
        "exp_hair_care",
        "exp_alcohol_tobacco",
    ])

    page3["subtotal_deductions"] = _money_str(subtotal_deductions)
    page3["subtotal_housing"] = _money_str(subtotal_housing)
    page3["subtotal_utilities"] = _money_str(subtotal_utilities_page3)
    page3["subtotal_transportation"] = _money_str(subtotal_transportation)
    page3["subtotal_health"] = _money_str(subtotal_health)
    page3["subtotal_personal"] = _money_str(subtotal_personal_page3)

    # --------------------------------------------------
    # PAGE 4: subtotals + total expenses
    # note: print template uses subtotal_utilities on page 4 too
    # --------------------------------------------------
    subtotal_utilities_page4 = _sum_money_fields(page4, [
        "exp_telephone",
        "exp_cell_phone",
        "exp_cable",
        "exp_internet",
    ])

    subtotal_household = _sum_money_fields(page4, [
        "exp_groceries",
        "exp_household_supplies",
        "exp_meals_out",
        "exp_pet_care",
        "exp_laundry",
    ])

    subtotal_childcare = _sum_money_fields(page4, [
        "exp_daycare",
        "exp_babysitting",
    ])

    subtotal_personal_page4 = _sum_money_fields(page4, [
        "exp_education",
        "exp_entertainment",
        "exp_gifts",
    ])

    subtotal_other = _sum_money_fields(page4, [
        "exp_life_insurance",
        "exp_rrsp",
        "exp_vacations",
        "exp_school_fees",
        "exp_children_clothing",
        "exp_children_activities",
        "exp_summer_camp",
        "exp_debt_payments",
        "exp_other_support",
        "exp_other",
    ])

    total_monthly_expenses = (
        subtotal_deductions
        + subtotal_housing
        + subtotal_utilities_page3
        + subtotal_transportation
        + subtotal_health
        + subtotal_personal_page3
        + subtotal_utilities_page4
        + subtotal_household
        + subtotal_childcare
        + subtotal_personal_page4
        + subtotal_other
    )
    total_yearly_expenses = total_monthly_expenses * Decimal("12")

    page4["subtotal_utilities"] = _money_str(subtotal_utilities_page4)
    page4["subtotal_household"] = _money_str(subtotal_household)
    page4["subtotal_childcare"] = _money_str(subtotal_childcare)
    page4["subtotal_personal"] = _money_str(subtotal_personal_page4)
    page4["subtotal_other"] = _money_str(subtotal_other)
    page4["total_monthly_expenses"] = _money_str(total_monthly_expenses)
    page4["total_yearly_expenses"] = _money_str(total_yearly_expenses)

    # --------------------------------------------------
    # PAGE 10: Schedule A + Schedule B totals
    # --------------------------------------------------
    sched_a_subtotal = _sum_money_fields(page10, [
        "sched_a_1",
        "sched_a_2",
        "sched_a_3",
        "sched_a_4",
        "sched_a_5",
        "sched_a_6",
        "sched_a_7",
    ])
    page10["sched_a_subtotal"] = _money_str(sched_a_subtotal)

    sched_b_net_annual = Decimal("0")
    for i in range(1, 11):
        amount = _money_decimal(page10.get(f"sched_b_{i}_amount"))
        credit = _money_decimal(page10.get(f"sched_b_{i}_credit"))
        sched_b_net_annual += (amount - credit)

    sched_b_net_monthly = sched_b_net_annual / Decimal("12") if sched_b_net_annual != 0 else Decimal("0")

    page10["sched_b_total_annual"] = _money_str(sched_b_net_annual)
    page10["sched_b_total_monthly"] = _money_str(sched_b_net_monthly)

    pages["page2"] = page2
    pages["page3"] = page3
    pages["page4"] = page4
    pages["page10"] = page10

    return pages

from decimal import Decimal, InvalidOperation


def _money_decimal(value):
    """
    Convert user-entered money-like values to Decimal safely.
    Handles '', None, commas, dollar signs, and spaces.
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))

    text = str(value).strip()
    if not text:
        return Decimal("0")

    text = text.replace(",", "").replace("$", "").strip()
    if not text:
        return Decimal("0")

    try:
        return Decimal(text)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _money_str(value):
    """
    Return '' for zero/empty values to match your current display style,
    otherwise return 2-decimal text.
    """
    dec = _money_decimal(value)
    return f"{dec:.2f}" if dec != 0 else ""


def _sum_money_fields(data, field_names):
    total = Decimal("0")
    for name in field_names:
        total += _money_decimal(data.get(name))
    return total


def _calculate_form131_missing_totals(pages):
    """
    Fill totals/subtotals that the existing _calculate_form131_totals()
    does not currently calculate:
      - page 2 income totals
      - page 3 subtotals
      - page 4 subtotals + total monthly/yearly expenses
      - page 10 Schedule A and Schedule B totals
    """
    pages = pages or {}

    page2 = pages.get("page2", {}) or {}
    page3 = pages.get("page3", {}) or {}
    page4 = pages.get("page4", {}) or {}
    page10 = pages.get("page10", {}) or {}

    # --------------------------------------------------
    # PAGE 2: income totals
    # Your print template should use:
    # income_self_employment_before_expenses
    # income_investment
    # income_tax_benefits
    # not self_emp_gross / income_interest / income_child_tax
    # --------------------------------------------------
    income_monthly_fields = [
        "income_employment",
        "income_commissions",
        "income_self_employment",
        "income_ei",
        "income_workers_comp",
        "income_social_assistance",
        "income_investment",
        "income_pension",
        "income_spousal_support",
        "income_tax_benefits",
        "income_other",
    ]
    income_total_monthly = _sum_money_fields(page2, income_monthly_fields)
    income_total_annual = income_total_monthly * Decimal("12")

    page2["income_total_monthly"] = _money_str(income_total_monthly)
    page2["income_total_annual"] = _money_str(income_total_annual)

    # Backward-compatible aliases in case old template lines still exist
    if not page2.get("self_emp_gross"):
        page2["self_emp_gross"] = page2.get("income_self_employment_before_expenses", "")
    if not page2.get("income_interest"):
        page2["income_interest"] = page2.get("income_investment", "")
    if not page2.get("income_child_tax"):
        page2["income_child_tax"] = page2.get("income_tax_benefits", "")

    # --------------------------------------------------
    # PAGE 3: subtotals
    # --------------------------------------------------
    subtotal_deductions = _sum_money_fields(page3, [
        "exp_cpp",
        "exp_ei",
        "exp_income_tax",
        "exp_pension_contrib",
        "exp_union_dues",
    ])

    subtotal_housing = _sum_money_fields(page3, [
        "exp_rent_mortgage",
        "exp_property_tax",
        "exp_property_insurance",
        "exp_condo_fees",
        "exp_repairs",
    ])

    subtotal_utilities_page3 = _sum_money_fields(page3, [
        "exp_water",
        "exp_heat",
        "exp_electricity",
    ])

    subtotal_transportation = _sum_money_fields(page3, [
        "exp_transit",
        "exp_gas",
        "exp_car_insurance",
        "exp_car_repairs",
        "exp_parking",
        "exp_car_loan",
    ])

    subtotal_health = _sum_money_fields(page3, [
        "exp_health_insurance",
        "exp_dental",
        "exp_medicine",
        "exp_eye_care",
    ])

    subtotal_personal_page3 = _sum_money_fields(page3, [
        "exp_clothing",
        "exp_hair_care",
        "exp_alcohol_tobacco",
    ])

    page3["subtotal_deductions"] = _money_str(subtotal_deductions)
    page3["subtotal_housing"] = _money_str(subtotal_housing)
    page3["subtotal_utilities"] = _money_str(subtotal_utilities_page3)
    page3["subtotal_transportation"] = _money_str(subtotal_transportation)
    page3["subtotal_health"] = _money_str(subtotal_health)
    page3["subtotal_personal"] = _money_str(subtotal_personal_page3)

    # --------------------------------------------------
    # PAGE 4: subtotals + total expenses
    # note: print template uses subtotal_utilities on page 4 too
    # --------------------------------------------------
    subtotal_utilities_page4 = _sum_money_fields(page4, [
        "exp_telephone",
        "exp_cell_phone",
        "exp_cable",
        "exp_internet",
    ])

    subtotal_household = _sum_money_fields(page4, [
        "exp_groceries",
        "exp_household_supplies",
        "exp_meals_out",
        "exp_pet_care",
        "exp_laundry",
    ])

    subtotal_childcare = _sum_money_fields(page4, [
        "exp_daycare",
        "exp_babysitting",
    ])

    subtotal_personal_page4 = _sum_money_fields(page4, [
        "exp_education",
        "exp_entertainment",
        "exp_gifts",
    ])

    subtotal_other = _sum_money_fields(page4, [
        "exp_life_insurance",
        "exp_rrsp",
        "exp_vacations",
        "exp_school_fees",
        "exp_children_clothing",
        "exp_children_activities",
        "exp_summer_camp",
        "exp_debt_payments",
        "exp_other_support",
        "exp_other",
    ])

    total_monthly_expenses = (
        subtotal_deductions
        + subtotal_housing
        + subtotal_utilities_page3
        + subtotal_transportation
        + subtotal_health
        + subtotal_personal_page3
        + subtotal_utilities_page4
        + subtotal_household
        + subtotal_childcare
        + subtotal_personal_page4
        + subtotal_other
    )
    total_yearly_expenses = total_monthly_expenses * Decimal("12")

    page4["subtotal_utilities"] = _money_str(subtotal_utilities_page4)
    page4["subtotal_household"] = _money_str(subtotal_household)
    page4["subtotal_childcare"] = _money_str(subtotal_childcare)
    page4["subtotal_personal"] = _money_str(subtotal_personal_page4)
    page4["subtotal_other"] = _money_str(subtotal_other)
    page4["total_monthly_expenses"] = _money_str(total_monthly_expenses)
    page4["total_yearly_expenses"] = _money_str(total_yearly_expenses)

    # --------------------------------------------------
    # PAGE 10: Schedule A + Schedule B totals
    # --------------------------------------------------
    sched_a_subtotal = _sum_money_fields(page10, [
        "sched_a_1",
        "sched_a_2",
        "sched_a_3",
        "sched_a_4",
        "sched_a_5",
        "sched_a_6",
        "sched_a_7",
    ])
    page10["sched_a_subtotal"] = _money_str(sched_a_subtotal)

    sched_b_net_annual = Decimal("0")
    for i in range(1, 11):
        amount = _money_decimal(page10.get(f"sched_b_{i}_amount"))
        credit = _money_decimal(page10.get(f"sched_b_{i}_credit"))
        sched_b_net_annual += (amount - credit)

    sched_b_net_monthly = sched_b_net_annual / Decimal("12") if sched_b_net_annual != 0 else Decimal("0")

    page10["sched_b_total_annual"] = _money_str(sched_b_net_annual)
    page10["sched_b_total_monthly"] = _money_str(sched_b_net_monthly)

    pages["page2"] = page2
    pages["page3"] = page3
    pages["page4"] = page4
    pages["page10"] = page10

    return pages
@login_required
def financial_statement_131_print(request, pk):
    """Print view for Form 13.1 - matches official form layout."""
    import json
    from .models import Form131FinancialStatement

    form = get_object_or_404(Form131FinancialStatement, pk=pk)
    merged_data = get_all_form131_data(form)

    pages = form.draft or {}
    page1 = _get_form131_page1_data(form, persist=True)
    pages["page1"] = page1

    # Existing totals logic (pages 5-9 in your current code)
    pages = _calculate_form131_totals(pages)

    # NEW: fill the missing totals/subtotals for pages 2, 3, 4, and 10
    pages = _calculate_form131_missing_totals(pages)

    # Log the print event for billing
    print_event = PrintEvent.log_print(
        user=request.user,
        form_type='financial_statement_131',
        form_id=pk,
        form_identifier=page1.get('court_file_number') or form.court_file_number or f'Form 13.1 #{pk}'
    )
    
    # Audit log for print
    log_audit(request, 'export', 'financial_statement_131', pk, 
              f"Form 13.1 #{pk}", f"Printed - Price: ${print_event.price_charged}")
    
    # Send email notification for print
    send_form_printed_notification('financial_statement_131', form, request.user, print_event.price_charged)

    return render(request, "forms/financial_statement_131_print.html", {
        "form": form,
        "pages": pages,
        "pages_json": json.dumps(pages),
        "court_file_number": page1.get("court_file_number") or form.court_file_number or "",
        "applicant_name": page1.get("applicant_name") or form.applicant_name or "",
        "respondent_name": page1.get("respondent_name") or form.respondent_name or "",
        **merged_data,
    })

@login_required
def financial_statement_list(request):
    """List all financial statements."""
    statements = FinancialStatement.objects.all().order_by('-updated_at')
    return render(request, "forms/financial_statement_list.html", {"statements": statements})


@login_required
@require_http_methods(["GET", "POST"])
def financial_statement_delete(request, pk):
    """Soft delete a financial statement (move to recycle bin)."""
    statement = get_object_or_404(FinancialStatement.all_objects, pk=pk)
    if request.method == "POST":
        statement.soft_delete()
        log_audit(request, 'delete', 'financial_statement', pk, 
                  f"Financial Statement #{pk}", 
                  f"Moved to recycle bin - Applicant: {statement.applicant_full_name or 'N/A'}")
        return redirect("financial_statement_list")
    return render(request, "forms/confirm_delete.html", {
        "object": statement,
        "object_name": f"Financial Statement #{statement.id}",
        "cancel_url": reverse("financial_statement_list"),
    })


def financial_statement_page1_redirect(request):
    """Redirect old URL to dashboard."""
    return HttpResponseRedirect('/forms/dashboard/')


@login_required
def financial_statement_page1_new(request):
    """Create a new Financial Statement."""
    if request.method == "POST":
        form = FinancialStatementForm(request.POST)
        if form.is_valid():
            statement = form.save()
            # Save additional page 1 fields
            _save_page1_fields(statement, request.POST)
            
            # Send email notification for new form
            send_form_created_notification('financial_statement', statement, request.user)
            
            # Audit log for creation
            log_audit(request, 'create', 'financial_statement', statement.pk, 
                      f"Form 13 #{statement.pk}", 
                      f"Created - Applicant: {statement.applicant_full_name or 'N/A'}")
            
            return redirect("financial_statement_page2", pk=statement.pk)
    else:
        form = FinancialStatementForm()
    return render(request, "forms/financial_statement_page1.html", {"form": form, "statement": None})


@login_required
def financial_statement_page1(request, pk=None):
    """Edit an existing Financial Statement page 1."""
    statement = get_object_or_404(FinancialStatement, pk=pk) if pk else None
    
    if request.method == "POST":
        form = FinancialStatementForm(request.POST, instance=statement)
        if form.is_valid():
            statement = form.save()
            _save_page1_fields(statement, request.POST)
            # Return JSON for AJAX autosave requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'saved', 'pk': statement.pk})
            return redirect("financial_statement_page2", pk=statement.pk)
    else:
        form = FinancialStatementForm(instance=statement)
    
    return render(request, "forms/financial_statement_page1.html", {"form": form, "statement": statement})


def _save_page1_fields(statement, post_data):
    """Helper to save page 1 specific fields."""
    statement.my_name = post_data.get('my_name', '')
    statement.my_location = post_data.get('my_location', '')
    statement.is_employed = 'is_employed' in post_data
    statement.employer_name_address = post_data.get('employer_name_address', '')
    statement.is_self_employed = 'is_self_employed' in post_data
    statement.business_name_address = post_data.get('business_name_address', '')
    statement.is_unemployed = 'is_unemployed' in post_data
    unemployed_since = post_data.get('unemployed_since', '')
    if unemployed_since:
        statement.unemployed_since = unemployed_since
    statement.save()


@login_required
def financial_statement_page2(request, pk):
    """Financial Statement Page 2 - Income Proof and Income Table."""
    statement = get_object_or_404(FinancialStatement, pk=pk)
    
    if request.method == "POST":
        # Save proof checkboxes
        statement.pay_cheque_stub = 'pay_cheque_stub' in request.POST
        statement.social_assistance_stub = 'social_assistance_stub' in request.POST
        statement.pension_stub = 'pension_stub' in request.POST
        statement.workers_comp_stub = 'workers_comp_stub' in request.POST
        statement.ei_stub = 'ei_stub' in request.POST
        statement.statement_of_income = 'statement_of_income' in request.POST
        statement.other_income_proof = 'other_income_proof' in request.POST
        
        # Save last year gross income
        statement.last_year_gross_income = parse_decimal(request.POST.get('last_year_gross_income'))
        
        # Save Indian status
        statement.indian_status = 'indian_status' in request.POST
        statement.indian_status_docs = request.POST.get('indian_status_docs', '')
        
        # Save income table
        statement.income_employment = parse_decimal(request.POST.get('income_employment'))
        statement.income_commissions = parse_decimal(request.POST.get('income_commissions'))
        statement.income_self_employment_before_expenses = parse_decimal(request.POST.get('income_self_employment_before_expenses'))
        statement.income_self_employment = parse_decimal(request.POST.get('income_self_employment'))
        statement.income_ei = parse_decimal(request.POST.get('income_ei'))
        statement.income_workers_comp = parse_decimal(request.POST.get('income_workers_comp'))
        statement.income_social_assistance = parse_decimal(request.POST.get('income_social_assistance'))
        statement.income_investment = parse_decimal(request.POST.get('income_investment'))
        statement.income_pension = parse_decimal(request.POST.get('income_pension'))
        statement.income_spousal_support = parse_decimal(request.POST.get('income_spousal_support'))
        statement.income_tax_benefits = parse_decimal(request.POST.get('income_tax_benefits'))
        statement.income_other = parse_decimal(request.POST.get('income_other'))
        statement.income_total_monthly = parse_decimal(request.POST.get('income_total_monthly'))
        statement.income_total_annual = parse_decimal(request.POST.get('income_total_annual'))
        
        statement.save()
        
        # Return JSON for AJAX autosave requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'saved', 'pk': statement.pk})
        
        if "prev" in request.POST:
            return redirect("financial_statement_page1", pk=statement.pk)
        return redirect("financial_statement_page3", pk=statement.pk)
    
    return render(request, "forms/financial_statement_page2.html", {"statement": statement})


@login_required
def financial_statement_page3(request, pk):
    """Financial Statement Page 3 - Other Benefits and Expenses."""
    statement = get_object_or_404(FinancialStatement, pk=pk)
    
    if request.method == "POST":
        # Save Other Benefits (items 1-4)
        statement.benefit_item_1 = request.POST.get('benefit_item_1', '')
        statement.benefit_details_1 = request.POST.get('benefit_details_1', '')
        statement.benefit_value_1 = parse_decimal(request.POST.get('benefit_value_1'))
        statement.benefit_item_2 = request.POST.get('benefit_item_2', '')
        statement.benefit_details_2 = request.POST.get('benefit_details_2', '')
        statement.benefit_value_2 = parse_decimal(request.POST.get('benefit_value_2'))
        statement.benefit_item_3 = request.POST.get('benefit_item_3', '')
        statement.benefit_details_3 = request.POST.get('benefit_details_3', '')
        statement.benefit_value_3 = parse_decimal(request.POST.get('benefit_value_3'))
        statement.benefit_item_4 = request.POST.get('benefit_item_4', '')
        statement.benefit_details_4 = request.POST.get('benefit_details_4', '')
        statement.benefit_value_4 = parse_decimal(request.POST.get('benefit_value_4'))
        
        # Save additional benefit rows (5+) to draft
        extra_benefits = []
        i = 5
        while True:
            item = request.POST.get(f'benefit_item_{i}', '')
            details = request.POST.get(f'benefit_details_{i}', '')
            value = request.POST.get(f'benefit_value_{i}', '')
            if not item and not details and not value:
                break
            extra_benefits.append({'item': item, 'details': details, 'value': value})
            i += 1
        
        # Update draft with extra benefits
        draft_data = statement.draft or {}
        draft_data['extra_benefits'] = extra_benefits
        statement.draft = draft_data
        
        # Save Automatic Deductions
        statement.cpp_contributions = parse_decimal(request.POST.get('cpp_contributions'))
        statement.ei_premiums = parse_decimal(request.POST.get('ei_premiums'))
        statement.income_taxes = parse_decimal(request.POST.get('income_taxes'))
        statement.employee_pension_contributions = parse_decimal(request.POST.get('employee_pension_contributions'))
        statement.union_dues = parse_decimal(request.POST.get('union_dues'))
        statement.automatic_deductions_subtotal = parse_decimal(request.POST.get('automatic_deductions_subtotal'))
        
        # Save Housing
        statement.rent_or_mortgage = parse_decimal(request.POST.get('rent_or_mortgage'))
        statement.property_taxes = parse_decimal(request.POST.get('property_taxes'))
        statement.property_insurance = parse_decimal(request.POST.get('property_insurance'))
        statement.condo_fees = parse_decimal(request.POST.get('condo_fees'))
        statement.repairs_maintenance = parse_decimal(request.POST.get('repairs_maintenance'))
        statement.housing_subtotal = parse_decimal(request.POST.get('housing_subtotal'))
        
        # Save Utilities
        statement.water = parse_decimal(request.POST.get('water'))
        statement.heat = parse_decimal(request.POST.get('heat'))
        statement.electricity = parse_decimal(request.POST.get('electricity'))
        
        # Save Transportation
        statement.public_transit_taxis = parse_decimal(request.POST.get('public_transit_taxis'))
        statement.gas_oil = parse_decimal(request.POST.get('gas_oil'))
        statement.car_insurance_license = parse_decimal(request.POST.get('car_insurance_license'))
        statement.car_repairs_maintenance = parse_decimal(request.POST.get('car_repairs_maintenance'))
        statement.parking = parse_decimal(request.POST.get('parking'))
        statement.car_loan_lease_payments = parse_decimal(request.POST.get('car_loan_lease_payments'))
        statement.transportation_subtotal = parse_decimal(request.POST.get('transportation_subtotal'))
        
        # Save Health
        statement.health_insurance_premiums = parse_decimal(request.POST.get('health_insurance_premiums'))
        statement.dental_expenses = parse_decimal(request.POST.get('dental_expenses'))
        statement.medicine_drugs = parse_decimal(request.POST.get('medicine_drugs'))
        statement.eye_care = parse_decimal(request.POST.get('eye_care'))
        statement.health_subtotal = parse_decimal(request.POST.get('health_subtotal'))
        
        # Save Personal
        statement.clothing = parse_decimal(request.POST.get('clothing'))
        statement.hair_care_beauty = parse_decimal(request.POST.get('hair_care_beauty'))
        statement.alcohol_tobacco = parse_decimal(request.POST.get('alcohol_tobacco'))
        
        statement.save()
        
        # Return JSON for AJAX autosave requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'saved', 'pk': statement.pk})
        
        if "prev" in request.POST:
            return redirect("financial_statement_page2", pk=statement.pk)
        return redirect("financial_statement_page4", pk=statement.pk)
    
    # Unpack extra benefits from draft for template
    context = {"statement": statement}
    extra_benefits = []
    if statement.draft and 'extra_benefits' in statement.draft:
        extra_benefits = statement.draft['extra_benefits']
    context['extra_benefits'] = extra_benefits
    
    return render(request, "forms/financial_statement_page3.html", context)


@login_required
def financial_statement_page4(request, pk):
    """Financial Statement Page 4 - More Expenses and Assets."""
    statement = get_object_or_404(FinancialStatement, pk=pk)
    
    if request.method == "POST":
        # Save more Utilities
        statement.telephone = parse_decimal(request.POST.get('telephone'))
        statement.cell_phone = parse_decimal(request.POST.get('cell_phone'))
        statement.cable = parse_decimal(request.POST.get('cable'))
        statement.internet = parse_decimal(request.POST.get('internet'))
        statement.utilities_subtotal = parse_decimal(request.POST.get('utilities_subtotal'))
        
        # Save more Personal
        statement.education = parse_decimal(request.POST.get('education'))
        statement.entertainment = parse_decimal(request.POST.get('entertainment'))
        statement.gifts = parse_decimal(request.POST.get('gifts'))
        statement.personal_subtotal = parse_decimal(request.POST.get('personal_subtotal'))
        
        # Save Household Expenses
        statement.groceries = parse_decimal(request.POST.get('groceries'))
        statement.household_supplies = parse_decimal(request.POST.get('household_supplies'))
        statement.meals_outside = parse_decimal(request.POST.get('meals_outside'))
        statement.pet_care = parse_decimal(request.POST.get('pet_care'))
        statement.laundry_dry_cleaning = parse_decimal(request.POST.get('laundry_dry_cleaning'))
        statement.household_subtotal = parse_decimal(request.POST.get('household_subtotal'))
        
        # Save Childcare Costs
        statement.daycare_expense = parse_decimal(request.POST.get('daycare_expense'))
        statement.babysitting_costs = parse_decimal(request.POST.get('babysitting_costs'))
        statement.childcare_subtotal = parse_decimal(request.POST.get('childcare_subtotal'))
        
        # Save Other expenses
        statement.life_insurance_premiums = parse_decimal(request.POST.get('life_insurance_premiums'))
        statement.rrsp_resp_withdrawals = parse_decimal(request.POST.get('rrsp_resp_withdrawals'))
        statement.vacations = parse_decimal(request.POST.get('vacations'))
        statement.school_fees_supplies = parse_decimal(request.POST.get('school_fees_supplies'))
        statement.clothing_for_children = parse_decimal(request.POST.get('clothing_for_children'))
        statement.children_activities = parse_decimal(request.POST.get('children_activities'))
        statement.summer_camp_expenses = parse_decimal(request.POST.get('summer_camp_expenses'))
        statement.debt_payments = parse_decimal(request.POST.get('debt_payments'))
        statement.support_paid_for_other_children = parse_decimal(request.POST.get('support_paid_for_other_children'))
        statement.other_expenses_specify = request.POST.get('other_expenses_specify', '')
        statement.other_expenses_amount = parse_decimal(request.POST.get('other_expenses_amount'))
        statement.other_expenses_subtotal = parse_decimal(request.POST.get('other_expenses_subtotal'))
        
        # Save Total expenses
        statement.total_monthly_expenses = parse_decimal(request.POST.get('total_monthly_expenses'))
        statement.total_yearly_expenses = parse_decimal(request.POST.get('total_yearly_expenses'))
        
        # Save Real Estate as JSON (all dynamic rows)
        real_estate = []
        i = 1
        while True:
            details = request.POST.get(f'real_estate_details_{i}', '')
            value = request.POST.get(f'real_estate_value_{i}', '')
            if not details and not value:
                break
            if details or value:
                real_estate.append({'details': details, 'value': value})
            i += 1
        statement.real_estate = real_estate if real_estate else None

        # Save Vehicles as JSON (all dynamic rows)
        vehicles = []
        i = 1
        while True:
            details = request.POST.get(f'vehicle_details_{i}', '')
            value = request.POST.get(f'vehicle_value_{i}', '')
            if not details and not value:
                break
            if details or value:
                vehicles.append({'details': details, 'value': value})
            i += 1
        statement.vehicles = vehicles if vehicles else None
        
        # Save all POST data to draft field as well
        # Exclude csrfmiddlewaretoken and any file uploads
        draft_data = {}
        for k, v in request.POST.items():
            if k != 'csrfmiddlewaretoken':
                draft_data[k] = v
        statement.draft = draft_data
        statement.save()
        
        # Return JSON for AJAX autosave requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'saved', 'pk': statement.pk})
        
        if "prev" in request.POST:
            return redirect("financial_statement_page3", pk=statement.pk)
        return redirect("financial_statement_page5", pk=statement.pk)
    
    # Unpack JSON fields for template
    context = {"statement": statement}
    
    # Unpack real_estate
    if statement.real_estate:
        for i, item in enumerate(statement.real_estate[:10], 1):
            context[f'real_estate_details_{i}'] = item.get('details', '')
            context[f'real_estate_value_{i}'] = item.get('value', '')
    
    # Unpack vehicles
    if statement.vehicles:
        for i, item in enumerate(statement.vehicles[:10], 1):
            context[f'vehicle_details_{i}'] = item.get('details', '')
            context[f'vehicle_value_{i}'] = item.get('value', '')
    
    return render(request, "forms/financial_statement_page4.html", context)


@login_required
def financial_statement_page5(request, pk):
    """Financial Statement Page 5 - Assets continued."""
    statement = get_object_or_404(FinancialStatement, pk=pk)
    
    if request.method == "POST":
        # Save Other Possessions as JSON
        other_possessions = []
        for i in range(1, 4):
            address = request.POST.get(f'possession_address_{i}', '')
            value = request.POST.get(f'possession_value_{i}', '')
            if address or value:
                other_possessions.append({'address_where_located': address, 'value': value})
        statement.other_possessions = other_possessions if other_possessions else None
        
        # Save Investments as JSON
        investments = []
        for i in range(1, 4):
            details = request.POST.get(f'investment_details_{i}', '')
            value = request.POST.get(f'investment_value_{i}', '')
            if details or value:
                investments.append({'type_issuer_due_date_shares': details, 'value': value})
        statement.investments = investments if investments else None
        
        # Save Bank Accounts as JSON
        bank_accounts = []
        for i in range(1, 4):
            institution = request.POST.get(f'bank_institution_{i}', '')
            account_number = request.POST.get(f'bank_account_number_{i}', '')
            value = request.POST.get(f'bank_value_{i}', '')
            if institution or account_number or value:
                bank_accounts.append({
                    'name_address_institution': institution,
                    'account_number': account_number,
                    'value': value
                })
        statement.bank_accounts = bank_accounts if bank_accounts else None
        
        # Save Savings Plans as JSON
        savings_plans = []
        for i in range(1, 4):
            type_issuer = request.POST.get(f'savings_type_{i}', '')
            account_number = request.POST.get(f'savings_account_{i}', '')
            value = request.POST.get(f'savings_value_{i}', '')
            if type_issuer or account_number or value:
                savings_plans.append({
                    'type_issuer': type_issuer,
                    'account_number': account_number,
                    'value': value
                })
        statement.savings_plans = savings_plans if savings_plans else None
        
        # Save Life Insurance as JSON
        life_insurance = []
        for i in range(1, 4):
            details = request.POST.get(f'insurance_details_{i}', '')
            cash_value = request.POST.get(f'insurance_cash_value_{i}', '')
            if details or cash_value:
                life_insurance.append({
                    'type_beneficiary_face_amount': details,
                    'cash_surrender_value': cash_value
                })
        statement.life_insurance = life_insurance if life_insurance else None
        
        # Save Interest in Business as JSON
        interest_in_business = []
        for i in range(1, 4):
            name_address = request.POST.get(f'business_name_address_{i}', '')
            value = request.POST.get(f'business_value_{i}', '')
            if name_address or value:
                interest_in_business.append({
                    'name_address_of_business': name_address,
                    'value': value
                })
        statement.interest_in_business = interest_in_business if interest_in_business else None
        
        # Save Money Owed to You as JSON
        money_owed_to_you = []
        for i in range(1, 4):
            debtor = request.POST.get(f'money_owed_debtor_{i}', '')
            value = request.POST.get(f'money_owed_value_{i}', '')
            if debtor or value:
                money_owed_to_you.append({
                    'name_address_of_debtors': debtor,
                    'value': value
                })
        statement.money_owed_to_you = money_owed_to_you if money_owed_to_you else None
        
        # Save Other Assets as JSON
        other_assets = []
        for i in range(1, 4):
            description = request.POST.get(f'other_asset_description_{i}', '')
            value = request.POST.get(f'other_asset_value_{i}', '')
            if description or value:
                other_assets.append({
                    'description': description,
                    'value': value
                })
        statement.other_assets = other_assets if other_assets else None
        
        # Save Total Value of All Property
        statement.total_value_all_property = parse_decimal(request.POST.get('total_value_all_property'))
        
        statement.save()
        
        # Return JSON for AJAX autosave requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'saved', 'pk': statement.pk})
        
        if "prev" in request.POST:
            return redirect("financial_statement_page4", pk=statement.pk)
        return redirect("financial_statement_page6", pk=statement.pk)
    
    # Unpack JSON fields for template
    context = {"statement": statement}
    
    # Unpack other_possessions
    if statement.other_possessions:
        for i, item in enumerate(statement.other_possessions[:3], 1):
            context[f'possession_address_{i}'] = item.get('address_where_located', '')
            context[f'possession_value_{i}'] = item.get('value', '')
    
    # Unpack investments
    if statement.investments:
        for i, item in enumerate(statement.investments[:3], 1):
            context[f'investment_details_{i}'] = item.get('type_issuer_due_date_shares', '')
            context[f'investment_value_{i}'] = item.get('value', '')
    
    # Unpack bank_accounts
    if statement.bank_accounts:
        for i, item in enumerate(statement.bank_accounts[:3], 1):
            context[f'bank_institution_{i}'] = item.get('name_address_institution', '')
            context[f'bank_account_number_{i}'] = item.get('account_number', '')
            context[f'bank_value_{i}'] = item.get('value', '')
    
    # Unpack savings_plans
    if statement.savings_plans:
        for i, item in enumerate(statement.savings_plans[:3], 1):
            context[f'savings_type_{i}'] = item.get('type_issuer', '')
            context[f'savings_account_{i}'] = item.get('account_number', '')
            context[f'savings_value_{i}'] = item.get('value', '')
    
    # Unpack life_insurance
    if statement.life_insurance:
        for i, item in enumerate(statement.life_insurance[:3], 1):
            context[f'insurance_details_{i}'] = item.get('type_beneficiary_face_amount', '')
            context[f'insurance_cash_value_{i}'] = item.get('cash_surrender_value', '')
    
    # Unpack interest_in_business
    if statement.interest_in_business:
        for i, item in enumerate(statement.interest_in_business[:3], 1):
            context[f'business_name_address_{i}'] = item.get('name_address_of_business', '')
            context[f'business_value_{i}'] = item.get('value', '')
    
    # Unpack money_owed_to_you
    if statement.money_owed_to_you:
        for i, item in enumerate(statement.money_owed_to_you[:3], 1):
            context[f'money_owed_debtor_{i}'] = item.get('name_address_of_debtors', '')
            context[f'money_owed_value_{i}'] = item.get('value', '')
    
    # Unpack other_assets
    if statement.other_assets:
        for i, item in enumerate(statement.other_assets[:3], 1):
            context[f'other_asset_description_{i}'] = item.get('description', '')
            context[f'other_asset_value_{i}'] = item.get('value', '')
    
    return render(request, "forms/financial_statement_page5.html", context)


@login_required
def financial_statement_page6(request, pk):
    """Financial Statement Page 6 - Debts and Summary."""
    statement = get_object_or_404(FinancialStatement, pk=pk)
    
    if request.method == "POST":
        # Save Debts as JSON - using actual template field names
        debts_data = {}
        
        # Mortgages 1-4
        for i in range(1, 5):
            debts_data[f'mortgage_creditor_{i}'] = request.POST.get(f'mortgage_creditor_{i}', '')
            debts_data[f'mortgage_amount_{i}'] = request.POST.get(f'mortgage_amount_{i}', '')
            debts_data[f'mortgage_monthly_{i}'] = request.POST.get(f'mortgage_monthly_{i}', '')
            debts_data[f'mortgage_payment_{i}'] = request.POST.get(f'mortgage_payment_{i}', '')
        
        # Credit cards 1-2
        for i in range(1, 3):
            debts_data[f'credit_card_creditor_{i}'] = request.POST.get(f'credit_card_creditor_{i}', '')
            debts_data[f'credit_card_amount_{i}'] = request.POST.get(f'credit_card_amount_{i}', '')
            debts_data[f'credit_card_monthly_{i}'] = request.POST.get(f'credit_card_monthly_{i}', '')
            debts_data[f'credit_card_payment_{i}'] = request.POST.get(f'credit_card_payment_{i}', '')
        
        # Unpaid support
        debts_data['unpaid_support_creditor'] = request.POST.get('unpaid_support_creditor', '')
        debts_data['unpaid_support_amount'] = request.POST.get('unpaid_support_amount', '')
        debts_data['unpaid_support_monthly'] = request.POST.get('unpaid_support_monthly', '')
        debts_data['unpaid_support_payment'] = request.POST.get('unpaid_support_payment', '')
        
        # Other debts (dynamic rows)
        other_debt_rows = []
        i = 1
        while True:
            creditor = request.POST.get(f'other_debt_creditor_{i}', None)
            amount = request.POST.get(f'other_debt_amount_{i}', None)
            monthly = request.POST.get(f'other_debt_monthly_{i}', None)
            payment = request.POST.get(f'other_debt_payment_{i}', None)
            if creditor is None and amount is None and monthly is None and payment is None:
                break
            debts_data[f'other_debt_creditor_{i}'] = creditor or ''
            debts_data[f'other_debt_amount_{i}'] = amount or ''
            debts_data[f'other_debt_monthly_{i}'] = monthly or ''
            debts_data[f'other_debt_payment_{i}'] = payment or ''
            i += 1
        
        statement.debts = debts_data
        
        # Save Total Debts Outstanding
        statement.total_debts_outstanding = parse_decimal(request.POST.get('total_debts_outstanding'))
        
        # Save Summary (Part 5)
        statement.total_assets = parse_decimal(request.POST.get('total_assets'))
        statement.total_debts = parse_decimal(request.POST.get('subtract_total_debts'))
        statement.net_worth = parse_decimal(request.POST.get('net_worth'))
        
        # Save Signature section
        statement.sworn_municipality = request.POST.get('municipality', '')
        statement.sworn_province_country = request.POST.get('province', '')
        sworn_date = request.POST.get('date', '')
        if sworn_date:
            statement.sworn_date = sworn_date
        statement.commissioner_signature = request.POST.get('commissioner', '')
        
        statement.save()
        
        # Return JSON for AJAX autosave requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'saved', 'pk': statement.pk})
        
        if "prev" in request.POST:
            return redirect("financial_statement_page5", pk=statement.pk)
        return redirect("financial_statement_page7", pk=statement.pk)
    
    # Unpack debts JSON for template
    context = {"statement": statement}
    if statement.debts:
        context.update(statement.debts)
    
    return render(request, "forms/financial_statement_page6.html", context)


@login_required
def financial_statement_page7(request, pk):
    """Financial Statement Page 7 - Schedule A and Schedule B."""
    statement = get_object_or_404(FinancialStatement, pk=pk)
    
    if request.method == "POST":
        # Save Schedule A - Additional Sources of Income
        statement.schedule_a_partnership_income = parse_decimal(request.POST.get('schedule_a_partnership_income'))
        statement.schedule_a_rental_income_gross = parse_decimal(request.POST.get('schedule_a_rental_income_gross'))
        statement.schedule_a_rental_income_net = parse_decimal(request.POST.get('schedule_a_rental_income_net'))
        statement.schedule_a_dividends = parse_decimal(request.POST.get('schedule_a_dividends'))
        statement.schedule_a_capital_gains = parse_decimal(request.POST.get('schedule_a_capital_gains'))
        statement.schedule_a_capital_losses = parse_decimal(request.POST.get('schedule_a_capital_losses'))
        statement.schedule_a_rrsp_withdrawals = parse_decimal(request.POST.get('schedule_a_rrsp_withdrawals'))
        statement.schedule_a_rrif_annuity = parse_decimal(request.POST.get('schedule_a_rrif_annuity'))
        statement.schedule_a_other_income_source = request.POST.get('schedule_a_other_income_source', '')
        statement.schedule_a_other_income_amount = parse_decimal(request.POST.get('schedule_a_other_income_amount'))
        statement.schedule_a_subtotal = parse_decimal(request.POST.get('schedule_a_subtotal'))
        
        # Save Schedule B - Other Income Earners in the Home
        statement.lives_alone = 'lives_alone' in request.POST
        statement.living_with_someone = 'living_with_someone' in request.POST
        statement.living_with_name = request.POST.get('living_with_name', '')
        statement.lives_with_other_adults = 'lives_with_other_adults' in request.POST
        statement.other_adults_names = request.POST.get('other_adults_names', '')
        statement.has_children_in_home = 'has_children_in_home' in request.POST
        num_children = request.POST.get('number_of_children_in_home', '')
        statement.number_of_children_in_home = int(num_children) if num_children.isdigit() else None
        
        statement.spouse_works = 'spouse_works' in request.POST
        statement.spouse_work_place = request.POST.get('spouse_work_place', '')
        statement.spouse_does_not_work = 'spouse_does_not_work' in request.POST
        
        statement.spouse_earns_income = 'spouse_earns_income' in request.POST
        statement.spouse_income_amount = parse_decimal(request.POST.get('spouse_income_amount'))
        statement.spouse_income_period = request.POST.get('spouse_income_period', '')
        statement.spouse_no_income = 'spouse_no_income' in request.POST
        
        statement.household_contribution = 'household_contribution' in request.POST
        statement.household_contribution_amount = parse_decimal(request.POST.get('household_contribution_amount'))
        statement.household_contribution_period = request.POST.get('household_contribution_period', '')
        
        statement.save()
        
        # Return JSON for AJAX autosave requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'saved', 'pk': statement.pk})
        
        if "prev" in request.POST:
            return redirect("financial_statement_page6", pk=statement.pk)
        return redirect("financial_statement_page8", pk=statement.pk)
    
    return render(request, "forms/financial_statement_page7.html", {"statement": statement})


@login_required
def financial_statement_page8(request, pk):
    """Financial Statement Page 8 - Schedule C (Special/Extraordinary Expenses)."""
    statement = get_object_or_404(FinancialStatement, pk=pk)
    
    if request.method == "POST":
        # Save Schedule C - Expenses for Children (dynamic rows)
        schedule_c_expenses = []
        i = 1
        while True:
            child_name = request.POST.get(f'schedule_c_child_name_{i}', '')
            expense = request.POST.get(f'schedule_c_expense_{i}', '')
            amount = request.POST.get(f'schedule_c_amount_{i}', '')
            tax_credits = request.POST.get(f'schedule_c_tax_credits_{i}', '')
            # Stop if no fields found for this index
            if not any([child_name, expense, amount, tax_credits]) and i > 2:
                break
            if child_name or expense or amount or tax_credits:
                schedule_c_expenses.append({
                    'child_name': child_name,
                    'expense': expense,
                    'amount_per_year': amount,
                    'tax_credits': tax_credits
                })
            i += 1
            if i > 50:  # Safety limit
                break
        statement.schedule_c_expenses = schedule_c_expenses if schedule_c_expenses else None
        
        statement.schedule_c_total_annual = parse_decimal(request.POST.get('schedule_c_total_annual'))
        statement.schedule_c_total_monthly = parse_decimal(request.POST.get('schedule_c_total_monthly'))
        statement.schedule_c_my_income_for_share = parse_decimal(request.POST.get('schedule_c_my_income_for_share'))
        
        statement.save()
        
        # Return JSON for AJAX autosave requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'saved', 'pk': statement.pk})
        
        if "prev" in request.POST:
            return redirect("financial_statement_page7", pk=statement.pk)
        return redirect("financial_statement_list")
    
    # Expand JSON data for template display
    schedule_c_rows = []
    expenses = statement.schedule_c_expenses or []
    # Show at least 2 rows, or more if data exists
    min_rows = max(2, len(expenses))
    for i in range(min_rows):
        if i < len(expenses):
            row = expenses[i]
            schedule_c_rows.append({
                'child_name': row.get('child_name', ''),
                'expense': row.get('expense', ''),
                'amount': row.get('amount_per_year', ''),
                'tax_credits': row.get('tax_credits', '')
            })
        else:
            schedule_c_rows.append({'child_name': '', 'expense': '', 'amount': '', 'tax_credits': ''})
    
    # Pass extra rows for JS to load dynamically (rows beyond 2)
    extra_schedule_c_rows = schedule_c_rows[2:] if len(schedule_c_rows) > 2 else []
    schedule_c_rows = schedule_c_rows[:2]  # Only show first 2 in initial HTML
    
    return render(request, "forms/financial_statement_page8.html", {
        "statement": statement,
        "schedule_c_rows": schedule_c_rows,
        "extra_schedule_c_rows": extra_schedule_c_rows
    })


@login_required
def financial_statement_view(request, pk):
    """Full view of a Financial Statement."""
    statement = get_object_or_404(FinancialStatement, pk=pk)
    
    # Extract JSON fields for template access (same as print view)
    context = {
        "statement": statement,
        "pk": pk,
        # Process JSON fields to ensure they're iterable lists
        "real_estate": statement.real_estate or [],
        "vehicles": statement.vehicles or [],
        "other_possessions": statement.other_possessions or [],
        "investments": statement.investments or [],
        "bank_accounts": statement.bank_accounts or [],
        "savings_plans": statement.savings_plans or [],
        "life_insurance": statement.life_insurance or [],
        "interest_in_business": statement.interest_in_business or [],
        "money_owed_to_you": statement.money_owed_to_you or [],
        "other_assets": statement.other_assets or [],
        "schedule_c_expenses": statement.schedule_c_expenses or [],
    }
    
    # Build debt lists from flat dictionary structure
    debts_data = statement.debts or {}
    
    # Mortgages/Loans (4 rows)
    mortgages_loans = []
    for i in range(1, 5):
        creditor = debts_data.get(f'mortgage_creditor_{i}', '')
        full_amount = debts_data.get(f'mortgage_amount_{i}', '')
        monthly = debts_data.get(f'mortgage_monthly_{i}', '')
        payment = debts_data.get(f'mortgage_payment_{i}', '')
        if creditor or full_amount or monthly:
            mortgages_loans.append({
                'creditor': creditor,
                'full_amount': full_amount,
                'monthly_payment': monthly,
                'payments_made': payment == 'yes',
            })
    context['mortgages_loans'] = mortgages_loans
    
    # Credit Cards (2 rows)
    credit_cards = []
    for i in range(1, 3):
        creditor = debts_data.get(f'credit_card_creditor_{i}', '')
        full_amount = debts_data.get(f'credit_card_amount_{i}', '')
        monthly = debts_data.get(f'credit_card_monthly_{i}', '')
        payment = debts_data.get(f'credit_card_payment_{i}', '')
        if creditor or full_amount or monthly:
            credit_cards.append({
                'creditor': creditor,
                'full_amount': full_amount,
                'monthly_payment': monthly,
                'payments_made': payment == 'yes',
            })
    context['credit_cards'] = credit_cards
    
    # Unpaid Support (1 row)
    unpaid_support = []
    creditor = debts_data.get('unpaid_support_creditor', '')
    full_amount = debts_data.get('unpaid_support_amount', '')
    monthly = debts_data.get('unpaid_support_monthly', '')
    payment = debts_data.get('unpaid_support_payment', '')
    if creditor or full_amount or monthly:
        unpaid_support.append({
            'creditor': creditor,
            'full_amount': full_amount,
            'monthly_payment': monthly,
            'payments_made': payment == 'yes',
        })
    context['unpaid_support'] = unpaid_support
    
    # Other Debts (dynamic rows)
    other_debts = []
    i = 1
    while True:
        creditor = debts_data.get(f'other_debt_creditor_{i}', None)
        full_amount = debts_data.get(f'other_debt_amount_{i}', None)
        monthly = debts_data.get(f'other_debt_monthly_{i}', None)
        payment = debts_data.get(f'other_debt_payment_{i}', None)
        if creditor is None and full_amount is None and monthly is None and payment is None:
            break
        if creditor or full_amount or monthly:
            other_debts.append({
                'creditor': creditor,
                'full_amount': full_amount,
                'monthly_payment': monthly,
                'payments_made': payment == 'yes',
            })
        i += 1
    context['other_debts'] = other_debts
    
    return render(request, "forms/financial_statement_full_view.html", context)


@login_required
def financial_statement_print(request, pk):
    """Official printable version of Financial Statement."""
    statement = get_object_or_404(FinancialStatement, pk=pk)
    
    # Ensure JSON fields are properly formatted as lists
    context = {
        "statement": statement,
        "pk": pk,
        # Process JSON fields to ensure they're iterable lists
        "real_estate": statement.real_estate or [],
        "vehicles": statement.vehicles or [],
        "other_possessions": statement.other_possessions or [],
        "investments": statement.investments or [],
        "bank_accounts": statement.bank_accounts or [],
        "savings_plans": statement.savings_plans or [],
        "life_insurance": statement.life_insurance or [],
        "interest_in_business": statement.interest_in_business or [],
        "money_owed_to_you": statement.money_owed_to_you or [],
        "other_assets": statement.other_assets or [],
        "schedule_c_expenses": statement.schedule_c_expenses or [],
    }
    
    # Build debt lists from flat dictionary structure
    debts_data = statement.debts or {}
    
    # Mortgages/Loans (4 rows)
    mortgages_loans = []
    for i in range(1, 5):
        creditor = debts_data.get(f'mortgage_creditor_{i}', '')
        full_amount = debts_data.get(f'mortgage_amount_{i}', '')
        monthly = debts_data.get(f'mortgage_monthly_{i}', '')
        payment = debts_data.get(f'mortgage_payment_{i}', '')
        if creditor or full_amount or monthly:
            mortgages_loans.append({
                'creditor': creditor,
                'full_amount': full_amount,
                'monthly_payment': monthly,
                'payments_made': payment == 'yes',
            })
    context['mortgages_loans'] = mortgages_loans
    
    # Credit Cards (2 rows)
    credit_cards = []
    for i in range(1, 3):
        creditor = debts_data.get(f'credit_card_creditor_{i}', '')
        full_amount = debts_data.get(f'credit_card_amount_{i}', '')
        monthly = debts_data.get(f'credit_card_monthly_{i}', '')
        payment = debts_data.get(f'credit_card_payment_{i}', '')
        if creditor or full_amount or monthly:
            credit_cards.append({
                'creditor': creditor,
                'full_amount': full_amount,
                'monthly_payment': monthly,
                'payments_made': payment == 'yes',
            })
    context['credit_cards'] = credit_cards
    
    # Unpaid Support (1 row)
    unpaid_support = []
    creditor = debts_data.get('unpaid_support_creditor', '')
    full_amount = debts_data.get('unpaid_support_amount', '')
    monthly = debts_data.get('unpaid_support_monthly', '')
    payment = debts_data.get('unpaid_support_payment', '')
    if creditor or full_amount or monthly:
        unpaid_support.append({
            'creditor': creditor,
            'full_amount': full_amount,
            'monthly_payment': monthly,
            'payments_made': payment == 'yes',
        })
    context['unpaid_support'] = unpaid_support
    
    # Other Debts (dynamic rows)
    other_debts = []
    i = 1
    while True:
        creditor = debts_data.get(f'other_debt_creditor_{i}', None)
        full_amount = debts_data.get(f'other_debt_amount_{i}', None)
        monthly = debts_data.get(f'other_debt_monthly_{i}', None)
        payment = debts_data.get(f'other_debt_payment_{i}', None)
        if creditor is None and full_amount is None and monthly is None and payment is None:
            break
        if creditor or full_amount or monthly:
            other_debts.append({
                'creditor': creditor,
                'full_amount': full_amount,
                'monthly_payment': monthly,
                'payments_made': payment == 'yes',
            })
        i += 1
    context['other_debts'] = other_debts
    
    # Log the print event for billing
    print_event = PrintEvent.log_print(
        user=request.user,
        form_type='financial_statement',
        form_id=pk,
        form_identifier=statement.court_file_number or f'Form 13 #{pk}'
    )
    
    # Audit log for print
    log_audit(request, 'export', 'financial_statement', pk, 
              f"Form 13 #{pk}", f"Printed - Price: ${print_event.price_charged}")
    
    # Send email notification for print
    send_form_printed_notification('financial_statement', statement, request.user, print_event.price_charged)
    
    return render(request, "forms/financial_statement_print.html", context)


# ============================================================
# NET FAMILY PROPERTY 13B - 3 PAGES
# ============================================================
@login_required
def net_family_property_13b_list(request):
    """List all 13B forms."""
    forms = NetFamilyProperty13B.objects.all().order_by('-updated_at')
    return render(request, "forms/net_family_property_13b_list.html", {"forms": forms})


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
        "cancel_url": reverse("net_family_property_13b_list"),
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

    if request.method == "POST":
        form = NetFamilyProperty13BForm(request.POST, instance=statement)
        asset_formset = AssetFormSet(request.POST, instance=statement)

        if form.is_valid() and asset_formset.is_valid():
            statement = form.save()
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

    return render(request, "forms/net_family_property_13b_page1.html", {
        "form": form,
        "asset_formset": asset_formset,
        "statement": statement,
        "totals": totals,
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
    """13B Page 3 - Excluded Property."""
    statement = get_object_or_404(NetFamilyProperty13B, pk=pk)
    
    ExcludedFormSet = inlineformset_factory(
        NetFamilyProperty13B,
        NetFamilyProperty13BExcluded,
        form=NetFamilyProperty13BExcludedForm,
        extra=5,
        can_delete=True,
    )

    if request.method == "POST":
        if "prev" in request.POST:
            return redirect("net_family_property_13b_page2", pk=pk)
            
        excluded_formset = ExcludedFormSet(request.POST, instance=statement)
        if excluded_formset.is_valid():
            excluded_formset.save()
            return redirect("net_family_property_13b_list")
    else:
        excluded_formset = ExcludedFormSet(instance=statement)

    # Calculate totals from related data
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
        'total1_app': sum_field(assets, 'applicant_value'),
        'total1_resp': sum_field(assets, 'respondent_value'),
        'total2_app': sum_field(debts, 'applicant_value'),
        'total2_resp': sum_field(debts, 'respondent_value'),
    }
    
    marriage_prop_app = sum_field(marriage_properties, 'applicant_value')
    marriage_prop_resp = sum_field(marriage_properties, 'respondent_value')
    marriage_debt_app = sum_field(marriage_debts, 'applicant_value')
    marriage_debt_resp = sum_field(marriage_debts, 'respondent_value')
    
    totals['total3_app'] = marriage_prop_app - marriage_debt_app
    totals['total3_resp'] = marriage_prop_resp - marriage_debt_resp
    totals['total4_app'] = sum_field(excluded_properties, 'applicant_value')
    totals['total4_resp'] = sum_field(excluded_properties, 'respondent_value')
    totals['total5_app'] = totals['total2_app'] + totals['total3_app'] + totals['total4_app']
    totals['total5_resp'] = totals['total2_resp'] + totals['total3_resp'] + totals['total4_resp']
    totals['total6_app'] = totals['total1_app'] - totals['total5_app']
    totals['total6_resp'] = totals['total1_resp'] - totals['total5_resp']
    
    return render(request, "forms/net_family_property_13b_page3.html", {
        "excluded_formset": excluded_formset,
        "statement": statement,
        "totals": totals,
        "pk": pk
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
    except:
        final_totals = None
    
    def sum_field(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total
    
    totals = {
        'total1_app': sum_field(assets, 'applicant_value'),
        'total1_resp': sum_field(assets, 'respondent_value'),
        'total2_app': sum_field(debts, 'applicant_value'),
        'total2_resp': sum_field(debts, 'respondent_value'),
    }
    
    marriage_prop_app = sum_field(marriage_properties, 'applicant_value')
    marriage_prop_resp = sum_field(marriage_properties, 'respondent_value')
    marriage_debt_app = sum_field(marriage_debts, 'applicant_value')
    marriage_debt_resp = sum_field(marriage_debts, 'respondent_value')
    
    totals['total3_app'] = marriage_prop_app - marriage_debt_app
    totals['total3_resp'] = marriage_prop_resp - marriage_debt_resp
    totals['total4_app'] = sum_field(excluded_properties, 'applicant_value')
    totals['total4_resp'] = sum_field(excluded_properties, 'respondent_value')
    totals['total5_app'] = totals['total2_app'] + totals['total3_app'] + totals['total4_app']
    totals['total5_resp'] = totals['total2_resp'] + totals['total3_resp'] + totals['total4_resp']
    totals['total6_app'] = totals['total1_app'] - totals['total5_app']
    totals['total6_resp'] = totals['total1_resp'] - totals['total5_resp']
    
    return render(request, "forms/net_family_property_13b_view.html", {
        "statement": statement,
        "assets": assets,
        "debts": debts,
        "marriage_properties": marriage_properties,
        "marriage_debts": marriage_debts,
        "excluded_properties": excluded_properties,
        "final_totals": final_totals,
        "totals": totals,
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
    except:
        final_totals = None
    
    def sum_field(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total
    
    totals = {
        'total1_app': sum_field(assets, 'applicant_value'),
        'total1_resp': sum_field(assets, 'respondent_value'),
        'total2_app': sum_field(debts, 'applicant_value'),
        'total2_resp': sum_field(debts, 'respondent_value'),
    }
    
    marriage_prop_app = sum_field(marriage_properties, 'applicant_value')
    marriage_prop_resp = sum_field(marriage_properties, 'respondent_value')
    marriage_debt_app = sum_field(marriage_debts, 'applicant_value')
    marriage_debt_resp = sum_field(marriage_debts, 'respondent_value')
    
    totals['total3_app'] = marriage_prop_app - marriage_debt_app
    totals['total3_resp'] = marriage_prop_resp - marriage_debt_resp
    totals['total4_app'] = sum_field(excluded_properties, 'applicant_value')
    totals['total4_resp'] = sum_field(excluded_properties, 'respondent_value')
    totals['total5_app'] = totals['total2_app'] + totals['total3_app'] + totals['total4_app']
    totals['total5_resp'] = totals['total2_resp'] + totals['total3_resp'] + totals['total4_resp']
    totals['total6_app'] = totals['total1_app'] - totals['total5_app']
    totals['total6_resp'] = totals['total1_resp'] - totals['total5_resp']
    
    # Log the print event for billing
    print_event = PrintEvent.log_print(
        user=request.user,
        form_type='net_family_property_13b',
        form_id=pk,
        form_identifier=statement.court_file_number or f'Form 13B #{pk}'
    )
    
    # Audit log for print
    log_audit(request, 'export', 'net_family_property_13b', pk, 
              f"Form 13B #{pk}", f"Printed - Price: ${print_event.price_charged}")
    
    # Send email notification for print
    send_form_printed_notification('net_family_property_13b', statement, request.user, print_event.price_charged)
    
    return render(request, "forms/net_family_property_13b_print.html", {
        "statement": statement,
        "assets": assets,
        "debts": debts,
        "marriage_properties": marriage_properties,
        "marriage_debts": marriage_debts,
        "excluded_properties": excluded_properties,
        "final_totals": final_totals,
        "totals": totals,
        "pk": pk,
    })


# ============================================================
# COMPARISON NFP (FORM 13C) - 5 PAGES
# ============================================================
@login_required
def net_family_property_create(request):
    """Simple NFP form."""
    if request.method == "POST":
        form = NetFamilyPropertyStatementForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = NetFamilyPropertyStatementForm()
    return render(request, "forms/net_family_property_form.html", {"form": form})


@login_required
def financial_statement_create(request):
    """Create a new financial statement."""
    if request.method == "POST":
        form = FinancialStatementForm(request.POST)
        if form.is_valid():
            statement = form.save()
            return redirect("financial_statement_page1", pk=statement.pk)
    else:
        form = FinancialStatementForm()
    return render(request, "forms/financial_statement_page1.html", {"form": form})


class ComparisonNetFamilyPropertyListView(ListView):
    model = ComparisonNetFamilyProperty
    template_name = "forms/comparison_nfp_list.html"
    context_object_name = "nfp_list"


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
        "cancel_url": reverse("comparison_nfp_list"),
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
    nfp = ComparisonNetFamilyProperty.objects.create()
    return redirect("comparison_nfp_page1_edit", pk=nfp.pk)


@login_required
def comparison_nfp_success(request):
    return render(request, "forms/comparison_nfp_success.html")


@login_required
def comparison_nfp_page1(request, pk=None):
    """Comparison NFP Page 1 - Basic info and Land."""
    instance = get_object_or_404(ComparisonNetFamilyProperty, pk=pk) if pk else None
    is_new = instance is None  # Track if this is a new form

    AssetFormSet = modelformset_factory(
        Form13CAsset,
        form=Form13CAssetForm,
        extra=5,
        can_delete=True,
    )

    if request.method == "POST":
        form = ComparisonNetFamilyPropertyForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            form13c, created = Form13CComparison.objects.get_or_create(parent=obj)
            
            land_formset = AssetFormSet(
                request.POST,
                queryset=Form13CAsset.objects.filter(form13c=form13c),
                prefix="land",
            )
            
            if land_formset.is_valid():
                for form_instance in land_formset.forms:
                    if form_instance.cleaned_data.get('DELETE', False):
                        inst = form_instance.instance
                        if inst and getattr(inst, 'pk', None):
                            inst.delete()
                        continue

                    data_present = False
                    for k, v in form_instance.cleaned_data.items():
                        if k in ('id', 'DELETE'):
                            continue
                        if v not in (None, '', []):
                            data_present = True
                            break

                    if not data_present:
                        continue

                    inst = form_instance.save(commit=False)
                    inst.form13c = form13c
                    inst.save()

                # Send email notification for new form only
                if is_new:
                    send_form_created_notification('comparison_nfp', obj, request.user)
                    # Audit log for creation
                    log_audit(request, 'create', 'comparison_nfp', obj.pk, 
                              f"Form 13C #{obj.pk}", 
                              f"Created - Court File: {obj.court_file_number or 'N/A'}")
                else:
                    # Audit log for update
                    log_audit(request, 'update', 'comparison_nfp', obj.pk, 
                              f"Form 13C #{obj.pk}", "Updated Page 1")

                return redirect("comparison_nfp_page2", pk=obj.pk)
            else:
                return render(request, "forms/comparison_nfp_page1.html", {
                    "form": form, "pk": obj.pk, "land_formset": land_formset
                })
        else:
            land_formset = AssetFormSet(
                queryset=Form13CAsset.objects.filter(form13c__parent=instance) if instance else Form13CAsset.objects.none(),
                prefix="land",
            )
            return render(request, "forms/comparison_nfp_page1.html", {
                "form": form, "pk": pk, "land_formset": land_formset
            })
    else:
        form = ComparisonNetFamilyPropertyForm(instance=instance)
        land_formset = AssetFormSet(
            queryset=Form13CAsset.objects.filter(form13c__parent=instance) if instance else Form13CAsset.objects.none(),
            prefix="land",
        )

    return render(request, "forms/comparison_nfp_page1.html", {
        "form": form, "pk": pk, "land_formset": land_formset
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
    except:
        final_totals = None

    # Calculate totals from previous pages
    from django.db.models import Sum
    
    def sum_field(qs, field):
        agg = qs.aggregate(total=Sum(field))['total']
        return float(agg or 0)

    cols = [
        'applicant_position_applicant',
        'applicant_position_respondent',
        'respondent_position_applicant',
        'respondent_position_respondent',
    ]
    suffixes = ['_app_pos_applicant', '_app_pos_respondent', '_resp_pos_applicant', '_resp_pos_respondent']

    totals = {
        'total1': [0,0,0,0],
        'total2': [0,0,0,0],
        'total3': [0,0,0,0],
        'total4': [0,0,0,0],
        'total5': [0,0,0,0],
        'total6': [0,0,0,0],
    }

    for i, col in enumerate(cols):
        totals['total2'][i] = sum_field(Form13CDebtLiability.objects.filter(form13c=form13c), col)
        totals['total3'][i] = sum_field(Form13CMarriageProperty.objects.filter(form13c=form13c, is_debt=False), col)
        totals['total4'][i] = sum_field(Form13CExcludedProperty.objects.filter(form13c=form13c), col)
        
        comp_household = sum_field(ComparisonNetFamilyPropertyHouseholdItem.objects.filter(parent=comparison), col)
        comp_bank = sum_field(ComparisonNetFamilyPropertyBankAccount.objects.filter(parent=comparison), col)
        comp_insurance = sum_field(ComparisonNetFamilyPropertyInsurance.objects.filter(parent=comparison), col)
        comp_business = sum_field(ComparisonNetFamilyPropertyBusiness.objects.filter(parent=comparison), col)

        totals['total1'][i] = (
            comp_household + comp_bank + comp_insurance + comp_business
            + sum_field(Form13CAsset.objects.filter(form13c=form13c), col)
            + sum_field(Form13CMoneyOwed.objects.filter(form13c=form13c), col)
            + sum_field(Form13COtherProperty.objects.filter(form13c=form13c), col)
        )
        
        totals['total5'][i] = totals['total2'][i] + totals['total3'][i] + totals['total4'][i]
        totals['total6'][i] = totals['total1'][i] - totals['total5'][i]

    # Build initial data dict for the form
    initial_data = {}
    for key in ['total1', 'total2', 'total3', 'total4', 'total5', 'total6']:
        for i, suffix in enumerate(suffixes):
            initial_data[key + suffix] = totals[key][i]
    # total5b is same as total5
    for i, suffix in enumerate(suffixes):
        initial_data['total5b' + suffix] = totals['total5'][i]

    # Calculate equalization payments
    # Applicant's Position: columns 0 (applicant) and 1 (respondent)
    t6_app_app = totals['total6'][0]
    t6_app_resp = totals['total6'][1]
    if t6_app_app > t6_app_resp:
        initial_data['eq_app_pos_applicant_pays'] = (t6_app_app - t6_app_resp) / 2
        initial_data['eq_app_pos_respondent_pays'] = 0
    else:
        initial_data['eq_app_pos_applicant_pays'] = 0
        initial_data['eq_app_pos_respondent_pays'] = (t6_app_resp - t6_app_app) / 2

    # Respondent's Position: columns 2 (applicant) and 3 (respondent)
    t6_resp_app = totals['total6'][2]
    t6_resp_resp = totals['total6'][3]
    if t6_resp_app > t6_resp_resp:
        initial_data['eq_resp_pos_applicant_pays'] = (t6_resp_app - t6_resp_resp) / 2
        initial_data['eq_resp_pos_respondent_pays'] = 0
    else:
        initial_data['eq_resp_pos_applicant_pays'] = 0
        initial_data['eq_resp_pos_respondent_pays'] = (t6_resp_resp - t6_resp_app) / 2

    if request.method == "POST":
        form = Form13CFinalTotalsForm(request.POST, instance=final_totals)
        if form.is_valid():
            ft = form.save(commit=False)
            ft.form13c = form13c
            ft.save()
            
            if "save_draft" in request.POST:
                return redirect("comparison_nfp_page5", pk=pk)
            if "prev" in request.POST:
                return redirect("comparison_nfp_page4", pk=pk)
            return redirect("comparison_nfp_list")
    else:
        # Use initial data to pre-fill computed totals
        form = Form13CFinalTotalsForm(instance=final_totals, initial=initial_data)

    totals_json = json.dumps(totals)

    return render(request, "forms/comparison_nfp_page5.html", {
        "form": form,
        "pk": pk,
        "comparison": comparison,
        "totals_json": totals_json
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
def comparison_nfp_print(request, pk):
    """Official printable format for Comparison NFP."""
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    form13c = getattr(comparison, 'form13c', None)
    
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
    
    if form13c:
        assets = list(form13c.assets.all())
        money_owed = list(form13c.money_owed.all())
        other_property = list(form13c.other_properties.all())
        debts = list(form13c.debts_liabilities.all())
        marriage_property = list(form13c.marriage_properties.filter(is_debt=False))
        marriage_debts = list(form13c.marriage_properties.filter(is_debt=True))
        excluded_property = list(form13c.excluded_properties.all())
    
    def sum_items(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total
    
    cols = ['applicant_position_applicant', 'applicant_position_respondent', 
            'respondent_position_applicant', 'respondent_position_respondent']
    
    total_a = [sum_items(assets, c) for c in cols]
    total_b = [sum_items(household_items, c) for c in cols]
    total_c = [sum_items(bank_accounts, c) for c in cols]
    total_d = [sum_items(insurances, c) for c in cols]
    total_e = [sum_items(businesses, c) for c in cols]
    total_f = [sum_items(money_owed, c) for c in cols]
    total_g = [sum_items(other_property, c) for c in cols]
    
    total_1 = [total_a[i] + total_b[i] + total_c[i] + total_d[i] + total_e[i] + total_f[i] + total_g[i] for i in range(4)]
    total_2 = [sum_items(debts, c) for c in cols]
    
    total_marriage_property = [sum_items(marriage_property, c) for c in cols]
    total_marriage_debts = [sum_items(marriage_debts, c) for c in cols]
    total_3 = [total_marriage_property[i] - total_marriage_debts[i] for i in range(4)]
    
    total_4 = [sum_items(excluded_property, c) for c in cols]
    total_5 = [total_2[i] + total_3[i] + total_4[i] for i in range(4)]
    total_6 = [total_1[i] - total_5[i] for i in range(4)]
    
    equalization = {
        'app_pays_resp_app': '',
        'resp_pays_app_app': '',
        'app_pays_resp_resp': '',
        'resp_pays_app_resp': '',
    }
    
    nfp_app_app = total_6[0]
    nfp_resp_app = total_6[1]
    if nfp_app_app > nfp_resp_app:
        equalization['app_pays_resp_app'] = (nfp_app_app - nfp_resp_app) / 2
    elif nfp_resp_app > nfp_app_app:
        equalization['resp_pays_app_app'] = (nfp_resp_app - nfp_app_app) / 2
    
    nfp_app_resp = total_6[2]
    nfp_resp_resp = total_6[3]
    if nfp_app_resp > nfp_resp_resp:
        equalization['app_pays_resp_resp'] = (nfp_app_resp - nfp_resp_resp) / 2
    elif nfp_resp_resp > nfp_app_resp:
        equalization['resp_pays_app_resp'] = (nfp_resp_resp - nfp_app_resp) / 2

    # Log the print event for billing
    print_event = PrintEvent.log_print(
        user=request.user,
        form_type='comparison_nfp',
        form_id=pk,
        form_identifier=comparison.court_file_number or f'Form 13C #{pk}'
    )
    
    # Audit log for print
    log_audit(request, 'export', 'comparison_nfp', pk, 
              f"Form 13C #{pk}", f"Printed - Price: ${print_event.price_charged}")
    
    # Send email notification
    send_form_printed_notification('comparison_nfp', comparison, request.user, print_event.price_charged)

    return render(request, 'forms/comparison_nfp_print.html', {
        'comparison': comparison,
        'pk': pk,
        'assets': assets,
        'household_items': household_items,
        'bank_accounts': bank_accounts,
        'insurance_policies': insurances,
        'business_interests': businesses,
        'money_owed': money_owed,
        'other_property': other_property,
        'debts': debts,
        'marriage_property': marriage_property,
        'marriage_debts': marriage_debts,
        'excluded_property': excluded_property,
        'total_a': total_a,
        'total_b': total_b,
        'total_c': total_c,
        'total_d': total_d,
        'total_e': total_e,
        'total_f': total_f,
        'total_g': total_g,
        'total_1': total_1,
        'total_2': total_2,
        'total_3': total_3,
        'total_4': total_4,
        'total_5': total_5,
        'total_6': total_6,
        'total_marriage_property': total_marriage_property,
        'total_marriage_debts': total_marriage_debts,
        'equalization': equalization,
    })


@login_required
def comparison_nfp_full_view(request, pk):
    """Full view of a Comparison NFP form."""
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    form13c = getattr(comparison, 'form13c', None)
    
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
        except:
            final_totals = None
    
    def sum_field(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total
    
    cols = ['applicant_position_applicant', 'applicant_position_respondent', 
            'respondent_position_applicant', 'respondent_position_respondent']
    
    totals = {
        'land': [sum_field(land_assets, c) for c in cols],
        'household': [sum_field(household_items, c) for c in cols],
        'bank': [sum_field(bank_accounts, c) for c in cols],
        'insurance': [sum_field(insurances, c) for c in cols],
        'business': [sum_field(businesses, c) for c in cols],
        'money_owed': [sum_field(money_owed_list, c) for c in cols],
        'other': [sum_field(other_properties, c) for c in cols],
        'debts': [sum_field(debts_liabilities, c) for c in cols],
        'marriage_property': [sum_field(marriage_properties, c) for c in cols],
        'marriage_debt': [sum_field(marriage_debts, c) for c in cols],
        'excluded': [sum_field(excluded_properties, c) for c in cols],
    }
    
    totals['total1'] = [
        totals['land'][i] + totals['household'][i] + totals['bank'][i] + 
        totals['insurance'][i] + totals['business'][i] + totals['money_owed'][i] + 
        totals['other'][i]
        for i in range(4)
    ]
    totals['total2'] = totals['debts']
    totals['total3'] = [totals['marriage_property'][i] - totals['marriage_debt'][i] for i in range(4)]
    totals['total4'] = totals['excluded']
    totals['total5'] = [totals['total2'][i] + totals['total3'][i] + totals['total4'][i] for i in range(4)]
    totals['total6'] = [totals['total1'][i] - totals['total5'][i] for i in range(4)]
    
    # Calculate equalization payments
    equalization = {
        'app_pays_resp_app': 0,
        'resp_pays_app_app': 0,
        'app_pays_resp_resp': 0,
        'resp_pays_app_resp': 0,
    }
    
    nfp_app_app = totals['total6'][0]
    nfp_resp_app = totals['total6'][1]
    if nfp_app_app > nfp_resp_app:
        equalization['app_pays_resp_app'] = (nfp_app_app - nfp_resp_app) / 2
    elif nfp_resp_app > nfp_app_app:
        equalization['resp_pays_app_app'] = (nfp_resp_app - nfp_app_app) / 2
    
    nfp_app_resp = totals['total6'][2]
    nfp_resp_resp = totals['total6'][3]
    if nfp_app_resp > nfp_resp_resp:
        equalization['app_pays_resp_resp'] = (nfp_app_resp - nfp_resp_resp) / 2
    elif nfp_resp_resp > nfp_app_resp:
        equalization['resp_pays_app_resp'] = (nfp_resp_resp - nfp_app_resp) / 2
    
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
    
    # Initialize default settings if none exist
    if not settings.exists():
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


@login_required
def financial_statement_131_view(request, pk):
    """View page for Form 13.1 Financial Statement (read-only)."""
    from .models import Form131FinancialStatement
    statement = get_object_or_404(Form131FinancialStatement, pk=pk)
    pages = {}
    for page_num in range(1, 11):
        pages[f"page{page_num}"] = statement.get_page_data(page_num)
    page1 = _get_form131_page1_data(statement, persist=True)
    pages["page1"] = page1
    template_meta_by_page = _get_form131_template_meta()
    ordered_pages = []
    for page_num in range(1, 11):
        page_data = pages.get(f"page{page_num}", {})
        block_html = _get_form131_page_block_html(page_num)
        page_html = _apply_page_data_to_block(block_html, page_data) if block_html else ""
        page_meta = template_meta_by_page.get(page_num, {})
        ordered_pages.append(_build_form131_page_display_data(
            page_num,
            page_data,
            page_meta.get("fields", []),
            page_html,
            page_meta.get("header", ""),
            page_meta.get("subheader", ""),
        ))
    return render(request, "forms/financial_statement_131_view.html", {
        "statement": statement,
        "pages": pages,
        "ordered_pages": ordered_pages,
        "court_file_number": page1.get("court_file_number") or statement.court_file_number or "",
        "applicant_name": page1.get("applicant_name") or statement.applicant_name or "",
        "respondent_name": page1.get("respondent_name") or statement.respondent_name or "",
        "pk": pk,
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
        "cancel_url": reverse("financial_statement_131_list"),
    })

from django.contrib.auth.decorators import login_required, user_passes_test
# Delete PrintEvent (admin/staff only)
from django.shortcuts import get_object_or_404
from django.urls import reverse

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
    
    # Current email settings (read-only from settings.py)
    email_config = {
        'EMAIL_HOST': getattr(django_settings, 'EMAIL_HOST', ''),
        'EMAIL_PORT': getattr(django_settings, 'EMAIL_PORT', 587),
        'EMAIL_USE_SSL': getattr(django_settings, 'EMAIL_USE_SSL', False),
        'EMAIL_USE_TLS': getattr(django_settings, 'EMAIL_USE_TLS', True),
        'EMAIL_HOST_USER': getattr(django_settings, 'EMAIL_HOST_USER', ''),
        'DEFAULT_FROM_EMAIL': getattr(django_settings, 'DEFAULT_FROM_EMAIL', ''),
        'ADMIN_NOTIFICATION_EMAIL': getattr(django_settings, 'ADMIN_NOTIFICATION_EMAIL', ''),
    }
    
    test_result = None
    if request.method == 'POST' and 'test_email' in request.POST:
        test_to = request.POST.get('test_to', request.user.email)
        if test_to:
            try:
                from django.core.mail import send_mail
                send_mail(
                    subject='Test Email from Family Law Forms',
                    message='This is a test email to verify your email configuration is working correctly.',
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[test_to],
                    fail_silently=False,
                )
                test_result = {'success': True, 'message': f'Test email sent successfully to {test_to}'}
                log_audit(request, 'update', 'email_settings', '', 'Email Settings', 
                          f'Test email sent to {test_to}')
            except Exception as e:
                test_result = {'success': False, 'message': f'Failed to send test email: {str(e)}'}
        else:
            test_result = {'success': False, 'message': 'Please provide an email address'}
    
    context = {
        'email_config': email_config,
        'test_result': test_result,
    }
    
    return render(request, 'forms/email_settings.html', context)