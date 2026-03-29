
from django.contrib import admin
from .models import (
    FinancialStatement, 
    NetFamilyPropertyStatement, 
    ComparisonNetFamilyProperty, 
    NetFamilyPropertyAsset,
    PrintEvent,
    BillingSetting,
    Invoice,
)

@admin.register(ComparisonNetFamilyProperty)
class ComparisonNetFamilyPropertyAdmin(admin.ModelAdmin):
	list_display = (
		'court_file_number', 'prepared_by', 'applicant_name', 'respondent_name', 'valuation_date', 'statement_date', 'created_at'
	)
	search_fields = ('court_file_number', 'applicant_name', 'respondent_name')
	list_filter = ('prepared_by', 'valuation_date', 'statement_date', 'created_at')

admin.site.register(FinancialStatement)
class NetFamilyPropertyAssetInline(admin.TabularInline):
	model = NetFamilyPropertyAsset
	extra = 1



@admin.register(NetFamilyPropertyStatement)
class NetFamilyPropertyStatementAdmin(admin.ModelAdmin):
	inlines = [NetFamilyPropertyAssetInline]

admin.site.register(NetFamilyPropertyAsset)


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
