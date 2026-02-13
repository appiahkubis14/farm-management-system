# views.py - Add these views

import json
import uuid
import csv
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from portal.models import (
    EquipmentModel, EquipmentAssignmentModel,
    staffTbl, projectTbl, cocoaDistrict
)
import logging

logger = logging.getLogger(__name__)

# ============== EQUIPMENT OVERVIEW PAGE ==============

@login_required
def equipment_overview_page(request):
    """Render the Equipment Overview management page"""
    status_choices = ['Good', 'Fair', 'Bad', 'Under Repair']
    condition_choices = ['Good', 'Fair', 'Bad', 'Under Repair']
    
    context = {
        'status_choices': status_choices,
        'condition_choices': condition_choices,
    }
    return render(request, 'portal/equipment/equipment_overview.html', context)


# ============== EQUIPMENT API VIEWS ==============

@login_required
@require_http_methods(["GET"])
def equipment_list(request):
    """Get paginated list of equipment"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Filter parameters
        status = request.GET.get('status')
        district_id = request.GET.get('district_id')
        project_id = request.GET.get('project_id')
        assigned = request.GET.get('assigned')  # 'yes', 'no', or null
        
        # Base queryset
        queryset = EquipmentModel.objects.filter(delete_field='no').select_related(
            'staff_name', 'projectTbl_foreignkey', 'district'
        ).order_by('-created_date')
        
        # Apply filters
        if status:
            queryset = queryset.filter(status=status)
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        if project_id:
            queryset = queryset.filter(projectTbl_foreignkey_id=project_id)
        
        # Filter by assignment status
        if assigned == 'yes':
            queryset = queryset.filter(staff_name__isnull=False)
        elif assigned == 'no':
            queryset = queryset.filter(staff_name__isnull=True)
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(equipment_code__icontains=search_value) |
                Q(equipment__icontains=search_value) |
                Q(serial_number__icontains=search_value) |
                Q(manufacturer__icontains=search_value) |
                Q(staff_name__first_name__icontains=search_value) |
                Q(staff_name__last_name__icontains=search_value)
            )
        
        # Get total counts
        total_records = queryset.count()
        
        # Apply pagination
        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        page_obj = paginator.get_page(page_number)
        
        # Prepare data
        data = []
        for equipment in page_obj:
            # Get current assignment
            current_assignment = EquipmentAssignmentModel.objects.filter(
                equipment=equipment,
                status='Assigned',
                delete_field='no'
            ).select_related('assigned_to').first()
            
            data.append({
                'id': equipment.id,
                'uid': equipment.uid,
                'equipment_code': equipment.equipment_code,
                'equipment': equipment.equipment,
                'status': equipment.status,
                'serial_number': equipment.serial_number,
                'manufacturer': equipment.manufacturer,
                'pic_serial_number': equipment.pic_serial_number.url if equipment.pic_serial_number else None,
                'pic_equipment': equipment.pic_equipment.url if equipment.pic_equipment else None,
                'staff_id': equipment.staff_name.id if equipment.staff_name else None,
                'staff_name': f"{equipment.staff_name.first_name} {equipment.staff_name.last_name}" if equipment.staff_name else None,
                'assigned_to': current_assignment.assigned_to.get_full_name() if current_assignment else None,
                'assignment_date': current_assignment.assignment_date.strftime('%Y-%m-%d %H:%M') if current_assignment else None,
                'project_id': equipment.projectTbl_foreignkey.id if equipment.projectTbl_foreignkey else None,
                'project_name': equipment.projectTbl_foreignkey.name if equipment.projectTbl_foreignkey else 'N/A',
                'district_id': equipment.district.id if equipment.district else None,
                'district_name': equipment.district.name if equipment.district else 'N/A',
                'date_of_capturing': equipment.date_of_capturing.strftime('%Y-%m-%d %H:%M:%S') if equipment.date_of_capturing else None,
                'created_date': equipment.created_date.strftime('%Y-%m-%d %H:%M:%S') if equipment.created_date else None,
                'is_assigned': equipment.staff_name is not None,
            })
        
        response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data,
            'success': True
        }
        return JsonResponse(response)
        
    except Exception as e:
        logger.error(f"Error in equipment_list: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e),
            'data': []
        })


@login_required
@require_http_methods(["GET"])
def equipment_stats(request):
    """Get equipment statistics"""
    try:
        # Base queryset
        queryset = EquipmentModel.objects.filter(delete_field='no')
        
        # Apply filters from request
        district_id = request.GET.get('district_id')
        project_id = request.GET.get('project_id')
        
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        if project_id:
            queryset = queryset.filter(projectTbl_foreignkey_id=project_id)
        
        # Get statistics
        total_equipment = queryset.count()
        
        # Count by status
        status_counts = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Count assigned vs unassigned
        assigned_count = queryset.filter(staff_name__isnull=False).count()
        unassigned_count = queryset.filter(staff_name__isnull=True).count()
        
        # Count by manufacturer
        manufacturer_counts = queryset.values('manufacturer').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Recent equipment
        recent_equipment = queryset.order_by('-created_date')[:5].values(
            'equipment_code', 'equipment', 'status'
        )
        
        data = {
            'total_equipment': total_equipment,
            'assigned_count': assigned_count,
            'unassigned_count': unassigned_count,
            'status_counts': list(status_counts),
            'manufacturer_counts': list(manufacturer_counts),
            'recent_equipment': list(recent_equipment),
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error in equipment_stats: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def equipment_create(request):
    """Create new equipment"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['equipment', 'serial_number', 'manufacturer']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required'
                })
        
        # Check for duplicate serial number
        if EquipmentModel.objects.filter(serial_number=data['serial_number'], delete_field='no').exists():
            return JsonResponse({
                'success': False,
                'message': 'Equipment with this serial number already exists'
            })
        
        # Create equipment
        equipment = EquipmentModel()
        equipment.uid = str(uuid.uuid4())
        equipment.equipment = data.get('equipment')
        equipment.status = data.get('status', 'Good')
        equipment.serial_number = data.get('serial_number')
        equipment.manufacturer = data.get('manufacturer')
        
        # Set foreign keys
        if data.get('staff_id'):
            try:
                equipment.staff_name = staffTbl.objects.get(id=data['staff_id'])
            except staffTbl.DoesNotExist:
                pass
        
        if data.get('project_id'):
            try:
                equipment.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                pass
        
        if data.get('district_id'):
            try:
                equipment.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        
        equipment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Equipment created successfully',
            'data': {'id': equipment.id, 'equipment_code': equipment.equipment_code}
        })
        
    except Exception as e:
        logger.error(f"Error in equipment_create: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["GET"])
def equipment_detail(request, pk):
    """Get equipment details with assignment history"""
    try:
        equipment = EquipmentModel.objects.select_related(
            'staff_name', 'projectTbl_foreignkey', 'district'
        ).get(pk=pk, delete_field='no')
        
        # Get assignment history
        assignments = EquipmentAssignmentModel.objects.filter(
            equipment=equipment,
            delete_field='no'
        ).select_related('assigned_to', 'assigned_by').order_by('-assignment_date')
        
        assignment_history = []
        for a in assignments:
            assignment_history.append({
                'id': a.id,
                'assigned_to': a.assigned_to.get_full_name() if a.assigned_to else None,
                'assigned_by': a.assigned_by.get_full_name() if a.assigned_by else None,
                'assignment_date': a.assignment_date.strftime('%Y-%m-%d %H:%M:%S'),
                'return_date': a.return_date.strftime('%Y-%m-%d %H:%M:%S') if a.return_date else None,
                'condition_at_assignment': a.condition_at_assignment,
                'notes': a.notes,
                'status': a.status,
            })
        
        data = {
            'id': equipment.id,
            'uid': equipment.uid,
            'equipment_code': equipment.equipment_code,
            'equipment': equipment.equipment,
            'status': equipment.status,
            'serial_number': equipment.serial_number,
            'manufacturer': equipment.manufacturer,
            'pic_serial_number': equipment.pic_serial_number.url if equipment.pic_serial_number else None,
            'pic_equipment': equipment.pic_equipment.url if equipment.pic_equipment else None,
            'staff_id': equipment.staff_name.id if equipment.staff_name else None,
            'staff_name': f"{equipment.staff_name.first_name} {equipment.staff_name.last_name}" if equipment.staff_name else None,
            'project_id': equipment.projectTbl_foreignkey.id if equipment.projectTbl_foreignkey else None,
            'project_name': equipment.projectTbl_foreignkey.name if equipment.projectTbl_foreignkey else 'N/A',
            'district_id': equipment.district.id if equipment.district else None,
            'district_name': equipment.district.name if equipment.district else 'N/A',
            'date_of_capturing': equipment.date_of_capturing.strftime('%Y-%m-%d %H:%M:%S') if equipment.date_of_capturing else None,
            'created_date': equipment.created_date.strftime('%Y-%m-%d %H:%M:%S') if equipment.created_date else None,
            'assignment_history': assignment_history,
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except EquipmentModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Equipment not found'
        })
    except Exception as e:
        logger.error(f"Error in equipment_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def equipment_update(request, pk):
    """Update equipment"""
    try:
        equipment = EquipmentModel.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body)
        
        # Check for duplicate serial number if changed
        new_serial = data.get('serial_number')
        if new_serial and new_serial != equipment.serial_number:
            if EquipmentModel.objects.filter(serial_number=new_serial, delete_field='no').exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Equipment with this serial number already exists'
                })
        
        # Update fields
        if data.get('equipment'):
            equipment.equipment = data['equipment']
        if data.get('status'):
            equipment.status = data['status']
        if data.get('serial_number'):
            equipment.serial_number = data['serial_number']
        if data.get('manufacturer'):
            equipment.manufacturer = data['manufacturer']
        
        # Update foreign keys
        if data.get('staff_id'):
            try:
                equipment.staff_name = staffTbl.objects.get(id=data['staff_id'])
            except staffTbl.DoesNotExist:
                pass
        elif 'staff_id' in data and data['staff_id'] is None:
            equipment.staff_name = None
        
        if data.get('project_id'):
            try:
                equipment.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                pass
        elif 'project_id' in data and data['project_id'] is None:
            equipment.projectTbl_foreignkey = None
        
        if data.get('district_id'):
            try:
                equipment.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        elif 'district_id' in data and data['district_id'] is None:
            equipment.district = None
        
        equipment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Equipment updated successfully'
        })
        
    except EquipmentModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Equipment not found'
        })
    except Exception as e:
        logger.error(f"Error in equipment_update: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def equipment_delete(request, pk):
    """Soft delete equipment"""
    try:
        equipment = EquipmentModel.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', 'No reason provided')
        
        # Check if equipment is currently assigned
        if equipment.staff_name:
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete equipment that is currently assigned. Please return it first.'
            })
        
        # Soft delete
        equipment.delete_field = 'yes'
        equipment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Equipment deleted successfully'
        })
        
    except EquipmentModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Equipment not found'
        })
    except Exception as e:
        logger.error(f"Error in equipment_delete: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# ============== EQUIPMENT ASSIGNMENT API VIEWS ==============

@login_required
@require_http_methods(["GET"])
def equipment_assignment_list(request):
    """Get paginated list of equipment assignments"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Filter parameters
        status = request.GET.get('status', 'Assigned')
        equipment_id = request.GET.get('equipment_id')
        assigned_to_id = request.GET.get('assigned_to_id')
        
        # Base queryset
        queryset = EquipmentAssignmentModel.objects.filter(
            delete_field='no'
        ).select_related(
            'equipment', 'assigned_to', 'assigned_by',
            'projectTbl_foreignkey', 'district'
        ).order_by('-assignment_date')
        
        # Apply filters
        if status:
            queryset = queryset.filter(status=status)
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        if assigned_to_id:
            queryset = queryset.filter(assigned_to_id=assigned_to_id)
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(equipment__equipment__icontains=search_value) |
                Q(equipment__equipment_code__icontains=search_value) |
                Q(assigned_to__first_name__icontains=search_value) |
                Q(assigned_to__last_name__icontains=search_value) |
                Q(notes__icontains=search_value)
            )
        
        # Get total counts
        total_records = queryset.count()
        
        # Apply pagination
        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        page_obj = paginator.get_page(page_number)
        
        # Prepare data
        data = []
        for a in page_obj:
            data.append({
                'id': a.id,
                'uid': a.uid,
                'equipment_id': a.equipment.id,
                'equipment_code': a.equipment.equipment_code,
                'equipment_name': a.equipment.equipment,
                'assigned_to_id': a.assigned_to.id if a.assigned_to else None,
                'assigned_to_name': f"{a.assigned_to.first_name} {a.assigned_to.last_name}" if a.assigned_to else None,
                'assigned_by_id': a.assigned_by.id if a.assigned_by else None,
                'assigned_by_name': f"{a.assigned_by.first_name} {a.assigned_by.last_name}" if a.assigned_by else None,
                'assignment_date': a.assignment_date.strftime('%Y-%m-%d %H:%M:%S'),
                'return_date': a.return_date.strftime('%Y-%m-%d %H:%M:%S') if a.return_date else None,
                'condition_at_assignment': a.condition_at_assignment,
                'notes': a.notes,
                'status': a.status,
                'project_id': a.projectTbl_foreignkey.id if a.projectTbl_foreignkey else None,
                'project_name': a.projectTbl_foreignkey.name if a.projectTbl_foreignkey else 'N/A',
                'district_id': a.district.id if a.district else None,
                'district_name': a.district.name if a.district else 'N/A',
            })
        
        response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data,
            'success': True
        }
        return JsonResponse(response)
        
    except Exception as e:
        logger.error(f"Error in equipment_assignment_list: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e),
            'data': []
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def equipment_assign(request, pk):
    """Assign equipment to staff"""
    try:
        equipment = EquipmentModel.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body)
        
        # Validate required fields
        if not data.get('assigned_to_id'):
            return JsonResponse({
                'success': False,
                'message': 'Please select a staff member to assign to'
            })
        
        if not data.get('condition_at_assignment'):
            return JsonResponse({
                'success': False,
                'message': 'Please specify the condition at assignment'
            })
        
        # Check if equipment is already assigned
        if equipment.staff_name:
            return JsonResponse({
                'success': False,
                'message': 'Equipment is already assigned to someone'
            })
        
        # Get staff
        try:
            assigned_to = staffTbl.objects.get(id=data['assigned_to_id'])
        except staffTbl.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Staff member not found'
            })
        
        # Get current user as assigned_by
        try:
            assigned_by = staffTbl.objects.get(user=request.user)
        except staffTbl.DoesNotExist:
            assigned_by = None
        
        # Create assignment record
        assignment = EquipmentAssignmentModel()
        assignment.uid = str(uuid.uuid4())
        assignment.equipment = equipment
        assignment.assigned_to = assigned_to
        assignment.assigned_by = assigned_by
        assignment.condition_at_assignment = data.get('condition_at_assignment')
        assignment.notes = data.get('notes', '')
        assignment.status = 'Assigned'
        assignment.projectTbl_foreignkey = equipment.projectTbl_foreignkey
        assignment.district = equipment.district
        assignment.save()
        
        # Update equipment
        equipment.staff_name = assigned_to
        equipment.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Equipment assigned to {assigned_to.first_name} {assigned_to.last_name} successfully'
        })
        
    except EquipmentModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Equipment not found'
        })
    except Exception as e:
        logger.error(f"Error in equipment_assign: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def equipment_return(request, pk):
    """Return equipment from assignment"""
    try:
        equipment = EquipmentModel.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body)
        
        # Check if equipment is assigned
        if not equipment.staff_name:
            return JsonResponse({
                'success': False,
                'message': 'Equipment is not currently assigned'
            })
        
        # Find current assignment
        current_assignment = EquipmentAssignmentModel.objects.filter(
            equipment=equipment,
            status='Assigned',
            delete_field='no'
        ).first()
        
        if not current_assignment:
            return JsonResponse({
                'success': False,
                'message': 'No active assignment found for this equipment'
            })
        
        # Update assignment
        current_assignment.return_date = timezone.now()
        current_assignment.status = 'Returned'
        current_assignment.notes = data.get('notes', current_assignment.notes)
        current_assignment.save()
        
        # Update equipment
        equipment.staff_name = None
        equipment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Equipment returned successfully'
        })
        
    except EquipmentModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Equipment not found'
        })
    except Exception as e:
        logger.error(f"Error in equipment_return: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["GET"])
def equipment_assignment_detail(request, pk):
    """Get assignment details"""
    try:
        assignment = EquipmentAssignmentModel.objects.select_related(
            'equipment', 'assigned_to', 'assigned_by',
            'projectTbl_foreignkey', 'district'
        ).get(pk=pk, delete_field='no')
        
        data = {
            'id': assignment.id,
            'uid': assignment.uid,
            'equipment_id': assignment.equipment.id,
            'equipment_code': assignment.equipment.equipment_code,
            'equipment_name': assignment.equipment.equipment,
            'equipment_serial': assignment.equipment.serial_number,
            'assigned_to_id': assignment.assigned_to.id if assignment.assigned_to else None,
            'assigned_to_name': f"{assignment.assigned_to.first_name} {assignment.assigned_to.last_name}" if assignment.assigned_to else None,
            'assigned_to_contact': assignment.assigned_to.contact if assignment.assigned_to else None,
            'assigned_by_id': assignment.assigned_by.id if assignment.assigned_by else None,
            'assigned_by_name': f"{assignment.assigned_by.first_name} {assignment.assigned_by.last_name}" if assignment.assigned_by else None,
            'assignment_date': assignment.assignment_date.strftime('%Y-%m-%d %H:%M:%S'),
            'return_date': assignment.return_date.strftime('%Y-%m-%d %H:%M:%S') if assignment.return_date else None,
            'condition_at_assignment': assignment.condition_at_assignment,
            'notes': assignment.notes,
            'status': assignment.status,
            'project_id': assignment.projectTbl_foreignkey.id if assignment.projectTbl_foreignkey else None,
            'project_name': assignment.projectTbl_foreignkey.name if assignment.projectTbl_foreignkey else 'N/A',
            'district_id': assignment.district.id if assignment.district else None,
            'district_name': assignment.district.name if assignment.district else 'N/A',
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except EquipmentAssignmentModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Assignment not found'
        })
    except Exception as e:
        logger.error(f"Error in equipment_assignment_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# ============== EXPORT FUNCTION ==============

@login_required
@require_http_methods(["GET"])
def export_equipment(request):
    """Export equipment inventory to CSV"""
    try:
        # Get filter parameters
        status = request.GET.get('status')
        district_id = request.GET.get('district_id')
        assigned = request.GET.get('assigned')
        
        # Base queryset
        queryset = EquipmentModel.objects.filter(delete_field='no').select_related(
            'staff_name', 'district'
        ).order_by('-created_date')
        
        # Apply filters
        if status:
            queryset = queryset.filter(status=status)
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        if assigned == 'yes':
            queryset = queryset.filter(staff_name__isnull=False)
        elif assigned == 'no':
            queryset = queryset.filter(staff_name__isnull=True)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="equipment_inventory_{timestamp}.csv"'
        
        writer = csv.writer(response)
        
        # Write headers
        writer.writerow([
            'Equipment Code', 'Equipment Name', 'Serial Number', 'Manufacturer',
            'Status', 'Assigned To', 'District', 'Project', 'Date Added'
        ])
        
        # Write data
        for eq in queryset:
            writer.writerow([
                eq.equipment_code or '',
                eq.equipment,
                eq.serial_number,
                eq.manufacturer,
                eq.status,
                f"{eq.staff_name.first_name} {eq.staff_name.last_name}" if eq.staff_name else 'Unassigned',
                eq.district.name if eq.district else '',
                eq.projectTbl_foreignkey.name if eq.projectTbl_foreignkey else '',
                eq.created_date.strftime('%Y-%m-%d') if eq.created_date else ''
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error in export_equipment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# ============== HELPER API VIEWS ==============

@login_required
def get_staff(request):
    """Get staff for dropdown"""
    try:
        staff = staffTbl.objects.filter(delete_field='no').order_by('first_name', 'last_name')
        
        search = request.GET.get('search', '')
        if search:
            staff = staff.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(staffid__icontains=search)
            )
        
        district_id = request.GET.get('district_id')
        if district_id:
            staff = staff.filter(districtstafftbl__districtTbl_foreignkey_id=district_id).distinct()
        
        data = [{
            'id': s.id,
            'name': f"{s.first_name} {s.last_name}",
            'staff_id': s.staffid,
            'contact': s.contact,
            'department': s.projectTbl_foreignkey.name if s.projectTbl_foreignkey else None
        } for s in staff[:100]]  # Limit to 100 for performance
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })