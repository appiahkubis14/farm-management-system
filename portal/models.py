# models.py
import uuid
from django.db import models
from django.contrib.gis.db.models import GeometryField
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.auth import get_user_model 
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User, Group
from datetime import date
from django.contrib.gis.db import models

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.utils.text import slugify 
from django.contrib.gis.geos import GEOSGeometry, Point

from django.utils.html import mark_safe

class protectedValueError(Exception):
    def __init__(self, msg):
        super(protectedValueError, self).__init__(msg)
    
class timeStampManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', True)
        super(timeStampManager, self).__init__(*args, **kwargs)
    
    def get_queryset(self):
        if self.alive_only:
            return timeStampQuerySet(self.model).filter(delete_field="no")
        return timeStampQuerySet(self.model)    
    
    def hard_delete(self):
        return self.get_queryset().hard_delete()

class timeStampQuerySet(models.QuerySet):
    def delete(self):
        for item in self:
            item.delete()
        return super(timeStampQuerySet, self)

    def hard_delete(self):
        return super(timeStampQuerySet, self).delete()
    
    def alive(self):
        return self.filter(delete_field="no")
    
    def dead(self):
        return self.filter(delete_field="yes")

class timeStamp(models.Model):
    """
    Description: This models is an abstract class that defines the columns that should be present in every table.
    """
    created_date = models.DateTimeField(auto_now=True)
    delete_field = models.CharField(max_length=10, default="no")
    objects = timeStampManager()
    default_objects = models.Manager()
    class Meta:
        abstract = True

# ============== REGION & DISTRICT MODELS ==============

class Region(timeStamp):
    """Region model (e.g., Ashanti, Western, etc.)"""
    region = models.CharField(max_length=250, unique=True)
    reg_code = models.CharField(max_length=50, unique=True)
    geom = models.GeometryField(blank=True, null=True)
    
    def __str__(self):
        return self.region

