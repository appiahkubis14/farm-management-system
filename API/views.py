from django.shortcuts import render
from API.models import *
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
# from portal.decorators.decorator import usergroup
import datetime
from django.contrib.gis.geos import Polygon,Point
# views.py
from rest_framework.generics import ListAPIView
# from .serializers import rehabassistantsTblSerializer
# from portal.models import rehabassistantsTbl

# -*- coding: utf-8 -*-
from rest_framework import viewsets
from django.shortcuts import render
from .serializers import *
from datetime import date, timedelta
from API.models import *
from portal.models import *

def decodeDesignImage(data):
    try:
        data = base64.b64decode(data.encode('UTF-8'))
        buf = io.BytesIO(data)
        img = Image.open(buf)
        return img
    except:
        return None




# def saveimage(image, imgname):
#     img = decodeDesignImage(image)
#     img_io = io.BytesIO()
#     img.save(img_io, format='PNG')
#     data= InMemoryUploadedFile(img_io, field_name=None, name=str(imgname)+".jpg", content_type='image/jpeg', size=img_io.tell, charset=None)
#     return data





def saveimage(image, imgname):
    img = decodeDesignImage(image)
    img_io = io.BytesIO()

    if img is not None:
        img.save(img_io, format='PNG')
        img_io.seek(0)  # Reset buffer position to the beginning

        data = InMemoryUploadedFile(
            img_io,
            field_name=None,
            name=f"{imgname}.png",
            content_type='image/png',
            size=img_io.getbuffer().nbytes,  # Get the correct size
            charset=None
        )
        return data
    return None

def saveimageJPG(image, imgname):
    img = decodeDesignImage(image)
    img_io = io.BytesIO()
    print(img_io)
    print(img_io)
    print(img_io)
    img.save(img_io, format='PNG')
    data= InMemoryUploadedFile(img_io, field_name=None, name=str(imgname)+".jpg", content_type='image/jpeg', size=img_io.tell, charset=None)
    return data



def saveFile(image, imgname,format):
    
    img = decodeDesignImage(image)

    print(img)

    img_io = io.BytesIO()
    img.save(img_io, format=f'{format}')
    data= InMemoryUploadedFile(img_io, field_name=None, name=str(imgname)+ f".{format}", content_type='image/jpeg', size=img_io.tell, charset=None)
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
        sectorlist =sectorStaffassignment.objects.filter(staffTbl_foreignkey = data["userid"]).values_list("sector",flat=True)
        # dist = districtStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).districtTbl_foreignkey.id
        # sector__in = level["sector"]
     
        # import pandas as pd
        # ADS = FarmdetailsTbl.objects.filter(district='KADE').update(sector='23')
        # pandas_array = pd.Series(ADS)
        # df = pd.DataFrame({'Data': pandas_array})
        # df.to_excel('output.xlsx', index=False)

        # print(sectorlist)
       
        farms = FarmdetailsTbl.objects.filter(sector__in=sectorlist).defer("expunge","reason4expunge",'location','sector','region',"year_of_establishment")
        # print(farms.count())
        data = []

        for farm in farms:
            # print(farm.farm_reference)
            try:
                eok={}
                eok["farm_code"]=farm.id
                eok["farm_id"]=farm.farm_reference
                eok["farmer_nam"]=checkTitle(farm.farmername)
                eok["district_id"]=farm.districtTbl_foreignkey.id
                eok["district_name"]=checkTitle(farm.districtTbl_foreignkey.district)
                eok["region_id"]=farm.districtTbl_foreignkey.reg_code.reg_code
                eok["region_name"]=checkTitle(farm.districtTbl_foreignkey.reg_code.region)
                eok["farm_size"]= farm.farm_size
                data.append(eok)
                status["status"] =  True
                status["msg"] = "Success!"
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

        proj = projectStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).projectTbl_foreignkey.id

        Rehabs = rehabassistantsTbl.objects.filter(projectTbl_foreignkey=proj)
        data = []
        domain = "https://cocoa-monitor-static.s3.amazonaws.com/media"
        # print(domain)
        if Rehabs:
            for rehab in Rehabs:
                eok={}
                eok["rehab_code"]=rehab.id
                eok["rehab_name"]=f'{rehab.name.title()}'
                eok["project_id"]=rehab.projectTbl_foreignkey.id
                eok["project_name"]=rehab.projectTbl_foreignkey.name.title()
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
                if rehab.momo_account_name:
                    eok["momo_account_name"]=rehab.momo_account_name.title()
                else:
                    eok["momo_account_name"]= "Not Provided"
                eok["momo_number"]=rehab.momo_number
                if rehab.payment_option:
                    eok["payment_option"]=rehab.payment_option
                else:
                    eok["payment_option"]= "Not Provided"
                if rehab.staffTbl_foreignkey:
                    eok["po"]=f'{rehab.staffTbl_foreignkey.first_name.title()} {rehab.staffTbl_foreignkey.last_name.title()}'
                else:
                    eok["po"]='Not Assigned'
        
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
        dist = projectStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).projectTbl_foreignkey.id

        if data["userid"] :
            projects = cocoaDistrict.objects.filter(id=dist)
        else:
            projects = cocoaDistrict.objects.all()
        data = []

        for project in projects:
            eok={}
            eok["project_id"]=project.id
            eok["project_name"]=project.name
            # eok["region_id"]=project.reg_code.reg_code
            # eok["region_name"]=project.reg_code.region.title()
            data.append(eok)
        
        if data:
            status["status"] =  True
            status["data"] = data
        return JsonResponse(status, safe=False)





# @method_decorator(csrf_exempt, name='dispatch')
# class loginmobileView(View):
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             status ={}
#             status["status"] =False

#             if data["telephone"] :
#                 if staffTbl.objects.filter(contact=data["telephone"]).exists():
#                     staff= staffTbl.objects.filter(contact=data["telephone"]).first()
#                     print(staff.staffid)
#                     status["status"] =  1
#                     status["msg"] = "Login successful11"
#                     status["data"] ={
#                     "first_name" :f'{staff.first_name.title()}',
#                     "last_name" :f'{staff.last_name.title()}',
#                     "user_id" :f'{staff.id}',
#                     "staff_id" :f'{staff.staffid}',
#                     "group" : f'{staff.designation.name}'
#                     }

#                 else:
#                     status["status"] =  0
#                     status["msg"] =  "Login unsuccessful!"
#                     status["data"] ={
#                     "user" :'',
#                     "group" : ''
#                     }
#             else:
#                 status["status"] =  0
#                 status["msg"] =  "Login unsuccessful!"
#                 status["data"] ={
#                 "user" :'',
#                 "group" : ''
#                 }

