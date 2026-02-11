# admin.py - UPDATED VERSION
from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, DateWidget
from django.utils.html import format_html
from django.db import models
from django.forms import TextInput, Textarea, Select
from django.contrib.auth.models import Group
from .models import *

# ============================================
# RESOURCE CLASSES FOR IMPORT-EXPORT
# ============================================

# GIS Models Resources
class FarmsResource(resources.ModelResource):
    class Meta:
        model = Farms
        fields = '__all__'

# Region & District Resources
from import_export import resources, fields
from django.contrib.gis.geos import GEOSGeometry
import re

class RegionResource(resources.ModelResource):
    # Map your CSV columns correctly
    # Your CSV has 'reg_code' not 'reg_code'
    region = fields.Field(attribute='region', column_name='region')
    reg_code = fields.Field(attribute='reg_code', column_name='reg_code')  # Map to your CSV column
    geom = fields.Field(attribute='geom', column_name='geom')
    
    class Meta:
        model = Region
        fields = ('id', 'region', 'reg_code', 'geom')
        # Don't include id in fields since we're not importing it
        # import_id_fields = []  # Don't use import_id_fields
        skip_unchanged = True
        report_skipped = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Don't include id field in the import
        self.fields.pop('id', None)
    
    def before_import(self, dataset, **kwargs):
        """Check dataset structure before import"""
        headers = dataset.headers
        print(f"Dataset headers: {headers}")
        
        # Rename 'reg_code' to 'reg_code' if needed
        if 'reg_code' in headers and 'reg_code' not in headers:
            idx = headers.index('reg_code')
            headers[idx] = 'reg_code'
            dataset.headers = headers
        
        return dataset
    
    def before_import_row(self, row, **kwargs):
        """Process each row before import"""
        try:
            # Debug info
            print(f"Processing row: {dict(row)}")
            
            # Handle the reg_code -> reg_code mapping
            if 'reg_code' in row and 'reg_code' not in row:
                row['reg_code'] = row['reg_code']
            
            # Ensure reg_code exists and is valid
            reg_code = str(row.get('reg_code', '')).strip()
            if not reg_code:
                # Generate from region name
                region_name = str(row.get('region', '')).strip()
                if region_name:
                    if ' ' in region_name:
                        code = ''.join([word[0] for word in region_name.split() if word])
                    else:
                        code = region_name[:2]
                    row['reg_code'] = code.upper()
                else:
                    raise ValueError("Missing both region and reg_code")
            
            # Process geometry - handle empty/invalid WKT
            self._process_geometry(row)
            
            # Remove id field if present - we don't want to import IDs
            if 'id' in row:
                row.pop('id')
            
        except Exception as e:
            print(f"Error processing row: {e}")
            raise ValueError(f"Row processing failed: {e}")
    
    def _process_geometry(self, row):
        """Process geometry data - handle empty/incomplete WKT"""
        if 'geom' not in row:
            return
        
        geom_data = str(row['geom']).strip()
        
        # Handle empty/null geometry
        if not geom_data or geom_data.upper() in ['NULL', 'NONE', '', 'NAN']:
            row['geom'] = None
            return
        
        # Check if it's a valid WKT string
        if self._is_valid_wkt(geom_data):
            try:
                geom = GEOSGeometry(geom_data)
                row['geom'] = geom.wkt
                return
            except Exception as e:
                print(f"Invalid WKT geometry (trying to fix): {e}")
        
        # Try to fix common WKT issues
        fixed_wkt = self._fix_wkt_string(geom_data)
        if fixed_wkt:
            try:
                geom = GEOSGeometry(fixed_wkt)
                row['geom'] = geom.wkt
                return
            except Exception as e:
                print(f"Could not fix WKT: {e}")
        
        # If all else fails, set to None
        print(f"Setting geometry to None for region: {row.get('region')}")
        row['geom'] = None
    
    def _is_valid_wkt(self, wkt_string):
        """Check if string looks like valid WKT"""
        wkt = wkt_string.upper().strip()
        valid_prefixes = ['MULTIPOLYGON', 'POLYGON', 'POINT', 'LINESTRING', 'GEOMETRYCOLLECTION']
        
        for prefix in valid_prefixes:
            if wkt.startswith(prefix + '(') or wkt.startswith(prefix + ' (('):
                # Check basic structure
                if wkt.count('(') == wkt.count(')'):
                    return True
        return False
    
    def _fix_wkt_string(self, wkt_string):
        """Try to fix common WKT issues"""
        wkt = wkt_string.strip()
        
        # Fix 1: Ensure proper parentheses
        open_count = wkt.count('(')
        close_count = wkt.count(')')
        
        if open_count != close_count:
            # Add missing closing parentheses
            wkt += ')' * (open_count - close_count)
        
        # Fix 2: Handle incomplete MULTIPOLYGON/POLYGON
        if wkt.upper().startswith('MULTIPOLYGON') and '(((' not in wkt:
            # Try to convert to POLYGON if MULTIPOLYGON is malformed
            wkt = wkt.replace('MULTIPOLYGON', 'POLYGON', 1)
        
        # Fix 3: Ensure proper coordinate format
        # Remove any non-numeric characters except parentheses, commas, and dots
        lines = wkt.split('(')
        if len(lines) > 1:
            coords_part = lines[-1].rsplit(')', 1)[0]
            # Clean coordinates
            coords_clean = re.sub(r'[^\d\s.,-]', '', coords_part)
            # Reconstruct WKT
            wkt = f"{'('.join(lines[:-1])}({coords_clean}))"
        
        # Fix 4: Check for missing closing
        if not wkt.endswith(')'):
            wkt += ')'
        
        return wkt if self._is_valid_wkt(wkt) else None
    
    def get_or_init_instance(self, instance_loader, row):
        """Handle instance lookup - fix for NoneType error"""
        try:
            # Use reg_code as the lookup field
            if 'reg_code' in row and row['reg_code']:
                reg_code = str(row['reg_code']).strip().upper()
                existing = Region.objects.filter(reg_code=reg_code).first()
                if existing:
                    print(f"Updating existing region: {reg_code}")
                    return existing, False  # Update existing
            
            # Fallback: use region name
            if 'region' in row and row['region']:
                region_name = str(row['region']).strip()
                existing = Region.objects.filter(region=region_name).first()
                if existing:
                    print(f"Updating existing region by name: {region_name}")
                    return existing, False  # Update existing
            
            # Create new instance
            print(f"Creating new region: {row.get('reg_code', 'Unknown')}")
            return Region(), True  # Create new
            
        except Exception as e:
            print(f"Error in get_or_init_instance: {e}")
            # Always return a new instance on error
            return Region(), True
    
    def after_import_instance(self, instance, new, row, **kwargs):
        """Additional processing after instance is created/updated"""
        if new:
            print(f"Successfully created region: {instance.region}")
        else:
            print(f"Successfully updated region: {instance.region}")
    
    # def import_data(self, dataset, dry_run=False, raise_errors=False, **kwargs):
    #     """Override to handle import errors gracefully"""
    #     # First, clean the dataset
    #     cleaned_dataset = self.before_import(dataset, True, dry_run, **kwargs)
        
    #     # Import with error handling
    #     result = super().import_data(
    #         cleaned_dataset,
    #         dry_run=dry_run,
    #         raise_errors=False,  # Collect errors instead of raising immediately
    #         **kwargs
    #     )
        
    #     # Report results
    #     if not dry_run:
    #         print(f"Import completed: {result.totals}")
        
    #     return result


