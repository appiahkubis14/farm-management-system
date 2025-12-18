from django.shortcuts import render
from backend.models import *
# Create your views here.
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.views.decorators.csrf import csrf_protect,csrf_exempt
from django.http import HttpResponseRedirect, JsonResponse,HttpResponse
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import authenticate,login as Login,logout as Logout
from django.contrib import messages
import json
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.contrib.auth.models import User
import base64
import io
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q, Value, F, ExpressionWrapper,Sum
from backend.decorators.decorator import usergroup
import datetime
from django.contrib.gis.geos import Polygon,Point


def decodeDesignImage(data):
	try:
		data = base64.b64decode(data.encode('UTF-8'))
		buf = io.BytesIO(data)
		img = Image.open(buf)
		return img
	except:
		return None




def saveimage(image, imgname):
	img = decodeDesignImage(image)
	img_io = io.BytesIO()
	img.save(img_io, format='PNG')
	data= InMemoryUploadedFile(img_io, field_name=None, name=str(imgname)+".jpg", content_type='image/jpeg', size=img_io.tell, charset=None)
	return data
	
def checkTitle(text):
	if text :
		return text.title()
	else : 
		return text

# APIS For mobile App 

@method_decorator(csrf_exempt, name='dispatch')
class fetchfarmsView(View):
	def post(self, request):	
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		userid= data["userid"]

		dist = districtStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).districtTbl_foreignkey.id

		# if data["userid"] :
		# 	districts = cocoaDistrict.objects.get(id=dist)
		# else:
		# 	districts = cocoaDistrict.objects.all()

		# print(dist)

		farms = FarmdetailsTbl.objects.filter(districtTbl_foreignkey=dist)[:300]
		data = []

		for farm in farms:
			try:
				eok={}
				eok["farm_code"]=farm.id
				eok["farm_id"]=farm.farm_reference
				eok["farmer_nam"]=checkTitle(farm.farmername)
				eok["district_id"]=farm.districtTbl_foreignkey.id
				eok["district_name"]=checkTitle(farm.districtTbl_foreignkey.district)
				eok["region_id"]=farm.districtTbl_foreignkey.reg_code.reg_code
				eok["region_name"]=checkTitle(farm.districtTbl_foreignkey.reg_code.region)
				# if farm.geom:
				eok["farm_size"]= farm.farm_size
				data.append(eok)
				status["status"] =  True
				status["msg"]: "Success!"
			except Exception as e:
				continue

		status["data"] = data

		return JsonResponse(status, safe=False)



@method_decorator(csrf_exempt, name='dispatch')
class fetchRehabassistantsView(View):
	def post(self, request):	
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		userid= data["userid"]

		dist = districtStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).districtTbl_foreignkey.id

		Rehabs = rehabassistantsTbl.objects.filter(districtTbl_foreignkey=dist)
		data = []
		domain = "https://cocoa-monitor-static.s3.amazonaws.com/media"
		# print(domain)
		if Rehabs:
			for rehab in Rehabs:
				eok={}
				eok["rehab_code"]=rehab.id
				eok["rehab_name"]=f'{rehab.name.title()}'
				eok["district_id"]=rehab.districtTbl_foreignkey.id
				eok["district_name"]=rehab.districtTbl_foreignkey.district.title()
				eok["region_id"]=rehab.districtTbl_foreignkey.reg_code.reg_code
				eok["region_name"]=rehab.districtTbl_foreignkey.reg_code.region.title()
				eok["designation"]=rehab.designation
				if rehab.photo_staff:
					eok["image"]=f'{domain}/{str(rehab.photo_staff)}'
				else:
					eok["image"]=str(rehab.photo_staff)
				eok["staff_id"]=rehab.staff_code
				eok["phone_number"]=rehab.phone_number
				eok["salary_bank_name"]=rehab.salary_bank_name
				eok["bank_account_number"]=rehab.bank_account_number
				eok["ssnit_number"]=rehab.ssnit_number
		
				data.append(eok)
	
		if data:
			status["status"] =  True
			status["data"] = data
		return JsonResponse(status, safe=False)



def fetchactivitiesView(request):	
	status ={}
	status["status"] =False
	activities = Activities.objects.all()
	data = []

	for active in activities:
		eok={}
		eok["code"]=active.id
		eok["main_activity"]=active.main_activity
		eok["sub_activity"]=active.sub_activity.title()
		eok["required_equipment"]=active.required_equipment
		data.append(eok)
	
	if data:
		status["status"] =  True
		status["data"] = data
	return JsonResponse(status, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class fetchregionDistrictsView(View):
	def post(self, request):
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		dist = districtStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).districtTbl_foreignkey.id

		if data["userid"] :
			districts = cocoaDistrict.objects.filter(id=dist)
		else:
			districts = cocoaDistrict.objects.all()
		data = []

		for district in districts:
			eok={}
			eok["district_id"]=district.id
			eok["district_name"]=district.district.title()
			eok["region_id"]=district.reg_code.reg_code
			eok["region_name"]=district.reg_code.region.title()
			data.append(eok)
		
		if data:
			status["status"] =  True
			status["data"] = data
		return JsonResponse(status, safe=False)





