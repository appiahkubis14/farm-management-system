from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from portal.models import FarmdetailsTbl, cocoaDistrict
import json
from django.core.paginator import Paginator
from django.db import transaction
from datetime import datetime

@login_required
def farm_details_page(request):
    """Main page for farm details management"""
    districts = cocoaDistrict.objects.all().order_by('district')
    farms = FarmdetailsTbl.objects.filter(expunge=False).select_related('farm_foreignkey', 'districtTbl_foreignkey')
    
    context = {
        'page_title': 'Farm Details Management',
        'districts': districts,
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
        'farm_foreignkey', 'districtTbl_foreignkey'
    )
    
    # Search functionality
    if search_value:
        queryset = queryset.filter(
            Q(farm_reference__icontains=search_value) |
            Q(farmername__icontains=search_value) |
            Q(location__icontains=search_value) |
            Q(district__icontains=search_value) |
            Q(region__icontains=search_value) |
            Q(status__icontains=search_value)
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
            'district': farm.district,
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
            'district': farm.district,
            'location': farm.location,
            'farm_size': farm.farm_size,
            'status': farm.status,
            'year_of_establishment': farm.year_of_establishment.strftime('%Y-%m-%d') if farm.year_of_establishment else None,
            'sector': farm.sector,
            'created_date': farm.created_date.strftime('%Y-%m-%d %H:%M') if farm.created_date else None,
            # 'updated_at': farm.updated_at.strftime('%Y-%m-%d %H:%M') if farm.updated_at else None,
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
        required_fields = ['farm_reference', 'farmer_name', 'region', 'district', 'location']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'{field.replace("_", " ").title()} is required'})
        
        # Check if farm reference already exists
        if FarmdetailsTbl.objects.filter(farm_reference=data['farm_reference']).exists():
            return JsonResponse({'success': False, 'message': 'Farm reference already exists'})
        
        # Get or create cocoa district
        district_obj, created = cocoaDistrict.objects.get_or_create(
            district=data['district'],
            defaults={'district_code': data['district'][:3].upper()}
        )
        
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
            district=data['district'],
            location=data['location'],
            farm_size=data.get('farm_size'),
            status=data.get('status', 'Maintenance'),
            sector=data.get('sector'),
            year_of_establishment=year_of_establishment,
            districtTbl_foreignkey=district_obj
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
        
        # Update district if changed
        if data.get('district') and data['district'] != farm.district:
            district_obj, created = cocoaDistrict.objects.get_or_create(
                district=data['district'],
                defaults={'district_code': data['district'][:3].upper()}
            )
            farm.districtTbl_foreignkey = district_obj
        
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
        farm.district = data.get('district', farm.district)
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
def get_districts_by_region(request):
    """Get districts by region for dropdown"""
    region = request.GET.get('region', '')
    
    if region:
        districts = cocoaDistrict.objects.filter(
            farmdetailstbl__region=region
        ).distinct().values_list('district', flat=True)
    else:
        districts = cocoaDistrict.objects.all().values_list('district', flat=True)
    
    return JsonResponse({
        'success': True,
        'districts': list(districts)
    })






##########################################################################################################################################################

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from portal.models import projectStaffTbl, staffTbl, FarmdetailsTbl, Farms
from django.db.models import Q

def farm_assignment_page(request):
    """Render the main farm assignment page"""
    context = {
        'page_title': 'Farm Assignment Management',
        'staff_list': staffTbl.objects.all().order_by('first_name')
    }
    return render(request, 'portal/Farms/assignment.html', context)
