import json
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, OuterRef, Subquery
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, datetime, timedelta

from portal.models import (
    PersonnelModel, cocoaDistrict, Community, 
    projectTbl, staffTbl, contractorsTbl, contratorDistrictAssignment,
    Region, ContractorCertificateModel, ContractorCertificateVerificationModel,
    PersonnelAssignmentModel
)

# ============== STAFF ASSIGNMENTS VIEWS ==============

@login_required
def staff_assignments_overview(request):
    """Render the Staff Assignments Overview page"""
    context = {
        'assignment_status': [
            {'value': 0, 'label': 'Pending', 'badge': 'bg-warning'},
            {'value': 1, 'label': 'Submitted', 'badge': 'bg-success'},
            {'value': 2, 'label': 'Approved', 'badge': 'bg-info'},
            {'value': 3, 'label': 'Rejected', 'badge': 'bg-danger'},
            {'value': 4, 'label': 'Completed', 'badge': 'bg-primary'},
            {'value': 5, 'label': 'Revoked', 'badge': 'bg-dark'}
        ],
        'assignment_types': [
            ('RA Assignment', 'Rehab Assistant Assignment'),
            ('PO Supervision', 'Project Officer Supervision'),
            ('District Coverage', 'District Coverage'),
            ('Community Coverage', 'Community Coverage')
        ]
    }
    return render(request, 'portal/personnel/staff_assignments_overview.html', context)

