# views.py - Farm Management Views
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from portal.models import FarmdetailsTbl, projectTbl, staffTbl, projectStaffTbl, Farms, PersonnelModel
import json
from django.core.paginator import Paginator
from django.db import transaction
from datetime import datetime

@login_required
def farm_details_page(request):
    """Main page for farm details management"""
    projects = projectTbl.objects.all().order_by('name')
    farms = FarmdetailsTbl.objects.filter(expunge=False).select_related('farm_foreignkey', 'projectTbl_foreignkey')
    
    context = {
        'page_title': 'Farm Details Management',
        'projects': projects,
        'status_choices': FarmdetailsTbl.STATUS_CHOICES,
        'farms': farms,
    }
    return render(request, 'portal/Farms/farms.html', context)

@login_required
def farm_details_api(request):
    """API endpoint for datatable"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    
    # Base queryset
    queryset = FarmdetailsTbl.objects.filter(expunge=False).select_related(
        'farm_foreignkey', 'projectTbl_foreignkey'
    )
    
    # Search functionality
    if search_value:
        queryset = queryset.filter(
            Q(farm_reference__icontains=search_value) |
            Q(farmername__icontains=search_value) |
            Q(location__icontains=search_value) |
            Q(region__icontains=search_value) |
            Q(status__icontains=search_value) |
            Q(projectTbl_foreignkey__name__icontains=search_value)
        )
    
    # Total records
    total_records = queryset.count()
    
    # Apply pagination
    queryset = queryset.order_by('-id')[start:start + length]
    
    # Prepare data
    data = []
    for farm in queryset:
        data.append({
            'id': farm.id,
            'farm_reference': farm.farm_reference,
            'farmer_name': farm.farmername,
            'region': farm.region,
            'project': farm.projectTbl_foreignkey.name if farm.projectTbl_foreignkey else "N/A",
            'location': farm.location,
            'farm_size': f"{farm.farm_size} acres" if farm.farm_size else "N/A",
            'status': farm.status,
            'year_of_establishment': farm.year_of_establishment.strftime('%Y-%m-%d') if farm.year_of_establishment else "N/A",
            'sector': farm.sector if farm.sector else "N/A",
            'created_date': farm.created_date.strftime('%Y-%m-%d %H:%M') if farm.created_date else "N/A",
        })
    
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })

@login_required
@require_http_methods(["GET"])
def get_farm_details(request, farm_id):
    """Get single farm details"""
    try:
        farm = FarmdetailsTbl.objects.get(id=farm_id)
        
        data = {
            'id': farm.id,
            'farm_reference': farm.farm_reference,
            'farmer_name': farm.farmername,
            'region': farm.region,
            'project_id': farm.projectTbl_foreignkey.id if farm.projectTbl_foreignkey else None,
            'project_name': farm.projectTbl_foreignkey.name if farm.projectTbl_foreignkey else None,
            'location': farm.location,
            'farm_size': farm.farm_size,
            'status': farm.status,
            'year_of_establishment': farm.year_of_establishment.strftime('%Y-%m-%d') if farm.year_of_establishment else None,
            'sector': farm.sector,
            'created_date': farm.created_date.strftime('%Y-%m-%d %H:%M') if farm.created_date else None,
        }
        
        return JsonResponse({'success': True, 'data': data})
    except FarmdetailsTbl.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Farm not found'}, status=404)

@login_required
@require_http_methods(["POST"])
def create_farm(request):
    """Create new farm"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['farm_reference', 'farmer_name', 'region', 'location']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'{field.replace("_", " ").title()} is required'})
        
        # Check if farm reference already exists
        if FarmdetailsTbl.objects.filter(farm_reference=data['farm_reference']).exists():
            return JsonResponse({'success': False, 'message': 'Farm reference already exists'})
        
        # Get project if provided
        project = None
        project_id = data.get('project_id')
        if project_id:
            try:
                project = projectTbl.objects.get(id=project_id)
            except projectTbl.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Project not found'})
        
        # Parse date
        year_of_establishment = None
        if data.get('year_of_establishment'):
            try:
                year_of_establishment = datetime.strptime(data['year_of_establishment'], '%Y-%m-%d').date()
            except:
                pass
        
        # Create farm
        farm = FarmdetailsTbl.objects.create(
            farm_reference=data['farm_reference'],
            farmername=data['farmer_name'],
            region=data['region'],
            location=data['location'],
            farm_size=data.get('farm_size'),
            status=data.get('status', 'Maintenance'),
            sector=data.get('sector'),
            year_of_establishment=year_of_establishment,
            projectTbl_foreignkey=project
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Farm created successfully',
            'farm_id': farm.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def update_farm(request, farm_id):
    """Update farm details"""
    try:
        data = json.loads(request.body)
        farm = FarmdetailsTbl.objects.get(id=farm_id)
        
        # Check if farm reference is being changed and already exists
        if data.get('farm_reference') and data['farm_reference'] != farm.farm_reference:
            if FarmdetailsTbl.objects.filter(farm_reference=data['farm_reference']).exists():
                return JsonResponse({'success': False, 'message': 'Farm reference already exists'})
        
        # Update project if changed
        if data.get('project_id'):
            try:
                project = projectTbl.objects.get(id=data['project_id'])
                farm.projectTbl_foreignkey = project
            except projectTbl.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Project not found'})
        
        # Parse date
        if data.get('year_of_establishment'):
            try:
                farm.year_of_establishment = datetime.strptime(data['year_of_establishment'], '%Y-%m-%d').date()
            except:
                pass
        
        # Update fields
        farm.farm_reference = data.get('farm_reference', farm.farm_reference)
        farm.farmername = data.get('farmer_name', farm.farmername)
        farm.region = data.get('region', farm.region)
        farm.location = data.get('location', farm.location)
        farm.farm_size = data.get('farm_size', farm.farm_size)
        farm.status = data.get('status', farm.status)
        farm.sector = data.get('sector', farm.sector)
        
        farm.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Farm updated successfully'
        })
        
    except FarmdetailsTbl.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Farm not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def delete_farm(request, farm_id):
    """Soft delete farm (mark as expunged)"""
    try:
        data = json.loads(request.body)
        farm = FarmdetailsTbl.objects.get(id=farm_id)
        
        farm.expunge = True
        farm.reason4expunge = data.get('reason', 'No reason provided')
        farm.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Farm deleted successfully'
        })
        
    except FarmdetailsTbl.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Farm not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_projects_by_region(request):
    """Get projects by region for dropdown"""
    region = request.GET.get('region', '')
    
    if region:
        projects = projectTbl.objects.filter(
            farmdetailstbl__region=region
        ).distinct().values_list('name', flat=True)
    else:
        projects = projectTbl.objects.all().values_list('name', flat=True)
    
    return JsonResponse({
        'success': True,
        'projects': list(projects)
    })