@method_decorator(csrf_exempt, name='dispatch')
class loginmobileView(View):
	def post(self, request):
		try:
			data = json.loads(request.body)
			status ={}
			status["status"] =False

			if data["telephone"] :
				if staffTbl.objects.filter(contact=data["telephone"]).exists():
					staff= staffTbl.objects.filter(contact=data["telephone"]).first()
					status["status"] =  1
					status["msg"] = "Login successful"
					status["data"] ={
					"first_name" :f'{staff.first_name.title()}',
					"last_name" :f'{staff.last_name.title()}',
					"user_id" :f'{staff.id}',
					# "designation" :f'{staff.designation}',
					"group" : f'{staff.designation.name}'
					}

				else:
					status["status"] =  0
					status["msg"] =  "Login unsuccessful!"
					status["data"] ={
					"user" :'',
					"group" : ''
					}
			else:
				status["status"] =  0
				status["msg"] =  "Login unsuccessful!"
				status["data"] ={
				"user" :'',
				"group" : ''
				}

		except Exception as e:
			raise e
			status["status"] =  0
			status["msg"] =  "Error Occured!"
			status["data"] =str(e),
		return JsonResponse(status, safe=False)




@method_decorator(csrf_exempt, name='dispatch')
class saveregistrationView(View):
	def post(self, request):
		status ={}
		status["status"] = 0
		try:
			data = json.loads(request.body)
			name = data["name"]
			gender = data["gender"]
			contact = data["contact"]
			dob = data["dob"]
			designation = data["designation"]
			district = data["district"]
			uid = data["uid"]
			if district :
				district = cocoaDistrict.objects.get(id=district)
		
			if name!="" and contact!="" and dob!="" and designation!="" :
				# if designation == "Project Officer" :
				# 	if not staffTbl.objects.filter(uid=uid).exists():
				# 		staffobj, staffcreated = staffTbl.objects.get_or_create(
				# 			contact= contact,
				# 		    defaults={
				# 		    # "user" :"",
				# 		    "first_name":fname,
				# 			"last_name":lname,
				# 			"gender":gender,
				# 			"dob":dob,
				# 			"contact":contact,
				# 			"designation":groupTbl.objects.get(name=designation) ,
				# 			"email_address":email,
				# 			"uid":uid
				# 		    },
				# 		  )
				# 		if staffcreated: 
				# 			if district :
				# 				dist_obj, dist_created = districtStaffTbl.objects.get_or_create(districtTbl_foreignkey=district,staffTbl_foreignkey=staffobj)
				# 				if dist_created:
				# 					status["status"] =  1
				# 					status["msg"] =  "successful saved"
				# 					status["data"] ={
				# 					# "user" :'',
				# 					# "group" : ''
				# 					}
				# 				else:
				# 					if dist_obj:
				# 						status["status"] =  0
				# 						status["msg"] =  "User exist"
				# 						status["data"] ={
				# 						# "user" :'',
				# 						# "group" : ''
				# 						}
				# 		else:
				# 			if staffobj:
				# 				status["status"] =  0
				# 				status["msg"] =  "User exist"
				# 				status["data"] ={
				# 				# "user" :'',
				# 				# "group" : ''
				# 				}
				# 	else:
				# 		status["status"] =  2
				# 		status["msg"] =  "record exist"
				# 		status["data"] = uid
				# elif designation == "Rehab Assistant" or designation == "Rehab Technician":
				if not rehabassistantsTbl.objects.filter(uid=uid).exists():
					getstaff = staffTbl.objects.get(id=data["agent"])
					if data["photo_staff"] :
						photo_staff =saveimage(data["photo_staff"], contact) 
					else:
						photo_staff =data["photo_staff"] 
					
					
					gender = data["gender"]
					# phone_number = data["phone_number"]
					salary_bank_name = data["salary_bank_name"]
					bank_branch = data["bank_branch"]
					bank_account_number = data["bank_account_number"]
					dob = data["dob"]
					ssnit_number = data["ssnit_number"]
					designation = data["designation"]

					rehabobj, rehab_created = rehabassistantsTbl.objects.get_or_create(
						phone_number= contact,
						defaults={
						"name":name,
						"photo_staff":photo_staff,
						"phone_number":contact,
						"salary_bank_name":salary_bank_name,
						"bank_branch":bank_branch,
						"bank_account_number":bank_account_number,
						"ssnit_number":ssnit_number,
						"dob":dob,
						"districtTbl_foreignkey": district,
						"uid":uid,
						"staffTbl_foreignkey":getstaff,
						"gender":gender,
						"designation":designation
												
						},
						)

					if rehab_created:
						status["status"] =  1
						status["msg"] =  "Successful Saved !!"
						status["data"] ={
						
						}

					else:
						if rehabobj:
							status["status"] = 0
							status["msg"] =  "User exist"


				

				else:
					status["status"] =  2
					status["msg"] =  "record exist"
					status["data"] = uid
					# else :
					# 	if staffobj :
					# 		status["status"] =  False
					# 		status["msg"] =  "User exist",
					# 		# status["data"] ={
					# 		# "user" :'',
					# 		# "group" : ''
					# 		# }

				# else:
				# 	status["status"] =  0
				# 	status["msg"] =  "Error Occured!"
					
					# status["data"] ={
					# "user" :'',
					# "group" : ''
					# }

		except Exception as e:
			raise e
			status["status"] =  0
			status["msg"] =  "Error Occured!7777"
			status["data"] =str(e),
		return JsonResponse(status, safe=False)




