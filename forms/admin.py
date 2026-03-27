
from django.contrib import admin
from .models import FinancialStatement, NetFamilyPropertyStatement, ComparisonNetFamilyProperty, NetFamilyPropertyAsset

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
