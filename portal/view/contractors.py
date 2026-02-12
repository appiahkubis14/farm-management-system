import json
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, datetime

from portal.models import (
    PersonnelModel, cocoaDistrict, Community, 
    projectTbl, contractorsTbl, contratorDistrictAssignment,
    Region, ContractorCertificateModel, ContractorCertificateVerificationModel
)

# ============== CONTRACTORS VIEWS ==============

@login_required
def contractors_overview(request):
    """Render the Contractors Overview page"""
    context = {
        'status_choices': [
            ('Active', 'Active'),
            ('Inactive', 'Inactive'),
            ('Under Review', 'Under Review'),
            ('Suspended', 'Suspended'),
            ('Terminated', 'Terminated')
        ],
        'service_types': [
            ('Farm Establishment', 'Farm Establishment'),
            ('Farm Maintenance', 'Farm Maintenance'),
            ('Treatment Services', 'Treatment Services'),
            ('Irrigation Installation', 'Irrigation Installation'),
            ('Equipment Supply', 'Equipment Supply'),
            ('Transport Services', 'Transport Services'),
            ('Consultancy', 'Consultancy'),
            ('Other', 'Other')
        ],
        'target_types': [
            ('Small Scale', 'Small Scale (1-10 farms)'),
            ('Medium Scale', 'Medium Scale (11-50 farms)'),
            ('Large Scale', 'Large Scale (51+ farms)'),
            ('District Wide', 'District Wide'),
            ('Regional', 'Regional')
        ],
        'certification_status': [
            ('Pending', 'Pending'),
            ('Verified', 'Verified'),
            ('Expired', 'Expired'),
            ('Revoked', 'Revoked')
        ]
    }
    return render(request, 'portal/personnel/contractors_overview.html', context)