class cocoaDistrict(timeStamp):
    """District model for cocoa-growing districts"""
    geom = models.GeometryField(blank=True, null=True)
    name = models.CharField(max_length=250, unique=True)
    district_code = models.CharField(max_length=50, unique=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, blank=True, null=True)
    shape_area = models.FloatField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Community(timeStamp):
    """Community model"""
    name = models.CharField(max_length=250)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    operational_area = models.CharField(max_length=250, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Communities"

class versionTbl(timeStamp):
    version = models.CharField(max_length=250, blank=True, null=True)

class projectTbl(timeStamp):
    name = models.CharField(max_length=250) 
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return self.name
    

class staffTbl(timeStamp):
    """
    Description: Contains details for Staff, Facilitators and other key personnel
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    gender = models.CharField(max_length=100, choices=[('Male', 'Male'), ('Female', 'Female')])
    dob = models.DateField(max_length=250)
    contact = models.CharField(max_length=250, unique=True)
    email_address = models.EmailField(max_length=250, blank=True)
    uid = models.CharField(max_length=2500, blank=True, null=True)
    fbase_code = models.CharField(max_length=2500, blank=True, null=True)
    staffid = models.CharField(max_length=250, blank=True, null=True, unique=True)
    staffidnum = models.IntegerField(blank=True, null=True, unique=True)
    password = models.CharField(max_length=250, blank=True, null=True,default='P@ssw0rd24')
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    class Meta:
        ordering = ('first_name',)

class districtStaffTbl(timeStamp):
    staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE)
    districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name_plural = "Staff District Assignments"
        unique_together = ['staffTbl_foreignkey', 'districtTbl_foreignkey']

class projectStaffTbl(timeStamp):
    staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)

class Activities(timeStamp):
    main_activity = models.CharField(max_length=500)
    sub_activity = models.TextField(max_length=500, blank=True, null=True)  # Will store comma-separated values
    activity_code = models.CharField(max_length=500)
    required_equipment = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.main_activity} - {self.sub_activity}"
    
    def get_sub_activities_list(self):
        """Convert comma-separated string to list"""
        if self.sub_activity:
            return [s.strip() for s in self.sub_activity.split(',') if s.strip()]
        return []
    
    
    def __str__(self):
        return str(self.sub_activity)
    
    class Meta:
        db_table = 'backend_activities'
    
    class Meta:
        db_table = 'activities'
        verbose_name_plural = "Activities"

class Farms(models.Model):
    geom = models.MultiPolygonField(blank=True, null=True)
    farm_id = models.CharField(max_length=51, blank=True, null=True)

class FarmdetailsTbl(timeStamp):
    STATUS_CHOICES = ( 
        ("Treatment", "Treatment"), 
        ("Establishment", "Establishment"), 
        ("Maintenance", "Maintenance"), 
    )
    
    id = models.AutoField(primary_key=True) 
    farm_foreignkey = models.ForeignKey(Farms, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    farmername = models.CharField(max_length=2500, blank=True, null=True)
    location = models.CharField(max_length=2500, blank=True, null=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, blank=True, null=True)
    farm_reference = models.CharField(max_length=2500, unique=True, blank=True, null=True)
    farm_size = models.FloatField(max_length=2500, blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    sector = models.IntegerField(blank=True, null=True)
    year_of_establishment = models.DateField(max_length=2500, blank=True, null=True)
    expunge = models.BooleanField(default=False, blank=True, null=True)
    reason4expunge = models.CharField(max_length=2500, blank=True, null=True)
    status = models.CharField(default="Maintenance", max_length=2500, blank=True, null=True, choices=STATUS_CHOICES)
    
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        return super(FarmdetailsTbl, self).save()
    
    def __str__(self):
        return self.farm_reference

class contractorsTbl(timeStamp):
    contractor_name = models.CharField(max_length=250)
    contact_person = models.CharField(max_length=250)
    address = models.CharField(max_length=250)
    contact_number = models.CharField(max_length=250)
    interested_services = models.CharField(max_length=250)
    target = models.CharField(max_length=250)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return str(self.contractor_name)

class contratorDistrictAssignment(timeStamp):
    contractor = models.ForeignKey(contractorsTbl, on_delete=models.CASCADE, blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)



class Feedback(timeStamp):
    status = (
        ("Open", "Open"),
        ("In Progress", "In Progress"),
        ("Resolved", "Resolved"),
    )
    staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=2500, blank=True, null=True)
    feedback = models.CharField(max_length=2500, blank=True, null=True)
    sent_date = models.DateTimeField(auto_now=True)
    uid = models.CharField(max_length=2500, blank=True, null=True)
    farm_reference = models.CharField(max_length=2500, blank=True, null=True)
    activity = models.CharField(max_length=2500, blank=True, null=True)
    ra_id = models.CharField(max_length=2500, blank=True, null=True)
    Status = models.CharField(default="Open", max_length=2500, choices=status)
    week = models.CharField(max_length=2500, blank=True, null=True)
    month = models.CharField(max_length=2500, blank=True, null=True)
    year = models.CharField(max_length=2500, blank=True, null=True)

    def __str__(self):
        return str(self.title)

class Sidebar(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        
        return str(self.name)

class GroupSidebar(models.Model):
    assigned_group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    hidden_sidebars = models.ManyToManyField(Sidebar, blank=True)
    
    def __str__(self):
        return str(self.assigned_group)

class mappedFarms(timeStamp):
    farm_reference = models.CharField(max_length=250, blank=True, null=True, unique=True)
    farm_area = models.FloatField(max_length=250, blank=True, null=True)
    farmer_name = models.CharField(max_length=2500, blank=True, null=True)
    location = models.CharField(max_length=2500, blank=True, null=True)
    contact = models.CharField(max_length=2500, blank=True, null=True)
    staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
    farmboundary = models.CharField(max_length=925000)
    geom = GeometryField(blank=True, null=True)
    uid = models.CharField(max_length=2500, blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Farm Mapping Exercise"

class FarmValidation(timeStamp):
    field_uri = models.CharField(primary_key=True, unique=True, max_length=1000)
    field_submission_date = models.DateTimeField(max_length=1000, blank=True, null=True)
    reporting_date = models.CharField(max_length=1000, blank=True, null=True)
    staff_id = models.CharField(max_length=1000, blank=True, null=True)
    staff_name = models.CharField(max_length=1000, blank=True, null=True)
    sector_no = models.IntegerField(blank=True, null=True)
    region = models.CharField(max_length=1000, blank=True, null=True)
    farm = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE, blank=True, null=True)
    farm_size = models.FloatField(max_length=1000, blank=True, null=True)
    farmer_contact = models.CharField(max_length=1000, blank=True, null=True)
    farm_verified_by_ched = models.CharField(max_length=1000, blank=True, null=True)
    demarcated_to_boundary = models.CharField(max_length=1000, blank=True, null=True)
    treated_to_boundary = models.CharField(max_length=1000, blank=True, null=True)
    undesirable_shade_tree = models.CharField(max_length=1000, blank=True, null=True)
    farmer_name = models.CharField(max_length=1000, blank=True, null=True)
    maintained_to_boundary = models.CharField(max_length=1000, blank=True, null=True)
    point_lng = models.CharField(max_length=1000, blank=True, null=True)
    point_lat = models.CharField(max_length=1000, blank=True, null=True)
    point_acc = models.CharField(max_length=1000, blank=True, null=True)
    farms_in_mushy_field = models.CharField(max_length=1000, blank=True, null=True)
    rice_maize_cassava_farm = models.CharField(max_length=1000, blank=True, null=True)
    location = models.CharField(max_length=1000, blank=True, null=True)
    established_to_boundary = models.CharField(max_length=1000, blank=True, null=True)
    general_remarks = models.CharField(max_length=1000, blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Farm Validation Exercise"

class Joborder(timeStamp):
    id = models.AutoField(primary_key=True)
    farm_foreignkey = models.ForeignKey(Farms, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    farmername = models.CharField(max_length=2500, blank=True, null=True)
    location = models.CharField(max_length=2500, blank=True, null=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, blank=True, null=True)
    farm_reference = models.CharField(max_length=2500, unique=True, blank=True, null=True)
    farm_size = models.FloatField(max_length=2500, blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    sector = models.IntegerField(blank=True, null=True)
    year_of_establishment = models.DateField(max_length=2500, blank=True, null=True)
    job_order_code = models.CharField(max_length=4540, blank=True, null=True, unique=True)
    
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.job_order_code = f"{self.region}{self.location}{self.farm_size}{self.farm_reference}{self.farmername}"
        return super(Joborder, self).save()
    
    def __str__(self):
        return self.farm_reference

# ============== API MODELS ==============

class PersonnelModel(timeStamp):
    """Model for Add Personnel module - CmUser/Personnel"""
    first_name = models.CharField(max_length=250)
    surname = models.CharField(max_length=250)
    other_names = models.CharField(max_length=250, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    date_of_birth = models.DateField()
    staff_id = models.CharField(max_length=250, unique=True, blank=True, null=True)
    primary_phone_number = models.CharField(max_length=15)
    secondary_phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=250, blank=True, null=True)  # Add this field
    momo_number = models.CharField(max_length=15, blank=True, null=True)
    momo_name = models.CharField(max_length=250, blank=True, null=True)
    belongs_to_ra = models.CharField(max_length=250, blank=True, null=True)
    emergency_contact_person = models.CharField(max_length=250)
    emergency_contact_number = models.CharField(max_length=15)
    id_type = models.CharField(max_length=50)
    id_number = models.CharField(max_length=50)
    address = models.TextField()
    community = models.ForeignKey(Community, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    education_level = models.CharField(max_length=100)
    marital_status = models.CharField(max_length=50)
    bank_id = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=50, blank=True, null=True)
    bank_branch = models.CharField(max_length=50, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    branch_id = models.CharField(max_length=50, blank=True, null=True)
    SSNIT_number = models.CharField(max_length=50, blank=True, null=True)
    sort_code = models.CharField(max_length=50, blank=True, null=True)
    personnel_type = models.CharField(max_length=50)
    ezwich_number = models.CharField(max_length=50, blank=True, null=True)
    date_joined = models.DateField()
    supervisor_id = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(upload_to='personnel/images/', blank=True, null=True)
    id_image_front = models.ImageField(upload_to='personnel/id_front/', blank=True, null=True)
    id_image_back = models.ImageField(upload_to='personnel/id_back/', blank=True, null=True)
    consent_form_image = models.ImageField(upload_to='personnel/consent/', blank=True, null=True)
    uid = models.CharField(max_length=2500, blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.surname}"
    
    def save(self, *args, **kwargs):
        """Generate staff_id based on personnel_type"""
        # Handle staff_id generation
        if not self.staff_id:  # Only generate if staff_id doesn't exist
            if self.pk is None:
                # New instance - save first to get an ID
                super().save(*args, **kwargs)
                
                # Generate staff_id using the new ID
                if self.personnel_type == "Rehab Assistant":
                    self.staff_id = f"RA-{self.pk:06d}"
                elif self.personnel_type == "Rehab Technician":
                    self.staff_id = f"RT-{self.pk:06d}"
                else:
                    self.staff_id = f"ST-{self.pk:06d}"
                
                # Save again with staff_id - use update_fields to avoid recursion
                kwargs.pop('force_insert', None)  # Remove force_insert if present
                super().save(update_fields=['staff_id'])
            else:
                # Existing instance - just save normally
                super().save(*args, **kwargs)
        else:
            # Staff_id already exists - just save normally
            super().save(*args, **kwargs)


class posRoutemonitoring(timeStamp):
    staffTbl_foreignkey = models.ForeignKey(PersonnelModel, on_delete=models.CASCADE, blank=True, null=True)
    lat = models.FloatField(max_length=2540, blank=True, null=True)
    lng = models.FloatField(max_length=2540, blank=True, null=True)
    accuracy = models.FloatField(max_length=2540, blank=True, null=True)
    inspection_date = models.DateTimeField(max_length=250, blank=True, null=True)
    geom = GeometryField(blank=True, null=True)
    uid = models.CharField(max_length=2500, blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "POs Monitor"
    
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.lat and self.lng:
            try:
                self.geom = Point(float(self.lng), float(self.lat))
            except:
                pass
        return super(posRoutemonitoring, self).save()

# class PoMonitoringModel(timeStamp):
#     lat = models.FloatField(max_length=2540, blank=True, null=True)
#     lng = models.FloatField(max_length=2540, blank=True, null=True)
#     uid = models.CharField(max_length=2500, blank=True, null=True)
#     accuracy = models.FloatField(max_length=2540, blank=True, null=True)
#     inspection_date = models.DateTimeField(max_length=250, blank=True, null=True)
#     po = models.ForeignKey(PersonnelModel, on_delete=models.CASCADE, blank=True, null=True)
#     # geom = GeometryField(blank=True, null=True)
            
class PersonnelAssignmentModel(timeStamp):
    """Model for Assign Rehab Assistant (RA) module"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    po = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True, related_name="po_assignments")
    ra = models.ForeignKey(PersonnelModel, on_delete=models.CASCADE, blank=True, null=True, related_name="ra_assignments")
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, blank=True, null=True)
    date_assigned = models.DateField(blank=True, null=True)
    status = models.IntegerField(default=0)  # 0=Pending, 1=Submitted
    
    def __str__(self):
        return f"{self.po} -> {self.ra}"
    
    class Meta:
        verbose_name = 'Rehab Assistant'
        verbose_name_plural = 'Rehab Assistants'