def farm_assignment_api(request):
    """API endpoint for DataTables server-side processing"""
    # Get DataTables parameters
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    order_column = request.GET.get('order[0][column]', '0')
    order_dir = request.GET.get('order[0][dir]', 'asc')
    
    # Base query
    assignments = projectStaffTbl.objects.all().select_related(
        'staffTbl_foreignkey'
    ).order_by('-id')
    
    # Apply search filter
    if search_value:
        assignments = assignments.filter(
            Q(staffTbl_foreignkey__first_name__icontains=search_value) |
            Q(staffTbl_foreignkey__last_name__icontains=search_value) |
            Q(farms__farmdetailstbl__farm_reference__icontains=search_value) |  # Changed to farmdetailstbl
            Q(farms__farmdetailstbl__farmername__icontains=search_value) |      # Changed to farmdetailstbl
            Q(farms__farmdetailstbl__region__icontains=search_value) |          # Changed to farmdetailstbl
            Q(farms__farmdetailstbl__district__icontains=search_value)          # Changed to farmdetailstbl
        )
    
    # Total records
    total_records = projectStaffTbl.objects.count()
    filtered_records = assignments.count()
    
    # Apply ordering
    column_mapping = {
        '0': 'id',  # Assignment ID
        '1': 'staffTbl_foreignkey__first_name',  # Staff Name
        '2': 'staffTbl_foreignkey__staffid',  # Staff ID
        '3': 'farms__farmdetailstbl__farm_reference',  # Farm Reference
        '4': 'farms__farmdetailstbl__farmername',  # Farmer Name
        '5': 'farms__farmdetailstbl__region',  # Region
        '6': 'farms__farmdetailstbl__district',  # District
        '7': 'created_date',  # Assigned Date
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
            # Get farm details using reverse relationship
            farm_details = FarmdetailsTbl.objects.filter(farm_foreignkey=assignment.farms).first()
            staff = assignment.staffTbl_foreignkey
            
            # Prepare staff name
            staff_name = f"{staff.first_name} {staff.last_name}" if staff.first_name and staff.last_name else "Unknown"
            
            # Prepare farm reference and other details
            farm_reference = farm_details.farm_reference if farm_details else 'N/A'
            farmer_name = farm_details.farmername if farm_details else 'N/A'
            region = farm_details.region if farm_details else 'N/A'
            district = farm_details.district if farm_details else 'N/A'
            location = farm_details.location if farm_details else 'N/A'
            farm_size = farm_details.farm_size if farm_details else 'N/A'
            status = farm_details.status if farm_details else 'N/A'
            
            data.append({
                'id': assignment.id,
                'staff_name': staff_name,
                'staff_id': staff.staffid or 'N/A',
                'staff_designation': staff.designation.group_name if staff.designation else 'N/A',
                'farm_reference': farm_reference,
                'farmer_name': farmer_name,
                'region': region,
                'district': district,
                'location': location,
                'farm_size': farm_size,
                'status': status,
                'assigned_date': assignment.created_date.strftime('%Y-%m-%d %H:%M') if assignment.created_date else 'N/A',
                'assignment_id': f"ASS-{assignment.id:04d}"
            })
            get_available_staff(request)
        except Exception as e:
            print(f"Error processing assignment {assignment.id}: {e}")
            continue
    
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })

def get_available_farms(request):
    """Get farms that are not assigned to any staff"""
    # Get IDs of farms that are already assigned
    assigned_farm_ids = projectStaffTbl.objects.values_list(flat=True)
    
    # Get available farms (not assigned and not expunged)
    available_farms = FarmdetailsTbl.objects.filter(
        expunge=False
    ).exclude(
        farm_foreignkey__id__in=assigned_farm_ids
    ).select_related('farm_foreignkey').order_by('farm_reference')
    
    farm_list = []
    for farm_detail in available_farms:
        farm_list.append({
            'id': farm_detail.farm_foreignkey.id if farm_detail.farm_foreignkey else farm_detail.id,
            'farm_reference': farm_detail.farm_reference or 'N/A',
            'farmer_name': farm_detail.farmername or 'N/A',
            'region': farm_detail.region or 'N/A',
            'district': farm_detail.district or 'N/A',
            'location': farm_detail.location or 'N/A',
            'status': farm_detail.status or 'N/A'
        })
    
    return JsonResponse({'success': True, 'farms': farm_list})

