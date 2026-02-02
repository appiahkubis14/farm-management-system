# admin.py
from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin, ImportExportActionModelAdmin
from import_export.widgets import ForeignKeyWidget, DateWidget
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum, Avg
from django.contrib.gis.db import models as gis_models
from django.forms import TextInput, Textarea
from django.db import models
from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.auth.models import User, Group
import json
from .models import *

# ============================================
# RESOURCE CLASSES FOR IMPORT-EXPORT
# ============================================

class timeStampResource(resources.ModelResource):
    class Meta:
        model = timeStamp
        abstract = True
        exclude = ('created_date',)
        skip_unchanged = True
        report_skipped = False
        import_id_fields = []

class groupTblResource(resources.ModelResource):
    class Meta:
        model = groupTbl
        exclude = ('created_date', 'delete_field')
        import_id_fields = ['name']

class staffTblResource(resources.ModelResource):
    class Meta:
        model = staffTbl
        exclude = ('created_date', 'delete_field')
        import_id_fields = ['contact']
        export_order = ('id', 'first_name', 'last_name', 'gender', 'dob', 'contact', 
                       'designation', 'email_address', 'district', 'staffid', 'staffidnum')

class regionStaffTblResource(resources.ModelResource):
    staffTbl_foreignkey = fields.Field(
        column_name='staff',
        attribute='staffTbl_foreignkey',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    
    class Meta:
        model = regionStaffTbl
        exclude = ('created_date', 'delete_field')

class districtStaffTblResource(resources.ModelResource):
    staffTbl_foreignkey = fields.Field(
        column_name='staff',
        attribute='staffTbl_foreignkey',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    districtTbl_foreignkey = fields.Field(
        column_name='district',
        attribute='districtTbl_foreignkey',
        widget=ForeignKeyWidget(cocoaDistrict, 'district')
    )
    
    class Meta:
        model = districtStaffTbl
        exclude = ('created_date', 'delete_field')

class usergroupTblResource(resources.ModelResource):
    class Meta:
        model = usergroupTbl
        exclude = ('created_date', 'delete_field')

class ActivitiesResource(resources.ModelResource):
    class Meta:
        model = Activities
        import_id_fields = ['activity_code']

class rehabassistantsTblResource(resources.ModelResource):
    staffTbl_foreignkey = fields.Field(
        column_name='project_officer',
        attribute='staffTbl_foreignkey',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    districtTbl_foreignkey = fields.Field(
        column_name='district',
        attribute='districtTbl_foreignkey',
        widget=ForeignKeyWidget(cocoaDistrict, 'district')
    )
    
    class Meta:
        model = rehabassistantsTbl
        exclude = ('created_date', 'delete_field', 'uid', 'fbase_code', 'passportpic', 
                   'sigcode', 'kobocode', 'comments')
        import_id_fields = ['phone_number']

class FarmdetailsTblResource(resources.ModelResource):
    districtTbl_foreignkey = fields.Field(
        column_name='district',
        attribute='districtTbl_foreignkey',
        widget=ForeignKeyWidget(cocoaDistrict, 'district')
    )
    
    class Meta:
        model = FarmdetailsTbl
        exclude = ('created_date', 'delete_field')
        import_id_fields = ['farm_reference']

class rehabassistantsAssignmentTblResource(resources.ModelResource):
    farmTbl_foreignkey = fields.Field(
        column_name='farm_reference',
        attribute='farmTbl_foreignkey',
        widget=ForeignKeyWidget(Farms, 'farm_id')
    )
    rehabassistantsTbl_foreignkey = fields.Field(
        column_name='rehab_assistant',
        attribute='rehabassistantsTbl_foreignkey',
        widget=ForeignKeyWidget(rehabassistantsTbl, 'phone_number')
    )
    activity = fields.Field(
        column_name='activity',
        attribute='activity',
        widget=ForeignKeyWidget(Activities, 'activity_code')
    )
    staffTbl_foreignkey = fields.Field(
        column_name='project_officer',
        attribute='staffTbl_foreignkey',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    
    class Meta:
        model = rehabassistantsAssignmentTbl
        exclude = ('created_date', 'delete_field', 'uid')

class weeklyMontoringTblResource(resources.ModelResource):
    staffTbl_foreignkey = fields.Field(
        column_name='project_officer',
        attribute='staffTbl_foreignkey',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    farmTbl_foreignkey = fields.Field(
        column_name='farm_reference',
        attribute='farmTbl_foreignkey',
        widget=ForeignKeyWidget(FarmdetailsTbl, 'farm_reference')
    )
    activity = fields.Field(
        column_name='activity',
        attribute='activity',
        widget=ForeignKeyWidget(Activities, 'activity_code')
    )
    districtTbl_foreignkey = fields.Field(
        column_name='district',
        attribute='districtTbl_foreignkey',
        widget=ForeignKeyWidget(cocoaDistrict, 'district')
    )
    monitoring_date = fields.Field(
        column_name='monitoring_date',
        attribute='monitoring_date',
        widget=DateWidget(format='%Y-%m-%d')
    )
    
    class Meta:
        model = weeklyMontoringTbl
        exclude = ('created_date', 'delete_field', 'uid', 'current_farm_pic', 'geom', 'code')
        export_order = ('id', 'monitoring_date', 'farm_ref_number', 'farm_size_ha', 
                       'activity', 'area_covered_ha', 'status', 'remark')

class currentstatusFarmTblResource(resources.ModelResource):
    class Meta:
        model = currentstatusFarmTbl
        exclude = ('created_date', 'delete_field')

class weeklyMontoringrehabassistTblResource(resources.ModelResource):
    class Meta:
        model = weeklyMontoringrehabassistTbl
        exclude = ('created_date', 'delete_field')

class fuelMontoringTblResource(resources.ModelResource):
    class Meta:
        model = fuelMontoringTbl
        exclude = ('created_date', 'delete_field', 'uid')

class odkUrlModelResource(resources.ModelResource):
    class Meta:
        model = odkUrlModel
        exclude = ('created_date', 'delete_field')

class communityTblResource(resources.ModelResource):
    districtTbl_foreignkey = fields.Field(
        column_name='district',
        attribute='districtTbl_foreignkey',
        widget=ForeignKeyWidget(cocoaDistrict, 'district')
    )
    
    class Meta:
        model = communityTbl
        import_id_fields = ['community']

class POdailyreportTblResource(resources.ModelResource):
    class Meta:
        model = POdailyreportTbl
        exclude = ('created_date', 'delete_field', 'code')

class activateRateResource(resources.ModelResource):
    class Meta:
        model = activateRate
        exclude = ('created_date', 'delete_field')

class contractorsTblResource(resources.ModelResource):
    class Meta:
        model = contractorsTbl
        exclude = ('created_date', 'delete_field')
        import_id_fields = ['contractor_name']

class contratorDistrictAssignmentResource(resources.ModelResource):
    class Meta:
        model = contratorDistrictAssignment
        exclude = ('created_date', 'delete_field')

class monitorbackroundtaskTblResource(resources.ModelResource):
    class Meta:
        model = monitorbackroundtaskTbl
        exclude = ('created_date', 'delete_field')

class LayersResource(resources.ModelResource):
    class Meta:
        model = Layers
        exclude = ('created_date',)
        import_id_fields = ['name']

class posRoutemonitoringResource(resources.ModelResource):
    class Meta:
        model = posRoutemonitoring
        exclude = ('created_date', 'delete_field', 'uid', 'geom')

class FeedbackResource(resources.ModelResource):
    class Meta:
        model = Feedback
        exclude = ('created_date', 'delete_field', 'uid')

class maintenanceReportResource(resources.ModelResource):
    class Meta:
        model = maintenanceReport
        exclude = ('created_date', 'delete_field', 'uuid', 'formid', 'instanceID', 
                   'submission_time', 'submitted_by', 'Take_farm_picture', 'Please_Sign_Here')

class EquipmentResource(resources.ModelResource):
    class Meta:
        model = Equipment
        exclude = ('created_date', 'delete_field', '_uuid', 'koboid', 'pic_serial_number', 
                   'pic_equipment')
        import_id_fields = ['equipment_code']

class chedcertficateofWorkdoneResource(resources.ModelResource):
    class Meta:
        model = chedcertficateofWorkdone
        exclude = ('created_date', 'delete_field', 'code')

class paymentReportResource(resources.ModelResource):
    class Meta:
        model = paymentReport
        exclude = ('created_date', 'delete_field', 'code')

class weeklyreportSummaryResource(resources.ModelResource):
    class Meta:
        model = weeklyreportSummary
        exclude = ('created_date', 'delete_field')

class farmDatabaseResource(resources.ModelResource):
    class Meta:
        model = farmDatabase
        exclude = ('created_date', 'delete_field')
        import_id_fields = ['farm_ref']

class paymentdetailedReportResource(resources.ModelResource):
    class Meta:
        model = paymentdetailedReport
        exclude = ('created_date', 'delete_field', 'code')

class versionTblResource(resources.ModelResource):
    class Meta:
        model = versionTbl
        exclude = ('created_date', 'delete_field')

class mobileMaintenanceResource(resources.ModelResource):
    class Meta:
        model = mobileMaintenance
        exclude = ('created_date', 'delete_field', 'uid', 'current_farm_pic')

class mobileMaintenancerehabassistTblResource(resources.ModelResource):
    class Meta:
        model = mobileMaintenancerehabassistTbl
        exclude = ('created_date', 'delete_field')

class verificationWorkdoneResource(resources.ModelResource):
    class Meta:
        model = verificationWorkdone
        exclude = ('created_date', 'delete_field', 'code', 'current_farm_pic', 'geom', 'uuid')

class sectorResource(resources.ModelResource):
    class Meta:
        model = sector
        exclude = ('created_date', 'delete_field')

class sectorDistrictResource(resources.ModelResource):
    class Meta:
        model = sectorDistrict
        exclude = ('created_date', 'delete_field')

class sectorStaffassignmentResource(resources.ModelResource):
    class Meta:
        model = sectorStaffassignment
        exclude = ('created_date', 'delete_field')

class seedlingEnumerationResource(resources.ModelResource):
    class Meta:
        model = seedlingEnumeration
        exclude = ('created_date', 'delete_field', 'field_uri', 'instanceID', 
                   'field_submission_date', 'summary_sheet_pic')

class seedlingenumworkdoneRaResource(resources.ModelResource):
    class Meta:
        model = seedlingenumworkdoneRa
        exclude = ('created_date', 'delete_field')

class seedlingenumworkdonePoResource(resources.ModelResource):
    class Meta:
        model = seedlingenumworkdonePo
        exclude = ('created_date', 'delete_field')

class HQcertificateRecieptResource(resources.ModelResource):
    class Meta:
        model = HQcertificateReciept
        exclude = ('created_date', 'delete_field')

class SectorcertificateRecieptResource(resources.ModelResource):
    class Meta:
        model = SectorcertificateReciept
        exclude = ('created_date', 'delete_field')

class SidebarResource(resources.ModelResource):
    class Meta:
        model = Sidebar
        exclude = ('created_date', 'delete_field')

class GroupSidebarResource(resources.ModelResource):
    class Meta:
        model = GroupSidebar
        exclude = ('created_date', 'delete_field')

class mappedFarmsResource(resources.ModelResource):
    class Meta:
        model = mappedFarms
        exclude = ('created_date', 'delete_field', 'uuid', 'geom', 'farmboundary')

class seedlingEnumerationCheckResource(resources.ModelResource):
    class Meta:
        model = seedlingEnumerationCheck
        exclude = ('created_date', 'delete_field', 'field_uri')

class powerbiReportResource(resources.ModelResource):
    class Meta:
        model = powerbiReport
        exclude = ('created_date', 'delete_field')

class FarmValidationResource(resources.ModelResource):
    class Meta:
        model = FarmValidation
        exclude = ('created_date', 'delete_field', 'field_uri')

class FarmValidationCheckResource(resources.ModelResource):
    class Meta:
        model = FarmValidationCheck
        exclude = ('created_date', 'delete_field', 'field_uri')

class weeklyActivityReportResource(resources.ModelResource):
    class Meta:
        model = weeklyActivityReport
        exclude = ('created_date', 'delete_field', 'code')

class calbankmomoTransactionResource(resources.ModelResource):
    class Meta:
        model = calbankmomoTransaction
        exclude = ('created_date', 'delete_field')
        import_id_fields = ['TransactionReference']

class JoborderResource(resources.ModelResource):
    class Meta:
        model = Joborder
        exclude = ('created_date', 'delete_field', 'job_order_code')
        import_id_fields = ['farm_reference']

class activityReportingResource(resources.ModelResource):
    class Meta:
        model = activityReporting
        exclude = ('created_date', 'delete_field', 'uid')

class activityreportingrehabassistTblResource(resources.ModelResource):
    class Meta:
        model = activityreportingrehabassistTbl
        exclude = ('created_date', 'delete_field')

class specialprojectfarmsTblResource(resources.ModelResource):
    class Meta:
        model = specialprojectfarmsTbl
        exclude = ('created_date', 'delete_field', 'code')

class odkfarmsvalidationTblResource(resources.ModelResource):
    class Meta:
        model = odkfarmsvalidationTbl
        exclude = ('created_date', 'delete_field', 'code', 'instanceID', 'deviceId', 
                   'ex_video_widget')

class odkdailyreportingTblResource(resources.ModelResource):
    class Meta:
        model = odkdailyreportingTbl
        exclude = ('created_date', 'delete_field', 'code', 'instanceID', 'deviceId')

class allFarmqueryTblResource(resources.ModelResource):
    class Meta:
        model = allFarmqueryTbl
        exclude = ('created_date', 'delete_field', 'code')

class staffFarmsAssignmentResource(resources.ModelResource):
    class Meta:
        model = staffFarmsAssignment
        exclude = ('created_date', 'delete_field')

# ============================================
# ADMIN CLASSES WITH IMPORT-EXPORT
# ============================================

# GIS Models Admin
class MajorRoadsAdmin(gis_admin.GISModelAdmin):
    list_display = ('segment', 'road_num', 'length_km_field', 'class_code')
    list_filter = ('reg_code', 'class_code')
    search_fields = ('segment', 'road_num')
    gis_widget_kwargs = {
        'attrs': {
            'default_lon': -1.023194,
            'default_lat': 7.946527,
            'default_zoom': 7,
        }
    }

class DistrictOfficesAdmin(gis_admin.GISModelAdmin):
    list_display = ('town_name',)
    search_fields = ('town_name',)

class FarmsAdmin(gis_admin.GISModelAdmin):
    list_display = ('farm_id',)
    search_fields = ('farm_id',)
    list_per_page = 50

class cocoaDistrictAdmin(gis_admin.GISModelAdmin):
    list_display = ('district', 'district_code', 'shape_area')
    search_fields = ('district', 'district_code')
    list_filter = ('district_code',)
    list_per_page = 50

# Non-GIS Models Admin
class groupTblAdmin(ImportExportModelAdmin):
    resource_class = groupTblResource
    list_display = ('name', 'created_date')
    search_fields = ('name',)
    list_per_page = 50

class staffTblAdmin(ImportExportModelAdmin):
    resource_class = staffTblResource
    list_display = ('first_name', 'last_name', 'contact', 'designation', 'district', 'staffid')
    list_filter = ('designation', 'district', 'gender')
    search_fields = ('first_name', 'last_name', 'contact', 'staffid', 'email_address')
    readonly_fields = ('staffid', 'staffidnum')
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'gender', 'dob', 'contact', 'email_address')
        }),
        ('Professional Information', {
            'fields': ('designation', 'district', 'staff_station', 'nursery')
        }),
        ('System Information', {
            'fields': ('user', 'staffid', 'staffidnum', 'crmpassword', 'uid', 'fbase_code')
        }),
    )
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('designation')

class regionStaffTblAdmin(ImportExportModelAdmin):
    resource_class = regionStaffTblResource
    list_display = ('staffTbl_foreignkey', 'created_date')
    list_filter = ('created_date',)
    search_fields = ('staffTbl_foreignkey__first_name', 'staffTbl_foreignkey__last_name')
    list_per_page = 50

class districtStaffTblAdmin(ImportExportModelAdmin):
    resource_class = districtStaffTblResource
    list_display = ('staffTbl_foreignkey', 'created_date')
    list_filter = ('created_date',)
    search_fields = ('staffTbl_foreignkey__first_name', 'staffTbl_foreignkey__last_name', 
                     'districtTbl_foreignkey__district')
    list_per_page = 50

class usergroupTblAdmin(ImportExportModelAdmin):
    resource_class = usergroupTblResource
    list_display = ('staffTbl_foreignkey', 'group_location', 'created_date')
    list_filter = ('group_location', 'created_date')
    search_fields = ('staffTbl_foreignkey__first_name', 'staffTbl_foreignkey__last_name')
    list_per_page = 50

class ActivitiesAdmin(ImportExportModelAdmin):
    resource_class = ActivitiesResource
    list_display = ('main_activity', 'sub_activity', 'activity_code', 'required_equipment')
    list_filter = ('required_equipment', 'main_activity')
    search_fields = ('main_activity', 'sub_activity', 'activity_code')
    list_per_page = 50

class rehabassistantsTblAdmin(ImportExportModelAdmin):
    resource_class = rehabassistantsTblResource
    list_display = ('name', 'phone_number', 'district', 'designation', 'staffTbl_foreignkey')
    list_filter = ('designation', 'district', 'region', 'gender')
    search_fields = ('name', 'phone_number', 'staff_code', 'id_number')
    readonly_fields = ('staff_code', 'computcode', 'uid', 'code')
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'gender', 'dob', 'phone_number', 'photo_staff', 'passportpic')
        }),
        ('Employment Details', {
            'fields': ('designation', 'district', 'region', 'staffTbl_foreignkey')
        }),
        ('Identification', {
            'fields': ('id_type', 'id_number', 'ssnit_number')
        }),
        ('Payment Information', {
            'fields': ('salary_bank_name', 'bank_branch', 'bank_account_number', 
                      'payment_option', 'owner_momo', 'momo_account_name', 'momo_number',
                      'po', 'po_number')
        }),
        ('System Information', {
            'fields': ('staff_code', 'new_staff_code', 'computcode', 'uid', 'sigcode', 
                      'kobocode', 'code', 'comments')
        }),
    )
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('districtTbl_foreignkey', 'staffTbl_foreignkey')