# Alternative: Simple working version if above is too complex
class SimpleRegionResource(resources.ModelResource):
    """Simplified version that should work with your data"""
    
    class Meta:
        model = Region
        fields = ('region', 'reg_code')
        import_id_fields = ['reg_code']
        skip_unchanged = True
    
    def __init__(self):
        super().__init__()
        # Map your CSV columns
        self.fields['reg_code'].column_name = 'reg_code'
    
    def before_import_row(self, row, **kwargs):
        """Simple preprocessing"""
        # Map reg_code to reg_code
        if 'reg_code' in row:
            row['reg_code'] = row['reg_code']
        
        # Ensure reg_code is uppercase
        if 'reg_code' in row and row['reg_code']:
            row['reg_code'] = str(row['reg_code']).strip().upper()
        
        # Skip geometry for now
        if 'geom' in row:
            row.pop('geom')
        
        # Skip id
        if 'id' in row:
            row.pop('id')

class cocoaDistrictResource(resources.ModelResource):
    region = fields.Field(
        column_name='region',
        attribute='region',
        widget=ForeignKeyWidget(Region, 'name')
    )
    
    class Meta:
        model = cocoaDistrict
        fields = ('name', 'district_code', 'region', 'shape_area')

class CommunityResource(resources.ModelResource):
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = Community
        fields = ('name', 'district', 'operational_area')

