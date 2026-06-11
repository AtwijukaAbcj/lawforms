
from django.contrib import admin
from .models import (
    AffidavitOfService,
    ApplicationDivorce8A,
    BillingSetting,
    CaseFile,
    CertificateOfDivorce,
    ComparisonNetFamilyProperty,
    ComparisonNetFamilyPropertyBankAccount,
    ComparisonNetFamilyPropertyBusiness,
    ComparisonNetFamilyPropertyHouseholdItem,
    ComparisonNetFamilyPropertyInsurance,
    DivorceOrder,
    DivorceOrderA25A,
    FinancialStatement,
    Form13CAsset,
    Form13CComparison,
    Form13CBusinessInterest,
    Form13CDebtLiability,
    Form13CExcludedProperty,
    Form13CFinalTotals,
    Form13CGeneralHouseholdItem,
    Form13CMoneyOwed,
    Form13COtherProperty,
    Form13CMarriageProperty,
    Form131FinancialStatement,
    NetFamilyProperty13B,
    NetFamilyProperty13BAsset,
    NetFamilyProperty13BDebt,
    NetFamilyProperty13BExcluded,
    NetFamilyProperty13BFinalTotals,
    NetFamilyProperty13BMarriageDebt,
    NetFamilyProperty13BMarriageProperty,
    NetFamilyPropertyAsset,
    NetFamilyPropertyStatement,
    PrintEvent,
    Invoice,
)

@admin.register(ComparisonNetFamilyProperty)
class ComparisonNetFamilyPropertyAdmin(admin.ModelAdmin):
	list_display = (
        'court_file_number', 'prepared_by', 'applicant_name', 'respondent_name', 'valuation_date', 'statement_date', 'created_at'
	)
	search_fields = ('court_file_number', 'applicant_name', 'respondent_name')
	list_filter = ('prepared_by', 'valuation_date', 'statement_date', 'created_at')

@admin.register(FinancialStatement)
class FinancialStatementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "court_file_number",
        "applicant_name",
        "respondent_name",
        "updated_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "court_file_number",
                "case_file",
                "applicant_name",
                "respondent_name",
            )
        }),
        ("Saved Form 13 JSON Draft", {
            "fields": (
                "draft",
            )
        }),
        ("System", {
            "fields": (
                "is_deleted",
                "deleted_at",
                "created_at",
                "updated_at",
            )
        }),
    )
    
class NetFamilyPropertyAssetInline(admin.TabularInline):
	model = NetFamilyPropertyAsset
	extra = 1



@admin.register(NetFamilyPropertyStatement)
class NetFamilyPropertyStatementAdmin(admin.ModelAdmin):
	inlines = [NetFamilyPropertyAssetInline]

admin.site.register(NetFamilyPropertyAsset)


@admin.register(NetFamilyProperty13B)
class NetFamilyProperty13BAdmin(admin.ModelAdmin):
    list_display = ('id', 'court_file_number', 'applicant_name', 'respondent_name', 'updated_at')
    search_fields = ('court_file_number', 'applicant_name', 'respondent_name')
    list_filter = ('updated_at', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(NetFamilyProperty13BAsset)
class NetFamilyProperty13BAssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'statement', 'item', 'applicant_value', 'respondent_value')
    search_fields = ('item',)
    list_filter = ('statement',)


@admin.register(NetFamilyProperty13BDebt)
class NetFamilyProperty13BDebtAdmin(admin.ModelAdmin):
    list_display = ('id', 'statement', 'item', 'applicant_value', 'respondent_value')
    search_fields = ('item',)
    list_filter = ('statement',)


@admin.register(NetFamilyProperty13BMarriageProperty)
class NetFamilyProperty13BMarriagePropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'statement', 'item', 'applicant_value', 'respondent_value')
    search_fields = ('item',)
    list_filter = ('statement',)


@admin.register(NetFamilyProperty13BMarriageDebt)
class NetFamilyProperty13BMarriageDebtAdmin(admin.ModelAdmin):
    list_display = ('id', 'statement', 'item', 'applicant_value', 'respondent_value')
    search_fields = ('item',)
    list_filter = ('statement',)


@admin.register(NetFamilyProperty13BExcluded)
class NetFamilyProperty13BExcludedAdmin(admin.ModelAdmin):
    list_display = ('id', 'statement', 'item', 'applicant_value', 'respondent_value')
    search_fields = ('item',)
    list_filter = ('statement',)


@admin.register(NetFamilyProperty13BFinalTotals)
class NetFamilyProperty13BFinalTotalsAdmin(admin.ModelAdmin):
    list_display = ('id', 'statement')
    search_fields = ('statement__court_file_number',)


@admin.register(ComparisonNetFamilyPropertyHouseholdItem)
class ComparisonNetFamilyPropertyHouseholdItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent', 'item', 'document_number')
    search_fields = ('item', 'document_number')
    list_filter = ('parent',)


@admin.register(ComparisonNetFamilyPropertyBankAccount)
class ComparisonNetFamilyPropertyBankAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent', 'institution', 'account_number')
    search_fields = ('institution', 'account_number')
    list_filter = ('parent',)


@admin.register(ComparisonNetFamilyPropertyInsurance)
class ComparisonNetFamilyPropertyInsuranceAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent', 'company_policy', 'document_number')
    search_fields = ('company_policy', 'document_number')
    list_filter = ('parent',)


@admin.register(ComparisonNetFamilyPropertyBusiness)
class ComparisonNetFamilyPropertyBusinessAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent', 'firm_name', 'document_number')
    search_fields = ('firm_name', 'document_number')
    list_filter = ('parent',)