class FarmdetailsTblAdmin(ImportExportModelAdmin):
    resource_class = FarmdetailsTblResource
    list_display = ('farm_reference', 'farmername', 'district', 'farm_size', 'status', 'year_of_establishment')
    list_filter = ('status', 'district', 'region', 'sector', 'expunge')
    search_fields = ('farm_reference', 'farmername', 'location')
    list_per_page = 50
    actions = ['mark_as_expunged']

    def mark_as_expunged(self, request, queryset):
        queryset.update(expunge=True)
        self.message_user(request, f"{queryset.count()} farms marked as expunged")
    mark_as_expunged.short_description = "Mark selected farms as expunged"

class rehabassistantsAssignmentTblAdmin(ImportExportModelAdmin):
    resource_class = rehabassistantsAssignmentTblResource
    list_display = ('farmTbl_foreignkey', 'rehabassistantsTbl_foreignkey', 'activity', 'assigned_date')
    list_filter = ('assigned_date', 'activity')
    search_fields = ('farmTbl_foreignkey__farm_id', 'rehabassistantsTbl_foreignkey__name')
    
    list_per_page = 50

class weeklyMontoringTblAdmin(ImportExportModelAdmin):
    resource_class = weeklyMontoringTblResource
    list_display = ('monitoring_date', 'farm_ref_number', 'activity', 'area_covered_ha', 'status', 'staffTbl_foreignkey')
    list_filter = ('status', 'monitoring_date', 'district', 'activity')
    search_fields = ('farm_ref_number', 'remark', 'name_po', 'name_ras')
    readonly_fields = ('code', 'geom')
  
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('monitoring_date', 'staffTbl_foreignkey', 'farmTbl_foreignkey', 'activity')
        }),
        ('Monitoring Details', {
            'fields': ('no_rehab_assistants', 'no_rehab_technicians', 'original_farm_size', 
                      'area_covered_ha', 'status', 'remark')
        }),
        ('Location Information', {
            'fields': ('lat', 'lng', 'accuracy', 'geom')
        }),
        ('Additional Details', {
            'fields': ('current_farm_pic', 'name_ra_rt', 'contractor', 'uid', 'date_purchased',
                      'date', 'qty_purchased', 'name_operator_receiving', 'quantity_ltr',
                      'red_oil_ltr', 'engine_oil_ltr', 'rate', 'remarks')
        }),
        ('Farm Information', {
            'fields': ('farm_ref_number', 'community', 'Operational_area', 'main_activity',
                      'sub_activity', 'district', 'name_ras', 'name_po', 'po_id',
                      'quantity_plantain_suckers', 'quantity_plantain_seedling',
                      'quantity_cocoa_seedling', 'quantity')
        }),
        ('System Information', {
            'fields': ('code', 'weeddingcycle')
        }),
    )