# ============================================
# FARM ASSIGNMENT VIEWS
# ============================================

@login_required
def farm_assignment_page(request):
    """Render the main farm assignment page"""
    context = {
        'page_title': 'Farm Assignment Management',
        'staff_list': staffTbl.objects.all().order_by('first_name'),
        'projects': projectTbl.objects.all().order_by('name')
    }
    return render(request, 'portal/Farms/assignment.html', context)

@login_required
def farm_assignment_api(request):
    """API endpoint for DataTables server-side processing"""
    # Get DataTables parameters
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    order_column = request.GET.get('order[0][column]', '0')
    order_dir = request.GET.get('order[0][dir]', 'asc')
    
    # Base query - using projectStaffTbl for assignments
    assignments = projectStaffTbl.objects.all().select_related(
        'staffTbl_foreignkey', 'projectTbl_foreignkey'
    ).order_by('-id')
    
    # Apply search filter
    if search_value:
        assignments = assignments.filter(
            Q(staffTbl_foreignkey__first_name__icontains=search_value) |
            Q(staffTbl_foreignkey__last_name__icontains=search_value) |
            Q(projectTbl_foreignkey__name__icontains=search_value)
        )
    
    # Total records
    total_records = projectStaffTbl.objects.count()
    filtered_records = assignments.count()
    
    # Apply ordering
    column_mapping = {
        '0': 'id',  # Assignment ID
        '1': 'staffTbl_foreignkey__first_name',  # Staff Name
        '2': 'staffTbl_foreignkey__staffid',  # Staff ID
        '3': 'projectTbl_foreignkey__name',  # Project Name
        '4': 'created_date',  # Assigned Date
    }
    
    order_field = column_mapping.get(order_column, 'id')
    if order_dir == 'desc':
        order_field = f'-{order_field}'
    
    assignments = assignments.order_by(order_field)
    
    # Pagination
    assignments = assignments[start:start + length]
    
    # Prepare data
    data = []
    for assignment in assignments:
        try:
            staff = assignment.staffTbl_foreignkey
            
            # Prepare staff name
            staff_name = f"{staff.first_name} {staff.last_name}" if staff.first_name and staff.last_name else "Unknown"
            
            # Get farm count for this staff in this project
            farm_count = FarmdetailsTbl.objects.filter(
                projectTbl_foreignkey=assignment.projectTbl_foreignkey
            ).count()
            
            data.append({
                'id': assignment.id,
                'staff_name': staff_name,
                'staff_id': staff.staffid or 'N/A',
                'staff_contact': staff.contact or 'N/A',
                'project_name': assignment.projectTbl_foreignkey.name if assignment.projectTbl_foreignkey else 'N/A',
                'farm_count': farm_count,
                'assigned_date': assignment.created_date.strftime('%Y-%m-%d %H:%M') if assignment.created_date else 'N/A',
                'assignment_id': f"ASS-{assignment.id:04d}"
            })
        except Exception as e:
            print(f"Error processing assignment {assignment.id}: {e}")
            # continue
    
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })

@login_required
def get_available_farms_by_project(request):
    """Get farms by project that can be assigned"""
    project_id = request.GET.get('project_id')
    
    if not project_id:
        return JsonResponse({'success': False, 'message': 'Project ID is required'})
    
    try:
        project = projectTbl.objects.get(id=project_id)
        
        # Get all farms in this project
        farms = FarmdetailsTbl.objects.filter(
            projectTbl_foreignkey=project,
            expunge=False
        ).order_by('farm_reference')
        
        farm_list = []
        for farm in farms:
            farm_list.append({
                'id': farm.id,
                'farm_reference': farm.farm_reference or 'N/A',
                'farmer_name': farm.farmername or 'N/A',
                'region': farm.region or 'N/A',
                'location': farm.location or 'N/A',
                'farm_size': farm.farm_size or 0,
                'status': farm.status or 'N/A'
            })
        
        return JsonResponse({'success': True, 'farms': farm_list})
        
    except projectTbl.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Project not found'})

@login_required
def get_available_staff(request):
    """Get staff available for assignment"""
    # Get all staff
    staff_members = staffTbl.objects.all().order_by('first_name')
    
    staff_list = []
    for staff in staff_members:
        staff_list.append({
            'id': staff.id,
            'staff_name': f"{staff.first_name} {staff.last_name}",
            'staff_id': staff.staffid or 'N/A',
            'contact': staff.contact or 'N/A',
            'email': staff.email_address or 'N/A',
            'project': staff.projectTbl_foreignkey.name if staff.projectTbl_foreignkey else 'N/A'
        })
    
    return JsonResponse({'success': True, 'staff': staff_list})

