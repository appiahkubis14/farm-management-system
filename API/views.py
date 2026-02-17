# views.py
import traceback
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from datetime import datetime, date
from django.db.models import Q
import base64
import io
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.gis.geos import Point
from portal.models import *

# ============== HELPER FUNCTIONS ==============

def decodeDesignImage(data):
    """Decode base64 image"""
    try:
        if data and data.strip():
            data = base64.b64decode(data.encode('UTF-8'))
            buf = io.BytesIO(data)
            img = Image.open(buf)
            return img
    except:
        return None
    return None

def save_image(image, imgname, format='PNG'):
    """Save base64 image to file"""
    img = decodeDesignImage(image)
    if img is not None:
        img_io = io.BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        
        content_type = 'image/png' if format == 'PNG' else 'image/jpeg'
        extension = 'png' if format == 'PNG' else 'jpg'
        
        data = InMemoryUploadedFile(
            img_io,
            field_name=None,
            name=f"{imgname}.{extension}",
            content_type=content_type,
            size=img_io.getbuffer().nbytes,
            charset=None
        )
        return data
    return None




@method_decorator(csrf_exempt, name='dispatch')
class versionTblView(View):
    def post(self, request):
        status = {
            "status": False,
            "msg": "Error Occured!",
            "data": None
        }
        
        try:
            data = json.loads(request.body)
            
            if data.get("version"):
                if versionTbl.objects.filter(version=data["version"]).exists():
                    status["status"] = True
                    status["msg"] = "successful"
                else:
                    status["status"] = False
                    status["msg"] = "not successful"
            else:
                status["status"] = False
                status["msg"] = "version field is required"

        except json.JSONDecodeError as e:
            status["msg"] = "Invalid JSON format"
            status["data"] = str(e)
        except Exception as e:
            status["msg"] = "Error Occurred!"
            status["data"] = str(e)
            
        return JsonResponse(status, safe=False)