@require_http_methods(["GET"])
def get_assignments_list(request):
    """Get paginated staff assignments list for DataTable"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        status_filter = request.GET.get('status', '')
        po_filter = request.GET.get('po_id', '')
        district_filter = request.GET.get('district_id', '')
        
        # Base queryset
        queryset = PersonnelAssignmentModel.objects.filter(
            delete_field='no'
        ).select_related(
            'po', 'ra', 'district', 'community', 'projectTbl_foreignkey'
        )
        
        # Apply filters
        if status_filter and status_filter != '':
            queryset = queryset.filter(status=status_filter)
        
        if po_filter and po_filter != '':
            queryset = queryset.filter(po_id=po_filter)
        
        if district_filter and district_filter != '':
            queryset = queryset.filter(district_id=district_filter)
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(ra__first_name__icontains=search_value) |
                Q(ra__surname__icontains=search_value) |
                Q(ra__staff_id__icontains=search_value) |
                Q(po__first_name__icontains=search_value) |
                Q(po__last_name__icontains=search_value) |
                Q(po__staffid__icontains=search_value) |
                Q(district__name__icontains=search_value) |
                Q(community__name__icontains=search_value)
            )
        
        # Get total counts
        total_records = PersonnelAssignmentModel.objects.filter(delete_field='no').count()
        filtered_records = queryset.count()
        
        # Apply pagination
        page = (start // length) + 1
        paginator = Paginator(queryset.order_by('-created_date'), length)
        page_obj = paginator.get_page(page)
        
        # Format data
        data = []
        for assignment in page_obj:
            # Get status badge
            status_badge = 'bg-warning'
            status_text = 'Pending'
            if assignment.status == 1:
                status_badge = 'bg-success'
                status_text = 'Submitted'
            elif assignment.status == 2:
                status_badge = 'bg-info'
                status_text = 'Approved'
            elif assignment.status == 3:
                status_badge = 'bg-danger'
                status_text = 'Rejected'
            elif assignment.status == 4:
                status_badge = 'bg-primary'
                status_text = 'Completed'
            elif assignment.status == 5:
                status_badge = 'bg-dark'
                status_text = 'Revoked'
            
            data.append({
                'id': assignment.id,
                'assignment_code': f"ASS-{assignment.id:06d}",
                'ra_id': assignment.ra.id if assignment.ra else None,
                'ra_name': f"{assignment.ra.first_name} {assignment.ra.surname}" if assignment.ra else 'N/A',
                'ra_staff_id': assignment.ra.staff_id if assignment.ra else 'N/A',
                'po_id': assignment.po.id if assignment.po else None,
                'po_name': f"{assignment.po.first_name} {assignment.po.last_name}" if assignment.po else 'N/A',
                'po_staff_id': assignment.po.staffid if assignment.po else 'N/A',
                'district': assignment.district.name if assignment.district else 'N/A',
                'district_id': assignment.district.id if assignment.district else None,
                'community': assignment.community.name if assignment.community else 'N/A',
                'community_id': assignment.community.id if assignment.community else None,
                'project': assignment.projectTbl_foreignkey.name if assignment.projectTbl_foreignkey else 'N/A',
                'project_id': assignment.projectTbl_foreignkey.id if assignment.projectTbl_foreignkey else None,
                'date_assigned': assignment.date_assigned.strftime('%Y-%m-%d') if assignment.date_assigned else '',
                'status': assignment.status,
                'status_text': status_text,
                'status_badge': status_badge,
                'created_date': assignment.created_date.strftime('%Y-%m-%d') if assignment.created_date else '',
                'uid': assignment.uid or ''
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
        print(f"Error in get_assignments_list: {str(e)}")
        return JsonResponse({
            'draw': request.GET.get('draw', 1),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_assignment_detail(request, assignment_id):
    """Get single assignment details"""
    try:
        assignment = PersonnelAssignmentModel.objects.get(
            id=assignment_id, 
            delete_field='no'
        )
        
        # Get status info
        status_badge = 'bg-warning'
        status_text = 'Pending'
        if assignment.status == 1:
            status_badge = 'bg-success'
            status_text = 'Submitted'
        elif assignment.status == 2:
            status_badge = 'bg-info'
            status_text = 'Approved'
        elif assignment.status == 3:
            status_badge = 'bg-danger'
            status_text = 'Rejected'
        elif assignment.status == 4:
            status_badge = 'bg-primary'
            status_text = 'Completed'
        elif assignment.status == 5:
            status_badge = 'bg-dark'
            status_text = 'Revoked'
        
        data = {
            'id': assignment.id,
            'assignment_code': f"ASS-{assignment.id:06d}",
            'ra': {
                'id': assignment.ra.id if assignment.ra else None,
                'name': f"{assignment.ra.first_name} {assignment.ra.surname}" if assignment.ra else 'N/A',
                'staff_id': assignment.ra.staff_id if assignment.ra else 'N/A',
                'phone': assignment.ra.primary_phone_number if assignment.ra else 'N/A',
                'personnel_type': assignment.ra.personnel_type if assignment.ra else 'N/A',
                'district': assignment.ra.district.name if assignment.ra and assignment.ra.district else 'N/A'
            },
            'po': {
                'id': assignment.po.id if assignment.po else None,
                'name': f"{assignment.po.first_name} {assignment.po.last_name}" if assignment.po else 'N/A',
                'staff_id': assignment.po.staffid if assignment.po else 'N/A',
                'phone': assignment.po.contact if assignment.po else 'N/A'
            },
            'district': {
                'id': assignment.district.id if assignment.district else None,
                'name': assignment.district.name if assignment.district else 'N/A',
                'code': assignment.district.district_code if assignment.district else 'N/A'
            },
            'community': {
                'id': assignment.community.id if assignment.community else None,
                'name': assignment.community.name if assignment.community else 'N/A'
            },
            'project': {
                'id': assignment.projectTbl_foreignkey.id if assignment.projectTbl_foreignkey else None,
                'name': assignment.projectTbl_foreignkey.name if assignment.projectTbl_foreignkey else 'N/A'
            },
            'date_assigned': assignment.date_assigned.strftime('%Y-%m-%d') if assignment.date_assigned else '',
            'status': assignment.status,
            'status_text': status_text,
            'status_badge': status_badge,
            'created_date': assignment.created_date.strftime('%Y-%m-%d %H:%M:%S') if assignment.created_date else '',
            'updated_date': assignment.updated_date.strftime('%Y-%m-%d %H:%M:%S') if hasattr(assignment, 'updated_date') and assignment.updated_date else '',
            # 'uid': assignment.uid or ''
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except PersonnelAssignmentModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Assignment not found'
        }, status=404)
    except Exception as e:
        print(f"Error in get_assignment_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_assignment(request):
    """Create a new staff assignment"""
    try:
        data = json.loads(request.body)
        
        # Generate UID if not provided
        uid = data.get('uid', str(uuid.uuid4()))
        
        # Get related objects
        po = None
        if data.get('po_id'):
            try:
                po = staffTbl.objects.get(id=data['po_id'])
            except staffTbl.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Project Officer not found'
                }, status=400)
        
        ra = None
        if data.get('ra_id'):
            try:
                ra = PersonnelModel.objects.get(id=data['ra_id'])
            except PersonnelModel.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Rehab Assistant not found'
                }, status=400)
        
        district = None
        if data.get('district_id'):
            try:
                district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        
        community = None
        if data.get('community_id'):
            try:
                community = Community.objects.get(id=data['community_id'])
            except Community.DoesNotExist:
                pass
        
        project = None
        if data.get('project_id'):
            try:
                project = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                pass
        
        # Parse date
        date_assigned = None
        if data.get('date_assigned'):
            try:
                date_assigned = datetime.strptime(data['date_assigned'], '%Y-%m-%d').date()
            except:
                date_assigned = timezone.now().date()
        else:
            date_assigned = timezone.now().date()
        
        # Check for existing active assignment
        existing_assignment = PersonnelAssignmentModel.objects.filter(
            ra=ra,
            delete_field='no'
        ).exclude(status__in=[4, 5]).first()
        
        if existing_assignment:
            return JsonResponse({
                'success': False,
                'message': 'This Rehab Assistant already has an active assignment'
            }, status=400)
        
        # Create assignment
        assignment = PersonnelAssignmentModel.objects.create(
            po=po,
            ra=ra,
            district=district,
            community=community,
            projectTbl_foreignkey=project,
            date_assigned=date_assigned,
            status=0,  # Pending
            uid=uid
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Staff assignment created successfully',
            'data': {
                'id': assignment.id,
                'assignment_code': f"ASS-{assignment.id:06d}"
            }
        })
        
    except Exception as e:
        print(f"Error creating assignment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error creating assignment: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_assignment(request, assignment_id):
    """Update an existing staff assignment"""
    try:
        assignment = PersonnelAssignmentModel.objects.get(
            id=assignment_id, 
            delete_field='no'
        )
        
        # Check if assignment can be updated
        if assignment.status not in [0, 3]:  # Only pending or rejected can be updated
            return JsonResponse({
                'success': False,
                'message': 'This assignment cannot be updated in its current status'
            }, status=400)
        
        data = json.loads(request.body)
        
        # Update related objects
        if 'po_id' in data:
            try:
                assignment.po = staffTbl.objects.get(id=data['po_id'])
            except staffTbl.DoesNotExist:
                assignment.po = None
        
        if 'district_id' in data:
            try:
                assignment.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                assignment.district = None
        
        if 'community_id' in data:
            try:
                assignment.community = Community.objects.get(id=data['community_id'])
            except Community.DoesNotExist:
                assignment.community = None
        
        if 'project_id' in data:
            try:
                assignment.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                assignment.projectTbl_foreignkey = None
        
        # Update date
        if 'date_assigned' in data and data['date_assigned']:
            try:
                assignment.date_assigned = datetime.strptime(data['date_assigned'], '%Y-%m-%d').date()
            except:
                pass
        
        assignment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Staff assignment updated successfully',
            'data': {
                'id': assignment.id,
                'assignment_code': f"ASS-{assignment.id:06d}"
            }
        })
        
    except PersonnelAssignmentModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Assignment not found'
        }, status=404)
    except Exception as e:
        print(f"Error updating assignment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error updating assignment: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def delete_assignment(request, assignment_id):
    """Soft delete a staff assignment"""
    try:
        assignment = PersonnelAssignmentModel.objects.get(
            id=assignment_id, 
            delete_field='no'
        )
        
        data = json.loads(request.body)
        reason = data.get('reason', 'No reason provided')
        
        # Soft delete
        assignment.delete_field = 'yes'
        assignment.reason4expunge = reason
        assignment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Staff assignment deleted successfully'
        })
        
    except PersonnelAssignmentModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Assignment not found'
        }, status=404)
    except Exception as e:
        print(f"Error deleting assignment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error deleting assignment: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def submit_assignment(request, assignment_id):
    """Submit an assignment for approval"""
    try:
        assignment = PersonnelAssignmentModel.objects.get(
            id=assignment_id, 
            delete_field='no'
        )
        
        # Only pending assignments can be submitted
        if assignment.status != 0:
            return JsonResponse({
                'success': False,
                'message': 'Only pending assignments can be submitted'
            }, status=400)
        
        assignment.status = 1  # Submitted
        assignment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Assignment submitted successfully'
        })
        
    except PersonnelAssignmentModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Assignment not found'
        }, status=404)
    except Exception as e:
        print(f"Error submitting assignment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error submitting assignment: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def revoke_assignment(request, assignment_id):
    """Revoke an assignment"""
    try:
        assignment = PersonnelAssignmentModel.objects.get(
            id=assignment_id, 
            delete_field='no'
        )
        
        data = json.loads(request.body)
        reason = data.get('reason', 'No reason provided')
        
        assignment.status = 5  # Revoked
        assignment.reason4revoke = reason
        assignment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Assignment revoked successfully'
        })
        
    except PersonnelAssignmentModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Assignment not found'
        }, status=404)
    except Exception as e:
        print(f"Error revoking assignment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error revoking assignment: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_po_list(request):
    """Get list of Project Officers for dropdown"""
    try:
        # Get staff with Project Officer or Project Coordinator role
        pos = staffTbl.objects.filter(
            delete_field='no'
        ).filter(
            Q(staffid__icontains='PO-') | 
            Q(staffid__icontains='PC-') |
            Q(projectTbl_foreignkey__isnull=False)
        ).order_by('first_name')
        
        data = [{
            'id': po.id,
            'name': f"{po.first_name} {po.last_name}",
            'staff_id': po.staffid,
            'contact': po.contact
        } for po in pos]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        print(f"Error in get_po_list: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_ra_list(request):
    """Get list of Rehab Assistants for dropdown"""
    try:
        # Get personnel with Rehab Assistant role and no active assignment
        ras = PersonnelModel.objects.filter(
            delete_field='no',
            personnel_type='Rehab Assistant'
        ).exclude(
            id__in=PersonnelAssignmentModel.objects.filter(
                delete_field='no',
                status__in=[0, 1, 2]  # Exclude those with pending, submitted, or approved assignments
            ).values_list('ra_id', flat=True)
        ).order_by('first_name')
        
        data = [{
            'id': ra.id,
            'name': f"{ra.first_name} {ra.surname}",
            'staff_id': ra.staff_id,
            'phone': ra.primary_phone_number,
            'district': ra.district.name if ra.district else 'N/A'
        } for ra in ras]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        print(f"Error in get_ra_list: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_assignments_by_po(request, po_id):
    """Get all assignments for a specific Project Officer"""
    try:
        assignments = PersonnelAssignmentModel.objects.filter(
            po_id=po_id,
            delete_field='no'
        ).select_related('ra', 'district', 'community')
        
        data = []
        for assignment in assignments:
            data.append({
                'id': assignment.id,
                'assignment_code': f"ASS-{assignment.id:06d}",
                'ra_name': f"{assignment.ra.first_name} {assignment.ra.surname}" if assignment.ra else 'N/A',
                'ra_staff_id': assignment.ra.staff_id if assignment.ra else 'N/A',
                'district': assignment.district.name if assignment.district else 'N/A',
                'community': assignment.community.name if assignment.community else 'N/A',
                'date_assigned': assignment.date_assigned.strftime('%Y-%m-%d') if assignment.date_assigned else '',
                'status': assignment.status
            })
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_assignments_by_ra(request, ra_id):
    """Get all assignments for a specific Rehab Assistant"""
    try:
        assignments = PersonnelAssignmentModel.objects.filter(
            ra_id=ra_id,
            delete_field='no'
        ).select_related('po', 'district', 'community')
        
        data = []
        for assignment in assignments:
            data.append({
                'id': assignment.id,
                'assignment_code': f"ASS-{assignment.id:06d}",
                'po_name': f"{assignment.po.first_name} {assignment.po.last_name}" if assignment.po else 'N/A',
                'po_staff_id': assignment.po.staffid if assignment.po else 'N/A',
                'district': assignment.district.name if assignment.district else 'N/A',
                'community': assignment.community.name if assignment.community else 'N/A',
                'date_assigned': assignment.date_assigned.strftime('%Y-%m-%d') if assignment.date_assigned else '',
                'status': assignment.status
            })
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_assignments_by_district(request, district_id):
    """Get all assignments for a specific district"""
    try:
        assignments = PersonnelAssignmentModel.objects.filter(
            district_id=district_id,
            delete_field='no'
        ).select_related('ra', 'po', 'community')
        
        data = []
        for assignment in assignments:
            data.append({
                'id': assignment.id,
                'assignment_code': f"ASS-{assignment.id:06d}",
                'ra_name': f"{assignment.ra.first_name} {assignment.ra.surname}" if assignment.ra else 'N/A',
                'ra_staff_id': assignment.ra.staff_id if assignment.ra else 'N/A',
                'po_name': f"{assignment.po.first_name} {assignment.po.last_name}" if assignment.po else 'N/A',
                'community': assignment.community.name if assignment.community else 'N/A',
                'date_assigned': assignment.date_assigned.strftime('%Y-%m-%d') if assignment.date_assigned else '',
                'status': assignment.status
            })
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })