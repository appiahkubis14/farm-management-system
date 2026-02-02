# # Create your models here.
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
from datetime import date

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.utils.text import slugify 
from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.auth.models import User,Group

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
	
	# def delete(self):
	# 	self.delete_field = "yes"
	# 	for relation in self._meta._relation_tree:
	# 		on_delete = relation.remote_field.on_delete.__name__
	# 		qfilter = {relation.name: self}
	# 		related_queryset = relation.model.objects.filter(**qfilter)
	# 		if on_delete == "CASCADE":
	# 			relation.model.objects.filter(**qfilter).delete()
	# 		elif on_delete == "SET_NULL":
	# 			related_queryset.update(**{relation.name: None})
	# 		elif on_delete == "PROTECT":
	# 			if related_queryset.count() > 0:
	# 				raise protectedValueError("Cannot delete this record because it is referenced in '%s'" %(relation.model.__name__))
	# 	self.save()

	# def hard_delete(self):
	# 	super(timeStamp, self).delete()



# class userTbl(timeStamp):
# 	"""
# 	Description: Model Description
# 	"""
# 	user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
# 	user_accept_email = models.CharField(max_length=3, default='yes')
# 	user_contact = models.CharField(max_length=10, blank=True, null=True )
# 	assigned_group = models.CharField(max_length=3, default="no")

# 	class Meta:
# 		pass

# First, create Region as a regular model (not managed=False)
# class Region(models.Model):
#     geom = GeometryField(blank=True, null=True)
#     region = models.CharField(max_length=50, blank=True, null=True)
#     reg_code = models.CharField(primary_key=True, max_length=10)

#     class Meta:
#         managed = True  # Changed from False to True
#         db_table = 'region'

#     def __str__(self):
#         return str(self.region)

class DistrictOffices(models.Model):
    geom = GeometryField(blank=True, null=True)
    town_name = models.CharField(max_length=40, blank=True, null=True)


class MajorRoads(models.Model):
	geom = models.GeometryField(blank=True, null=True)
	length = models.FloatField(blank=True, null=True)
	wr_roads_field = models.FloatField(db_column='wr_roads_', blank=True, null=True)  # Field renamed because it ended with '_'.
	wr_roads_i = models.FloatField(blank=True, null=True)
	segment = models.CharField(max_length=60, blank=True, null=True)
	reg_code = models.CharField(max_length=2, blank=True, null=True)
	dist_code = models.CharField(max_length=5, blank=True, null=True)
	surface_co = models.IntegerField(blank=True, null=True)
	road_num = models.CharField(max_length=8, blank=True, null=True)
	length_km_field = models.FloatField(db_column='length_km_', blank=True, null=True)  # Field renamed because it ended with '_'.
	class_code = models.IntegerField(blank=True, null=True)






class cocoaDistrict(models.Model):
	geom = models.GeometryField(blank=True, null=True)
	district = models.CharField(max_length=50, blank=True, null=True)
	# reg_code = models.ForeignKey('Region', models.DO_NOTHING, blank=True, null=True)
	shape_area = models.FloatField(blank=True, null=True)
	district_code = models.CharField(max_length=50, blank=True, null=True)

	def __str__(self):
		return str(self.district)






# class district_code(models.Model):
# 	district_code = models.CharField(max_length=50, blank=True, null=True)
# 	district = models.CharField(max_length=50, blank=True, null=True)
# 	reg_code = models.ForeignKey('Region', models.DO_NOTHING, blank=True, null=True)
	
# # class Region(models.Model):

# # 	geom = models.GeometryField(blank=True, null=True , srid=32630)
# # 	region = models.CharField(max_length=50, blank=True, null=True)
# # 	reg_code = models.CharField(primary_key=True, max_length=20)
# # 	pilot = models.BooleanField()

# # 	class Meta:
# # 		managed = True
# # 		db_table = 'region'

# # 	def __str__(self):
# # 		return self.region



# class District(models.Model):
# 	geom = models.GeometryField(blank=True, null=True, srid=32630)
# 	region = models.CharField(max_length=50, blank=True, null=True)
# 	district = models.CharField(max_length=50, blank=True, null=True)
# 	district_code = models.CharField(max_length=254, blank=True, null=True)
# 	reg_code =models.ForeignKey(Region, on_delete=models.CASCADE) 
# 	pilot = models.BooleanField()

# 	class Meta:
# 		managed = True
# 		db_table = 'district'
# 	def __str__(self):
# 		return str(self.district)


# # class cocoaDistrict(models.Model):
# # 	# geom = models.GeometryField(blank=True, null=True, srid=32630)
# # 	region = models.CharField(max_length=50, blank=True, null=True)
# # 	district = models.CharField(max_length=50, blank=True, null=True)
# # 	reg_code =models.ForeignKey(Region, on_delete=models.CASCADE, blank=True, null=True) 


# # 	def __str__(self):
# # 		return self.district




class groupTbl(timeStamp):
	# choices=(
	# 		("Regional Manager", "Regional Manager"),
	# 		("Monitoring and Evaluation", "Monitoring and Evaluation"),
	# 		("Project Officer", "Project Officer"),
	# 		("District Officer", "District Officer"),
	# 		("Project Coordinator", "Project Coordinator"),
	# 		("Project Manager", "Project Manager"),
	# 		("National", "National"),

	# 	)
	name = models.CharField(max_length=250)

	def __str__(self):
		return self.name





class staffTbl(timeStamp):
	"""
	Description: Contains details for Staff, Facilitators and other key personnel
	"""

	STATUS_CHOICES = ( 
    ("farm_services", "Farm Services"), 
	("nursery", "Nursery"),  

	) 

	Nursery_CHOICES = ( 
	("Dadieso", "Dadieso"), 
	("Nobekaw", "Nobekaw"), 
	("Akontombra", "Akontombra"), 
	("Dodi Papase", "Dodi Papase"), 
	("Manso Amenfi", "Manso Amenfi"), 
	("Koforidua", "Koforidua"), 

	)

	user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
	first_name = models.CharField(max_length=250)
	last_name = models.CharField(max_length=250)
	gender = models.CharField(max_length=250)
	dob = models.DateField(max_length=250)
	contact = models.CharField(max_length=250,unique=True)
	designation = models.ForeignKey(groupTbl, on_delete=models.CASCADE)
	email_address = models.EmailField(max_length=250, blank=True)
	uid= models.CharField(max_length=2500,blank=True, null=True)
	fbase_code= models.CharField(max_length=2500,blank=True, null=True)
	district = models.CharField(max_length=250, blank=True, null=True)

	staff_station = models.CharField(max_length=250,default="farm_services",choices=STATUS_CHOICES)

	nursery = models.CharField(max_length=250,default="",blank=True, null=True,choices=Nursery_CHOICES)

	staffid = models.CharField(max_length=250, blank=True, null=True,unique=True)
	staffidnum = models.IntegerField(blank=True, null=True,unique=True)

	crmpassword = models.CharField(max_length=250,default="P@ssw0rd24")
	# staffid = models.CharField(max_length=250, blank=True, null=True,unique=True)

	# def save(self, force_insert=False, force_update=False, using=None, update_fields=None):

	# 	staff=staffTbl.objects.filter(designation=3,staffid__startswith="P").latest("staffidnum").staffidnum + 1 
	# 	num="{0:0>4}".format(staff)
	# 	staff = f"P{num}"
	# 	self.staffid = staff
	
	# 	return super(staffTbl, self).save()
	def __str__(self):
		return f'{self.first_name} {self.last_name}'


	class Meta:
		ordering = ('first_name',)
# @receiver(pre_save, sender=staffTbl)
# def create_slug(sender, instance, *args, **kwargs):


# 	if instance :
# 		print(staffTbl.objects.all().count())
# 		staff=staffTbl.objects.get(contact=instance.contact)
# 		district = District.objects.get(district=instance.district)
# 		dist_obj,created = districtStaffTbl.objects.get_or_create(staffTbl_foreignkey=staff ,deafault=dict(districtTbl_foreignkey=district,staffTbl_foreignkey=staff))
	
	# def save(self, *args, **kwargs):
	# 	if not self.pk:
	# 		staff=staffTbl.objects.get(contact=self.contact)
	# 	super().save(*args, **kwargs)
			# Category.objects.filter(pk=self.category_id).update(hero_count=F('hero_count')+1)
			# staff=staffTbl.objects.get(contact=self.contact)
			# district = District.objects.get(district=self.district)
			# dist_obj,created = districtStaffTbl.objects.get_or_create(districtTbl_foreignkey=district,staffTbl_foreignkey=)
		# super().save(*args, **kwargs)

	# /@receiver(post_save)
	# def pre_save_receiver(sender, instance, *args, **kwargs):
	# def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
	# 	if self.district :
	# 		print(staffTbl.objects.filter(contact=self.contact).count())
			# staff=staffTbl.objects.get(contact=self.contact)
			# district = District.objects.get(district=self.district)
			# dist_obj,created = districtStaffTbl.objects.get_or_create(districtTbl_foreignkey=district,staffTbl_foreignkey=)
	# 	return super(FarmdetailsTbl, self).save()





class regionStaffTbl(timeStamp):
	# regionTbl_foreignkey = models.ForeignKey(Region, on_delete=models.CASCADE)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE)
	class Meta:
		verbose_name_plural = "Staff Region Assignments"
	

class districtStaffTbl(timeStamp):
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE)

	class Meta:
		verbose_name_plural = "Staff District Assignments"
		


class usergroupTbl(timeStamp):
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE)
	group_location = models.CharField(max_length=100, blank=True, null=True, default='national')

# 	class Meta:
# 		unique_together = ['userTbl_foreignkey', 'groupTbl_foreignkey']


class Activities(models.Model):
	main_activity = models.CharField(max_length=500)
	sub_activity = models.CharField(max_length=500)
	activity_code= models.CharField(max_length=500)
	required_equipment = models.BooleanField(default=False)

	def __str__(self):
		return str(self.sub_activity)




class Farms(models.Model):
    geom = models.MultiPolygonField(blank=True, null=True)
    farm_id = models.CharField(max_length=51, blank=True, null=True)

  

# class Farms(models.Model):
#     geom = models.MultiPolygonField(blank=True, null=True)
#     farm_id = models.CharField(max_length=50, blank=True, null=True)
#     farm_loc = models.CharField(max_length=50, blank=True, null=True)
#     farmer_nam = models.CharField(max_length=50, blank=True, null=True)
#     sex = models.CharField(max_length=50, blank=True, null=True)
#     age = models.CharField(max_length=50, blank=True, null=True)
#     id_number = models.CharField(max_length=50, blank=True, null=True)
#     name_ta = models.CharField(max_length=50, blank=True, null=True)
#     area_ha = models.FloatField(blank=True, null=True)
#     region = models.CharField(max_length=254, blank=True, null=True)
#     district = models.CharField(max_length=254, blank=True, null=True)
#     farm_size = models.CharField(max_length=254, blank=True, null=True)
#     main_activity = models.CharField(max_length=254, blank=True, null=True)
#     lng = models.CharField(max_length=254, blank=True, null=True)
#     lat = models.CharField(max_length=254, blank=True, null=True)
#     date = models.DateField(blank=True, null=True)
#     sub_activity = models.CharField(max_length=254, blank=True, null=True)

#     class Meta:
#         managed = False
#         db_table = 'farmss'

class projectTbl(timeStamp):
	name= models.CharField(max_length=250) 

	def __str__(self):
		return self.name


class projectStaffTbl(timeStamp):
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE)
	projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE,blank=True, null=True)
	