class currentstatusFarmTblAdmin(ImportExportModelAdmin):
    resource_class = currentstatusFarmTblResource
    list_display = ('farmTbl_foreignkey', 'activity', 'status', 'monitoring_date', 'year')
    list_filter = ('status', 'year', 'activity')
    search_fields = ('farmTbl_foreignkey__farm_reference',)
  
    list_per_page = 50

class weeklyMontoringrehabassistTblAdmin(ImportExportModelAdmin):
    resource_class = weeklyMontoringrehabassistTblResource
    list_display = ('weeklyMontoringTbl_foreignkey', 'rehabassistants', 'area_covered_ha')
    list_filter = ('weeklyMontoringTbl_foreignkey__monitoring_date',)
    search_fields = ('rehabassistants',)
    list_per_page = 50

class fuelMontoringTblAdmin(ImportExportModelAdmin):
    resource_class = fuelMontoringTblResource
    list_display = ('date_received', 'farmdetailstbl_foreignkey', 'rehabassistantsTbl_foreignkey', 'fuel_ltr')
    list_filter = ('date_received',)
    search_fields = ('farmdetailstbl_foreignkey__farm_reference', 'remarks')
   
    list_per_page = 50

class odkUrlModelAdmin(ImportExportModelAdmin):
    resource_class = odkUrlModelResource
    list_display = ('form_name', 'urlname', 'csvname', 'csvtype')
    list_filter = ('csvtype',)
    search_fields = ('form_name', 'urlname', 'csvname')
    list_per_page = 50