@admin.register(Form131FinancialStatement)
class Form131FinancialStatementAdmin(admin.ModelAdmin):
    list_display = ('id', 'court_file_number', 'applicant_name', 'respondent_name', 'updated_at')
    search_fields = ('court_file_number', 'applicant_name', 'respondent_name')
    list_filter = ('updated_at', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CaseFile)
class CaseFileAdmin(admin.ModelAdmin):
    list_display = ('court_file_number', 'owner', 'applicant_name', 'respondent_name', 'updated_at')
    search_fields = ('court_file_number', 'applicant_name', 'respondent_name', 'owner__username')
    list_filter = ('updated_at', 'created_at')


@admin.register(AffidavitOfService)
class AffidavitOfServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'court_file_number', 'plaintiff_name', 'defendant_name', 'form_variant', 'updated_at')
    search_fields = ('court_file_number', 'plaintiff_name', 'defendant_name')
    list_filter = ('form_variant', 'updated_at', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CertificateOfDivorce)
class CertificateOfDivorceAdmin(admin.ModelAdmin):
    list_display = ('id', 'court_file_number', 'applicant_name', 'respondent_name', 'updated_at')
    search_fields = ('court_file_number', 'applicant_name', 'respondent_name')
    list_filter = ('updated_at', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DivorceOrder)
class DivorceOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'court_file_number', 'applicant_name', 'respondent_name', 'judge_name', 'updated_at')
    search_fields = ('court_file_number', 'applicant_name', 'respondent_name', 'judge_name')
    list_filter = ('updated_at', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DivorceOrderA25A)
class DivorceOrderA25AAdmin(admin.ModelAdmin):
    list_display = ('id', 'court_file_number', 'applicant_name', 'respondent_name', 'judge_name', 'updated_at')
    search_fields = ('court_file_number', 'applicant_name', 'respondent_name', 'judge_name')
    list_filter = ('updated_at', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ApplicationDivorce8A)
class ApplicationDivorce8AAdmin(admin.ModelAdmin):
    list_display = ('id', 'court_file_number', 'applicant_name', 'respondent_name', 'is_joint_application', 'updated_at')
    search_fields = ('court_file_number', 'applicant_name', 'respondent_name')
    list_filter = ('is_joint_application', 'updated_at', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Form13CComparison)
class Form13CComparisonAdmin(admin.ModelAdmin):
    list_display = ('id', 'court_file_number', 'applicant_name', 'respondent_name', 'updated_at')
    search_fields = ('court_file_number', 'applicant_name', 'respondent_name')
    list_filter = ('updated_at', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Form13CAsset)
class Form13CAssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'form13c', 'nature_type_of_ownership', 'document_number')
    search_fields = ('nature_type_of_ownership', 'document_number')
    list_filter = ('form13c',)


@admin.register(Form13CGeneralHouseholdItem)
class Form13CGeneralHouseholdItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'form13c', 'item', 'document_number')
    search_fields = ('item', 'document_number')
    list_filter = ('form13c',)


@admin.register(Form13CBusinessInterest)
class Form13CBusinessInterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'form13c', 'name_of_firm', 'document_number')
    search_fields = ('name_of_firm', 'document_number')
    list_filter = ('form13c',)


@admin.register(Form13CMoneyOwed)
class Form13CMoneyOwedAdmin(admin.ModelAdmin):
    list_display = ('id', 'form13c', 'details', 'document_number')
    search_fields = ('details', 'document_number')
    list_filter = ('form13c',)


@admin.register(Form13COtherProperty)
class Form13COtherPropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'form13c', 'category', 'document_number')
    search_fields = ('category', 'document_number')
    list_filter = ('form13c',)


@admin.register(Form13CDebtLiability)
class Form13CDebtLiabilityAdmin(admin.ModelAdmin):
    list_display = ('id', 'form13c', 'category', 'document_number')
    search_fields = ('category', 'document_number')
    list_filter = ('form13c',)


@admin.register(Form13CMarriageProperty)
class Form13CMarriagePropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'form13c', 'category_details', 'is_debt')
    search_fields = ('category_details', 'document_number')
    list_filter = ('form13c', 'is_debt')


@admin.register(Form13CExcludedProperty)
class Form13CExcludedPropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'form13c', 'item', 'document_number')
    search_fields = ('item', 'document_number')
    list_filter = ('form13c',)


@admin.register(Form13CFinalTotals)
class Form13CFinalTotalsAdmin(admin.ModelAdmin):
    list_display = ('id', 'form13c')
    search_fields = ('form13c__court_file_number',)


# ============================================================
# BILLING ADMIN
# ============================================================
@admin.register(PrintEvent)
class PrintEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'form_type', 'form_identifier', 'price_charged', 'is_billed', 'printed_at')
    list_filter = ('form_type', 'is_billed', 'printed_at')
    search_fields = ('user__username', 'form_identifier')
    date_hierarchy = 'printed_at'
    readonly_fields = ('printed_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(BillingSetting)
class BillingSettingAdmin(admin.ModelAdmin):
    list_display = ('form_display_name', 'form_type', 'price_per_print', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    list_editable = ('price_per_print', 'is_active')
    search_fields = ('form_display_name', 'form_type')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user', 'status', 'total', 'created_at', 'due_date')
    list_filter = ('status', 'created_at')
    search_fields = ('invoice_number', 'user__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    filter_horizontal = ('print_events',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')