class rehabassistantsTbl(timeStamp):
	new_staff_code	= models.CharField(max_length=250,blank=True, null=True,unique=True)
	computcode	= models.IntegerField(blank=True, null=True)
	staff_code	= models.CharField(max_length=250,blank=True, null=True,unique=True)
	designation	= models.CharField(max_length=250,blank=True, null=True,default="Rehab Assistant")
	name	= models.CharField(max_length=250,blank=True, null=True)
	photo_staff = models.ImageField(upload_to="staff" ,blank=True, null=True)	
	phone_number= models.CharField(max_length=250,blank=True, null=True)	
	salary_bank_name = models.CharField(max_length=250, blank=True, null=True)			
	bank_branch = models.CharField(max_length=250, blank=True, null=True)	
	bank_account_number	= models.CharField(max_length=250, blank=True, null=True)
	id_type	= models.CharField(max_length=250, blank=True, null=True)
	id_number	= models.CharField(max_length=250, blank=True, null=True)
	gender= models.CharField(max_length=250, blank=True, null=True)
	ssnit_number = models.CharField(max_length=250,blank=True, null=True)	
	district = models.CharField(max_length=250,blank=True, null=True)
	region = models.CharField(max_length=250,blank=True, null=True)
	projectTbl_foreignkey = models.ForeignKey(projectTbl,on_delete=models.CASCADE,blank=True, null=True	)
	dob = models.DateField(max_length=250,blank=True, null=True)
	owner_momo = models.CharField(max_length=250,blank=True, null=True)
	momo_account_name = models.CharField(max_length=250,blank=True, null=True)
	momo_number = models.CharField(max_length=250,blank=True, null=True)
	payment_option = models.CharField(max_length=250,blank=True, null=True)
	po = models.CharField(max_length=250,blank=True, null=True)
	po_number = models.CharField(max_length=250,blank=True, null=True)
	passportpic = models.CharField(max_length=2500,blank=True, null=True)
	uid= models.CharField(max_length=2500,blank=True, null=True)
	sigcode= models.CharField(max_length=2500,blank=True, null=True)
	kobocode= models.CharField(max_length=2500,blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True,verbose_name="Project Officer")
	code=models.CharField(max_length=3540, blank=True, null=True,unique=True)
	comments = models.CharField(max_length=2500,blank=True, null=True)


	def __str__(self):
		return self.name
	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):

		code = f"{self.name}{self.phone_number}{self.designation}{self.salary_bank_name}{self.bank_branch}{self.bank_account_number}{self.ssnit_number}{self.district}{self.region}{self.dob}" 

		self.code = code
		if self.district :
			district = cocoaDistrict.objects.get(district__iexact=self.district)
			self.districtTbl_foreignkey = district

		if self.staff_code:
			self.computcode= self.staff_code[10:]
			
		dist = cocoaDistrict.objects.get(id=self.districtTbl_foreignkey.id)

		self.district=dist.district
		self.region=dist.reg_code


		# if not self.designation == "Rehab Assistant":
		# 	initcode=f"RT/{dist.reg_code.reg_code}/{dist.district_code}"
		# 	if rehabassistantsTbl.objects.filter(staff_code__startswith= initcode).exists():
		# 		staff = rehabassistantsTbl.objects.filter(staff_code__startswith= initcode).latest("staff_code").staff_code.split("/")[-1]
		# 	else:
		# 		staff = 0

		# 	staff = int(staff) + 1
				
		# 	num="{0:0>3}".format(staff)
		# 	racode = f"RT/{dist.reg_code.reg_code}/{dist.district_code}/{num}"
		# else:

		# 	initcode=f"RA/{dist.reg_code.reg_code}/{dist.district_code}"
		# 	if rehabassistantsTbl.objects.filter(staff_code__startswith= initcode).exists():
		# 		staff = rehabassistantsTbl.objects.filter(staff_code__startswith= initcode).latest("staff_code").staff_code.split("/")[-1]
		# 	else:
		# 		staff = 0

		# 	staff = int(staff) + 1
		# 	num="{0:0>3}".format(staff)

		# 	racode = f"RA/{dist.reg_code.reg_code}/{dist.district_code}/{num}"

		# self.staff_code = racode
		return super(rehabassistantsTbl, self).save()




class FarmdetailsTbl(timeStamp):
	STATUS_CHOICES = ( 
	("Treatment", "Treatment"), 
	("Establishment", "Establishment"), 
	("Maintenance", "Maintenance"), 
	)

	id = models.AutoField(primary_key=True) 
	farm_foreignkey = models.ForeignKey(Farms, on_delete=models.CASCADE,blank=True, null=True)
	region= models.CharField(max_length=2500,blank=True, null=True)
	district= models.CharField(max_length=2500,blank=True, null=True)
	farmername= models.CharField(max_length=2500,blank=True, null=True)
	location= models.CharField(max_length=2500,blank=True, null=True)
	farm_reference= models.CharField(max_length=2500,unique=True,blank=True, null=True)
	farm_size= models.FloatField(max_length=2500, blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	sector= models.IntegerField(blank=True, null=True)
	year_of_establishment= models.DateField(max_length=2500,blank=True, null=True)
	expunge= models.BooleanField(default=False,blank=True, null=True)
	reason4expunge= models.CharField(max_length=2500,blank=True, null=True)
	status= models.CharField(default="Maintenance" ,max_length=2500,blank=True, null=True,choices=STATUS_CHOICES)



	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		self.job_order = f"{self.region}{self.district}{self.location}{self.farm_size}{self.farm_reference}{self.farmername}"
		
		if cocoaDistrict.objects.filter(district__iexact=self.district).exists():
			district = cocoaDistrict.objects.get(district__iexact=self.district)
		# FarmdetailsTbl.objects.filter(id = self.id ).update(districtTbl_foreignkey=district)
			self.districtTbl_foreignkey =  district
		return super(FarmdetailsTbl, self).save()

	def __str__(self):
		return self.farm_reference
	

class rehabassistantsAssignmentTbl(timeStamp):
	farmTbl_foreignkey = models.ForeignKey(Farms, on_delete=models.CASCADE)
	rehabassistantsTbl_foreignkey = models.ForeignKey(rehabassistantsTbl, on_delete=models.CASCADE)
	activity = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
	assigned_date= models.DateField(max_length=250, blank=True, null=True)
	uid= models.CharField(max_length=2500,blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)


class weeklyMontoringTbl(timeStamp):
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	farmTbl_foreignkey = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE,blank=True, null=True)
	activity = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
	monitoring_date= models.DateField(max_length=250)
	no_rehab_assistants =  models.IntegerField(default=0, blank=True, null=True)
	no_rehab_technicians =  models.IntegerField(default=0, blank=True, null=True)
	original_farm_size = models.FloatField(default=0, blank=True, null=True)
	area_covered_ha =  models.FloatField(default=0, blank=True, null=True)
	remark = models.CharField(max_length=2540, blank=True, null=True)
	status = models.CharField(max_length=2540, blank=True, null=True)
	lat= models.FloatField(default=0,blank=True, null=True	)
	lng= models.FloatField(default=0,blank=True, null=True	)
	accuracy= models.FloatField(default=0,blank=True, null=True)
	geom = models.GeometryField(blank=True, null=True, srid=32630)
	current_farm_pic =models.ImageField(upload_to=f"weeklymonitoring/{date.today().strftime('%Y-%m-%d')}" ,blank=True, null=True)
	name_ra_rt = models.CharField(max_length=2540, blank=True, null=True)
	contractor = models.CharField(max_length=2540, blank=True, null=True)
	uid= models.CharField(max_length=2500,blank=True, null=True)
	date_purchased = models.DateField(max_length=254, blank=True, null=True)
	date = models.DateField(max_length=254, blank=True, null=True)	
	qty_purchased= models.FloatField(default=0,blank=True, null=True	)
	name_operator_receiving= models.CharField(max_length=254, blank=True, null=True)
	quantity_ltr= models.FloatField(default=0,blank=True, null=True	)
	red_oil_ltr	= models.FloatField(default=0,blank=True, null=True	)
	engine_oil_ltr	= models.FloatField(default=0,blank=True, null=True	)
	rate	= models.FloatField(default=0,blank=True, null=True	)
	remarks = models.CharField(max_length=654, blank=True, null=True)
	farm_ref_number=models.CharField(max_length=2540, blank=True, null=True)
	community=	models.CharField(max_length=2540, blank=True, null=True)
	Operational_area=models.CharField(max_length=2540, blank=True, null=True)
	main_activity=models.CharField(max_length=2540, blank=True, null=True)
	sub_activity=models.CharField(max_length=2540, blank=True, null=True)
	district=models.CharField(max_length=2540, blank=True, null=True)
	name_ras=models.CharField(max_length=2540, blank=True, null=True)
	name_po=models.CharField(max_length=2540, blank=True, null=True)
	po_id=models.CharField(max_length=2540, blank=True, null=True)
	quantity_plantain_suckers=models.FloatField(max_length=2540, blank=True, null=True)
	quantity_plantain_seedling=models.FloatField(max_length=2540, blank=True, null=True)
	quantity_cocoa_seedling=models.FloatField(max_length=2540, blank=True, null=True)
	quantity=models.FloatField(max_length=2540, blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
	code=models.CharField(max_length=3540, blank=True, null=True,unique=True)
	weeddingcycle=models.IntegerField(default=1,null=True)
	class Meta:
		verbose_name_plural = "Weekly Maintenance Report"

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		
		if self.district :
			print(self.district)
			district = cocoaDistrict.objects.get(district=self.district)
			self.districtTbl_foreignkey = district
		if self.main_activity  and self.sub_activity:
			act = Activities.objects.get(main_activity__iexact=self.main_activity,sub_activity__iexact=self.sub_activity)
			self.activity = act

		code = f"{self.staffTbl_foreignkey}{self.farmTbl_foreignkey}{self.farm_ref_number}{self.activity}{self.monitoring_date}{self.no_rehab_assistants}{self.original_farm_size}{self.area_covered_ha}{self.remark}{self.status}{self.lat}{self.lng}{self.accuracy}{self.uid}{self.date_purchased}{self.date}{self.qty_purchased}" 

		self.code = code
		
		if FarmdetailsTbl.objects.filter(farm_reference=self.farmTbl_foreignkey).exists():
			farmfk = FarmdetailsTbl.objects.get(farm_reference=self.farmTbl_foreignkey)
			self.community=farmfk.location
			currentstatusFarmTbl.objects.update_or_create(
				year=str(self.monitoring_date)[:4],
				activity=self.activity,
				farmTbl_foreignkey=farmfk,
				defaults=dict(farmTbl_foreignkey=farmfk,activity=self.activity,year=str(self.monitoring_date)[:4],status=self.status,monitoring_date=self.monitoring_date )
				)

		return super(weeklyMontoringTbl, self).save()
	


class currentstatusFarmTbl(timeStamp):
	farmTbl_foreignkey = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE,blank=True, null=True)
	activity = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
	monitoring_date= models.DateField(max_length=250, blank=True, null=True)
	status = models.CharField(max_length=2540, blank=True, null=True)
	year = models.CharField(max_length=2540, blank=True, null=True)
	









# 	main_activity=models.CharField(max_length=2540, blank=True, null=True)
# 	sub_activity=models.CharField(max_length=2540, blank=True, null=True)	
# 	machine_brand=models.CharField(max_length=2540, blank=True, null=True)
# 	machine_serial_id=models.CharField(max_length=2540, blank=True, null=True)	
# 	fuel=models.FloatField(max_length=2540, blank=True, null=True)	
# 	oil=models.FloatField(max_length=2540, blank=True, null=True)
# 	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE)

	# def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
	# 	if self.district :
	# 		print(self.district)
	# 		district = cocoaDistrict.objects.get(district=self.district)
	# 		self.districtTbl_foreignkey = district
	# 	if self.main_activity  and self.sub_activity:
	# 		act = Activities.objects.get(main_activity=self.main_activity,sub_activity=self.sub_activity)
	# 		self.activity = act
	# 	return super(weeklymonthtestTbl, self).save()





class weeklyMontoringrehabassistTbl(timeStamp):
	weeklyMontoringTbl_foreignkey = models.ForeignKey(weeklyMontoringTbl, on_delete=models.CASCADE)
	rehabassistantsTbl_foreignkey = models.ForeignKey(rehabassistantsTbl, on_delete=models.CASCADE, blank=True, null=True)
	rehabassistants = models.CharField(max_length=254, blank=True, null=True)
	area_covered_ha =  models.FloatField(default=0, blank=True, null=True)