class communityTblAdmin(ImportExportModelAdmin):
    resource_class = communityTblResource
    list_display = ('district', 'Operational_area', 'community')
    list_filter = ('district', 'Operational_area')
    search_fields = ('district', 'Operational_area', 'community')
    list_per_page = 50

class POdailyreportTblAdmin(ImportExportModelAdmin):
    resource_class = POdailyreportTblResource
    list_display = ('reporting_date', 'farm_reference', 'activity', 'percentage_of_workdone', 'status')
    list_filter = ('status', 'reporting_date')
    search_fields = ('farm_reference', 'location', 'activity_code')
   
    list_per_page = 50

class activateRateAdmin(ImportExportModelAdmin):
    resource_class = activateRateResource
    list_display = ('activate_foreignkey', 'rate')
    list_filter = ('activate_foreignkey',)
    search_fields = ('activate_foreignkey__sub_activity',)
    list_per_page = 50

class contractorsTblAdmin(ImportExportModelAdmin):
    resource_class = contractorsTblResource
    list_display = ('contractor_name', 'contact_person', 'contact_number', 'interested_services')
    search_fields = ('contractor_name', 'contact_person', 'contact_number')
    list_per_page = 50

class contratorDistrictAssignmentAdmin(ImportExportModelAdmin):
    resource_class = contratorDistrictAssignmentResource
    list_display = ('contractor',)
    list_filter = ('districtTbl_foreignkey',)
    search_fields = ('contractor__contractor_name', 'districtTbl_foreignkey__district')
    list_per_page = 50

class monitorbackroundtaskTblAdmin(ImportExportModelAdmin):
    resource_class = monitorbackroundtaskTblResource
    list_display = ('name', 'start', 'finish')
    search_fields = ('name',)
    list_per_page = 50

class LayersAdmin(ImportExportModelAdmin):
    resource_class = LayersResource
    list_display = ('name', 'layername', 'layer_type', 'created_date')
    list_filter = ('layer_type', 'created_date')
    search_fields = ('name', 'layername')
    list_per_page = 50

class posRoutemonitoringAdmin(ImportExportModelAdmin):
    resource_class = posRoutemonitoringResource
    list_display = ('staffTbl_foreignkey', 'inspection_date', 'lat', 'lng', 'accuracy')
    list_filter = ('inspection_date',)
    search_fields = ('staffTbl_foreignkey__first_name', 'staffTbl_foreignkey__last_name')
   
    list_per_page = 50

class FeedbackAdmin(ImportExportModelAdmin):
    resource_class = FeedbackResource
    list_display = ('title', 'staffTbl_foreignkey', 'Status', 'sent_date', 'farm_reference')
    list_filter = ('Status', 'sent_date', 'week', 'month')
    search_fields = ('title', 'feedback', 'farm_reference')
    readonly_fields = ('sent_date', 'uid', 'week', 'month')
    list_per_page = 50