@method_decorator(csrf_exempt, name='dispatch')
class saveraAssignmentView(View):
	def post(self, request):
		status ={}
		status["status"] = 0
		try:
			data = json.loads(request.body)
			
			farm = data["farmid"]
			activity= data["activity"]
			ralist = json.loads(data["rehab_assistants"])
			assigned_date = data["assigned_date"]
			uid = data["uid"]
			staff = data["agent"]

			getstaff =staffTbl.objects.get(id=staff) 

			if not rehabassistantsAssignmentTbl.objects.filter(uid=uid).exists():
				if farm!="" and ralist!="" :

					for ra in ralist:
						rehabobj, rehab_created = rehabassistantsAssignmentTbl.objects.get_or_create(
							farmTbl_foreignkey=farm,
							rehabassistantsTbl_foreignkey=ra,
							activity=activity,
						    defaults={
						  
						    "farmTbl_foreignkey":Farms.objects.get(id=farm),
							"rehabassistantsTbl_foreignkey":rehabassistantsTbl.objects.get(id=ra),
							"activity":Activities.objects.get(id=activity),
							"assigned_date":assigned_date,
							"uid":uid,
							"staffTbl_foreignkey":getstaff
						    },
						  )

					if rehab_created:
						status["status"] =  1
						status["msg"] =  "Successful Saved !!"
						status["data"] ={
						
						}

					else:
						if rehabobj:
							status["status"] = 0
							status["msg"] =  "User exist"
				else:
					status["status"] =  0
					status["msg"] =  "Error Occured!",
					# status["data"] ={
					# "user" :'',
					# "group" : ''
					# }

			else:
				status["status"] =  2
				status["msg"] =  "record exist",
				status["data"] = uid


		except Exception as e:
			raise e
			status["status"] =  0
			status["msg"] =  "Error Occured!",
			status["data"] =str(e),
		return JsonResponse(status, safe=False)









@method_decorator(csrf_exempt, name='dispatch')
class saveMonitoringformView(View):
	def post(self, request):
		status ={}
		status["status"] = 0
		try:
			data = json.loads(request.body)
			staff_contact= data["agent"]

			
			
			farmTbl_foreignkey= data["farmTbl_foreignkey"]
			activity= data["activity"]
			monitoring_date= data["monitoring_date"]
			no_rehab_assistants= data["no_rehab_assistants"]
			original_farm_size= data["original_farm_size"]
			area_covered_ha= data["area_covered_ha"]
			remark= data["remark"]
			lat= data["lat"]
			lng= data["lng"]
			tstatus = data["status"]
			accuracy= data["accuracy"]
			if data["current_farm_pic"]:
				current_farm_pic=saveimage(data["current_farm_pic"], staff_contact) 
			else:
				current_farm_pic=""

			ralist = data["rehab_assistants"]
			fuel_oil = data["fuel_oil"]
			uid = data["uid"]
			
			if fuel_oil["quantity_ltr"] and fuel_oil["area"]:
				try:
					rate = round (fuel_oil["quantity_ltr"]/fuel_oil["area"],3)
				except Exception as e:
					rate=0
				
			else:
				rate=0

			# print(activity)
			

			act=Activities.objects.get(id=int(activity))
			if not weeklyMontoringTbl.objects.filter(uid=uid).exists():

				if farmTbl_foreignkey!="" and ralist!="" :

					# cycle= weeklyMontoringTbl.objects.filter(monitoring_date__year=monitoring_date[:4],activity= act ,farmTbl_foreignkey=farmTbl_foreignkey).latest("monitoring_date").weeddingcycle  
					# if weeklyMontoringTbl.objects.filter(monitoring_date__year=monitoring_date[:4],activity= act ,farmTbl_foreignkey=farmTbl_foreignkey,status="Completed").count()>0:
					# 	cycle = weeklyMontoringTbl.objects.filter(monitoring_date__year=monitoring_date[:4],activity= act ,farmTbl_foreignkey=farmTbl_foreignkey).latest("monitoring_date").weeddingcycle + 1
					
					weekmonitorobj, weekmonitor_created = weeklyMontoringTbl.objects.get_or_create(
						farmTbl_foreignkey=FarmdetailsTbl.objects.get(id=farmTbl_foreignkey),
						activity= act ,
						uid=uid,
						monitoring_date=monitoring_date,
						no_rehab_assistants=no_rehab_assistants,
						original_farm_size=original_farm_size,
						area_covered_ha=area_covered_ha,
						remark=remark,
						lat=lat,
						lng=lng,
						accuracy=accuracy,
						status=tstatus,
						current_farm_pic=current_farm_pic,
					    staffTbl_foreignkey=staffTbl.objects.get(id = staff_contact),

					    date_purchased=fuel_oil["date_purchased"],
						date=fuel_oil["date"],
						qty_purchased=fuel_oil["qty_purchased"],
						name_operator_receiving=fuel_oil["name_operator_receiving"],
						quantity_ltr=fuel_oil["quantity_ltr"],
						red_oil_ltr=fuel_oil["red_oil_ltr"],
						engine_oil_ltr=fuel_oil["engine_oil_ltr"],
						rate=rate,
						remarks=fuel_oil["remarks"],
						# weeddingcycle=cycle

					  )

					if weekmonitor_created:
						if ralist:
							for rehab in ralist:
								rehabobj,rehab_created =weeklyMontoringrehabassistTbl.objects.get_or_create(
											weeklyMontoringTbl_foreignkey=weekmonitorobj,
											rehabassistantsTbl_foreignkey=rehabassistantsTbl.objects.get(id=rehab["rehab_asistant"]),
											area_covered_ha=rehab["area_covered_ha"],

										)

						# if fuel_oil:
						# 	if fuel_oil["quantity_ltr"] and fuel_oil["area"]:
						# 		rate = round (fuel_oil["quantity_ltr"]/fuel_oil["area"],3)
						# 	else:
						# 		rate=0
						# 	fuel_oilobj,fuel_oil_created =fuelMontoringTbl.objects.get_or_create(
						# 				weeklyMontoringTbl_foreignkey=weekmonitorobj,
						# 				date_purchased=fuel_oil["date_purchased"],
						# 				date=fuel_oil["date"],
						# 				qty_purchased=fuel_oil["qty_purchased"],
						# 				name_operator_receiving=fuel_oil["name_operator_receiving"],
						# 				quantity_ltr=fuel_oil["quantity_ltr"],
						# 				red_oil_ltr=fuel_oil["red_oil_ltr"],
						# 				engine_oil_ltr=fuel_oil["engine_oil_ltr"],
						# 				rate=rate,
						# 				remarks=fuel_oil["remarks"]

						# 			)


						status["status"] =  1
						status["msg"] =  "Successful Saved !!"
						status["data"] ={
						
						}
 
					else:
						status["status"] = 0
						status["msg"] =  "data exist"
				else:
					status["status"] =  0
					status["msg"] =  "Error Occured!"

			else:
				status["status"] =  2
				status["msg"] =  "record exist"
				status["data"] = uid

		except Exception as e:
			raise e
			status["status"] =  0
			status["msg"] =  "Error Occured!"
			status["data"] =str(e)
		return JsonResponse(status, safe=False)