# class DailyReportingModel(timeStamp):
#     """Model for Daily Reporting and Activity Reporting modules"""
#     uid = models.CharField(max_length=2500, blank=True, null=True)
#     agent = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
#     completion_date = models.DateField(blank=True, null=True)
#     reporting_date = models.DateField(blank=True, null=True)
#     main_activity = models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True, related_name="main_activities")
#     activity = models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True, related_name="sub_activities")
#     no_rehab_assistants = models.IntegerField(default=0, blank=True, null=True)
#     area_covered_ha = models.FloatField(default=0.0, blank=True, null=True)
#     remark = models.TextField(blank=True, null=True)
#     status = models.IntegerField(default=0)  # 0=Pending, 1=Submitted
#     farm = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE, blank=True, null=True)
#     farm_ref_number = models.CharField(max_length=250, blank=True, null=True)
#     farm_size_ha = models.FloatField(default=0.0, blank=True, null=True)
#     community = models.ForeignKey(Community, on_delete=models.CASCADE, blank=True, null=True)
#     number_of_people_in_group = models.IntegerField(default=0, blank=True, null=True)
#     group_work = models.CharField(max_length=50, blank=True, null=True)  # Yes/No
#     sector = models.IntegerField(blank=True, null=True)
#     ras = models.ManyToManyField(PersonnelModel, blank=True)
#     projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
#     district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    
#     def __str__(self):
#         return f"{self.agent} - {self.reporting_date}"
    

