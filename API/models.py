from django.db import models
from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from django.contrib.gis.db import models
from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.auth import get_user_model 
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User


# class Coco32FormCore(models.Model):
#     field_uri = models.CharField(primary_key_key=True,db_column='_URI', unique=True, max_length=80,)  # Field name made lowercase. Field renamed because it started with '_'.
#     field_creator_uri_user = models.CharField(db_column='_CREATOR_URI_USER', max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
#     field_creation_date = models.DateTimeField(db_column='_CREATION_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
#     field_last_update_uri_user = models.CharField(db_column='_LAST_UPDATE_URI_USER', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
#     field_last_update_date = models.DateTimeField(db_column='_LAST_UPDATE_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
#     field_model_version = models.IntegerField(db_column='_MODEL_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
#     field_ui_version = models.IntegerField(db_column='_UI_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
#     field_is_complete = models.BooleanField(db_column='_IS_COMPLETE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
#     field_submission_date = models.DateTimeField(db_column='_SUBMISSION_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
#     field_marked_as_complete_date = models.DateTimeField(db_column='_MARKED_AS_COMPLETE_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
#     location = models.CharField(db_column='LOCATION', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     farm_size = models.CharField(db_column='FARM_SIZE', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     sector_no = models.IntegerField(db_column='SECTOR_NO', blank=True, null=True)  # Field name made lowercase.
#     farm_id = models.CharField(db_column='FARM_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     please_kindly_pick_the_farm_geo_point_acc = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_ACC', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
#     farmer_name = models.CharField(db_column='FARMER_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     staff_id = models.CharField(db_column='STAFF_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     start_raw = models.CharField(db_column='START_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     general_remarks = models.CharField(db_column='GENERAL_REMARKS', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     afarinick_cocoa_plantain_enumeration_form = models.CharField(db_column='AFARINICK_COCOA_PLANTAIN_ENUMERATION_FORM', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     reporting_date_raw = models.CharField(db_column='REPORTING_DATE_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     meta_instance_id = models.CharField(db_column='META_INSTANCE_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     district = models.CharField(db_column='DISTRICT', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     end_raw = models.CharField(db_column='END_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     number_cocoa_seedlings = models.IntegerField(db_column='NUMBER_COCOA_SEEDLINGS', blank=True, null=True)  # Field name made lowercase.
#     please_kindly_pick_the_farm_geo_point_lng = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_LNG', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
#     staff_name = models.CharField(db_column='STAFF_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     please_kindly_pick_the_farm_geo_point_alt = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_ALT', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
#     please_kindly_pick_the_farm_geo_point_lat = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_LAT', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
#     workdone_by = models.CharField(db_column='WORKDONE_BY', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     region = models.CharField(db_column='REGION', max_length=255, blank=True, null=True)  # Field name made lowercase.
#     reporting_date = models.DateTimeField(db_column='REPORTING_DATE', blank=True, null=True)  # Field name made lowercase.
#     start = models.DateTimeField(db_column='START', blank=True, null=True)  # Field name made lowercase.
#     end = models.DateTimeField(db_column='END', blank=True, null=True)  # Field name made lowercase.
#     number_plantain_seedlings = models.IntegerField(db_column='NUMBER_PLANTAIN_SEEDLINGS', blank=True, null=True)  # Field name made lowercase.

#     class Meta:
#         managed = False
#         db_table = 'COCO32_FORM_CORE'