@method_decorator(csrf_exempt, name='dispatch')
class updatefirebaseView(View):
	def post(self, request):
		status ={}
		status["status"] = 0
		try:
			data = json.loads(request.body)
			token = data["token"]
			userid= data["userid"]
			getstaff =staffTbl.objects.get(id=userid,delete_field="no") 
			obj, created = staffTbl.objects.update_or_create(
				id=userid,
			    defaults={
			    "id":userid,
				"fbase_code":token
			    },
			  )

			if created:
				status["status"] =  0
				status["msg"] =  "Successful Saved !!"
				status["data"] ={
				
				}

			else:
				if obj:
					status["status"] = 1
					status["msg"] =  "Successful Saved !!"
				else:
					status["status"] =  0
					status["msg"] =  "Error Occured!",

		except Exception as e:
			raise e
			status["status"] =  0
			status["msg"] =  "Error Occured!",
			status["data"] =str(e),
		return JsonResponse(status, safe=False)



@method_decorator(csrf_exempt, name='dispatch')
class fetchfarmstatusView(View):
	def post(self, request):

		status ={}
		status["status"] =False

		data = json.loads(request.body)
		userid= data["userid"]

		dist = districtStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).districtTbl_foreignkey.id
		Farms = FarmdetailsTbl.objects.filter(districtTbl_foreignkey=dist)
		data = []

		today = datetime.date.today()
		current_year = today.year
		current_month = today.month

		for farm in Farms:

			activity = weeklyMontoringTbl.objects.filter(farmTbl_foreignkey=farm.id,monitoring_date__year=current_year, monitoring_date__month=current_month, delete_field="no").distinct('activity').values_list('activity', flat=True)
			for act in activity:
				# print(act)
				eok={}
				area_covered = weeklyMontoringTbl.objects.filter(farmTbl_foreignkey=farm.id,activity=act,monitoring_date__year=current_year, monitoring_date__month=current_month,delete_field="no").aggregate(Sum('area_covered_ha'))['area_covered_ha__sum']
				tstatus = weeklyMontoringTbl.objects.filter(farmTbl_foreignkey=farm.id,activity=act,monitoring_date__year=current_year, monitoring_date__month=current_month,delete_field="no").latest("monitoring_date").status
			
				eok["farmid"]=farm.farm_reference
				eok["location"]=farm.location.title()
				eok["activity"]=Activities.objects.get(id=act).sub_activity
				eok["area"]=farm.farm_size
				eok["area_covered"]=area_covered
				eok["farmer_name"]=farm.farmername.title()
				eok["status"]=tstatus
				datetime_object = datetime.datetime.strptime(str(current_month), "%m")
				eok["month"]= datetime_object.strftime("%B")
				eok["year"]=current_year

				data.append(eok)
		status["status"] =  True
		status["msg"] =  "Success"
		status["data"] = data

		return JsonResponse(status, safe=False)

from django.contrib.gis.gdal import SpatialReference, CoordTransform


@method_decorator(csrf_exempt, name='dispatch')
class fetchpoAssignedfarmsView(View):
	def post(self, request):
		status ={}
		data = json.loads(request.body)
		userid= data["userid"]
		status["status"] =False
		dist = districtStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).districtTbl_foreignkey.id
		Farm = Farms.objects.filter(farmdetailstbl__districtTbl_foreignkey=dist)[:200]
		data = []
		gcoord = SpatialReference(32630)
		mycoord = SpatialReference(4326)
		trans = CoordTransform(gcoord, mycoord)

		for fam in Farm:
			eok={}
			#print(fam.geom.transform(trans,clone=True))
			if fam.geom:
				eok["farm_boundary"]= fam.geom.geojson
			else:
				eok["farm_boundary"]=""
			eok["farmername"]= fam.farmer_nam
			eok["location"]= fam.farm_loc
			eok["farm_reference"]= fam.farm_id
			if fam.farm_size:
				eok["farm_size"]= f"{fam.farm_size} Ha"
			else:
				eok["farm_size"]= 0

			data.append(eok)
		status["status"] =  True
		status["msg"] =  "Success"
		status["data"] = data

		return JsonResponse(status, safe=False)




