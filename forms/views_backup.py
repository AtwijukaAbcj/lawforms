# List all financial statements
from django.contrib.auth.decorators import login_required

@login_required
def financial_statement_list(request):
    statements = FinancialStatement.objects.all().order_by('-updated_at')
    return render(request, "forms/financial_statement_list.html", {"statements": statements})
from django.http import HttpResponseRedirect
# Redirect /forms/financial-statement/page1/ to dashboard to avoid 404
def financial_statement_page1_redirect(request):
    return HttpResponseRedirect('/forms/dashboard/')

from django.contrib.auth.decorators import login_required

@login_required
def financial_statement_page4(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # TODO: Save page 4 fields to the model
        # Example: statement.telephone = request.POST.get('telephone')
        # statement.save()
        return redirect("financial_statement_page5", pk=statement.pk)
    return render(request, "forms/financial_statement_page4.html", {"statement": statement})

@login_required
def financial_statement_page5(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # TODO: Save page 5 fields to the model
        return redirect("financial_statement_page6", pk=statement.pk)
    return render(request, "forms/financial_statement_page5.html", {"statement": statement})

@login_required
def financial_statement_page6(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # TODO: Save page 6 fields to the model
        return redirect("financial_statement_page7", pk=statement.pk)
    return render(request, "forms/financial_statement_page6.html", {"statement": statement})

@login_required
def financial_statement_page7(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # TODO: Save page 7 fields to the model
        return redirect("financial_statement_page8", pk=statement.pk)
    return render(request, "forms/financial_statement_page7.html", {"statement": statement})

@login_required
def financial_statement_page8(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # TODO: Save page 8 fields to the model
        return redirect("financial_statement_list")
    return render(request, "forms/financial_statement_page8.html", {"statement": statement})

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.forms import modelformset_factory, inlineformset_factory
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

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
)

from .forms import (
    NetFamilyPropertyStatementForm,
    FinancialStatementForm,
    NetFamilyProperty13BForm,
    NetFamilyProperty13BAssetForm,
    NetFamilyProperty13BDebtForm,
    NetFamilyProperty13BMarriagePropertyForm,
    NetFamilyProperty13BMarriageDebtForm,
    NetFamilyProperty13BExcludedForm,
    NetFamilyProperty13BFinalTotalsForm,
    ComparisonNetFamilyPropertyForm,
    ComparisonNetFamilyPropertyHouseholdItemForm,
    ComparisonNetFamilyPropertyBankAccountForm,
    ComparisonNetFamilyPropertyInsuranceForm,
    ComparisonNetFamilyPropertyBusinessForm,
    Form13CComparisonForm,
    Form13CAssetForm,
    Form13CGeneralHouseholdItemForm,
    Form13CBusinessInterestForm,
    Form13CMoneyOwedForm,
    Form13COtherPropertyForm,
    Form13CDebtLiabilityForm,
    Form13CMarriagePropertyForm,
    Form13CExcludedPropertyForm,
    Form13CFinalTotalsForm,
)


@login_required
def net_family_property_13b_create_page3(request, pk):
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

    return render(
        request,
        "forms/net_family_property_13b_page3.html",
        {"excluded_formset": excluded_formset, "pk": pk},
    )


@login_required
def comparison_nfp_page3(request, pk):
    """
    Page 3: Assets, Money Owed, Other Property, Debts & Liabilities
    MUST always return an HttpResponse.
    """
    comparison = get_object_or_404(Form13CComparison, pk=pk)

    AssetFormSet = inlineformset_factory(Form13CComparison, Form13CAsset, form=Form13CAssetForm, extra=3, can_delete=True)
    MoneyOwedFormSet = inlineformset_factory(Form13CComparison, Form13CMoneyOwed, form=Form13CMoneyOwedForm, extra=3, can_delete=True)
    OtherPropertyFormSet = inlineformset_factory(Form13CComparison, Form13COtherProperty, form=Form13COtherPropertyForm, extra=3, can_delete=True)
    DebtLiabilityFormSet = inlineformset_factory(Form13CComparison, Form13CDebtLiability, form=Form13CDebtLiabilityForm, extra=3, can_delete=True)

    if request.method == "POST":
        assets_formset = AssetFormSet(
            request.POST,
            queryset=Form13CAsset.objects.filter(comparison=comparison),
            prefix="assets",
        )
        money_owed_formset = MoneyOwedFormSet(
            request.POST,
            queryset=Form13CMoneyOwed.objects.filter(comparison=comparison),
            prefix="money_owed",
        )
        other_property_formset = OtherPropertyFormSet(
            request.POST,
            queryset=Form13COtherProperty.objects.filter(comparison=comparison),
            prefix="other_property",
        )
        debt_liability_formset = DebtLiabilityFormSet(
            request.POST,
            queryset=Form13CDebtLiability.objects.filter(comparison=comparison),
            prefix="debt_liability",
        )

        if (
            assets_formset.is_valid()
            and money_owed_formset.is_valid()
            and other_property_formset.is_valid()
            and debt_liability_formset.is_valid()
        ):
            assets_formset.save()
            money_owed_formset.save()
            other_property_formset.save()
            debt_liability_formset.save()
            if "prev" in request.POST:
                return redirect("comparison_nfp_page2", pk=comparison.parent.pk)
            return redirect("comparison_nfp_page4", pk=pk)

    else:
        assets_formset = AssetFormSet(
            queryset=Form13CAsset.objects.filter(comparison=comparison),
            prefix="assets",
        )
        money_owed_formset = MoneyOwedFormSet(
            queryset=Form13CMoneyOwed.objects.filter(comparison=comparison),
            prefix="money_owed",
        )
        other_property_formset = OtherPropertyFormSet(
            queryset=Form13COtherProperty.objects.filter(comparison=comparison),
            prefix="other_property",
        )
        debt_liability_formset = DebtLiabilityFormSet(
            queryset=Form13CDebtLiability.objects.filter(comparison=comparison),
            prefix="debt_liability",
        )

    return render(
        request,
        "forms/comparison_nfp_page3.html",
        {
            "pk": pk,
            "comparison": comparison,
            "assets_formset": assets_formset,
            "money_owed_formset": money_owed_formset,
            "other_property_formset": other_property_formset,
            "debt_liability_formset": debt_liability_formset,
        },
    )


@login_required
def net_family_property_13b_list(request):
    forms = NetFamilyProperty13B.objects.all()
    return render(request, "forms/net_family_property_13b_list.html", {"forms": forms})


# -------------------------
# Comparison NFP List/Detail
# -------------------------
class ComparisonNetFamilyPropertyListView(ListView):
    model = ComparisonNetFamilyProperty
    template_name = "forms/comparison_nfp_list.html"
    context_object_name = "nfp_list"


class ComparisonNetFamilyPropertyDetailView(DetailView):
    model = ComparisonNetFamilyProperty
    template_name = "forms/comparison_nfp_detail.html"
    context_object_name = "nfp"


@login_required
def comparison_nfp_create(request):
    return redirect("comparison_nfp_page1")


@login_required
def comparison_nfp_success(request):
    return render(request, "forms/comparison_nfp_success.html")


# -------------------------
# Comparison NFP Multi-page
# -------------------------
@login_required
def comparison_nfp_page1(request, pk=None):
    instance = get_object_or_404(ComparisonNetFamilyProperty, pk=pk) if pk else None

    AssetFormSet = modelformset_factory(
        Form13CAsset,
        form=Form13CAssetForm,
        extra=5,
        can_delete=True,
    )

    if request.method == "POST":
        form = ComparisonNetFamilyPropertyForm(request.POST, instance=instance)
        obj = None
        if form.is_valid():
            obj = form.save()
            # Ensure Form13CComparison exists for this parent
            form13c, created = Form13CComparison.objects.get_or_create(parent=obj)
            # Now build the formset with the correct queryset (for editing) or none (for new)
            land_formset = AssetFormSet(
                request.POST,
                queryset=Form13CAsset.objects.filter(form13c=form13c),
                prefix="land",
            )
            if land_formset.is_valid():
                try:
                    # Save only forms that have data (skip completely empty extra forms)
                    for form_instance in land_formset.forms:
                        # If form is marked for deletion, skip here; will handle deletions below
                        if form_instance.cleaned_data.get('DELETE', False):
                            continue

                        # Determine if the form contains any non-empty data (besides the auto PK/DELETE)
                        data_present = False
                        for k, v in form_instance.cleaned_data.items():
                            if k in ('id', 'DELETE'):
                                continue
                            if v not in (None, '', []):
                                data_present = True
                                break

                        if not data_present:
                            # skip saving empty extra form
                            continue

                        inst = form_instance.save(commit=False)
                        inst.form13c = form13c
                        inst.save()

                    # handle deletions: delete any form instances marked for deletion
                    for form_instance in land_formset.forms:
                        try:
                            if form_instance.cleaned_data.get('DELETE', False):
                                inst = form_instance.instance
                                if inst and getattr(inst, 'pk', None):
                                    inst.delete()
                        except Exception:
                            # ignore forms that don't have cleaned_data or instance
                            pass

                    return redirect("comparison_nfp_page2", pk=obj.pk)
                except Exception as e:
                    from django.db import IntegrityError
                    if isinstance(e, IntegrityError):
                        return render(request, "forms/user_friendly_error.html", {
                            "message": "A required field was missing for one or more land table rows. Please ensure all required fields are filled and try again. (Details: NOT NULL constraint failed: forms_form13casset.form13c_id)",
                            "details": str(e),
                            "form": form,
                            "land_formset": land_formset,
                            "pk": obj.pk if obj else pk,
                        })
                    else:
                        raise
            else:
                # Formset invalid, re-render with errors
                return render(request, "forms/comparison_nfp_page1.html", {"form": form, "pk": obj.pk if obj else pk, "land_formset": land_formset})
        else:
            # Form invalid, build empty formset for display
            land_formset = AssetFormSet(
                queryset=Form13CAsset.objects.filter(form13c__parent=instance) if instance else Form13CAsset.objects.none(),
                prefix="land",
            )
            return render(request, "forms/comparison_nfp_page1.html", {"form": form, "pk": pk, "land_formset": land_formset})
    else:
        form = ComparisonNetFamilyPropertyForm(instance=instance)
        land_formset = AssetFormSet(
            queryset=Form13CAsset.objects.filter(form13c__parent=instance) if instance else Form13CAsset.objects.none(),
            prefix="land",
        )

    return render(
        request,
        "forms/comparison_nfp_page1.html",
        {"form": form, "pk": pk, "land_formset": land_formset},
    )


@login_required
def comparison_nfp_page2(request, pk):
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
        household_items_formset = HouseholdItemFormSet(
            request.POST,
            instance=instance,
            prefix="household_items",
        )
        bank_accounts_formset = BankAccountFormSet(
            request.POST,
            instance=instance,
            prefix="bank_accounts",
        )
        insurance_formset = InsuranceFormSet(
            request.POST,
            instance=instance,
            prefix="insurances",
        )
        business_formset = BusinessFormSet(
            request.POST,
            instance=instance,
            prefix="businesses",
        )

        if (
            household_items_formset.is_valid()
            and bank_accounts_formset.is_valid()
            and insurance_formset.is_valid()
            and business_formset.is_valid()
        ):
            try:
                household_items_formset.save()
                bank_accounts_formset.save()
                insurance_formset.save()
                business_formset.save()

                if "prev" in request.POST:
                    return redirect("comparison_nfp_page1_edit", pk=instance.pk)
                return redirect("comparison_nfp_page3", pk=instance.pk)
            except Exception as e:
                from django.db import IntegrityError
                if isinstance(e, IntegrityError):
                    return render(request, "forms/user_friendly_error.html", {
                        "message": "A required field was missing for one or more table rows. Please ensure all required fields are filled and try again.",
                        "details": str(e),
                        "household_items_formset": household_items_formset,
                        "bank_accounts_formset": bank_accounts_formset,
                        "insurance_formset": insurance_formset,
                        "business_formset": business_formset,
                        "pk": instance.pk,
                    })
                else:
                    raise

    else:
        household_items_formset = HouseholdItemFormSet(instance=instance, prefix="household_items")
        bank_accounts_formset = BankAccountFormSet(instance=instance, prefix="bank_accounts")
        insurance_formset = InsuranceFormSet(instance=instance, prefix="insurances")
        business_formset = BusinessFormSet(instance=instance, prefix="businesses")

    return render(
        request,
        "forms/comparison_nfp_page2.html",
        {
            "household_items_formset": household_items_formset,
            "bank_accounts_formset": bank_accounts_formset,
            "insurance_formset": insurance_formset,
            "business_formset": business_formset,
            "pk": instance.pk,     # pk for next pages
        },
    )

@login_required
def comparison_nfp_page3(request, pk):
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    form13c, _ = Form13CComparison.objects.get_or_create(parent=comparison)

    AssetFormSet = modelformset_factory(Form13CAsset, form=Form13CAssetForm, extra=3, can_delete=True)
    MoneyOwedFormSet = modelformset_factory(Form13CMoneyOwed, form=Form13CMoneyOwedForm, extra=3, can_delete=True)
    OtherPropertyFormSet = modelformset_factory(Form13COtherProperty, form=Form13COtherPropertyForm, extra=3, can_delete=True)
    DebtLiabilityFormSet = modelformset_factory(Form13CDebtLiability, form=Form13CDebtLiabilityForm, extra=3, can_delete=True)

    if request.method == "POST":
        if "prev" in request.POST:
            return redirect("comparison_nfp_page2", pk=comparison.pk)

        assets_formset = AssetFormSet(request.POST, queryset=Form13CAsset.objects.filter(form13c=form13c), prefix="assets")
        money_owed_formset = MoneyOwedFormSet(request.POST, queryset=Form13CMoneyOwed.objects.filter(form13c=form13c), prefix="money_owed")
        other_property_formset = OtherPropertyFormSet(request.POST, queryset=Form13COtherProperty.objects.filter(form13c=form13c), prefix="other_property")
        debt_liability_formset = DebtLiabilityFormSet(request.POST, queryset=Form13CDebtLiability.objects.filter(form13c=form13c), prefix="debt_liability")

        if (
            assets_formset.is_valid()
            and money_owed_formset.is_valid()
            and other_property_formset.is_valid()
            and debt_liability_formset.is_valid()
        ):
            # Save each formset with FK assignment
            for formset, model_class in [
                (assets_formset, Form13CAsset),
                (money_owed_formset, Form13CMoneyOwed),
                (other_property_formset, Form13COtherProperty),
                (debt_liability_formset, Form13CDebtLiability),
            ]:
                for f in formset.forms:
                    if f.cleaned_data.get('DELETE', False):
                        inst = f.instance
                        if inst and getattr(inst, 'pk', None):
                            inst.delete()
                        continue
                    # Skip empty forms
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
                    inst.save()

            # Save draft: stay on this page so user can continue editing
            if "save_draft" in request.POST:
                return redirect("comparison_nfp_page3", pk=pk)
            # Next: advance to page 4
            if "next" in request.POST or "save_draft" not in request.POST:
                return redirect("comparison_nfp_page4", pk=pk)

    else:
        assets_formset = AssetFormSet(queryset=Form13CAsset.objects.filter(form13c=form13c), prefix="assets")
        money_owed_formset = MoneyOwedFormSet(queryset=Form13CMoneyOwed.objects.filter(form13c=form13c), prefix="money_owed")
        other_property_formset = OtherPropertyFormSet(queryset=Form13COtherProperty.objects.filter(form13c=form13c), prefix="other_property")
        debt_liability_formset = DebtLiabilityFormSet(queryset=Form13CDebtLiability.objects.filter(form13c=form13c), prefix="debt_liability")

    return render(
        request,
        "forms/comparison_nfp_page3.html",
        {
            "pk": pk,
            "comparison": comparison,
            "assets_formset": assets_formset,
            "money_owed_formset": money_owed_formset,
            "other_property_formset": other_property_formset,
            "debt_liability_formset": debt_liability_formset,
        },
    )

@login_required
def comparison_nfp_page5(request, pk):
    """
    Page 5: Final totals / equalization payments
    """
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)

    # NOTE: this assumes your model is named Form13CFinalTotals and related_name is "final_totals"
    # If your related_name differs, tell me the exact field name and I’ll adjust.
    from .models import Form13CComparison
    form13c, _ = Form13CComparison.objects.get_or_create(parent=comparison)
    try:
        final_totals = form13c.final_totals
    except Exception:
        final_totals = None

    # Import form + model if you didn’t import them at top
    from .forms import Form13CFinalTotalsForm
    from .models import Form13CFinalTotals

    if request.method == "POST":
        form = Form13CFinalTotalsForm(request.POST, instance=final_totals)
        if form.is_valid():
            ft = form.save(commit=False)
            ft.form13c = form13c
            ft.save()
            # If user clicked Save Draft, stay on this page so they can continue editing
            if "save_draft" in request.POST:
                return redirect("comparison_nfp_page5", pk=pk)
            # If user clicked Previous, go back to page 4 after saving
            if "prev" in request.POST:
                return redirect("comparison_nfp_page4", pk=pk)
            # Otherwise, finish and go back to list
            return redirect("comparison_nfp_list")
    else:
        form = Form13CFinalTotalsForm(instance=final_totals)

    # Compute server-side aggregates as a fallback for clients without localStorage
    from django.db.models import Sum
    def sum_field(qs, field):
        agg = qs.aggregate(total=Sum(field))['total']
        return float(agg or 0)

    totals = {
        'total1': [0,0,0,0],
        'total2': [0,0,0,0],
        'total3': [0,0,0,0],
        'total4': [0,0,0,0],
        'total5': [0,0,0,0],
        'total6': [0,0,0,0],
    }

    if form13c:
        from .models import (
            Form13CAsset,
            Form13CMoneyOwed,
            Form13COtherProperty,
            Form13CDebtLiability,
            Form13CMarriageProperty,
            Form13CExcludedProperty,
        )

        cols = [
            'applicant_position_applicant',
            'applicant_position_respondent',
            'respondent_position_applicant',
            'respondent_position_respondent',
        ]

        for i, col in enumerate(cols):
            totals['total2'][i] = sum_field(Form13CDebtLiability.objects.filter(form13c=form13c), col)
            totals['total3'][i] = sum_field(Form13CMarriageProperty.objects.filter(form13c=form13c, is_debt=False), col)
            marriage_debt_val = sum_field(Form13CMarriageProperty.objects.filter(form13c=form13c, is_debt=True), col)
            totals['total4'][i] = sum_field(Form13CExcludedProperty.objects.filter(form13c=form13c), col)
            totals['total5'][i] = totals['total2'][i] + totals['total3'][i] + totals['total4'][i]

            # Include page1 & page2 Comparison model sums (household, bank, insurance, business)
            from .models import (
                ComparisonNetFamilyPropertyHouseholdItem,
                ComparisonNetFamilyPropertyBankAccount,
                ComparisonNetFamilyPropertyInsurance,
                ComparisonNetFamilyPropertyBusiness,
            )

            comp_household = sum_field(ComparisonNetFamilyPropertyHouseholdItem.objects.filter(parent=comparison), col)
            comp_bank = sum_field(ComparisonNetFamilyPropertyBankAccount.objects.filter(parent=comparison), col)
            comp_insurance = sum_field(ComparisonNetFamilyPropertyInsurance.objects.filter(parent=comparison), col)
            comp_business = sum_field(ComparisonNetFamilyPropertyBusiness.objects.filter(parent=comparison), col)

            totals['total1'][i] = (
                comp_household + comp_bank + comp_insurance + comp_business
                + sum_field(Form13CAsset.objects.filter(form13c=form13c), col)
                + sum_field(Form13CMoneyOwed.objects.filter(form13c=form13c), col)
                + sum_field(Form13COtherProperty.objects.filter(form13c=form13c), col)
                + totals['total3'][i] + totals['total4'][i]
            )
            totals['total6'][i] = totals['total1'][i] - totals['total5'][i]

    import json
    totals_json = json.dumps(totals)

    return render(request, "forms/comparison_nfp_page5.html", {"form": form, "pk": pk, "comparison": comparison, "totals_json": totals_json})


@login_required
def comparison_nfp_print(request, pk):
    """
    Official printable format for Comparison NFP (Form 13C) matching Ontario court form layout.
    """
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    form13c = getattr(comparison, 'form13c', None)
    
    # Get all related data
    assets = []
    household_items = list(comparison.household_items.all())
    bank_accounts = list(comparison.bank_accounts.all())
    insurance_policies = list(comparison.insurances.all())
    business_interests = list(comparison.businesses.all())
    
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
    
    # Helper to sum a field across a list of items
    def sum_items(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total
    
    # Column field names (4 columns: App Position App, App Position Resp, Resp Position App, Resp Position Resp)
    cols = ['applicant_position_applicant', 'applicant_position_respondent', 
            'respondent_position_applicant', 'respondent_position_respondent']
    
    # Calculate section totals
    total_a = [sum_items(assets, c) for c in cols]
    total_b = [sum_items(household_items, c) for c in cols]
    total_c = [sum_items(bank_accounts, c) for c in cols]
    total_d = [sum_items(insurance_policies, c) for c in cols]
    total_e = [sum_items(business_interests, c) for c in cols]
    total_f = [sum_items(money_owed, c) for c in cols]
    total_g = [sum_items(other_property, c) for c in cols]
    
    # Total 1: Sum of all assets (A through G)
    total_1 = [total_a[i] + total_b[i] + total_c[i] + total_d[i] + total_e[i] + total_f[i] + total_g[i] for i in range(4)]
    
    # Total 2: Debts
    total_2 = [sum_items(debts, c) for c in cols]
    
    # Total 3: NET marriage property (property - debts)
    total_marriage_property = [sum_items(marriage_property, c) for c in cols]
    total_marriage_debts = [sum_items(marriage_debts, c) for c in cols]
    total_3 = [total_marriage_property[i] - total_marriage_debts[i] for i in range(4)]
    
    # Total 4: Excluded property
    total_4 = [sum_items(excluded_property, c) for c in cols]
    
    # Total 5: Deductions (Total 2 + Total 3 + Total 4)
    total_5 = [total_2[i] + total_3[i] + total_4[i] for i in range(4)]
    
    # Total 6: Net Family Property (Total 1 - Total 5)
    total_6 = [total_1[i] - total_5[i] for i in range(4)]
    
    # Equalization calculation (simplified - half the difference of NFPs)
    equalization = {
        'app_pays_resp_app': '',
        'resp_pays_app_app': '',
        'app_pays_resp_resp': '',
        'resp_pays_app_resp': '',
    }
    
    # Calculate equalization based on Applicant's Position (columns 0,1)
    nfp_app_app = total_6[0]
    nfp_resp_app = total_6[1]
    if nfp_app_app > nfp_resp_app:
        equalization['app_pays_resp_app'] = (nfp_app_app - nfp_resp_app) / 2
    elif nfp_resp_app > nfp_app_app:
        equalization['resp_pays_app_app'] = (nfp_resp_app - nfp_app_app) / 2
    
    # Calculate equalization based on Respondent's Position (columns 2,3)
    nfp_app_resp = total_6[2]
    nfp_resp_resp = total_6[3]
    if nfp_app_resp > nfp_resp_resp:
        equalization['app_pays_resp_resp'] = (nfp_app_resp - nfp_resp_resp) / 2
    elif nfp_resp_resp > nfp_app_resp:
        equalization['resp_pays_app_resp'] = (nfp_resp_resp - nfp_app_resp) / 2

    return render(request, 'forms/comparison_nfp_print.html', {
        'comparison': comparison,
        'pk': pk,
        'assets': assets,
        'household_items': household_items,
        'bank_accounts': bank_accounts,
        'insurance_policies': insurance_policies,
        'business_interests': business_interests,
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
@require_http_methods(["GET", "POST"])
def comparison_nfp_draft(request, pk):
    """
    API endpoint to save/load JSON drafts for a ComparisonNetFamilyProperty instance.
    POST: save JSON body into `comparison.draft`
    GET: return JSON draft
    """
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8")) if request.body else None
        except Exception:
            # Fallback to form POST data
            payload = request.POST.get('draft')
            try:
                payload = json.loads(payload) if payload else None
            except Exception:
                pass

        comparison.draft = payload
        comparison.save(update_fields=["draft", "updated_at"])
        return JsonResponse({"status": "ok"})

    # GET -> return saved draft (may be None)
    return JsonResponse({"draft": comparison.draft})
@login_required
def comparison_nfp_page4(request, pk):
    """
    Page 4: Property & Debts on Date of Marriage + Excluded Property (matches your page4 template)
    """
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

        if (
            marriage_property_formset.is_valid()
            and marriage_debt_formset.is_valid()
            and excluded_property_formset.is_valid()
        ):
            try:
                # Save marriage property rows (only non-empty) and set FK
                for f in marriage_property_formset.forms:
                    if f.cleaned_data.get('DELETE', False):
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
                    inst.save()
                for f in marriage_property_formset.forms:
                    if f.cleaned_data.get('DELETE', False):
                        inst = f.instance
                        if inst and getattr(inst, 'pk', None):
                            inst.delete()

                # Save marriage debt rows
                for f in marriage_debt_formset.forms:
                    if f.cleaned_data.get('DELETE', False):
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
                    inst.is_debt = True  # Mark as debt
                    inst.save()
                for f in marriage_debt_formset.forms:
                    if f.cleaned_data.get('DELETE', False):
                        inst = f.instance
                        if inst and getattr(inst, 'pk', None):
                            inst.delete()

                # Save excluded property rows
                for f in excluded_property_formset.forms:
                    if f.cleaned_data.get('DELETE', False):
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
                    inst.save()
                for f in excluded_property_formset.forms:
                    if f.cleaned_data.get('DELETE', False):
                        inst = f.instance
                        if inst and getattr(inst, 'pk', None):
                            inst.delete()

                return redirect("comparison_nfp_page5", pk=pk)
            except Exception as e:
                from django.db import IntegrityError
                if isinstance(e, IntegrityError):
                    return render(request, "forms/user_friendly_error.html", {
                        "message": "A required field was missing for one or more rows on page 4. Please ensure required fields are filled.",
                        "details": str(e),
                        "comparison": comparison,
                        "marriage_property_formset": marriage_property_formset,
                        "marriage_debt_formset": marriage_debt_formset,
                        "excluded_property_formset": excluded_property_formset,
                    })
                else:
                    raise

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

    return render(
        request,
        "forms/comparison_nfp_page4.html",
        {
            "pk": pk,
            "comparison": comparison,
            "marriage_property_formset": marriage_property_formset,
            "marriage_debt_formset": marriage_debt_formset,
            "excluded_property_formset": excluded_property_formset,
        },
    )


# -------------------------
# Full View / Print Views
# -------------------------
@login_required
def comparison_nfp_full_view(request, pk):
    """
    Full view of a Comparison NFP form (Form 13C) - all pages combined for viewing/printing.
    """
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    form13c = getattr(comparison, 'form13c', None)
    
    # Get all related data
    land_assets = []
    household_items = list(comparison.household_items.all())
    bank_accounts = list(comparison.bank_accounts.all())
    insurances = list(comparison.insurances.all())
    businesses = list(comparison.businesses.all())
    
    assets = []
    money_owed_list = []
    other_properties = []
    debts_liabilities = []
    marriage_properties = []
    marriage_debts = []
    excluded_properties = []
    final_totals = None
    
    if form13c:
        land_assets = list(form13c.assets.all())
        assets = list(form13c.assets.all())
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
    
    # Calculate totals
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
    
    # Calculate grand totals
    totals['total1'] = [
        totals['land'][i] + totals['household'][i] + totals['bank'][i] + 
        totals['insurance'][i] + totals['business'][i] + totals['money_owed'][i] + 
        totals['other'][i]
        for i in range(4)
    ]
    totals['total2'] = totals['debts']
    # Total 3 is NET: marriage property minus marriage debts
    totals['total3'] = [totals['marriage_property'][i] - totals['marriage_debt'][i] for i in range(4)]
    totals['total4'] = totals['excluded']
    totals['total5'] = [totals['total2'][i] + totals['total3'][i] + totals['total4'][i] for i in range(4)]
    totals['total6'] = [totals['total1'][i] - totals['total5'][i] for i in range(4)]
    
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
        "pk": pk,
    })


@login_required
def net_family_property_13b_view(request, pk):
    """
    Full view of a Net Family Property 13B form - all pages combined.
    """
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
    
    # Calculate totals
    def sum_field(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total
    
    # Total 1: Assets
    total1_app = sum_field(assets, 'applicant_value')
    total1_resp = sum_field(assets, 'respondent_value')
    
    # Total 2: Debts
    total2_app = sum_field(debts, 'applicant_value')
    total2_resp = sum_field(debts, 'respondent_value')
    
    # Total 3: Marriage property (net: property - debts)
    marriage_prop_app = sum_field(marriage_properties, 'applicant_value')
    marriage_prop_resp = sum_field(marriage_properties, 'respondent_value')
    marriage_debt_app = sum_field(marriage_debts, 'applicant_value')
    marriage_debt_resp = sum_field(marriage_debts, 'respondent_value')
    total3_app = marriage_prop_app - marriage_debt_app
    total3_resp = marriage_prop_resp - marriage_debt_resp
    
    # Total 4: Excluded property
    total4_app = sum_field(excluded_properties, 'applicant_value')
    total4_resp = sum_field(excluded_properties, 'respondent_value')
    
    # Total 5: Deductions (Total 2 + Total 3 + Total 4)
    total5_app = total2_app + total3_app + total4_app
    total5_resp = total2_resp + total3_resp + total4_resp
    
    # Total 6: Net Family Property (Total 1 - Total 5)
    total6_app = total1_app - total5_app
    total6_resp = total1_resp - total5_resp
    
    totals = {
        'total1_app': total1_app,
        'total1_resp': total1_resp,
        'total2_app': total2_app,
        'total2_resp': total2_resp,
        'total3_app': total3_app,
        'total3_resp': total3_resp,
        'total4_app': total4_app,
        'total4_resp': total4_resp,
        'total5_app': total5_app,
        'total5_resp': total5_resp,
        'total6_app': total6_app,
        'total6_resp': total6_resp,
    }
    
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
    """
    Printable version of 13B form - official Ontario Form 13B format.
    """
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
    
    # Calculate totals
    def sum_field(items, field):
        total = 0
        for item in items:
            val = getattr(item, field, None)
            if val:
                total += float(val)
        return total
    
    # Total 1: Assets
    total1_app = sum_field(assets, 'applicant_value')
    total1_resp = sum_field(assets, 'respondent_value')
    
    # Total 2: Debts
    total2_app = sum_field(debts, 'applicant_value')
    total2_resp = sum_field(debts, 'respondent_value')
    
    # Total 3: Marriage property (net: property - debts)
    marriage_prop_app = sum_field(marriage_properties, 'applicant_value')
    marriage_prop_resp = sum_field(marriage_properties, 'respondent_value')
    marriage_debt_app = sum_field(marriage_debts, 'applicant_value')
    marriage_debt_resp = sum_field(marriage_debts, 'respondent_value')
    total3_app = marriage_prop_app - marriage_debt_app
    total3_resp = marriage_prop_resp - marriage_debt_resp
    
    # Total 4: Excluded property
    total4_app = sum_field(excluded_properties, 'applicant_value')
    total4_resp = sum_field(excluded_properties, 'respondent_value')
    
    # Total 5: Deductions (Total 2 + Total 3 + Total 4)
    total5_app = total2_app + total3_app + total4_app
    total5_resp = total2_resp + total3_resp + total4_resp
    
    # Total 6: Net Family Property (Total 1 - Total 5)
    total6_app = total1_app - total5_app
    total6_resp = total1_resp - total5_resp
    
    totals = {
        'total1_app': total1_app,
        'total1_resp': total1_resp,
        'total2_app': total2_app,
        'total2_resp': total2_resp,
        'total3_app': total3_app,
        'total3_resp': total3_resp,
        'total4_app': total4_app,
        'total4_resp': total4_resp,
        'total5_app': total5_app,
        'total5_resp': total5_resp,
        'total6_app': total6_app,
        'total6_resp': total6_resp,
    }
    
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


@login_required
def financial_statement_view(request, pk):
    """
    Full view of a Financial Statement - all 8 pages combined.
    """
    statement = get_object_or_404(FinancialStatement, pk=pk)
    
    return render(request, "forms/financial_statement_full_view.html", {
        "statement": statement,
        "pk": pk,
    })


@login_required
def financial_statement_print(request, pk):
    """
    Official printable version of Financial Statement (Form 13) matching Ontario court format.
    """
    statement = get_object_or_404(FinancialStatement, pk=pk)
    
    return render(request, "forms/financial_statement_print.html", {
        "statement": statement,
        "pk": pk,
    })


# List all financial statements
from django.contrib.auth.decorators import login_required

@login_required
def financial_statement_list(request):
    statements = FinancialStatement.objects.all().order_by('-updated_at')
    return render(request, "forms/financial_statement_list.html", {"statements": statements})
from django.http import HttpResponseRedirect
# Redirect /forms/financial-statement/page1/ to dashboard to avoid 404
def financial_statement_page1_redirect(request):
    return HttpResponseRedirect('/forms/dashboard/')

from django.contrib.auth.decorators import login_required

@login_required
def financial_statement_page4(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # TODO: Save page 4 fields to the model
        # Example: statement.telephone = request.POST.get('telephone')
        # statement.save()
        return redirect("financial_statement_page5", pk=statement.pk)
    return render(request, "forms/financial_statement_page4.html", {"statement": statement})

@login_required
def financial_statement_page5(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # TODO: Save page 5 fields to the model
        return redirect("financial_statement_page6", pk=statement.pk)
    return render(request, "forms/financial_statement_page5.html", {"statement": statement})

@login_required
def financial_statement_page6(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # TODO: Save page 6 fields to the model
        return redirect("financial_statement_page7", pk=statement.pk)
    return render(request, "forms/financial_statement_page6.html", {"statement": statement})

@login_required
def financial_statement_page7(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # TODO: Save page 7 fields to the model
        return redirect("financial_statement_page8", pk=statement.pk)
    return render(request, "forms/financial_statement_page7.html", {"statement": statement})

@login_required
def financial_statement_page8(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # TODO: Save page 8 fields to the model
        return redirect("financial_statement_list")
    return render(request, "forms/financial_statement_page8.html", {"statement": statement})

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.forms import modelformset_factory, inlineformset_factory

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
)

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
)


# -------------------------
# Dashboard
# -------------------------
@login_required
def dashboard(request):
    # Get counts and recent items for all form types
    financial_statements = FinancialStatement.objects.all().order_by('-updated_at')
    net_family_13b = NetFamilyProperty13B.objects.all().order_by('-updated_at')
    comparison_nfp = Form13CComparison.objects.all().order_by('-updated_at')
    
    context = {
        # Financial Statements (Form 13)
        'financial_statements': financial_statements[:5],
        'financial_statements_count': financial_statements.count(),
        
        # Net Family Property 13B
        'net_family_13b': net_family_13b[:5],
        'net_family_13b_count': net_family_13b.count(),
        
        # Comparison NFP (Form 13C)
        'comparison_nfp': comparison_nfp[:5],
        'comparison_nfp_count': comparison_nfp.count(),
        
        # Total forms
        'total_forms': financial_statements.count() + net_family_13b.count() + comparison_nfp.count(),
    }
    return render(request, "forms/dashboard.html", context)


# -------------------------
# Single page basic forms
# -------------------------
@login_required
def net_family_property_create(request):
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
    if request.method == "POST":
        form = FinancialStatementForm(request.POST)
        if form.is_valid():
            statement = form.save()
            return redirect("financial_statement_page1", pk=statement.pk)
    else:
        form = FinancialStatementForm()
    return render(request, "forms/financial_statement_page1.html", {"form": form})



@login_required
def financial_statement_page1_new(request):
    """Create a new Financial Statement."""
    if request.method == "POST":
        form = FinancialStatementForm(request.POST)
        if form.is_valid():
            statement = form.save()
            return redirect("financial_statement_page2", pk=statement.pk)
    else:
        form = FinancialStatementForm()
    return render(request, "forms/financial_statement_page1.html", {"form": form})


@login_required
def financial_statement_page1(request, pk=None):
    """Edit an existing Financial Statement."""
    statement = None
    if pk:
        statement = get_object_or_404(FinancialStatement, pk=pk)
        if request.method == "POST":
            form = FinancialStatementForm(request.POST, instance=statement)
            if form.is_valid():
                statement = form.save()
                # Save employment status fields
                statement.my_name = request.POST.get('my_name', '')
                statement.my_location = request.POST.get('my_location', '')
                statement.is_employed = 'is_employed' in request.POST
                statement.employer_name_address = request.POST.get('employer_name_address', '')
                statement.is_self_employed = 'is_self_employed' in request.POST
                statement.business_name_address = request.POST.get('business_name_address', '')
                statement.is_unemployed = 'is_unemployed' in request.POST
                unemployed_since = request.POST.get('unemployed_since', '')
                if unemployed_since:
                    statement.unemployed_since = unemployed_since
                statement.save()
                return redirect("financial_statement_page2", pk=statement.pk)
        else:
            form = FinancialStatementForm(instance=statement)
    else:
        if request.method == "POST":
            form = FinancialStatementForm(request.POST)
            if form.is_valid():
                statement = form.save()
                # Save employment status fields
                statement.my_name = request.POST.get('my_name', '')
                statement.my_location = request.POST.get('my_location', '')
                statement.is_employed = 'is_employed' in request.POST
                statement.employer_name_address = request.POST.get('employer_name_address', '')
                statement.is_self_employed = 'is_self_employed' in request.POST
                statement.business_name_address = request.POST.get('business_name_address', '')
                statement.is_unemployed = 'is_unemployed' in request.POST
                unemployed_since = request.POST.get('unemployed_since', '')
                if unemployed_since:
                    statement.unemployed_since = unemployed_since
                statement.save()
                return redirect("financial_statement_page2", pk=statement.pk)
        else:
            form = FinancialStatementForm()
    return render(request, "forms/financial_statement_page1.html", {"form": form, "statement": statement})



# Financial Statement Page 2 (Support Claims)
@login_required
def financial_statement_page2(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # TODO: Save page 2 fields to the model
        # statement.some_field = request.POST.get('some_field')
        # statement.save()
        return redirect("financial_statement_page3", pk=statement.pk)
    return render(request, "forms/financial_statement_page2.html", {"statement": statement})


# Financial Statement Page 3 (Support Claims)
@login_required
def financial_statement_page3(request, pk):
    statement = get_object_or_404(FinancialStatement, pk=pk)
    if request.method == "POST":
        # Save Other Benefits
        other_benefits = []
        for i in range(4):
            item = request.POST.get(f"other_benefits_item_{i}", "")
            details = request.POST.get(f"other_benefits_details_{i}", "")
            value = request.POST.get(f"other_benefits_value_{i}", "")
            if item or details or value:
                other_benefits.append({
                    "item": item,
                    "details": details,
                    "value": value,
                })
        # Save Expenses (example, you should wire these to your model fields)
        expenses = {
            "cpp_contributions": request.POST.get("cpp_contributions"),
            "ei_premiums": request.POST.get("ei_premiums"),
            "income_taxes": request.POST.get("income_taxes"),
            "employee_pension_contributions": request.POST.get("employee_pension_contributions"),
            "union_dues": request.POST.get("union_dues"),
            "automatic_deductions_subtotal": request.POST.get("automatic_deductions_subtotal"),
            "rent_or_mortgage": request.POST.get("rent_or_mortgage"),
            "property_taxes": request.POST.get("property_taxes"),
            "property_insurance": request.POST.get("property_insurance"),
            "condo_fees": request.POST.get("condo_fees"),
            "repairs_maintenance": request.POST.get("repairs_maintenance"),
            "housing_subtotal": request.POST.get("housing_subtotal"),
            "water": request.POST.get("water"),
            "heat": request.POST.get("heat"),
            "electricity": request.POST.get("electricity"),
            "public_transit": request.POST.get("public_transit"),
            "gas_oil": request.POST.get("gas_oil"),
            "car_insurance_license": request.POST.get("car_insurance_license"),
            "car_repairs_maintenance": request.POST.get("car_repairs_maintenance"),
            "parking": request.POST.get("parking"),
            "car_loan_lease": request.POST.get("car_loan_lease"),
            "transportation_subtotal": request.POST.get("transportation_subtotal"),
            "health_insurance_premiums": request.POST.get("health_insurance_premiums"),
            "dental_expenses": request.POST.get("dental_expenses"),
            "medicine_drugs": request.POST.get("medicine_drugs"),
            "eye_care": request.POST.get("eye_care"),
            "health_subtotal": request.POST.get("health_subtotal"),
            "clothing": request.POST.get("clothing"),
            "hair_care_beauty": request.POST.get("hair_care_beauty"),
            "alcohol_tobacco": request.POST.get("alcohol_tobacco"),
        }
        # TODO: Save these to the model or a related model
        # statement.expenses = expenses
        # statement.other_benefits = other_benefits
        # statement.save()
        return redirect("dashboard")
    return render(request, "forms/financial_statement_page3.html", {"statement": statement})


# -------------------------
# 13B Multi-page Views
# -------------------------
@login_required
def net_family_property_13b_create_page1(request, pk=None):
    statement = get_object_or_404(NetFamilyProperty13B, pk=pk) if pk else None

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
            return HttpResponseRedirect(reverse("net_family_property_13b_page2", args=[statement.pk]))
    else:
        form = NetFamilyProperty13BForm(instance=statement)
        asset_formset = AssetFormSet(instance=statement)

    return render(
        request,
        "forms/net_family_property_13b_page1.html",
        {"form": form, "asset_formset": asset_formset},
    )


@login_required
def net_family_property_13b_create_page2(request, pk):
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
            return HttpResponseRedirect(reverse("net_family_property_13b_page1_edit", args=[statement.pk]))

        debt_formset = DebtFormSet(request.POST, instance=statement, prefix="debt")
        marriage_property_formset = MarriagePropertyFormSet(request.POST, instance=statement, prefix="mprop")
        marriage_debt_formset = MarriageDebtFormSet(request.POST, instance=statement, prefix="mdebt")

        if debt_formset.is_valid() and marriage_property_formset.is_valid() and marriage_debt_formset.is_valid():
            debt_formset.save()
            marriage_property_formset.save()
            marriage_debt_formset.save()
            return HttpResponseRedirect(reverse("net_family_property_13b_page3", args=[statement.pk]))
    else:
        debt_formset = DebtFormSet(instance=statement, prefix="debt")
        marriage_property_formset = MarriagePropertyFormSet(instance=statement, prefix="mprop")
        marriage_debt_formset = MarriageDebtFormSet(instance=statement, prefix="mdebt")

    return render(
        request,
        "forms/net_family_property_13b_page2.html",
        {
            "debt_formset": debt_formset,
            "marriage_property_formset": marriage_property_formset,
            "marriage_debt_formset": marriage_debt_formset,
        },
    )


@login_required
def net_family_property_13b_create_page3(request, pk):
    statement = get_object_or_404(NetFamilyProperty13B, pk=pk)
    ExcludedFormSet = inlineformset_factory(
        NetFamilyProperty13B,
        NetFamilyProperty13BExcluded,
        form=NetFamilyProperty13BExcludedForm,
        extra=5,
        can_delete=True,
    )

    if request.method == "POST":
        excluded_formset = ExcludedFormSet(request.POST, instance=statement)
        if excluded_formset.is_valid():
            excluded_formset.save()
            return redirect("net_family_property_13b_list")
    else:
        excluded_formset = ExcludedFormSet(instance=statement)

    return render(
        request,
        "forms/net_family_property_13b_page3.html",
        {"excluded_formset": excluded_formset, "pk": pk},
    )


@login_required
def comparison_nfp_page3(request, pk):
    """
    Page 3: Assets, Money Owed, Other Property, Debts & Liabilities
    MUST always return an HttpResponse.
    """
    comparison = get_object_or_404(Form13CComparison, pk=pk)

    AssetFormSet = modelformset_factory(Form13CAsset, form=Form13CAssetForm, extra=3, can_delete=True)
    MoneyOwedFormSet = modelformset_factory(Form13CMoneyOwed, form=Form13CMoneyOwedForm, extra=3, can_delete=True)
    OtherPropertyFormSet = modelformset_factory(Form13COtherProperty, form=Form13COtherPropertyForm, extra=3, can_delete=True)
    DebtLiabilityFormSet = modelformset_factory(Form13CDebtLiability, form=Form13CDebtLiabilityForm, extra=3, can_delete=True)

    if request.method == "POST":
        if "prev" in request.POST:
            # go back to page2 using the *parent* ComparisonNetFamilyProperty pk
            return redirect("comparison_nfp_page2", pk=comparison.parent.pk)

        assets_formset = AssetFormSet(
            request.POST,
            queryset=Form13CAsset.objects.filter(comparison=comparison),
            prefix="assets",
        )
        money_owed_formset = MoneyOwedFormSet(
            request.POST,
            queryset=Form13CMoneyOwed.objects.filter(comparison=comparison),
            prefix="money_owed",
        )
        other_property_formset = OtherPropertyFormSet(
            request.POST,
            queryset=Form13COtherProperty.objects.filter(comparison=comparison),
            prefix="other_property",
        )
        debt_liability_formset = DebtLiabilityFormSet(
            request.POST,
            queryset=Form13CDebtLiability.objects.filter(comparison=comparison),
            prefix="debt_liability",
        )

        if (
            assets_formset.is_valid()
            and money_owed_formset.is_valid()
            and other_property_formset.is_valid()
            and debt_liability_formset.is_valid()
        ):
            assets_formset.save()
            money_owed_formset.save()
            other_property_formset.save()
            debt_liability_formset.save()
            return redirect("comparison_nfp_page4", pk=pk)

    else:
        assets_formset = AssetFormSet(
            queryset=Form13CAsset.objects.filter(comparison=comparison),
            prefix="assets",
        )
        money_owed_formset = MoneyOwedFormSet(
            queryset=Form13CMoneyOwed.objects.filter(comparison=comparison),
            prefix="money_owed",
        )
        other_property_formset = OtherPropertyFormSet(
            queryset=Form13COtherProperty.objects.filter(comparison=comparison),
            prefix="other_property",
        )
        debt_liability_formset = DebtLiabilityFormSet(
            queryset=Form13CDebtLiability.objects.filter(comparison=comparison),
            prefix="debt_liability",
        )

    return render(
        request,
        "forms/comparison_nfp_page3.html",
        {
            "pk": pk,
            "comparison": comparison,
            "assets_formset": assets_formset,
            "money_owed_formset": money_owed_formset,
            "other_property_formset": other_property_formset,
            "debt_liability_formset": debt_liability_formset,
        },
    )


@login_required
def net_family_property_13b_list(request):
    forms = NetFamilyProperty13B.objects.all()
    return render(request, "forms/net_family_property_13b_list.html", {"forms": forms})


# -------------------------
# Comparison NFP List/Detail

@login_required
def comparison_nfp_page3(request, pk):
    """
    Page 3: Assets, Money Owed, Other Property, Debts & Liabilities.
    Accepts the ComparisonNetFamilyProperty PK (parent), ensures a Form13CComparison exists,
    and uses inline formsets bound to the Form13CComparison instance so FK is set automatically.
    """
    comparison = get_object_or_404(ComparisonNetFamilyProperty, pk=pk)
    form13c, _ = Form13CComparison.objects.get_or_create(parent=comparison)

    AssetFormSet = inlineformset_factory(Form13CComparison, Form13CAsset, form=Form13CAssetForm, extra=3, can_delete=True)
    MoneyOwedFormSet = inlineformset_factory(Form13CComparison, Form13CMoneyOwed, form=Form13CMoneyOwedForm, extra=3, can_delete=True)
    OtherPropertyFormSet = inlineformset_factory(Form13CComparison, Form13COtherProperty, form=Form13COtherPropertyForm, extra=3, can_delete=True)
    DebtLiabilityFormSet = inlineformset_factory(Form13CComparison, Form13CDebtLiability, form=Form13CDebtLiabilityForm, extra=3, can_delete=True)

    if request.method == "POST":
        if "prev" in request.POST:
            return redirect("comparison_nfp_page2", pk=comparison.pk)

        # Only instantiate/validate formsets that were actually submitted (management form present).
        def posted(prefix):
            return f'id_{prefix}-TOTAL_FORMS' in request.POST

        assets_formset = AssetFormSet(request.POST, instance=form13c, prefix="assets") if posted('assets') else AssetFormSet(instance=form13c, prefix="assets")
        money_owed_formset = MoneyOwedFormSet(request.POST, instance=form13c, prefix="money_owed") if posted('money_owed') else MoneyOwedFormSet(instance=form13c, prefix="money_owed")
        other_property_formset = OtherPropertyFormSet(request.POST, instance=form13c, prefix="other_property") if posted('other_property') else OtherPropertyFormSet(instance=form13c, prefix="other_property")
        debt_liability_formset = DebtLiabilityFormSet(request.POST, instance=form13c, prefix="debt_liability") if posted('debt_liability') else DebtLiabilityFormSet(instance=form13c, prefix="debt_liability")

        # Validate only the posted formsets; treat non-posted as valid by default.
        valid_assets = assets_formset.is_valid() if posted('assets') else True
        valid_money_owed = money_owed_formset.is_valid() if posted('money_owed') else True
        valid_other = other_property_formset.is_valid() if posted('other_property') else True
        valid_debt = debt_liability_formset.is_valid() if posted('debt_liability') else True

        if valid_assets and valid_money_owed and valid_other and valid_debt:
            # Save only posted formsets
            if posted('assets'):
                assets_formset.save()
            if posted('money_owed'):
                money_owed_formset.save()
            if posted('other_property'):
                other_property_formset.save()
            if posted('debt_liability'):
                debt_liability_formset.save()
            return redirect("comparison_nfp_page4", pk=comparison.pk)
    else:
        assets_formset = AssetFormSet(instance=form13c, prefix="assets")
        money_owed_formset = MoneyOwedFormSet(instance=form13c, prefix="money_owed")
        other_property_formset = OtherPropertyFormSet(instance=form13c, prefix="other_property")
        debt_liability_formset = DebtLiabilityFormSet(instance=form13c, prefix="debt_liability")

    return render(
        request,
        "forms/comparison_nfp_page3.html",
        {
            "pk": comparison.pk,
            "comparison": comparison,
            "assets_formset": assets_formset,
            "money_owed_formset": money_owed_formset,
            "other_property_formset": other_property_formset,
            "debt_liability_formset": debt_liability_formset,
        },
    )


@login_required
def comparison_nfp_page4(request, pk):
    """
    Page 4: Property & Debts on Date of Marriage + Excluded Property
    Uses safe per-form saving to ensure the FK `form13c` is set on new rows
    and prevents NOT NULL constraint errors when users leave extra forms empty.
    """
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

        if (
            marriage_property_formset.is_valid()
            and marriage_debt_formset.is_valid()
            and excluded_property_formset.is_valid()
        ):
            try:
                # helper to save a formset safely
                def save_safe(formset):
                    for f in formset.forms:
                        if f.cleaned_data.get('DELETE', False):
                            continue
                        # detect non-empty fields
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
                        inst.save()
                    # deletions
                    for f in formset.forms:
                        if f.cleaned_data.get('DELETE', False):
                            inst = f.instance
                            if inst and getattr(inst, 'pk', None):
                                inst.delete()

                save_safe(marriage_property_formset)
                save_safe(marriage_debt_formset)
                save_safe(excluded_property_formset)

                return redirect("comparison_nfp_page5", pk=pk)
            except Exception as e:
                from django.db import IntegrityError
                if isinstance(e, IntegrityError):
                    return render(request, "forms/user_friendly_error.html", {
                        "message": "A required field was missing for one or more rows on page 4. Please ensure required fields are filled.",
                        "details": str(e),
                        "comparison": comparison,
                        "marriage_property_formset": marriage_property_formset,
                        "marriage_debt_formset": marriage_debt_formset,
                        "excluded_property_formset": excluded_property_formset,
                    })
                else:
                    raise

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

    return render(
        request,
        "forms/comparison_nfp_page4.html",
        {
            "pk": pk,
            "comparison": comparison,
            "marriage_property_formset": marriage_property_formset,
            "marriage_debt_formset": marriage_debt_formset,
            "excluded_property_formset": excluded_property_formset,
        },
    )