class Coco32FormCore(models.Model):
    field_uri = models.CharField(db_column='_URI', unique=True, max_length=80 ,primary_key=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creator_uri_user = models.CharField(db_column='_CREATOR_URI_USER', max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creation_date = models.DateTimeField(db_column='_CREATION_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_uri_user = models.CharField(db_column='_LAST_UPDATE_URI_USER', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_date = models.DateTimeField(db_column='_LAST_UPDATE_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_model_version = models.IntegerField(db_column='_MODEL_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_ui_version = models.IntegerField(db_column='_UI_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_is_complete = models.BooleanField(db_column='_IS_COMPLETE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_submission_date = models.DateTimeField(db_column='_SUBMISSION_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_marked_as_complete_date = models.DateTimeField(db_column='_MARKED_AS_COMPLETE_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    sector_no = models.IntegerField(db_column='SECTOR_NO', blank=True, null=True)  # Field name made lowercase.
    farm_id = models.CharField(db_column='FARM_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    please_kindly_pick_the_farm_geo_point_acc = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_ACC', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
    staff_id = models.CharField(db_column='STAFF_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    start_raw = models.CharField(db_column='START_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    general_remarks = models.CharField(db_column='GENERAL_REMARKS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    afarinick_cocoa_plantain_enumeration_form = models.CharField(db_column='AFARINICK_COCOA_PLANTAIN_ENUMERATION_FORM', max_length=255, blank=True, null=True)  # Field name made lowercase.
    reporting_date_raw = models.CharField(db_column='REPORTING_DATE_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    meta_instance_id = models.CharField(db_column='META_INSTANCE_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    district = models.CharField(db_column='DISTRICT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    farms_details_farm_size = models.CharField(db_column='FARMS_DETAILS_FARM_SIZE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    farms_details_year_of_establishment_raw = models.CharField(db_column='FARMS_DETAILS_YEAR_OF_ESTABLISHMENT_RAW', max_length=255, blank=True, null=True) 
    end_raw = models.CharField(db_column='END_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    number_cocoa_seedlings = models.IntegerField(db_column='NUMBER_COCOA_SEEDLINGS', blank=True, null=True)  # Field name made lowercase.
    please_kindly_pick_the_farm_geo_point_lng = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_LNG', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
    staff_name = models.CharField(db_column='STAFF_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    farms_details_farmer_name = models.CharField(db_column='FARMS_DETAILS_FARMER_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    please_kindly_pick_the_farm_geo_point_alt = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_ALT', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
    please_kindly_pick_the_farm_geo_point_lat = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_LAT', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
    workdone_by = models.CharField(db_column='WORKDONE_BY', max_length=255, blank=True, null=True)  # Field name made lowercase.
    farms_details_location = models.CharField(db_column='FARMS_DETAILS_LOCATION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    region = models.CharField(db_column='REGION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    reporting_date = models.DateTimeField(db_column='REPORTING_DATE', blank=True, null=True)  # Field name made lowercase.
    start = models.DateTimeField(db_column='START', blank=True, null=True)  # Field name made lowercase.
    end = models.DateTimeField(db_column='END', blank=True, null=True)  # Field name made lowercase.
    number_plantain_seedlings = models.IntegerField(db_column='NUMBER_PLANTAIN_SEEDLINGS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'COCO32_FORM_CORE'



class Coco32FormWorkdoneByPoNsp(models.Model):
    field_uri = models.CharField(primary_key=True,db_column='_URI', unique=True, max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creator_uri_user = models.CharField(db_column='_CREATOR_URI_USER', max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creation_date = models.DateTimeField(db_column='_CREATION_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_uri_user = models.CharField(db_column='_LAST_UPDATE_URI_USER', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_date = models.DateTimeField(db_column='_LAST_UPDATE_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_parent_auri = models.CharField(db_column='_PARENT_AURI', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_ordinal_number = models.IntegerField(db_column='_ORDINAL_NUMBER')  # Field name made lowercase. Field renamed because it started with '_'.
    field_top_level_auri = models.CharField(db_column='_TOP_LEVEL_AURI', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    workdone_by_staff_name_po_nsp = models.CharField(db_column='WORKDONE_BY_STAFF_NAME_PO_NSP', max_length=255, blank=True, null=True)  # Field name made lowercase.
    staff_id_workdone_by_po_nsp = models.CharField(db_column='STAFF_ID_WORKDONE_BY_PO_NSP', max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'COCO32_FORM_WORKDONE_BY_PO_NSP'


class Coco32FormWorkdoneByRa(models.Model):
    field_uri = models.CharField(primary_key=True,db_column='_URI', unique=True, max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creator_uri_user = models.CharField(db_column='_CREATOR_URI_USER', max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creation_date = models.DateTimeField(db_column='_CREATION_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_uri_user = models.CharField(db_column='_LAST_UPDATE_URI_USER', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_date = models.DateTimeField(db_column='_LAST_UPDATE_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_parent_auri = models.CharField(db_column='_PARENT_AURI', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_ordinal_number = models.IntegerField(db_column='_ORDINAL_NUMBER')  # Field name made lowercase. Field renamed because it started with '_'.
    field_top_level_auri = models.CharField(db_column='_TOP_LEVEL_AURI', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    workdone_by_ra_name = models.CharField(db_column='WORKDONE_BY_RA_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    workdone_by_ra_id = models.CharField(db_column='WORKDONE_BY_RA_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'COCO32_FORM_WORKDONE_BY_RA'


class FarmInspectionAndManagementCore(models.Model):
    field_uri = models.CharField(primary_key=True,db_column='_URI', unique=True, max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creator_uri_user = models.CharField(db_column='_CREATOR_URI_USER', max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creation_date = models.DateTimeField(db_column='_CREATION_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_uri_user = models.CharField(db_column='_LAST_UPDATE_URI_USER', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_date = models.DateTimeField(db_column='_LAST_UPDATE_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_model_version = models.IntegerField(db_column='_MODEL_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_ui_version = models.IntegerField(db_column='_UI_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_is_complete = models.BooleanField(db_column='_IS_COMPLETE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_submission_date = models.DateTimeField(db_column='_SUBMISSION_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_marked_as_complete_date = models.DateTimeField(db_column='_MARKED_AS_COMPLETE_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    location = models.CharField(db_column='LOCATION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    farm_size = models.DecimalField(db_column='FARM_SIZE', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
    diseaseand_pest_control_disease_cssvd = models.CharField(db_column='DISEASEAND_PEST_CONTROL_DISEASE_CSSVD', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sector_no = models.IntegerField(db_column='SECTOR_NO', blank=True, null=True)  # Field name made lowercase.
    farm_id = models.CharField(db_column='FARM_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    genrl_ppearnc_f_farm_physical_appearance_of_cocoa_seedlings = models.CharField(db_column='GENRL_PPEARNC__F_FARM_PHYSICAL_APPEARANCE_OF_COCOA_SEEDLINGS', max_length=255, blank=True, null=True)  # Field name made lowercase. Field renamed because it contained more than one '_' in a row.
    diseaseand_pest_control_disease_pink_disease = models.CharField(db_column='DISEASEAND_PEST_CONTROL_DISEASE_PINK_DISEASE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    farmer_name = models.CharField(db_column='FARMER_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    staff_id = models.CharField(db_column='STAFF_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    start_raw = models.CharField(db_column='START_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    diseaseand_pest_control_sanitation = models.CharField(db_column='DISEASEAND_PEST_CONTROL_SANITATION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    reporting_date_raw = models.CharField(db_column='REPORTING_DATE_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    meta_instance_id = models.CharField(db_column='META_INSTANCE_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    table = models.CharField(db_column='TABLE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    district = models.CharField(db_column='DISTRICT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    weed_control_measures_close_to_ground_weeding = models.CharField(db_column='WEED_CONTROL_MEASURES_CLOSE_TO_GROUND_WEEDING', max_length=255, blank=True, null=True)  # Field name made lowercase.
    end_raw = models.CharField(db_column='END_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    staff_name = models.CharField(db_column='STAFF_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sol_frtlty_nd_mngment_inorganic_fertilizer_application_granular = models.CharField(db_column='SOL_FRTLTY_ND_MNGMENT_INORGANIC_FERTILIZER_APPLICATION_GRANULAR', max_length=255, blank=True, null=True)  # Field name made lowercase.
    genrl_ppearnc_f_farm_physical_appearance_of_plantain_seedlings = models.CharField(db_column='GENRL_PPEARNC__F_FARM_PHYSICAL_APPEARANCE_OF_PLANTAIN_SEEDLINGS', max_length=255, blank=True, null=True)  # Field name made lowercase. Field renamed because it contained more than one '_' in a row.
    afarinick_farm_inspection_and_management_form = models.CharField(db_column='AFARINICK_FARM_INSPECTION_AND_MANAGEMENT_FORM', max_length=255, blank=True, null=True)  # Field name made lowercase.
    diseaseand_pest_control_pests = models.CharField(db_column='DISEASEAND_PEST_CONTROL_PESTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    region = models.CharField(db_column='REGION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sol_frtlty_nd_mngment_soil_organic_matter = models.CharField(db_column='SOL_FRTLTY_ND_MNGMENT_SOIL_ORGANIC_MATTER', max_length=255, blank=True, null=True)  # Field name made lowercase.
    diseaseand_pest_control_disease_thread_blights = models.CharField(db_column='DISEASEAND_PEST_CONTROL_DISEASE_THREAD_BLIGHTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    refllng_of_sdlings_replacement_of_dead_cocoa_plantain_seedlings = models.CharField(db_column='REFLLNG_OF_SDLINGS_REPLACEMENT_OF_DEAD_COCOA_PLANTAIN_SEEDLINGS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    reporting_date = models.DateTimeField(db_column='REPORTING_DATE', blank=True, null=True)  # Field name made lowercase.
    sol_frtlty_nd_mngment_soil_erosion_management = models.CharField(db_column='SOL_FRTLTY_ND_MNGMENT_SOIL_EROSION_MANAGEMENT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    start = models.DateTimeField(db_column='START', blank=True, null=True)  # Field name made lowercase.
    end = models.DateTimeField(db_column='END', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'FARM_INSPECTION_AND_MANAGEMENT_CORE'




#********************************************** Nursery models ************************************************************************************

class HarvestingAndTransplantingFormCore(models.Model):
    field_uri = models.CharField(db_column='_URI', unique=True, max_length=80,primary_key=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creator_uri_user = models.CharField(db_column='_CREATOR_URI_USER', max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creation_date = models.DateTimeField(db_column='_CREATION_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_uri_user = models.CharField(db_column='_LAST_UPDATE_URI_USER', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_date = models.DateTimeField(db_column='_LAST_UPDATE_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_model_version = models.IntegerField(db_column='_MODEL_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_ui_version = models.IntegerField(db_column='_UI_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_is_complete = models.BooleanField(db_column='_IS_COMPLETE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_submission_date = models.DateTimeField(db_column='_SUBMISSION_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_marked_as_complete_date = models.DateTimeField(db_column='_MARKED_AS_COMPLETE_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    harvesting_box_code = models.CharField(db_column='HARVESTING_BOX_CODE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    transplanting_transplanted_cluster_code = models.CharField(db_column='TRANSPLANTING_TRANSPLANTED_CLUSTER_CODE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    date_of_capturing_raw = models.CharField(db_column='DATE_OF_CAPTURING_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    harvesting_loss_quantity = models.CharField(db_column='HARVESTING_LOSS_QUANTITY', max_length=255, blank=True, null=True)  # Field name made lowercase.
    growing_media = models.CharField(db_column='GROWING_MEDIA', max_length=255, blank=True, null=True)  # Field name made lowercase.
    transplanting_quantityofseedlingscluster = models.CharField(db_column='TRANSPLANTING_QUANTITYOFSEEDLINGSCLUSTER', max_length=255, blank=True, null=True)  # Field name made lowercase.
    meta_instance_id = models.CharField(db_column='META_INSTANCE_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    date_of_capturing = models.DateTimeField(db_column='DATE_OF_CAPTURING', blank=True, null=True)  # Field name made lowercase.
    nursery_name = models.CharField(db_column='NURSERY_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    staff_contact = models.CharField(db_column='STAFF_CONTACT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    note = models.CharField(db_column='NOTE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    harvesting_quantity_harvested = models.CharField(db_column='HARVESTING_QUANTITY_HARVESTED', max_length=255, blank=True, null=True)  # Field name made lowercase.
    staff_name = models.CharField(db_column='STAFF_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'HARVESTING_AND_TRANSPLANTING__FORM_CORE'


class HealthOfSeedlingsFormCore(models.Model):
    field_uri = models.CharField(db_column='_URI', unique=True, max_length=80,primary_key=True)
    field_creator_uri_user = models.CharField(db_column='_CREATOR_URI_USER', max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creation_date = models.DateTimeField(db_column='_CREATION_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_uri_user = models.CharField(db_column='_LAST_UPDATE_URI_USER', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_date = models.DateTimeField(db_column='_LAST_UPDATE_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_model_version = models.IntegerField(db_column='_MODEL_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_ui_version = models.IntegerField(db_column='_UI_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_is_complete = models.BooleanField(db_column='_IS_COMPLETE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_submission_date = models.DateTimeField(db_column='_SUBMISSION_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_marked_as_complete_date = models.DateTimeField(db_column='_MARKED_AS_COMPLETE_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    waterlogging_comments = models.CharField(db_column='WATERLOGGING_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    bag_damage_comments = models.CharField(db_column='BAG_DAMAGE_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    pests_comments = models.CharField(db_column='PESTS_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    water_sucker = models.CharField(db_column='WATER_SUCKER', max_length=255, blank=True, null=True)  # Field name made lowercase.
    extra_comments = models.CharField(db_column='EXTRA_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    date_of_capturing_raw = models.CharField(db_column='DATE_OF_CAPTURING_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    yellowing_comments = models.CharField(db_column='YELLOWING_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    yellowing = models.CharField(db_column='YELLOWING', max_length=255, blank=True, null=True)  # Field name made lowercase.
    meta_instance_id = models.CharField(db_column='META_INSTANCE_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    nursery_name = models.CharField(db_column='NURSERY_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    bag_damage = models.CharField(db_column='BAG_DAMAGE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    no_of_dead_seedlings_cluster = models.IntegerField(db_column='NO_OF_DEAD_SEEDLINGS_CLUSTER', blank=True, null=True)  # Field name made lowercase.
    note = models.CharField(db_column='NOTE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    termite_attack = models.CharField(db_column='TERMITE_ATTACK', max_length=255, blank=True, null=True)  # Field name made lowercase.
    cluster = models.CharField(db_column='CLUSTER', max_length=255, blank=True, null=True)  # Field name made lowercase.
    staff_name = models.CharField(db_column='STAFF_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    no_of_leaves_per_week = models.IntegerField(db_column='NO_OF_LEAVES_PER_WEEK', blank=True, null=True)  # Field name made lowercase.
    segment = models.CharField(db_column='SEGMENT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    browning = models.CharField(db_column='BROWNING', max_length=255, blank=True, null=True)  # Field name made lowercase.
    leaf_wilting_comments = models.CharField(db_column='LEAF_WILTING_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    waterlogging = models.CharField(db_column='WATERLOGGING', max_length=255, blank=True, null=True)  # Field name made lowercase.
    roots_penetrating_bags_comments = models.CharField(db_column='ROOTS_PENETRATING_BAGS_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sector = models.CharField(db_column='SECTOR', max_length=255, blank=True, null=True)  # Field name made lowercase.
    termite_attack_comments = models.CharField(db_column='TERMITE_ATTACK_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    roots_penetrating_bags = models.CharField(db_column='ROOTS_PENETRATING_BAGS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    date_of_capturing = models.DateTimeField(db_column='DATE_OF_CAPTURING', blank=True, null=True)  # Field name made lowercase.
    no_of_roots_penetrating_bags = models.IntegerField(db_column='NO_OF_ROOTS_PENETRATING_BAGS', blank=True, null=True)  # Field name made lowercase.
    leaf_wilting = models.CharField(db_column='LEAF_WILTING', max_length=255, blank=True, null=True)  # Field name made lowercase.
    staff_contact = models.CharField(db_column='STAFF_CONTACT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    all_correct = models.CharField(db_column='ALL_CORRECT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    water_sucker_comments = models.CharField(db_column='WATER_SUCKER_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    pests = models.CharField(db_column='PESTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    browning_comments = models.CharField(db_column='BROWNING_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    viral_attack_comments = models.CharField(db_column='VIRAL_ATTACK_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    viral_attack = models.CharField(db_column='VIRAL_ATTACK', max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'HEALTH_OF_SEEDLINGS_FORM_CORE'


class NurseryActivitiesFormCore(models.Model):
    field_uri = models.CharField(db_column='_URI', unique=True, max_length=80,primary_key=True)
    field_creator_uri_user = models.CharField(db_column='_CREATOR_URI_USER', max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creation_date = models.DateTimeField(db_column='_CREATION_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_uri_user = models.CharField(db_column='_LAST_UPDATE_URI_USER', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_date = models.DateTimeField(db_column='_LAST_UPDATE_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_model_version = models.IntegerField(db_column='_MODEL_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_ui_version = models.IntegerField(db_column='_UI_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_is_complete = models.BooleanField(db_column='_IS_COMPLETE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_submission_date = models.DateTimeField(db_column='_SUBMISSION_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_marked_as_complete_date = models.DateTimeField(db_column='_MARKED_AS_COMPLETE_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    weeding_control_comments = models.CharField(db_column='WEEDING_CONTROL_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    decapitation_comments = models.CharField(db_column='DECAPITATION_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    insecticide_application_comments = models.CharField(db_column='INSECTICIDE_APPLICATION_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    extra_comments = models.CharField(db_column='EXTRA_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    date_of_capturing_raw = models.CharField(db_column='DATE_OF_CAPTURING_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    leaf_cutting = models.CharField(db_column='LEAF_CUTTING', max_length=255, blank=True, null=True)  # Field name made lowercase.
    weeding_control = models.CharField(db_column='WEEDING_CONTROL', max_length=255, blank=True, null=True)  # Field name made lowercase.
    splitting_of_multiple_seedlings_in_bags_comments = models.CharField(db_column='SPLITTING_OF_MULTIPLE_SEEDLINGS_IN_BAGS_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    meta_instance_id = models.CharField(db_column='META_INSTANCE_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    nursery_name = models.CharField(db_column='NURSERY_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    watering_comments = models.CharField(db_column='WATERING_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    note = models.CharField(db_column='NOTE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    fertigation_comments = models.CharField(db_column='FERTIGATION_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    cluster = models.CharField(db_column='CLUSTER', max_length=255, blank=True, null=True)  # Field name made lowercase.
    staff_name = models.CharField(db_column='STAFF_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    decapitation = models.CharField(db_column='DECAPITATION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    leaf_cutting_comments = models.CharField(db_column='LEAF_CUTTING_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    fungicide_application = models.CharField(db_column='FUNGICIDE_APPLICATION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    segment = models.CharField(db_column='SEGMENT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    insecticide_application = models.CharField(db_column='INSECTICIDE_APPLICATION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sector = models.CharField(db_column='SECTOR', max_length=255, blank=True, null=True)  # Field name made lowercase.
    re_arrangement = models.CharField(db_column='RE_ARRANGEMENT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    watering = models.CharField(db_column='WATERING', max_length=255, blank=True, null=True)  # Field name made lowercase.
    splitting_of_multiple_seedlings_in_bags = models.CharField(db_column='SPLITTING_OF_MULTIPLE_SEEDLINGS_IN_BAGS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    date_of_capturing = models.DateTimeField(db_column='DATE_OF_CAPTURING', blank=True, null=True)  # Field name made lowercase.
    staff_contact = models.CharField(db_column='STAFF_CONTACT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    re_arrangement_comments = models.CharField(db_column='RE_ARRANGEMENT_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    mulching = models.CharField(db_column='MULCHING', max_length=255, blank=True, null=True)  # Field name made lowercase.
    fertigation = models.CharField(db_column='FERTIGATION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    fungicide_application_comments = models.CharField(db_column='FUNGICIDE_APPLICATION_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    mulching_comments = models.CharField(db_column='MULCHING_COMMENTS', max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'NURSERY_ACTIVITIES_FORM_CORE'


class PropagationFormCore(models.Model):
    field_uri = models.CharField(db_column='_URI', unique=True, max_length=80,primary_key=True)
    field_creator_uri_user = models.CharField(db_column='_CREATOR_URI_USER', max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creation_date = models.DateTimeField(db_column='_CREATION_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_uri_user = models.CharField(db_column='_LAST_UPDATE_URI_USER', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_date = models.DateTimeField(db_column='_LAST_UPDATE_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_model_version = models.IntegerField(db_column='_MODEL_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_ui_version = models.IntegerField(db_column='_UI_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_is_complete = models.BooleanField(db_column='_IS_COMPLETE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_submission_date = models.DateTimeField(db_column='_SUBMISSION_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_marked_as_complete_date = models.DateTimeField(db_column='_MARKED_AS_COMPLETE_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    truck_number = models.CharField(db_column='TRUCK_NUMBER', max_length=255, blank=True, null=True)  # Field name made lowercase.
    source_location = models.CharField(db_column='SOURCE_LOCATION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    date_of_capturing_raw = models.CharField(db_column='DATE_OF_CAPTURING_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    waybill_quantity = models.IntegerField(db_column='WAYBILL_QUANTITY', blank=True, null=True)  # Field name made lowercase.
    quantity_of_suckers_received = models.IntegerField(db_column='QUANTITY_OF_SUCKERS_RECEIVED', blank=True, null=True)  # Field name made lowercase.
    meta_instance_id = models.CharField(db_column='META_INSTANCE_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    date_of_capturing = models.DateTimeField(db_column='DATE_OF_CAPTURING', blank=True, null=True)  # Field name made lowercase.
    nursery_name = models.CharField(db_column='NURSERY_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    quantity_suckers_pared_quantity_of_bull_head_corms = models.IntegerField(db_column='QUANTITY_SUCKERS_PARED_QUANTITY_OF_BULL_HEAD_CORMS', blank=True, null=True)  # Field name made lowercase.
    corm_buring_quantity_of_corms_buried = models.IntegerField(db_column='CORM_BURING_QUANTITY_OF_CORMS_BURIED', blank=True, null=True)  # Field name made lowercase.
    staff_contact = models.CharField(db_column='STAFF_CONTACT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    note = models.CharField(db_column='NOTE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    quantity_suckers_pared_quantity_of_standard_sized_corms = models.IntegerField(db_column='QUANTITY_SUCKERS_PARED_QUANTITY_OF_STANDARD_SIZED_CORMS', blank=True, null=True)  # Field name made lowercase.
    quantity_suckers_pared_quantity_of_corms_rejected = models.IntegerField(db_column='QUANTITY_SUCKERS_PARED_QUANTITY_OF_CORMS_REJECTED', blank=True, null=True)  # Field name made lowercase.
    quantity_suckers_pared_quantity_of_undersized_corms = models.IntegerField(db_column='QUANTITY_SUCKERS_PARED_QUANTITY_OF_UNDERSIZED_CORMS', blank=True, null=True)  # Field name made lowercase.
    corm_buring_number_of_boxes_generated = models.IntegerField(db_column='CORM_BURING_NUMBER_OF_BOXES_GENERATED', blank=True, null=True)  # Field name made lowercase.
    staff_name = models.CharField(db_column='STAFF_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PROPAGATION_FORM_CORE'





class PropagationFormCormBuringBoxNumbering(models.Model):
    field_uri = models.CharField(db_column='_URI', unique=True, max_length=80,primary_key=True)
    field_creator_uri_user = models.CharField(db_column='_CREATOR_URI_USER', max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creation_date = models.DateTimeField(db_column='_CREATION_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_uri_user = models.CharField(db_column='_LAST_UPDATE_URI_USER', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_date = models.DateTimeField(db_column='_LAST_UPDATE_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_parent_auri = models.CharField(db_column='_PARENT_AURI', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_ordinal_number = models.IntegerField(db_column='_ORDINAL_NUMBER')  # Field name made lowercase. Field renamed because it started with '_'.
    field_top_level_auri = models.CharField(db_column='_TOP_LEVEL_AURI', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    box_num_group_box_code = models.CharField(db_column='BOX_NUM_GROUP_BOX_CODE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    box_num_group_corm_quantity_per_individual_box = models.IntegerField(db_column='BOX_NUM_GROUP_CORM_QUANTITY_PER_INDIVIDUAL_BOX', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PROPAGATION_FORM_CORM_BURING_BOX_NUMBERING'




class FarmValidationFormsCore(models.Model):
    field_uri = models.CharField(primary_key = True, db_column='_URI', unique=True, max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creator_uri_user = models.CharField(db_column='_CREATOR_URI_USER', max_length=80)  # Field name made lowercase. Field renamed because it started with '_'.
    field_creation_date = models.DateTimeField(db_column='_CREATION_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_uri_user = models.CharField(db_column='_LAST_UPDATE_URI_USER', max_length=80, blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_last_update_date = models.DateTimeField(db_column='_LAST_UPDATE_DATE')  # Field name made lowercase. Field renamed because it started with '_'.
    field_model_version = models.IntegerField(db_column='_MODEL_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_ui_version = models.IntegerField(db_column='_UI_VERSION', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_is_complete = models.BooleanField(db_column='_IS_COMPLETE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_submission_date = models.DateTimeField(db_column='_SUBMISSION_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    field_marked_as_complete_date = models.DateTimeField(db_column='_MARKED_AS_COMPLETE_DATE', blank=True, null=True)  # Field name made lowercase. Field renamed because it started with '_'.
    sector_no = models.IntegerField(db_column='SECTOR_NO', blank=True, null=True)  # Field name made lowercase.
    farm_id = models.CharField(db_column='FARM_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    farm_verified_by_ched = models.CharField(db_column='FARM_VERIFIED_BY_CHED', max_length=255, blank=True, null=True)  # Field name made lowercase.
    farmer_contact = models.CharField(db_column='FARMER_CONTACT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    please_kindly_pick_the_farm_geo_point_acc = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_ACC', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
    staff_id = models.CharField(db_column='STAFF_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    start_raw = models.CharField(db_column='START_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    general_remarks = models.CharField(db_column='GENERAL_REMARKS', max_length=255, blank=True, null=True)  # Field name made lowercase.
    reporting_date_raw = models.CharField(db_column='REPORTING_DATE_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    meta_instance_id = models.CharField(db_column='META_INSTANCE_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    district = models.CharField(db_column='DISTRICT', max_length=255, blank=True, null=True)  # Field name made lowercase.
    farms_details_farm_size = models.CharField(db_column='FARMS_DETAILS_FARM_SIZE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    demarcated_to_boundary = models.CharField(db_column='DEMARCATED_TO_BOUNDARY', max_length=255, blank=True, null=True)  # Field name made lowercase.
    end_raw = models.CharField(db_column='END_RAW', max_length=255, blank=True, null=True)  # Field name made lowercase.
    treated_to_boundary = models.CharField(db_column='TREATED_TO_BOUNDARY', max_length=255, blank=True, null=True)  # Field name made lowercase.
    please_kindly_pick_the_farm_geo_point_lng = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_LNG', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
    staff_name = models.CharField(db_column='STAFF_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    undesirable_shade_tree = models.CharField(db_column='UNDESIRABLE_SHADE_TREE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    farms_details_farmer_name = models.CharField(db_column='FARMS_DETAILS_FARMER_NAME', max_length=255, blank=True, null=True)  # Field name made lowercase.
    please_kindly_pick_the_farm_geo_point_alt = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_ALT', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
    maintained_to_boundary = models.CharField(db_column='MAINTAINED_TO_BOUNDARY', max_length=255, blank=True, null=True)  # Field name made lowercase.
    please_kindly_pick_the_farm_geo_point_lat = models.DecimalField(db_column='PLEASE_KINDLY_PICK_THE_FARM_GEO_POINT_LAT', max_digits=38, decimal_places=10, blank=True, null=True)  # Field name made lowercase.
    farms_in_mushy_field = models.CharField(db_column='FARMS_IN_MUSHY_FIELD', max_length=255, blank=True, null=True)  # Field name made lowercase.
    rice_maize_cassava_farm = models.CharField(db_column='RICE_MAIZE_CASSAVA_FARM', max_length=255, blank=True, null=True)  # Field name made lowercase.
    farms_details_location = models.CharField(db_column='FARMS_DETAILS_LOCATION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    afarinick_farm_validation_form = models.CharField(db_column='AFARINICK_FARM_VALIDATION_FORM', max_length=255, blank=True, null=True)  # Field name made lowercase.
    region = models.CharField(db_column='REGION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    reporting_date = models.DateTimeField(db_column='REPORTING_DATE', blank=True, null=True)  # Field name made lowercase.
    start = models.DateTimeField(db_column='START', blank=True, null=True)  # Field name made lowercase.
    end = models.DateTimeField(db_column='END', blank=True, null=True)  # Field name made lowercase.
    established_to_boundary = models.CharField(db_column='ESTABLISHED_TO_BOUNDARY', max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'AFARINICK_FARM_VALIDATION_FORMS_CORE'