@method_decorator(csrf_exempt, name='dispatch')
class outbreakFarmView(View):
	def post(self, request):
		status ={}
		status["status"] = 0
		try:
			data = json.loads(request.body)
			
			outbreaks_foreignkey = data["outbreaks_foreignkey"]
			farmboundary = data["farmboundary"]
			farm_location = ""
			farmer_name = data["farmer_name"]
			farmer_age = data["farmer_age"]
			id_type = data["id_type"]
			id_number = data["id_number"]
			farmer_contact = data["farmer_contact"]
			cocoa_type = data["cocoa_type"]
			age_class = data["age_class"]
			farm_area = data["farm_area"]
			communitytbl_foreignkey = data["communitytbl_foreignkey"]
			agent= data["agent"]
			inspection_date= data["inspection_date"]
			uid= data["uid"]
			
			aa=[]
			for points in data["farmboundary"]:
				aa.append((points["longitude"],points["latitude"]))

			farm_geom = Polygon(tuple(aa) )

			# print(farm_geom)
			dist=communityTbl.objects.get(id=communitytbl_foreignkey).districtTbl_foreignkey.district
			district = cocoaDistrict.objects.get(district=dist)
			staff=outbreakFarms.objects.filter(temp_code__startswith= f"ACL/{district.reg_code.reg_code}/{district.district_code}").count() + 1 
			num="{0:0>3}".format(staff)
			code = f"ACL/{district.reg_code.reg_code}/{district.district_code}/{num}"
			
			if  outbreakFarms.objects.filter(temp_code= code).exists():
				staff = staff + 2
				num="{0:0>3}".format(staff)
				code = f"ACL/{district.reg_code.reg_code}/{district.district_code}/{num}"
			
			obj, created = outbreakFarms.objects.get_or_create(
				uid=uid,
				inspection_date=inspection_date,
				staffTbl_foreignkey=staffTbl.objects.get(id = agent),
				outbreaks_foreignkey = outBreaks.objects.get(id=outbreaks_foreignkey),
				farmboundary=str(aa),
				farm_geom=farm_geom,
				farm_location=farm_location,
				farmer_name=farmer_name,
				farmer_age=farmer_age,
				id_type=id_type,
				id_number=id_number,
				farmer_contact=farmer_contact,
				cocoa_type = cocoa_type,
				age_class = age_class,
				farm_area = farm_area,
				communitytbl_foreignkey = communityTbl.objects.get(id=communitytbl_foreignkey),
				temp_code=code,
				

			  )

			if created:
				status["status"] =  1
				status["msg"] =  "Successful Saved !!"
				status["data"] ={

				}

			else:
				if obj:
					status["status"] = 1
					status["msg"] =  "Successful Saved !!"
				else:
					status["status"] =  0
					status["msg"] =  "Error Occured!",

		except Exception as e:
			raise e
			status["status"] =  0
			status["msg"] =  "Error Occured!",
			status["data"] =str(e),
		return JsonResponse(status, safe=False)



# fetch all outbreaks
@method_decorator(csrf_exempt, name='dispatch')
class fetchoutbreakView(View):
	def post(self, request):	
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		userid= data["userid"]

		dist = districtStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).districtTbl_foreignkey.id
	
		approvedobs = approvedobsTbl.objects.filter(districtTbl_foreignkey=dist).values_list("outbreakid",flat=True)
	
		farms = outBreaks.objects.filter(ob_id__in=approvedobs,geom__isnull=False)
		
		asd=[]
		for farm in farms:
			eok={}
			if farm.geom:
				eok["ob_boundary"]=farm.geom.geojson
			else:
				eok["ob_boundary"]=""
			eok["ob_id"]=farm.id
			eok["ob_code"]=farm.ob_id
			eok["ob_size"]=farm.ob_size
			if farm.districtTbl_foreignkey:
				eok["district_id"]=farm.districtTbl_foreignkey.id
				eok["district_name"]=farm.districtTbl_foreignkey.district.title()
				eok["region_id"]=farm.districtTbl_foreignkey.reg_code.reg_code
				eok["region_name"]=farm.districtTbl_foreignkey.reg_code.region.title()
				# if farm.geom:
				
			asd.append(eok)
			status["status"] =  True
			status["msg"]: "Success!"

		status["data"] = asd

		return JsonResponse(status, safe=False)




# fetch all outbreaks
@method_decorator(csrf_exempt, name='dispatch')
class fetchcommunityTblView(View):
	def post(self, request):	
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		userid= data["userid"]
		dist = districtStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).districtTbl_foreignkey.id
		farms = communityTbl.objects.filter(districtTbl_foreignkey=dist)
		data = []

		for farm in farms:
			eok={}
			eok["operational_area"]=farm.Operational_area
			eok["community_id"]=farm.id
			eok["community"]=farm.community
			eok["district_id"]=farm.districtTbl_foreignkey.id
			eok["district_name"]=farm.districtTbl_foreignkey.district.title()
			eok["region_id"]=farm.districtTbl_foreignkey.reg_code.reg_code
			eok["region_name"]=farm.districtTbl_foreignkey.reg_code.region.title()
			
			data.append(eok)
			status["status"] =  True
			status["msg"]: "Success!"

		status["data"] = data

		return JsonResponse(status, safe=False)




