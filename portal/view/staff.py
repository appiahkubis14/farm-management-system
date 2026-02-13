import json
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, datetime

from portal.models import (
    PersonnelModel, cocoaDistrict, Community, 
    projectTbl, Region  # Remove staffTbl from here - it's not needed for PersonnelModel
)

@login_required
def staff_overview(request):
    """Render the Staff Overview page"""
    context = {
        'status_choices': [
            ('Active', 'Active'),
            ('Inactive', 'Inactive'),
            ('On Leave', 'On Leave'),
            ('Terminated', 'Terminated'),
            ('Suspended', 'Suspended')
        ],
        'personnel_types': [
            ('Rehab Assistant', 'Rehab Assistant'),
            ('Rehab Technician', 'Rehab Technician'),
            ('Project Officer', 'Project Officer'),
            ('Project Coordinator', 'Project Coordinator'),
            ('Regional Manager', 'Regional Manager'),
            ('Admin', 'Admin')
        ],
        'genders': [
            ('Male', 'Male'),
            ('Female', 'Female')
        ],
        'education_levels': [
            ('No Formal Education', 'No Formal Education'),
            ('Primary', 'Primary'),
            ('JHS', 'JHS'),
            ('SHS', 'SHS'),
            ('Tertiary', 'Tertiary'),
            ('Post Graduate', 'Post Graduate')
        ],
        'marital_statuses': [
            ('Single', 'Single'),
            ('Married', 'Married'),
            ('Divorced', 'Divorced'),
            ('Widowed', 'Widowed')
        ],
        'id_types': [
            ('National ID', 'National ID'),
            ('Voters ID', 'Voters ID'),
            ('Drivers License', 'Drivers License'),
            ('Passport', 'Passport'),
            ('NHIS', 'NHIS')
        ],
        'banks': [
            ('GCB', 'GCB'),
            ('ADB', 'ADB'),
            ('Cal Bank', 'Cal Bank'),
            ('Stanbic', 'Stanbic'),
            ('Ecobank', 'Ecobank'),
            ('Fidelity', 'Fidelity'),
            ('Access Bank', 'Access Bank'),
            ('Zenith', 'Zenith'),
            ('UBA', 'UBA')
        ]
    }
    return render(request, 'portal/personnel/staff_overview.html', context)

