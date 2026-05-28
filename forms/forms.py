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
    AffidavitOfService,
    ApplicationDivorce8A,
    CertificateOfDivorce,
    DivorceOrder,
)
# from .models import AffidavitService

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


class AffidavitOfServiceForm(BaseModelForm):
    class Meta:
        model = AffidavitOfService
        fields = "__all__"


class CertificateOfDivorceForm(BaseModelForm):
    class Meta:
        model = CertificateOfDivorce
        exclude = ["case_file"]
        widgets = {
            "marriage_date": forms.DateInput(attrs={"type": "date"}),
            "divorce_order_date": forms.DateInput(attrs={"type": "date"}),
            "divorce_effective_date": forms.DateInput(attrs={"type": "date"}),
            "date_of_signature": forms.DateInput(attrs={"type": "date"}),
        }


class DivorceOrderForm(BaseModelForm):
    class Meta:
        model = DivorceOrder
        exclude = ["case_file"]
        widgets = {
            "marriage_date": forms.DateInput(attrs={"type": "date"}),
            "date_of_order": forms.DateInput(attrs={"type": "date"}),
            "date_of_signature": forms.DateInput(attrs={"type": "date"}),
        }


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

# =====================================================
# FORM 6B - AFFIDAVIT OF SERVICE FORMS
# =====================================================

class AffidavitServicePage1Form(BaseModelForm):
    class Meta:
        model = AffidavitOfService
        fields = [
            "court_name",
            "court_file_number",
            "court_office_address",
            "court_phone_number",

            "plaintiff_name",
            "applicant_lawyer_details",

            "defendant_name",
            "respondent_lawyer_details",

            "server_name",
            "server_city",

            "served_name",
            "served_date",
            "served_time",

            "served_at_address",
            "documents_served",

            "document_1_name",
            "document_1_author",
            "document_1_date",

            "document_2_name",
            "document_2_author",
            "document_2_date",

            "document_3_name",
            "document_3_author",
            "document_3_date",

            "document_4_name",
            "document_4_author",
            "document_4_date",

            "document_5_name",
            "document_5_author",
            "document_5_date",

            "service_special",
            "service_mail",
            "service_same_day_courier",
            "service_next_day_courier",
            "service_document_exchange",
            "service_electronic_document_exchange",
            "service_fax",
            "service_email",
            "service_substituted",
        ]

        widgets = {
            "served_date": forms.DateInput(attrs={"type": "date"}),
            "served_time": forms.TimeInput(attrs={"type": "time"}),

            "document_1_date": forms.DateInput(attrs={"type": "date"}),
            "document_2_date": forms.DateInput(attrs={"type": "date"}),
            "document_3_date": forms.DateInput(attrs={"type": "date"}),
            "document_4_date": forms.DateInput(attrs={"type": "date"}),
            "document_5_date": forms.DateInput(attrs={"type": "date"}),

            "plaintiff_name": forms.Textarea(attrs={"rows": 3}),
            "defendant_name": forms.Textarea(attrs={"rows": 3}),
            "applicant_lawyer_details": forms.Textarea(attrs={"rows": 3}),
            "respondent_lawyer_details": forms.Textarea(attrs={"rows": 3}),
        }
        
class AffidavitServicePage2Form(BaseModelForm):
    class Meta:
        model = AffidavitOfService
        fields = [
            "special_service_place",

            "special_service_left_with_person",
            "special_service_left_with_named_person",
            "special_service_named_person",

            "special_service_accepted_in_writing",
            "special_service_lawyer_of_record",

            "special_service_officer_position",
            "special_service_officer_position_details",

            "special_service_corporation_named",

            "special_service_prepaid_return_postcard",

            "special_service_sealed_envelope_residence",
            "special_service_adult_resident_name",

            "special_service_other",
            "special_service_other_details",

            "mail_service_address",

            "mail_address_place_of_business",
            "mail_address_lawyer_accepted",
            "mail_address_lawyer_record",
            "mail_address_home",
            "mail_address_recent_document",
            "mail_address_other",
            "mail_address_other_details",

            "courier_pickup_time",
            "courier_pickup_date",
            "courier_service_name",
            "courier_service_address",

            "courier_address_place_of_business",
            "courier_address_lawyer_accepted",
            "courier_address_lawyer_record",
            "courier_address_home",
            "courier_address_recent_document",
            "courier_address_other",
            "courier_address_other_details",

            "commissioner_municipality",
            "commissioner_province",
            "sworn_date",
            "commissioner_name",
            "signature",
        ]


class AffidavitServicePage3Form(BaseModelForm):
    class Meta:
        model = AffidavitOfService
        fields = [
            "document_exchange_service",
            "document_exchange_details",

            "electronic_document_exchange_service",
            "electronic_document_exchange_details",

            "fax_service",
            "fax_service_details",

            "email_service",
            "email_service_details",

            "service_order_date",
            "service_order_substituted_service",
            "service_order_advertisement",
            "service_order_details",

            "relationship_to_party",

            "is_at_least_18",

            "kilometres_travelled",
            "service_fee",
            "travel_fee",

            "commissioner_municipality",
            "commissioner_province",
            "sworn_date",
            "commissioner_name",
            "signature",
        ]



# =====================================================
# FORM 8A FORMS
# =====================================================