# class ActivityReportingModel(timeStamp):
#     """Model for Daily Reporting and Activity Reporting modules"""
#     uid = models.CharField(max_length=2500, blank=True, null=True)
#     agent = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
#     completion_date = models.DateField(blank=True, null=True)
#     reporting_date = models.DateField(blank=True, null=True)
#     main_activity = models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True, related_name="main_activities_reporting")
#     activity = models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True, related_name="sub_activities_reporting")
#     no_rehab_assistants = models.IntegerField(default=0, blank=True, null=True)
#     area_covered_ha = models.FloatField(default=0.0, blank=True, null=True)
#     remark = models.TextField(blank=True, null=True)
#     status = models.IntegerField(default=0)  # 0=Pending, 1=Submitted
#     farm = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE, blank=True, null=True)
#     farm_ref_number = models.CharField(max_length=250, blank=True, null=True)
#     farm_size_ha = models.FloatField(default=0.0, blank=True, null=True)
#     community = models.ForeignKey(Community, on_delete=models.CASCADE, blank=True, null=True)
#     number_of_people_in_group = models.IntegerField(default=0, blank=True, null=True)
#     group_work = models.CharField(max_length=50, blank=True, null=True)  # Yes/No
#     sector = models.IntegerField(blank=True, null=True)
#     ras = models.ManyToManyField(PersonnelModel, blank=True)
#     projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
#     district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    
#     def __str__(self):
#         return f"{self.agent} - {self.reporting_date}"




