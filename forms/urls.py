from django.urls import path
from . import views

urlpatterns = [
    path('financial-statement/list/', views.financial_statement_list, name='financial_statement_list'),
    path('financial-statement/delete/<int:pk>/', views.financial_statement_delete, name='financial_statement_delete'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('comparison-nfp/', views.ComparisonNetFamilyPropertyListView.as_view(), name='comparison_nfp_list'),
    path('cases/', views.case_list, name='case_list'),
    path('cases/new/', views.case_create, name='case_create'),
    path('cases/<int:pk>/', views.case_detail, name='case_detail'),
    path('cases/<int:pk>/push/', views.case_push_to_forms, name='case_push_to_forms'),
    path("cases/<int:pk>/edit/", views.case_create, name="case_edit"),
    path('comparison-nfp/<int:pk>/', views.ComparisonNetFamilyPropertyDetailView.as_view(), name='comparison_nfp_detail'),
    path('comparison-nfp/delete/<int:pk>/', views.comparison_nfp_delete, name='comparison_nfp_delete'),
    path('comparison-nfp/new/', views.comparison_nfp_create, name='comparison_nfp_create'),
    path('comparison-nfp/success/', views.comparison_nfp_success, name='comparison_nfp_success'),
    path('net-family-property/', views.net_family_property_create, name='net_family_property_create'),
    path('financial-statement/', views.financial_statement_create, name='financial_statement_create'),
    # 13B Multi-page form
    path('net-family-property-13b/', views.net_family_property_13b_create_page1, name='net_family_property_13b_page1'),
    path('net-family-property-13b/<int:pk>/', views.net_family_property_13b_create_page1, name='net_family_property_13b_page1_edit'),
    path('net-family-property-13b/<int:pk>/page2/', views.net_family_property_13b_create_page2, name='net_family_property_13b_page2'),
    path('net-family-property-13b/<int:pk>/page3/', views.net_family_property_13b_create_page3, name='net_family_property_13b_page3'),
    path('net-family-property-13b/list/', views.net_family_property_13b_list, name='net_family_property_13b_list'),
    path('net-family-property-13b/delete/<int:pk>/', views.net_family_property_13b_delete, name='net_family_property_13b_delete'),
    path('net-family-property-13b/view/<int:pk>/', views.net_family_property_13b_view, name='net_family_property_13b_view'),
    path('net-family-property-13b/print/<int:pk>/', views.net_family_property_13b_print, name='net_family_property_13b_print'),
    # Recycle Bin
    path('recycle-bin/', views.recycle_bin, name='recycle_bin'),
    path('recycle-bin/restore/<str:form_type>/<int:pk>/', views.restore_form, name='restore_form'),
    path('recycle-bin/permanent-delete/<str:form_type>/<int:pk>/', views.permanent_delete, name='permanent_delete'),
    path('recycle-bin/empty/', views.empty_recycle_bin, name='empty_recycle_bin'),
    # Comparison NFP pages
    path('comparison-nfp/page1/<int:pk>/', views.comparison_nfp_page1, name='comparison_nfp_page1_edit'),
    path('comparison-nfp/page2/<int:pk>/', views.comparison_nfp_page2, name='comparison_nfp_page2'),
    path('comparison-nfp/page3/<int:pk>/', views.comparison_nfp_page3, name='comparison_nfp_page3'),
    path('comparison-nfp/page4/<int:pk>/', views.comparison_nfp_page4, name='comparison_nfp_page4'),
    path('comparison-nfp/page5/<int:pk>/', views.comparison_nfp_page5, name='comparison_nfp_page5'),
    path('comparison-nfp/<int:pk>/draft/', views.comparison_nfp_draft, name='comparison_nfp_draft'),
    path('comparison-nfp/print/<int:pk>/', views.comparison_nfp_print, name='comparison_nfp_print'),
    path('comparison-nfp/view/<int:pk>/', views.comparison_nfp_full_view, name='comparison_nfp_full_view'),
    path('financial-statement/page1/', views.financial_statement_page1_redirect, name='financial_statement_page1_redirect'),
    path('financial-statement/new/', views.financial_statement_page1_new, name='financial_statement_page1_new'),
    path('financial-statement/<int:pk>/edit/', views.financial_statement_page1, name='financial_statement_page1_edit'),
    # Form 13.1 (Financial Statement Property & Support Claims)
    path('financial-statement-131/new/', views.financial_statement_131_page1_new, name='financial_statement_131_page1_new'),
    path('financial-statement-131/list/', views.financial_statement_131_list, name='financial_statement_131_list'),
    path('financial-statement-131/page1/<int:pk>/', views.financial_statement_131_page1, name='financial_statement_131_page1'),
    path('financial-statement-131/page2/<int:pk>/', views.financial_statement_131_page2, name='financial_statement_131_page2'),
    path('financial-statement-131/page3/<int:pk>/', views.financial_statement_131_page3, name='financial_statement_131_page3'),
    path('financial-statement-131/page4/<int:pk>/', views.financial_statement_131_page4, name='financial_statement_131_page4'),
    path('financial-statement-131/page5/<int:pk>/', views.financial_statement_131_page5, name='financial_statement_131_page5'),
    path('financial-statement-131/page6/<int:pk>/', views.financial_statement_131_page6, name='financial_statement_131_page6'),
    path('financial-statement-131/page7/<int:pk>/', views.financial_statement_131_page7, name='financial_statement_131_page7'),
    path('financial-statement-131/page8/<int:pk>/', views.financial_statement_131_page8, name='financial_statement_131_page8'),
    path('financial-statement-131/page9/<int:pk>/', views.financial_statement_131_page9, name='financial_statement_131_page9'),
    path('financial-statement-131/page10/<int:pk>/', views.financial_statement_131_page10, name='financial_statement_131_page10'),
    path('financial-statement-131/print/<int:pk>/', views.financial_statement_131_print, name='financial_statement_131_print'),
    path('financial-statement-131/view/<int:pk>/', views.financial_statement_131_view, name='financial_statement_131_view'),
    path('financial-statement-131/delete/<int:pk>/', views.financial_statement_131_delete, name='financial_statement_131_delete'),
    path('financial-statement/page1/<int:pk>/', views.financial_statement_page1, name='financial_statement_page1'),
    path('financial-statement/page2/<int:pk>/', views.financial_statement_page2, name='financial_statement_page2'),
    path('financial-statement/page3/<int:pk>/', views.financial_statement_page3, name='financial_statement_page3'),
    path('financial-statement/page4/<int:pk>/', views.financial_statement_page4, name='financial_statement_page4'),
    path('financial-statement/page5/<int:pk>/', views.financial_statement_page5, name='financial_statement_page5'),
    path('financial-statement/page6/<int:pk>/', views.financial_statement_page6, name='financial_statement_page6'),
    path('financial-statement/page7/<int:pk>/', views.financial_statement_page7, name='financial_statement_page7'),
    path('financial-statement/page8/<int:pk>/', views.financial_statement_page8, name='financial_statement_page8'),
    path('financial-statement/view/<int:pk>/', views.financial_statement_view, name='financial_statement_view'),
    path('financial-statement/print/<int:pk>/', views.financial_statement_print, name='financial_statement_print'),
    # Billing & Print Tracking
    path('billing/', views.billing_dashboard, name='billing_dashboard'),
    path('billing/history/', views.billing_history, name='billing_history'),
    path('billing/history/delete/<int:pk>/', views.delete_print_event, name='delete_print_event'),
    path('billing/settings/', views.billing_settings_view, name='billing_settings'),
    path('billing/admin-report/', views.admin_billing_report, name='admin_billing_report'),
    # View-only printed copy (secure, no print/screenshot)
    path('billing/printed-copy/<int:print_event_id>/', views.view_printed_copy, name='view_printed_copy'),
    # Settings
    path('settings/', views.settings_page_view, name='settings_page'),
    path('settings/email/', views.email_settings_view, name='email_settings'),
    path("affidavit-service/list/", views.affidavit_service_list, name="affidavit_service_list"),
    path("affidavit-service/new/", views.affidavit_service_page1, name="affidavit_service_page1"),
    path("affidavit-service/<int:pk>/page1/", views.affidavit_service_page1, name="affidavit_service_page1_edit"),
    path("affidavit-service/<int:pk>/page2/", views.affidavit_service_page2, name="affidavit_service_page2"),
    path("affidavit-service/view/<int:pk>/", views.affidavit_service_view, name="affidavit_service_view"),
    path("affidavit-service/print/<int:pk>/", views.affidavit_service_print, name="affidavit_service_print"),
    path("affidavit-service/print-view/<int:pk>/", views.affidavit_service_print_view, name="affidavit_service_print_view"),
    path("affidavit-service/delete/<int:pk>/", views.affidavit_service_delete, name="affidavit_service_delete"),
    # Certificate of Divorce (Form 36B)
    path('certificate-of-divorce/list/', views.certificate_of_divorce_list, name='certificate_of_divorce_list'),
    path('certificate-of-divorce/new/', views.certificate_of_divorce_create, name='certificate_of_divorce_create'),
    path('certificate-of-divorce/<int:pk>/page1/', views.certificate_of_divorce_page1, name='certificate_of_divorce_page1'),
    path('certificate-of-divorce/view/<int:pk>/', views.certificate_of_divorce_view, name='certificate_of_divorce_view'),
    path('certificate-of-divorce/print/<int:pk>/', views.certificate_of_divorce_print, name='certificate_of_divorce_print'),
    path('certificate-of-divorce/print-view/<int:pk>/', views.certificate_of_divorce_print_view, name='certificate_of_divorce_print_view'),
    path('certificate-of-divorce/delete/<int:pk>/', views.certificate_of_divorce_delete, name='certificate_of_divorce_delete'),
    # Divorce Order (Form 25A)
    path('divorce-order/list/', views.divorce_order_list, name='divorce_order_list'),
    path('divorce-order/onepage-list/', views.divorce_order_onepage_list, name='divorce_order_onepage_list'),
    path('divorce-order/onepage/new/', views.divorce_order_a25a_create, name='divorce_order_a25a_create'),
    path('divorce-order/onepage/<int:pk>/page/', views.divorce_order_a25a_page, name='divorce_order_a25a_page'),
    path('divorce-order/onepage/view/<int:pk>/', views.divorce_order_a25a_view, name='divorce_order_a25a_view'),
    path('divorce-order/onepage/print/<int:pk>/', views.divorce_order_a25a_print, name='divorce_order_a25a_print'),
    path('divorce-order/onepage/print-view/<int:pk>/', views.divorce_order_a25a_print_view, name='divorce_order_a25a_print_view'),
    path('divorce-order/onepage/delete/<int:pk>/', views.divorce_order_a25a_delete, name='divorce_order_a25a_delete'),
    path('divorce-order/new/', views.divorce_order_create, name='divorce_order_create'),
    path('divorce-order/<int:pk>/page/', views.divorce_order_page, name='divorce_order_page'),
    path('divorce-order/view/<int:pk>/', views.divorce_order_view, name='divorce_order_view'),
    path('divorce-order/print/<int:pk>/', views.divorce_order_print, name='divorce_order_print'),
    path('divorce-order/print-onepage/<int:pk>/', views.divorce_order_print_onepage, name='divorce_order_print_onepage'),
    path('divorce-order/print-view/<int:pk>/', views.divorce_order_print_view, name='divorce_order_print_view'),
    path('divorce-order/delete/<int:pk>/', views.divorce_order_delete, name='divorce_order_delete'),
# =====================================================
# FORM 8A — APPLICATION (DIVORCE)
# =====================================================

    path(
        'application-divorce-8a/',
        views.application_divorce_8a_list,
        name='application_divorce_8a_list'
    ),

    path(
        'application-divorce-8a/create/',
        views.application_divorce_8a_create,
        name='application_divorce_8a_create'
    ),

    path(
        'application-divorce-8a/<int:pk>/page1/',
        views.application_divorce_8a_page1,
        name='application_divorce_8a_page1'
    ),

    path(
        'application-divorce-8a/<int:pk>/page1/',
        views.application_divorce_8a_page1,
        name='application_divorce_8a_page1_edit'
    ),

    path(
        'application-divorce-8a/<int:pk>/page2/',
        views.application_divorce_8a_page2,
        name='application_divorce_8a_page2'
    ),

    path(
        'application-divorce-8a/<int:pk>/page3/',
        views.application_divorce_8a_page3,
        name='application_divorce_8a_page3'
    ),

    path(
        'application-divorce-8a/<int:pk>/page4/',
        views.application_divorce_8a_page4,
        name='application_divorce_8a_page4'
    ),

    path(
        'application-divorce-8a/<int:pk>/page5/',
        views.application_divorce_8a_page5,
        name='application_divorce_8a_page5'
    ),

    path(
        'application-divorce-8a/<int:pk>/page6/',
        views.application_divorce_8a_page6,
        name='application_divorce_8a_page6'
    ),

    path(
        'application-divorce-8a/<int:pk>/view/',
        views.application_divorce_8a_view,
        name='application_divorce_8a_view'
    ),

    path(
        'application-divorce-8a/<int:pk>/print/',
        views.application_divorce_8a_print,
        name='application_divorce_8a_print'
    ),

    path(
        'application-divorce-8a/delete/<int:pk>/',
        views.application_divorce_8a_delete,
        name='application_divorce_8a_delete'
    ),

    path("affidavit-service/<int:pk>/page-3/", views.affidavit_service_page3, name="affidavit_service_page3"),      
        
]