#         except Exception as e:
#             raise e
#         return JsonResponse(status, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class loginmobileV2View(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {}
            status["status"] = False

            if data["telephone"]:
                if staffTbl.objects.filter(contact=data["telephone"], crmpassword=data["password"]).exists():
                    staff = staffTbl.objects.filter(contact=data["telephone"]).first()
                    
                    # Get assigned farms with optimized query
                    assigned_farms = projectStaffTbl.objects.filter(
                        staffTbl_foreignkey=staff.id
                    ).select_related('projectTbl_foreignkey')
                    
                    # Get all farm details in one query
                    project_id = [assignment.projectTbl_foreignkey.id for assignment in assigned_farms if assignment.projectTbl_foreignkey]
                    project_details = FarmdetailsTbl.objects.filter(
                        farm_foreignkey__id__in=project_id
                    )
                    
                    # Create a lookup dictionary for quick access
                    farm_detail_dict = {}
                    for detail in project_details:
                        if detail.farm_foreignkey:
                            farm_detail_dict[detail.farm_foreignkey.id] = detail
                    
                    # Prepare farm data
                    farm_data = []
                    # Also collect projectStaffTbl IDs
                    project_staff_ids = []
                    
                    for assignment in assigned_farms:
                        if assignment.projectTbl_foreignkey and assignment.projectTbl_foreignkey.id in farm_detail_dict:
                            farm_detail = farm_detail_dict[assignment.projectTbl_foreignkey.id]
                            farm_data.append({
                                "farm_id": assignment.projectTbl_foreignkey.id,
                                "farm_reference": farm_detail.farm_reference or "N/A",
                                "farmer_name": farm_detail.farmername or "N/A",
                                "region": farm_detail.region or "N/A",
                                "district": farm_detail.district or "N/A",
                                "location": farm_detail.location or "N/A",
                                "farm_size": farm_detail.farm_size or 0,
                                "status": farm_detail.status or "N/A",
                                "sector": farm_detail.sector or 0,
                                "year_established": farm_detail.year_of_establishment.strftime('%Y-%m-%d') if farm_detail.year_of_establishment else "N/A",
                                "assigned_date": assignment.created_date.strftime('%Y-%m-%d %H:%M:%S') if assignment.created_date else "N/A"
                            })
                            project_staff_ids.append(assignment.id)
                    
                    print(f"Login successful for: {staff.staffid}")
                    status["status"] = 1
                    status["msg"] = "Login successful"
                    status["data"] = {
                        "project_id": assignment.id if assigned_farms else None,
                        "first_name": f'{staff.first_name.title()}',
                        "last_name": f'{staff.last_name.title()}',
                        "user_id": f'{staff.id}',
                        "staff_id": staff.staffid if staff.staffid else "",
                        "group": f'{staff.designation.name}',
                       
                    }

                else:
                    status["status"] = 0
                    status["msg"] = "Invalid telephone number or password!"
                    status["data"] = {
                        "user": '',
                        "group": '',
                        "assigned_farms": []
                    }
            else:
                status["status"] = 0
                status["msg"] = "Telephone number is required!"
                status["data"] = {
                    "user": '',
                    "group": '',
                    "assigned_farms": []
                }

        except json.JSONDecodeError:
            status["status"] = 0
            status["msg"] = "Invalid JSON data!"
            status["data"] = {
                "user": '',
                "group": '',
                "assigned_farms": []
            }
        except Exception as e:
            status["status"] = 0
            status["msg"] = f"Error occurred: {str(e)}"
            status["data"] = {
                "user": '',
                "group": '',
                "assigned_farms": []
            }
        
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

                    designation = data["designation"]
                    designation = data["designation"]
                    designation = data["designation"]
                    if not bank_account_number:
                        owner_momo= "yes"
                        momo_account_name= name
                        momo_number= contact
                        payment_option= "momo"
                    else:
                        owner_momo= ""
                        momo_account_name= ""
                        momo_number= ""
                        payment_option= ""

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
                        "designation":designation,

                        "owner_momo":owner_momo,
                        "momo_account_name":momo_account_name,
                        "momo_number":momo_number,
                        "payment_option":payment_option,
                        
                                                
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

        dist = projectStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).projectTbl_foreignkey.id
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
        # sector = staffFarmsAssignment.objects.filter(staffTbl_foreignkey=data["userid"]).value_lists("joborder_foreignkey_farm_reference")

        
        # Farm = Farms.objects.filter(farmdetailstbl__sector=sector)
        Farm = staffFarmsAssignment.objects.filter(staffTbl_foreignkey=data["userid"]).values_list("joborder_foreignkey__farm_reference",flat=True)
        data = []

       
        for fam in Farm:
            try:
                poly = Farms.objects.filter(farm_id=fam).first()
                eok={}
                #print(fam.geom.transform(trans,clone=True))
                if poly.geom:
                    eok["farm_boundary"]= poly.geom.geojson
                else:
                    eok["farm_boundary"]=""
                eok["farmername"]= fam.farmername
                eok["location"]= fam.location
                eok["farm_reference"]= fam.farm_reference
                if fam.farm_size:
                    eok["farm_size"]= f"{fam.farm_size} Ha"
                else:
                    eok["farm_size"]= 0

                data.append(eok)
            except Exception as e:
                raise
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
            status["msg"] = "Success!"

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
            status["msg"] = "Success!"

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
            status["msg"] = "Success!"

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
            status["msg"] = "Success!"

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
            status["msg"] = "Success!"

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
            status["msg"] = "Success!"

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
            eok["momo_number"]=rehab.momo_number
            eok["momo_account_name"]=rehab.momo_account_name
            eok["dob"]=rehab.dob
            eok["po"]=f'{rehab.staffTbl_foreignkey.first_name} {rehab.staffTbl_foreignkey.last_name}'

            data.append(eok)
            status["status"] =  True
            status["msg"] = "Success!"

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
            status["msg"] = "Success!"

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
            status["msg"] = "Success!"

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
            feedback= data["feedback"]
            uid=data["uid"]
            week=data["week"]
            month=data["month"]
            farm_reference=data["farm_reference"]
            activity=data["activity"]
            ra_id=data["ra_id"]
            

            getstaff =staffTbl.objects.get(id=userid,delete_field="no") 

            obj,created = Feedback.objects.get_or_create(
                staffTbl_foreignkey=getstaff, 
                title=title,
                feedback=feedback,
                uid=uid,
                week=week,
                month=month,
                farm_reference=farm_reference,
                activity=activity,
                ra_id=ra_id
              )

            if created:
                status["status"] =  1
                status["msg"] =  "Successfully Sent !!"
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




