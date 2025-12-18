from django.urls import path
from . import views
from django.contrib import admin 
from django.contrib.auth.views import LogoutView
import json
app_name = 'API'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/login/', views.loginmobileView.as_view()),
    path('api/v2/auth/login/', views.loginmobileV2View.as_view()),

    # path('api/v1/saveoutbreakfarm/', views.outbreakFarmView.as_view()),
    # path('api/v1/fetchoutbreak/', views.fetchoutbreakView.as_view()),
    # path('api/v1/fetchcommunity/', views.fetchcommunityTblView.as_view()),
    # path('api/v1/fetchcocoatype/', views.fetchcocoatypeTblView.as_view()),
    # path('api/v1/cocoaageclass/', views.cocoaageclassTblView.as_view()),
    # path('api/v1/fetchoutbreakcsv/', views.fetchoutbreakCSV.as_view()),
    # path('api/v1/fetchallra/', views.fetchallRAView.as_view()),
    # path('api/v1/savepomonitoring/', views.savepomonitoringView.as_view()),

    

    path('api/v1/saveregister/', views.saveregistrationView.as_view()),
    path('api/v1/regiondistricts/', views.fetchregionDistrictsView.as_view()),
    path('api/v1/fetchallcontractors/', views.fetchallContractors.as_view()), 
    path('api/v1/activity/', views.fetchactivitiesView),
    path('api/v1/farms/', views.fetchfarmsView.as_view()),
    path('api/v1/fetchjoborder/', views.fetchjoborderView.as_view()),
    path('api/v1/fetchrehabassistants/', views.fetchRehabassistantsView.as_view()),
    path('api/v1/savemonitoringform/', views.saveMonitoringformView.as_view()),
    path('api/v1/saveactivityreport/', views.savenActivityReportView.as_view()), 
    path('api/v1/saverehabasssignment/', views.saveraAssignmentView.as_view()),
    path('api/v1/savefeedback/', views.savefeedbackView.as_view()),
    path('api/v1/version/', views.versionTblView.as_view()),
    path('api/v1/fetchpayments/', views.fetchpaymentReportView.as_view()),
    path('api/v1/fetchpaymentdetailedreport/', views.fetchpaymentdetailsReportView.as_view()),
    path('api/v1/updatefirebase/', views.updatefirebaseView.as_view()),
    
   
    
    # path('api/v1/fetchfarmstatus/', views.fetchfarmstatusView.as_view()),
    # path('api/v1/fetchpoassignedfarms/', views.fetchpoAssignedfarmsView.as_view()),
    # # path('api/v1/fetchpoassignedfarms/', views.fetchpoAssignedfarmsView),
    # path('api/v1/savemaintenancefuel/', views.savemaintenancefuelView.as_view()),
    # path('api/v1/saveobfuel/', views.saveobfuelView.as_view()),
    # path('api/v1/saveobfuel/', views.saveobfuelView.as_view()),
    # path('api/v1/saveobmonitoringform/', views.saveOBformView.as_view()),
    # path('api/v1/fetchoutbreafarmslist/', views.fetchoutbreaFarms.as_view()),
    # path('api/v1/fetchcontractor/', views.fetchcontractorView.as_view()),
    # path('api/v1/fetchallequipment/', views.fetchallEquipmentView.as_view()),
    # path('api/v1/saveequipmenteventory/', views.saveequipmentEventory.as_view()),
    # path('api/v1/fetchallfeedback/', views.fetchallFeedback.as_view()),
    # path('rehabassistantslist_drf/', views.rehabassistantsTblListView.as_view(), name='rehabassistantslist_drf'),
    # path('api/v1/savenewmaintenanceform/', views.savenewMaintenanceReportView.as_view()),
    # path('api/v1/saveContractorcertificateofworkdone/', views.saveContractorcertificateofworkdoneAPIView.as_view()),
    # path('api/v1/saveverificationfarms/', views.saveVerificationFarmsAPIView.as_view()), 
    # path('api/Coco32FormCoreSerializer/', views.Coco32FormCoreSerializerView.as_view({'get': 'list'}), name='Coco32FormCoreSerializer'),
    # path('api/Coco32FormWorkdoneByRaSerializer/', views.Coco32FormWorkdoneByRaSerializerView.as_view({'get': 'list'}), name='Coco32FormWorkdoneByRaSerializer'),
    # path('api/Coco32FormWorkdoneByPoNspSerializer/', views.Coco32FormWorkdoneByPoNspSerializerView.as_view({'get': 'list'}), name='Coco32FormWorkdoneByPoNspSerializer'),
    # path('api/v1/savemappedfarm/', views.savemappedFarmView.as_view()), 
    #  path('wbpfarmslist_drf/', views.WbpFarmsListView.as_view(), name='Wbpfarmslist_drf'),
    
 ]