class ApplicationDivorce8APage1Form(BaseModelForm):
    class Meta:
        model = ApplicationDivorce8A
        fields = [
            "court_name",
            "court_file_number",
            "court_office_address",
            "is_simple_divorce",
            "is_joint_application",
            "applicant_name",
            "applicant_address",
            "applicant_phone_fax",
            "applicant_email",
            "applicant_lawyer_name",
            "applicant_lawyer_address",
            "applicant_lawyer_phone_fax",
            "applicant_lawyer_email",
            "respondent_name",
            "respondent_address",
            "respondent_phone_fax",
            "respondent_email",
            "respondent_lawyer_name",
            "respondent_lawyer_address",
            "respondent_lawyer_phone_fax",
            "respondent_lawyer_email",
        ]


class ApplicationDivorce8APage2Form(BaseModelForm):
    class Meta:
        model = ApplicationDivorce8A
        fields = [
            "court_file_number",
            "date_of_issue",
            "is_joint_application",
            "joint_application_details",
            "clerk_name",
            "clerk_signature",
        ]
        widgets = {
            "date_of_issue": forms.DateInput(attrs={"type": "date"}),
        }


class ApplicationDivorce8APage3Form(BaseModelForm):
    class Meta:
        model = ApplicationDivorce8A
        fields = [
            "court_file_number",
            "applicant_age",
            "applicant_birthdate",
            "applicant_resident_in",
            "applicant_first_name_before_marriage",
            "applicant_last_name_before_marriage",
            "applicant_gender",
            "applicant_divorced_before",
            "applicant_previous_divorce_details",
            "applicant_resided_ontario_one_year",
            "respondent_age",
            "respondent_birthdate",
            "respondent_resident_in",
            "respondent_first_name_before_marriage",
            "respondent_last_name_before_marriage",
            "respondent_gender",
            "respondent_divorced_before",
            "respondent_previous_divorce_details",
            "respondent_resided_ontario_one_year",
            "married_on",
            "started_living_together_on",
            "separated_on",
            "never_lived_together",
            "children_details",
            "previous_court_case",
            "previous_written_agreement",
            "previous_agreement_details",
        ]
        widgets = {
            "applicant_previous_divorce_details": forms.TextInput(),
            "respondent_previous_divorce_details": forms.TextInput(),
            "applicant_birthdate": forms.DateInput(attrs={"type": "date"}),
            "respondent_birthdate": forms.DateInput(attrs={"type": "date"}),
            "married_on": forms.DateInput(attrs={"type": "date"}),
            "started_living_together_on": forms.DateInput(attrs={"type": "date"}),
            "separated_on": forms.DateInput(attrs={"type": "date"}),
        }


class ApplicationDivorce8APage4Form(BaseModelForm):
    class Meta:
        model = ApplicationDivorce8A
        fields = [
            "court_file_number",
            "notice_of_calculation_issued",
            "notice_of_calculation_details",
            "asking_different_child_support",
            "different_child_support_explanation",
            "claim_divorce",
            "claim_spousal_support",
            "claim_child_support_table",
            "claim_child_support_other",
            "claim_decision_making",
            "claim_parenting_time",
            "claim_support_child_table_family_law",
            "claim_support_child_other_family_law",
            "claim_restraining_order",
            "claim_indexing_spousal_support",
            "claim_declaration_parentage",
            "claim_guardianship_child_property",
            "claim_property_equalization",
            "claim_exclusive_possession_home",
            "claim_exclusive_possession_contents",
            "claim_freezing_assets",
            "claim_sale_family_property",
            "claim_costs",
            "claim_annulment",
            "claim_prejudgment_interest",
            "claim_other",
            "other_claims",
            "simple_claim_divorce",
            "simple_claim_costs",
            "divorce_ground_separation",
            "separation_date",
            "not_lived_together_since",
            "lived_together_attempt_reconcile",
            "lived_together_periods",
            "divorce_ground_adultery",
            "adultery_spouse_name",
            "adultery_details",
        ]
        widgets = {
            "separation_date": forms.DateInput(attrs={"type": "date"}),
        }


class ApplicationDivorce8APage5Form(BaseModelForm):
    class Meta:
        model = ApplicationDivorce8A
        fields = [
            "court_file_number",
            "divorce_ground_cruelty",
            "cruelty_spouse_name",
            "cruelty_victim_name",
            "cruelty_details",
            "joint_orders_details",
            "important_facts_supporting_claims",
            "applicant_certificate_confirmed",
            "applicant_signature",
            "applicant_signature_date",
            "joint_applicant_signature_1",
            "joint_applicant_signature_1_date",
            "joint_applicant_signature_2",
            "joint_applicant_signature_2_date",
        ]
        widgets = {
            "applicant_signature_date": forms.DateInput(attrs={"type": "date"}),
            "joint_applicant_signature_1_date": forms.DateInput(attrs={"type": "date"}),
            "joint_applicant_signature_2_date": forms.DateInput(attrs={"type": "date"}),
        }


class ApplicationDivorce8APage6Form(BaseModelForm):
    class Meta:
        model = ApplicationDivorce8A
        fields = [
            "court_file_number",
            "applicant_lawyer_certificate_name",
            "applicant_lawyer_certificate_date",
            "applicant_lawyer_certificate_signature",
            "respondent_lawyer_certificate_name",
            "respondent_lawyer_certificate_date",
            "respondent_lawyer_certificate_signature",
            "filing_date",
            "place_of_filing",
            "filing_notes",
            "additional_notes",
            "special_filing_instructions",
            "marriage_certificate",
            "financial_statement_attachment",
            "other_supporting_documents",
            "review_confirmed",
            "documents_complete",
            "is_completed",
        ]
        widgets = {
            "applicant_lawyer_certificate_date": forms.DateInput(attrs={"type": "date"}),
            "respondent_lawyer_certificate_date": forms.DateInput(attrs={"type": "date"}),
            "filing_date": forms.DateInput(attrs={"type": "date"}),
        }