# ============== 1. AUTHENTICATION & USER ==============

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    """Handle user login (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            username = data.get("username", "")
            password = data.get("password", "")
            
            if not username or not password:
                status["message"] = "Username and password are required"
                return JsonResponse(status, status=400)
            
            # Try to find staff by contact or email
            staff = staffTbl.objects.filter(
                contact = username,
                password = password
            )
            
            if staff.exists():
                staff = staff.first()
                # Check password (assuming simple password check for now)
                # In production, you should use proper authentication
                status["status"] = True
                status["message"] = "Login successful"
                status["data"] = {
                    "user_id": staff.id,
                    "first_name": staff.first_name,
                    "last_name": staff.last_name,
                    "email": staff.email_address if staff.email_address else "",
                    "contact": staff.contact,
                    "staff_id": staff.staffid if staff.staffid else "",
                    "project_id": staff.projectTbl_foreignkey.id if staff.projectTbl_foreignkey else None,
                    "project_name": staff.projectTbl_foreignkey.name if staff.projectTbl_foreignkey else "",
                    "district_id": staff.projectTbl_foreignkey.district.id if staff.projectTbl_foreignkey and staff.projectTbl_foreignkey.district else None,
                    "district_name": staff.projectTbl_foreignkey.district.name if staff.projectTbl_foreignkey and staff.projectTbl_foreignkey.district else None
                }
            else:
                status["message"] = "Invalid username or password"
                
        except json.JSONDecodeError:
            status["message"] = "Invalid JSON data"
            return JsonResponse(status, status=400)
        except Exception as e:
            status["message"] = f"Error occurred: {str(e)}"
            
        return JsonResponse(status)

# ============== 2. DAILY REPORTING / ACTIVITY REPORTING ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveActivityReportView(View):
    """Handle daily reporting and activity reporting (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID already exists
            if uid and  ActivityReportingModel.objects.filter(uid=uid).exists():
                status["message"] = "Report with this UID already exists"
                status["data"] = {"uid": uid}
                return JsonResponse(status)
            
            # Get agent
            agent = None
            agent_id = data.get("agent", "")
            if agent_id:
                try:
                    agent = staffTbl.objects.get(id=agent_id)
                except:
                    pass
            
            # Get farm
            farm = None
            farm_ref = data.get("farm_ref_number", "")
            if farm_ref:
                try:
                    farm = FarmdetailsTbl.objects.get(farm_reference=farm_ref)
                except:
                    pass
            
            # Get community
            community = None
            community_id = data.get("community", "")
            if community_id:
                try:
                    community = Community.objects.get(id=community_id)
                except:
                    # Try by name if ID doesn't work
                    try:
                        community = Community.objects.get(name=community_id)
                    except:
                        pass
            
            # Get district (from farm or agent's project)
            district = None
            if farm and farm.district:
                district = farm.district
            elif agent and agent.projectTbl_foreignkey and agent.projectTbl_foreignkey.district:
                district = agent.projectTbl_foreignkey.district
            
            # Get project
            project = None
            if agent and agent.projectTbl_foreignkey:
                project = agent.projectTbl_foreignkey
            
            # Get activities
            main_activity_obj = None
            activity_obj = None
            main_activity_code = data.get("main_activity", "")
            activity_code = data.get("activity", "")
            
            if main_activity_code:
                try:
                    main_activity_obj = Activities.objects.get(id=main_activity_code)
                except:
                    pass
            
            if activity_code:
                try:
                    activity_obj = Activities.objects.get(id=activity_code)
                except:
                    pass
            
            # Parse RAS if it's a list
            ras_ids = data.get("ras", [])
            
            # Create daily report
            report = ActivityReportingModel.objects.create(
                uid=uid,
                agent=agent,
                completion_date=data.get("completion_date"),
                reporting_date=data.get("reporting_date"),
                main_activity=main_activity_obj,
                activity=activity_obj,
                no_rehab_assistants=data.get("no_rehab_assistants", 0),
                area_covered_ha=data.get("area_covered_ha", 0.0),
                remark=data.get("remark", ""),
                status=data.get("status", 0),
                farm=farm,
                farm_ref_number=farm_ref,
                farm_size_ha=data.get("farm_size_ha", 0.0),
                community=community,
                number_of_people_in_group=data.get("number_of_people_in_group", 0),
                group_work=data.get("group_work", ""),
                sector=data.get("sector"),
                projectTbl_foreignkey=project,
                district=district
            )
            
            # Add RAS if provided
            if ras_ids:
                for ra_id in ras_ids:
                    try:
                        ra = PersonnelModel.objects.get(id=ra_id)
                        report.ras.add(ra)
                    except:
                        continue
            
            status["status"] = True
            status["message"] = "Activity report saved successfully"
            status["data"] = {
                "uid": report.uid,
                "id": report.id
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status)
    


@method_decorator(csrf_exempt, name='dispatch')
class SaveDailyReportView(View):
    """Handle daily reporting and activity reporting (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            # print(data)
            
            uid = data.get("uid", "")
            
            # Check if UID already exists
            if uid and DailyReportingModel.objects.filter(uid=uid).exists():
                status["message"] = "Report with this UID already exists"
                status["data"] = {"uid": uid}
                return JsonResponse(status)
            
            # Get agent
            agent = None
            agent_id = data.get("agent", "")
            if agent_id:
                try:
                    agent = staffTbl.objects.get(id=agent_id)
                except:
                    pass
            
            # Get farm
            farm = None
            farm_ref = data.get("farm_ref_number", "")
            if farm_ref:
                try:
                    farm = FarmdetailsTbl.objects.get(farm_reference=farm_ref)
                except:
                    pass
            
            # Get community
            community = None
            community_id = data.get("community", "")
            if community_id:
                try:
                    community = Community.objects.get(id=community_id)
                except:
                    # Try by name if ID doesn't work
                    try:
                        community = Community.objects.get(name=community_id)
                    except:
                        pass
            
            # Get district (from farm or agent's project)
            district = None
            if farm and farm.district:
                district = farm.district
            elif agent and agent.projectTbl_foreignkey and agent.projectTbl_foreignkey.district:
                district = agent.projectTbl_foreignkey.district
            
            # Get project
            project = None
            if agent and agent.projectTbl_foreignkey:
                project = agent.projectTbl_foreignkey
            
            # Get activities
            main_activity_obj = None
            activity_obj = None
            main_activity_code = data.get("main_activity", "")
            activity_code = data.get("activity", "")
            
            print(main_activity_code, activity_code)

            main_activity_obj = Activities.objects.get(id=main_activity_code)
               
            activity_obj = Activities.objects.get(id=activity_code)

            # Parse RAS if it's a list
            ras_ids = data.get("ras", [])
            
            # Create daily report
            report = DailyReportingModel.objects.create(
                uid=uid,
                agent=agent,
                completion_date=data.get("completion_date"),
                reporting_date=data.get("reporting_date"),
                main_activity=main_activity_obj,
                activity=activity_obj,
                no_rehab_assistants=data.get("no_rehab_assistants", 0),
                area_covered_ha=data.get("area_covered_ha", 0.0),
                remark=data.get("remark", ""),
                status=data.get("status", 0),
                farm=farm,
                farm_ref_number=farm_ref,
                farm_size_ha=data.get("farm_size_ha", 0.0),
                community=community,
                number_of_people_in_group=data.get("number_of_people_in_group", 0),
                group_work=data.get("group_work", ""),
                sector=data.get("sector"),
                projectTbl_foreignkey=project,
                district=district
            )

            print(report)
            
            # Add RAS if provided
            if ras_ids:
                for ra_id in ras_ids:
                    try:
                        ra = PersonnelModel.objects.get(id=ra_id)
                        report.ras.add(ra)
                    except:
                        continue
            
            status["status"] = True
            status["message"] = "Activity report saved successfully"
            status["data"] = {
                "uid": report.uid,
                "id": report.id
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status)


# ============== 3. FARM BOUNDARY ==============
from django.contrib.gis.geos import Polygon, MultiPolygon
import json

@method_decorator(csrf_exempt, name='dispatch')
class SaveMappedFarmView(View):
    """Handle farm boundary mapping (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID already exists
            if uid and mappedFarms.objects.filter(uid=uid).exists():
                status["message"] = "Farm boundary with this UID already exists"
                status["data"] = {"uid": uid}
                return JsonResponse(status)
            
            # Get staff
            staff = None
            staff_id = data.get("staffTbl_foreignkey", "")
            if staff_id:
                try:
                    staff = staffTbl.objects.get(id=staff_id)
                except:
                    pass
            
            # Get farmboundary string
            farmboundary = data.get("farmboundary", "")
            
            # Convert string coordinates to GEOS geometry
            geom = None
            if farmboundary:
                try:
                    # Parse the JSON string
                    coords = json.loads(farmboundary)
                    
                    # You need at least 3 points to form a polygon
                    if len(coords) >= 3:
                        # Convert to tuple format (lng, lat) - note the order: lng first, then lat
                        polygon_coords = []
                        for coord in coords:
                            if len(coord) == 2:
                                lng = float(coord[0])
                                lat = float(coord[1])
                                polygon_coords.append((lng, lat))
                        
                        # IMPORTANT: Close the polygon (add first point at the end)
                        if polygon_coords and polygon_coords[0] != polygon_coords[-1]:
                            polygon_coords.append(polygon_coords[0])
                        
                        # Create Polygon - note the extra parentheses
                        # Polygon requires a sequence of coordinates: ((x1 y1, x2 y2, x3 y3, x1 y1),)
                        polygon = Polygon(polygon_coords)
                        
                        # Ensure polygon is valid
                        if polygon.valid:
                            # Wrap in MultiPolygon
                            geom = MultiPolygon(polygon)
                            geom.srid = 4326  # Set coordinate system
                            
                except Exception as e:
                    print(f"Error creating geometry: {e}")
            
            # Create the farm record
            farm = mappedFarms.objects.create(
                uid=uid,
                farm_reference=data.get("farm_reference", ""),
                farm_area=data.get("farm_area", 0.0),
                farmer_name=data.get("farmer_name", ""),
                location=data.get("location", ""),
                contact=data.get("contact", ""),
                staffTbl_foreignkey=staff,
                farmboundary=farmboundary,
                geom=geom
            )
            
            status["status"] = True
            status["message"] = "Farm boundary saved successfully"
            status["data"] = {
                "uid": farm.uid,
                "id": farm.id
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status)
# ============== 4. ADD PERSONNEL ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveRegisterView(View):
    """Handle personnel registration (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            # Get district
            district = None
            district_id = data.get("district", "")
            if district_id:
                try:
                    district = cocoaDistrict.objects.get(id=district_id)
                except:
                    # Try by name if ID doesn't work
                    try:
                        district = cocoaDistrict.objects.get(name=district_id)
                    except:
                        pass
            
            # Get community
            community = None
            community_name = data.get("community", "")
            if community_name and district:
                try:
                    community = Community.objects.get(name=community_name, district=district)
                except Community.DoesNotExist:
                    # Create community if it doesn't exist
                    community = Community.objects.create(
                        name=community_name,
                        district=district
                    )
                except:
                    pass
            
            # Get project based on district
            project = None
            if district:
                try:
                    project = projectTbl.objects.get(district=district)
                except:
                    pass
            
            # Save images if provided
            primary_phone = data.get("primary_phone_number", "")
            image = save_image(data.get("image", ""), f"{primary_phone}_image") if data.get("image") else None
            id_image_front = save_image(data.get("id_image_front", ""), f"{primary_phone}_id_front") if data.get("id_image_front") else None
            id_image_back = save_image(data.get("id_image_back", ""), f"{primary_phone}_id_back") if data.get("id_image_back") else None
            consent_form_image = save_image(data.get("consent_form_image", ""), f"{primary_phone}_consent") if data.get("consent_form_image") else None
            
            # Create personnel record
            personnel = PersonnelModel.objects.create(
                first_name=data.get("first_name", ""),
                surname=data.get("surname", ""),
                other_names=data.get("other_names", ""),
                gender=data.get("gender", ""),
                date_of_birth=data.get("date_of_birth"),
                primary_phone_number=primary_phone,
                secondary_phone_number=data.get("secondary_phone_number", ""),
                momo_number=data.get("momo_number", ""),
                momo_name=data.get("momo_name", ""),
                belongs_to_ra=data.get("belongs_to_ra", False),
                emergency_contact_person=data.get("emergency_contact_person", ""),
                emergency_contact_number=data.get("emergency_contact_number", ""),
                id_type=data.get("id_type", ""),
                id_number=data.get("id_number", ""),
                address=data.get("address", ""),
                community=community,
                district=district,
                projectTbl_foreignkey=project,
                education_level=data.get("education_level", ""),
                marital_status=data.get("marital_status", ""),
                bank_id=data.get("bank_id", ""),
                bank_name=data.get("bank_name", ""),
                bank_branch=data.get("bank_branch", ""),
                account_number=data.get("account_number", ""),
                branch_id=data.get("branch_id", ""),
                sort_code=data.get("sort_code", ""),
                personnel_type=data.get("personnel_type", ""),
                SSNIT_number=data.get("SSNIT_number", ""),
                ezwich_number=data.get("ezwich_number", ""),
                date_joined=data.get("date_joined"),
                supervisor_id=data.get("supervisor_id", ""),
                image=image,
                id_image_front=id_image_front,
                id_image_back=id_image_back,
                consent_form_image=consent_form_image,
                uid=data.get("uid", "")
            )
            
            status["status"] = True
            status["message"] = "Personnel registered successfully"
            status["data"] = {
                "id": personnel.id,
                "uid": personnel.uid,
                "name": f"{personnel.first_name} {personnel.surname}"
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            print(traceback.format_exc())
            print(e)
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status)

# ============== 5. ASSIGN REHAB ASSISTANT (RA) ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveRehabAssignmentView(View):
    """Handle rehab assistant assignment (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID already exists
            if uid and PersonnelAssignmentModel.objects.filter(uid=uid).exists():
                status["message"] = "Assignment with this UID already exists"
                status["data"] = {"uid": uid}
                return JsonResponse(status)
            
            # Get PO (Project Officer)
            po = None
            po_id = data.get("po_id", "")
            if po_id:
                try:
                    po = staffTbl.objects.get(id=po_id)
                except:
                    pass
            
            # Get RA (Rehab Assistant)
            ra = None
            ra_id = data.get("ra_id", "")
            if ra_id:
                try:
                    ra = PersonnelModel.objects.get(id=ra_id)
                except:
                    pass
            
            # Get district
            district = None
            district_id = data.get("district_id", "")
            if district_id:
                try:
                    district = cocoaDistrict.objects.get(id=district_id)
                except:
                    try:
                        district = cocoaDistrict.objects.get(name=district_id)
                    except:
                        pass
            
            # Get community
            community = None
            community_id = data.get("community_id", "")
            if community_id:
                try:
                    community = Community.objects.get(id=community_id)
                except:
                    try:
                        community = Community.objects.get(name=community_id)
                    except:
                        pass
            
            # Get project (from PO or district)
            project = None
            if po and po.projectTbl_foreignkey:
                project = po.projectTbl_foreignkey
            elif district:
                try:
                    project = projectTbl.objects.get(district=district)
                except:
                    pass
            
            # Create personnel assignment
            assignment = PersonnelAssignmentModel.objects.create(
                uid=uid,
                po=po,
                ra=ra,
                projectTbl_foreignkey=project,
                district=district,
                community=community,
                date_assigned=data.get("date_assigned"),
                status=data.get("status", 0)
            )
            
            status["status"] = True
            status["message"] = "Rehab assistant assigned successfully"
            status["data"] = {
                "uid": assignment.uid,
                "id": assignment.id
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status)

# ============== 6. GROWTH MONITORING ==============
# ============== 6. GROWTH MONITORING ==============
@method_decorator(csrf_exempt, name='dispatch')
class GrowthMonitoringView(View):
    """Handle growth monitoring - supports single and batch POST"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Check if it's a batch request (list) or single request (dict)
            if isinstance(data, list):
                return self.handle_batch_request(data)
            else:
                return self.handle_single_request(data)
                
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
    
    def handle_single_request(self, data):
        """Handle single growth monitoring record"""
        status = {"status": False, "message": "", "data": {}}
        
        uid = data.get("uid", "")
        
        # Check if UID already exists
        if uid and GrowthMonitoringModel.objects.filter(uid=uid).exists():
            status["message"] = "Growth monitoring record with this UID already exists"
            status["data"] = {"uid": uid}
            return JsonResponse(status)
        
        # Get or create QR code based on plant_uid
        plant_uid = data.get("plant_uid", "")
        qr_code = None
        
        if plant_uid:
            # Try to find existing QR code with this UID
            try:
                qr_code = QR_CodeModel.objects.get(uid=plant_uid)
            except QR_CodeModel.DoesNotExist:
                # Create new QR code if it doesn't exist
                qr_code = QR_CodeModel.objects.create(
                    uid=plant_uid,
                    qr_code=None  # QR image will be generated later if needed
                )
        
        # Get agent
        agent = None
        agent_id = data.get("agent", "")
        if agent_id:
            try:
                agent = staffTbl.objects.get(id=agent_id)
            except staffTbl.DoesNotExist:
                pass
        
        # Get district and project from agent
        district = None
        project = None
        if agent and agent.projectTbl_foreignkey:
            project = agent.projectTbl_foreignkey
            if project.district:
                district = project.district
        
        # Create growth monitoring record
        record = GrowthMonitoringModel.objects.create(
            uid=uid or None,
            plant_uid=plant_uid,
            number_of_leaves=data.get("number_of_leaves", 0),
            height=data.get("height", 0.0),
            stem_size=data.get("stem_size", 0.0),
            leaf_color=data.get("leaf_color", ""),
            date=data.get("date", timezone.now().date()),
            lat=data.get("lat", 0.0),
            lng=data.get("lng", 0.0),
            qr_code=qr_code,
            agent=agent,
            projectTbl_foreignkey=project,
            district=district
        )
        
        status["status"] = True
        status["message"] = "Growth monitoring record saved successfully"
        status["data"] = self.format_record_response(record, agent, district, project, qr_code)
        
        return JsonResponse(status)
    
    def handle_batch_request(self, data_list):
        """Handle multiple growth monitoring records"""
        status = {"status": False, "message": "", "data": {}}
        
        successful_records = []
        failed_records = []
        
        # Cache for QR codes and agents to avoid repeated DB queries
        qr_code_cache = {}
        agent_cache = {}
        
        for index, record_data in enumerate(data_list):
            try:
                uid = record_data.get("uid", "")
                
                # Skip if UID already exists
                if uid and GrowthMonitoringModel.objects.filter(uid=uid).exists():
                    failed_records.append({
                        "index": index,
                        "plant_uid": record_data.get("plant_uid", ""),
                        "error": f"Record with UID {uid} already exists"
                    })
                    continue
                
                # Get or create QR code based on plant_uid
                plant_uid = record_data.get("plant_uid", "")
                qr_code = None
                
                if plant_uid:
                    if plant_uid in qr_code_cache:
                        qr_code = qr_code_cache[plant_uid]
                    else:
                        try:
                            qr_code = QR_CodeModel.objects.get(uid=plant_uid)
                        except QR_CodeModel.DoesNotExist:
                            qr_code = QR_CodeModel.objects.create(
                                uid=plant_uid,
                                qr_code=None
                            )
                        qr_code_cache[plant_uid] = qr_code
                
                # Get agent
                agent = None
                agent_id = record_data.get("agent", "")
                if agent_id:
                    if agent_id in agent_cache:
                        agent = agent_cache[agent_id]
                    else:
                        try:
                            agent = staffTbl.objects.get(id=agent_id)
                            agent_cache[agent_id] = agent
                        except staffTbl.DoesNotExist:
                            pass
                
                # Get district and project from agent
                district = None
                project = None
                if agent and agent.projectTbl_foreignkey:
                    project = agent.projectTbl_foreignkey
                    if project.district:
                        district = project.district
                
                # Create growth monitoring record
                record = GrowthMonitoringModel.objects.create(
                    uid=uid or None,
                    plant_uid=plant_uid,
                    number_of_leaves=record_data.get("number_of_leaves", 0),
                    height=record_data.get("height", 0.0),
                    stem_size=record_data.get("stem_size", 0.0),
                    leaf_color=record_data.get("leaf_color", ""),
                    date=record_data.get("date", timezone.now().date()),
                    lat=record_data.get("lat", 0.0),
                    lng=record_data.get("lng", 0.0),
                    qr_code=qr_code,
                    agent=agent,
                    projectTbl_foreignkey=project,
                    district=district
                )
                
                successful_records.append(self.format_record_response(
                    record, agent, district, project, qr_code
                ))
                
            except Exception as e:
                failed_records.append({
                    "index": index,
                    "plant_uid": record_data.get("plant_uid", ""),
                    "error": str(e)
                })
        
        status["status"] = True
        status["message"] = f"Processed {len(successful_records)} records, {len(failed_records)} failed"
        status["data"] = {
            "successful": successful_records,
            "failed": failed_records,
            "total_processed": len(successful_records) + len(failed_records),
            "success_count": len(successful_records),
            "failure_count": len(failed_records)
        }
        
        return JsonResponse(status)
    
    def format_record_response(self, record, agent, district, project, qr_code):
        """Format record data for response"""
        return {
            "id": record.id,
            "uid": record.uid,
            "plant_uid": record.plant_uid,
            "qr_code": {
                "id": qr_code.id if qr_code else None,
                "uid": qr_code.uid if qr_code else None,
                "qr_image_url": qr_code.qr_code.url if qr_code and qr_code.qr_code else None
            },
            "measurements": {
                "height": record.height,
                "leaves": record.number_of_leaves,
                "stem_size": record.stem_size,
                "leaf_color": record.leaf_color
            },
            "location": {
                "lat": record.lat,
                "lng": record.lng
            },
            "agent": {
                "id": agent.id if agent else None,
                "name": f"{agent.first_name} {agent.last_name}".strip() if agent else None
            },
            "district": district.name if district else None,
            "project": project.name if project else None,
            # "date": record.date.strftime('%Y-%m-%d'),
            # "created_at": record.created_date.strftime('%Y-%m-%d %H:%M:%S') if hasattr(record, 'created_date') else None
        }
    

# ============== 7. OUTBREAK FARM ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveOutbreakFarmView(View):
    """Handle outbreak farm reporting (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID already exists
            if uid and OutbreakFarmModel.objects.filter(uid=uid).exists():
                status["message"] = "Outbreak farm record with this UID already exists"
                status["data"] = {"uid": uid}
                return JsonResponse(status)
            
            # Get reported by
            reported_by = None
            reported_by_id = data.get("reported_by", "")
            if reported_by_id:
                try:
                    reported_by = staffTbl.objects.get(id=reported_by_id)
                except:
                    pass
            
            # Get community
            community = None
            community_name = data.get("community", "")
            if community_name:
                try:
                    community = Community.objects.get(name=community_name)
                except:
                    pass
            
            # Get district (from community or agent's project)
            district = None
            region = None
            project = None
            
            if community and community.district:
                district = community.district
                region = community.district.region
            
            if reported_by and reported_by.projectTbl_foreignkey:
                project = reported_by.projectTbl_foreignkey
                if project.district and not district:
                    district = project.district
                    region = project.district.region
            
            # Create geometry from coordinates if provided
            geom = None
            coordinates = data.get("coordinates", "")
            if coordinates:
                try:
                    lat, lng = map(float, coordinates.split(','))
                    geom = Point(lng, lat)
                except:
                    pass
            
            # Create outbreak farm record
            outbreak = OutbreakFarmModel.objects.create(
                uid=uid,
                farmer_name=data.get("farmer_name", ""),
                farm_location=data.get("farm_location", ""),
                community=community,
                farm_size=data.get("farm_size", 0.0),
                disease_type=data.get("disease_type", ""),
                date_reported=data.get("date_reported"),
                reported_by=reported_by,
                status=data.get("status", 0),
                coordinates=coordinates,
                geom=geom,
                projectTbl_foreignkey=project,
                district=district,
                region=region
            )
            
            status["status"] = True
            status["message"] = "Outbreak farm record saved successfully"
            status["data"] = {
                "uid": outbreak.uid,
                "id": outbreak.id
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status)

# ============== 8. CONTRACTOR CERTIFICATE ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveContractorCertificateView(View):
    """Handle contractor certificate (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID already exists
            if uid and ContractorCertificateModel.objects.filter(uid=uid).exists():
                status["message"] = "Contractor certificate with this UID already exists"
                status["data"] = {"uid": uid}
                return JsonResponse(status)
            
            # Get contractor
            contractor = None
            contractor_id = data.get("contractor_id", "")
            if contractor_id:
                try:
                    contractor = contractorsTbl.objects.get(id=contractor_id)
                except:
                    try:
                        contractor = contractorsTbl.objects.get(contractor_name=contractor_id)
                    except:
                        pass
            
            # Get district (from contractor or context)
            district = None
            project = None
            
            if contractor and contractor.district:
                district = contractor.district
            
            # Try to get project from district
            if district:
                try:
                    project = projectTbl.objects.get(district=district)
                except:
                    pass
            
            # Create contractor certificate
            certificate = ContractorCertificateModel.objects.create(
                uid=uid,
                contractor=contractor,
                work_type=data.get("work_type", ""),
                start_date=data.get("start_date"),
                end_date=data.get("end_date"),
                status=data.get("status", "Pending"),
                remarks=data.get("remarks", ""),
                projectTbl_foreignkey=project,
                district=district
            )
            
            status["status"] = True
            status["message"] = "Contractor certificate saved successfully"
            status["data"] = {
                "uid": certificate.uid,
                "id": certificate.id
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status)

# ============== 9. CONTRACTOR CERTIFICATE VERIFICATION ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveVerificationFarmsView(View):
    """Handle contractor certificate verification (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID already exists
            if uid and ContractorCertificateVerificationModel.objects.filter(uid=uid).exists():
                status["message"] = "Certificate verification with this UID already exists"
                status["data"] = {"uid": uid}
                return JsonResponse(status)
            
            # Get certificate
            certificate = None
            certificate_id = data.get("certificate_id", "")
            if certificate_id:
                try:
                    certificate = ContractorCertificateModel.objects.get(uid=certificate_id)
                except:
                    try:
                        certificate = ContractorCertificateModel.objects.get(id=certificate_id)
                    except:
                        pass
            
            # Get verified by
            verified_by = None
            verified_by_id = data.get("verified_by", "")
            if verified_by_id:
                try:
                    verified_by = staffTbl.objects.get(id=verified_by_id)
                except:
                    pass
            
            # Get district (from certificate or verifier)
            district = None
            project = None
            
            if certificate and certificate.district:
                district = certificate.district
                project = certificate.projectTbl_foreignkey
            elif verified_by and verified_by.projectTbl_foreignkey:
                project = verified_by.projectTbl_foreignkey
                if project.district:
                    district = project.district
            
            # Create certificate verification
            verification = ContractorCertificateVerificationModel.objects.create(
                uid=uid,
                certificate=certificate,
                verified_by=verified_by,
                verification_date=data.get("verification_date"),
                is_verified=data.get("is_verified", False),
                comments=data.get("comments", ""),
                projectTbl_foreignkey=project,
                district=district
            )
            
            status["status"] = True
            status["message"] = "Certificate verification saved successfully"
            status["data"] = {
                "uid": verification.uid,
                "id": verification.id
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status)

# ============== 10. SUBMIT ISSUE / FEEDBACK ==============

# @method_decorator(csrf_exempt, name='dispatch')
# class SaveFeedbackView(View):
#     """Handle issue/feedback submission (POST only)"""
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             status = {"status": False, "message": "", "data": {}}
            
#             uid = data.get("uid", "")
            
#             # Check if UID already exists
#             if uid and IssueModel.objects.filter(uid=uid).exists():
#                 status["message"] = "Issue with this UID already exists"
#                 status["data"] = {"uid": uid}
#                 return JsonResponse(status)
            
#             # Get user
#             user = None
#             user_id = data.get("user_id", "")
#             if user_id:
#                 try:
#                     user = staffTbl.objects.get(id=user_id)
#                 except:
#                     pass
            
#             # Get district and project from user
#             district = None
#             project = None
            
#             if user and user.projectTbl_foreignkey:
#                 project = user.projectTbl_foreignkey
#                 if project.district:
#                     district = project.district
            
#             # Create issue
#             issue = IssueModel.objects.create(
#                 uid=uid,
#                 user=user,
#                 issue_type=data.get("issue_type", ""),
#                 description=data.get("description", ""),
#                 date_reported=data.get("date_reported"),
#                 status=data.get("status", 0),
#                 projectTbl_foreignkey=project,
#                 district=district
#             )
            
#             status["status"] = True
#             status["message"] = "Issue/feedback submitted successfully"
#             status["data"] = {
#                 "uid": issue.uid,
#                 "id": issue.id
#             }
            
#         except json.JSONDecodeError:
#             return JsonResponse({
#                 "status": False,
#                 "message": "Invalid JSON data",
#                 "data": {}
#             }, status=400)
#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": f"Error occurred: {str(e)}",
#                 "data": {}
#             }, status=500)
            
#         return JsonResponse(status)

@method_decorator(csrf_exempt, name='dispatch')
class SaveFeedbackView(View):
    """Handle issue/feedback submission (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status_response = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID already exists (optional - remove if you want to allow multiple feedbacks with same UID)
            if uid and Feedback.objects.filter(uid=uid).exists():
                status_response["message"] = "Feedback with this UID already exists"
                status_response["data"] = {"uid": uid}
                return JsonResponse(status_response)
            
            # Get staff user
            staff = None
            staff_id = data.get("staff_id", "") or data.get("user_id", "")  # Accept both field names
            if staff_id:
                try:
                    staff = staffTbl.objects.get(id=staff_id)
                except staffTbl.DoesNotExist:
                    pass
            
            # Create feedback
            feedback = Feedback.objects.create(
                staffTbl_foreignkey=staff,
                title=data.get("title", ""),
                feedback=data.get("feedback", "") or data.get("description", ""),  # Accept both
                uid=uid,
                farm_reference=data.get("farm_reference", ""),
                activity=data.get("activity", ""),
                ra_id=data.get("ra_id", ""),
                Status=data.get("status", "Open") or data.get("Status", "Open"),  # Accept both cases
                # sent_date will be auto_now=True, so no need to set it
            )
            
            status_response["status"] = True
            status_response["message"] = "Feedback submitted successfully"
            status_response["data"] = {
                "id": feedback.id,
                "uid": feedback.uid,
                "title": feedback.title,
                "status": feedback.Status,
                "created_at": feedback.sent_date.isoformat() if feedback.sent_date else None
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status_response)

# ============== 11. IRRIGATION ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveIrrigationView(View):
    """Handle irrigation reporting (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID already exists
            if uid and IrrigationModel.objects.filter(uid=uid).exists():
                status["message"] = "Irrigation record with this UID already exists"
                status["data"] = {"uid": uid}
                return JsonResponse(status)
            
            # Get farm
            farm = None
            farm_id = data.get("farm_id", "")
            if farm_id:
                try:
                    farm = FarmdetailsTbl.objects.get(id=farm_id)
                except:
                    try:
                        farm = FarmdetailsTbl.objects.get(farm_reference=farm_id)
                    except:
                        pass
            
            # Get agent
            agent = None
            agent_id = data.get("agent", "")
            if agent_id:
                try:
                    agent = staffTbl.objects.get(id=agent_id)
                except:
                    pass
            
            # Get district and project
            district = None
            project = None
            
            if farm and farm.district:
                district = farm.district
                project = farm.projectTbl_foreignkey
            elif agent and agent.projectTbl_foreignkey:
                project = agent.projectTbl_foreignkey
                if project.district:
                    district = project.district
            
            # Create irrigation record
            irrigation = IrrigationModel.objects.create(
                uid=uid,
                farm=farm,
                irrigation_type=data.get("irrigation_type", ""),
                water_volume=data.get("water_volume", 0.0),
                date=data.get("date"),
                agent=agent,
                projectTbl_foreignkey=project,
                district=district
            )
            
            status["status"] = True
            status["message"] = "Irrigation record saved successfully"
            status["data"] = {
                "uid": irrigation.uid,
                "id": irrigation.id
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status)

# ============== 12. GENERAL DATA LOADING ==============

@method_decorator(csrf_exempt, name='dispatch')
class FetchRegionDistrictsView(View):
    """Load regions and districts (GET)"""
    def get(self, request):
        try:
            regions = Region.objects.all()
            region_data = []
            
            for region in regions:
                districts = cocoaDistrict.objects.filter(region=region)
                district_list = []
                
                for district in districts:
                    district_list.append({
                        "id": district.id,
                        "name": district.name,
                        "district_code": district.district_code,
                        "shape_area": district.shape_area
                    })
                
                region_data.append({
                    "id": region.id,
                    "name": region.region,
                    "region_code": region.reg_code,
                    "districts": district_list
                })
            
            return JsonResponse({
                "status": True,
                "message": f"Found {len(regions)} regions",
                "data": region_data
            })
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FetchAllContractorsView(View):
    """Load contractors (GET)"""
    def get(self, request):
        try:
            contractors = contractorsTbl.objects.all()
            contractor_data = []
            
            for contractor in contractors:
                contractor_data.append({
                    "id": contractor.id,
                    "contractor_name": contractor.contractor_name,
                    "contact_person": contractor.contact_person,
                    "address": contractor.address,
                    "contact_number": contractor.contact_number,
                    "interested_services": contractor.interested_services,
                    "target": contractor.target,
                    "district_id": contractor.district.id if contractor.district else None,
                    "district_name": contractor.district.name if contractor.district else None
                })
            
            return JsonResponse({
                "status": True,
                "message": f"Found {len(contractor_data)} contractors",
                "data": contractor_data
            })
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FetchActivitiesView(View):
    """Load activities (GET)"""
    def get(self, request):
        try:
            activities = Activities.objects.all()
            activity_data = []
            
            for activity in activities:
                activity_data.append({
                    "id": activity.id,
                    "main_activity": activity.main_activity,
                    "sub_activity": activity.sub_activity,
                    "activity_code": activity.activity_code,
                    "required_equipment": activity.required_equipment
                })
            
            return JsonResponse({
                "status": True,
                "message": f"Found {len(activity_data)} activities",
                "data": activity_data
            })
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FetchFarmsView(View):
    """Load farms (GET)"""
    def get(self, request):
        try:
            user_id = request.GET.get('user_id')
            
            # If user_id is provided, get their assigned farms
            if user_id:
                try:
                    staff = staffTbl.objects.get(id=user_id)
                    project = staff.projectTbl_foreignkey
                    if project:
                        farms = FarmdetailsTbl.objects.filter(projectTbl_foreignkey=project)
                    else:
                        farms = FarmdetailsTbl.objects.all()
                except:
                    farms = FarmdetailsTbl.objects.all()
            else:
                farms = FarmdetailsTbl.objects.all()
            
            farm_data = []
            for farm in farms:
                farm_data.append({
                    "id": farm.id,
                    "farm_reference": farm.farm_reference,
                    "farmername": farm.farmername,
                    "location": farm.location,
                    "region_id": farm.region.id if farm.region else None,
                    "region_name": farm.region.region if farm.region else None,
                    "district_id": farm.district.id if farm.district else None,
                    "district_name": farm.district.name if farm.district else None,
                    "community_id": farm.community.id if farm.community else None,
                    "community_name": farm.community.name if farm.community else None,
                    "farm_size": farm.farm_size,
                    "status": farm.status,
                    "sector": farm.sector,
                    "project_id": farm.projectTbl_foreignkey.id if farm.projectTbl_foreignkey else None,
                    "project_name": farm.projectTbl_foreignkey.name if farm.projectTbl_foreignkey else None
                })
            
            return JsonResponse({
                "status": True,
                "message": f"Found {len(farm_data)} farms",
                "data": farm_data
            })
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FetchCommunityView(View):
    """Load communities (GET)"""
    def get(self, request):
        try:
            district_id = request.GET.get('district_id')
            
            if district_id:
                try:
                    district = cocoaDistrict.objects.get(id=district_id)
                    communities = Community.objects.filter(district=district)
                except:
                    communities = Community.objects.all()
            else:
                communities = Community.objects.all()
            
            community_data = []
            for community in communities:
                community_data.append({
                    "id": community.id,
                    "name": community.name,
                    "district_id": community.district.id if community.district else None,
                    "district_name": community.district.name if community.district else None,
                    "operational_area": community.operational_area
                })
            
            return JsonResponse({
                "status": True,
                "message": f"Found {len(community_data)} communities",
                "data": community_data
            })
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FetchJobOrderView(View):
    """Load job order farms (GET)"""
    def get(self, request):
        try:
            user_id = request.GET.get('user_id')
            
            # If user_id is provided, get their assigned job orders
            if user_id:
                try:
                    staff = staffTbl.objects.get(id=user_id)
                    project = staff.projectTbl_foreignkey
                    if project:
                        job_orders = Joborder.objects.filter(projectTbl_foreignkey=project)
                    else:
                        job_orders = Joborder.objects.all()
                except:
                    job_orders = Joborder.objects.all()
            else:
                job_orders = Joborder.objects.all()
            
            job_order_data = []
            for job in job_orders:
                job_order_data.append({
                    "id": job.id,
                    "farm_reference": job.farm_reference,
                    "farmername": job.farmername,
                    "location": job.location,
                    "region_id": job.region.id if job.region else None,
                    "region_name": job.region.region if job.region else None,
                    "district_id": job.district.id if job.district else None,
                    "district_name": job.district.name if job.district else None,
                    "community_id": job.community.id if job.community else None,
                    "community_name": job.community.name if job.community else None,
                    "farm_size": job.farm_size,
                    "sector": job.sector,
                    "job_order_code": job.job_order_code,
                    "project_id": job.projectTbl_foreignkey.id if job.projectTbl_foreignkey else None,
                    "project_name": job.projectTbl_foreignkey.name if job.projectTbl_foreignkey else None
                })
            
            return JsonResponse({
                "status": True,
                "message": f"Found {len(job_order_data)} job orders",
                "data": job_order_data
            })
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)

# @method_decorator(csrf_exempt, name='dispatch')
# class FetchRehabAssistantsView(View):
#     """Load rehab assistants (GET)"""
#     def get(self, request):
#         try:
#             user_id = request.GET.get('user_id')
#             district_id = request.GET.get('district_id')
            
#             # Base query
#             query = PersonnelModel.objects.all()
            
#             # Filter by district if provided
#             if district_id:
#                 try:
#                     district = cocoaDistrict.objects.get(id=district_id)
#                     query = query.filter(district=district)
#                 except:
#                     pass
#             # Filter by user's district if user_id provided
#             elif user_id:
#                 try:
#                     staff = staffTbl.objects.get(id=user_id)
#                     if staff.projectTbl_foreignkey and staff.projectTbl_foreignkey.district:
#                         query = query.filter(district=staff.projectTbl_foreignkey.district)
#                 except:
#                     pass
            
#             rehab_data = []
#             for person in query:
#                 rehab_data.append({
#                     "id": person.id,
#                     "uid": person.uid,
#                     "name": f"{person.first_name} {person.surname}",
#                     "phone_number": person.primary_phone_number,
#                     "personnel_type": person.personnel_type,
#                     "district_id": person.district.id if person.district else None,
#                     "district_name": person.district.name if person.district else None,
#                     "community_id": person.community.id if person.community else None,
#                     "community_name": person.community.name if person.community else None,
#                     "project_id": person.projectTbl_foreignkey.id if person.projectTbl_foreignkey else None,
#                     "project_name": person.projectTbl_foreignkey.name if person.projectTbl_foreignkey else None
#                 })
            
#             return JsonResponse({
#                 "status": True,
#                 "message": f"Found {len(rehab_data)} rehab assistants",
#                 "data": rehab_data
#             })
            
#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": f"Error occurred: {str(e)}",
#                 "data": []
#             }, status=500)

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.http import JsonResponse

@method_decorator(csrf_exempt, name='dispatch')
class FetchRehabAssistantsView(View):
    """Load rehab assistants (GET) with pagination"""
    
    def get(self, request):
        try:
            user_id = request.GET.get('user_id')
            district_id = request.GET.get('district_id')
            
            # Pagination parameters
            page = request.GET.get('page', 1)
            page_size = request.GET.get('page_size', 20)  # Default 20 items per page
            # Allow max 100 items per page to prevent abuse
            try:
                page_size = min(int(page_size), 100)
            except (ValueError, TypeError):
                page_size = 20
            
            # Base query with optimized select_related
            query = PersonnelModel.objects.select_related(
                'district', 
                'community', 
                'projectTbl_foreignkey'
            ).all().order_by('id')  # Add ordering for consistent pagination
            
            # Apply filters
            if district_id:
                try:
                    district = cocoaDistrict.objects.get(id=district_id)
                    query = query.filter(district=district)
                except cocoaDistrict.DoesNotExist:
                    pass
            elif user_id:
                try:
                    staff = staffTbl.objects.select_related(
                        'projectTbl_foreignkey__district'
                    ).get(id=user_id)
                    if staff.projectTbl_foreignkey and staff.projectTbl_foreignkey.district:
                        query = query.filter(district=staff.projectTbl_foreignkey.district)
                except staffTbl.DoesNotExist:
                    pass
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            paginator = Paginator(query, page_size)
            
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            
            # Build response data
            rehab_data = []
            for person in page_obj:
                rehab_data.append({
                    "id": person.id,
                    "uid": person.uid,
                    "name": f"{person.first_name} {person.surname}".strip(),
                    "first_name": person.first_name,
                    "surname": person.surname,
                    "phone_number": person.primary_phone_number,
                    "secondary_phone": person.secondary_phone_number,
                    "momo_number": person.momo_number,
                    "momo_name": person.momo_name,
                    "staff_id": person.staff_id,
                    "belongs_to_ra": person.belongs_to_ra,
                    "personnel_type": person.personnel_type,
                    "district_id": person.district.id if person.district else None,
                    "district_name": person.district.name if person.district else None,
                    "community_id": person.community.id if person.community else None,
                    "community_name": person.community.name if person.community else None,
                    "project_id": person.projectTbl_foreignkey.id if person.projectTbl_foreignkey else None,
                    "project_name": person.projectTbl_foreignkey.name if person.projectTbl_foreignkey else None,
                    "gender": person.gender,
                    "id_type": person.id_type,
                    "id_number": person.id_number,
                    "bank_id": person.bank_id,
                    "bank_name": person.bank_name,
                    "bank_branch": person.bank_branch,
                    "ssnit_number": person.SSNIT_number,
                    "account_number": person.account_number,
                    "ezwich_number": person.ezwich_number,
                    "date_joined": person.date_joined.strftime('%Y-%m-%d') if person.date_joined else None,
                    "has_image": bool(person.image),
                    "has_id_front": bool(person.id_image_front),
                    "has_id_back": bool(person.id_image_back),
                })
            
            # Pagination metadata
            pagination_info = {
                "current_page": page_obj.number,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
                "total_records": total_count,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
                "previous_page": page_obj.previous_page_number() if page_obj.has_previous() else None,
            }
            
            return JsonResponse({
                "status": True,
                "message": f"Found {total_count} rehab assistants",
                "data": rehab_data,
                "pagination": pagination_info
            })
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": [],
                "pagination": None
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FetchPOAssignedFarmsView(View):
    """Load assigned farms for PO (GET)"""
    def get(self, request):
        try:
            user_id = request.GET.get('user_id')
            
            if not user_id:
                return JsonResponse({
                    "status": False,
                    "message": "user_id is required",
                    "data": []
                }, status=400)
            
            try:
                staff = staffTbl.objects.get(id=user_id)
                project = staff.projectTbl_foreignkey
                
                if project:
                    farms = FarmdetailsTbl.objects.filter(projectTbl_foreignkey=project)
                    
                    farm_data = []
                    for farm in farms:
                        # Get farm boundary if available from mappedFarms
                        boundary = ""
                        try:
                            mapped_farm = mappedFarms.objects.get(farm_reference=farm.farm_reference)
                            if mapped_farm.farmboundary:
                                boundary = mapped_farm.farmboundary
                        except:
                            pass
                        
                        farm_data.append({
                            "id": farm.id,
                            "farm_boundary": boundary,
                            "farmername": farm.farmername,
                            "location": farm.location,
                            "farm_reference": farm.farm_reference,
                            "farm_size": farm.farm_size,
                            "district_id": farm.district.id if farm.district else None,
                            "district_name": farm.district.name if farm.district else None,
                            "region_id": farm.region.id if farm.region else None,
                            "region_name": farm.region.name if farm.region else None
                        })
                    
                    return JsonResponse({
                        "status": True,
                        "message": f"Found {len(farm_data)} assigned farms",
                        "data": farm_data
                    })
                else:
                    return JsonResponse({
                        "status": False,
                        "message": "User is not assigned to any project",
                        "data": []
                    }, status=404)
                    
            except staffTbl.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "User not found",
                    "data": []
                }, status=404)
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class FetchOutbreakView(View):
    """Load assigned outbreaks (GET)"""
    def get(self, request):
        try:
            user_id = request.GET.get('user_id')
            
            if not user_id:
                return JsonResponse({
                    "status": False,
                    "message": "user_id is required",
                    "data": []
                }, status=400)
            
            try:
                staff = staffTbl.objects.get(id=user_id)
                project = staff.projectTbl_foreignkey
                
                if project:
                    outbreaks = OutbreakFarmModel.objects.filter(projectTbl_foreignkey=project)
                    
                    outbreak_data = []
                    for outbreak in outbreaks:
                        outbreak_data.append({
                            "ob_id": outbreak.id,
                            "ob_code": outbreak.uid,
                            "ob_size": outbreak.farm_size,
                            "district_id": outbreak.district.id if outbreak.district else None,
                            "district_name": outbreak.district.name if outbreak.district else None,
                            "region_id": outbreak.region.id if outbreak.region else None,
                            "region_name": outbreak.region.name if outbreak.region else None,
                            "ob_boundary": outbreak.coordinates if outbreak.coordinates else ""
                        })
                    
                    return JsonResponse({
                        "status": True,
                        "message": f"Found {len(outbreak_data)} outbreaks",
                        "data": outbreak_data
                    })
                else:
                    return JsonResponse({
                        "status": False,
                        "message": "User is not assigned to any project",
                        "data": []
                    }, status=404)
                    
            except staffTbl.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "User not found",
                    "data": []
                }, status=404)
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)