def get_available_staff(request):
    """Get staff available for assignment (Field Officers)"""
    # Get staff already assigned to farms today
    assigned_staff_ids = projectStaffTbl.objects.values_list('staffTbl_foreignkey_id', flat=True)
    
    # Get available staff (Field Officers)
    available_staff = staffTbl.objects.filter(
        designation__group_name="Field Officer"
    ).exclude(id__in=assigned_staff_ids).order_by('first_name')
    
    staff_list = []
    for staff in available_staff:
        staff_list.append({
            'id': staff.id,
            'staff_name': f"{staff.first_name} {staff.last_name}",
            'staff_id': staff.staffid,
            'designation': staff.designation.group_name if staff.designation else 'N/A',
            'contact': staff.contact,
            'email': staff.email_address
        })

        print(staff_list)
    
    return JsonResponse({'success': True, 'staff': staff_list})

@csrf_exempt
@require_http_methods(["POST"])
def create_assignment(request):
    """Create a new farm assignment"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if not data.get('staff_id') or not data.get('farm_ids'):
            return JsonResponse({
                'success': False,
                'message': 'Staff and at least one farm are required'
            })
        
        staff = get_object_or_404(staffTbl, id=data['staff_id'])
        farm_ids = data['farm_ids']
        
        created_assignments = []
        for farm_id in farm_ids:
            try:
                # Get the Farms object
                farm = get_object_or_404(Farms, id=farm_id)
                
                # Check if assignment already exists
                if projectStaffTbl.objects.filter(
                    staffTbl_foreignkey=staff,
                    farms=farm
                ).exists():
                    continue
                
                # Create the assignment
                assignment = projectStaffTbl.objects.create(
                    staffTbl_foreignkey=staff,
                    farms=farm
                )
                
                # Get farm details for response
                farm_detail = FarmdetailsTbl.objects.filter(farm_foreignkey=farm).first()
                
                created_assignments.append({
                    'assignment_id': assignment.id,
                    'farm_reference': farm_detail.farm_reference if farm_detail else 'Unknown'
                })
                
            except Exception as e:
                print(f"Error assigning farm {farm_id} to staff {staff.id}: {e}")
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully assigned {len(created_assignments)} farm(s) to {staff.first_name} {staff.last_name}',
            'assignments': created_assignments
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

@csrf_exempt
@require_http_methods(["POST"])
def delete_assignment(request, assignment_id):
    """Delete a farm assignment"""
    try:
        assignment = get_object_or_404(projectStaffTbl, id=assignment_id)
        assignment.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Assignment deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting assignment: {str(e)}'
        })

def get_assignment_details(request, assignment_id):
    """Get details of a specific assignment"""
    try:
        assignment = get_object_or_404(projectStaffTbl, id=assignment_id)
        
        # Get farm details through reverse relationship
        farm_detail = FarmdetailsTbl.objects.filter(farm_foreignkey=assignment.farms).first()
        staff = assignment.staffTbl_foreignkey
        
        data = {
            'success': True,
            'data': {
                'assignment_id': assignment.id,
                'assignment_ref': f"ASS-{assignment.id:04d}",
                'staff_name': f"{staff.first_name} {staff.last_name}",
                'staff_id': staff.staffid,
                'staff_designation': staff.designation.group_name if staff.designation else 'N/A',
                'staff_contact': staff.contact,
                'staff_email': staff.email_address,
                'farm_reference': farm_detail.farm_reference if farm_detail else 'N/A',
                'farmer_name': farm_detail.farmername if farm_detail else 'N/A',
                'region': farm_detail.region if farm_detail else 'N/A',
                'district': farm_detail.district if farm_detail else 'N/A',
                'location': farm_detail.location if farm_detail else 'N/A',
                'farm_size': farm_detail.farm_size if farm_detail else 'N/A',
                'farm_status': farm_detail.status if farm_detail else 'N/A',
                'year_established': farm_detail.year_of_establishment.strftime('%Y-%m-%d') if farm_detail and farm_detail.year_of_establishment else 'N/A',
                'assigned_date': assignment.created_date.strftime('%Y-%m-%d %H:%M') if assignment.created_date else 'N/A',
                'assignment_notes': 'N/A'
            }
        }
        return JsonResponse(data)
        
    except Exception as e:
        print(f"Error in get_assignment_details: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error fetching assignment details: {str(e)}'
        })