class DailyReportingModel(timeStamp):
    """Model for Daily Reporting and Activity Reporting modules"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    agent = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)
    reporting_date = models.DateField(blank=True, null=True)
    main_activity = models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True, related_name="main_activities")
    activity = models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True, related_name="sub_activities")
    # Add this field to store selected sub-activities
    sub_activities = models.TextField(blank=True, null=True)  # Will store comma-separated values
    no_rehab_assistants = models.IntegerField(default=0, blank=True, null=True)
    area_covered_ha = models.FloatField(default=0.0, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    status = models.IntegerField(default=0)  # 0=Pending, 1=Submitted
    farm = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE, blank=True, null=True)
    farm_ref_number = models.CharField(max_length=250, blank=True, null=True)
    farm_size_ha = models.FloatField(default=0.0, blank=True, null=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, blank=True, null=True)
    number_of_people_in_group = models.IntegerField(default=0, blank=True, null=True)
    group_work = models.CharField(max_length=50, blank=True, null=True)  # Yes/No
    sector = models.IntegerField(blank=True, null=True)
    ras = models.ManyToManyField(PersonnelModel, blank=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    is_done_by_contractor = models.BooleanField(default=False)
    contractor_name = models.ForeignKey(contractorsTbl, on_delete=models.CASCADE, blank=True, null=True)
    rounds_of_weeding = models.IntegerField(default=0, blank=True, null=True)
    is_done_equally = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.agent} - {self.reporting_date}"
    
    def get_sub_activities_list(self):
        """Convert comma-separated string to list"""
        if self.sub_activities:
            return [s.strip() for s in self.sub_activities.split(',') if s.strip()]
        return []

class ActivityReportingModel(timeStamp):
    """Model for Daily Reporting and Activity Reporting modules"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    agent = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)
    reporting_date = models.DateField(blank=True, null=True)
    main_activity = models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True, related_name="main_activities_reporting")
    activity = models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True, related_name="sub_activities_reporting")
    # Add this field to store selected sub-activities
    sub_activities = models.TextField(blank=True, null=True)  # Will store comma-separated values
    no_rehab_assistants = models.IntegerField(default=0, blank=True, null=True)
    area_covered_ha = models.FloatField(default=0.0, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    status = models.IntegerField(default=0)  # 0=Pending, 1=Submitted
    farm = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE, blank=True, null=True)
    farm_ref_number = models.CharField(max_length=250, blank=True, null=True)
    farm_size_ha = models.FloatField(default=0.0, blank=True, null=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, blank=True, null=True)
    number_of_people_in_group = models.IntegerField(default=0, blank=True, null=True)
    group_work = models.CharField(max_length=50, blank=True, null=True)  # Yes/No
    sector = models.IntegerField(blank=True, null=True)
    ras = models.ManyToManyField(PersonnelModel, blank=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    is_done_by_contractor = models.BooleanField(default=False)
    contractor_name = models.ForeignKey(contractorsTbl, on_delete=models.CASCADE, blank=True, null=True)
    rounds_of_weeding = models.IntegerField(default=0, blank=True, null=True)
    is_done_equally = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.agent} - {self.reporting_date}"
    
    def get_sub_activities_list(self):
        """Convert comma-separated string to list"""
        if self.sub_activities:
            return [s.strip() for s in self.sub_activities.split(',') if s.strip()]
        return []
    
# models.py - Update your QR_CodeModel
import uuid
import random
import string
from django.db import models
from django.utils import timezone
import os