# fetch all cocotype
@method_decorator(csrf_exempt, name='dispatch')
class fetchcocoatypeTblView(View):
	def post(self, request):	
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		# userid= data["userid"]

		farms = cocoatypeTbl.objects.all()
		data = []

		for farm in farms:
			eok={}
			eok["name"]=farm.name
			
			
			data.append(eok)
			status["status"] =  True
			status["msg"]: "Success!"

		status["data"] = data

		return JsonResponse(status, safe=False)


# fetch all cocoa class
@method_decorator(csrf_exempt, name='dispatch')
class cocoaageclassTblView(View):
	def post(self, request):	
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		# userid= data["userid"]

		farms = cocoaageclassTbl.objects.all()
		data = []

		for farm in farms:
			eok={}
			eok["name"]=farm.classtype
			
			
			data.append(eok)
			status["status"] =  True
			status["msg"]: "Success!"

		status["data"] = data

		return JsonResponse(status, safe=False)



# fetch all outbreaks demarcated Farms 
@method_decorator(csrf_exempt, name='dispatch')
class fetchdemarcartedFarmsTblView(View):
	def post(self, request):	
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		userid= data["userid"]

		farms = communityTbl.objects.all()
		data = []

		for farm in farms:
			eok={}
			eok["operational_area"]=farm.Operational_area
			eok["community_id"]=farm.id
			eok["community"]=farm.community
			eok["district_id"]=farm.districtTbl_foreignkey.id
			eok["district_name"]=farm.districtTbl_foreignkey.district.title()
			eok["region_id"]=farm.districtTbl_foreignkey.reg_code.reg_code
			eok["region_name"]=farm.districtTbl_foreignkey.reg_code.region.title()
			
			data.append(eok)
			status["status"] =  True
			status["msg"]: "Success!"

		status["data"] = data

		return JsonResponse(status, safe=False)



# fetch all outbreaks
@method_decorator(csrf_exempt, name='dispatch')
class fetchoutbreakCSV(View):
	def post(self, request):	
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		userid= data["userid"]
		startdate= data["start_date"]
		enddate= data["end_date"]

		query = dict()
		if startdate and enddate:
			query.update(inspection_date__range =[startdate, enddate])
		if startdate and enddate=="" :
			query.update(inspection_date__gte=startdate)
		if enddate and startdate=="":
			query.update(inspection_date__lte=enddate)

		dist = districtStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).districtTbl_foreignkey.id
		# farms = outbreakFarms.objects.filter(**query,outbreaks_foreignkey__districtTbl_foreignkey=dist)
		
		farms = outbreakFarms.objects.filter(**query,staffTbl_foreignkey=userid)
		data = []

		for farm in farms:
			eok={}
			eok["outbreaks_id"]=farm.outbreaks_foreignkey.ob_id
			eok["farm_location"]=farm.farm_location
			eok["farmer_name"]=farm.farmer_name
			eok["farmer_age"]=farm.farmer_age
			eok["id_type"]=farm.id_type
			eok["id_number"]=farm.id_number
			eok["farmer_contact"]=farm.farmer_contact
			eok["cocoa_type"]=farm.cocoa_type
			eok["age_class"]=farm.age_class
			eok["farm_area"]=farm.farm_area
			eok["communitytbl"]=farm.communitytbl_foreignkey.community
			eok["inspection_date"]=farm.inspection_date
			eok["temp_code"]=farm.temp_code
			data.append(eok)
			status["status"] =  True
			status["msg"]: "Success!"

		status["data"] = data

		return JsonResponse(status, safe=False)




# fetch all outbreaks demarcated Farms 
@method_decorator(csrf_exempt, name='dispatch')
class fetchallRAView(View):
	def post(self, request):	
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		userid= data["userid"]
		dist = districtStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).districtTbl_foreignkey.id
		# print(dist)
		rehabs = rehabassistantsTbl.objects.filter(districtTbl_foreignkey=dist)

		data = []

		for rehab in rehabs:
			eok={}
			eok["image"]=str(rehab.photo_staff)
			eok["name"]=rehab.name
			eok["staff_code"]=rehab.staff_code
			eok["phone_number"]=rehab.phone_number
			eok["salary_bank_name"]=rehab.bank_branch
			eok["bank_account_number"]=rehab.bank_account_number
			eok["gender"]=rehab.gender
			eok["ssnit_number"]=rehab.ssnit_number
			eok["district"]=rehab.districtTbl_foreignkey.district
			eok["district_id"]=rehab.districtTbl_foreignkey.id
			eok["region_id"]=rehab.districtTbl_foreignkey.reg_code.region
			eok["dob"]=rehab.dob

			data.append(eok)
			status["status"] =  True
			status["msg"]: "Success!"

		status["data"] = data

		return JsonResponse(status, safe=False)