# fetch all Equipment
@method_decorator(csrf_exempt, name='dispatch')
class fetchallFeedback(View):
    def post(self, request):	
        status ={}
        status["status"] =False
        data = json.loads(request.body)
        userid= data["userid"]

        feeds = Feedback.objects.filter(staffTbl_foreignkey=data["userid"])

        data = []

        for feed in feeds:
            eok={}
            eok["title"]=feed.title
            eok["feedback"]=feed.feedback
            eok["sent_date"]=feed.sent_date
            eok["uid"]=feed.uid
            eok["week"]=feed.week
            eok["month"]=feed.month
            eok["farm_reference"]=feed.farm_reference
            eok["activity"]=feed.activity
            eok["ra_id"]=feed.ra_id
            eok["Status"]=feed.Status
            
            data.append(eok)
            status["status"] =  True
            status["msg"] = "Success!"

        status["data"] = data

        return JsonResponse(status, safe=False)









# fetch all Equipment
@method_decorator(csrf_exempt, name='dispatch')
class fetchallEquipmentView(View):
    def post(self, request):	
        status ={}
        status["status"] =False
        data = json.loads(request.body)
        userid= data["userid"]
        dist = districtStaffTbl.objects.get(staffTbl_foreignkey=data["userid"]).districtTbl_foreignkey.id
        # print(dist)
        # equips = Equipment.objects.filter(districtTbl_foreignkey=dist)
        equips = Equipment.objects.all()
        data = []

        for equip in equips:
            eok={}
            eok["equipment_code"]=equip.equipment_code
            eok["date_of_capturing"]=equip.date_of_capturing
            eok["equipment"]=equip.equipment
            eok["status"]=equip.status
            eok["serial_number"]=equip.serial_number
            eok["manufacturer"]=equip.manufacturer
            eok["pic_serial_number"]= f'https://cocoa-monitor-static.s3.us-west-2.amazonaws.com/media/{str(equip.pic_serial_number)}'
            eok["pic_equipment"]= f'https://cocoa-monitor-static.s3.us-west-2.amazonaws.com/media/{str(equip.pic_equipment)}'
            eok["staff_name"]=equip.staff_name
            data.append(eok)
            status["status"] =  True
            status["msg"] = "Success!"

        status["data"] = data

        return JsonResponse(status, safe=False)



@method_decorator(csrf_exempt, name='dispatch')
class saveequipmentEventory(View):
    def post(self, request):
        status ={}
        status["status"] = 0
        data = json.loads(request.body)
        userid= data["userid"]
                
        try : 


            date_of_capturing  = data['date_of_capturing']
            
            district  = data['district']
            equipment  = data['equipment']
            status_fo  = data['status']
            serial_number  = data['serial_number']
            manufacturer  = data['manufacturer']
            pic_serial_number  = data['pic_serial_number']
            pic_equipment  = data['pic_equipment']
            telephone  = data['telephone'] 
            uuid = data['uuid'] 
            # staff_name  = data['staff_name']
            

            getstaff = staffTbl.objects.get(id=userid)

            if data["pic_serial_number"] :
                pic_serial_number =saveimage(data["pic_serial_number"], serial_number) 
            else:
                pic_serial_number =data["pic_serial_number"] 

            if data["pic_equipment"] :
                pic_equipment =saveimage(data["pic_equipment"], telephone) 
            else:
                pic_equipment =data["pic_equipment"] 

            dist = cocoaDistrict.objects.get(id=district)
            equip=equipment[:3]
            initcode=f"{equip}/{dist.reg_code.reg_code}/{dist.district_code}"
            if Equipment.objects.filter(equipment_code__startswith= initcode).exists():
                equipnum = Equipment.objects.filter(equipment_code__startswith= f"{initcode}").count()
            else:
                equipnum = 0
        
            equipnum_sum = int(equipnum) + 1
            num="{0:0>3}".format(equipnum_sum)
            eqcode = f"{initcode}/{num}"

            rehabobj, rehab_created = Equipment.objects.get_or_create(
            _uuid=uuid,serial_number=serial_number,
            defaults=dict(
            equipment_code=eqcode,
            date_of_capturing=date_of_capturing,
            region=dist.reg_code.region,
            district=district,
            equipment=equipment,
            status=status_fo,
            serial_number=serial_number,
            manufacturer= manufacturer,
            pic_serial_number=pic_serial_number,
            pic_equipment=pic_equipment,
            telephone=telephone,
            staff_name=f'{getstaff.first_name} {getstaff.last_name}',
            _uuid=uuid,
            staffTbl_foreignkey=getstaff,
            districtTbl_foreignkey=dist

            )

            )

            if rehab_created:
                status["status"] =  1
                status["msg"] =  "Successful Saved !!"
                status["data"] ={
                
                }

            else:
                if rehabobj:
                    status["status"] = 2
                    status["msg"] =  "Already exist !!"
                else:
                    status["status"] =  0
                    status["msg"] =  "Error Occured! DDDD",



        except Exception as e:
            raise e
            status={}
            status["status"] =  0
            status["msg"] =  "Error Occured!",
            status["data"] =str(e),

        return JsonResponse(status, safe=False)
    



# fetch all Equipment
@method_decorator(csrf_exempt, name='dispatch')
class fetchpaymentReportView(View):
    def post(self, request):	
        status ={}
        status["status"] =False
        data = json.loads(request.body)
        userid= data["userid"]
        month= data["month"]
        week= data["week"]
        year= data["year"]

        dist = projectStaffTbl.objects.get(staffTbl_foreignkey=data["userid"])
        print(dist.projectTbl_foreignkey.name)
        reports = paymentReport.objects.filter(district__iexact=dist.projectTbl_foreignkey.name,year=year,month__iexact=month,week=week)
        print(reports.count())
        data = []

        for rep in reports:
            eok={}
            # eok["district"]=rep.district
            eok["bank_name"]=rep.bank_name
            eok["bank_branch"]=rep.bank_branch
            eok["snnit_no"]=rep.snnit_no
            eok["salary"]=rep.salary
            eok["year"]=rep.year
            eok["po_number"]= rep.po_number
            eok["month"]= rep.month
            eok["week"]=rep.week
            eok["payment_option"]=rep.payment_option
            eok["momo_acc"]=rep.momo_acc
            eok["ra_id"]=rep.ra_id
            eok["ra_name"]=rep.ra_name
            
            data.append(eok)
            status["status"] =  True
            status["msg"] = "Success!"

        status["data"] = data

        return JsonResponse(status, safe=False)
    