class QR_CodeModel(timeStamp):
    """Model for QR Code module"""
    uid = models.CharField(max_length=2500, blank=True, null=True, db_index=True)
    qr_code = models.ImageField(
        upload_to='qr_codes/', 
        blank=True, 
        null=True,
        help_text='QR code image file'
    )
    
    # Add default_objects manager to bypass soft delete
    default_objects = models.Manager()
    
    def __str__(self):
        return self.uid or f"QR Code {self.id}"
    
    def generate_uid(self):
        """Generate UID in format: ACL-PLT-YEAR-TIME-00001"""
        # This matches the plantation format
        prefix = "ACL"
        plantation = "PLT"
        year = timezone.now().strftime('%Y')
        time_part = timezone.now().strftime('%H%M')
        
        # Get the last QR code with similar pattern
        try:
            last_qr = QR_CodeModel.default_objects.filter(
                uid__startswith=f"{prefix}-{plantation}-{year}-{time_part}"
            ).order_by('-id').first()
        except:
            last_qr = QR_CodeModel.objects.filter(
                uid__startswith=f"{prefix}-{plantation}-{year}-{time_part}"
            ).order_by('-id').first()
        
        if last_qr and last_qr.uid:
            try:
                parts = last_qr.uid.split('-')
                if len(parts) >= 5:
                    last_num = int(parts[4])
                    new_num = last_num + 1
                else:
                    new_num = 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        
        sequential = f"{new_num:05d}"
        uid = f"{prefix}-{plantation}-{year}-{time_part}-{sequential}"
        return uid
    
    def save(self, *args, **kwargs):
        # ONLY generate UID if it's not set - never overwrite
        if not self.uid:
            self.uid = self.generate_uid()
        # Don't convert to uppercase automatically
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete the image file when model is deleted
        if self.qr_code:
            # Check if file exists before deleting
            if hasattr(self.qr_code, 'path') and os.path.isfile(self.qr_code.path):
                os.remove(self.qr_code.path)
        super().delete(*args, **kwargs)


        
