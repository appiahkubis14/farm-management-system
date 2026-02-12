# urls.py
from django.urls import path
from . import views
from django.contrib import admin

app_name = 'API'

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    path('v1/version/', views.versionTblView.as_view()),
    # 1. Authentication & User (POST only)
    path('v1/auth/login/', views.LoginView.as_view(), name='login'),
    
    # 2. Daily Reporting / Activity Reporting (POST only)
    path('v1/saveactivityreport/', views.SaveActivityReportView.as_view(), name='save_activity_report'),
    path('v1/savedailyreport/', views.SaveDailyReportView.as_view(), name='save_daily_report'),

    # 4. Add Personnel (POST only)
    path('v1/saveregister/', views.SaveRegisterView.as_view(), name='save_register'),
    
    # 5. Assign Rehab Assistant (RA) (POST only)
    path('v1/saverehabasssignment/', views.SaveRehabAssignmentView.as_view(), name='save_rehab_assignment'),
    
    # 6. Growth Monitoring (POST only)
    path('v1/growth-monitoring/', views.GrowthMonitoringView.as_view(), name='growth_monitoring'),
    
    # 7. Outbreak Farm (POST only)
    path('v1/saveoutbreakfarm/', views.SaveOutbreakFarmView.as_view(), name='save_outbreak_farm'),
    
    # 8. Contractor Certificate (POST only)
    path('v1/saveContractorcertificateofworkdone/', views.SaveContractorCertificateView.as_view(), name='save_contractor_certificate'),
    
    # 8. Contractor Certificate Verification (POST only)
    path('v1/saveverificationfarms/', views.SaveVerificationFarmsView.as_view(), name='save_verification_farms'),
    
    # 9. Submit Issue / Feedback (POST only)
    path('v1/savefeedback/', views.SaveFeedbackView.as_view(), name='save_feedback'),
    
    # 10. Irrigation (POST only - new endpoint)
    path('v1/saveirrigation/', views.SaveIrrigationView.as_view(), name='save_irrigation'),
    
    # 11. General Data Loading (GET endpoints)
    path('v1/regiondistricts/', views.FetchRegionDistrictsView.as_view(), name='region_districts'),
    path('v1/fetchallcontractors/', views.FetchAllContractorsView.as_view(), name='fetch_all_contractors'),
    path('v1/activity/', views.FetchActivitiesView.as_view(), name='activity'),
    path('v1/farms/', views.FetchFarmsView.as_view(), name='farms'),
    path('v1/fetchcommunity/', views.FetchCommunityView.as_view(), name='fetch_community'),
    path('v1/fetchjoborder/', views.FetchJobOrderView.as_view(), name='fetch_joborder'),
    path('v1/fetchrehabassistants/', views.FetchRehabAssistantsView.as_view(), name='fetch_rehabassistants'),
    path('v1/fetchpoassignedfarms/', views.FetchPOAssignedFarmsView.as_view(), name='fetch_po_assigned_farms'),
    path('v1/fetchoutbreak/', views.FetchOutbreakView.as_view(), name='fetch_outbreak'),
    
    # 12. Payment Report (POST only)
    path('v1/fetchpayments/', views.FetchPaymentsView.as_view(), name='fetch_payments'),
    
    # 13. Detailed Payment Report (POST only)
    path('v1/fetchpaymentdetailedreport/', views.FetchPaymentDetailedReportView.as_view(), name='fetch_payment_detailed_report'),
    
    # 15. Verification (Video Record) (POST only)
    path('v1/saveverificationrecord/', views.SaveVerificationRecordView.as_view(), name='save_verification_record'),
    
    # Calculated Area APIs
    path('v1/savecalculatedarea/', views.SaveCalculatedAreaView.as_view(), name='save_calculated_area'),
    path('v1/fetchcalculatedareas/', views.FetchCalculatedAreasView.as_view(), name='fetch_calculated_areas'),
    
    # Equipment APIs
    path('v1/saveequipment/', views.SaveEquipmentView.as_view(), name='save_equipment'),
    path('v1/fetchallequipment/', views.FetchAllEquipmentView.as_view(), name='fetch_all_equipment'),
    path('v1/equipment/<str:equipment_code>/', views.FetchEquipmentDetailView.as_view(), name='equipment_detail'),
    
    # Outbreak Farm APIs
    path('v1/saveoutbreakfarm/', views.SaveOutbreakFarmView.as_view(), name='save_outbreak_farm'),
    path('v1/fetchoutbreakfarmslist/', views.FetchOutbreakFarmsListView.as_view(), name='fetch_outbreak_farms'),
    path('v1/outbreakfarm/<str:outbreak_id>/', views.FetchOutbreakFarmDetailView.as_view(), name='outbreak_farm_detail'),
  
    # 18. save map farms
    path('v1/savemapfarms/', views.SaveMappedFarmView.as_view(), name='save_map_farms'),
]