@method_decorator(csrf_exempt, name='dispatch')
class savepomonitoringView(View):
	def post(self, request):
		status ={}
		status["status"] = 0
		try:
			data = json.loads(request.body)
			userid= data["userid"]
			# staffTbl_foreignkey= data["staffTbl_foreignkey"]
			lat= data["lat"]
			lng= data["lng"]
			inspection_date= data["inspection_date"]
			accuracy= data["accuracy"]
			uid=data["uid"]

			getstaff =staffTbl.objects.get(id=userid,delete_field="no") 
	

		
			obj, created = posRoutemonitoring.objects.get_or_create(
			
				staffTbl_foreignkey=getstaff, 
				lat=lat,
				lng=lng,
				inspection_date=inspection_date,
				accuracy=accuracy,
				uid=uid
			
			   
			  )

	
			if created:
				status["status"] =  1
				status["msg"] =  "Successful Saved !!"
				status["data"] ={
				
				}

			
			else :
				status["status"] = 2
				status["msg"] =  "Already exist !!"
		

		except Exception as e:
			raise e
			status["status"] =  0
			status["msg"] =  "Error Occured!",
			status["data"] =str(e),
		return JsonResponse(status, safe=False)





@method_decorator(csrf_exempt, name='dispatch')
class saveOBformView(View):
	def post(self, request):
		status ={}
		status["status"] = 0
		try:
			data = json.loads(request.body)
			uid = data["uid"]
			userid= data["agent"]
			farmTbl_foreignkey= data["farmTbl_foreignkey"]
			activity= data["activity"]
			monitoring_date= data["monitoring_date"]
			no_ras= data["no_rehab_assistants"]
			# no_rts= data["no_rts"]
			no_rts=""
			# area_covered_ha= data["area_covered_ha"]
			remark= data["remark"]
			lat= data["lat"]
			lng= data["lng"]
			status_activity = data["status"]
			accuracy= data["accuracy"]
			# contractor_name=data["contractor_name"]
			contractor_name=""
			# ob_id= data["ob_id"]
			total_workdone= data["area_covered_ha"]
			if data["current_farm_pic"]:
				current_farm_pic=saveimage(data["current_farm_pic"], uid) 
			else:
				current_farm_pic=""

			ralist = data["rehab_assistants"]
			
	

			act=Activities.objects.get(id=int(activity))
			if not weeklyMontoringTbl.objects.filter(uid=uid).exists():

				if farmTbl_foreignkey!="" and ralist!="" :

					obfarm =outbreakFarms.objects.get(id=farmTbl_foreignkey)

					weekmonitorobj, weekmonitor_created = weeklyobreportTbl.objects.get_or_create(
						uid=uid,
						staffTbl_foreignkey=staffTbl.objects.get(id = userid),
						monitoring_date = monitoring_date,
						district = obfarm.communitytbl_foreignkey.districtTbl_foreignkey.district,
						Operational_area= obfarm.communitytbl_foreignkey.Operational_area,
						community=obfarm.communitytbl_foreignkey.community,
						ob_id = obfarm.outbreaks_foreignkey.ob_id,
						farm_name=obfarm.farmer_name,
						farm_contact=obfarm.farmer_contact,
						farmer_ref_number=obfarm.temp_code,
						main_activity=act.main_activity,
						sub_activity=act.sub_activity,
						status_activity=status_activity,
						no_ras =no_ras,
						no_rts=no_rts,
						name_ras="",
						farm_size=obfarm.farm_area,
						total_workdone=total_workdone,
						remark=remark,
						contractor_name=contractor_name,
						districtTbl_foreignkey=obfarm.communitytbl_foreignkey.districtTbl_foreignkey,
						activity=act,
						current_farm_pic = current_farm_pic,
						lat=lat,
						lng=lng,
						accuracy =accuracy
					  )

					if weekmonitor_created:
						if ralist:
							for rehab in ralist:
								rehabobj,rehab_created =weeklyOBrehabassistTbl.objects.get_or_create(
											weeklyMontoringTbl_foreignkey=weekmonitorobj,
											rehabassistantsTbl_foreignkey=rehabassistantsTbl.objects.get(id=rehab["rehab_asistant"]),
											area_covered_ha=rehab["area_covered_ha"],

										)


						status["status"] =  1
						status["msg"] =  "Successful Saved !!"
						status["data"] ={
						
						}
 
					else:
						status["status"] = 0
						status["msg"] =  "data exist"
				else:
					status["status"] =  0
					status["msg"] =  "Error Occured!"

			else:
				status["status"] =  2
				status["msg"] =  "record exist"
				status["data"] = uid

		except Exception as e:
			raise e
			status["status"] =  0
			status["msg"] =  "Error Occured!"
			status["data"] =str(e)
		return JsonResponse(status, safe=False)





@method_decorator(csrf_exempt, name='dispatch')
class savemaintenancefuelView(View):
	def post(self, request):
		status ={}
		status["status"] = 0
		try:
			data = json.loads(request.body)
			userid= data["userid"]
			# staffTbl_foreignkey= data["staffTbl_foreignkey"]
			farmdetailstbl_foreignkey= data["farmdetailstbl_foreignkey"]
			date_received= data["date_received"]
			rehabassistantsTbl_foreignkey= data["rehabassistantsTbl_foreignkey"]
			fuel_ltr= data["fuel_ltr"]
			remarks=data["remarks"]
			uid=data["uid"]

			getstaff =staffTbl.objects.get(id=userid,delete_field="no") 

			obj, created = fuelMontoringTbl.objects.get_or_create(
				staffTbl_foreignkey=getstaff, 
				farmdetailstbl_foreignkey_id=farmdetailstbl_foreignkey,
				date_received=date_received,
				rehabassistantsTbl_foreignkey_id=rehabassistantsTbl_foreignkey,
				fuel_ltr=fuel_ltr,
				remarks=remarks,
				uid=uid
			   
			  )

			if created:
				status["status"] =  1
				status["msg"] =  "Successful Saved !!"
				status["data"] ={
				
				}

			else:
				if obj:
					status["status"] = 2
					status["msg"] =  "Already exist !!"
				else:
					status["status"] =  0
					status["msg"] =  "Error Occured!",

		except Exception as e:
			raise e
			status["status"] =  0
			status["msg"] =  "Error Occured!",
			status["data"] =str(e),
		return JsonResponse(status, safe=False)