class maintenanceReportAdmin(ImportExportModelAdmin):
    resource_class = maintenanceReportResource
    list_display = ('report_date', 'Farm_ID', 'District', 'Project_Officer', 'Farm_Size')
    list_filter = ('District', 'report_date', 'Region')
    search_fields = ('Farm_ID', 'Farm_Location', 'Project_Officer')
    readonly_fields = ('formid', 'uuid', 'instanceID', 'submission_time', 'submitted_by', 
                      'signid', 'version', 'status')
   
    list_per_page = 50

class EquipmentAdmin(ImportExportModelAdmin):
    resource_class = EquipmentResource
    list_display = ('equipment_code', 'equipment', 'serial_number', 'district', 'status', 'date_of_capturing')
    list_filter = ('status', 'district', 'region', 'date_of_capturing')
    search_fields = ('equipment_code', 'serial_number', 'manufacturer', 'telephone', 'staff_name')
    readonly_fields = ('_uuid', 'koboid', 'pic_serial_number', 'pic_equipment')
    list_per_page = 50
    
    def get_export_queryset(self, request):
        """Override to use a queryset without image field processing"""
        qs = super().get_export_queryset(request)
        return qs.defer('pic_serial_number', 'pic_equipment')
    
    def get_import_form(self):
        """Custom import form that excludes image fields"""
        form = super().get_import_form()
        form.base_fields.pop('pic_serial_number', None)
        form.base_fields.pop('pic_equipment', None)
        return form

class chedcertficateofWorkdoneAdmin(ImportExportModelAdmin):
    resource_class = chedcertficateofWorkdoneResource
    list_display = ('reference_number', 'district', 'farmer_name', 'farm_reference', 'activity', 'month', 'year')
    list_filter = ('district', 'month', 'year', 'activity')
    search_fields = ('reference_number', 'farm_reference', 'farmer_name')
    readonly_fields = ('code',)
    list_per_page = 50

class paymentReportAdmin(ImportExportModelAdmin):
    resource_class = paymentReportResource
    list_display = ('district', 'bank_name', 'salary', 'month', 'week', 'year', 'ra_name')
    list_filter = ('district', 'month', 'year', 'payment_option')
    search_fields = ('district', 'bank_name', 'ra_name', 'po_number')
    readonly_fields = ('code',)
    list_per_page = 50

class weeklyreportSummaryAdmin(ImportExportModelAdmin):
    resource_class = weeklyreportSummaryResource
    list_display = ('region', 'district', 'month', 'week', 'year')
    list_filter = ('region', 'district', 'month', 'year')
    search_fields = ('region', 'district')
    list_per_page = 50

class farmDatabaseAdmin(ImportExportModelAdmin):
    resource_class = farmDatabaseResource
    list_display = ( 'farmer_name', 'district', 'farm_size', 'po_name')
    list_filter = ('district', 'region')
    search_fields = ( 'farmer_name', 'location')
    list_per_page = 50

class paymentdetailedReportAdmin(ImportExportModelAdmin):
    resource_class = paymentdetailedReportResource
    list_display = ('ra_name', 'farm_reference', 'activity', 'achievement', 'amount', 'week', 'month', 'year')
    list_filter = ('district', 'month', 'year', 'activity')
    search_fields = ('ra_name', 'farm_reference', 'po_name', 'group_code')
    readonly_fields = ('code',)
    list_per_page = 50

class versionTblAdmin(ImportExportModelAdmin):
    resource_class = versionTblResource
    list_display = ('version', 'created_date')
    list_per_page = 50

class mobileMaintenanceAdmin(ImportExportModelAdmin):
    resource_class = mobileMaintenanceResource
    list_display = ('monitoring_date', 'farm_ref_number', 'activity', 'area_covered_ha', 'staffTbl_foreignkey')
    list_filter = ('monitoring_date', 'activity')
    search_fields = ('farm_ref_number', 'remark', 'name_of_ched_ta')
  
    list_per_page = 50

class mobileMaintenancerehabassistTblAdmin(ImportExportModelAdmin):
    resource_class = mobileMaintenancerehabassistTblResource
    list_display = ('mobileMaintenance_foreignkey', 'rehabassistantsTbl_foreignkey', 'area_covered_ha')
    list_per_page = 50

class verificationWorkdoneAdmin(ImportExportModelAdmin):
    resource_class = verificationWorkdoneResource
    list_display = ('reporting_date', 'district', 'farmer_ref_number', 'activity', 'farm_size', 'project_officer')
    list_filter = ('district', 'month', 'year', 'reporting_date')
    search_fields = ('farmer_ref_number', 'community', 'project_officer')
    readonly_fields = ('code', 'geom', 'uuid')
   
    list_per_page = 50

class sectorAdmin(ImportExportModelAdmin):
    resource_class = sectorResource
    list_display = ('sector',)
    search_fields = ('sector',)
    list_per_page = 50

class sectorDistrictAdmin(ImportExportModelAdmin):
    resource_class = sectorDistrictResource
    list_display = ('sector',)
    list_filter = ('sector',)
    list_per_page = 50

class sectorStaffassignmentAdmin(ImportExportModelAdmin):
    resource_class = sectorStaffassignmentResource
    list_display = ('sector', 'staffTbl_foreignkey')
    list_filter = ('sector',)
    search_fields = ('staffTbl_foreignkey__first_name', 'staffTbl_foreignkey__last_name')
    list_per_page = 50

class seedlingEnumerationAdmin(ImportExportModelAdmin):
    resource_class = seedlingEnumerationResource
    list_display = ('Farm_ID', 'District', 'sector_no', 'Farmer_Name', 'Location', 'reporting_date')
    list_filter = ('District', 'sector_no', 'reporting_date')
    search_fields = ('Farm_ID', 'Farmer_Name', 'Location')
    readonly_fields = ('field_uri', 'instanceID', 'field_submission_date')
   
    list_per_page = 50

class seedlingenumworkdoneRaAdmin(ImportExportModelAdmin):
    resource_class = seedlingenumworkdoneRaResource
    list_display = ('seedlingEnumeration_foreignkey', 'rehabassistantsTbl_foreignkey')
    list_per_page = 50

class seedlingenumworkdonePoAdmin(ImportExportModelAdmin):
    resource_class = seedlingenumworkdonePoResource
    list_display = ('seedlingEnumeration_foreignkey', 'staffTbl_foreignkey')
    list_per_page = 50