@require_http_methods(["GET"])
def get_contractors_list(request):
    """Get paginated contractors list for DataTable"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Base queryset
        queryset = contractorsTbl.objects.filter(delete_field='no')
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(contractor_name__icontains=search_value) |
                Q(contact_person__icontains=search_value) |
                Q(contact_number__icontains=search_value) |
                Q(interested_services__icontains=search_value) |
                Q(district__name__icontains=search_value)
            )
        
        # Get total counts
        total_records = contractorsTbl.objects.filter(delete_field='no').count()
        filtered_records = queryset.count()
        
        # Apply pagination
        page = (start // length) + 1
        paginator = Paginator(queryset.order_by('-created_date'), length)
        page_obj = paginator.get_page(page)
        
        # Format data
        data = []
        for contractor in page_obj:
            # Get assigned districts
            assigned_districts = contratorDistrictAssignment.objects.filter(
                contractor=contractor,
                delete_field='no'
            ).select_related('district')
            
            districts_list = [a.district.name for a in assigned_districts if a.district]
            districts_display = ', '.join(districts_list[:3])
            if len(districts_list) > 3:
                districts_display += f' (+{len(districts_list) - 3} more)'
            
            # Get certificate count
            cert_count = ContractorCertificateModel.objects.filter(
                contractor=contractor,
                delete_field='no'
            ).count()
            
            # Get active certificates
            active_certificates = ContractorCertificateModel.objects.filter(
                contractor=contractor,
                delete_field='no',
                status='Verified'
            ).count()
            
            data.append({
                'id': contractor.id,
                'contractor_name': contractor.contractor_name,
                'contact_person': contractor.contact_person,
                'address': contractor.address,
                'contact_number': contractor.contact_number,
                'interested_services': contractor.interested_services,
                'target': contractor.target,
                'primary_district': contractor.district.name if contractor.district else 'N/A',
                'assigned_districts': districts_display,
                'certificate_count': cert_count,
                'active_certificates': active_certificates,
                'created_date': contractor.created_date.strftime('%Y-%m-%d') if contractor.created_date else '',
                'status': 'Active'  # You can add a status field to the model
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
        print(f"Error in get_contractors_list: {str(e)}")
        return JsonResponse({
            'draw': request.GET.get('draw', 1),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def get_contractor_detail(request, contractor_id):
    """Get single contractor details"""
    try:
        contractor = contractorsTbl.objects.get(id=contractor_id, delete_field='no')
        
        # Get assigned districts
        assigned_districts = contratorDistrictAssignment.objects.filter(
            contractor=contractor,
            delete_field='no'
        ).select_related('district', 'projectTbl_foreignkey')
        
        districts_data = []
        for assignment in assigned_districts:
            districts_data.append({
                'id': assignment.id,
                'district_id': assignment.district.id if assignment.district else None,
                'district_name': assignment.district.name if assignment.district else '',
                'project_id': assignment.projectTbl_foreignkey.id if assignment.projectTbl_foreignkey else None,
                'project_name': assignment.projectTbl_foreignkey.name if assignment.projectTbl_foreignkey else '',
                'assigned_date': assignment.created_date.strftime('%Y-%m-%d') if assignment.created_date else ''
            })
        
        # Get certificates
        certificates = ContractorCertificateModel.objects.filter(
            contractor=contractor,
            delete_field='no'
        ).order_by('-start_date')
        
        certificates_data = []
        for cert in certificates:
            # Get verifications
            verifications = ContractorCertificateVerificationModel.objects.filter(
                certificate=cert,
                delete_field='no'
            )
            
            is_verified = verifications.filter(is_verified=True).exists()
            verified_by = None
            verification_date = None
            
            if is_verified:
                latest_verification = verifications.filter(is_verified=True).first()
                if latest_verification:
                    verified_by = str(latest_verification.verified_by) if latest_verification.verified_by else 'N/A'
                    verification_date = latest_verification.verification_date.strftime('%Y-%m-%d') if latest_verification.verification_date else ''
            
            certificates_data.append({
                'id': cert.id,
                'work_type': cert.work_type,
                'start_date': cert.start_date.strftime('%Y-%m-%d') if cert.start_date else '',
                'end_date': cert.end_date.strftime('%Y-%m-%d') if cert.end_date else '',
                'status': cert.status,
                'remarks': cert.remarks or '',
                'is_verified': is_verified,
                'verified_by': verified_by,
                'verification_date': verification_date,
                # 'uid': cert.uid or ''
            })
        
        data = {
            'id': contractor.id,
            'contractor_name': contractor.contractor_name,
            'contact_person': contractor.contact_person,
            'address': contractor.address,
            'contact_number': contractor.contact_number,
            'interested_services': contractor.interested_services,
            'target': contractor.target,
            'district_id': contractor.district.id if contractor.district else '',
            'district_name': contractor.district.name if contractor.district else '',
            'assigned_districts': districts_data,
            'certificates': certificates_data,
            'certificate_count': len(certificates_data),
            'created_date': contractor.created_date.strftime('%Y-%m-%d %H:%M:%S') if contractor.created_date else '',
            # 'uid': contractor.uid or ''
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except contractorsTbl.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Contractor not found'
        }, status=404)
    except Exception as e:
        print(f"Error in get_contractor_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_contractor(request):
    """Create a new contractor"""
    try:
        data = json.loads(request.body)
        
        # Generate UID if not provided
        uid = data.get('uid', str(uuid.uuid4()))
        
        # Get primary district
        district = None
        if data.get('district_id'):
            try:
                district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        
        # Create contractor
        contractor = contractorsTbl.objects.create(
            contractor_name=data.get('contractor_name'),
            contact_person=data.get('contact_person'),
            address=data.get('address'),
            contact_number=data.get('contact_number'),
            interested_services=data.get('interested_services'),
            target=data.get('target'),
            district=district,
            # uid=uid
        )
        
        # Assign additional districts if provided
        if data.get('assigned_districts') and isinstance(data['assigned_districts'], list):
            for district_id in data['assigned_districts']:
                try:
                    dist = cocoaDistrict.objects.get(id=district_id)
                    project = None
                    if data.get('project_id'):
                        try:
                            project = projectTbl.objects.get(id=data['project_id'])
                        except projectTbl.DoesNotExist:
                            pass
                    
                    contratorDistrictAssignment.objects.create(
                        contractor=contractor,
                        district=dist,
                        projectTbl_foreignkey=project,
                        uid=str(uuid.uuid4())
                    )
                except cocoaDistrict.DoesNotExist:
                    continue
        
        return JsonResponse({
            'success': True,
            'message': 'Contractor created successfully',
            'data': {
                'id': contractor.id,
                'contractor_name': contractor.contractor_name
            }
        })
        
    except Exception as e:
        print(f"Error creating contractor: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error creating contractor: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_contractor(request, contractor_id):
    """Update an existing contractor"""
    try:
        contractor = contractorsTbl.objects.get(id=contractor_id, delete_field='no')
        data = json.loads(request.body)
        
        # Update primary district
        if 'district_id' in data:
            try:
                contractor.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                contractor.district = None
        
        # Update fields
        fields_to_update = [
            'contractor_name', 'contact_person', 'address',
            'contact_number', 'interested_services', 'target'
        ]
        
        for field in fields_to_update:
            if field in data:
                setattr(contractor, field, data[field])
        
        contractor.save()
        
        # Update assigned districts if provided
        if data.get('assigned_districts') and isinstance(data['assigned_districts'], list):
            # Remove existing assignments
            contratorDistrictAssignment.objects.filter(
                contractor=contractor,
                delete_field='no'
            ).update(delete_field='yes')
            
            # Create new assignments
            for district_id in data['assigned_districts']:
                try:
                    dist = cocoaDistrict.objects.get(id=district_id)
                    project = None
                    if data.get('project_id'):
                        try:
                            project = projectTbl.objects.get(id=data['project_id'])
                        except projectTbl.DoesNotExist:
                            pass
                    
                    contratorDistrictAssignment.objects.create(
                        contractor=contractor,
                        district=dist,
                        projectTbl_foreignkey=project,
                        uid=str(uuid.uuid4())
                    )
                except cocoaDistrict.DoesNotExist:
                    continue
        
        return JsonResponse({
            'success': True,
            'message': 'Contractor updated successfully',
            'data': {
                'id': contractor.id,
                'contractor_name': contractor.contractor_name
            }
        })
        
    except contractorsTbl.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Contractor not found'
        }, status=404)
    except Exception as e:
        print(f"Error updating contractor: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error updating contractor: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def delete_contractor(request, contractor_id):
    """Soft delete a contractor"""
    try:
        contractor = contractorsTbl.objects.get(id=contractor_id, delete_field='no')
        
        data = json.loads(request.body)
        reason = data.get('reason', 'No reason provided')
        
        # Soft delete contractor
        contractor.delete_field = 'yes'
        contractor.reason4expunge = reason
        contractor.save()
        
        # Soft delete all district assignments
        contratorDistrictAssignment.objects.filter(
            contractor=contractor,
            delete_field='no'
        ).update(delete_field='yes')
        
        # Soft delete all certificates
        ContractorCertificateModel.objects.filter(
            contractor=contractor,
            delete_field='no'
        ).update(delete_field='yes')
        
        return JsonResponse({
            'success': True,
            'message': 'Contractor deleted successfully'
        })
        
    except contractorsTbl.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Contractor not found'
        }, status=404)
    except Exception as e:
        print(f"Error deleting contractor: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error deleting contractor: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def assign_contractor_district(request, contractor_id):
    """Assign a district to a contractor"""
    try:
        contractor = contractorsTbl.objects.get(id=contractor_id, delete_field='no')
        data = json.loads(request.body)
        
        district_id = data.get('district_id')
        project_id = data.get('project_id')
        
        if not district_id:
            return JsonResponse({
                'success': False,
                'message': 'District ID is required'
            }, status=400)
        
        district = cocoaDistrict.objects.get(id=district_id)
        
        project = None
        if project_id:
            try:
                project = projectTbl.objects.get(id=project_id)
            except projectTbl.DoesNotExist:
                pass
        
        # Check if assignment already exists
        existing = contratorDistrictAssignment.objects.filter(
            contractor=contractor,
            district=district,
            delete_field='no'
        ).first()
        
        if existing:
            return JsonResponse({
                'success': False,
                'message': 'Contractor already assigned to this district'
            }, status=400)
        
        # Create assignment
        assignment = contratorDistrictAssignment.objects.create(
            contractor=contractor,
            district=district,
            projectTbl_foreignkey=project,
            uid=str(uuid.uuid4())
        )
        
        return JsonResponse({
            'success': True,
            'message': 'District assigned successfully',
            'data': {
                'id': assignment.id,
                'district_id': district.id,
                'district_name': district.name,
                'assigned_date': assignment.created_date.strftime('%Y-%m-%d')
            }
        })
        
    except contractorsTbl.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Contractor not found'
        }, status=404)
    except cocoaDistrict.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'District not found'
        }, status=404)
    except Exception as e:
        print(f"Error assigning district: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error assigning district: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_contractor_districts(request, contractor_id):
    """Get all districts assigned to a contractor"""
    try:
        contractor = contractorsTbl.objects.get(id=contractor_id, delete_field='no')
        
        assignments = contratorDistrictAssignment.objects.filter(
            contractor=contractor,
            delete_field='no'
        ).select_related('district', 'projectTbl_foreignkey')
        
        data = []
        for assignment in assignments:
            data.append({
                'id': assignment.id,
                'district_id': assignment.district.id if assignment.district else None,
                'district_name': assignment.district.name if assignment.district else '',
                'project_id': assignment.projectTbl_foreignkey.id if assignment.projectTbl_foreignkey else None,
                'project_name': assignment.projectTbl_foreignkey.name if assignment.projectTbl_foreignkey else '',
                'assigned_date': assignment.created_date.strftime('%Y-%m-%d') if assignment.created_date else ''
            })
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except contractorsTbl.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Contractor not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)