class GrowthMonitoringModel(timeStamp):
    """Model for Growth Monitoring module"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    plant_uid = models.CharField(max_length=2500)
    number_of_leaves = models.IntegerField()
    height = models.FloatField()  # in cm
    stem_size = models.FloatField()  # in cm
    leaf_color = models.CharField(max_length=50)
    date = models.DateField()
    lat = models.FloatField()
    lng = models.FloatField()
    qr_code = models.ForeignKey(QR_CodeModel, on_delete=models.CASCADE, blank=True, null=True)
    agent = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"{self.plant_uid} - {self.date}"
    



class OutbreakFarmModel(timeStamp):
    """Model for Outbreak Farm module"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    farmer_name = models.CharField(max_length=250)
    farm_location = models.CharField(max_length=250)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, blank=True, null=True)
    farm_size = models.FloatField()
    disease_type = models.CharField(max_length=250)
    date_reported = models.DateField()
    reported_by = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
    status = models.IntegerField(default=0)  # 0=Pending, 1=Submitted
    coordinates = models.CharField(max_length=100, blank=True, null=True)  # lat,lng
    geom = GeometryField(blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"{self.farmer_name} - {self.disease_type}"

class ContractorCertificateModel(timeStamp):
    """Model for Contractor Certificate module"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    contractor = models.ForeignKey(contractorsTbl, on_delete=models.CASCADE, blank=True, null=True)
    work_type = models.CharField(max_length=250)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=50, default='Pending')
    remarks = models.TextField(blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"{self.contractor} - {self.work_type}"

class ContractorCertificateVerificationModel(timeStamp):
    """Model for Contractor Certificate Verification"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    certificate = models.ForeignKey(ContractorCertificateModel, on_delete=models.CASCADE, blank=True, null=True)
    verified_by = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
    verification_date = models.DateField()
    is_verified = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"{self.certificate} - Verified: {self.is_verified}"

class IssueModel(timeStamp):
    """Model for Submit Issue / Feedback module"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    user = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
    issue_type = models.CharField(max_length=250)
    description = models.TextField()
    date_reported = models.DateField()
    status = models.IntegerField(default=0)  # 0=Pending, 1=Submitted
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user} - {self.issue_type}"

class IrrigationModel(timeStamp):
    """Model for Irrigation module"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    farm = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE, blank=True, null=True, related_name="irrigation_farm")
    # farm_id = models.CharField(max_length=250, blank=True, null=True)
    irrigation_type = models.CharField(max_length=50)  # drip/sprinkler
    water_volume = models.FloatField()  # in liters
    date = models.DateField()
    agent = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"{self.farm} - {self.irrigation_type}"

class VerifyRecord(timeStamp):
    """Model for Verification (Video Record) module"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    farm = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE, blank=True, null=True)
    farmRef = models.CharField(max_length=250, blank=True, null=True)
    videoPath = models.FileField(upload_to='verification/videos/', blank=True, null=True)
    timestamp = models.DateTimeField()
    status = models.IntegerField(default=0)  # 0=Pending, 1=Synced
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"{self.farmRef} - {self.timestamp}"

class CalculatedArea(timeStamp):
    """Model for Area Calculation module"""
    date = models.DateTimeField()
    title = models.CharField(max_length=250)
    value = models.FloatField()  # Area in Hectares
    geom = GeometryField(blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} - {self.value} ha"

# ============== PAYMENT MODELS ==============

class PaymentReport(timeStamp):
    """Model for Payment Report Summary"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    ra = models.ForeignKey(PersonnelModel, on_delete=models.CASCADE, blank=True, null=True)
    ra_name = models.CharField(max_length=250, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    bank_name = models.CharField(max_length=250, blank=True, null=True)
    bank_branch = models.CharField(max_length=250, blank=True, null=True)
    snnit_no = models.CharField(max_length=250, blank=True, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    po_number = models.CharField(max_length=250, blank=True, null=True)
    month = models.CharField(max_length=50, blank=True, null=True)
    week = models.CharField(max_length=50, blank=True, null=True)
    payment_option = models.CharField(max_length=50, blank=True, null=True)
    momo_acc = models.CharField(max_length=50, blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"{self.ra_name} - {self.month} {self.year}"

class DetailedPaymentReport(timeStamp):
    """Model for Detailed Payment Report"""
    uid = models.CharField(max_length=2500, blank=True, null=True)
    group_code = models.CharField(max_length=250, blank=True, null=True)
    ra = models.ForeignKey(PersonnelModel, on_delete=models.CASCADE, blank=True, null=True, related_name="ra_payments")
    # ra_id = models.CharField(max_length=250, blank=True, null=True)
    ra_name = models.CharField(max_length=250, blank=True, null=True)
    ra_account = models.CharField(max_length=250, blank=True, null=True)
    po = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
    po_name = models.CharField(max_length=250, blank=True, null=True)
    po_number = models.CharField(max_length=250, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    farmhands_type = models.CharField(max_length=250, blank=True, null=True)
    farm = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE, blank=True, null=True)
    farm_reference = models.CharField(max_length=250, blank=True, null=True)
    number_in_a_group = models.IntegerField(blank=True, null=True)
    activity = models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
    farmsize = models.FloatField(blank=True, null=True)
    achievement = models.FloatField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    week = models.CharField(max_length=50, blank=True, null=True)
    month = models.CharField(max_length=50, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    issue = models.TextField(blank=True, null=True)
    sector = models.IntegerField(blank=True, null=True)
    act_code = models.CharField(max_length=250, blank=True, null=True)
    
    def __str__(self):
        return f"{self.ra_name} - {self.activity} - {self.month}/{self.year}"

# ============== MENU MANAGEMENT ==============

class MenuItem(models.Model):
    """Recursive menu item model - can have parent MenuItem for hierarchy"""
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    icon = models.CharField(
        max_length=50, 
        help_text="FontAwesome icon class (e.g., 'fas fa-chart-pie')"
    )
    url = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        help_text="URL pattern (e.g., '/dashboard/')"
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
        help_text="Parent menu item (leave blank for top-level menu)"
    )
    
    order = models.PositiveIntegerField(
        default=0, 
        help_text="Display order (lower numbers appear first)"
    )
    is_active = models.BooleanField(default=True)
    
    allowed_groups = models.ManyToManyField(
        Group, 
        related_name='menu_items',
        blank=True,
        help_text="User groups that can access this menu item"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'display_name']
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"
    
    def __str__(self):
        return self.display_name
    
    @property
    def is_top_level(self):
        return self.parent is None
    
    @property
    def has_children(self):
        return self.children.exists()
    
    @property
    def child_count(self):
        return self.children.count()
    
    @property
    def level(self):
        if self.parent is None:
            return 0
        return self.parent.level + 1

class SidebarConfiguration(models.Model):
    """Configuration settings for the sidebar"""
    name = models.CharField(max_length=100, default="Default Configuration")
    is_active = models.BooleanField(default=True)
    show_icons = models.BooleanField(default=True)
    expand_all = models.BooleanField(
        default=False, 
        help_text="Expand all menu items by default"
    )
    show_user_info = models.BooleanField(
        default=True, 
        help_text="Show user info in sidebar"
    )
    show_search = models.BooleanField(
        default=False, 
        help_text="Show search in sidebar"
    )
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('auto', 'Auto (System)')
        ],
        default='light'
    )
    
    class Meta:
        verbose_name = "Sidebar Configuration"
        verbose_name_plural = "Sidebar Configurations"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.is_active:
            SidebarConfiguration.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)








#######################################################################################################################################################################

# ============== EQUIPMENT MANAGEMENT ==============

class EquipmentModel(timeStamp):
    """Model for Equipment Management module"""
    equipment_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    date_of_capturing = models.DateTimeField(auto_now_add=True)
    equipment = models.CharField(max_length=250)
    status = models.CharField(max_length=100, choices=[
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Bad', 'Bad'),
        ('Under Repair', 'Under Repair')
    ], default='Good')
    serial_number = models.CharField(max_length=100, unique=True)
    manufacturer = models.CharField(max_length=250)
    pic_serial_number = models.ImageField(upload_to='equipment/serial/', blank=True, null=True)
    pic_equipment = models.ImageField(upload_to='equipment/device/', blank=True, null=True)
    staff_name = models.ForeignKey(staffTbl, on_delete=models.SET_NULL, blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    uid = models.CharField(max_length=2500, blank=True, null=True)
    
    def __str__(self):
        return f"{self.equipment_code} - {self.equipment}"
    
    def save(self, *args, **kwargs):
        if not self.equipment_code:
            # Generate equipment code (e.g., EQ-2024-0001)
            last_equip = EquipmentModel.objects.order_by('-id').first()
            if last_equip and last_equip.equipment_code:
                try:
                    last_num = int(last_equip.equipment_code.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            self.equipment_code = f"EQ-{timezone.now().year}-{new_num:04d}"
        super().save(*args, **kwargs)

class EquipmentAssignmentModel(timeStamp):
    """Model for Equipment Assignment to staff/projects"""
    equipment = models.ForeignKey(EquipmentModel, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(staffTbl, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(staffTbl, on_delete=models.SET_NULL, null=True, related_name='equipment_assignments')
    assignment_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(blank=True, null=True)
    condition_at_assignment = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='Assigned')  # Assigned, Returned, Lost, Damaged
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    uid = models.CharField(max_length=2500, blank=True, null=True)
    
    def __str__(self):
        return f"{self.equipment} assigned to {self.assigned_to}"

# ============== OUTBREAK FARM MANAGEMENT ==============

class OutbreakFarm(timeStamp):
    """Model for Outbreak Farm module - Enhanced"""
    farm = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE, blank=True, null=True)
    outbreak_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    farm_location = models.CharField(max_length=250)
    farmer_name = models.CharField(max_length=250)
    farmer_age = models.IntegerField(blank=True, null=True)
    id_type = models.CharField(max_length=50, blank=True, null=True)
    id_number = models.CharField(max_length=50, blank=True, null=True)
    farmer_contact = models.CharField(max_length=15, blank=True, null=True)
    cocoa_type = models.CharField(max_length=100, blank=True, null=True)
    age_class = models.CharField(max_length=50, blank=True, null=True)
    farm_area = models.FloatField()
    communitytbl = models.CharField(max_length=250, blank=True, null=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, blank=True, null=True)
    inspection_date = models.DateField()
    temp_code = models.CharField(max_length=100, blank=True, null=True)
    disease_type = models.CharField(max_length=250)
    date_reported = models.DateField()
    reported_by = models.ForeignKey(staffTbl, on_delete=models.CASCADE, blank=True, null=True)
    status = models.IntegerField(default=0)  # 0=Pending, 1=Submitted, 2=Treated, 3=Resolved
    coordinates = models.CharField(max_length=100, blank=True, null=True)
    geom = GeometryField(blank=True, null=True)
    severity = models.CharField(max_length=50, choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical')
    ], default='Medium')
    treatment_applied = models.TextField(blank=True, null=True)
    treatment_date = models.DateField(blank=True, null=True)
    projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE, blank=True, null=True)
    district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, blank=True, null=True)
    uid = models.CharField(max_length=2500, blank=True, null=True)
    
    def __str__(self):
        return f"{self.outbreak_id} - {self.farmer_name} - {self.disease_type}"
    
    def save(self, *args, **kwargs):
        if not self.outbreak_id:
            # Generate outbreak ID (e.g., OB-2024-0001)
            last_outbreak = OutbreakFarm.objects.order_by('-id').first()
            if last_outbreak and last_outbreak.outbreak_id:
                try:
                    last_num = int(last_outbreak.outbreak_id.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            self.outbreak_id = f"OB-{timezone.now().year}-{new_num:04d}"
        super().save(*args, **kwargs)