class HQcertificateRecieptAdmin(ImportExportModelAdmin):
    resource_class = HQcertificateRecieptResource
    list_display = ('reference_number', 'company_name', 'activity', 'total_workdone', 'status', 'certified_date')
    list_filter = ('status', 'activity', 'certified_date')
    search_fields = ('reference_number', 'company_name', 'serialNumber')
  
    list_per_page = 50

class SectorcertificateRecieptAdmin(ImportExportModelAdmin):
    resource_class = SectorcertificateRecieptResource
    list_display = ('reference_number', 'company_name', 'activity', 'total_workdone', 'sector', 'certified_date')
    list_filter = ('sector', 'activity', 'certified_date')
    search_fields = ('reference_number', 'company_name', 'serialNumber')
  
    list_per_page = 50

class SidebarAdmin(ImportExportModelAdmin):
    resource_class = SidebarResource
    list_display = ('name',)
    search_fields = ('name',)
    list_per_page = 50

class GroupSidebarAdmin(ImportExportModelAdmin):
    resource_class = GroupSidebarResource
    list_display = ('assigned_group',)
    filter_horizontal = ('hidden_sidebars',)
    list_per_page = 50

class mappedFarmsAdmin(ImportExportModelAdmin):
    resource_class = mappedFarmsResource
    list_display = ('farm_reference', 'farmer_name', 'location', 'farm_area', 'contact')
    search_fields = ('farm_reference', 'farmer_name', 'location')
    readonly_fields = ('uuid', 'geom', 'farmboundary')
    list_per_page = 50

class seedlingEnumerationCheckAdmin(ImportExportModelAdmin):
    resource_class = seedlingEnumerationCheckResource
    list_display = ('field_uri', 'created_date')
    readonly_fields = ('field_uri',)
    list_per_page = 50

class powerbiReportAdmin(ImportExportModelAdmin):
    resource_class = powerbiReportResource
    list_display = ('menu_label', 'url', 'last_updated')
    search_fields = ('menu_label', 'url')
    list_per_page = 50

class FarmValidationAdmin(ImportExportModelAdmin):
    resource_class = FarmValidationResource
    list_display = ( 'district', 'farm_size', 'farmer_name', 'reporting_date')
    list_filter = ('district', 'reporting_date')
    search_fields = ( 'farmer_name', 'farm_loc')
    readonly_fields = ('field_uri',)
   
    list_per_page = 50

class FarmValidationCheckAdmin(ImportExportModelAdmin):
    resource_class = FarmValidationCheckResource
    list_display = ('field_uri', 'created_date')
    readonly_fields = ('field_uri',)
    list_per_page = 50

class weeklyActivityReportAdmin(ImportExportModelAdmin):
    resource_class = weeklyActivityReportResource
    list_display = ('completion_date', 'farm_reference', 'activity', 'farm_size', 'rate', 'po_name')
    list_filter = ('district', 'month', 'report_week', 'activity')
    search_fields = ('farm_reference', 'farmer_name', 'community', 'po_name')
    readonly_fields = ('code',)
    
    list_per_page = 50

class calbankmomoTransactionAdmin(ImportExportModelAdmin):
    resource_class = calbankmomoTransactionResource
    list_display = ('TransactionReference', 'Name', 'PhoneNumber', 'Amount', 'Month', 'Week', 'year')
    list_filter = ('Month', 'Week', 'year', 'PaymentMode', 'BeneficiaryBank')
    search_fields = ('TransactionReference', 'Name', 'PhoneNumber', 'BeneficiaryAccount')
    readonly_fields = ('TransactionReference',)
    list_per_page = 50

class JoborderAdmin(ImportExportModelAdmin):
    resource_class = JoborderResource
    list_display = ('farm_reference', 'farmername', 'district', 'farm_size', 'sector', 'year_of_establishment')
    list_filter = ('district', 'sector', 'year_of_establishment')
    search_fields = ('farm_reference', 'farmername', 'location')
    readonly_fields = ('job_order_code',)
    list_per_page = 50

class activityReportingAdmin(ImportExportModelAdmin):
    resource_class = activityReportingResource
    list_display = ('completed_date', 'farm_ref_number', 'activity', 'area_covered_ha', 'sector', 'staffTbl_foreignkey')
    list_filter = ('districtTbl_foreignkey', 'sector', 'completed_date', 'activity')
    search_fields = ('farm_ref_number', 'community', 'remark')
    
    list_per_page = 50

class activityreportingrehabassistTblAdmin(ImportExportModelAdmin):
    resource_class = activityreportingrehabassistTblResource
    list_display = ('activityreporting_foreignkey', 'rehabassistantsTbl_foreignkey', 'area_covered_ha')
    list_per_page = 50

class specialprojectfarmsTblAdmin(ImportExportModelAdmin):
    resource_class = specialprojectfarmsTblResource
    list_display = ('plot_name', 'plot_reference_number', 'district', 'activity', 'achievement', 'name_of_po')
    list_filter = ('district', 'month', 'report_week', 'main_activity')
    search_fields = ('plot_name', 'plot_reference_number', 'name_of_po', 'mne_name')
    readonly_fields = ('code',)
    list_per_page = 50

class odkfarmsvalidationTblAdmin(ImportExportModelAdmin):
    resource_class = odkfarmsvalidationTblResource
    list_display = ( 'farmer_name', 'farm_loc', 'farm_size', 'farm_sector', 'poid', 'mne_validated')
    list_filter = ('mne_validated', 'farm_sector')
    search_fields = ( 'farmer_name', 'farm_loc', 'poid')
    readonly_fields = ('instanceID', 'deviceId',)
    list_per_page = 50

class odkdailyreportingTblAdmin(ImportExportModelAdmin):
    resource_class = odkdailyreportingTblResource
    list_display = ( 'farmer_name', 'main_activity', 'date_completion', 'poid', 'delete_check')
    list_filter = ('main_activity', 'date_completion', 'delete_check')
    search_fields = ( 'farmer_name', 'farm_loc', 'poid')
    readonly_fields = ('instanceID', 'deviceId',)
    
    list_per_page = 50

class allFarmqueryTblAdmin(ImportExportModelAdmin):
    resource_class = allFarmqueryTblResource
    list_display = ('farm_reference', 'district', 'sector', 'activity', 'farm_size', 'completion_date')
    list_filter = ('district', 'sector', 'month', 'week', 'year', 'activity')
    search_fields = ('farm_reference', 'ranrt', 'name_of_po', 'po_id')
    readonly_fields = ('code',)
    
    list_per_page = 50

class staffFarmsAssignmentAdmin(ImportExportModelAdmin):
    resource_class = staffFarmsAssignmentResource
    list_display = ('joborder_foreignkey', 'staffTbl_foreignkey')
    list_filter = ('staffTbl_foreignkey',)
    search_fields = ('joborder_foreignkey__farm_reference', 'staffTbl_foreignkey__first_name')
    list_per_page = 50

# ============================================
# REGISTER ALL MODELS
# ============================================

# GIS Models
admin.site.register(MajorRoads, MajorRoadsAdmin)
admin.site.register(DistrictOffices, DistrictOfficesAdmin)
admin.site.register(Farms, FarmsAdmin)
admin.site.register(cocoaDistrict, cocoaDistrictAdmin)

# Non-GIS Models
admin.site.register(groupTbl, groupTblAdmin)
admin.site.register(staffTbl, staffTblAdmin)
admin.site.register(regionStaffTbl, regionStaffTblAdmin)
admin.site.register(districtStaffTbl, districtStaffTblAdmin)
admin.site.register(usergroupTbl, usergroupTblAdmin)
admin.site.register(Activities, ActivitiesAdmin)
admin.site.register(rehabassistantsTbl, rehabassistantsTblAdmin)
admin.site.register(FarmdetailsTbl, FarmdetailsTblAdmin)
admin.site.register(rehabassistantsAssignmentTbl, rehabassistantsAssignmentTblAdmin)
admin.site.register(weeklyMontoringTbl, weeklyMontoringTblAdmin)
admin.site.register(currentstatusFarmTbl, currentstatusFarmTblAdmin)
admin.site.register(weeklyMontoringrehabassistTbl, weeklyMontoringrehabassistTblAdmin)
admin.site.register(fuelMontoringTbl, fuelMontoringTblAdmin)
admin.site.register(odkUrlModel, odkUrlModelAdmin)
admin.site.register(communityTbl, communityTblAdmin)
admin.site.register(POdailyreportTbl, POdailyreportTblAdmin)
admin.site.register(activateRate, activateRateAdmin)
admin.site.register(contractorsTbl, contractorsTblAdmin)
admin.site.register(contratorDistrictAssignment, contratorDistrictAssignmentAdmin)
admin.site.register(monitorbackroundtaskTbl, monitorbackroundtaskTblAdmin)
admin.site.register(Layers, LayersAdmin)
admin.site.register(posRoutemonitoring, posRoutemonitoringAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(maintenanceReport, maintenanceReportAdmin)
admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(chedcertficateofWorkdone, chedcertficateofWorkdoneAdmin)
admin.site.register(paymentReport, paymentReportAdmin)
admin.site.register(weeklyreportSummary, weeklyreportSummaryAdmin)
admin.site.register(farmDatabase, farmDatabaseAdmin)
admin.site.register(paymentdetailedReport, paymentdetailedReportAdmin)
admin.site.register(versionTbl, versionTblAdmin)
admin.site.register(mobileMaintenance, mobileMaintenanceAdmin)
admin.site.register(mobileMaintenancerehabassistTbl, mobileMaintenancerehabassistTblAdmin)
admin.site.register(verificationWorkdone, verificationWorkdoneAdmin)
admin.site.register(sector, sectorAdmin)
admin.site.register(sectorDistrict, sectorDistrictAdmin)
admin.site.register(sectorStaffassignment, sectorStaffassignmentAdmin)
admin.site.register(seedlingEnumeration, seedlingEnumerationAdmin)
admin.site.register(seedlingenumworkdoneRa, seedlingenumworkdoneRaAdmin)
admin.site.register(seedlingenumworkdonePo, seedlingenumworkdonePoAdmin)
admin.site.register(HQcertificateReciept, HQcertificateRecieptAdmin)
admin.site.register(SectorcertificateReciept, SectorcertificateRecieptAdmin)
admin.site.register(Sidebar, SidebarAdmin)
admin.site.register(GroupSidebar, GroupSidebarAdmin)
admin.site.register(mappedFarms, mappedFarmsAdmin)
admin.site.register(seedlingEnumerationCheck, seedlingEnumerationCheckAdmin)
admin.site.register(powerbiReport, powerbiReportAdmin)
admin.site.register(FarmValidation, FarmValidationAdmin)
admin.site.register(FarmValidationCheck, FarmValidationCheckAdmin)
admin.site.register(weeklyActivityReport, weeklyActivityReportAdmin)
admin.site.register(calbankmomoTransaction, calbankmomoTransactionAdmin)
admin.site.register(Joborder, JoborderAdmin)
admin.site.register(activityReporting, activityReportingAdmin)
admin.site.register(activityreportingrehabassistTbl, activityreportingrehabassistTblAdmin)
admin.site.register(specialprojectfarmsTbl, specialprojectfarmsTblAdmin)
admin.site.register(odkfarmsvalidationTbl, odkfarmsvalidationTblAdmin)
admin.site.register(odkdailyreportingTbl, odkdailyreportingTblAdmin)
admin.site.register(allFarmqueryTbl, allFarmqueryTblAdmin)
admin.site.register(staffFarmsAssignment, staffFarmsAssignmentAdmin)

from django.contrib import admin
from .models import projectStaffTbl,projectTbl

@admin.register(projectStaffTbl)
class projectStaffTblAdmin(admin.ModelAdmin):
    list_display = ['id', 'staffTbl_foreignkey', 'projectTbl_foreignkey',]
    # list_filter = ['create_date']
    search_fields = ['staffTbl_foreignkey__first_name', 'staffTbl_foreignkey__last_name', 'projectTbl_foreignkey__project_name']
    # ordering = ['-create_date']

# ============================================
# ADMIN SITE CUSTOMIZATION
# ============================================

admin.site.site_header = "Cocoa Rehabilitation System Administration"
admin.site.site_title = "Cocoa Rehab System"
admin.site.index_title = "System Administration"

# Custom admin ordering
admin.site._registry = dict(sorted(admin.site._registry.items(), key=lambda x: x[0].__name__))

admin.site.register(projectTbl)






##########################################################################################################################################
# admin.py
# admin.py
# admin.py - COMPLETELY FIXED VERSION
from django.contrib import admin
from django import forms
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.contrib import messages
from django.db.models import Count
from .models import MenuItem, SidebarConfiguration

# Form for MenuItem with validation
class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        # Filter parent choices to exclude self and descendants
        if instance and instance.pk:
            # Get all descendants to exclude
            descendants = instance.get_descendants()
            exclude_ids = [instance.pk] + [d.pk for d in descendants]
            self.fields['parent'].queryset = MenuItem.objects.exclude(id__in=exclude_ids)
        else:
            self.fields['parent'].queryset = MenuItem.objects.all()
        
        # Sort parent choices by full path for better readability
        self.fields['parent'].queryset = self.fields['parent'].queryset.order_by('display_name')
        
        # Add help text for parent field
        self.fields['parent'].help_text = "Select parent menu item. Leave blank for top-level menu."

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    form = MenuItemForm
    
    # List view configuration
    list_display = (
        'display_name_with_indent',
        'icon_preview',
        'parent_name',
        'order',
        'is_active_display',
        'child_count_display',
        'group_count',
        'url_preview'
    )
    list_display_links = ('display_name_with_indent',)
    list_editable = ('order',)
    list_filter = ('is_active', 'parent', 'allowed_groups')
    search_fields = ('display_name', 'name', 'url')
    filter_horizontal = ('allowed_groups',)
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'full_path_display',
        'level_display',
        'child_count_display'
    )
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'icon', 'url', 'order', 'is_active')
        }),
        ('Hierarchy', {
            'fields': ('parent',),
            'description': 'Set the parent menu item to create a hierarchical structure'
        }),
        ('Permissions', {
            'fields': ('allowed_groups',),
            'description': 'User groups that can access this menu item'
        }),
        ('Hierarchy Information', {
            'fields': ('full_path_display', 'level_display', 'child_count_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['activate_items', 'deactivate_items', 'make_top_level']
    
    def get_queryset(self, request):
        # Prefetch related data for better performance
        return super().get_queryset(request).select_related(
            'parent'
        ).prefetch_related(
            'children',
            'allowed_groups'
        )
    
    # Custom display methods - ALL FIXED
    def display_name_with_indent(self, obj):
        """Display name with indentation based on level"""
        if obj.level > 0:
            # For child items, show with indentation
            indent_px = obj.level * 20
            level_indicator = f'(Level {obj.level})'
            
            return format_html(
                '<div style="margin-left: {}px; display: flex; align-items: center;">'
                '<span style="margin-right: 5px;">↳</span>'
                '<strong>{}</strong>'
                '<span style="color: #666; font-size: 0.8em; margin-left: 5px;">{}</span>'
                '</div>',
                indent_px,
                obj.display_name,
                level_indicator
            )
        else:
            # For top-level items
            return format_html(
                '<strong>{}</strong>',
                obj.display_name
            )
    display_name_with_indent.short_description = 'Menu Item'
    display_name_with_indent.admin_order_field = 'display_name'
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<i class="{}" title="{}"></i>', obj.icon, obj.icon)
        return "—"
    icon_preview.short_description = 'Icon'
    
    def parent_name(self, obj):
        """Safe way to display parent name"""
        if obj.parent:
            try:
                return obj.parent.display_name
            except:
                return "(Parent)"
        return "(Top Level)"
    parent_name.short_description = 'Parent'
    parent_name.admin_order_field = 'parent__display_name'
    
    def is_active_display(self, obj):
        """Color-coded status - FIXED VERSION"""
        if obj.is_active:
            # CORRECT: Pass HTML content as a template string and variables
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">{}</span>',
                '● Active'  # This is the content that replaces {}
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">{}</span>',
                '○ Inactive'  # This is the content that replaces {}
            )
    is_active_display.short_description = 'Status'
    
    def child_count_display(self, obj):
        count = obj.children.count()
        if count > 0:
            url = reverse('admin:portal_menuitem_changelist') + f'?parent__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    child_count_display.short_description = 'Children'
    
    def group_count(self, obj):
        return obj.allowed_groups.count()
    group_count.short_description = 'Groups'
    
    def url_preview(self, obj):
        if obj.url:
            return format_html('<code style="font-size: 0.8em;">{}</code>', obj.url)
        return "—"
    url_preview.short_description = 'URL'
    
    # Read-only fields for display
    def full_path_display(self, obj):
        return obj.full_path
    full_path_display.short_description = 'Full Path'
    
    def level_display(self, obj):
        return obj.level
    level_display.short_description = 'Level'
    
    # Custom actions
    def activate_items(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} menu items activated.')
    activate_items.short_description = "Activate selected items"
    
    def deactivate_items(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} menu items deactivated.')
    deactivate_items.short_description = "Deactivate selected items"
    
    def make_top_level(self, request, queryset):
        """Make selected items top-level (remove parent)"""
        updated = queryset.update(parent=None)
        self.message_user(request, f'{updated} items set as top-level.')
    make_top_level.short_description = "Make selected items top-level"
    
    # Custom change view to show hierarchy
    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        
        # Get all descendants for display
        def get_descendants_tree(item, level=0):
            children_data = []
            for child in item.children.all().order_by('order'):
                child_data = {
                    'object': child,
                    'level': level,
                    'children': get_descendants_tree(child, level + 1)
                }
                children_data.append(child_data)
            return children_data
        
        tree_data = get_descendants_tree(obj)
        
        extra_context = extra_context or {}
        extra_context['hierarchy_tree'] = tree_data
        extra_context['show_hierarchy'] = True
        extra_context['ancestors'] = obj.get_ancestors()
        
        return super().change_view(request, object_id, form_url, extra_context)
    
    # Custom changelist view with filters for hierarchy
    def changelist_view(self, request, extra_context=None):
        # Add filter for top-level items
        extra_context = extra_context or {}
        extra_context['title'] = 'Menu Items'
        extra_context['subtitle'] = 'Manage sidebar navigation hierarchy'
        
        # Get parent filter from request
        parent_id = request.GET.get('parent__id__exact')
        if parent_id:
            try:
                parent = MenuItem.objects.get(id=parent_id)
                extra_context['current_parent'] = parent
                extra_context['breadcrumb'] = parent.get_ancestors(include_self=True)
            except MenuItem.DoesNotExist:
                pass
        
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(SidebarConfiguration)
class SidebarConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'get_theme_display', 'show_icons', 'expand_all')
    list_editable = ('is_active', 'show_icons', 'expand_all')
    fieldsets = (
        ('General Settings', {
            'fields': ('name', 'is_active', 'theme')
        }),
        ('Display Options', {
            'fields': ('show_icons', 'expand_all', 'show_user_info', 'show_search'),
        }),
    )
    
    def get_theme_display(self, obj):
        """Simple display of theme choice"""
        return obj.get_theme_display()
    get_theme_display.short_description = 'Theme'