@login_required
@require_http_methods(["POST"])
def create_assignment(request):
    """Create a new staff to project assignment"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if not data.get('staff_id') or not data.get('project_id'):
            return JsonResponse({
                'success': False,
                'message': 'Staff and Project are required'
            })
        
        staff = get_object_or_404(staffTbl, id=data['staff_id'])
        project = get_object_or_404(projectTbl, id=data['project_id'])
        
        # Check if assignment already exists
        if projectStaffTbl.objects.filter(
            staffTbl_foreignkey=staff,
            projectTbl_foreignkey=project
        ).exists():
            return JsonResponse({
                'success': False,
                'message': 'Staff is already assigned to this project'
            })
        
        # Create the assignment
        assignment = projectStaffTbl.objects.create(
            staffTbl_foreignkey=staff,
            projectTbl_foreignkey=project
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully assigned {staff.first_name} {staff.last_name} to {project.name}',
            'assignment_id': assignment.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        print(f"Error in create_assignment: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error creating assignment: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def delete_assignment(request, assignment_id):
    """Delete a project assignment"""
    try:
        assignment = get_object_or_404(projectStaffTbl, id=assignment_id)
        staff_name = f"{assignment.staffTbl_foreignkey.first_name} {assignment.staffTbl_foreignkey.last_name}"
        project_name = assignment.projectTbl_foreignkey.name if assignment.projectTbl_foreignkey else "Unknown"
        
        assignment.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Assignment for {staff_name} to {project_name} deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting assignment: {str(e)}'
        })

@login_required
def get_assignment_details(request, assignment_id):
    """Get details of a specific assignment"""
    try:
        assignment = get_object_or_404(projectStaffTbl, id=assignment_id)
        staff = assignment.staffTbl_foreignkey
        
        # Get farms in the assigned project
        farms = FarmdetailsTbl.objects.filter(
            projectTbl_foreignkey=assignment.projectTbl_foreignkey,
            expunge=False
        )
        
        farm_list = []
        for farm in farms:
            farm_list.append({
                'farm_reference': farm.farm_reference,
                'farmer_name': farm.farmername,
                'location': farm.location,
                'farm_size': farm.farm_size,
                'status': farm.status
            })
        
        data = {
            'success': True,
            'data': {
                'assignment_id': assignment.id,
                'assignment_ref': f"ASS-{assignment.id:04d}",
                'staff_name': f"{staff.first_name} {staff.last_name}",
                'staff_id': staff.staffid or 'N/A',
                'staff_contact': staff.contact or 'N/A',
                'staff_email': staff.email_address or 'N/A',
                'project_name': assignment.projectTbl_foreignkey.name if assignment.projectTbl_foreignkey else 'N/A',
                'project_id': assignment.projectTbl_foreignkey.id if assignment.projectTbl_foreignkey else None,
                'farms_count': farms.count(),
                'farms': farm_list,
                'assigned_date': assignment.created_date.strftime('%Y-%m-%d %H:%M') if assignment.created_date else 'N/A',
            }
        }
        return JsonResponse(data)
        
    except Exception as e:
        print(f"Error in get_assignment_details: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error fetching assignment details: {str(e)}'
        })

# ============================================
# PERSONNEL MANAGEMENT VIEWS
# ============================================

@login_required
def personnel_management_page(request):
    """Render the personnel management page"""
    context = {
        'page_title': 'Personnel Management',
        'projects': projectTbl.objects.all().order_by('name'),
        'personnel_types': ['Rehab Assistant', 'Field Officer', 'Supervisor', 'Manager', 'Admin'],
        'gender_choices': [('Male', 'Male'), ('Female', 'Female')],
        'education_levels': ['Primary', 'JHS', 'SHS', 'Tertiary', 'University'],
        'marital_statuses': ['Single', 'Married', 'Divorced', 'Widowed']
    }
    return render(request, 'portal/Personnel/personnel.html', context)

@login_required
def personnel_api(request):
    """API endpoint for personnel datatable"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    
    # Base queryset
    queryset = PersonnelModel.objects.all().select_related('projectTbl_foreignkey')
    
    # Search functionality
    if search_value:
        queryset = queryset.filter(
            Q(first_name__icontains=search_value) |
            Q(surname__icontains=search_value) |
            Q(other_names__icontains=search_value) |
            Q(primary_phone_number__icontains=search_value) |
            Q(id_number__icontains=search_value) |
            Q(personnel_type__icontains=search_value) |
            Q(projectTbl_foreignkey__name__icontains=search_value)
        )
    
    # Total records
    total_records = queryset.count()
    
    # Apply pagination
    queryset = queryset.order_by('-id')[start:start + length]
    
    # Prepare data
    data = []
    for person in queryset:
        data.append({
            'id': person.id,
            'full_name': f"{person.first_name} {person.surname}",
            'other_names': person.other_names or '',
            'gender': person.gender,
            'date_of_birth': person.date_of_birth.strftime('%Y-%m-%d') if person.date_of_birth else 'N/A',
            'phone_number': person.primary_phone_number,
            'personnel_type': person.personnel_type,
            'project': person.projectTbl_foreignkey.name if person.projectTbl_foreignkey else 'N/A',
            'id_number': person.id_number,
            'date_joined': person.date_joined.strftime('%Y-%m-%d') if person.date_joined else 'N/A',
            'created_date': person.created_date.strftime('%Y-%m-%d %H:%M') if person.created_date else 'N/A',
        })
    
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })

@login_required
@require_http_methods(["GET"])
def get_personnel_details(request, personnel_id):
    """Get single personnel details"""
    try:
        person = PersonnelModel.objects.get(id=personnel_id)
        
        data = {
            'id': person.id,
            'first_name': person.first_name,
            'surname': person.surname,
            'other_names': person.other_names,
            'gender': person.gender,
            'date_of_birth': person.date_of_birth.strftime('%Y-%m-%d') if person.date_of_birth else None,
            'primary_phone_number': person.primary_phone_number,
            'secondary_phone_number': person.secondary_phone_number,
            'momo_number': person.momo_number,
            'emergency_contact_person': person.emergency_contact_person,
            'emergency_contact_number': person.emergency_contact_number,
            'id_type': person.id_type,
            'id_number': person.id_number,
            'address': person.address,
            'community': person.community,
            'project_id': person.projectTbl_foreignkey.id if person.projectTbl_foreignkey else None,
            'project_name': person.projectTbl_foreignkey.name if person.projectTbl_foreignkey else None,
            'education_level': person.education_level,
            'marital_status': person.marital_status,
            'bank_id': person.bank_id,
            'account_number': person.account_number,
            'branch_id': person.branch_id,
            'sort_code': person.sort_code,
            'personnel_type': person.personnel_type,
            'ezwich_number': person.ezwich_number,
            'date_joined': person.date_joined.strftime('%Y-%m-%d') if person.date_joined else None,
            'supervisor_id': person.supervisor_id,
        }
        
        return JsonResponse({'success': True, 'data': data})
    except PersonnelModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Personnel not found'}, status=404)