# ============== 13. PAYMENT REPORT ==============

@method_decorator(csrf_exempt, name='dispatch')
class FetchPaymentsView(View):
    """Generate payment report (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": []}
            
            userid = data.get("userid", "")
            month = data.get("month", "")
            week = data.get("week", "")
            year = data.get("year", "")
            
            if not userid or not month or not week or not year:
                status["message"] = "userid, month, week, and year are required"
                return JsonResponse(status, status=400)
            
            try:
                staff = staffTbl.objects.get(id=userid)
                project = staff.projectTbl_foreignkey
                
                if project:
                    # Get personnel in this project for payment report
                    personnel = PersonnelModel.objects.filter(projectTbl_foreignkey=project)
                    
                    payment_data = []
                    for person in personnel:
                        payment_data.append({
                            "ra_id": person.uid or str(person.id),
                            "ra_name": f"{person.first_name} {person.surname}",
                            "district": project.district.name if project.district else "",
                            "bank_name": person.bank_id or "",
                            "bank_branch": person.branch_id or "",
                            "bank_acc_no": person.account_number or "",

                            "snnit_no": person.SSNIT_number or "",
                            "salary": "",  # Would need salary calculation logic
                            "year": year,
                            "po_number": staff.staffid if staff.staffid else "",
                            "month": month,
                            "week": week,
                            "payment_option": "Bank" if person.bank_id else "Momo" if person.momo_number else "Unknown",
                            "momo_acc": person.momo_number or "",
                            "momo_name": person.momo_name or "",
                        })
                    
                    status["status"] = True
                    status["message"] = f"Found {len(payment_data)} payment records"
                    status["data"] = payment_data
                else:
                    status["message"] = "User is not assigned to any project"
                    
            except staffTbl.DoesNotExist:
                status["message"] = "User not found"
                return JsonResponse(status, status=404)
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": []
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)
            
        return JsonResponse(status)

# ============== 14. DETAILED PAYMENT REPORT ==============

@method_decorator(csrf_exempt, name='dispatch')
class FetchPaymentDetailedReportView(View):
    """Generate detailed payment report (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": []}
            
            userid = data.get("userid", "")
            month = data.get("month", "")
            week = data.get("week", "")
            year = data.get("year", "")
            
            if not userid or not month or not week or not year:
                status["message"] = "userid, month, week, and year are required"
                return JsonResponse(status, status=400)
            
            try:
                staff = staffTbl.objects.get(id=userid)
                project = staff.projectTbl_foreignkey
                
                if project:
                    # Get daily reports for this project, month, week, year
                    # This is simplified - in reality you'd need proper date filtering
                    daily_reports = DailyReportingModel.objects.filter(
                        projectTbl_foreignkey=project
                    )
                    
                    detailed_data = []
                    for report in daily_reports:
                        # Get rehab assistants from ManyToMany field
                        ras_list = report.ras.all()
                        
                        for ra in ras_list:
                            detailed_data.append({
                                "group_code": f"GRP{report.id}",
                                "ra_id": ra.uid or str(ra.id),
                                "ra_name": f"{ra.first_name} {ra.surname}",
                                "ra_account": ra.account_number or ra.momo_number or "",
                                "po_id": staff.id,
                                "po_name": f"{staff.first_name} {staff.last_name}",
                                "po_number": staff.staffid or "",
                                "district": project.district.name if project.district else "",
                                "project": project.name,
                                "farmhands_type": "Rehab Assistant",
                                "farm_reference": report.farm_ref_number,
                                "number_in_a_group": ras_list.count(),
                                "activity": report.activity.sub_activity if report.activity else "",
                                "farmsize": report.farm_size_ha,
                                "achievement": report.area_covered_ha,
                                "amount": "",  # Would need rate calculation
                                "week": week,
                                "month": month,
                                "year": year,
                                "issue": report.remark,
                                "sector": report.sector or "",
                                "act_code": report.activity.activity_code if report.activity else ""
                            })
                    
                    status["status"] = True
                    status["message"] = f"Found {len(detailed_data)} detailed payment records"
                    status["data"] = detailed_data
                else:
                    status["message"] = "User is not assigned to any project"
                    
            except staffTbl.DoesNotExist:
                status["message"] = "User not found"
                return JsonResponse(status, status=404)
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": []
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)
            
        return JsonResponse(status)

