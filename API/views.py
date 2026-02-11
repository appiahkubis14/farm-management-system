# views.py
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
                    main_activity_obj = Activities.objects.get(activity_code=main_activity_code)
                except:
                    pass
            
            if activity_code:
                try:
                    activity_obj = Activities.objects.get(activity_code=activity_code)
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
            
            if main_activity_code:
                try:
                    main_activity_obj = Activities.objects.get(activity_code=main_activity_code)
                except:
                    pass
            
            if activity_code:
                try:
                    activity_obj = Activities.objects.get(activity_code=activity_code)
                except:
                    pass
            
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
                account_number=data.get("account_number", ""),
                branch_id=data.get("branch_id", ""),
                sort_code=data.get("sort_code", ""),
                personnel_type=data.get("personnel_type", ""),
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

@method_decorator(csrf_exempt, name='dispatch')
class GrowthMonitoringView(View):
    """Handle growth monitoring (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID already exists
            if uid and GrowthMonitoringModel.objects.filter(uid=uid).exists():
                status["message"] = "Growth monitoring record with this UID already exists"
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
            
            # Get district (from agent's project)
            district = None
            project = None
            if agent and agent.projectTbl_foreignkey:
                project = agent.projectTbl_foreignkey
                if project.district:
                    district = project.district
            
            # Create growth monitoring record
            record = GrowthMonitoringModel.objects.create(
                uid=uid,
                plant_uid=data.get("plant_uid", ""),
                number_of_leaves=data.get("number_of_leaves", 0),
                height=data.get("height", 0.0),
                stem_size=data.get("stem_size", 0.0),
                leaf_color=data.get("leaf_color", ""),
                date=data.get("date"),
                lat=data.get("lat", 0.0),
                lng=data.get("lng", 0.0),
                agent=agent,
                projectTbl_foreignkey=project,
                district=district
            )
            
            status["status"] = True
            status["message"] = "Growth monitoring record saved successfully"
            status["data"] = {
                "uid": record.uid,
                "id": record.id
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

@method_decorator(csrf_exempt, name='dispatch')
class SaveFeedbackView(View):
    """Handle issue/feedback submission (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            uid = data.get("uid", "")
            
            # Check if UID already exists
            if uid and IssueModel.objects.filter(uid=uid).exists():
                status["message"] = "Issue with this UID already exists"
                status["data"] = {"uid": uid}
                return JsonResponse(status)
            
            # Get user
            user = None
            user_id = data.get("user_id", "")
            if user_id:
                try:
                    user = staffTbl.objects.get(id=user_id)
                except:
                    pass
            
            # Get district and project from user
            district = None
            project = None
            
            if user and user.projectTbl_foreignkey:
                project = user.projectTbl_foreignkey
                if project.district:
                    district = project.district
            
            # Create issue
            issue = IssueModel.objects.create(
                uid=uid,
                user=user,
                issue_type=data.get("issue_type", ""),
                description=data.get("description", ""),
                date_reported=data.get("date_reported"),
                status=data.get("status", 0),
                projectTbl_foreignkey=project,
                district=district
            )
            
            status["status"] = True
            status["message"] = "Issue/feedback submitted successfully"
            status["data"] = {
                "uid": issue.uid,
                "id": issue.id
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
                    "region_name": farm.region.name if farm.region else None,
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
                    "region_name": job.region.name if job.region else None,
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
                            "snnit_no": "",  # Would need additional field
                            "salary": "",  # Would need salary calculation logic
                            "year": year,
                            "po_number": staff.staffid if staff.staffid else "",
                            "month": month,
                            "week": week,
                            "payment_option": "Bank" if person.bank_id else "Momo" if person.momo_number else "Unknown",
                            "momo_acc": person.momo_number or ""
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

@method_decorator(csrf_exempt, name='dispatch')
class SaveCalculatedAreaView(View):
    """Handle area calculation (POST only)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            status = {"status": False, "message": "", "data": {}}
            
            # Get district if provided in context
            district = None
            district_id = data.get("district_id", "")
            if district_id:
                try:
                    district = cocoaDistrict.objects.get(id=district_id)
                except:
                    pass
            
            # Get project from district
            project = None
            if district:
                try:
                    project = projectTbl.objects.get(district=district)
                except:
                    pass
            
            # Create calculated area
            area = CalculatedArea.objects.create(
                date=data.get("date"),
                title=data.get("title", ""),
                value=data.get("value", 0.0),
                projectTbl_foreignkey=project,
                district=district
            )
            
            status["status"] = True
            status["message"] = "Area calculation saved successfully"
            status["data"] = {
                "id": area.id,
                "title": area.title,
                "value": area.value
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