class fuelMontoringTbl(timeStamp):	
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)	
	farmdetailstbl_foreignkey = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE, blank=True, null=True)
	date_received = models.DateField(max_length=254, blank=True, null=True)
	rehabassistantsTbl_foreignkey = models.ForeignKey(rehabassistantsTbl, on_delete=models.CASCADE, blank=True, null=True)
	fuel_ltr	= models.FloatField(default=0,blank=True, null=True	)
	remarks = models.CharField(max_length=654, blank=True, null=True)
	uid = models.CharField(max_length=654, blank=True, null=True)





class odkUrlModel(timeStamp):
	form_name = models.CharField(max_length=150, blank=True, null=True)
	urlname = models.CharField(max_length=1500, blank=True, null=True, default='')
	csvname = models.CharField(max_length=150, blank=True, null=True, default='')
	csvtype = models.CharField(max_length=150, blank=True, null=True, default='generic')

	def __str__(self):
		 return "Form Name: %s | csvname: %s" %(self.form_name, self.csvname)



# class testTbl(timeStamp):	
# 	remarks = models.CharField(max_length=654, blank=True, null=True)
# 	image = models.ImageField(upload_to="account_details" ,blank=True, null=True)	



# class outBreaks(models.Model):
#     geom = models.GeometryField(blank=True, null=True)
#     objectid_1 = models.BigIntegerField(blank=True, null=True)
#     objectid = models.BigIntegerField(blank=True, null=True)
#     ob_id = models.CharField(max_length=50, blank=True, null=True)
#     ob_size = models.CharField(max_length=50, blank=True, null=True)
#     est_trees = models.FloatField(blank=True, null=True)
#     farm_in_ob = models.BigIntegerField(blank=True, null=True)
#     ob_status = models.CharField(max_length=50, blank=True, null=True)
#     date_discv = models.DateField(blank=True, null=True)
#     name_of_co = models.CharField(max_length=50, blank=True, null=True)
#     hectares = models.FloatField(blank=True, null=True)
#     shape_leng = models.FloatField(blank=True, null=True)
#     shape_area = models.FloatField(blank=True, null=True)
#     shape_area = models.FloatField(blank=True, null=True)
#     district_code = models.CharField(max_length=50, blank=True, null=True)
#     district = models.CharField(max_length=50, blank=True, null=True)
#     region = models.CharField(max_length=50, blank=True, null=True)
#     districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
#     class Meta:
#         managed = True
#         db_table = 'CSSVD_Outbreaks'


    
class communityTbl(models.Model):
	district = models.CharField(max_length=250)
	Operational_area = models.CharField(max_length=250)
	community = models.CharField(max_length=250)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		if self.district :
			district = cocoaDistrict.objects.get(district=self.district)
			self.districtTbl_foreignkey = district
		return super(communityTbl, self).save()






# class outbreakFarms(timeStamp):
# 	outbreaks_foreignkey = models.ForeignKey(outBreaks, on_delete=models.CASCADE,blank=True, null=True)
# 	farmboundary=  models.CharField(max_length=2500)
# 	farm_geom=models.GeometryField(blank=True, null=True)
# 	farm_location = models.CharField(max_length=250,blank=True, null=True)
# 	farmer_name = models.CharField(max_length=250)
# 	farmer_age = models.IntegerField(blank=True, null=True)
# 	id_type = models.CharField(max_length=250)
# 	id_number = models.CharField(max_length=250)
# 	farmer_contact = models.CharField(max_length=10)
# 	cocoa_type = models.CharField(max_length=250)
# 	age_class = models.CharField(max_length=250)
# 	farm_area = models.FloatField(max_length=10)
# 	communitytbl_foreignkey = models.ForeignKey(communityTbl, on_delete=models.CASCADE,blank=True, null=True)
# 	uid= models.CharField(max_length=2500,blank=True, null=True)
# 	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
# 	inspection_date= models.DateField(max_length=250, blank=True, null=True)
# 	temp_code = models.CharField(max_length=250,unique=True, blank=True, null=True)
# 	# staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)


# class weeklyobreportTbl(timeStamp):
# 	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
# 	monitoring_date=models.DateField(max_length=254)	
# 	district=models.CharField(max_length=2540, blank=True, null=True)
# 	Operational_area=models.CharField(max_length=2540, blank=True, null=True)
# 	community=	models.CharField(max_length=2540, blank=True, null=True)
# 	ob_id=	models.CharField(max_length=2540, blank=True, null=True)
# 	farm_name=models.CharField(max_length=2540, blank=True, null=True)
# 	farm_contact=models.CharField(max_length=2540, blank=True, null=True)
# 	farmer_ref_number=models.CharField(max_length=2540, blank=True, null=True)	
# 	main_activity=models.CharField(max_length=2540, blank=True, null=True)
# 	sub_activity=models.CharField(max_length=2540, blank=True, null=True)
# 	status_activity=models.CharField(max_length=2540, blank=True, null=True)
# 	no_ras=models.CharField(max_length=2540, blank=True, null=True)
# 	no_rts=models.CharField(max_length=2540, blank=True, null=True)
# 	name_ras=models.CharField(max_length=2540, blank=True, null=True)	
# 	farm_size=models.FloatField(max_length=2540, blank=True, null=True)
# 	total_workdone= models.FloatField(max_length=2540, blank=True, null=True)
# 	remark=	models.CharField(max_length=2540, blank=True, null=True)
# 	name_po=models.CharField(max_length=2540, blank=True, null=True)
# 	po_id=models.CharField(max_length=2540, blank=True, null=True)
# 	contractor_name=models.CharField(max_length=2540, blank=True, null=True)
# 	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
# 	activity = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
# 	current_farm_pic =models.ImageField(upload_to=f"obweeklymonitoring/{date.today().strftime('%Y-%m-%d')}" ,blank=True, null=True)
# 	farmTbl_foreignkey = models.ForeignKey(outbreakFarms, on_delete=models.CASCADE,blank=True, null=True)
# 	uid= models.CharField(max_length=2500,blank=True, null=True)
# 	lat= models.FloatField(default=0,blank=True, null=True	)
# 	lng= models.FloatField(default=0,blank=True, null=True	)
# 	accuracy= models.FloatField(default=0,blank=True, null=True)
# 	region= models.CharField(max_length=2500,blank=True, null=True)
# 	code=models.CharField(max_length=3540, blank=True, null=True,unique=True)

	
# 	class Meta:
# 		verbose_name_plural = "Weekly IT Report"

	# def save(self, force_insert=False, force_update=False, using=None, update_fields=None):

	# 	if self.districtTbl_foreignkey:
	# 		district = cocoaDistrict.objects.get(id=self.districtTbl_foreignkey.id)
	# 		self.region = district.reg_code.region
	# 	if self.district :
	# 		print(self.district)
	# 		district = cocoaDistrict.objects.get(district=self.district)
	# 		self.districtTbl_foreignkey = district
	# 		self.region = district.reg_code.region
	# 	if self.main_activity  and self.sub_activity:
	# 		act = Activities.objects.get(main_activity=self.main_activity,sub_activity=self.sub_activity)
	# 		self.activity = act

	# 	code = f"{self.monitoring_date}{self.district}{self.Operational_area}{self.community}{self.ob_id}{self.farm_name}{self.farm_contact}{self.farmer_ref_number}{self.main_activity}{self.sub_activity}{self.status_activity}{self.no_ras}{self.no_rts}{self.name_ras}{self.farm_size}{self.total_workdone}{self.remark}{self.name_po}{self.po_id}{self.contractor_name}{self.districtTbl_foreignkey}{self.activity}{self.current_farm_pic}{self.farmTbl_foreignkey}{self.uid}{self.lat}{self.lng}{self.accuracy}{self.region}" 

	# 	self.code = code

	# 	return super(weeklyobreportTbl, self).save()



class POdailyreportTbl(timeStamp):
	STATUS_CHOICES = ( 
    ("ongoing", "ongoing"), 
    ("complete", "complete"), 
	) 
	reporting_date= models.DateField(max_length=250)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	staff_id = models.CharField(max_length=2540, blank=True, null=True)
	location = models.CharField(max_length=2540, blank=True, null=True)
	farm_reference = models.CharField(max_length=2540, blank=True, null=True)
	farmTbl_foreignkey = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE,blank=True, null=True)
	activity = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
	activity_code = models.CharField(max_length=2540, blank=True, null=True)
	sector = models.CharField(max_length=2540, blank=True, null=True)
	original_farm_size = models.FloatField(default=0, blank=True, null=True)
	percentage_of_workdone =  models.FloatField(default=0, blank=True, null=True)
	status = models.CharField(default="Ongoing",max_length=2540, blank=True, null=True,choices =STATUS_CHOICES)
	code = models.CharField(max_length=3540, blank=True, null=True)
	class Meta:
		verbose_name_plural = "PO's Daily Reporting"

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):

		if self.staff_id:
			staff = staffTbl.objects.get(staffid=self.staff_id)
			self.staffTbl_foreignkey = staff
		# if self.farm_reference :
		# 	farm_reference = FarmdetailsTbl.objects.get(farm_reference=self.farm_reference)
		# 	self.farmTbl_foreignkey = farm_reference
		if  self.activity_code:
			act = Activities.objects.get(activity_code=self.activity_code)
			self.activity = act
		if self.percentage_of_workdone:
			if  self.percentage_of_workdone >= 100:
				self.status = "Completed"
			else:
				self.status = "Ongoing"



		code = f"{self.reporting_date}{self.staff_id}{self.location}{self.farm_reference}{self.activity_code}{self.sector}{self.original_farm_size}" 
		self.code = code

	

		return super(POdailyreportTbl, self).save()

























# class weeklyOBrehabassistTbl(timeStamp):
# 	weeklyMontoringTbl_foreignkey = models.ForeignKey(weeklyobreportTbl, on_delete=models.CASCADE)
# 	rehabassistantsTbl_foreignkey = models.ForeignKey(rehabassistantsTbl, on_delete=models.CASCADE, blank=True, null=True)
# 	rehabassistants = models.CharField(max_length=254, blank=True, null=True)
# 	area_covered_ha =  models.FloatField(default=0, blank=True, null=True)

# class fuelMontoringobTbl(timeStamp):	
# 	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)	
# 	farmdetailstbl_foreignkey = models.ForeignKey(outbreakFarms, on_delete=models.CASCADE, blank=True, null=True)
# 	date_received = models.DateField(max_length=254, blank=True, null=True)
# 	rehabassistantsTbl_foreignkey = models.ForeignKey(rehabassistantsTbl, on_delete=models.CASCADE, blank=True, null=True)
# 	fuel_ltr	= models.FloatField(default=0,blank=True, null=True	)
# 	remarks = models.CharField(max_length=654, blank=True, null=True) 
# 	uid = models.CharField(max_length=654, blank=True, null=True)




# class cocoatypeTbl(timeStamp):
# 	name = models.CharField(max_length=250)

# class cocoaageclassTbl(timeStamp):
# 	classtype = models.CharField(max_length=250)


class activateRate(timeStamp):
	activate_foreignkey = models.ForeignKey(Activities, on_delete=models.CASCADE,blank=True, null=True)
	rate = models.FloatField(max_length=10, blank=True, null=True)


class contractorsTbl(timeStamp):
	contractor_name	 = models.CharField(max_length=250)
	contact_person	 = models.CharField(max_length=250)
	address	 = models.CharField(max_length=250)
	contact_number	 = models.CharField(max_length=250)
	interested_services	 = models.CharField(max_length=250)
	target		 = models.CharField(max_length=250)		
	def __str__(self):
		return str(self.contractor_name)		


class contratorDistrictAssignment(timeStamp):
	contractor = models.ForeignKey(contractorsTbl, on_delete=models.CASCADE,blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)

# def myfunction(items) :
# 	newlist = []
# 	total=0
# 	# Check every item in list
# 	for item in items:
# 	  # If its a integer, add to newlist
# 		if isinstance(item, int):
# 			newlist.append(item)
# 		else:
# 			newlist.append(0)

# 	for ele in range(0, len(newlist)):
# 		total = total + newlist[ele]

# 	return total