# ============== 15. ALL FARM QUERY ==============

@method_decorator(csrf_exempt, name='dispatch')
class AllFarmQueryView(View):
    """Get all farms for a user (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": []}
            
            userid = data.get("userid", "")
            district_id = data.get("district_id", "")
            
            if not userid:
                status["message"] = "userid is required"
                return JsonResponse(status, status=400)
            
            try:
                staff = staffTbl.objects.get(id=userid)
                project = staff.projectTbl_foreignkey
                
                if project:
                    farms = FarmdetailsTbl.objects.filter(projectTbl_foreignkey=project)
                    
                    farm_data = []
                    for farm in farms:
                        farm_data.append({
                            "id": farm.id,
                            "farm_reference": farm.farm_reference,
                            "farmername": farm.farmername,
                            "location": farm.location,
                            "region": farm.region.name if farm.region else "",
                            "district": farm.district.name if farm.district else "",
                            "community": farm.community.name if farm.community else "",
                            "farm_size": farm.farm_size,
                            "status": farm.status,
                            "sector": farm.sector,
                            "year_of_establishment": farm.year_of_establishment
                        })
                    
                    status["status"] = True
                    status["message"] = f"Found {len(farm_data)} farms"
                    status["data"] = farm_data
                else:
                    status["message"] = "User is not assigned to any project"
                    
            except staffTbl.DoesNotExist:
                status["message"] = "User not found"
                return JsonResponse(status, status=404)
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": []
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)
            
        return JsonResponse(status)

# ============== 16. WEEKLY SUMMARY REPORT ==============

@method_decorator(csrf_exempt, name='dispatch')
class WeeklySummaryReportView(View):
    """Generate weekly summary report (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": []}
            
            userid = data.get("userid", "")
            month = data.get("month", "")
            week = data.get("week", "")
            year = data.get("year", "")
            
            if not userid or not month or not week or not year:
                status["message"] = "userid, month, week, and year are required"
                return JsonResponse(status, status=400)
            
            try:
                staff = staffTbl.objects.get(id=userid)
                project = staff.projectTbl_foreignkey
                
                if project:
                    # Get daily reports for the specified period
                    # This is simplified - in reality you'd need proper date filtering
                    daily_reports = DailyReportingModel.objects.filter(
                        projectTbl_foreignkey=project,
                        status=1  # Submitted reports only
                    )
                    
                    summary_data = []
                    for report in daily_reports:
                        summary_data.append({
                            "reporting_date": report.reporting_date,
                            "agent": f"{report.agent.first_name} {report.agent.last_name}" if report.agent else "",
                            "farm_reference": report.farm_ref_number,
                            "activity": report.activity.sub_activity if report.activity else "",
                            "area_covered_ha": report.area_covered_ha,
                            "no_rehab_assistants": report.no_rehab_assistants,
                            "community": report.community.name if report.community else "",
                            "district": report.district.name if report.district else "",
                            "remark": report.remark
                        })
                    
                    status["status"] = True
                    status["message"] = f"Found {len(summary_data)} weekly reports"
                    status["data"] = summary_data
                else:
                    status["message"] = "User is not assigned to any project"
                    
            except staffTbl.DoesNotExist:
                status["message"] = "User not found"
                return JsonResponse(status, status=404)
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": []
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)
            
        return JsonResponse(status)

# ============== 17. VERIFICATION (VIDEO RECORD) ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveVerificationRecordView(View):
    """Handle video verification (POST only)"""
    def post(self, request):
        try:
            # This endpoint should handle multipart form data for video upload
            if request.content_type.startswith('multipart/form-data'):
                uid = request.POST.get('uid', '')
                farmRef = request.POST.get('farmRef', '')
                timestamp = request.POST.get('timestamp', '')
                status_val = request.POST.get('status', '0')
                
                # Check if UID already exists
                if uid and VerifyRecord.objects.filter(uid=uid).exists():
                    return JsonResponse({
                        "status": False,
                        "message": "Verification record with this UID already exists",
                        "data": {"uid": uid}
                    })
                
                # Get farm
                farm = None
                if farmRef:
                    try:
                        farm = FarmdetailsTbl.objects.get(farm_reference=farmRef)
                    except:
                        pass
                
                # Get district and project
                district = None
                project = None
                if farm:
                    district = farm.district
                    project = farm.projectTbl_foreignkey
                
                # Create verification record
                verification = VerifyRecord.objects.create(
                    uid=uid,
                    farm=farm,
                    farmRef=farmRef,
                    timestamp=timestamp,
                    status=int(status_val),
                    projectTbl_foreignkey=project,
                    district=district
                )
                
                # Handle video file if provided
                if 'video' in request.FILES:
                    verification.videoPath = request.FILES['video']
                    verification.save()
                
                return JsonResponse({
                    "status": True,
                    "message": "Verification record saved successfully",
                    "data": {
                        "uid": verification.uid,
                        "id": verification.id
                    }
                })
            else:
                # Handle JSON payload (without video)
                data = json.loads(request.body)
                uid = data.get("uid", "")
                
                if uid and VerifyRecord.objects.filter(uid=uid).exists():
                    return JsonResponse({
                        "status": False,
                        "message": "Verification record with this UID already exists",
                        "data": {"uid": uid}
                    })
                
                # Get farm
                farm = None
                farmRef = data.get("farmRef", "")
                if farmRef:
                    try:
                        farm = FarmdetailsTbl.objects.get(farm_reference=farmRef)
                    except:
                        pass
                
                # Get district and project
                district = None
                project = None
                if farm:
                    district = farm.district
                    project = farm.projectTbl_foreignkey
                
                verification = VerifyRecord.objects.create(
                    uid=uid,
                    farm=farm,
                    farmRef=farmRef,
                    timestamp=data.get("timestamp"),
                    status=data.get("status", 0),
                    projectTbl_foreignkey=project,
                    district=district
                )
                
                return JsonResponse({
                    "status": True,
                    "message": "Verification record saved successfully",
                    "data": {
                        "uid": verification.uid,
                        "id": verification.id
                    }
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)

# ============== 18. AREA CALCULATION ==============

# @method_decorator(csrf_exempt, name='dispatch')
# class SaveCalculatedAreaView(View):
#     """Handle area calculation (POST only)"""
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             status = {"status": False, "message": "", "data": {}}
            
#             # Get district if provided in context
#             district = None
#             district_id = data.get("district_id", "")
#             if district_id:
#                 try:
#                     district = cocoaDistrict.objects.get(id=district_id)
#                 except:
#                     pass
            
#             # Get project from district
#             project = None
#             if district:
#                 try:
#                     project = projectTbl.objects.get(district=district)
#                 except:
#                     pass
            
#             # Create calculated area
#             area = CalculatedArea.objects.create(
#                 date=data.get("date"),
#                 title=data.get("title", ""),
#                 value=data.get("value", 0.0),
#                 projectTbl_foreignkey=project,
#                 district=district
#             )
            
#             status["status"] = True
#             status["message"] = "Area calculation saved successfully"
#             status["data"] = {
#                 "id": area.id,
#                 "title": area.title,
#                 "value": area.value
#             }
            
#         except json.JSONDecodeError:
#             return JsonResponse({
#                 "status": False,
#                 "message": "Invalid JSON data",
#                 "data": {}
#             }, status=400)
#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": f"Error occurred: {str(e)}",
#                 "data": {}
#             }, status=500)
            
#         return JsonResponse(status)





# views_api.py
import json
import uuid
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from portal.models import (
    CalculatedArea, EquipmentModel, OutbreakFarmModel, 
    projectTbl, cocoaDistrict, staffTbl, FarmdetailsTbl,
    Community, Region
)

# ============== 1. CALCULATED AREA APIs ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveCalculatedAreaView(View):
    """Save calculated area (POST)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Get district if provided
            district = None
            district_id = data.get("district_id")
            if district_id:
                try:
                    district = cocoaDistrict.objects.get(id=district_id)
                except cocoaDistrict.DoesNotExist:
                    pass
            
            # Get project from district or direct project_id
            project = None
            project_id = data.get("project_id")
            if project_id:
                try:
                    project = projectTbl.objects.get(id=project_id)
                except projectTbl.DoesNotExist:
                    pass
            elif district:
                try:
                    project = projectTbl.objects.filter(district=district).first()
                except:
                    pass
            
            # Create calculated area
            area = CalculatedArea.objects.create(
                date=data.get("date", timezone.now()),
                title=data.get("title", ""),
                value=data.get("value", 0.0),
                geom=data.get("geom") if data.get("geom") else None,
                projectTbl_foreignkey=project,
                district=district
            )
            
            return JsonResponse({
                "status": True,
                "message": "Area calculation saved successfully",
                "data": {
                    "id": area.id,
                    # "date": date,
                    "title": area.title,
                    "value": f"{area.value} ha",
                    "district": area.district.name if area.district else None,
                    "project": area.projectTbl_foreignkey.name if area.projectTbl_foreignkey else None
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class FetchCalculatedAreasView(View):
    """Fetch calculated areas (GET)"""
    def get(self, request):
        try:
            project_id = request.GET.get('project_id')
            district_id = request.GET.get('district_id')
            page = request.GET.get('page', 1)
            page_size = request.GET.get('page_size', 20)
            
            # Base query
            query = CalculatedArea.objects.select_related(
                'district', 'projectTbl_foreignkey'
            ).all().order_by('-date')
            
            # Apply filters
            if project_id:
                query = query.filter(projectTbl_foreignkey_id=project_id)
            if district_id:
                query = query.filter(district_id=district_id)
            
            # Pagination
            paginator = Paginator(query, page_size)
            page_obj = paginator.get_page(page)
            
            data = []
            for area in page_obj:
                data.append({
                    "id": area.id,
                    "date": area.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "title": area.title,
                    "value": f"{area.value} ha",
                    "district_id": area.district.id if area.district else None,
                    "district_name": area.district.name if area.district else None,
                    "project_id": area.projectTbl_foreignkey.id if area.projectTbl_foreignkey else None,
                    "project_name": area.projectTbl_foreignkey.name if area.projectTbl_foreignkey else None
                })
            
            return JsonResponse({
                "status": True,
                "message": "Calculated areas fetched successfully",
                "data": data,
                "pagination": {
                    "current_page": page_obj.number,
                    "total_pages": paginator.num_pages,
                    "total_records": paginator.count,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)


# ============== 2. EQUIPMENT APIs ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveEquipmentView(View):
    """Save equipment (POST)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Get related objects
            district = None
            if data.get("district_id"):
                try:
                    district = cocoaDistrict.objects.get(id=data["district_id"])
                except cocoaDistrict.DoesNotExist:
                    pass
            
            project = None
            if data.get("project_id"):
                try:
                    project = projectTbl.objects.get(id=data["project_id"])
                except projectTbl.DoesNotExist:
                    pass
            
            staff = None
            if data.get("staff_id"):
                try:
                    staff = staffTbl.objects.get(id=data["staff_id"])
                except staffTbl.DoesNotExist:
                    pass
            
            # Create equipment
            equipment = EquipmentModel.objects.create(
                equipment=data.get("equipment"),
                status=data.get("status", "Good"),
                serial_number=data.get("serial_number"),
                manufacturer=data.get("manufacturer"),
                staff_name=staff,
                projectTbl_foreignkey=project,
                district=district,
                uid=str(uuid.uuid4())
            )
            
            return JsonResponse({
                "status": True,
                "message": "Equipment saved successfully",
                "data": {
                    "equipment_code": equipment.equipment_code,
                    "date_of_capturing": equipment.date_of_capturing.strftime("%Y-%m-%d %H:%M:%S"),
                    "equipment": equipment.equipment,
                    "status": equipment.status,
                    "serial_number": equipment.serial_number,
                    "manufacturer": equipment.manufacturer,
                    "staff_name": f"{staff.first_name} {staff.last_name}" if staff else None
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class FetchAllEquipmentView(View):
    """Fetch all equipment (GET)"""
    def get(self, request):
        try:
            project_id = request.GET.get('project_id')
            district_id = request.GET.get('district_id')
            status = request.GET.get('status')
            page = request.GET.get('page', 1)
            page_size = request.GET.get('page_size', 20)
            
            # Base query
            query = EquipmentModel.objects.select_related(
                'staff_name', 'projectTbl_foreignkey', 'district'
            ).all().order_by('-date_of_capturing')
            
            # Apply filters
            if project_id:
                query = query.filter(projectTbl_foreignkey_id=project_id)
            if district_id:
                query = query.filter(district_id=district_id)
            if status:
                query = query.filter(status=status)
            
            # Pagination
            paginator = Paginator(query, page_size)
            page_obj = paginator.get_page(page)
            
            data = []
            for equip in page_obj:
                data.append({
                    "equipment_code": equip.equipment_code,
                    "date_of_capturing": equip.date_of_capturing.strftime("%Y-%m-%d %H:%M:%S"),
                    "equipment": equip.equipment,
                    "status": equip.status,
                    "serial_number": equip.serial_number,
                    "manufacturer": equip.manufacturer,
                    "pic_serial_number": request.build_absolute_uri(equip.pic_serial_number.url) if equip.pic_serial_number else None,
                    "pic_equipment": request.build_absolute_uri(equip.pic_equipment.url) if equip.pic_equipment else None,
                    "staff_name": f"{equip.staff_name.first_name} {equip.staff_name.last_name}" if equip.staff_name else None,
                    "staff_id": equip.staff_name.id if equip.staff_name else None,
                    "district_id": equip.district.id if equip.district else None,
                    "district_name": equip.district.name if equip.district else None,
                    "project_id": equip.projectTbl_foreignkey.id if equip.projectTbl_foreignkey else None,
                    "project_name": equip.projectTbl_foreignkey.name if equip.projectTbl_foreignkey else None
                })
            
            return JsonResponse({
                "status": True,
                "message": "Equipment fetched successfully",
                "data": data,
                "pagination": {
                    "current_page": page_obj.number,
                    "total_pages": paginator.num_pages,
                    "total_records": paginator.count,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)


# ============== 3. OUTBREAK FARM APIs ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveOutbreakFarmView(View):
    """Save outbreak farm (POST)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Get related objects
            district = None
            if data.get("district_id"):
                try:
                    district = cocoaDistrict.objects.get(id=data["district_id"])
                except cocoaDistrict.DoesNotExist:
                    pass
            
            region = None
            if data.get("region_id"):
                try:
                    region = Region.objects.get(id=data["region_id"])
                except Region.DoesNotExist:
                    pass
            elif district:
                region = district.region
            
            project = None
            if data.get("project_id"):
                try:
                    project = projectTbl.objects.get(id=data["project_id"])
                except projectTbl.DoesNotExist:
                    pass
            
            reported_by = None
            if data.get("reported_by_id"):
                try:
                    reported_by = staffTbl.objects.get(id=data["reported_by_id"])
                except staffTbl.DoesNotExist:
                    pass
            
            community = None
            if data.get("community_id"):
                try:
                    community = Community.objects.get(id=data["community_id"])
                except Community.DoesNotExist:
                    pass
            
            farm = None
            if data.get("farm_id"):
                try:
                    farm = FarmdetailsTbl.objects.get(id=data["farm_id"])
                except FarmdetailsTbl.DoesNotExist:
                    pass
            
            # Create outbreak farm
            outbreak = OutbreakFarm.objects.create(
                farm=farm,
                farm_location=data.get("farm_location"),
                farmer_name=data.get("farmer_name"),
                farmer_age=data.get("farmer_age"),
                id_type=data.get("id_type"),
                id_number=data.get("id_number"),
                farmer_contact=data.get("farmer_contact"),
                cocoa_type=data.get("cocoa_type"),
                age_class=data.get("age_class"),
                farm_area=data.get("farm_area", 0.0),
                communitytbl=data.get("communitytbl"),
                community=community,
                inspection_date=data.get("inspection_date"),
                temp_code=data.get("temp_code"),
                disease_type=data.get("disease_type"),
                date_reported=data.get("date_reported", timezone.now().date()),
                reported_by=reported_by,
                status=data.get("status", 0),
                coordinates=data.get("coordinates"),
                severity=data.get("severity", "Medium"),
                treatment_applied=data.get("treatment_applied"),
                treatment_date=data.get("treatment_date"),
                projectTbl_foreignkey=project,
                district=district,
                region=region,
                uid=str(uuid.uuid4())
            )
            
            return JsonResponse({
                "status": True,
                "message": "Outbreak farm saved successfully",
                "data": {
                    "farm_id": outbreak.farm.id if outbreak.farm else None,
                    "outbreaks_id": outbreak.outbreak_id,
                    "farm_location": outbreak.farm_location,
                    "farmer_name": outbreak.farmer_name,
                    "farmer_age": outbreak.farmer_age,
                    "id_type": outbreak.id_type,
                    "id_number": outbreak.id_number,
                    "farmer_contact": outbreak.farmer_contact,
                    "cocoa_type": outbreak.cocoa_type,
                    "age_class": outbreak.age_class,
                    "farm_area": outbreak.farm_area,
                    "communitytbl": outbreak.communitytbl,
                    "inspection_date": outbreak.inspection_date.strftime("%Y-%m-%d") if outbreak.inspection_date else None,
                    "temp_code": outbreak.temp_code,
                    "disease_type": outbreak.disease_type,
                    "severity": outbreak.severity,
                    "status": outbreak.status
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class FetchOutbreakFarmsListView(View):
    """Fetch outbreak farms list (GET)"""
    def get(self, request):
        try:
            project_id = request.GET.get('project_id')
            district_id = request.GET.get('district_id')
            status = request.GET.get('status')
            severity = request.GET.get('severity')
            page = request.GET.get('page', 1)
            page_size = request.GET.get('page_size', 20)
            
            # Base query
            query = OutbreakFarm.objects.select_related(
                'farm', 'reported_by', 'projectTbl_foreignkey', 'district', 'region', 'community'
            ).all().order_by('-date_reported')
            
            # Apply filters
            if project_id:
                query = query.filter(projectTbl_foreignkey_id=project_id)
            if district_id:
                query = query.filter(district_id=district_id)
            if status is not None:
                query = query.filter(status=status)
            if severity:
                query = query.filter(severity=severity)
            
            # Pagination
            paginator = Paginator(query, page_size)
            page_obj = paginator.get_page(page)
            
            data = []
            for outbreak in page_obj:
                data.append({
                    "farm_id": outbreak.farm.id if outbreak.farm else None,
                    "farm_reference": outbreak.farm.farm_reference if outbreak.farm else None,
                    "outbreaks_id": outbreak.outbreak_id,
                    "farm_location": outbreak.farm_location,
                    "farmer_name": outbreak.farmer_name,
                    "farmer_age": outbreak.farmer_age,
                    "id_type": outbreak.id_type,
                    "id_number": outbreak.id_number,
                    "farmer_contact": outbreak.farmer_contact,
                    "cocoa_type": outbreak.cocoa_type,
                    "age_class": outbreak.age_class,
                    "farm_area": outbreak.farm_area,
                    "communitytbl": outbreak.communitytbl,
                    "community_id": outbreak.community.id if outbreak.community else None,
                    "community_name": outbreak.community.name if outbreak.community else None,
                    "inspection_date": outbreak.inspection_date.strftime("%Y-%m-%d") if outbreak.inspection_date else None,
                    "temp_code": outbreak.temp_code,
                    "disease_type": outbreak.disease_type,
                    "severity": outbreak.severity,
                    "date_reported": outbreak.date_reported.strftime("%Y-%m-%d") if outbreak.date_reported else None,
                    "reported_by": f"{outbreak.reported_by.first_name} {outbreak.reported_by.last_name}" if outbreak.reported_by else None,
                    "status": outbreak.status,
                    "status_display": dict(OutbreakFarm._meta.get_field('status').choices).get(outbreak.status, 'Unknown'),
                    "coordinates": outbreak.coordinates,
                    "treatment_applied": outbreak.treatment_applied,
                    "treatment_date": outbreak.treatment_date.strftime("%Y-%m-%d") if outbreak.treatment_date else None,
                    "district_id": outbreak.district.id if outbreak.district else None,
                    "district_name": outbreak.district.name if outbreak.district else None,
                    "region_id": outbreak.region.id if outbreak.region else None,
                    "region_name": outbreak.region.region if outbreak.region else None,
                    "project_id": outbreak.projectTbl_foreignkey.id if outbreak.projectTbl_foreignkey else None,
                    "project_name": outbreak.projectTbl_foreignkey.name if outbreak.projectTbl_foreignkey else None
                })
            
            return JsonResponse({
                "status": True,
                "message": "Outbreak farms fetched successfully",
                "data": data,
                "pagination": {
                    "current_page": page_obj.number,
                    "total_pages": paginator.num_pages,
                    "total_records": paginator.count,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": []
            }, status=500)


# ============== 4. SINGLE RECORD FETCH APIs ==============

@method_decorator(csrf_exempt, name='dispatch')
class FetchOutbreakFarmDetailView(View):
    """Fetch single outbreak farm details (GET)"""
    def get(self, request, outbreak_id):
        try:
            outbreak = OutbreakFarm.objects.select_related(
                'farm', 'reported_by', 'projectTbl_foreignkey', 'district', 'region', 'community'
            ).get(outbreak_id=outbreak_id)
            
            return JsonResponse({
                "status": True,
                "message": "Outbreak farm details fetched successfully",
                "data": {
                    "farm_id": outbreak.farm.id if outbreak.farm else None,
                    "farm_reference": outbreak.farm.farm_reference if outbreak.farm else None,
                    "outbreaks_id": outbreak.outbreak_id,
                    "farm_location": outbreak.farm_location,
                    "farmer_name": outbreak.farmer_name,
                    "farmer_age": outbreak.farmer_age,
                    "id_type": outbreak.id_type,
                    "id_number": outbreak.id_number,
                    "farmer_contact": outbreak.farmer_contact,
                    "cocoa_type": outbreak.cocoa_type,
                    "age_class": outbreak.age_class,
                    "farm_area": outbreak.farm_area,
                    "communitytbl": outbreak.communitytbl,
                    "community_id": outbreak.community.id if outbreak.community else None,
                    "community_name": outbreak.community.name if outbreak.community else None,
                    "inspection_date": outbreak.inspection_date.strftime("%Y-%m-%d") if outbreak.inspection_date else None,
                    "temp_code": outbreak.temp_code,
                    "disease_type": outbreak.disease_type,
                    "severity": outbreak.severity,
                    "date_reported": outbreak.date_reported.strftime("%Y-%m-%d") if outbreak.date_reported else None,
                    "reported_by_id": outbreak.reported_by.id if outbreak.reported_by else None,
                    "reported_by": f"{outbreak.reported_by.first_name} {outbreak.reported_by.last_name}" if outbreak.reported_by else None,
                    "status": outbreak.status,
                    "coordinates": outbreak.coordinates,
                    "treatment_applied": outbreak.treatment_applied,
                    "treatment_date": outbreak.treatment_date.strftime("%Y-%m-%d") if outbreak.treatment_date else None,
                    "district_id": outbreak.district.id if outbreak.district else None,
                    "district_name": outbreak.district.name if outbreak.district else None,
                    "region_id": outbreak.region.id if outbreak.region else None,
                    "region_name": outbreak.region.region if outbreak.region else None,
                    "project_id": outbreak.projectTbl_foreignkey.id if outbreak.projectTbl_foreignkey else None,
                    "project_name": outbreak.projectTbl_foreignkey.name if outbreak.projectTbl_foreignkey else None
                }
            })
            
        except OutbreakFarm.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Outbreak farm not found",
                "data": {}
            }, status=404)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class FetchEquipmentDetailView(View):
    """Fetch single equipment details (GET)"""
    def get(self, request, equipment_code):
        try:
            equip = EquipmentModel.objects.select_related(
                'staff_name', 'projectTbl_foreignkey', 'district'
            ).get(equipment_code=equipment_code)
            
            return JsonResponse({
                "status": True,
                "message": "Equipment details fetched successfully",
                "data": {
                    "equipment_code": equip.equipment_code,
                    "date_of_capturing": equip.date_of_capturing.strftime("%Y-%m-%d %H:%M:%S"),
                    "equipment": equip.equipment,
                    "status": equip.status,
                    "serial_number": equip.serial_number,
                    "manufacturer": equip.manufacturer,
                    "pic_serial_number": request.build_absolute_uri(equip.pic_serial_number.url) if equip.pic_serial_number else None,
                    "pic_equipment": request.build_absolute_uri(equip.pic_equipment.url) if equip.pic_equipment else None,
                    "staff_id": equip.staff_name.id if equip.staff_name else None,
                    "staff_name": f"{equip.staff_name.first_name} {equip.staff_name.last_name}" if equip.staff_name else None,
                    "district_id": equip.district.id if equip.district else None,
                    "district_name": equip.district.name if equip.district else None,
                    "project_id": equip.projectTbl_foreignkey.id if equip.projectTbl_foreignkey else None,
                    "project_name": equip.projectTbl_foreignkey.name if equip.projectTbl_foreignkey else None
                }
            })
            
        except EquipmentModel.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Equipment not found",
                "data": {}
            }, status=404)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)





# ============== 19. FARM VALIDATION ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveFarmValidationView(View):
    """Handle farm validation (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            field_uri = data.get("field_uri", "")
            
            # Check if already exists
            if field_uri and FarmValidation.objects.filter(field_uri=field_uri).exists():
                status["message"] = "Farm validation record already exists"
                status["data"] = {"field_uri": field_uri}
                return JsonResponse(status)
            
            # Get farm
            farm = None
            farm_id = data.get("farm_id", "")
            if farm_id:
                try:
                    farm = FarmdetailsTbl.objects.get(farm_reference=farm_id)
                except:
                    pass
            
            # Create farm validation record
            validation = FarmValidation.objects.create(
                field_uri=field_uri,
                field_submission_date=data.get("field_submission_date"),
                reporting_date=data.get("reporting_date"),
                staff_id=data.get("staff_id", ""),
                staff_name=data.get("staff_name", ""),
                sector_no=data.get("sector_no"),
                region=data.get("region", ""),
                farm=farm,
                farm_size=data.get("farm_size", 0.0),
                farmer_contact=data.get("farmer_contact", ""),
                farm_verified_by_ched=data.get("farm_verified_by_ched", ""),
                demarcated_to_boundary=data.get("demarcated_to_boundary", ""),
                treated_to_boundary=data.get("treated_to_boundary", ""),
                undesirable_shade_tree=data.get("undesirable_shade_tree", ""),
                farmer_name=data.get("farmer_name", ""),
                maintained_to_boundary=data.get("maintained_to_boundary", ""),
                point_lng=data.get("point_lng", ""),
                point_lat=data.get("point_lat", ""),
                point_acc=data.get("point_acc", ""),
                farms_in_mushy_field=data.get("farms_in_mushy_field", ""),
                rice_maize_cassava_farm=data.get("rice_maize_cassava_farm", ""),
                location=data.get("location", ""),
                established_to_boundary=data.get("established_to_boundary", ""),
                general_remarks=data.get("general_remarks", "")
            )
            
            status["status"] = True
            status["message"] = "Farm validation record saved successfully"
            status["data"] = {
                "field_uri": validation.field_uri,
                "id": validation.field_uri
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status)

# ============== 20. FEEDBACK ==============

@method_decorator(csrf_exempt, name='dispatch')
class SaveFeedbackAPIView(View):
    """Handle feedback submission (POST only) - API version"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID already exists
            if uid and Feedback.objects.filter(uid=uid).exists():
                status["message"] = "Feedback with this UID already exists"
                status["data"] = {"uid": uid}
                return JsonResponse(status)
            
            # Get staff
            staff = None
            staff_id = data.get("staff_id", "")
            if staff_id:
                try:
                    staff = staffTbl.objects.get(id=staff_id)
                except:
                    pass
            
            # Create feedback
            feedback = Feedback.objects.create(
                staffTbl_foreignkey=staff,
                title=data.get("title", ""),
                feedback=data.get("feedback", ""),
                uid=uid,
                farm_reference=data.get("farm_reference", ""),
                activity=data.get("activity", ""),
                ra_id=data.get("ra_id", ""),
                Status=data.get("status", "Open")
            )
            
            status["status"] = True
            status["message"] = "Feedback submitted successfully"
            status["data"] = {
                "uid": feedback.uid,
                "id": feedback.id
            }
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data",
                "data": {}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Error occurred: {str(e)}",
                "data": {}
            }, status=500)
            
        return JsonResponse(status)



####################################################################################################################################################

import json
import traceback
from django.utils import timezone
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

# ==================== POS ROUTE MONITORING APIs ====================

@method_decorator(csrf_exempt, name='dispatch')
class PosRouteMonitoringView(View):
    """Handle POST and GET for PosRouteMonitoring model"""
    
    def post(self, request):
        """Create new POS route monitoring record"""
        try:
            data = json.loads(request.body)
            status_response = {"status": False, "message": "", "data": {}}
            
            # Check if record with same UID exists (optional)
            uid = data.get("uid", "")
            if uid and posRoutemonitoring.objects.filter(uid=uid).exists():
                status_response["message"] = "Record with this UID already exists"
                status_response["data"] = {"uid": uid}
                return JsonResponse(status_response)
            
            # Get staff
            staff = None
            staff_id = data.get("staff_id", "")
            if staff_id:
                try:
                    staff = PersonnelModel.objects.get(id=staff_id)
                except PersonnelModel.DoesNotExist:
                    pass
            
            # Parse date if provided
            inspection_date = None
            if data.get("inspection_date"):
                try:
                    inspection_date = timezone.datetime.fromisoformat(data.get("inspection_date").replace('Z', '+00:00'))
                except:
                    inspection_date = timezone.now()
            
            # Create record
            record = posRoutemonitoring.objects.create(
                staffTbl_foreignkey=staff,
                lat=data.get("lat"),
                lng=data.get("lng"),
                accuracy=data.get("accuracy"),
                inspection_date=inspection_date or timezone.now(),
                uid=uid,
            )
            
            status_response["status"] = True
            status_response["message"] = "POS route monitoring record created successfully"
            status_response["data"] = {
                "id": record.id,
                "uid": record.uid,
                "lat": record.lat,
                "lng": record.lng,
                "accuracy": record.accuracy,
                "inspection_date": record.inspection_date.isoformat() if record.inspection_date else None,
                "staff_id": staff_id
            }
            
        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON data"}, status=400)
        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({"status": False, "message": f"Error: {str(e)}"}, status=500)
        
        return JsonResponse(status_response)
    
    def get(self, request):
        """Get POS route monitoring records with filters"""
        try:
            # Query parameters for filtering
            uid = request.GET.get('uid', '')
            staff_id = request.GET.get('staff_id', '')
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            limit = int(request.GET.get('limit', 100))
            page = int(request.GET.get('page', 1))
            
            # Build query
            queryset = posRoutemonitoring.objects.all().order_by('-inspection_date')
            
            if uid:
                queryset = queryset.filter(uid=uid)
            
            if staff_id:
                queryset = queryset.filter(staffTbl_foreignkey_id=staff_id)
            
            if start_date:
                queryset = queryset.filter(inspection_date__gte=start_date)
            
            if end_date:
                queryset = queryset.filter(inspection_date__lte=end_date)
            
            # Pagination
            paginator = Paginator(queryset, limit)
            try:
                records = paginator.page(page)
            except PageNotAnInteger:
                records = paginator.page(1)
            except EmptyPage:
                records = paginator.page(paginator.num_pages)
            
            # Prepare response data
            data_list = []
            for record in records:
                data_list.append({
                    "id": record.id,
                    "uid": record.uid,
                    "lat": record.lat,
                    "lng": record.lng,
                    "accuracy": record.accuracy,
                    "inspection_date": record.inspection_date.isoformat() if record.inspection_date else None,
                    "staff_id": record.staffTbl_foreignkey_id,
                    "staff_name": str(record.staffTbl_foreignkey) if record.staffTbl_foreignkey else None,
                    "created_at": record.timeStamp.isoformat() if hasattr(record, 'timeStamp') and record.timeStamp else None
                })
            
            response = {
                "status": True,
                "message": "Records fetched successfully",
                "data": data_list,
                "pagination": {
                    "total": paginator.count,
                    "page": records.number,
                    "limit": limit,
                    "pages": paginator.num_pages
                }
            }
            
        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({"status": False, "message": f"Error: {str(e)}"}, status=500)
        
        return JsonResponse(response)


# ==================== VERIFY RECORD APIs ====================

@method_decorator(csrf_exempt, name='dispatch')
class VerifyRecordView(View):
    """Handle POST and GET for VerifyRecord model"""
    
    def post(self, request):
        """Create new verification record"""
        try:
            # Handle both JSON and multipart form data for file uploads
            if request.content_type and 'multipart/form-data' in request.content_type:
                data = request.POST
                video_file = request.FILES.get('videoPath', None)
            else:
                data = json.loads(request.body)
                video_file = None
            
            status_response = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID exists
            if uid and VerifyRecord.objects.filter(uid=uid).exists():
                status_response["message"] = "Record with this UID already exists"
                status_response["data"] = {"uid": uid}
                return JsonResponse(status_response)
            
            # Get farm
            farm = None
            farm_id = data.get("farm_id", "")
            if farm_id:
                try:
                    farm = FarmdetailsTbl.objects.get(id=farm_id)
                except FarmdetailsTbl.DoesNotExist:
                    pass
            
            # Get project
            project = None
            project_id = data.get("project_id", "")
            if project_id:
                try:
                    project = projectTbl.objects.get(id=project_id)
                except projectTbl.DoesNotExist:
                    pass
            
            # Get district
            district = None
            district_id = data.get("district_id", "")
            if district_id:
                try:
                    district = cocoaDistrict.objects.get(id=district_id)
                except cocoaDistrict.DoesNotExist:
                    pass
            
            # Parse timestamp
            timestamp = None
            if data.get("timestamp"):
                try:
                    timestamp = timezone.datetime.fromisoformat(data.get("timestamp").replace('Z', '+00:00'))
                except:
                    timestamp = timezone.now()
            else:
                timestamp = timezone.now()
            
            # Create record
            record = VerifyRecord(
                uid=uid,
                farm=farm,
                farmRef=data.get("farmRef", ""),
                timestamp=timestamp,
                status=int(data.get("status", 0)),
                projectTbl_foreignkey=project,
                district=district
            )
            
            # Handle video file
            if video_file:
                record.videoPath = video_file
            elif data.get("videoPath"):
                # If video path is provided as string (URL/path)
                record.videoPath = data.get("videoPath")
            
            record.save()
            
            status_response["status"] = True
            status_response["message"] = "Verification record created successfully"
            status_response["data"] = {
                "id": record.id,
                "uid": record.uid,
                "farmRef": record.farmRef,
                "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                "status": record.status,
                "videoPath": record.videoPath.url if record.videoPath and hasattr(record.videoPath, 'url') else str(record.videoPath),
                "farm_id": farm_id,
                "project_id": project_id,
                "district_id": district_id
            }
            
        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON data"}, status=400)
        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({"status": False, "message": f"Error: {str(e)}"}, status=500)
        
        return JsonResponse(status_response)
    
    def get(self, request):
        """Get verification records with filters"""
        try:
            # Query parameters
            uid = request.GET.get('uid', '')
            farm_id = request.GET.get('farm_id', '')
            farmRef = request.GET.get('farmRef', '')
            project_id = request.GET.get('project_id', '')
            district_id = request.GET.get('district_id', '')
            status = request.GET.get('status', '')
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            limit = int(request.GET.get('limit', 100))
            page = int(request.GET.get('page', 1))
            
            # Build query
            queryset = VerifyRecord.objects.all().order_by('-timestamp')
            
            if uid:
                queryset = queryset.filter(uid=uid)
            
            if farm_id:
                queryset = queryset.filter(farm_id=farm_id)
            
            if farmRef:
                queryset = queryset.filter(farmRef__icontains=farmRef)
            
            if project_id:
                queryset = queryset.filter(projectTbl_foreignkey_id=project_id)
            
            if district_id:
                queryset = queryset.filter(district_id=district_id)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if start_date:
                queryset = queryset.filter(timestamp__gte=start_date)
            
            if end_date:
                queryset = queryset.filter(timestamp__lte=end_date)
            
            # Pagination
            paginator = Paginator(queryset, limit)
            try:
                records = paginator.page(page)
            except PageNotAnInteger:
                records = paginator.page(1)
            except EmptyPage:
                records = paginator.page(paginator.num_pages)
            
            # Prepare response
            data_list = []
            for record in records:
                data_list.append({
                    "id": record.id,
                    "uid": record.uid,
                    "farmRef": record.farmRef,
                    "farm_id": record.farm_id,
                    "farm_name": str(record.farm) if record.farm else None,
                    "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                    "status": record.status,
                    "status_display": "Synced" if record.status == 1 else "Pending",
                    "videoPath": record.videoPath.url if record.videoPath and hasattr(record.videoPath, 'url') else str(record.videoPath),
                    "project_id": record.projectTbl_foreignkey_id,
                    "project_name": str(record.projectTbl_foreignkey) if record.projectTbl_foreignkey else None,
                    "district_id": record.district_id,
                    "district_name": str(record.district) if record.district else None,
                    "created_at": record.timeStamp.isoformat() if hasattr(record, 'timeStamp') and record.timeStamp else None
                })
            
            response = {
                "status": True,
                "message": "Records fetched successfully",
                "data": data_list,
                "pagination": {
                    "total": paginator.count,
                    "page": records.number,
                    "limit": limit,
                    "pages": paginator.num_pages
                }
            }
            
        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({"status": False, "message": f"Error: {str(e)}"}, status=500)
        
        return JsonResponse(response)


# ==================== UPDATED FEEDBACK API ====================

@method_decorator(csrf_exempt, name='dispatch')
class FeedbackView(View):
    """Handle POST and GET for Feedback model"""
    
    def post(self, request):
        """Create new feedback with all fields"""
        try:
            data = json.loads(request.body)
            status_response = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID exists (optional - remove if you want duplicates)
            if uid and Feedback.objects.filter(uid=uid).exists():
                status_response["message"] = "Feedback with this UID already exists"
                status_response["data"] = {"uid": uid}
                return JsonResponse(status_response)
            
            # Get staff user
            staff = None
            staff_id = data.get("staff_id", "") or data.get("user_id", "")
            if staff_id:
                try:
                    staff = staffTbl.objects.get(id=staff_id)
                except staffTbl.DoesNotExist:
                    pass
            
            # Get current date for week/month/year if not provided
            now = timezone.now()
            
            # Create feedback with all fields
            feedback = Feedback.objects.create(
                staffTbl_foreignkey=staff,
                title=data.get("title", ""),
                feedback=data.get("feedback", "") or data.get("description", ""),
                uid=uid,
                farm_reference=data.get("farm_reference", ""),
                activity=data.get("activity", ""),
                ra_id=data.get("ra_id", ""),
                Status=data.get("status", "Open") or data.get("Status", "Open"),
                week=data.get("week", str(now.isocalendar()[1])),  # ISO week number
                month=data.get("month", now.strftime("%B")),  # Month name
                year=data.get("year", str(now.year)),
            )
            
            status_response["status"] = True
            status_response["message"] = "Feedback submitted successfully"
            status_response["data"] = {
                "id": feedback.id,
                "uid": feedback.uid,
                "title": feedback.title,
                "feedback": feedback.feedback,
                "status": feedback.Status,
                "farm_reference": feedback.farm_reference,
                "activity": feedback.activity,
                "ra_id": feedback.ra_id,
                "week": feedback.week,
                "month": feedback.month,
                "year": feedback.year,
                "staff_id": staff_id,
                "created_at": feedback.sent_date.isoformat() if feedback.sent_date else None
            }
            
        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON data"}, status=400)
        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({"status": False, "message": f"Error: {str(e)}"}, status=500)
        
        return JsonResponse(status_response)
    
    def get(self, request):
        """Get feedback records with filters"""
        try:
            # Query parameters
            uid = request.GET.get('uid', '')
            staff_id = request.GET.get('staff_id', '')
            ra_id = request.GET.get('ra_id', '')
            farm_reference = request.GET.get('farm_reference', '')
            status = request.GET.get('status', '')
            week = request.GET.get('week', '')
            month = request.GET.get('month', '')
            year = request.GET.get('year', '')
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            limit = int(request.GET.get('limit', 100))
            page = int(request.GET.get('page', 1))
            
            # Build query
            queryset = Feedback.objects.all().order_by('-sent_date')
            
            if uid:
                queryset = queryset.filter(uid=uid)
            
            if staff_id:
                queryset = queryset.filter(staffTbl_foreignkey_id=staff_id)
            
            if ra_id:
                queryset = queryset.filter(ra_id__icontains=ra_id)
            
            if farm_reference:
                queryset = queryset.filter(farm_reference__icontains=farm_reference)
            
            if status:
                queryset = queryset.filter(Status__iexact=status)
            
            if week:
                queryset = queryset.filter(week=week)
            
            if month:
                queryset = queryset.filter(month__iexact=month)
            
            if year:
                queryset = queryset.filter(year=year)
            
            if start_date:
                queryset = queryset.filter(sent_date__gte=start_date)
            
            if end_date:
                queryset = queryset.filter(sent_date__lte=end_date)
            
            # Pagination
            paginator = Paginator(queryset, limit)
            try:
                feedbacks = paginator.page(page)
            except PageNotAnInteger:
                feedbacks = paginator.page(1)
            except EmptyPage:
                feedbacks = paginator.page(paginator.num_pages)
            
            # Prepare response
            data_list = []
            for fb in feedbacks:
                data_list.append({
                    "id": fb.id,
                    "uid": fb.uid,
                    "title": fb.title,
                    "feedback": fb.feedback,
                    "staff_id": fb.staffTbl_foreignkey_id,
                    "staff_name": str(fb.staffTbl_foreignkey) if fb.staffTbl_foreignkey else None,
                    "farm_reference": fb.farm_reference,
                    "activity": fb.activity,
                    "ra_id": fb.ra_id,
                    "status": fb.Status,
                    "week": fb.week,
                    "month": fb.month,
                    "year": fb.year,
                    "sent_date": fb.sent_date.isoformat() if fb.sent_date else None,
                    "created_at": fb.timeStamp.isoformat() if hasattr(fb, 'timeStamp') and fb.timeStamp else None
                })
            
            response = {
                "status": True,
                "message": "Feedbacks fetched successfully",
                "data": data_list,
                "pagination": {
                    "total": paginator.count,
                    "page": feedbacks.number,
                    "limit": limit,
                    "pages": paginator.num_pages,
                    "has_next": feedbacks.has_next(),
                    "has_previous": feedbacks.has_previous()
                }
            }
            
        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({"status": False, "message": f"Error: {str(e)}"}, status=500)
        
        return JsonResponse(response)


# ==================== URLS CONFIGURATION ====================
