from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from portal.view.farms import *
from portal.view.map import *
from portal.view.qr_code import *
from portal.view.activities import *
from portal.view.daily_reporting import *
from portal.view.activity_reporting import *
from portal.view.weekly_monitoring import *
from portal.view.growth_monitoring import *
from portal.view.growth_monitoring_dashboard_views import *
from portal.view.staff import *
from portal.view.contractors import *
from portal.view.staff_assignment import *
from portal.view.dashboard import *
from portal.view.certification import *
from portal.view.equipment import *
from portal.view.payments import *
from portal.view.irrigation import *
# from portal.view.equipment import *
from portal.view.outbreakfarms import *
# from portal.view.verification import *
# from portal.view.contractor import *

urlpatterns = [
    path('home/', views.index, name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('change-password/', views.change_password, name='change_password'),
    path('password-change-done/', views.password_change_done, name='password_change_done'),

    path('', views.landing, name='password_reset'),
    path('dashboard/', general_dashboard, name='dashboard'),
    path('dashboard/', general_dashboard, name='dashboard_redirect'),
    path('dashboard/api/stats/', get_dashboard_stats, name='dashboard_stats'),
    path('dashboard/api/recent-activities/', get_recent_activities, name='recent_activities'),
    path('dashboard/api/chart-data/', get_chart_data, name='chart_data'),
    path('dashboard/api/upcoming-tasks/', get_upcoming_tasks, name='upcoming_tasks'),
    path('dashboard/api/notifications/', get_notifications, name='notifications'),


    # Main page
    path('farm-management/farms/', farm_details_page, name='farm_details_page'),
    
    # API endpoints
    path('api/farm-details/', farm_details_api, name='farm_details_api'),
    path('api/farm-details/<int:farm_id>/', get_farm_details, name='get_farm_details'),
    path('api/farm-details/create/', create_farm, name='create_farm'),
    path('api/farm-details/<int:farm_id>/update/', update_farm, name='update_farm'),
    path('api/farm-details/<int:farm_id>/delete/', delete_farm, name='delete_farm'),
    # path('api/get-districts-by-region/', get_districts_by_region, name='get_districts_by_region'),

    path('farm-management/mapped-farms/', farm_mapping_page, name='farm_mapping_page'),
    path('api/farm-geojson/', get_farm_geojson, name='get_farm_geojson'),
    # path('api/district-boundaries/', get_district_boundaries, name='get_district_boundaries'),
    path('api/farm-stats/', get_farm_stats, name='get_farm_stats'),
    path('api/search-farms/', search_farms, name='search_farms'),
    path('api/farm/<int:farm_id>/', get_farm_by_id, name='get_farm_by_id'),

    path('farm-management/farm-assignment/', farm_assignment_page, name='farm_assignment_page'),
    path('api/farm-assignment/', farm_assignment_api, name='farm_assignment_api'),
    # path('api/get-available-farms/', get_available_farms, name='get_available_farms'),
    path('api/get-available-staff/', get_available_staff, name='get_available_staff'),
    path('api/create-assignment/', create_assignment, name='create_assignment'),
    path('api/delete-assignment/<int:assignment_id>/', delete_assignment, name='delete_assignment'),
    path('api/assignment-details/<int:assignment_id>/', get_assignment_details, name='get_assignment_details'),


    path('qr-code-generator/', qr_code_generator, name='qr_code_generator'),
    
    # API endpoints
    path('qr-code-generator/',qr_code_generator, name='qr_code_generator'),
    path('api/qr-codes/generate/',generate_qr_codes, name='generate_qr_codes'),
    path('api/qr-codes/',get_qr_codes, name='get_qr_codes'),
    path('api/qr-codes/<int:qr_id>/delete/',delete_qr_code, name='delete_qr_code'),
    path('api/qr-codes/bulk-delete/',bulk_delete_qr_codes, name='bulk_delete_qr_codes'),
    path('api/qr-codes/<int:qr_id>/download/',download_qr_code, name='download_qr_code'),
    path('api/qr-codes/bulk-download/',download_bulk_qr_codes, name='download_bulk_qr_codes'),




     # Page view
    path('activities/', activities_overview, name='activities_overview'),
    
    # API endpoints for activities
    path('api/activities/', activity_list_api, name='activity_list_api'),
    path('api/activities/create/', activity_create, name='activity_create'),
    path('api/activities/<int:activity_id>/', activity_detail, name='activity_detail'),
    path('api/activities/<int:activity_id>/update/', activity_update, name='activity_update'),
    path('api/activities/<int:activity_id>/delete/', activity_delete, name='activity_delete'),
    
    # Helper endpoints for dropdowns
    path('api/get-agents/', get_agents, name='get_agents'),
    path('api/get-main-activities/', get_main_activities, name='get_main_activities'),
    path('api/get-sub-activities/', get_sub_activities, name='get_sub_activities'),




     # Daily Reports URLs
    path('po-daily-reports/', daily_reports, name='daily_reports'),
    path('api/daily-reports/', daily_report_list_api, name='daily_report_list_api'),
    path('api/daily-reports/create/', daily_report_create, name='daily_report_create'),
    path('api/daily-reports/<int:report_id>/', daily_report_detail, name='daily_report_detail'),
    path('api/daily-reports/<int:report_id>/update/', daily_report_update, name='daily_report_update'),
    path('api/daily-reports/<int:report_id>/delete/', daily_report_delete, name='daily_report_delete'),
    path('api/daily-reports/<int:report_id>/submit/', daily_report_submit, name='daily_report_submit'),
    path('api/daily-reports/<int:report_id>/approve/', daily_report_approve, name='daily_report_approve'),
    path('api/daily-reports/<int:report_id>/reject/', daily_report_reject, name='daily_report_reject'),
    
    # Helper endpoints for Daily Reports
    path('api/get-farms-by-po/', get_farms_by_po, name='get_farms_by_po'),
    path('api/get-ras-by-po/', get_ras_by_po, name='get_ras_by_po'),



      # Activity Reporting URLs
    path('activity-reporting/', activity_reporting, name='activity_reporting'),
    path('api/activity-reports/', activity_report_list_api, name='activity_report_list_api'),
    path('api/activity-reports/create/', activity_report_create, name='activity_report_create'),
    path('api/activity-reports/<int:report_id>/', activity_report_detail, name='activity_report_detail'),
    path('api/activity-reports/<int:report_id>/update/', activity_report_update, name='activity_report_update'),
    path('api/activity-reports/<int:report_id>/delete/', activity_report_delete, name='activity_report_delete'),
    path('api/activity-reports/<int:report_id>/submit/', activity_report_submit, name='activity_report_submit'),
    path('api/activity-reports/<int:report_id>/approve/', activity_report_approve, name='activity_report_approve'),
    path('api/activity-reports/<int:report_id>/reject/', activity_report_reject, name='activity_report_reject'),



     # Weekly Monitoring URLs
    path('weekly-monitoring/', weekly_monitoring, name='weekly_monitoring'),
    path('api/weekly-monitoring/summary/', weekly_monitoring_summary, name='weekly_monitoring_summary'),
    path('api/weekly-monitoring/trends/', weekly_monitoring_trends, name='weekly_monitoring_trends'),
    path('api/weekly-monitoring/po-performance/', weekly_monitoring_po_performance, name='weekly_monitoring_po_performance'),
    path('api/weekly-monitoring/activity-breakdown/', weekly_monitoring_activity_breakdown, name='weekly_monitoring_activity_breakdown'),
    path('api/weekly-monitoring/district-summary/', weekly_monitoring_district_summary, name='weekly_monitoring_district_summary'),
    path('api/weekly-monitoring/reports/', weekly_monitoring_reports, name='weekly_monitoring_reports'),
    path('api/weekly-monitoring/export/', weekly_monitoring_export, name='weekly_monitoring_export'),


    # Page view
    path('growth-monitoring/', growth_monitoring_page, name='growth_monitoring_page'),
    
    # API endpoints
    path('api/growth-monitoring/list/', get_growth_monitoring_list, name='growth_monitoring_list'),
    path('api/growth-monitoring/create/', create_growth_monitoring, name='growth_monitoring_create'),
    path('api/growth-monitoring/<int:record_id>/', get_growth_monitoring_detail, name='growth_monitoring_detail'),
    path('api/growth-monitoring/<int:record_id>/update/', update_growth_monitoring, name='growth_monitoring_update'),
    path('api/growth-monitoring/<int:record_id>/delete/', delete_growth_monitoring, name='growth_monitoring_delete'),
    path('api/growth-monitoring/plant-history/<str:plant_uid>/', get_plant_growth_history, name='plant_growth_history'),
    
    # Stats and dropdowns
    path('api/growth-monitoring/stats/', get_growth_stats, name='growth_monitoring_stats'),
    path('api/growth-monitoring/qr-codes/', get_qr_code, name='growth_monitoring_qr_codes'),
    path('api/growth-monitoring/plant-uids/', get_plant_uids, name='growth_monitoring_plant_uids'),


     # Dashboard page
    path('growth-monitoring-dashboard/', growth_monitoring_dashboard, name='growth_monitoring_dashboard'),
    
    # Dashboard API endpoints
    path('api/growth-monitoring/dashboard/', get_dashboard_data, name='dashboard_api'),
    path('api/growth-monitoring/map-data/', get_map_data, name='map_data_api'),
    path('api/growth-monitoring/trends/', get_growth_trends_api, name='trends_api'),
    path('api/growth-monitoring/district-stats/', get_district_stats_api, name='district_stats_api'),
    path('api/get-agents/', get_agents, name='get_agents'),
    # path('api/get-districts/', get_districts, name='get_districts'),


     # Staff Overview Pages
    path('personnel/staff/', staff_overview, name='staff_overview'),
    path('staff/list/', get_staff_list, name='staff_list_api'),
    path('staff/<int:staff_id>/', get_staff_detail, name='staff_detail_api'),
    path('staff/create/', create_staff, name='create_staff'),
    path('staff/<int:staff_id>/update/', update_staff, name='update_staff'),
    path('staff/<int:staff_id>/delete/', delete_staff, name='delete_staff'),
    
    # Staff Type endpoints
    path('staff/types/', get_staff_types, name='staff_types'),
    
    # District/Region endpoints
    path('districts/', get_districts, name='get_districts'),
    path('communities/', get_communities, name='get_communities'),
    path('projects/', get_projects, name='get_projects'),



     # Contractors URLs
    path('contractors/', contractors_overview, name='contractors_overview'),
    path('contractors/list/', get_contractors_list, name='contractors_list_api'),
    path('contractors/<int:contractor_id>/', get_contractor_detail, name='contractor_detail_api'),
    path('contractors/create/', create_contractor, name='create_contractor'),
    path('contractors/<int:contractor_id>/update/', update_contractor, name='update_contractor'),
    path('contractors/<int:contractor_id>/delete/', delete_contractor, name='delete_contractor'),
    path('contractors/<int:contractor_id>/assign-district/', assign_contractor_district, name='assign_contractor_district'),
    path('contractors/<int:contractor_id>/districts/', get_contractor_districts, name='contractor_districts'),


    # Staff Assignments URLs
    path('assignments/', staff_assignments_overview, name='staff_assignments_overview'),
    path('assignments/list/', get_assignments_list, name='assignments_list_api'),
    path('assignments/<int:assignment_id>/', get_assignment_detail, name='assignment_detail_api'),
    path('assignments/create/', create_assignment, name='create_assignment'),
    path('assignments/<int:assignment_id>/update/', update_assignment, name='update_assignment'),
    path('assignments/<int:assignment_id>/delete/', delete_assignment, name='delete_assignment'),
    path('assignments/<int:assignment_id>/submit/', submit_assignment, name='submit_assignment'),
    path('assignments/<int:assignment_id>/revoke/', revoke_assignment, name='revoke_assignment'),
    
    # Assignment Filter Endpoints
    path('assignments/po/list/', get_po_list, name='po_list'),
    path('assignments/ra/list/', get_ra_list, name='ra_list'),
    path('assignments/by-po/<int:po_id>/', get_assignments_by_po, name='assignments_by_po'),
    path('assignments/by-ra/<int:ra_id>/', get_assignments_by_ra, name='assignments_by_ra'),
    path('assignments/by-district/<int:district_id>/', get_assignments_by_district, name='assignments_by_district'),

      # Work Certificates URLs
    path('certification/ched-certificates/', work_certificates_page, name='work_certificates_page'),
    path('api/work-certificates/', work_certificate_list, name='work_certificate_list_api'),
    path('api/work-certificates/create/', work_certificate_create, name='work_certificate_create'),
    path('api/work-certificates/<int:pk>/', work_certificate_detail, name='work_certificate_detail_api'),
    path('api/work-certificates/<int:pk>/update/', work_certificate_update, name='work_certificate_update'),
    path('api/work-certificates/<int:pk>/delete/', work_certificate_delete, name='work_certificate_delete'),
    path('api/work-certificates/<int:pk>/verify/', work_certificate_verify, name='work_certificate_verify'),
    
    # Helper URLs for dropdowns
    path('api/get-contractors/', get_contractors, name='get_contractors'),
    path('api/get-projects/', get_projects, name='get_projects_api'),
    path('api/get-districts/', get_districts, name='get_districts_api'),


    # Payment Reports URLs
    path('payment/payment-reports/', payment_reports_page, name='payment_reports_page'),
    path('api/payment-reports/', payment_report_list, name='payment_report_list_api'),
    path('api/payment-reports/summary/', payment_report_summary, name='payment_report_summary'),
    path('api/payment-reports/create/', payment_report_create, name='payment_report_create'),
    path('api/payment-reports/<int:pk>/', payment_report_detail, name='payment_report_detail_api'),
    path('api/payment-reports/<int:pk>/update/', payment_report_update, name='payment_report_update'),
    path('api/payment-reports/<int:pk>/delete/', payment_report_delete, name='payment_report_delete'),
    path('api/payment-reports/detailed/', detailed_payment_report_list, name='detailed_payment_report_list'),
    path('api/payment-reports/detailed/create/', detailed_payment_report_create, name='detailed_payment_report_create'),
    path('api/payment-reports/generate/', generate_payment_report, name='generate_payment_report'),
    path('api/payment-reports/export/', export_payment_report, name='export_payment_report'),
    
    # Helper URLs
    path('api/get-ras/', get_rehab_assistants, name='get_ras'),
    path('api/get-pos/', get_pos, name='get_pos'),
    path('api/get-farms/', get_farms, name='get_farms'),
    path('api/get-activities/', get_activities, name='get_activities'),


    # Equipment Overview URLs
    path('equipment/equipment/', equipment_overview_page, name='equipment_overview_page'),
    path('api/equipment/', equipment_list, name='equipment_list_api'),
    path('api/equipment/create/', equipment_create, name='equipment_create'),
    path('api/equipment/<int:pk>/', equipment_detail, name='equipment_detail_api'),
    path('api/equipment/<int:pk>/update/', equipment_update, name='equipment_update'),
    path('api/equipment/<int:pk>/delete/', equipment_delete, name='equipment_delete'),
    path('api/equipment/<int:pk>/assign/', equipment_assign, name='equipment_assign'),
    path('api/equipment/<int:pk>/return/', equipment_return, name='equipment_return'),
    path('api/equipment/assignments/', equipment_assignment_list, name='equipment_assignment_list'),
    path('api/equipment/assignments/<int:pk>/', equipment_assignment_detail, name='equipment_assignment_detail'),
    path('api/equipment/stats/', equipment_stats, name='equipment_stats'),
    path('api/equipment/export/', export_equipment, name='export_equipment'),
    
    # Helper URLs
    path('api/get-staff/', get_staff, name='get_staff'),


     # ===== OutbreakFarm (Enhanced) API endpoints =====
    path('outbreakfarms/', outbreakfarms_overview, name='outbreakfarm_list'),

    path('api/outbreakfarms/list/', outbreakfarm_list_api, name='outbreakfarm_list_api'),
    path('api/outbreakfarms/<int:pk>/', outbreakfarm_detail_api, name='outbreakfarm_detail_api'),
    path('api/outbreakfarms/create/', outbreakfarm_create, name='outbreakfarm_create'),
    path('api/outbreakfarms/<int:pk>/update/', outbreakfarm_update, name='outbreakfarm_update'),
    path('api/outbreakfarms/<int:pk>/delete/', outbreakfarm_delete, name='outbreakfarm_delete'),
    path('api/outbreakfarms/stats/', outbreakfarm_stats_api, name='outbreakfarm_stats_api'),
    
    # ===== OutbreakFarmModel API endpoints =====
    path('api/outbreakfarms/model/list/', outbreakfarmmodel_list_api, name='outbreakfarmmodel_list_api'),
    path('api/outbreakfarms/model/<int:pk>/', outbreakfarmmodel_detail_api, name='outbreakfarmmodel_detail_api'),
    path('api/outbreakfarms/model/create/', outbreakfarmmodel_create, name='outbreakfarmmodel_create'),
    path('api/outbreakfarms/model/<int:pk>/update/', outbreakfarmmodel_update, name='outbreakfarmmodel_update'),
    path('api/outbreakfarms/model/<int:pk>/delete/', outbreakfarmmodel_delete, name='outbreakfarmmodel_delete'),
    path('api/outbreakfarms/model/stats/', outbreakfarmmodel_stats_api, name='outbreakfarmmodel_stats_api'),

    path('api/get-districts/', get_districts, name='get_districts'),
    path('api/get-regions/', get_regions, name='get_regions'),
    path('api/get-communities/', get_communities, name='get_communities'),
    path('api/get-projects/', get_projects, name='get_projects'),
    path('api/staff/list/', get_staff, name='staff_list_api'),
    path('api/farms/list/', farm_list_api, name='farm_list_api'),


     # Main Irrigation Overview page
    path('irrigation/', irrigation_overview, name='irrigation_overview'),
    
    # Irrigation API endpoints
    path('api/irrigation/list/', irrigation_list_api, name='irrigation_list_api'),
    path('api/irrigation/<int:pk>/', irrigation_detail_api, name='irrigation_detail_api'),
    path('api/irrigation/create/', irrigation_create, name='irrigation_create'),
    path('api/irrigation/<int:pk>/update/', irrigation_update, name='irrigation_update'),
    path('api/irrigation/<int:pk>/delete/', irrigation_delete, name='irrigation_delete'),
    path('api/irrigation/stats/', irrigation_stats_api, name='irrigation_stats_api'),
    path('api/irrigation/chart-data/', irrigation_chart_api, name='irrigation_chart_api'),
    
    # Dropdown API endpoints
    path('api/farms/list/', farm_list_api, name='farm_list_api'),
    path('api/staff/dropdown/', staff_list_dropdown_api, name='staff_list_dropdown_api'),

]