class monitorbackroundtaskTbl(timeStamp):
	name = models.CharField(max_length=250)
	start = models.CharField(max_length=250)
	finish = models.CharField(max_length=250)


class Layers(models.Model):
	layer_choices = [
	('tif', 'TIF'),
	('shp', 'Shapefile'),
	('jpeg', 'Jpeg'),
	('kml', 'KML'),
	]
	name = models.CharField(max_length=254, blank=True, null=True,unique=True)
	layername = models.CharField(max_length=254, blank=True, null=True,unique=True)
	layer_type = models.CharField(max_length=254, blank=True, null=True,choices=layer_choices)
	created_date = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name




# class certificateCompletion(timeStamp):
# 	district = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
# 	reference_no = models.CharField(max_length=250)
# 	workdone_date_start	 = models.DateField(blank=True, null=True)
# 	workdone_date_end	 = models.DateField(blank=True, null=True)
# 	dispatched_date	 = models.DateField(blank=True, null=True)
# 	certified_by_peps = models.BooleanField(default=False)
# 	certified_by_dco = models.BooleanField(default=False)
# 	certified_by_service_provider = models.BooleanField(default=False)
# 	file = models.FileField(upload_to="certificate_completion",blank=True,null=True)
# 	payment_status = models.BooleanField(default=False)
# 	class Meta:
# 		verbose_name_plural = "Certificate of Completion"



# class approvedobsTbl(timeStamp):
# 	outbreakid = models.CharField(max_length=2540, unique=True)
# 	size = models.FloatField(max_length=2540, blank=True, null=True)
# 	estimated_trees =models.FloatField(max_length=2540, blank=True, null=True)
# 	district=models.CharField(max_length=2540, blank=True, null=True)
# 	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE)
# 	issue_size= models.FloatField(max_length=10, blank=True, null=True)
# 	treated_area= models.FloatField(max_length=10, blank=True, null=True)
# 	farm_reference=models.CharField(max_length=2540, blank=True, null=True)

# 	class Meta:
# 		verbose_name_plural = "Approved OBs"

# 	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
# 		if self.district :
# 			print
# 			district = cocoaDistrict.objects.get(district=self.district)
# 			self.districtTbl_foreignkey = district
# 		return super(approvedobsTbl, self).save()


def calc_geom(latitude, longitude):
	try:
		latitude = float(latitude)
		longitude = float(longitude)
		return GEOSGeometry('POINT (' + str(longitude) + ' ' + str(latitude) + ')')
	except Exception as e:
		import logging
		return logging.exception(str(e))

class posRoutemonitoring (timeStamp):
	
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	lat = models.FloatField(max_length=2540, blank=True, null=True)
	lng = models.FloatField(max_length=2540, blank=True, null=True)
	accuracy = models.FloatField(max_length=2540, blank=True, null=True)
	inspection_date= models.DateTimeField(max_length=250, blank=True, null=True)
	geom = models.GeometryField(blank=True, null=True)
	uid= models.CharField(max_length=2500,blank=True, null=True)

	class Meta:
		verbose_name_plural = "POs Monitor"

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		if self.lat :
			self.geom = calc_geom(self.lat, self.lng)
		return super(posRoutemonitoring, self).save()



class Feedback(timeStamp):
	status =(
		("Open", "Open"),
		("In Progress", "In Progress"),
		("Resolved", "Resolved"),
	) 
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	title= models.CharField(max_length=2500,blank=True, null=True)
	feedback= models.CharField(max_length=2500,blank=True, null=True)
	sent_date= models.DateTimeField(auto_now=True)
	uid= models.CharField(max_length=2500,blank=True, null=True)
	week= models.CharField(max_length=2500,blank=True, null=True)	
	month	= models.CharField(max_length=2500,blank=True, null=True)
	farm_reference = models.CharField(max_length=2500,blank=True, null=True)
	activity	= models.CharField(max_length=2500,blank=True, null=True)
	ra_id	= models.CharField(max_length=2500,blank=True, null=True)
	Status	= models.CharField(default="Open",max_length=2500, choices=status)





# class odkmaintenanceReportTbl(timeStamp):
# 	_id
# 	my_form_name
# 	date_of_reporting
# 	region
# 	district
# 	po_name
# 	telephone_number
# 	operation_name
# 	operational_year
# 	sex_farmer
# 	farmer_name
# 	farmer_reference
# 	farm_location
# 	farm_size
# 	activity
# 	farm_photo
# 	farm_video
# 	geopoint
# 	remarks
# 	po_signature
# 	__version__
# 	instanceID
# 	_xform_id_string
# 	_uuid
# 	_status
# 	_geolocation
# 	_submission_time
# 	_validation_status
# 	_submitted_by



	# monitoring_date=models.DateField(max_length=254)	
	# district=models.CharField(max_length=2540, blank=True, null=True)
	# Operational_area=models.CharField(max_length=2540, blank=True, null=True)
	# community=	models.CharField(max_length=2540, blank=True, null=True)
	# ob_id=	models.CharField(max_length=2540, blank=True, null=True)
	# farm_name=models.CharField(max_length=2540, blank=True, null=True)
	# farm_contact=models.CharField(max_length=2540, blank=True, null=True)
	# farmer_ref_number=models.CharField(max_length=2540, blank=True, null=True)	
	# main_activity=models.CharField(max_length=2540, blank=True, null=True)
	# sub_activity=models.CharField(max_length=2540, blank=True, null=True)
	# status_activity=models.CharField(max_length=2540, blank=True, null=True)
	# no_ras=models.CharField(max_length=2540, blank=True, null=True)
	# no_rts=models.CharField(max_length=2540, blank=True, null=True)
	# name_ras=models.CharField(max_length=2540, blank=True, null=True)	
	# farm_size=models.FloatField(max_length=2540, blank=True, null=True)
	# total_workdone= models.FloatField(max_length=2540, blank=True, null=True)
	# remark=	models.CharField(max_length=2540, blank=True, null=True)
	# name_po=models.CharField(max_length=2540, blank=True, null=True)
	# po_id=models.CharField(max_length=2540, blank=True, null=True)
	# contractor_name=models.CharField(max_length=2540, blank=True, null=True)
	# districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
	# activity = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
	# current_farm_pic =models.ImageField(upload_to=f"obweeklymonitoring/{date.today().strftime('%Y-%m-%d')}" ,blank=True, null=True)
	# farmTbl_foreignkey = models.ForeignKey(outbreakFarms, on_delete=models.CASCADE,blank=True, null=True)
	# uid= models.CharField(max_length=2500,blank=True, null=True)
	# lat= models.FloatField(default=0,blank=True, null=True	)
	# lng= models.FloatField(default=0,blank=True, null=True	)
	# accuracy= models.FloatField(default=0,blank=True, null=True)
	# region= models.CharField(max_length=2500,blank=True, null=True)
	
	# class Meta:
	# 	verbose_name_plural = "Weekly IT Report"

	# def save(self, force_insert=False, force_update=False, using=None, update_fields=None):

	# 	if self.districtTbl_foreignkey:
	# 		district = cocoaDistrict.objects.get(id=self.districtTbl_foreignkey.id)
	# 		self.region = district.reg_code.region
	# 	if self.district :
	# 		print(self.district)
	# 		district = cocoaDistrict.objects.get(district=self.district)
	# 		self.districtTbl_foreignkey = district
	# 		self.region = district.reg_code.region
	# 	if self.main_activity  and self.sub_activity:
	# 		act = Activities.objects.get(main_activity=self.main_activity,sub_activity=self.sub_activity)
	# 		self.activity = act
	# 	return super(weeklyobreportTbl, self).save()




# sql = "INSERT INTO general_information (project_number,project_name,project_lead,project_delivery_lead,project_status,financial_closure,project_type,contract_type,commodity,multi_calendar,project_start_date,project_finish_date, (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s)"


# data = ('project_number', 'project_name', 'project_lead', 'project_delivery_lead', 'project_status', 'financial_closure', 'project_type', 'contract_type',
#                     'commodity', 'multi_calendar', 'project_start_date', 'project_finish_date')


from django.conf import settings
from PIL import Image as Img
from PIL import ExifTags
from io import BytesIO
from django.core.files import File



# class koboMaintenance(timeStamp):
# 	formid= models.CharField(max_length=2500,blank=True, null=True)
# 	uuid= models.CharField(max_length=2500,blank=True, null=True)
# 	start=models.DateField(max_length=254,blank=True, null=True)	
# 	end=models.DateField(max_length=254,blank=True, null=True)	
# 	Region= models.CharField(max_length=2500,blank=True, null=True)
# 	District= models.CharField(max_length=2500,blank=True, null=True)
# 	Project_Officer= models.CharField(max_length=2500,blank=True, null=True)
# 	Ched_TA= models.CharField(max_length=2500,blank=True, null=True)
# 	Ched_TA_Number= models.CharField(max_length=2500,blank=True, null=True)
# 	Operational_Area_Name= models.CharField(max_length=2500,blank=True, null=True)
# 	Year= models.CharField(blank=True, null=True,max_length=250)
# 	Gender= models.CharField(max_length=2500,blank=True, null=True)
# 	Farmer_Name= models.CharField(max_length=2500,blank=True, null=True)
# 	Farm_ID= models.CharField(max_length=2500,blank=True, null=True)
# 	Farm_Location= models.CharField(max_length=2500,blank=True, null=True)
# 	Farm_Size= models.FloatField(default=0,blank=True, null=True	)
# 	Please_indicate_if_this_is_you= models.CharField(max_length=2500,blank=True, null=True)
# 	First_weeding= models.CharField(max_length=2500,blank=True, null=True)
# 	Please_kindly_indica_out_in_first_weeding= models.CharField(max_length=2500,blank=True, null=True)
# 	How_many_cocoa_seedlings_dead= models.IntegerField(default=0,blank=True, null=True	)
# 	How_many_plantain_suckers_dead= models.IntegerField(default=0,blank=True, null=True	)
# 	Take_farm_picture = models.ImageField(upload_to="farm_pic/", null=True,blank=True)

# 	# Take_a_Short_Video_o_t_State_of_the_Farm =models.FileField(upload_to=f"farm_video/{date.today().strftime('%Y-%m-%d')}" ,blank=True, null=True)
# 	Take_a_Short_Video_o_t_State_of_the_Farm =models.CharField(max_length=2500,blank=True, null=True)

# 	lat= models.FloatField(default=0,blank=True, null=True	)
# 	lng= models.FloatField(default=0,blank=True, null=True	)
# 	General_remarks= models.CharField(max_length=2500,blank=True, null=True)
# 	Please_Sign_Here = models.ImageField(upload_to=f"signature/{date.today().strftime('%Y-%m-%d')}" ,blank=True, null=True)
# 	version= models.CharField(max_length=2500,blank=True, null=True)
# 	instanceID= models.CharField(max_length=2500,blank=True, null=True)
# 	status= models.CharField(max_length=2500,blank=True, null=True)
# 	submission_time=models.DateTimeField(max_length=254,blank=True, null=True)	
# 	submitted_by= models.CharField(max_length=2500,blank=True, null=True)
# 	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
# 	class Meta:
# 		verbose_name_plural = "KOBO MAINTENANCE REPORT"








class maintenanceReport(timeStamp):
	formid= models.CharField(max_length=2500,blank=True, null=True)
	uuid= models.CharField(max_length=2500,blank=True, null=True)
	start=models.DateField(max_length=254,blank=True, null=True)	
	end=models.DateField(max_length=254,blank=True, null=True)	
	Region= models.CharField(max_length=2500,blank=True, null=True)
	District= models.CharField(max_length=2500,blank=True, null=True)
	Project_Officer= models.CharField(max_length=2500,blank=True, null=True)
	Ched_TA= models.CharField(max_length=2500,blank=True, null=True)
	Ched_TA_Number= models.CharField(max_length=2500,blank=True, null=True)
	Operational_Area_Name= models.CharField(max_length=2500,blank=True, null=True)
	report_date=models.DateField(max_length=254,blank=True, null=True)
	Farm_ID= models.CharField(max_length=2500,blank=True, null=True)
	Farm_Location= models.CharField(max_length=2500,blank=True, null=True)
	Farm_Size= models.FloatField(default=0,blank=True, null=True	)
	How_many_cocoa_seedlings_alive= models.IntegerField(default=0,blank=True, null=True	)
	How_many_plantain_suckers_alive= models.IntegerField(default=0,blank=True, null=True	)
	Take_farm_picture = models.ImageField(upload_to="farm_pic/", null=True,blank=True)
	# Take_a_Short_Video_o_t_State_of_the_Farm =models.FileField(upload_to=f"farm_video/{date.today().strftime('%Y-%m-%d')}" ,blank=True, null=True)
	# activity =models.CharField(max_length=2500,blank=True, null=True)
	lat= models.FloatField(default=0,blank=True, null=True	)
	lng= models.FloatField(default=0,blank=True, null=True	)

	activity =models.CharField(max_length=2500,blank=True, null=True)
	activity_done_contractor =models.CharField(max_length=2500,blank=True, null=True)

	General_remarks= models.CharField(max_length=2500,blank=True, null=True)
	Please_Sign_Here = models.ImageField(upload_to=f"signature/{date.today().strftime('%Y-%m-%d')}" ,blank=True, null=True)
	signid= models.CharField(max_length=2500,blank=True, null=True)
	version= models.CharField(max_length=2500,blank=True, null=True)
	instanceID= models.CharField(max_length=2500,blank=True, null=True)
	status= models.CharField(max_length=2500,blank=True, null=True)
	submission_time=models.DateTimeField(max_length=254,blank=True, null=True)	
	submitted_by= models.CharField(max_length=2500,blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	class Meta:
		verbose_name_plural = "MAINTENANCE REPORT"
		# ordering = ('first_name',)





# class MaintenancerehabachievementTbl(timeStamp):
# 	koboMaintenance_foreignkey = models.ForeignKey(koboMaintenance, on_delete=models.CASCADE)
# 	rehabassistantsTbl_foreignkey = models.ForeignKey(rehabassistantsTbl, on_delete=models.CASCADE, blank=True, null=True)
# 	rehabassistants = models.CharField(max_length=254, blank=True, null=True)
# 	area_covered_ha =  models.FloatField(default=0, blank=True, null=True)



class Equipment(timeStamp):
	equipment_code= models.CharField(max_length=2500,blank=True, null=True,unique=True)
	date_of_capturing=models.DateTimeField(max_length=254,blank=True, null=True)	
	region= models.CharField(max_length=2500,blank=True, null=True)
	district= models.CharField(max_length=2500,blank=True, null=True)
	project = models.CharField(max_length=2500,blank=True, null=True)
	equipment= models.CharField(max_length=2500,blank=True, null=True)
	status= models.CharField(max_length=2500,blank=True, null=True)
	serial_number= models.CharField(max_length=2500,blank=True, null=True)
	manufacturer= models.CharField(max_length=2500,blank=True, null=True)
	pic_serial_number= models.ImageField(upload_to="equipment/serialnumber", null=True,blank=True)
	pic_equipment= models.ImageField(upload_to="equipment/pic", null=True,blank=True)
	telephone= models.CharField(max_length=2500,blank=True, null=True)
	staff_name= models.CharField(max_length=2500,blank=True, null=True)
	_uuid= models.CharField(max_length=2500,blank=True, null=True)
	koboid= models.CharField(max_length=2500,blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	projectStaffTbl_foreignkey = models.ForeignKey(projectStaffTbl, on_delete=models.CASCADE,blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)

	# def save(self, *args, **kwargs):
	# 	# print("Saving")
	# 	# print(self.Take_farm_picture)
	# 	# print(self.Take_farm_picture)
	# 	# print("Saving")
	# 	if self.Take_farm_picture:
	# 		pilImage = Img.open(BytesIO(self.Take_farm_picture.read()))
	# 		for orientation in ExifTags.TAGS.keys():
	# 			if ExifTags.TAGS[orientation] == 'Orientation':
	# 				break
	# 		exif = dict(pilImage._getexif().items())
			
	# 		print(exif[orientation])
	# 		print(exif[orientation])
	# 		print(exif[orientation])
	# 		print(exif[orientation])
	# 		pilImage = pilImage.rotate(270, expand=True)

	# 		output = BytesIO()
	# 		pilImage.save(output, format='JPEG', quality=75)
	# 		output.seek(0)
	# 		self.image = File(output, self.imTake_farm_pictureage.name)

		# return super(koboMaintenance, self).save(*args, **kwargs)


# class contractorcertificateWorkdone(timeStamp):
# 	reporting_date=models.DateField(max_length=254)
# 	region= models.CharField(max_length=2500,blank=True, null=True)
# 	district= models.CharField(max_length=2500,blank=True, null=True)
# 	year= models.CharField(max_length=2500,blank=True, null=True)
# 	month= models.CharField(max_length=2500,blank=True, null=True)
# 	week = models.CharField(max_length=2500,blank=True, null=True)
# 	farmer_ref_number=models.CharField(max_length=2540, blank=True, null=True)
# 	farmer_name=models.CharField(max_length=2540, blank=True, null=True)	
# 	sector=models.IntegerField(blank=True, null=True)	
# 	community=models.CharField(max_length=2540, blank=True, null=True)
# 	activity=models.CharField(max_length=2540, blank=True, null=True)
# 	weeding_rounds=models.IntegerField(blank=True, null=True)
# 	farm_size=models.FloatField(max_length=2540, blank=True, null=True)
# 	contractor=models.CharField(max_length=2540, blank=True, null=True)
# 	po_telephone=models.FloatField(max_length=2540, blank=True, null=True)
# 	project_officer=models.CharField(max_length=2540, blank=True, null=True)
# 	submission_time=models.DateTimeField(max_length=254,blank=True, null=True)	
# 	uuid= models.CharField(max_length=2500,blank=True, null=True)
# 	po_validation=models.BooleanField(default=True)
# 	mne_validation=models.BooleanField(default=False, help_text="Only eidtable by Monitoring and Evaluation Officer " )
# 	rm_validation=models.BooleanField(default=False, help_text="Only eidtable by Regional Manager ")
# 	sm_validation=models.BooleanField(default=False, help_text="Only eidtable by Sector Manager ")
# 	# md_validation=models.BooleanField(default=False, help_text="Only eidtable by Managing Director ")
# 	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
# 	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
# 	code=models.CharField(max_length=3540, blank=True, null=True,unique=True)
# 	duplicate_status=models.CharField(max_length=2500,blank=True, null=True)
# 	duplicate_coments=models.CharField(max_length=2500,blank=True, null=True)

# 	class Meta:
# 		verbose_name_plural = "contractors Certificate of Workdone"

	
# 	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
# 		code = f"{self.reporting_date}{self.region}{self.district}{self.year}{self.month}{self.week}{self.farmer_ref_number}{self.community}{self.activity}{self.farm_size}{self.contractor}{self.po_telephone}{self.project_officer}{self.submission_time}{self.uuid}" 
# 		self.code = code
# 		return super(contractorcertificateWorkdone, self).save()
	



class chedcertficateofWorkdone(timeStamp):
	sector=models.IntegerField(max_length=2540, blank=True, null=True)
	reference_number=models.CharField(max_length=2540, blank=True, null=True)
	region=models.CharField(max_length=2540, blank=True, null=True)
	district	=models.CharField(max_length=2540, blank=False, null=False)
	farmer_name	=models.CharField(max_length=2540, blank=True, null=True)
	farm_reference=models.CharField(max_length=2540, blank=False, null=False)
	farm_location= models.CharField(max_length=2540, blank=True, null=True)	
	farm_size	= models.CharField(max_length=2540, blank=False, null=False)
	# certificate_reference	=models.CharField(max_length=2540, blank=False, null=False)
	activity	=models.CharField(max_length=2540, blank=False, null=False)
	activity_code	=models.CharField(max_length=2540, blank=False, null=False)
	month= models.CharField(max_length=2540, blank=False, null=False)
	year= models.CharField(max_length=2540, blank=False, null=False)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	code=models.CharField(max_length=3540, blank=True, null=True,unique=True)

	class Meta:
		verbose_name_plural = "CHED Certificate of Workdone"

	
	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		code = f"{self.farm_reference}{self.farm_size}{self.activity_code}{self.month}{self.year}" 
		self.code = code

		if self.district :
			district = cocoaDistrict.objects.get(district__iexact = self.district)
			self.districtTbl_foreignkey = district
		return super(chedcertficateofWorkdone, self).save()




class paymentReport(timeStamp):
	district	=models.CharField(max_length=2540, blank=True, null=True)
	bank_name	=models.CharField(max_length=2540, blank=True, null=True)
	bank_branch = models.CharField(max_length=2540, blank=True, null=True)	
	momo_acc = models.CharField(max_length=2540, blank=True, null=True)	
	payment_option = models.CharField(max_length=2540, blank=True, null=True)	
	snnit_no	= models.CharField(max_length=2540, blank=True, null=True)
	salary	=models.CharField(max_length=2540, blank=True, null=True)
	project= models.CharField(max_length=2540, blank=True, null=True)
	projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE,blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	po_number= models.CharField(max_length=2540, blank=True, null=True)
	month = models.CharField(max_length=2540, blank=False, null=True)
	week = models.CharField(max_length=2540, blank=False, null=True)
	year = models.CharField(max_length=2540, blank=False, null=True)
	ra_id = models.CharField(max_length=2540, blank=False, null=True,default="NA")
	ra_name = models.CharField(max_length=2540, blank=False, null=True,default="NA")
	code=models.CharField(max_length=3540, blank=True, null=True,unique=True)
	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		if self.district :
			print(self.district)
			district = cocoaDistrict.objects.get(district__iexact=self.district)
			self.districtTbl_foreignkey = district

		code = f"{self.district}{self.bank_name}{self.bank_branch}{self.momo_acc}{self.payment_option}{self.snnit_no}{self.salary}{self.districtTbl_foreignkey}{self.po_number}{self.month}{self.week}{self.year}{self.ra_id}{self.ra_name}" 
		self.code = code
		return super(paymentReport, self).save()


	
	# def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
	
		# if self.district :
		# 	district = cocoaDistrict.objects.get(district__iexact = self.district)
		# 	self.districtTbl_foreignkey = district
		# return super(paymentReport, self).save()



class weeklyreportSummary(timeStamp):
	region=models.CharField(max_length=2540, blank=True, null=True)
	district=models.CharField(max_length=2540, blank=True, null=True)
	aboricide_application=models.FloatField(max_length=2540, blank=True, null=True)	
	hacking	=models.FloatField(max_length=2540, blank=True, null=True)
	slashing_before_cutting	=models.FloatField(max_length=2540, blank=True, null=True)
	tree_cutting_cocoa=models.FloatField(max_length=2540, blank=True, null=True)
	fertilizer_application=models.FloatField(max_length=2540, blank=True, null=True)
	pesticide_application=models.FloatField(max_length=2540, blank=True, null=True)
	weeding_of_replanted_farms=models.FloatField(max_length=2540, blank=True, null=True)
	refill_of_plantain_suckers=models.FloatField(max_length=2540, blank=True, null=True)
	refill_of_cocoa_seedlings=models.FloatField(max_length=2540, blank=True, null=True)
	cutting_and_transportation_of_pegs=models.FloatField(max_length=2540, blank=True, null=True)
	holing_for_cocoa_seedlings=models.FloatField(max_length=2540, blank=True, null=True)
	holing_for_plantain_seedlings=models.FloatField(max_length=2540, blank=True, null=True)
	lining=models.FloatField(max_length=2540, blank=True, null=True)
	lining_and_pegging	=models.FloatField(max_length=2540, blank=True, null=True)
	planting_of_cocoa_seedlings=models.FloatField(max_length=2540, blank=True, null=True)
	planting_of_plantain_seedlings	=models.FloatField(max_length=2540, blank=True, null=True)
	portage_of_cocoa_seedlings=models.FloatField(max_length=2540, blank=True, null=True)
	portage_of_plantain_seedlings=models.FloatField(max_length=2540, blank=True, null=True)
	slashing_before_lining_and_pegging	=models.FloatField(max_length=2540, blank=True, null=True)
	year=models.FloatField(max_length=2540, blank=True, null=True)
	month=models.CharField(max_length=2540, blank=True, null=True)
	week=models.FloatField(max_length=2540, blank=True, null=True)
	refill_holing_for_cocoa_seedlings=models.FloatField(max_length=2540, blank=True, null=True)
	refill_holing_for_plantain_seedlings=models.FloatField(max_length=2540, blank=True, null=True)




class farmDatabase(timeStamp):
	region=models.CharField(max_length=2540, blank=True, null=True)
	district=models.CharField(max_length=2540, blank=True, null=True)
	location=models.CharField(max_length=2540, blank=True, null=True)
	farm_ref=models.CharField(max_length=2540, blank=True, null=True,unique=True)
	farm_size=models.CharField(max_length=2540, blank=True, null=True)
	farmer_name=models.CharField(max_length=2540, blank=True, null=True)
	po_contact=models.CharField(max_length=2540, blank=True, null=True)
	po_name=models.CharField(max_length=2540, blank=True, null=True)
	activities=models.CharField(max_length=2540, blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		if self.district :
			print(self.district)
			district = cocoaDistrict.objects.get(district__iexact=self.district)
			self.districtTbl_foreignkey = district
		return super(farmDatabase, self).save()





class paymentdetailedReport(timeStamp):
	group_code	=models.CharField(max_length=2540, blank=True, null=True)
	ra_id	=models.CharField(max_length=2540, blank=True, null=True)
	ra_name	=models.CharField(max_length=2540, blank=True, null=True)
	ra_account	=models.CharField(max_length=2540, blank=True, null=True)
	po_id	=models.CharField(max_length=2540, blank=True, null=True)
	po_name	=models.CharField(max_length=2540, blank=True, null=True)
	po_number=models.CharField(max_length=2540, blank=True, null=True)
	district=models.CharField(max_length=2540, blank=True, null=True)
	project = models.CharField(max_length=2540, blank=True, null=True)
	farmhands_type=models.CharField(max_length=2540, blank=True, null=True)
	farm_reference=models.CharField(max_length=2540, blank=True, null=True)
	number_in_a_group=models.CharField(max_length=2540, blank=True, null=True)
	activity=models.CharField(max_length=2540, blank=True, null=True)
	farmsize=models.FloatField(max_length=2540, blank=True, null=True)
	achievement=models.FloatField(max_length=2540, blank=True, null=True)
	amount=models.CharField(max_length=2540, blank=True, null=True)
	week=models.CharField(max_length=2540, blank=True, null=True)
	month=models.CharField(max_length=2540, blank=True, null=True)
	year=models.CharField(max_length=2540, blank=True, null=True)
	issue=models.CharField(max_length=2540, blank=True, null=True)
	sector=models.CharField(max_length=2540, blank=True, null=True)
	projectTbl_foreignkey = models.ForeignKey(projectTbl, on_delete=models.CASCADE,blank=True, null=True)
	# districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	code=models.CharField(max_length=3540, blank=True, null=True,unique=True)
	act_code=models.CharField(max_length=2540, blank=True, null=True)

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		if self.district :
			# print(self.district)
			district = cocoaDistrict.objects.get(district__iexact=self.district)
			self.districtTbl_foreignkey = district

		code = f"{self.group_code}{self.ra_id}{self.ra_name}{self.ra_account}{self.po_name}{self.po_number}{self.district}{self.farmhands_type}{self.farm_reference}{self.number_in_a_group}{self.activity}{self.achievement}{self.amount}{self.week}{self.month}{self.year}" 
		self.code = code


		return super(paymentdetailedReport, self).save()

# class issuesReport(timeStamp):
# 	group_code	= models.CharField(max_length=2540, blank=True, null=True)

class versionTbl(timeStamp):
	version = models.IntegerField(blank=True, null=True)




class mobileMaintenance(timeStamp):
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
	uid	=models.CharField(max_length=2540, blank=True, null=True)
	monitoring_date=models.DateField(blank=True, null=True)
	no_rehab_assistants=models.FloatField(max_length=2540, blank=True, null=True)
	area_covered_ha=models.FloatField(max_length=2540, blank=True, null=True)
	remark 	=models.CharField(max_length=2540, blank=True, null=True)
	lat =models.FloatField(max_length=2540, blank=True, null=True)
	lng= models.FloatField(max_length=2540, blank=True, null=True)
	accuracy=models.FloatField(max_length=2540, blank=True, null=True)
	activity = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
	current_farm_pic =models.ImageField(upload_to=f"obweeklymonitoring/{date.today().strftime('%Y-%m-%d')}" ,blank=True, null=True)
	farm_ref_number	=models.CharField(max_length=2540, blank=True, null=True)
	farm_size_ha =models.FloatField(max_length=2540, blank=True, null=True)
	cocoa_seedlings_alive=models.FloatField(max_length=2540, blank=True, null=True)
	plantain_seedlings_alive=models.FloatField(max_length=2540, blank=True, null=True)
	name_of_ched_ta	=models.CharField(max_length=2540, blank=True, null=True)
	ched_ta_contact	=models.CharField(max_length=2540, blank=True, null=True)
	community	=models.CharField(max_length=2540, blank=True, null=True)
	contractor_name 	=models.CharField(max_length=2540, blank=True, null=True)
	number_of_people_in_group =models.FloatField(max_length=2540, blank=True, null=True)
	groupWork	=models.CharField(max_length=2540, blank=True, null=True)
	completedByContractor	=models.CharField(max_length=2540, blank=True, null=True)





class mobileMaintenancerehabassistTbl(timeStamp):
	mobileMaintenance_foreignkey = models.ForeignKey(mobileMaintenance, on_delete=models.CASCADE)
	rehabassistantsTbl_foreignkey = models.ForeignKey(rehabassistantsTbl, on_delete=models.CASCADE, blank=True, null=True)
	area_covered_ha =  models.FloatField(default=0, blank=True, null=True)









class verificationWorkdone(timeStamp):
	reporting_date=models.DateField(max_length=254)
	region= models.CharField(max_length=2500,blank=True, null=True)
	district= models.CharField(max_length=2500,blank=True, null=True)
	year= models.CharField(max_length=2500,blank=True, null=True)
	month= models.CharField(max_length=2500,blank=True, null=True)
	week = models.CharField(max_length=2500,blank=True, null=True)
	farmer_ref_number=models.CharField(max_length=2540, blank=True, null=True)	
	community=models.CharField(max_length=2540, blank=True, null=True)
	activity=models.CharField(max_length=2540, blank=True, null=True)
	farm_size=models.FloatField(max_length=2540, blank=True, null=True)
	contractor=models.CharField(max_length=2540, blank=True, null=True)
	po_telephone=models.FloatField(max_length=2540, blank=True, null=True)
	project_officer=models.CharField(max_length=2540, blank=True, null=True)
	submission_time=models.DateTimeField(max_length=254,blank=True, null=True)
	lat =models.FloatField(max_length=2540, blank=True, null=True)
	lng= models.FloatField(max_length=2540, blank=True, null=True)	
	accuracy= models.FloatField(max_length=2540, blank=True, null=True)	
	geom = models.GeometryField(blank=True, null=True)
	uuid= models.CharField(max_length=2500,blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	code=models.CharField(max_length=3540, blank=True, null=True,unique=True)
	current_farm_pic =models.ImageField(upload_to=f"verificationworkdone/{date.today().strftime('%Y-%m-%d')}" ,blank=True, null=True)
	completed_by= models.CharField(max_length=2500,blank=True, null=True)
	class Meta:
		verbose_name_plural = "Verification Workdone"

	
	# def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
	# 	code = f"{self.reporting_date}{self.region}{self.district}{self.year}{self.month}{self.week}{self.farmer_ref_number}{self.community}{self.activity}{self.farm_size}{self.contractor}{self.po_telephone}{self.project_officer}{self.submission_time}{self.uuid}" 
	# 	self.code = code
	# 	return super(contractorcertificateWorkdone, self).save()

class sector(timeStamp):
	sector= models.IntegerField(blank=True, null=True)
	def __str__(self):
		return str(self.sector)

class sectorDistrict(timeStamp):

	sector = models.ForeignKey(sector, on_delete=models.CASCADE,blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)


class sectorStaffassignment(timeStamp):
	sector = models.ForeignKey(sector, on_delete=models.CASCADE,blank=False, null=False)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=False, null=False)



class seedlingEnumeration(timeStamp):
	field_uri= models.CharField(primary_key=True, unique=True, max_length=80,)
	start=models.DateTimeField(max_length=254,blank=True, null=True)
	end=models.DateTimeField(max_length=254,blank=True, null=True)
	reporting_date=models.DateTimeField(max_length=254,blank=True, null=True)
	staff=models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	Region= models.CharField(max_length=2500,blank=True, null=True)
	District= models.CharField(max_length=2500,blank=True, null=True)
	sector_no= models.IntegerField(blank=True, null=True)
	Farm_ID= models.CharField(max_length=2500,blank=True, null=True)
	Farm_Size= models.FloatField(max_length=2540, blank=True, null=True)	
	year_of_establishment=models.DateTimeField(max_length=254,blank=True, null=True)
	Farmer_Name= models.CharField(max_length=2500,blank=True, null=True)
	Location= models.CharField(max_length=2500,blank=True, null=True)
	Expected_seedlings= models.IntegerField( blank=True, null=True)	
	Number_Cocoa_Seedlings= models.IntegerField( blank=True, null=True)	
	Number_Cocoa_Seedling_dead= models.IntegerField( blank=True, null=True)	
	Number_Plantain_Seedlings= models.IntegerField(blank=True, null=True)	
	Number_Plantain_Seedlings_dead= models.IntegerField(blank=True, null=True)	
	workdone_by= models.CharField(max_length=2500,blank=True, null=True)
	Latitude= models.FloatField(max_length=2540, blank=True, null=True)	
	Longitude= models.FloatField(max_length=2540, blank=True, null=True)	
	Altitude= models.FloatField(max_length=2540, blank=True, null=True)	
	Accuracy= models.FloatField(max_length=2540, blank=True, null=True)	
	General_remarks= models.CharField(max_length=2500,blank=True, null=True)
	summary_sheet_pic=models.ImageField(upload_to=f"seedlingcount" ,blank=True, null=True)
	instanceID= models.CharField(max_length=2500,blank=True, null=True)
	field_submission_date=models.DateTimeField(max_length=254,blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	duplicate_check= models.CharField(max_length=2500,blank=True, null=True)
	delete_duplicate= models.BooleanField(default=False, max_length=2500)
	mne_comment= models.CharField(max_length=2500,blank=True, null=True)
	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		try:
			code = cocoaDistrict.objects.get(district=self.District)
			self.districtTbl_foreignkey = code
			farm=FarmdetailsTbl.objects.get(farm_reference=self.Farm_ID)
			self.Farm_Size=farm.farm_size
			self.Farmer_Name=farm.farmername
			self.Location=farm.location
		except:
			pass
			asd=""
		return super(seedlingEnumeration, self).save()

		


class seedlingenumworkdoneRa(timeStamp):
	seedlingEnumeration_foreignkey=models.ForeignKey(seedlingEnumeration, on_delete=models.CASCADE,blank=True, null=True)
	rehabassistantsTbl_foreignkey=models.CharField(max_length=2500,blank=True, null=True)

class seedlingenumworkdonePo(timeStamp):
	seedlingEnumeration_foreignkey=models.ForeignKey(seedlingEnumeration, on_delete=models.CASCADE,blank=True, null=True)
	staffTbl_foreignkey=models.CharField(max_length=2500,blank=True, null=True)



class HQcertificateReciept(timeStamp):

	INVOICE_STATUS_CHOICES = [
    ('Not Invoiced', 'Not Invoiced'),
    ('Invoiced', 'Invoiced'),
    ('Returned', 'Returned'),
]
	reference_number= models.CharField(max_length=2500,blank=True, null=True)
	company_name= models.CharField(max_length=2500,blank=True, null=True)
	activity = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
	total_workdone = models.FloatField(max_length=2540, blank=True, null=True)	
	workdone_date_from=models.DateField(max_length=254,blank=True, null=True)
	workdone_date_to=models.DateField(max_length=254,blank=True, null=True)
	certified_date=models.DateField(max_length=254,blank=True, null=True)
	activity_code= models.CharField(max_length=2500,blank=True, null=True)
	receipt_date=models.DateField(max_length=254,blank=True, null=True)
	serialNumber= models.CharField(max_length=2500,blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)

	status= models.CharField(choices=INVOICE_STATUS_CHOICES,max_length=2500,default="Not Invoiced")
	class Meta:
		verbose_name_plural = "HQ Certificate Reciept"


class SectorcertificateReciept(timeStamp):
	reference_number= models.CharField(max_length=2500,blank=True, null=True)
	company_name= models.CharField(max_length=2500,blank=True, null=True)
	activity = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
	activity_code= models.CharField(max_length=2500,blank=True, null=True)
	total_workdone = models.FloatField(max_length=2540, blank=True, null=True)	
	workdone_date_from=models.DateField(max_length=254,blank=True, null=True)
	workdone_date_to=models.DateField(max_length=254,blank=True, null=True)
	certified_date=models.DateField(max_length=254,blank=True, null=True)
	receipt_date=models.DateField(max_length=254,blank=True, null=True)
	serialNumber= models.CharField(max_length=2500,blank=True, null=True)
	sector= models.IntegerField(blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	class Meta:
		verbose_name_plural = "Sector Certificate Reciept"





class Sidebar(models.Model):
    name = models.CharField(max_length=50,null=True,blank=True)
    
    def __str__(self):
        return str(self.name)

class GroupSidebar(models.Model):
    assigned_group = models.ForeignKey(Group,on_delete=models.CASCADE,null=True,blank=True)
    hidden_sidebars = models.ManyToManyField(Sidebar,blank=True)

    def __str__(self):
        return str(self.assigned_group)
	


class mappedFarms(timeStamp):
	farm_reference	= models.CharField(max_length=250,blank=True, null=True,unique=True)
	farm_area = models.FloatField(max_length=250,blank=True, null=True)
	farmer_name= models.CharField(max_length=2500,blank=True, null=True)
	location = models.CharField(max_length=2500,blank=True, null=True)
	contact = models.CharField(max_length=2500,blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	farmboundary=  models.CharField(max_length=925000)
	geom=models.GeometryField(blank=True, null=True)
	uuid= models.CharField(max_length=2500,blank=True, null=True)
	class Meta:
		verbose_name_plural = "Farm Mapping Exercise"



class seedlingEnumerationCheck(timeStamp):
	field_uri= models.CharField(primary_key=True, unique=True, max_length=80,)



class powerbiReport(timeStamp):
	menu_label= models.CharField(unique=True, max_length=80,)
	url= models.CharField(unique=True, max_length=4000,)
	last_updated=  models.DateField(max_length=80 , blank=True) 


# 	id = models.IntegerField(primary_key=True)
# 	geom = models.MultiPolygonField(blank=True, null=True)
# 	name = models.CharField(max_length=38, blank=True, null=True)
# 	fid = models.IntegerField(blank=True, null=True)
# 	district = models.CharField(max_length=38, blank=True, null=True)
# 	reg_code_i = models.CharField(max_length=2, blank=True, null=True)
# 	shape_area = models.FloatField(blank=True, null=True)
# 	region = models.CharField(max_length=1, blank=True, null=True)
# 	district_c = models.CharField(max_length=18, blank=True, null=True)
# 	sector = models.CharField(max_length=9, blank=True, null=True)
# 	sector_num = models.CharField(max_length=10, blank=True, null=True)

# 	class Meta:
# 		managed = False
# 		db_table = 'sector_boundary'


class FarmValidation(timeStamp):
	field_uri= models.CharField(primary_key=True, unique=True, max_length=1000,)
	field_submission_date= models.DateTimeField(max_length=1000, blank=True, null=True)
	reporting_date= models.CharField(max_length=1000, blank=True, null=True)
	staff_id= models.CharField(max_length=1000, blank=True, null=True)
	staff_name= models.CharField(max_length=1000, blank=True, null=True)
	sector_no= models.IntegerField(max_length=1000, blank=True, null=True)
	region= models.CharField(max_length=1000, blank=True, null=True)
	district= models.CharField(max_length=1000, blank=True, null=True)
	farm_id= models.CharField(max_length=1000, blank=True, null=True)
	farm_size= models.FloatField(max_length=1000, blank=True, null=True)
	farmer_contact= models.CharField(max_length=1000, blank=True, null=True)
	farm_verified_by_ched= models.CharField(max_length=1000, blank=True, null=True)
	demarcated_to_boundary= models.CharField(max_length=1000, blank=True, null=True)
	treated_to_boundary= models.CharField(max_length=1000, blank=True, null=True)
	undesirable_shade_tree= models.CharField(max_length=1000, blank=True, null=True)
	farmer_name= models.CharField(max_length=1000, blank=True, null=True)
	maintained_to_boundary= models.CharField(max_length=1000, blank=True, null=True)
	point_lng= models.CharField(max_length=1000, blank=True, null=True)
	point_lat= models.CharField(max_length=1000, blank=True, null=True)
	point_acc= models.CharField(max_length=1000, blank=True, null=True)
	farms_in_mushy_field= models.CharField(max_length=1000, blank=True, null=True)
	rice_maize_cassava_farm= models.CharField(max_length=1000, blank=True, null=True)
	location= models.CharField(max_length=1000, blank=True, null=True)
	established_to_boundary= models.CharField(max_length=1000, blank=True, null=True)
	general_remarks= models.CharField(max_length=1000, blank=True, null=True)

	class Meta:
		verbose_name_plural = "Farm Validation Exercise"


class FarmValidationCheck(timeStamp):
	field_uri= models.CharField(primary_key=True, unique=True, max_length=80,)




class weeklyActivityReport(timeStamp):
	region= models.CharField(max_length=1000, blank=True, null=True)
	district= models.CharField(max_length=1000, blank=True, null=True)
	sector= models.IntegerField(max_length=1000, blank=True, null=True)
	report_week= models.CharField(max_length=1000, blank=True, null=True)
	day= models.IntegerField(max_length=1000, blank=True, null=True)
	month= models.CharField(max_length=1000, blank=True, null=True)
	completion_date= models.DateField(max_length=1000, blank=True, null=True)
	farmhand_type= models.CharField(max_length=1000, blank=True, null=True)
	activity= models.CharField(max_length=1000, blank=True, null=True)
	equipment= models.CharField(max_length=1000, blank=True, null=True)
	farmer_name= models.CharField(max_length=1000, blank=True, null=True)
	community= models.CharField(max_length=1000, blank=True, null=True)
	farm_reference= models.CharField(max_length=1000, blank=True, null=True)
	farm_size= models.FloatField(max_length=1000, blank=True, null=True)
	rate= models.FloatField(max_length=1000, blank=True, null=True)
	poid= models.CharField(max_length=1000, blank=True, null=True)
	po_name= models.CharField(max_length=1000, blank=True, null=True)
	po_number= models.CharField(max_length=1000, blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	activity_code= models.CharField(max_length=1000, blank=True, null=True)
	activity_foreignkey = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	farmTbl_foreignkey = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE,blank=True, null=True)
	code=models.CharField(max_length=4540, blank=True, null=True,unique=True)

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		code = f"{self.region}{self.district}{self.sector}{self.report_week}{self.day}{self.month}{self.completion_date}{self.farmhand_type}{self.activity_code}{self.equipment}{self.farmer_name}{self.community}{self.farm_reference}{self.farm_size}{self.rate}{self.poid}{self.po_name}{self.po_number}" 
		self.code = code

		if self.district:
			district = cocoaDistrict.objects.get(district=self.district)
			self.districtTbl_foreignkey = district

		if self.activity_code:
			act = Activities.objects.get(activity_code=self.activity_code)
			self.activity_foreignkey = act

		if self.poid:
			staff = staffTbl.objects.get(staffid=self.poid)
			self.staffTbl_foreignkey = staff
		
		if self.farm_reference :
			farm_reference = FarmdetailsTbl.objects.get(farm_reference=self.farm_reference)
			self.farmTbl_foreignkey = farm_reference

		return super(weeklyActivityReport, self).save()
	


# class dailyReportAnalysis(timeStamp):
# 	farmTbl_foreignkey = models.ForeignKey(FarmdetailsTbl, on_delete=models.CASCADE,blank=True, null=True)
# 	farm_size= models.FloatField(max_length=1000, blank=True, null=True)
# 	achievement= models.FloatField(max_length=1000, blank=True, null=True)
# 	activity_foreignkey = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
# 	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
# 	sector= models.CharField(max_length=1000, blank=True, null=True)
# 	status= models.CharField(max_length=1000, blank=True, null=True)
# 	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
# 	percentage_of_workdone =  models.FloatField(default=0, blank=True, null=True)
# 	latest_reporting_date= models.DateField(max_length=250)
# 	updated_date= models.DateTimeField(auto_now=True)
# 	farm_reference= models.CharField(max_length=1000, blank=True, null=True)



class calbankmomoTransaction(timeStamp):
	Month= models.CharField(max_length=1000, blank=True, null=True)
	Week= models.CharField(max_length=1000, blank=True, null=True)
	BranchCode= models.CharField(max_length=1000, blank=True, null=True)	
	BeneficiaryBank	= models.CharField(max_length=1000, blank=True, null=True)
	PhoneNumber	= models.CharField(max_length=1000, blank=True, null=True)
	PaymentMode	= models.CharField(max_length=1000, blank=True, null=True)
	WalletNumber	= models.CharField(max_length=1000, blank=True, null=True)
	TransactionReference= models.CharField( unique=True, max_length=1000, blank=True, null=True)	
	Amount	= models.FloatField(max_length=1000, blank=True, null=True)
	WalletNetwork	= models.CharField(max_length=1000, blank=True, null=True)
	BeneficiaryAccount	= models.CharField(max_length=1000, blank=True, null=True)
	Name	= models.CharField(max_length=1000, blank=True, null=True)
	Enquiry= models.CharField(max_length=1000, blank=True, null=True)
	year= models.IntegerField(max_length=1000, blank=True, null=True)


	class Meta:
		verbose_name_plural = "Cal Bank Momo Transaction"






class Joborder(timeStamp):
	id = models.AutoField(primary_key=True) 
	farm_foreignkey = models.ForeignKey(Farms, on_delete=models.CASCADE,blank=True, null=True)
	region= models.CharField(max_length=2500,blank=True, null=True)
	district= models.CharField(max_length=2500,blank=True, null=True)
	farmername= models.CharField(max_length=2500,blank=True, null=True)
	location= models.CharField(max_length=2500,blank=True, null=True)
	farm_reference= models.CharField(max_length=2500,unique=True,blank=True, null=True)
	farm_size= models.FloatField(max_length=2500, blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	sector= models.IntegerField(blank=True, null=True)
	year_of_establishment= models.DateField(max_length=2500,blank=True, null=True)
	farm_reference= models.CharField(max_length=2500,unique=True)
	E1= models.IntegerField(default=1,help_text="Slashing before Lining and Pegging")
	E2= models.IntegerField(default=1,help_text="Holing for Cocoa Seedlings")
	E3= models.IntegerField(default=1,help_text="Holing for Plantain Seedlings and Desirable Trees")
	E4= models.IntegerField(default=1,help_text="Lining")
	E6= models.IntegerField(default=1,help_text="Planting of Cocoa Seedlings")
	E7= models.IntegerField(default=1,help_text="Planting of Plantain Seedlings and Desirable Trees")
	M3= models.IntegerField(default=2,help_text="Weeding of Replanted Farms")
	R1= models.IntegerField(default=1,help_text="Refilling of Cocoa Seedlings (Holing)")
	R2= models.IntegerField(default=1,help_text="(Holing) Refilling of Plantain Seedlings")
	R3= models.IntegerField(default=1,help_text="Refilling of Cocoa Seedlings (Planting)")
	R4= models.IntegerField(default=1,help_text="Refilling of Plantain Seedlings (Planting)")
	T1= models.IntegerField(default=1,help_text="Aboricide Application")
	T2= models.IntegerField(default=1,help_text="Hacking")
	T5= models.IntegerField(default=1,help_text="Slashing before Cutting")
	T7= models.IntegerField(default=1,help_text="Tree Cutting (Cocoa and Undesirables)")
	job_order_code=models.CharField(max_length=4540, blank=True, null=True,unique=True)


	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		self.job_order_code = f"{self.region}{self.district}{self.location}{self.farm_size}{self.farm_reference}{self.farmername}"
		
		if cocoaDistrict.objects.filter(district__iexact=self.district).exists():
			district = cocoaDistrict.objects.get(district__iexact=self.district)
		# FarmdetailsTbl.objects.filter(id = self.id ).update(districtTbl_foreignkey=district)
			self.districtTbl_foreignkey =  district
		return super(Joborder, self).save()

	def __str__(self):
		return self.farm_reference
	




class activityReporting(timeStamp):
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE, blank=True, null=True)
	uid	=models.CharField(max_length=2540, blank=True, null=True)
	completed_date=models.DateField(blank=True, null=True)
	no_rehab_assistants=models.FloatField(max_length=2540, blank=True, null=True)
	area_covered_ha=models.FloatField(max_length=2540, blank=True, null=True)
	remark 	=models.CharField(max_length=2540, blank=True, null=True)
	activity = 	models.ForeignKey(Activities, on_delete=models.CASCADE, blank=True, null=True)
	farm_ref_number	=models.CharField(max_length=2540, blank=True, null=True)
	sector	=models.IntegerField(max_length=2540, blank=True, null=True)
	farm_size_ha =models.FloatField(max_length=2540, blank=True, null=True)
	reporting_date	=models.DateField(max_length=2540, blank=True, null=True)
	community	=models.CharField(max_length=2540, blank=True, null=True)
	number_of_people_in_group =models.FloatField(max_length=2540, blank=True, null=True)
	groupWork	=models.CharField(max_length=2540, blank=True, null=True)
	joborder = 	models.ForeignKey(Joborder, on_delete=models.CASCADE, blank=True, null=True)

	class Meta:
		verbose_name_plural = "RA Activity Reporting - New"



class activityreportingrehabassistTbl(timeStamp):
	activityreporting_foreignkey = models.ForeignKey(activityReporting, on_delete=models.CASCADE)
	rehabassistantsTbl_foreignkey = models.ForeignKey(rehabassistantsTbl, on_delete=models.CASCADE, blank=True, null=True)
	area_covered_ha =  models.FloatField(default=0, blank=True, null=True)





class specialprojectfarmsTbl(timeStamp):
	region=models.CharField(max_length=2540, blank=True, null=True)
	district=models.CharField(max_length=2540, blank=True, null=True)
	report_week=models.CharField(max_length=2540, blank=True, null=True)
	month=models.CharField(max_length=2540, blank=True, null=True)
	completion_date=models.CharField(max_length=2540, blank=True, null=True)
	main_activity=models.CharField(max_length=2540, blank=True, null=True)
	activity=models.CharField(max_length=2540, blank=True, null=True)
	plot_name=models.CharField(max_length=2540, blank=True, null=True)
	plot_reference_number=models.CharField(max_length=2540, blank=True, null=True)
	plot_size=models.CharField(max_length=2540, blank=True, null=True)
	achievement=models.CharField(max_length=2540, blank=True, null=True)
	po_id=models.CharField(max_length=2540, blank=True, null=True)
	name_of_po=models.CharField(max_length=2540, blank=True, null=True)
	phone_number=models.CharField(max_length=2540, blank=True, null=True)
	mne_id=models.CharField(max_length=2540, blank=True, null=True)
	mne_name=models.CharField(max_length=2540, blank=True, null=True)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	code=models.CharField(max_length=3540, blank=True, null=True,unique=True)

def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
	code = f"{self.region}{self.district}{self.report_week}{self.month}{self.completion_date}{self.main_activity}{self.activity}{self.plot_name}{self.plot_reference_number}{self.plot_size}{self.achievement}{self.po_id}{self.name_of_po}{self.phone_number}{self.mne_id}" 
	self.code = code

	if self.district:
		district = cocoaDistrict.objects.get(district=self.district)
		self.districtTbl_foreignkey = district

	if self.po_id:
		staff = staffTbl.objects.get(staffid=self.po_id)
		self.staffTbl_foreignkey = staff
	return super(specialprojectfarmsTbl, self).save()


class odkfarmsvalidationTbl(timeStamp):
	poid=models.CharField(max_length=2540, blank=True, null=True)
	po_name=models.CharField(max_length=2540, blank=True, null=True)
	po_phone=models.CharField(max_length=2540, blank=True, null=True)
	farm_status=models.CharField(max_length=2540, blank=True, null=True)
	farm_ref=models.CharField(max_length=2540, blank=True, null=True)
	farmer_name=models.CharField(max_length=2540, blank=True, null=True)
	farm_loc=models.CharField(max_length=2540, blank=True, null=True)
	farm_size=models.FloatField(blank=True, null=True)
	farm_sector=models.IntegerField(blank=True, null=True)
	coordinates_lng=models.FloatField(blank=True, null=True)
	coordinates_lat=models.FloatField(blank=True, null=True)
	accuracy=models.CharField(max_length=2540, blank=True, null=True)
	ex_video_widget=models.FileField(upload_to="odkvalidation",max_length=2540, blank=True, null=True)
	plantain_alive=models.IntegerField( blank=True, null=True)
	cocoa_alive=models.IntegerField( blank=True, null=True)
	instanceID=models.CharField(max_length=2540, blank=True, null=True)
	submissionDate=models.DateTimeField(max_length=2540, blank=True, null=True)
	deviceId=models.CharField(max_length=2540, blank=True, null=True)
	code=models.CharField(max_length=3540, blank=True, null=True,unique=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	mne_validated =models.BooleanField(default=False)
	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		code = f"{self.instanceID}{self.deviceId}"
		self.code = code
		if self.poid:
			try:
				staff = staffTbl.objects.get(staffid=self.poid)
				self.staffTbl_foreignkey = staff
			except Exception as e:
				print(self.poid)
		return super(odkfarmsvalidationTbl, self).save()
	
	
class odkdailyreportingTbl(timeStamp):
	poid=models.CharField(max_length=2540, blank=True, null=True)
	po_name=models.CharField(max_length=2540, blank=True, null=True)
	po_phone=models.CharField(max_length=2540, blank=True, null=True)
	main_activity=models.CharField(max_length=2540, blank=True, null=True)
	farm_ref=models.CharField(max_length=2540, blank=True, null=True)
	farmer_name=models.CharField(max_length=2540, blank=True, null=True)
	farm_loc=models.CharField(max_length=2540, blank=True, null=True)
	farm_size=models.CharField(max_length=2540, blank=True, null=True)
	farm_sector=models.IntegerField(max_length=2540, blank=True, null=True)
	date_completion=models.DateField(max_length=2540, blank=True, null=True)
	ra_contractor=models.CharField(max_length=2540, blank=True, null=True)
	comments=models.CharField(max_length=2540, blank=True, null=True)
	instanceID=models.CharField(max_length=2540, blank=True, null=True)
	submissionDate=models.DateTimeField(max_length=2540, blank=True, null=True)
	deviceId=models.CharField(max_length=2540, blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)
	year =models.IntegerField( blank=True, null=True)
	round_weeding=models.CharField(max_length=2540, blank=True, null=True)
	delete_check=models.BooleanField(default=False, help_text="Only eidtable by Monitoring and Evaluation Officer ")
	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		code = f"{self.instanceID}{self.deviceId}"

		self.code = code
		if self.poid:
			try:
				staff = staffTbl.objects.get(staffid=self.poid)
				self.staffTbl_foreignkey = staff
			except Exception as e:
				print(self.poid)
		return super(odkdailyreportingTbl, self).save()


class allFarmqueryTbl(timeStamp):
	ranrt	=models.CharField(max_length=2540,)
	rp_ref	=models.CharField(max_length=2540)
	month	=models.CharField(max_length=2540)
	week	=models.IntegerField(max_length=2540)
	year	=models.IntegerField(max_length=2540,default=2024)
	region	=models.CharField(max_length=2540)
	district =models.CharField(max_length=2540)	
	sector  =models.IntegerField(max_length=2540)
	po_id	=models.CharField(max_length=2540)
	name_of_po =models.CharField(max_length=2540)
	completion_date =models.DateField(max_length=2540)
	farm_reference =models.CharField(max_length=2540)
	activity =models.CharField(max_length=2540)
	activity_code =models.CharField(max_length=2540)
	r_ref_and_act =models.CharField(max_length=2540)
	r_ref_and_act_code =models.CharField(max_length=2540)
	farm_size =models.FloatField(max_length=2540)
	districtTbl_foreignkey = models.ForeignKey(cocoaDistrict, on_delete=models.CASCADE,blank=True, null=True)
	code=models.CharField(max_length=3540, blank=True, null=True,unique=True)

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):

		code = f"{self.ranrt}{self.rp_ref}{self.month}{self.week}{self.region}{self.district}{self.sector}{self.po_id}{self.name_of_po}{self.completion_date}{self.r_ref_and_act}{self.r_ref_and_act_code}{self.farm_size}" 
		self.code = code

		if self.district:
			district = cocoaDistrict.objects.get(district=self.district)
			self.districtTbl_foreignkey = district
			
		return super(allFarmqueryTbl, self).save()
	

class staffFarmsAssignment(timeStamp):	
	joborder_foreignkey = models.OneToOneField(Joborder, on_delete=models.CASCADE,blank=True, null=True)
	staffTbl_foreignkey = models.ForeignKey(staffTbl, on_delete=models.CASCADE,blank=True, null=True)

	class Meta:
		verbose_name_plural = "Staff Farms Assignment"












#########################################################################################################################################################################################
# models.py
# models.py
from django.db import models
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

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
    
    # Parent field for creating hierarchy
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
    
    # Permission groups that can see this item
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
    
    def clean(self):
        """Validate the menu item structure"""
        # Prevent circular references
        if self.parent == self:
            raise ValidationError("A menu item cannot be its own parent.")
        
        # Check for circular hierarchy
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError("Circular hierarchy detected.")
                current = current.parent
    
    @property
    def is_top_level(self):
        """Check if this is a top-level menu item"""
        return self.parent is None
    
    @property
    def has_children(self):
        """Check if this item has child items"""
        return self.children.exists()
    
    @property
    def child_count(self):
        """Count of direct children"""
        return self.children.count()
    
    @property
    def level(self):
        """Get the depth/level of this item in the hierarchy"""
        if self.parent is None:
            return 0
        return self.parent.level + 1
    
    @property
    def breadcrumb(self):
        """Get breadcrumb trail from root to this item"""
        if self.parent:
            return self.parent.breadcrumb + [self]
        return [self]
    
    @property
    def full_path(self):
        """Get full path as string"""
        return " > ".join([item.display_name for item in self.breadcrumb])
    
    def get_descendants(self, include_self=False):
        """Get all descendants of this menu item"""
        descendants = []
        
        def collect_descendants(item):
            for child in item.children.all():
                descendants.append(child)
                collect_descendants(child)
        
        if include_self:
            descendants.append(self)
        collect_descendants(self)
        
        return descendants
    
    def get_ancestors(self, include_self=False):
        """Get all ancestors of this menu item"""
        ancestors = []
        current = self
        
        if include_self:
            ancestors.append(self)
        
        while current.parent:
            ancestors.insert(0, current.parent)
            current = current.parent
        
        return ancestors
    
    def save(self, *args, **kwargs):
        self.clean()  # Validate before saving
        super().save(*args, **kwargs)

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
        # Ensure only one active configuration exists
        if self.is_active:
            SidebarConfiguration.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)