@require_http_methods(["GET"])
def get_staff_list_api(request):
    print("=== get_staff_list_api called ===")
    """Get paginated staff list for DataTable"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Base queryset
        queryset = PersonnelModel.objects.all()
        print(f"SQL Query: {queryset.query}")
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(first_name__icontains=search_value) |
                Q(surname__icontains=search_value) |
                Q(staff_id__icontains=search_value) |
                Q(primary_phone_number__icontains=search_value) |
                Q(personnel_type__icontains=search_value)
            )
        
        # Get total counts
        total_records = PersonnelModel.objects.filter(delete_field='no').count()
        filtered_records = queryset.count()
        
        # Apply pagination
        page = (start // length) + 1
        paginator = Paginator(queryset.order_by('-created_date'), length)
        page_obj = paginator.get_page(page)
        
        # Format data
        data = []
        for staff in page_obj:
            # Calculate age from DOB
            age = None
            if staff.date_of_birth:
                today = date.today()
                age = today.year - staff.date_of_birth.year - ((today.month, today.day) < (staff.date_of_birth.month, staff.date_of_birth.day))
            
            data.append({
                'id': staff.id,
                'staff_id': staff.staff_id or 'N/A',
                'full_name': f"{staff.first_name} {staff.surname}",
                'first_name': staff.first_name,
                'surname': staff.surname,
                'other_names': staff.other_names or '',
                'gender': staff.gender,
                'age': age,
                'date_of_birth': staff.date_of_birth.strftime('%Y-%m-%d') if staff.date_of_birth else '',
                'contact': staff.primary_phone_number,
                'email': staff.email or '',
                'personnel_type': staff.personnel_type,
                'district': staff.district.name if staff.district else '',
                'community': staff.community.name if staff.community else '',
                'date_joined': staff.date_joined.strftime('%Y-%m-%d') if staff.date_joined else '',
                'status': 'Active',
                'education_level': staff.education_level,
                'marital_status': staff.marital_status,
                'bank_name': staff.bank_name or '',
                'account_number': staff.account_number or '',
                'momo_number': staff.momo_number or '',
                'emergency_contact': staff.emergency_contact_person,
                'emergency_number': staff.emergency_contact_number
            })
        
        response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data,
            'success': True
        }
        return JsonResponse(response)
        
    except Exception as e:
        print(f"Error in get_staff_list: {str(e)}")
        return JsonResponse({
            'draw': request.GET.get('draw', 1),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_staff_detail_api(request, staff_id):
    """Get single staff details"""
    try:
        staff = PersonnelModel.objects.get(id=staff_id)
        
        # Calculate age
        age = None
        if staff.date_of_birth:
            today = date.today()
            age = today.year - staff.date_of_birth.year - ((today.month, today.day) < (staff.date_of_birth.month, staff.date_of_birth.day))
        
        data = {
            'id': staff.id,
            'first_name': staff.first_name,
            'surname': staff.surname,
            'other_names': staff.other_names or '',
            'full_name': f"{staff.first_name} {staff.surname}",
            'gender': staff.gender,
            'age': age,
            'date_of_birth': staff.date_of_birth.strftime('%Y-%m-%d') if staff.date_of_birth else '',
            'staff_id': staff.staff_id or '',
            'primary_phone_number': staff.primary_phone_number,
            'secondary_phone_number': staff.secondary_phone_number or '',
            'momo_number': staff.momo_number or '',
            'momo_name': staff.momo_name or '',
            'belongs_to_ra': staff.belongs_to_ra or '',
            'email': staff.email or '',
            'emergency_contact_person': staff.emergency_contact_person,
            'emergency_contact_number': staff.emergency_contact_number,
            'id_type': staff.id_type,
            'id_number': staff.id_number,
            'address': staff.address,
            'community_id': staff.community.id if staff.community else '',
            'community': staff.community.name if staff.community else '',
            'district_id': staff.district.id if staff.district else '',
            'district': staff.district.name if staff.district else '',
            'project_id': staff.projectTbl_foreignkey.id if staff.projectTbl_foreignkey else '',
            'project': staff.projectTbl_foreignkey.name if staff.projectTbl_foreignkey else '',
            'education_level': staff.education_level,
            'marital_status': staff.marital_status,
            'bank_id': staff.bank_id or '',
            'bank_name': staff.bank_name or '',
            'bank_branch': staff.bank_branch or '',
            'account_number': staff.account_number or '',
            'branch_id': staff.branch_id or '',
            'SSNIT_number': staff.SSNIT_number or '',
            'sort_code': staff.sort_code or '',
            'personnel_type': staff.personnel_type,
            'ezwich_number': staff.ezwich_number or '',
            'date_joined': staff.date_joined.strftime('%Y-%m-%d') if staff.date_joined else '',
            'supervisor_id': staff.supervisor_id or '',
            'image': staff.image.url if staff.image else '',
            'id_image_front': staff.id_image_front.url if staff.id_image_front else '',
            'id_image_back': staff.id_image_back.url if staff.id_image_back else '',
            'consent_form_image': staff.consent_form_image.url if staff.consent_form_image else '',
            'uid': staff.uid or '',
            'created_date': staff.created_date.strftime('%Y-%m-%d %H:%M:%S') if staff.created_date else '',
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except PersonnelModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Staff member not found'
        }, status=404)
    except Exception as e:
        print(f"Error in get_staff_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_staff(request):
    """Create a new staff member"""
    try:
        data = json.loads(request.body)
        
        # Generate UID if not provided
        uid = data.get('uid', str(uuid.uuid4()))
        
        # Get related objects
        community = None
        if data.get('community_id'):
            try:
                community = Community.objects.get(id=data['community_id'])
            except Community.DoesNotExist:
                pass
        
        district = None
        if data.get('district_id'):
            try:
                district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        
        project = None
        if data.get('project_id'):
            try:
                project = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                pass
        
        # Parse dates
        date_of_birth = None
        if data.get('date_of_birth'):
            try:
                date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except:
                pass
        
        date_joined = None
        if data.get('date_joined'):
            try:
                date_joined = datetime.strptime(data['date_joined'], '%Y-%m-%d').date()
            except:
                date_joined = timezone.now().date()
        else:
            date_joined = timezone.now().date()
        
        # Create staff - staff_id will be auto-generated by save() method
        staff = PersonnelModel.objects.create(
            first_name=data.get('first_name'),
            surname=data.get('surname'),
            other_names=data.get('other_names', ''),
            gender=data.get('gender'),
            date_of_birth=date_of_birth,
            primary_phone_number=data.get('primary_phone_number'),
            secondary_phone_number=data.get('secondary_phone_number', ''),
            email=data.get('email', ''),  # Add email field
            momo_number=data.get('momo_number', ''),
            momo_name=data.get('momo_name', ''),
            belongs_to_ra=data.get('belongs_to_ra', ''),
            emergency_contact_person=data.get('emergency_contact_person'),
            emergency_contact_number=data.get('emergency_contact_number'),
            id_type=data.get('id_type'),
            id_number=data.get('id_number'),
            address=data.get('address'),
            community=community,
            district=district,
            projectTbl_foreignkey=project,
            education_level=data.get('education_level'),
            marital_status=data.get('marital_status'),
            bank_id=data.get('bank_id', ''),
            bank_name=data.get('bank_name', ''),
            bank_branch=data.get('bank_branch', ''),
            account_number=data.get('account_number', ''),
            branch_id=data.get('branch_id', ''),
            SSNIT_number=data.get('SSNIT_number', ''),
            sort_code=data.get('sort_code', ''),
            personnel_type=data.get('personnel_type'),
            ezwich_number=data.get('ezwich_number', ''),
            date_joined=date_joined,
            supervisor_id=data.get('supervisor_id', ''),
            uid=uid
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Staff member created successfully',
            'data': {
                'id': staff.id,
                'staff_id': staff.staff_id
            }
        })
        
    except Exception as e:
        print(f"Error creating staff: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error creating staff: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_staff(request, staff_id):
    """Update an existing staff member"""
    try:
        staff = PersonnelModel.objects.get(id=staff_id, delete_field='no')
        data = json.loads(request.body)
        
        # Get related objects
        if 'community_id' in data:
            try:
                staff.community = Community.objects.get(id=data['community_id'])
            except Community.DoesNotExist:
                staff.community = None
        
        if 'district_id' in data:
            try:
                staff.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                staff.district = None
        
        if 'project_id' in data:
            try:
                staff.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                staff.projectTbl_foreignkey = None
        
        # Update fields
        fields_to_update = [
            'first_name', 'surname', 'other_names', 'gender',
            'primary_phone_number', 'secondary_phone_number', 'email',
            'momo_number', 'momo_name', 'belongs_to_ra',
            'emergency_contact_person', 'emergency_contact_number',
            'id_type', 'id_number', 'address',
            'education_level', 'marital_status',
            'bank_id', 'bank_name', 'bank_branch', 'account_number',
            'branch_id', 'SSNIT_number', 'sort_code',
            'personnel_type', 'ezwich_number', 'supervisor_id'
        ]
        
        for field in fields_to_update:
            if field in data:
                setattr(staff, field, data[field])
        
        # Update dates
        if 'date_of_birth' in data and data['date_of_birth']:
            try:
                staff.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except:
                pass
        
        if 'date_joined' in data and data['date_joined']:
            try:
                staff.date_joined = datetime.strptime(data['date_joined'], '%Y-%m-%d').date()
            except:
                pass
        
        staff.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Staff member updated successfully',
            'data': {
                'id': staff.id,
                'staff_id': staff.staff_id
            }
        })
        
    except PersonnelModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Staff member not found'
        }, status=404)
    except Exception as e:
        print(f"Error updating staff: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error updating staff: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def delete_staff(request, staff_id):
    """Soft delete a staff member"""
    try:
        staff = PersonnelModel.objects.get(id=staff_id, delete_field='no')
        
        data = json.loads(request.body)
        reason = data.get('reason', 'No reason provided')
        
        # Soft delete
        staff.delete_field = 'yes'
        staff.reason4expunge = reason
        staff.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Staff member deleted successfully'
        })
        
    except PersonnelModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Staff member not found'
        }, status=404)
    except Exception as e:
        print(f"Error deleting staff: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error deleting staff: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_staff_types(request):
    """Get list of staff types"""
    staff_types = [
        {'value': 'Rehab Assistant', 'label': 'Rehab Assistant'},
        {'value': 'Rehab Technician', 'label': 'Rehab Technician'},
        {'value': 'Project Officer', 'label': 'Project Officer'},
        {'value': 'Project Coordinator', 'label': 'Project Coordinator'},
        {'value': 'Regional Manager', 'label': 'Regional Manager'},
        {'value': 'Admin', 'label': 'Admin'}
    ]
    return JsonResponse({
        'success': True,
        'data': staff_types
    })

@require_http_methods(["GET"])
def get_districts(request):
    """Get list of districts"""
    try:
        region_id = request.GET.get('region_id')
        
        if region_id:
            districts = cocoaDistrict.objects.filter(
                region_id=region_id, 
                delete_field='no'
            ).order_by('name')
        else:
            districts = cocoaDistrict.objects.filter(delete_field='no').order_by('name')
        
        data = [{'id': d.id, 'name': d.name} for d in districts]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        print(f"Error in get_districts: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_communities(request):
    """Get list of communities by district"""
    try:
        district_id = request.GET.get('district_id')
        
        if district_id:
            communities = Community.objects.filter(
                district_id=district_id,
                delete_field='no'
            ).order_by('name')
        else:
            communities = Community.objects.filter(delete_field='no').order_by('name')
        
        data = [{'id': c.id, 'name': c.name} for c in communities]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        print(f"Error in get_communities: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_projects(request):
    """Get list of projects"""
    try:
        projects = projectTbl.objects.filter(delete_field='no').order_by('name')
        data = [{'id': p.id, 'name': p.name} for p in projects]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        print(f"Error in get_projects: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })