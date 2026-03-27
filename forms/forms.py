# forms/forms.py
from django import forms

from .models import (
    # Single-page
    NetFamilyPropertyStatement,
    FinancialStatement,

    # 13B
    NetFamilyProperty13B,
    NetFamilyProperty13BAsset,
    NetFamilyProperty13BDebt,
    NetFamilyProperty13BMarriageProperty,
    NetFamilyProperty13BMarriageDebt,
    NetFamilyProperty13BExcluded,
    NetFamilyProperty13BFinalTotals,

    # Comparison NFP base + page2 children
    ComparisonNetFamilyProperty,
    ComparisonNetFamilyPropertyHouseholdItem,
    ComparisonNetFamilyPropertyBankAccount,
    ComparisonNetFamilyPropertyInsurance,
    ComparisonNetFamilyPropertyBusiness,

    # Form 13C models
    Form13CComparison,
    Form13CAsset,
    Form13CGeneralHouseholdItem,
    Form13CBusinessInterest,
    Form13CMoneyOwed,
    Form13COtherProperty,
    Form13CDebtLiability,
    Form13CMarriageProperty,
    Form13CExcludedProperty,
    Form13CFinalTotals,
)


# ----------------------------
# Small helper for consistent UI
# ----------------------------
class BaseModelForm(forms.ModelForm):
    default_input_class = "form-control"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            widget = field.widget

            # Skip checkboxes
            if isinstance(widget, forms.CheckboxInput):
                continue

            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = (existing + f" {self.default_input_class}").strip()


# ----------------------------
# Single-page forms
# ----------------------------
class NetFamilyPropertyStatementForm(BaseModelForm):
    class Meta:
        model = NetFamilyPropertyStatement
        fields = "__all__"


class FinancialStatementForm(BaseModelForm):
    class Meta:
        model = FinancialStatement
        fields = "__all__"


# ----------------------------
# 13B Forms (multi-page)
# ----------------------------
class NetFamilyProperty13BForm(BaseModelForm):
    class Meta:
        model = NetFamilyProperty13B
        fields = "__all__"


class NetFamilyProperty13BAssetForm(BaseModelForm):
    class Meta:
        model = NetFamilyProperty13BAsset
        fields = ["item", "applicant_value", "respondent_value"]


class NetFamilyProperty13BDebtForm(BaseModelForm):
    class Meta:
        model = NetFamilyProperty13BDebt
        fields = ["item", "applicant_value", "respondent_value"]


class NetFamilyProperty13BMarriagePropertyForm(BaseModelForm):
    class Meta:
        model = NetFamilyProperty13BMarriageProperty
        fields = ["item", "applicant_value", "respondent_value"]  # ✅ FIXED


class NetFamilyProperty13BMarriageDebtForm(BaseModelForm):
    class Meta:
        model = NetFamilyProperty13BMarriageDebt
        fields = ["item", "applicant_value", "respondent_value"]  # ✅ FIXED


class NetFamilyProperty13BExcludedForm(BaseModelForm):
    class Meta:
        model = NetFamilyProperty13BExcluded
        fields = ["item", "applicant_value", "respondent_value"]


class NetFamilyProperty13BFinalTotalsForm(BaseModelForm):
    class Meta:
        model = NetFamilyProperty13BFinalTotals
        exclude = ["statement"]  # set in view


# ----------------------------
# Comparison NFP (Page 1)
# ----------------------------
class ComparisonNetFamilyPropertyForm(BaseModelForm):
    class Meta:
        model = ComparisonNetFamilyProperty
        fields = "__all__"
        widgets = {
            "valuation_date": forms.DateInput(attrs={"type": "date"}),
            "statement_date": forms.DateInput(attrs={"type": "date"}),
        }


# ----------------------------
# Comparison NFP (Page 2 child forms) - these use parent FK
# ----------------------------
class ComparisonNetFamilyPropertyHouseholdItemForm(BaseModelForm):
    class Meta:
        model = ComparisonNetFamilyPropertyHouseholdItem
        fields = [
            "item",
            "description",
            "comments",
            "document_number",
            "applicant_position_applicant",
            "applicant_position_respondent",
            "respondent_position_applicant",
            "respondent_position_respondent",
        ]


class ComparisonNetFamilyPropertyBankAccountForm(BaseModelForm):
    class Meta:
        model = ComparisonNetFamilyPropertyBankAccount
        fields = [
            "category",
            "institution",
            "account_number",
            "comments",
            "document_number",
            "applicant_position_applicant",
            "applicant_position_respondent",
            "respondent_position_applicant",
            "respondent_position_respondent",
        ]


class ComparisonNetFamilyPropertyInsuranceForm(BaseModelForm):
    class Meta:
        model = ComparisonNetFamilyPropertyInsurance
        fields = [
            "company_policy",
            "owner",
            "beneficiary",
            "face_amount",
            "comments",
            "document_number",
            "applicant_position_applicant",
            "applicant_position_respondent",
            "respondent_position_applicant",
            "respondent_position_respondent",
        ]


class ComparisonNetFamilyPropertyBusinessForm(BaseModelForm):
    class Meta:
        model = ComparisonNetFamilyPropertyBusiness
        fields = [
            "firm_name",
            "interests",
            "comments",
            "document_number",
            "applicant_position_applicant",
            "applicant_position_respondent",
            "respondent_position_applicant",
            "respondent_position_respondent",
        ]


# ----------------------------
# Form 13C (ROOT header form)
# ----------------------------
class Form13CComparisonForm(BaseModelForm):
    class Meta:
        model = Form13CComparison
        exclude = ["parent"]  # set via get_or_create(parent=...)


# ----------------------------
# Form 13C child-table forms (Page 3+)
# IMPORTANT: FK is `form13c`
# ----------------------------
class Form13CAssetForm(BaseModelForm):
    class Meta:
        model = Form13CAsset
        exclude = ["form13c"]


class Form13CGeneralHouseholdItemForm(BaseModelForm):
    class Meta:
        model = Form13CGeneralHouseholdItem
        exclude = ["form13c"]


class Form13CBusinessInterestForm(BaseModelForm):
    class Meta:
        model = Form13CBusinessInterest
        exclude = ["form13c"]


class Form13CMoneyOwedForm(BaseModelForm):
    class Meta:
        model = Form13CMoneyOwed
        exclude = ["form13c"]


class Form13COtherPropertyForm(BaseModelForm):
    class Meta:
        model = Form13COtherProperty
        exclude = ["form13c"]


class Form13CDebtLiabilityForm(BaseModelForm):
    class Meta:
        model = Form13CDebtLiability
        exclude = ["form13c"]


class Form13CMarriagePropertyForm(BaseModelForm):
    class Meta:
        model = Form13CMarriageProperty
        exclude = ["form13c"]


class Form13CExcludedPropertyForm(BaseModelForm):
    class Meta:
        model = Form13CExcludedProperty
        exclude = ["form13c"]


# ----------------------------
# Form 13C Final Totals (last page)
# ----------------------------
class Form13CFinalTotalsForm(BaseModelForm):
    class Meta:
        model = Form13CFinalTotals
        exclude = ["form13c"]  # ✅ FIXED