# fetch all Equipment
@method_decorator(csrf_exempt, name='dispatch')
class fetchpaymentdetailsReportView(View):
    def post(self, request):	
        status ={}
        status["status"] =False
        data = json.loads(request.body)
        userid= data["userid"]
        month= data["month"]
        week= data["week"]
        year= data["year"]
        raid= data["raid"]

        dist = projectStaffTbl.objects.get(staffTbl_foreignkey=data["userid"])
        print(dist.projectTbl_foreignkey.name)
        if not raid:
            reports = paymentdetailedReport.objects.filter(project__iexact=dist.projectTbl_foreignkey.name,year=year,month__iexact=month,week=week)
        else:
            reports = paymentdetailedReport.objects.filter(project__iexact=dist.projectTbl_foreignkey.name,year=year,month__iexact=month,week=week,ra_id=raid)

        data = []

        for rep in reports:
            eok={}
            eok["group_code"]=rep.group_code
            eok["ra_id"]=rep.ra_id
            eok["ra_name"]=rep.ra_name
            eok["po_name"]=rep.po_name
            eok["po_number"]=rep.po_number
            eok["district"]=rep.district
            eok["farmhands_type"]= rep.farmhands_type
            eok["farm_reference"]= rep.farm_reference
            eok["number_in_a_group"]= rep.number_in_a_group
            eok["activity"]=rep.activity
            eok["achievement"]=rep.achievement
            eok["amount"]=rep.amount
            eok["week"]=rep.week
            eok["month"]=rep.month
            eok["year"]=rep.year
            eok["issue"]=rep.issue
            

            data.append(eok)
            status["status"] =  True
            status["msg"] = "Success!"

        status["data"] = data
        return JsonResponse(status, safe=False)
    






class rehabassistantsTblListView(ListAPIView):
    queryset = rehabassistantsTbl.objects.all()
    serializer_class = rehabassistantsTblSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
    

        # Get the request parameters
        filters = rehabassistantsTblSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)

        if self.request.query_params['userid']:
            print(self.request.query_params['userid'])
            dist = projectStaffTbl.objects.filter(staffTbl_foreignkey=self.request.query_params['userid']).values_list("districtTbl_foreignkey__id", flat=True)
            queryset = queryset.filter(projectTbl_foreignkey__in=dist)
            print("dist")
            print(dist)
        return queryset
# /items/?category=Electronics&price_min=100&price_max=500


@method_decorator(csrf_exempt, name='dispatch')
class versionTblView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            status ={}
            status["status"] =False

            if data["version"] :
                if versionTbl.objects.filter(version=data["version"]).exists():
                    status["status"] =  1
                    status["msg"] =  "sucessful"
                else:
                    status["status"] =  0
                    status["msg"] =  "not sucessful"
                    
            else:
                status["status"] =  0
                status["msg"] =  "not sucessful"

        except Exception as e:
            raise e
            status["status"] =  0
            status["msg"] =  "Error Occured!"
            status["data"] =str(e),
        return JsonResponse(status, safe=False)
    