@login_required
@require_http_methods(["POST"])
def create_personnel(request):
    """Create new personnel"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['first_name', 'surname', 'gender', 'date_of_birth', 
                          'primary_phone_number', 'id_type', 'id_number', 'personnel_type']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'{field.replace("_", " ").title()} is required'})
        
        # Get project if provided
        project = None
        project_id = data.get('project_id')
        if project_id:
            try:
                project = projectTbl.objects.get(id=project_id)
            except projectTbl.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Project not found'})
        
        # Parse dates
        date_of_birth = None
        date_joined = None
        
        if data.get('date_of_birth'):
            try:
                date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except:
                pass
        
        if data.get('date_joined'):
            try:
                date_joined = datetime.strptime(data['date_joined'], '%Y-%m-%d').date()
            except:
                pass
        
        # Create personnel
        personnel = PersonnelModel.objects.create(
            first_name=data['first_name'],
            surname=data['surname'],
            other_names=data.get('other_names'),
            gender=data['gender'],
            date_of_birth=date_of_birth,
            primary_phone_number=data['primary_phone_number'],
            secondary_phone_number=data.get('secondary_phone_number'),
            momo_number=data.get('momo_number'),
            emergency_contact_person=data.get('emergency_contact_person', ''),
            emergency_contact_number=data.get('emergency_contact_number', ''),
            id_type=data['id_type'],
            id_number=data['id_number'],
            address=data.get('address', ''),
            community=data.get('community', ''),
            projectTbl_foreignkey=project,
            education_level=data.get('education_level', ''),
            marital_status=data.get('marital_status', ''),
            bank_id=data.get('bank_id'),
            account_number=data.get('account_number'),
            branch_id=data.get('branch_id'),
            sort_code=data.get('sort_code'),
            personnel_type=data['personnel_type'],
            ezwich_number=data.get('ezwich_number'),
            date_joined=date_joined,
            supervisor_id=data.get('supervisor_id'),
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Personnel created successfully',
            'personnel_id': personnel.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def update_personnel(request, personnel_id):
    """Update personnel details"""
    try:
        data = json.loads(request.body)
        personnel = PersonnelModel.objects.get(id=personnel_id)
        
        # Update project if changed
        if data.get('project_id'):
            try:
                project = projectTbl.objects.get(id=data['project_id'])
                personnel.projectTbl_foreignkey = project
            except projectTbl.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Project not found'})
        
        # Parse dates
        if data.get('date_of_birth'):
            try:
                personnel.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except:
                pass
        
        if data.get('date_joined'):
            try:
                personnel.date_joined = datetime.strptime(data['date_joined'], '%Y-%m-%d').date()
            except:
                pass
        
        # Update fields
        personnel.first_name = data.get('first_name', personnel.first_name)
        personnel.surname = data.get('surname', personnel.surname)
        personnel.other_names = data.get('other_names', personnel.other_names)
        personnel.gender = data.get('gender', personnel.gender)
        personnel.primary_phone_number = data.get('primary_phone_number', personnel.primary_phone_number)
        personnel.secondary_phone_number = data.get('secondary_phone_number', personnel.secondary_phone_number)
        personnel.momo_number = data.get('momo_number', personnel.momo_number)
        personnel.emergency_contact_person = data.get('emergency_contact_person', personnel.emergency_contact_person)
        personnel.emergency_contact_number = data.get('emergency_contact_number', personnel.emergency_contact_number)
        personnel.id_type = data.get('id_type', personnel.id_type)
        personnel.id_number = data.get('id_number', personnel.id_number)
        personnel.address = data.get('address', personnel.address)
        personnel.community = data.get('community', personnel.community)
        personnel.education_level = data.get('education_level', personnel.education_level)
        personnel.marital_status = data.get('marital_status', personnel.marital_status)
        personnel.bank_id = data.get('bank_id', personnel.bank_id)
        personnel.account_number = data.get('account_number', personnel.account_number)
        personnel.branch_id = data.get('branch_id', personnel.branch_id)
        personnel.sort_code = data.get('sort_code', personnel.sort_code)
        personnel.personnel_type = data.get('personnel_type', personnel.personnel_type)
        personnel.ezwich_number = data.get('ezwich_number', personnel.ezwich_number)
        personnel.supervisor_id = data.get('supervisor_id', personnel.supervisor_id)
        
        personnel.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Personnel updated successfully'
        })
        
    except PersonnelModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Personnel not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def delete_personnel(request, personnel_id):
    """Delete personnel record"""
    try:
        personnel = PersonnelModel.objects.get(id=personnel_id)
        personnel.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Personnel deleted successfully'
        })
        
    except PersonnelModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Personnel not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)