# Project Resources
class projectTblResource(resources.ModelResource):
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = projectTbl
        fields = ('name', 'district')

class projectStaffTblResource(resources.ModelResource):
    staffTbl_foreignkey = fields.Field(
        column_name='staff',
        attribute='staffTbl_foreignkey',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    
    class Meta:
        model = projectStaffTbl
        fields = ('staffTbl_foreignkey', 'projectTbl_foreignkey')

# Staff Resources
class staffTblResource(resources.ModelResource):
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    
    class Meta:
        model = staffTbl
        fields = ('first_name', 'last_name', 'gender', 'dob', 'contact', 
                 'email_address', 'staffid', 'staffidnum', 'projectTbl_foreignkey')
        import_id_fields = ['contact']

class districtStaffTblResource(resources.ModelResource):
    staffTbl_foreignkey = fields.Field(
        column_name='staff',
        attribute='staffTbl_foreignkey',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    districtTbl_foreignkey = fields.Field(
        column_name='district',
        attribute='districtTbl_foreignkey',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = districtStaffTbl
        fields = ('staffTbl_foreignkey', 'districtTbl_foreignkey')

# Activity Resources
class ActivitiesResource(resources.ModelResource):
    class Meta:
        model = Activities
        fields = ('main_activity', 'sub_activity', 'activity_code', 'required_equipment')

# Farm Resources
class FarmdetailsTblResource(resources.ModelResource):
    region = fields.Field(
        column_name='region',
        attribute='region',
        widget=ForeignKeyWidget(Region, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    community = fields.Field(
        column_name='community',
        attribute='community',
        widget=ForeignKeyWidget(Community, 'name')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    
    class Meta:
        model = FarmdetailsTbl
        fields = ('farm_reference', 'region', 'district', 'farmername', 'location', 
                 'community', 'farm_size', 'projectTbl_foreignkey', 'sector', 'year_of_establishment',
                 'status', 'expunge', 'reason4expunge')
        import_id_fields = ['farm_reference']

# Contractor Resources
class contractorsTblResource(resources.ModelResource):
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = contractorsTbl
        fields = ('contractor_name', 'contact_person', 'address', 'contact_number',
                 'interested_services', 'target', 'district')

class contratorDistrictAssignmentResource(resources.ModelResource):
    contractor = fields.Field(
        column_name='contractor',
        attribute='contractor',
        widget=ForeignKeyWidget(contractorsTbl, 'contractor_name')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = contratorDistrictAssignment
        fields = ('contractor', 'projectTbl_foreignkey', 'district')

# Job Order Resources
class JoborderResource(resources.ModelResource):
    region = fields.Field(
        column_name='region',
        attribute='region',
        widget=ForeignKeyWidget(Region, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    community = fields.Field(
        column_name='community',
        attribute='community',
        widget=ForeignKeyWidget(Community, 'name')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    
    class Meta:
        model = Joborder
        fields = ('farm_reference', 'region', 'district', 'farmername', 'farm_size', 'location',
                 'community', 'projectTbl_foreignkey', 'sector', 'year_of_establishment',
                 'job_order_code')

# API Structure Models Resources
class PersonnelModelResource(resources.ModelResource):
    community = fields.Field(
        column_name='community',
        attribute='community',
        widget=ForeignKeyWidget(Community, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    
    class Meta:
        model = PersonnelModel
        fields = ('first_name', 'surname', 'other_names', 'gender', 'date_of_birth',
                 'primary_phone_number', 'id_type', 'id_number', 'address',
                 'community', 'district', 'projectTbl_foreignkey', 'personnel_type', 'date_joined')

class PersonnelAssignmentModelResource(resources.ModelResource):
    po = fields.Field(
        column_name='po',
        attribute='po',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    ra = fields.Field(
        column_name='ra',
        attribute='ra',
        widget=ForeignKeyWidget(PersonnelModel, 'primary_phone_number')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    community = fields.Field(
        column_name='community',
        attribute='community',
        widget=ForeignKeyWidget(Community, 'name')
    )
    
    class Meta:
        model = PersonnelAssignmentModel
        fields = ('uid', 'po', 'ra', 'projectTbl_foreignkey', 'district', 'community',
                 'date_assigned', 'status')

class DailyReportingModelResource(resources.ModelResource):
    agent = fields.Field(
        column_name='agent',
        attribute='agent',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    main_activity = fields.Field(
        column_name='main_activity',
        attribute='main_activity',
        widget=ForeignKeyWidget(Activities, 'main_activity')
    )
    activity = fields.Field(
        column_name='activity',
        attribute='activity',
        widget=ForeignKeyWidget(Activities, 'sub_activity')
    )
    farm = fields.Field(
        column_name='farm',
        attribute='farm',
        widget=ForeignKeyWidget(FarmdetailsTbl, 'farm_reference')
    )
    community = fields.Field(
        column_name='community',
        attribute='community',
        widget=ForeignKeyWidget(Community, 'name')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = DailyReportingModel
        fields = ('uid', 'agent', 'completion_date', 'reporting_date', 'main_activity',
                 'activity', 'no_rehab_assistants', 'area_covered_ha', 'remark',
                 'status', 'farm', 'farm_ref_number', 'farm_size_ha', 'community',
                 'number_of_people_in_group', 'group_work', 'sector',
                 'projectTbl_foreignkey', 'district')

class GrowthMonitoringModelResource(resources.ModelResource):
    agent = fields.Field(
        column_name='agent',
        attribute='agent',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = GrowthMonitoringModel
        fields = ('uid', 'plant_uid', 'number_of_leaves', 'height', 'stem_size',
                 'leaf_color', 'date', 'lat', 'lng', 'agent', 'projectTbl_foreignkey', 'district')

class OutbreakFarmModelResource(resources.ModelResource):
    community = fields.Field(
        column_name='community',
        attribute='community',
        widget=ForeignKeyWidget(Community, 'name')
    )
    reported_by = fields.Field(
        column_name='reported_by',
        attribute='reported_by',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    region = fields.Field(
        column_name='region',
        attribute='region',
        widget=ForeignKeyWidget(Region, 'name')
    )
    
    class Meta:
        model = OutbreakFarmModel
        fields = ('uid', 'farmer_name', 'farm_location', 'community', 'farm_size',
                 'disease_type', 'date_reported', 'reported_by', 'status',
                 'coordinates', 'projectTbl_foreignkey', 'district', 'region')

class ContractorCertificateModelResource(resources.ModelResource):
    contractor = fields.Field(
        column_name='contractor',
        attribute='contractor',
        widget=ForeignKeyWidget(contractorsTbl, 'contractor_name')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = ContractorCertificateModel
        fields = ('uid', 'contractor', 'work_type', 'start_date', 'end_date',
                 'status', 'remarks', 'projectTbl_foreignkey', 'district')

class ContractorCertificateVerificationModelResource(resources.ModelResource):
    certificate = fields.Field(
        column_name='certificate',
        attribute='certificate',
        widget=ForeignKeyWidget(ContractorCertificateModel, 'uid')
    )
    verified_by = fields.Field(
        column_name='verified_by',
        attribute='verified_by',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = ContractorCertificateVerificationModel
        fields = ('uid', 'certificate', 'verified_by', 'verification_date',
                 'is_verified', 'comments', 'projectTbl_foreignkey', 'district')

class IssueModelResource(resources.ModelResource):
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = IssueModel
        fields = ('uid', 'user', 'issue_type', 'description', 'date_reported',
                 'status', 'projectTbl_foreignkey', 'district')

class IrrigationModelResource(resources.ModelResource):
    farm = fields.Field(
        column_name='farm',
        attribute='farm',
        widget=ForeignKeyWidget(FarmdetailsTbl, 'farm_reference')
    )
    agent = fields.Field(
        column_name='agent',
        attribute='agent',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = IrrigationModel
        fields = ('uid', 'farm', 'farm_id', 'irrigation_type', 'water_volume', 'date',
                 'agent', 'projectTbl_foreignkey', 'district')

class VerifyRecordResource(resources.ModelResource):
    farm = fields.Field(
        column_name='farm',
        attribute='farm',
        widget=ForeignKeyWidget(FarmdetailsTbl, 'farm_reference')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = VerifyRecord
        fields = ('uid', 'farm', 'farmRef', 'timestamp', 'status', 'projectTbl_foreignkey', 'district')

class CalculatedAreaResource(resources.ModelResource):
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    
    class Meta:
        model = CalculatedArea
        fields = ('date', 'title', 'value', 'projectTbl_foreignkey', 'district')

# Payment Models Resources
class PaymentReportResource(resources.ModelResource):
    ra = fields.Field(
        column_name='ra',
        attribute='ra',
        widget=ForeignKeyWidget(PersonnelModel, 'primary_phone_number')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    
    class Meta:
        model = PaymentReport
        fields = ('uid', 'ra', 'ra_name', 'district', 'bank_name', 'bank_branch',
                 'snnit_no', 'salary', 'year', 'po_number', 'month', 'week',
                 'payment_option', 'momo_acc', 'projectTbl_foreignkey')

class DetailedPaymentReportResource(resources.ModelResource):
    ra = fields.Field(
        column_name='ra',
        attribute='ra',
        widget=ForeignKeyWidget(PersonnelModel, 'primary_phone_number')
    )
    po = fields.Field(
        column_name='po',
        attribute='po',
        widget=ForeignKeyWidget(staffTbl, 'contact')
    )
    farm = fields.Field(
        column_name='farm',
        attribute='farm',
        widget=ForeignKeyWidget(FarmdetailsTbl, 'farm_reference')
    )
    activity = fields.Field(
        column_name='activity',
        attribute='activity',
        widget=ForeignKeyWidget(Activities, 'sub_activity')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(cocoaDistrict, 'name')
    )
    projectTbl_foreignkey = fields.Field(
        column_name='project',
        attribute='projectTbl_foreignkey',
        widget=ForeignKeyWidget(projectTbl, 'name')
    )
    
    class Meta:
        model = DetailedPaymentReport
        fields = ('uid', 'group_code', 'ra', 'ra_id', 'ra_name', 'ra_account',
                 'po', 'po_name', 'po_number', 'district', 'projectTbl_foreignkey',
                 'farmhands_type', 'farm', 'farm_reference', 'number_in_a_group',
                 'activity', 'farmsize', 'achievement', 'amount', 'week', 'month',
                 'year', 'issue', 'sector', 'act_code')

# ============================================
# GIS ADMIN CLASSES
# ============================================

class FarmsAdmin(gis_admin.GISModelAdmin):
    resource_class = FarmsResource
    list_display = ('farm_id',)
    search_fields = ('farm_id',)
    list_per_page = 50

# ============================================
# NON-GIS ADMIN CLASSES
# ============================================

from django.contrib.gis.admin import GISModelAdmin

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from leaflet.admin import LeafletGeoAdmin  # Now this will work
from .models import Region
# from .resources import RegionResource

@admin.register(Region)
class RegionAdmin(ImportExportModelAdmin, LeafletGeoAdmin):
    resource_class = RegionResource
    list_display = ('region', 'reg_code', 'created_date')
    search_fields = ('region', 'reg_code')
    list_per_page = 50
    
    # Leaflet settings
    settings_overrides = {
        'DEFAULT_CENTER': (7.9465, -1.0232),
        'DEFAULT_ZOOM': 6,
    }

@admin.register(cocoaDistrict)
class cocoaDistrictAdmin(ImportExportModelAdmin):
    resource_class = cocoaDistrictResource
    list_display = ('name', 'district_code', 'region', 'shape_area', 'created_date')
    list_filter = ('region',)
    search_fields = ('name', 'district_code')
    list_per_page = 50

@admin.register(Community)
class CommunityAdmin(ImportExportModelAdmin):
    resource_class = CommunityResource
    list_display = ('name', 'district', 'operational_area')
    list_filter = ('district',)
    search_fields = ('name', 'operational_area')
    list_per_page = 50

@admin.register(projectTbl)
class projectTblAdmin(ImportExportModelAdmin):
    resource_class = projectTblResource
    list_display = ('name', 'district', 'created_date')
    list_filter = ('district',)
    search_fields = ('name',)
    list_per_page = 50

@admin.register(projectStaffTbl)
class projectStaffTblAdmin(ImportExportModelAdmin):
    resource_class = projectStaffTblResource
    list_display = ('staffTbl_foreignkey', 'projectTbl_foreignkey')
    list_filter = ('projectTbl_foreignkey',)
    search_fields = ('staffTbl_foreignkey__first_name', 'staffTbl_foreignkey__last_name',
                    'projectTbl_foreignkey__name')
    list_per_page = 50

@admin.register(districtStaffTbl)
class districtStaffTblAdmin(ImportExportModelAdmin):
    resource_class = districtStaffTblResource
    list_display = ('staffTbl_foreignkey', 'districtTbl_foreignkey')
    list_filter = ('districtTbl_foreignkey',)
    search_fields = ('staffTbl_foreignkey__first_name', 'staffTbl_foreignkey__last_name',
                    'districtTbl_foreignkey__name')
    list_per_page = 50

@admin.register(staffTbl)
class staffTblAdmin(ImportExportModelAdmin):
    resource_class = staffTblResource
    list_display = ('first_name', 'last_name', 'contact', 'staffid', 'projectTbl_foreignkey','password')
    list_filter = ('gender', 'projectTbl_foreignkey')
    search_fields = ('first_name', 'last_name', 'contact', 'staffid', 'email_address')
    readonly_fields = ('staffid', 'staffidnum', 'uid', 'fbase_code')
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'first_name', 'last_name', 'gender', 'dob', 'contact', 'email_address', 'password')
        }),
        ('Professional Information', {
            'fields': ('projectTbl_foreignkey',)
        }),
        ('System Information', {
            'fields': ('staffid', 'staffidnum', 'uid', 'fbase_code')
        }),
    )
    list_per_page = 50

@admin.register(Activities)
class ActivitiesAdmin(ImportExportModelAdmin):
    resource_class = ActivitiesResource
    list_display = ('main_activity', 'sub_activity', 'activity_code', 'required_equipment')
    list_filter = ('required_equipment', 'main_activity')
    search_fields = ('main_activity', 'sub_activity', 'activity_code')
    list_per_page = 50

@admin.register(FarmdetailsTbl)
class FarmdetailsTblAdmin(ImportExportModelAdmin):
    resource_class = FarmdetailsTblResource
    list_display = ('farm_reference', 'farmername', 'region', 'district', 'community', 'farm_size', 'status', 'projectTbl_foreignkey')
    list_filter = ('status', 'region', 'district', 'sector', 'expunge', 'projectTbl_foreignkey')
    search_fields = ('farm_reference', 'farmername', 'location')
    list_per_page = 50
    actions = ['mark_as_expunged']

    def mark_as_expunged(self, request, queryset):
        queryset.update(expunge=True)
        self.message_user(request, f"{queryset.count()} farms marked as expunged")
    mark_as_expunged.short_description = "Mark selected farms as expunged"

@admin.register(contractorsTbl)
class contractorsTblAdmin(ImportExportModelAdmin):
    resource_class = contractorsTblResource
    list_display = ('contractor_name', 'contact_person', 'district', 'contact_number', 'interested_services')
    list_filter = ('district',)
    search_fields = ('contractor_name', 'contact_person', 'contact_number')
    list_per_page = 50

@admin.register(contratorDistrictAssignment)
class contratorDistrictAssignmentAdmin(ImportExportModelAdmin):
    resource_class = contratorDistrictAssignmentResource
    list_display = ('contractor', 'projectTbl_foreignkey', 'district')
    list_filter = ('projectTbl_foreignkey', 'district')
    search_fields = ('contractor__contractor_name', 'projectTbl_foreignkey__name', 'district__name')
    list_per_page = 50

@admin.register(Joborder)
class JoborderAdmin(ImportExportModelAdmin):
    resource_class = JoborderResource
    list_display = ('farm_reference', 'farmername', 'region', 'district', 'community', 'farm_size', 'sector', 'projectTbl_foreignkey')
    list_filter = ('region', 'district', 'sector', 'projectTbl_foreignkey')
    search_fields = ('farm_reference', 'farmername', 'location')
    readonly_fields = ('job_order_code',)
    list_per_page = 50

@admin.register(versionTbl)
class versionTblAdmin(ImportExportModelAdmin):
    list_display = ('version', 'created_date')
    search_fields = ('version',)
    list_per_page = 50

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('title', 'staffTbl_foreignkey', 'Status', 'sent_date', 'farm_reference')
    list_filter = ('Status', 'sent_date')
    search_fields = ('title', 'feedback', 'farm_reference')
    list_per_page = 50

@admin.register(posRoutemonitoring)
class posRoutemonitoringAdmin(admin.ModelAdmin):
    list_display = ('staffTbl_foreignkey', 'inspection_date', 'lat', 'lng', 'accuracy')
    list_filter = ('inspection_date',)
    search_fields = ('staffTbl_foreignkey__first_name', 'staffTbl_foreignkey__last_name')
    list_per_page = 50

from django.contrib.gis import admin as gis_admin

@admin.register(mappedFarms)
class mappedFarmsAdmin(ImportExportModelAdmin, LeafletGeoAdmin):
    list_display = ('farm_reference', 'farmer_name', 'location', 'farm_area', 'contact')
    search_fields = ('farm_reference', 'farmer_name', 'location')
    list_per_page = 50
    
    # Optional: Customize the map
    default_lon = -1.234
    default_lat = 5.678
    default_zoom = 12

@admin.register(FarmValidation)
class FarmValidationAdmin(admin.ModelAdmin):
    list_display = ('region', 'farm_size', 'farmer_name', 'reporting_date')
    list_filter = ('region', 'reporting_date')
    search_fields = ('farmer_name', 'location')
    list_per_page = 50

# ============================================
# API STRUCTURE MODELS ADMIN
# ============================================

@admin.register(PersonnelModel)
class PersonnelModelAdmin(ImportExportModelAdmin):
    resource_class = PersonnelModelResource
    list_display = ('first_name', 'surname', 'gender', 'district', 'community', 'primary_phone_number', 'personnel_type', 'projectTbl_foreignkey')
    list_filter = ('gender', 'personnel_type', 'district', 'projectTbl_foreignkey')
    search_fields = ('first_name', 'surname', 'id_number', 'primary_phone_number')
    readonly_fields = ('uid',)
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'surname', 'other_names', 'gender', 'date_of_birth',
                      'primary_phone_number', 'secondary_phone_number', 'momo_number')
        }),
        ('Identification', {
            'fields': ('emergency_contact_person', 'emergency_contact_number',
                      'id_type', 'id_number', 'address')
        }),
        ('Location Information', {
            'fields': ('community', 'district')
        }),
        ('Employment Information', {
            'fields': ('projectTbl_foreignkey', 'education_level', 'marital_status',
                      'personnel_type', 'date_joined', 'supervisor_id')
        }),
        ('Banking Information', {
            'fields': ('bank_id', 'account_number', 'branch_id', 'sort_code', 'ezwich_number'),
            'classes': ('collapse',)
        }),
        ('Documentation', {
            'fields': ('image', 'id_image_front', 'id_image_back', 'consent_form_image'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('uid',),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50

@admin.register(PersonnelAssignmentModel)
class PersonnelAssignmentModelAdmin(ImportExportModelAdmin):
    resource_class = PersonnelAssignmentModelResource
    list_display = ('po', 'ra', 'district', 'community', 'date_assigned', 'status', 'projectTbl_foreignkey')
    list_filter = ('status', 'date_assigned', 'district', 'projectTbl_foreignkey')
    search_fields = ('po__first_name', 'po__last_name', 'ra__first_name', 'ra__surname', 'community__name')
    readonly_fields = ('uid',)
    list_per_page = 50

@admin.register(DailyReportingModel)
class DailyReportingModelAdmin(ImportExportModelAdmin):
    resource_class = DailyReportingModelResource
    list_display = ('reporting_date', 'agent', 'district', 'farm_ref_number', 'activity', 'area_covered_ha', 'status')
    list_filter = ('status', 'reporting_date', 'main_activity', 'district', 'projectTbl_foreignkey')
    search_fields = ('agent__first_name', 'agent__last_name', 'farm_ref_number', 'community__name', 'remark')
    readonly_fields = ('uid',)
    list_per_page = 50

@admin.register(GrowthMonitoringModel)
class GrowthMonitoringModelAdmin(ImportExportModelAdmin):
    resource_class = GrowthMonitoringModelResource
    list_display = ('plant_uid', 'date', 'district', 'height', 'number_of_leaves', 'agent', 'projectTbl_foreignkey')
    list_filter = ('date', 'leaf_color', 'district', 'projectTbl_foreignkey')
    search_fields = ('plant_uid', 'agent__first_name', 'agent__last_name')
    readonly_fields = ('uid',)
    list_per_page = 50

@admin.register(OutbreakFarmModel)
class OutbreakFarmModelAdmin(ImportExportModelAdmin):
    resource_class = OutbreakFarmModelResource
    list_display = ('farmer_name', 'district', 'region', 'community', 'farm_size', 'disease_type', 'date_reported', 'status', 'projectTbl_foreignkey')
    list_filter = ('status', 'disease_type', 'date_reported', 'district', 'region', 'projectTbl_foreignkey')
    search_fields = ('farmer_name', 'farm_location', 'community__name')
    readonly_fields = ('uid',)
    list_per_page = 50

@admin.register(ContractorCertificateModel)
class ContractorCertificateModelAdmin(ImportExportModelAdmin):
    resource_class = ContractorCertificateModelResource
    list_display = ('contractor', 'work_type', 'district', 'start_date', 'end_date', 'status', 'projectTbl_foreignkey')
    list_filter = ('status', 'work_type', 'start_date', 'district', 'projectTbl_foreignkey')
    search_fields = ('contractor__contractor_name', 'remarks')
    readonly_fields = ('uid',)
    list_per_page = 50

@admin.register(ContractorCertificateVerificationModel)
class ContractorCertificateVerificationModelAdmin(ImportExportModelAdmin):
    resource_class = ContractorCertificateVerificationModelResource
    list_display = ('certificate', 'district', 'verified_by', 'verification_date', 'is_verified', 'projectTbl_foreignkey')
    list_filter = ('is_verified', 'verification_date', 'district', 'projectTbl_foreignkey')
    search_fields = ('certificate__contractor__contractor_name', 'verified_by__first_name', 'verified_by__last_name', 'comments')
    readonly_fields = ('uid',)
    list_per_page = 50

@admin.register(IssueModel)
class IssueModelAdmin(ImportExportModelAdmin):
    resource_class = IssueModelResource
    list_display = ('user', 'district', 'issue_type', 'date_reported', 'status', 'projectTbl_foreignkey')
    list_filter = ('status', 'issue_type', 'date_reported', 'district', 'projectTbl_foreignkey')
    search_fields = ('user__first_name', 'user__last_name', 'description')
    readonly_fields = ('uid',)
    list_per_page = 50

@admin.register(IrrigationModel)
class IrrigationModelAdmin(ImportExportModelAdmin):
    resource_class = IrrigationModelResource
    list_display = ('farm', 'district', 'irrigation_type', 'water_volume', 'date', 'agent', 'projectTbl_foreignkey')
    list_filter = ('irrigation_type', 'date', 'district', 'projectTbl_foreignkey')
    search_fields = ('farm__farm_reference', 'farm_id', 'agent__first_name', 'agent__last_name')
    readonly_fields = ('uid',)
    list_per_page = 50

@admin.register(VerifyRecord)
class VerifyRecordAdmin(ImportExportModelAdmin):
    resource_class = VerifyRecordResource
    list_display = ('farm', 'district', 'timestamp', 'status', 'projectTbl_foreignkey')
    list_filter = ('status', 'timestamp', 'district', 'projectTbl_foreignkey')
    search_fields = ('farm__farm_reference', 'farmRef')
    readonly_fields = ('uid',)
    list_per_page = 50

@admin.register(CalculatedArea)
class CalculatedAreaAdmin(ImportExportModelAdmin):
    resource_class = CalculatedAreaResource
    list_display = ('title', 'district', 'value', 'date', 'projectTbl_foreignkey')
    list_filter = ('date', 'district', 'projectTbl_foreignkey')
    search_fields = ('title',)
    list_per_page = 50

@admin.register(PaymentReport)
class PaymentReportAdmin(ImportExportModelAdmin):
    resource_class = PaymentReportResource
    list_display = ('ra', 'district', 'month', 'year', 'week', 'salary', 'payment_option', 'projectTbl_foreignkey')
    list_filter = ('month', 'year', 'week', 'district', 'projectTbl_foreignkey')
    search_fields = ('ra__first_name', 'ra__surname', 'ra_name', 'po_number')
    readonly_fields = ('uid',)
    list_per_page = 50

@admin.register(DetailedPaymentReport)
class DetailedPaymentReportAdmin(ImportExportModelAdmin):
    resource_class = DetailedPaymentReportResource
    list_display = ('ra', 'district', 'farm', 'activity', 'month', 'year', 'achievement', 'amount', 'projectTbl_foreignkey')
    list_filter = ('month', 'year', 'district', 'farmhands_type', 'projectTbl_foreignkey')
    search_fields = ('ra__first_name', 'ra__surname', 'ra_name', 'po_name', 'farm_reference')
    readonly_fields = ('uid',)
    list_per_page = 50

# ============================================
# MENU MANAGEMENT ADMIN
# ============================================



# ============================================
# SIMPLE ADMIN CLASSES
# ============================================


# ============================================

admin.site.site_header = "Farm Management System"
admin.site.site_title = "Farm Management System"
admin.site.index_title = "System Administration"

# Register GIS models
admin.site.register(Farms, FarmsAdmin)

# ============================================
# UNREGISTER DEFAULT USER/GROUP IF NEEDED
# ============================================
# If you want to customize the default User/Group admin:
# admin.site.unregister(User)
# admin.site.unregister(Group)