@method_decorator(csrf_exempt, name='dispatch')
class savenewMaintenanceReportView(View):
    def post(self, request):
        status ={}
        status["status"] = 0
        try:
            data = json.loads(request.body)
    

            staffTbl_foreignkey= data["agent"]
            # districtTbl_foreignkey= data["community"]["district_id"]
            uid= data["uid"]
            monitoring_date= data["monitoring_date"]
            no_rehab_assistants= data["no_rehab_assistants"]
            area_covered_ha= data["area_covered_ha"]
            remark= data["remark"]
            lat= data["lat"]
            lng= data["lng"]
            accuracy= data["accuracy"]
            activity= data["activity"]
            current_farm_pic= data["current_farm_pic"]
            farm_ref_number= data["farm_ref_number"]
            farm_size_ha= data["farm_size_ha"]
            cocoa_seedlings_alive= data["cocoa_seedlings_alive"]
            plantain_seedlings_alive= data["plantain_seedlings_alive"]
            name_of_ched_ta= data["name_of_ched_ta"]
            ched_ta_contact= data["ched_ta_contact"]
            community= data["community"]
            contractor_name= data["contractor_name"]
            number_of_people_in_group= data["number_of_people_in_group"]
            groupWork= data["groupWork"]
            completedByContractor= data["completedByContractor"]
            ralist = data["rehab_assistants"]

            comm = communityTbl.objects.get(id=community)



            if data["current_farm_pic"]:
                current_farm_pic=saveimage(data["current_farm_pic"], staff_contact) 
            else:
                current_farm_pic=""

        
            # act=Activities.objects.get(id=int(activity))
            if not mobileMaintenance.objects.filter(uid=uid).exists():

                if farm_ref_number!="" and ralist!="" :
                    weekmonitorobj, weekmonitor_created = mobileMaintenance.objects.get_or_create(
                        staffTbl_foreignkey=staffTbl.objects.get(id = staffTbl_foreignkey),
                        districtTbl_foreignkey_id=comm.districtTbl_foreignkey.id,
                        uid=uid,
                        monitoring_date=monitoring_date,
                        no_rehab_assistants=no_rehab_assistants,
                        area_covered_ha=area_covered_ha,
                        remark=remark,
                        lat=lat,
                        lng=lng,
                        accuracy=accuracy,
                        activity_id=activity,
                        current_farm_pic=current_farm_pic,
                        farm_ref_number=farm_ref_number,
                        farm_size_ha=farm_size_ha,
                        cocoa_seedlings_alive=cocoa_seedlings_alive,
                        plantain_seedlings_alive=plantain_seedlings_alive,
                        name_of_ched_ta=name_of_ched_ta,
                        ched_ta_contact=ched_ta_contact,
                        community=comm.community,
                        contractor_name=contractor_name,
                        number_of_people_in_group=number_of_people_in_group,
                        groupWork=groupWork,
                        completedByContractor=completedByContractor
                      )

                    if weekmonitor_created:
                        if ralist:
                            for rehab in ralist:
                                rehabobj,rehab_created =mobileMaintenancerehabassistTbl.objects.get_or_create(
                                            mobileMaintenance_foreignkey=weekmonitorobj,
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





# @method_decorator(csrf_exempt, name='dispatch')
# class saveContractorcertificateofworkdoneAPIView(View):
#     def post(self, request):
#         status ={}
#         status["status"] = 0
#         try:
#             data = json.loads(request.body)
#             staffTbl_foreignkey= data["userid"]
#             districtTbl_foreignkey= data["district"]
#             uid= data["uid"]
#             current_year= data["current_year"]
#             current_month= data["current_month"]
#             currrent_week= data["currrent_week"]
#             activity= data["activity"]
#             weeding_rounds= data["weeding_rounds"]
#             farmer_name= data["farmer_name"]
#             sector=data["sector"]
#             reporting_date= data["reporting_date"]
#             farm_ref_number= data["farm_ref_number"]
#             farm_size_ha= data["farm_size_ha"]
#             community= data["community"]
#             contractor= data["contractor"]

#             contractor = contractorsTbl.objects.get(id=contractor)
        
#             district = cocoaDistrict.objects.get(id=districtTbl_foreignkey)
#             for act in activity:
#                 # print (act)
#             # if not contractorcertificateWorkdone.objects.filter(uuid=uid).exists():
#                 staffid = staffTbl.objects.get(id = staffTbl_foreignkey)
#                 weekmonitorobj, contract_created = contractorcertificateWorkdone.objects.get_or_create(
#                     staffTbl_foreignkey=staffTbl.objects.get(id = staffTbl_foreignkey),
#                     uuid=uid,
#                     reporting_date=reporting_date,
#                     region=district.reg_code.region,
#                     districtTbl_foreignkey=district,
#                     district=district.district,
#                     year=current_year,
#                     month=current_month,
#                     week=currrent_week,
#                     farmer_ref_number=farm_ref_number,
#                     community=community,
#                     activity=Activities.objects.get(id=act),
#                     weeding_rounds=weeding_rounds,
#                     farmer_name=farmer_name,
#                     sector=sector,
#                     farm_size=farm_size_ha,
#                     contractor=contractor.contractor_name,
#                     po_telephone=staffTbl.objects.get(id = staffTbl_foreignkey).contact,
#                     project_officer=f'{staffid.first_name} {staffid.last_name}'
#                         )
                
#                 if contract_created :
#                     status["status"] =  1
#                     status["msg"] =  "Successful Saved !!"
                     

#                 else:
#                     status["status"] =  2
#                     status["msg"] =  "record exist"
#                     status["data"] = uid

#         except Exception as e:
#             raise e
#             status["status"] =  0
#             status["msg"] =  "Error Occured!"
#             status["data"] =str(e)
#         return JsonResponse(status, safe=False)
    

@method_decorator(csrf_exempt, name='dispatch')
class saveContractorcertificateofworkdoneAPIView(View):
    def post(self, request):
        status ={}
        status["status"] = 0
        try:
            data = json.loads(request.body)
            staffTbl_foreignkey= data["userid"]
            districtTbl_foreignkey= data["district"]
            uid= data["uid"]
            current_year= data["current_year"]
            current_month= data["current_month"]
            currrent_week= data["currrent_week"]
            activity= data["activity"]
            weeding_rounds= data["weeding_rounds"]
            # farmer_name= data["farmer_name"]
            sector=data["sector"]
            reporting_date= data["reporting_date"]
            farm_ref_number= data["farm_ref_number"]
            farm_size_ha= data["farm_size_ha"]
            community= data["community"]
            contractor= data["contractor"]

            contractor = contractorsTbl.objects.get(id=contractor)
        
            district = cocoaDistrict.objects.get(id=districtTbl_foreignkey)
            for act in activity:
                # print (act)
            # if not contractorcertificateWorkdone.objects.filter(uuid=uid).exists():

                staffid = staffTbl.objects.get(id = staffTbl_foreignkey)

                activity_instance = Activities.objects.get(id=act)
                # Fetch the job order using the farm reference number
                job_order = Joborder.objects.get(farm_reference=farm_ref_number)
                activity_code = activity_instance.activity_code
                # Print the activity code
                # print(hasattr(job_order, activity_code))
                
                act_check = allFarmqueryTbl.objects.filter(farm_reference=farm_ref_number,activity_code=activity_instance.activity_code,year=current_year).count()
                
               

                contractorz = contractorcertificateWorkdone.objects.filter(farmer_ref_number=farm_ref_number,activity=act,reporting_date__year=current_year).count()
                activity_count = activityReporting.objects.filter(activity_id=act,farm_ref_number=farm_ref_number,reporting_date__year=current_year).count()
                allcheck=contractorz+activity_count

               
                if  allcheck < job_order.M3 :

                    weekmonitorobj, contract_created = contractorcertificateWorkdone.objects.get_or_create(
                        staffTbl_foreignkey=staffTbl.objects.get(id = staffTbl_foreignkey),
                        uuid=uid,
                        reporting_date=reporting_date,
                        region=district.reg_code.region,
                        districtTbl_foreignkey=district,
                        district=district.district,
                        year=current_year,
                        month=current_month,
                        week=currrent_week,
                        farmer_ref_number=farm_ref_number,
                        community=community,
                        activity=Activities.objects.get(id=act),
                        weeding_rounds=weeding_rounds,
                        # farmer_name=farmer_name,
                        sector=sector,
                        farm_size=farm_size_ha,
                        contractor=contractor.contractor_name,
                        po_telephone=staffTbl.objects.get(id = staffTbl_foreignkey).contact,
                        project_officer=f'{staffid.first_name} {staffid.last_name}'
                            )
                    
                    if contract_created :
                        status["status"] =  1
                        status["msg"] =  "Successful Saved !!"
                        

                    else:
                        status["status"] =  2
                        status["msg"] =  "record exist"
                        status["data"] = uid
                
                else:
                        status["status"] =  3
                        status["msg"] =  "reported for in RA reporting"
                        status["data"] = uid

        except Exception as e:
            raise e
            status["status"] =  0
            status["msg"] =  "Error Occured!"
            status["data"] =str(e)
        return JsonResponse(status, safe=False)
    


@method_decorator(csrf_exempt, name='dispatch')
class fetchallContractors(View):
    def post(self, request):
        try:
            datas = contractorsTbl.objects.all()
            status ={}
            status["status"] =False

            datas = contractorsTbl.objects.all()
            data = []
            for aa in datas:
                eok={}
                eok["id"]=aa.id
                eok["name"]=aa.contractor_name
                data.append(eok)
              
            status["status"] =  1
            status["msg"] =  "sucessful"
            status["data"] = data
    
        except Exception as e:
            raise e
            status["status"] =  0
            status["msg"] =  "Error Occured!"
            status["data"] =str(e),
        return JsonResponse(status, safe=False)
    




@method_decorator(csrf_exempt, name='dispatch')
class saveVerificationFarmsAPIView(View):
    def post(self, request):
        status ={}
        status["status"] = 0
        try:
            data = json.loads(request.body)
            uid=data["uid"]
            current_year= data["current_year"]
            current_month= data["current_month"]
            currrent_week= data["currrent_week"]
            activity= data["activity"]
            reporting_date= data["reporting_date"]
            farm_ref_number= data["farm_ref_number"]
            farm_size_ha= data["farm_size_ha"]
            community= data["community"]
            district=  data["district"]
            staffTbl_foreignkey= data["userid"]
            lat= data["lat"]
            lng= data["lng"]
            accuracy= data["accuracy"]
          
            contractor_name= data["contractor"]
            completed_by= data["completed_by"]


            def saveimage(image, imgname):
                img = decodeDesignImage(image)
                img_io = io.BytesIO()

                if img is not None:
                    img.save(img_io, format='PNG')
                    img_io.seek(0)  # Reset buffer position to the beginning

                    data = InMemoryUploadedFile(
                        img_io,
                        field_name=None,
                        name=f"{imgname}.png",
                        content_type='image/png',
                        size=img_io.getbuffer().nbytes,  # Get the correct size
                        charset=None
                    )
                    return data
                return None



            if contractor_name: 
                contractors = contractorsTbl.objects.get(id=contractor_name).contractor_name
            else:
                contractors = "none"
        
            district = cocoaDistrict.objects.get(id=district)
            for act in activity:
                current_farm_pic = saveimage(data.get("current_farm_pic"), uid) if data.get("current_farm_pic") else None
                staffid = staffTbl.objects.get(id = staffTbl_foreignkey)
                weekmonitorobj, contract_created = verificationWorkdone.objects.get_or_create(
                    staffTbl_foreignkey=staffTbl.objects.get(id = staffTbl_foreignkey),
                    uuid=uid,
                    reporting_date=reporting_date,
                    region=district.reg_code.region,
                    districtTbl_foreignkey=district,
                    district=district.district,
                    year=current_year,
                    month=current_month,
                    week=currrent_week,
                    farmer_ref_number=farm_ref_number,
                    community=community,
                    activity=Activities.objects.get(id=act),
                    farm_size=farm_size_ha,
                    contractor=contractors,
                    po_telephone=staffTbl.objects.get(id = staffTbl_foreignkey).contact,
                    project_officer=f'{staffid.first_name} {staffid.last_name}',
                    lat=lat,
                    lng=lng,
                    accuracy=accuracy,
                    geom=Point(lng,lat),
                    completed_by=completed_by,
                    current_farm_pic=current_farm_pic
                    )
                
                if contract_created :
                    status["status"] =  1
                    status["msg"] =  "Successful Saved !!"
                     

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
    



# @method_decorator(csrf_exempt, name='dispatch')
# class saveVerificationFarmsAPIView(View):
#     def post(self, request):
#         status = {}
#         status["status"] = 0
#         try:
#             data = json.loads(request.body)
#             # print(f"Received data: {data.keys()}")

#             uid = data["uid"]
#             current_year = data["current_year"]
#             current_month = data["current_month"]
#             currrent_week = data["currrent_week"]
#             activity = data["activity"]
#             reporting_date = data["reporting_date"]
#             farm_ref_number = data["farm_ref_number"]
#             farm_size_ha = data["farm_size_ha"]
#             community = data["community"]
#             district = data["district"]
#             staffTbl_foreignkey = data["userid"]
#             lat = data["lat"]
#             lng = data["lng"]
#             accuracy = data["accuracy"]

#             contractor_name = data.get("contractor")
#             completed_by = data["completed_by"]

#             current_farm_pic = ""
#             # Save the image only before the first activity is processed
#             if data.get("current_farm_pic"):
#                 current_farm_pic = saveimage(data["current_farm_pic"], uid)
#                 print(f"Path returned by saveimage: {current_farm_pic}")
#             else:
#                 print("No current_farm_pic data received.")

#             contractors = "none"
#             if contractor_name:
#                 try:
#                     contractors = contractorsTbl.objects.get(id=contractor_name).contractor_name
#                 except contractorsTbl.DoesNotExist:
#                     print(f"Contractor with ID {contractor_name} not found.")
#                     status["status"] = 0
#                     status["msg"] = f"Error: Contractor with ID {contractor_name} not found."
#                     return JsonResponse(status, safe=False)

#             try:
#                 district_obj = cocoaDistrict.objects.get(id=district)
#             except cocoaDistrict.DoesNotExist:
#                 print(f"Cocoa district with ID {district} not found.")
#                 status["status"] = 0
#                 status["msg"] = f"Error: Cocoa district with ID {district} not found."
#                 return JsonResponse(status, safe=False)

#             staff_obj = staffTbl.objects.get(id=staffTbl_foreignkey)

#             for i, act in enumerate(activity):
#                 try:
#                     activity_obj = Activities.objects.get(id=act)
#                 except Activities.DoesNotExist:
#                     print(f"Activity with ID {act} not found.")
#                     status["status"] = 0
#                     status["msg"] = f"Error: Activity with ID {act} not found."
#                     return JsonResponse(status, safe=False)

#                 weekmonitorobj, contract_created = verificationWorkdone.objects.get_or_create(
#                     staffTbl_foreignkey=staff_obj,
#                     uuid=uid,
#                     reporting_date=reporting_date,
#                     region=district_obj.reg_code.region,
#                     districtTbl_foreignkey=district_obj,
#                     district=district_obj.district,
#                     year=current_year,
#                     month=current_month,
#                     week=currrent_week,
#                     farmer_ref_number=farm_ref_number,
#                     community=community,
#                     activity=activity_obj,
#                     farm_size=farm_size_ha,
#                     contractor=contractors,
#                     po_telephone=staff_obj.contact,
#                     project_officer=f'{staff_obj.first_name} {staff_obj.last_name}',
#                     lat=lat,
#                     lng=lng,
#                     accuracy=accuracy,
#                     geom=Point(lng,lat),
#                     completed_by=completed_by,
#                     current_farm_pic=current_farm_pic  # The same saved pic for all activities
#                 )

#                 if contract_created:
#                     status["status"] = 1
#                     status["msg"] = "Successful Saved !!"
#                 else:
#                     status["status"] = 2
#                     status["msg"] = "record exist"
#                     status["data"] = uid

#         except Exception as e:
#             print(f"An error occurred: {str(e)}", exc_info=True)
#             status["status"] = 0
#             status["msg"] = "Error Occured!"
#             status["data"] = str(e)
#         return JsonResponse(status, safe=False)


# # Create your views here.
class Coco32FormCoreSerializerView(viewsets.ReadOnlyModelViewSet):
    try:
        queryset = Coco32FormCore.objects.using('odk').filter(field_submission_date__date__gte=(date.today()-timedelta(days=5)))
    except:
        queryset =Coco32FormCore.objects.using('odk').all()
    serializer_class = Coco32FormCoreSerializer


class Coco32FormWorkdoneByRaSerializerView(viewsets.ReadOnlyModelViewSet):
    try:
        queryset = Coco32FormWorkdoneByRa.objects.using('odk').filter(field_submission_date__date__gte=(date.today()-timedelta(days=5)))
    except:
        queryset =Coco32FormWorkdoneByRa.objects.using('odk').all()
    serializer_class = Coco32FormWorkdoneByRaSerializer


class Coco32FormWorkdoneByPoNspSerializerView(viewsets.ReadOnlyModelViewSet):
    try:
        queryset = Coco32FormWorkdoneByPoNsp.objects.using('odk').filter(field_submission_date__date__gte=(date.today()-timedelta(days=5)))
    except:
        queryset =Coco32FormWorkdoneByPoNsp.objects.using('odk').all()
    serializer_class = Coco32FormWorkdoneByPoNspSerializer





@method_decorator(csrf_exempt, name='dispatch')
class savemappedFarmView(View):
    def post(self, request):
        status ={}
        status["status"] = 0
        try:
            data = json.loads(request.body)
            
    
            uid= data["uid"]
            staff= data["userid"]
            farm_reference= data["farm_reference"]
            farm_area= data["farm_size"]
            farmer_name= data["farmer_name"]
            location= data["location"]
            farmboundary= data["farmboundary"]
            contact = data["contact"]
            
            
            aa=[]
            for points in farmboundary:
                aa.append((points["longitude"],points["latitude"]))

            farm_geom = Polygon(tuple(aa) )
            staffid = staffTbl.objects.get(id = staff)

            obj, created = mappedFarms.objects.get_or_create(farm_reference=farm_reference,
                defaults=dict(
                geom=farm_geom,
                uuid=uid,
                contact=contact,
                farm_reference=farm_reference,
                farm_area=farm_area,
                farmer_name=farmer_name,
                location=location,
                staffTbl_foreignkey=staffid,
                farmboundary=str(aa),
          
                
                )
               
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
    




@method_decorator(csrf_exempt, name='dispatch')
class fetchjoborderView(View):
    def post(self, request):	
        status ={}
        status["status"] =False
        data = json.loads(request.body)
        userid= data["userid"]

        print(userid)
        sectorlist =sectorStaffassignment.objects.filter(staffTbl_foreignkey = data["userid"]).values_list("sector",flat=True)
        print(sectorlist)
        
        farms = Joborder.objects.filter(sector__in=sectorlist).defer('location','sector','region',"year_of_establishment")
        # print(farms.count())
        print(farms.count())
        data = []

        for farm in farms:
            # print(farm.farm_reference)
            try:
                eok={}
                eok["farm_code"]=farm.id
                eok["farm_id"]=farm.farm_reference
                eok["farmer_nam"]=checkTitle(farm.farmername)
                eok["district_id"]=farm.districtTbl_foreignkey.id
                eok["district_name"]=checkTitle(farm.districtTbl_foreignkey.district)
                eok["region_id"]=farm.districtTbl_foreignkey.reg_code.reg_code
                eok["region_name"]=checkTitle(farm.districtTbl_foreignkey.reg_code.region)
                eok["sector"]=farm.sector
                eok["farm_code"]=farm.id
                eok["location"]=farm.location
                eok["farm_size"]=farm.farm_size
                eok["E1"]= farm.E1
                eok["E2"]= farm.E2
                eok["E3"]= farm.E3
                eok["E4"]= farm.E4
                eok["E6"]= farm.E6
                eok["E7"]= farm.E7
                eok["M3"]= farm.M3
                eok["R1"]= farm.R1
                eok["R2"]= farm.R2
                eok["R2"]= farm.R2
                eok["R4"]= farm.R4
                eok["R4"]= farm.R4
                eok["T1"]= farm.T1
                eok["T2"]= farm.T2
                eok["T5"]= farm.T5
                eok["T7"]= farm.T7

                data.append(eok)
                status["status"] =  True
                status["msg"] = "Success!"
            except Exception as e:
                print(e)
                continue

        status["data"] = data

        return JsonResponse(status, safe=False)


from datetime import datetime

# Get the current year
current_year = datetime.now().year

print(current_year)

@method_decorator(csrf_exempt, name='dispatch')
class savenActivityReportView(View):
    def post(self, request):
        status ={}
        status["status"] = 0
        results=[]
        try:
            data = json.loads(request.body)
    

            staffTbl_foreignkey= data["agent"]
            # districtTbl_foreignkey= data["community"]["district_id"]
            uid= data["uid"]
            
            no_rehab_assistants= data["no_rehab_assistants"]
            area_covered_ha= data["area_covered_ha"]
            remark= data["remark"]
            sector= data["sector"]
           
            activity= data["activity"]
            farm_ref_number= data["farm_ref_number"]
            farm_size_ha= data["farm_size_ha"]
            community= data["community"]
            number_of_people_in_group= data["number_of_people_in_group"]
            groupWork= data["groupWork"]
            ralist = data["rehab_assistants"]
            completed_date= data["completed_date"]
            reporting_date= data["reporting_date"]

            # act=Activities.objects.get(id=activity)
            # activ=act.activity_code
            # joborder=Joborder.objects.get(farm_reference=farm_ref_number)
            # print("Amos",activ)
            # print("helloo",joborder.activ)

            for act in activity:
                activity_instance = Activities.objects.get(id=act)
                print(activity_instance.sub_activity)
                activity_code = activity_instance.activity_code

                # Fetch the job order using the farm reference number
                job_order = Joborder.objects.get(farm_reference=farm_ref_number)

                # Print the activity code
                # print(hasattr(job_order, activity_code))

                act_check = getattr(job_order, activity_code)

            

                # if not activityReporting.objects.filter(uid=uid).exists():
                joborder=Joborder.objects.get(farm_reference=farm_ref_number)
                
                # print(activ.activ)
                # print(act.activity_code)
                contractor = contractorcertificateWorkdone.objects.filter(farmer_ref_number=farm_ref_number,activity=act,reporting_date__year=current_year).count()
                activity_count = activityReporting.objects.filter(activity_id=act,farm_ref_number=farm_ref_number,reporting_date__year=current_year).count()
                allcheck=contractor+activity_count
                if  allcheck < act_check :
                    if farm_ref_number!="" and ralist!="" :
                        weekmonitorobj, weekmonitor_created = activityReporting.objects.get_or_create(
                            staffTbl_foreignkey=staffTbl.objects.get(id = staffTbl_foreignkey),
                            joborder = joborder,
                            uid=uid,
                            sector=sector,
                            reporting_date=reporting_date,
                            completed_date=completed_date,
                            no_rehab_assistants=no_rehab_assistants,
                            area_covered_ha=area_covered_ha,
                            remark=remark,
                            activity_id=act,
                            farm_ref_number=farm_ref_number,
                            farm_size_ha=farm_size_ha,
                            community=community,
                            number_of_people_in_group=number_of_people_in_group,
                            groupWork=groupWork,
                        
                        
                        )

                        if weekmonitor_created:
                            if ralist:
                                for rehab in ralist:
                                    rehabobj,rehab_created =activityreportingrehabassistTbl.objects.get_or_create(
                                                activityreporting_foreignkey=weekmonitorobj,
                                                rehabassistantsTbl_foreignkey=rehabassistantsTbl.objects.get(id=rehab["rehab_asistant"]),
                                                area_covered_ha=rehab["area_covered_ha"],

                                            )


                            status["status"] =  1
                            status["msg"] =  "Successful Saved !!"
                            status["data"] ={
                            # "activity":activity_instance.sub_activity
                            }
    
                        else:
                            status["status"] = 0
                            status["msg"] =  "data exist"
                    else:
                        status["status"] =  0
                        status["msg"] =  "Error Occured!"
                        
                else:
                    status["status"] =  3
                    status["msg"] =  "max threahold met;contact your MnE "
                    status["data"] = uid
               
                results.append(status)

        except Exception as e:
            raise e
            status["status"] =  0
            status["msg"] =  "Error Occured!"
            status["data"] =str(e)
        return JsonResponse(results, safe=False)






@method_decorator(csrf_exempt, name='dispatch')
class savenspecialprojectfarmsTblView(View):
    def post(self, request):
        status ={}
        status["status"] = 0
        results=[]
        try:
            data = json.loads(request.body)
    

            staffTbl_foreignkey= data["agent"]
            # districtTbl_foreignkey= data["community"]["district_id"]
            uid= data["uid"]
            
            no_rehab_assistants= data["no_rehab_assistants"]
            area_covered_ha= data["area_covered_ha"]
            remark= data["remark"]
            sector= data["sector"]
           
            activity= data["activity"]
            farm_ref_number= data["farm_ref_number"]
            farm_size_ha= data["farm_size_ha"]
            community= data["community"]
            number_of_people_in_group= data["number_of_people_in_group"]
            groupWork= data["groupWork"]
            ralist = data["rehab_assistants"]
            completed_date= data["completed_date"]
            reporting_date= data["reporting_date"]

            # act=Activities.objects.get(id=activity)
            # activ=act.activity_code
            # joborder=Joborder.objects.get(farm_reference=farm_ref_number)
            # print("Amos",activ)
            # print("helloo",joborder.activ)

            for act in activity:
                activity_instance = Activities.objects.get(id=act)
                print(activity_instance.sub_activity)
                activity_code = activity_instance.activity_code

                # Fetch the job order using the farm reference number
                job_order = Joborder.objects.get(farm_reference=farm_ref_number)

                # Print the activity code
                # print(hasattr(job_order, activity_code))

                act_check = getattr(job_order, activity_code)

            

                # if not activityReporting.objects.filter(uid=uid).exists():
                joborder=Joborder.objects.get(farm_reference=farm_ref_number)
                
                # print(activ.activ)
                # print(act.activity_code)
                contractor = contractorcertificateWorkdone.objects.filter(farmer_ref_number=farm_ref_number,activity=act,reporting_date__year=current_year).count()
                activity_count = activityReporting.objects.filter(activity_id=act,farm_ref_number=farm_ref_number,reporting_date__year=current_year).count()
                allcheck=contractor+activity_count
                if  allcheck < act_check :
                    if farm_ref_number!="" and ralist!="" :
                        weekmonitorobj, weekmonitor_created = activityReporting.objects.get_or_create(
                            staffTbl_foreignkey=staffTbl.objects.get(id = staffTbl_foreignkey),
                            joborder = joborder,
                            uid=uid,
                            sector=sector,
                            reporting_date=reporting_date,
                            completed_date=completed_date,
                            no_rehab_assistants=no_rehab_assistants,
                            area_covered_ha=area_covered_ha,
                            remark=remark,
                            activity_id=act,
                            farm_ref_number=farm_ref_number,
                            farm_size_ha=farm_size_ha,
                            community=community,
                            number_of_people_in_group=number_of_people_in_group,
                            groupWork=groupWork,
                        
                        
                        )

                        if weekmonitor_created:
                            if ralist:
                                for rehab in ralist:
                                    rehabobj,rehab_created =activityreportingrehabassistTbl.objects.get_or_create(
                                                activityreporting_foreignkey=weekmonitorobj,
                                                rehabassistantsTbl_foreignkey=rehabassistantsTbl.objects.get(id=rehab["rehab_asistant"]),
                                                area_covered_ha=rehab["area_covered_ha"],

                                            )


                            status["status"] =  1
                            status["msg"] =  "Successful Saved !!"
                            status["data"] ={
                            # "activity":activity_instance.sub_activity
                            }
    
                        else:
                            status["status"] = 0
                            status["msg"] =  "data exist"
                    else:
                        status["status"] =  0
                        status["msg"] =  "Error Occured!"
                        
                else:
                    status["status"] =  3
                    status["msg"] =  "max threahold met;contact your MnE "
                    status["data"] = uid
               
                results.append(status)

        except Exception as e:
            raise e
            status["status"] =  0
            status["msg"] =  "Error Occured!"
            status["data"] =str(e)
        return JsonResponse(results, safe=False)



class WbpFarmsListView(ListAPIView):
    queryset = Farms.objects.all()
    serializer_class = WbpFarmsSerializer
    
    def get_queryset(self):
    # Start with the base queryset
        queryset = super().get_queryset()

        # Check if the request method is POST and handle JSON body
        if self.request.method == 'POST':
            data = json.loads(self.request.body)
            userid = data.get('userid')
            
        else:
            
            userid = self.request.query_params.get('userid')
            print(userid)
        if userid:
            # Attempt to retrieve farms assigned to the specified staff member
            farms = staffFarmsAssignment.objects.filter(
                staffTbl_foreignkey=userid
            ).values_list("joborder_foreignkey__farm_reference", flat=True)

            if farms:
                queryset = queryset.filter(farm_id__in=farms)
            else:
                queryset = queryset.none()

        return queryset.order_by('farm_id')