@method_decorator(csrf_exempt, name='dispatch')
class saveobfuelView(View):
	def post(self, request):
		status ={}
		status["status"] = 0
		try:
			data = json.loads(request.body)
			userid= data["userid"]
			# staffTbl_foreignkey= data["staffTbl_foreignkey"]
			farmdetailstbl_foreignkey= data["farmdetailstbl_foreignkey"]
			date_received= data["date_received"]
			rehabassistantsTbl_foreignkey= data["rehabassistantsTbl_foreignkey"]
			fuel_ltr= data["fuel_ltr"]
			remarks=data["remarks"]
			uid=data["uid"]

			getstaff =staffTbl.objects.get(id=userid,delete_field="no") 

			obj, created = fuelMontoringobTbl.objects.get_or_create(
				staffTbl_foreignkey=getstaff, 
				farmdetailstbl_foreignkey_id=farmdetailstbl_foreignkey,
				date_received=date_received,
				rehabassistantsTbl_foreignkey_id=rehabassistantsTbl_foreignkey,
				fuel_ltr=fuel_ltr,
				remarks=remarks,
				uid=uid
				
			  )

			if created:
				status["status"] =  1
				status["msg"] =  "Successful Saved !!"
				status["data"] ={
				
				}

			else:
				if obj:
					status["status"] = 2
					status["msg"] =  "Already exist !!"
				else:
					status["status"] =  0
					status["msg"] =  "Error Occured!",

		except Exception as e:
			raise e
			status["status"] =  0
			status["msg"] =  "Error Occured!",
			status["data"] =str(e),
		return JsonResponse(status, safe=False)




# fetch all outbreaks
@method_decorator(csrf_exempt, name='dispatch')
class fetchoutbreaFarms(View):
	def post(self, request):	
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		userid= data["userid"]


		# farms = outbreakFarms.objects.filter(**query,outbreaks_foreignkey__districtTbl_foreignkey=dist)
		
		farms = outbreakFarms.objects.filter(staffTbl_foreignkey=userid)
		data = []

		for farm in farms:
			eok={}
			eok["farm_id"]=farm.id
			eok["outbreaks_id"]=farm.outbreaks_foreignkey.ob_id
			eok["farm_location"]=farm.farm_location
			eok["farmer_name"]=farm.farmer_name
			eok["farmer_age"]=farm.farmer_age
			eok["id_type"]=farm.id_type
			eok["id_number"]=farm.id_number
			eok["farmer_contact"]=farm.farmer_contact
			eok["cocoa_type"]=farm.cocoa_type
			eok["age_class"]=farm.age_class
			eok["farm_area"]=farm.farm_area
			eok["communitytbl"]=farm.communitytbl_foreignkey.community
			eok["inspection_date"]=farm.inspection_date
			eok["temp_code"]=farm.temp_code
			data.append(eok)
			status["status"] =  True
			status["msg"]: "Success!"

		status["data"] = data

		return JsonResponse(status, safe=False)




# fetch all Contractors
@method_decorator(csrf_exempt, name='dispatch')
class fetchcontractorView(View):
	def post(self, request):	
		status ={}
		status["status"] =False
		data = json.loads(request.body)
		userid= data["userid"]


		# farms = outbreakFarms.objects.filter(**query,outbreaks_foreignkey__districtTbl_foreignkey=dist)
		
		contractors = contractorsTbl.objects.all()
		data = []

		for cont in contractors:
			eok={}
			eok["farm_id"]=cont.id
			eok["contractor_name"]=cont.contractor_name
			eok["contact_person"]=cont.contact_person
			eok["address"]=cont.address
			eok["contact_number"]=cont.contact_number
			
			data.append(eok)
			status["status"] =  True
			status["msg"]: "Success!"

		status["data"] = data

		return JsonResponse(status, safe=False)






@method_decorator(csrf_exempt, name='dispatch')
class savefeedbackView(View):
	def post(self, request):
		status ={}
		status["status"] = 0
		try:
			data = json.loads(request.body)
			userid= data["userid"]
			title= data["title"]
			fedback= data["Feedback"]
			sent_date= data["sent_date"]
			uid=data["uid"]
			

			getstaff =staffTbl.objects.get(id=userid,delete_field="no") 

			obj, created = Feedback.objects.get_or_create(
				
				staffTbl_foreignkey=getstaff, 
				title=title,
				Feedback=fedback,
				sent_date=sent_date,
				uid=uid,
				
			   
			  )

			if created:
				status["status"] =  1
				status["msg"] =  "Successful Saved !!"
				status["data"] ={
				
				}

			else:
				if obj:
					status["status"] = 2
					status["msg"] =  "Already exist !!"
				else:
					status["status"] =  0
					status["msg"] =  "Error Occured!",

		except Exception as e:
			raise e
			status["status"] =  0
			status["msg"] =  "Error Occured!",
			status["data"] =str(e),
		return JsonResponse(status, safe=False)
