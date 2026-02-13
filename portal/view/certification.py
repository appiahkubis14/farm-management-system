# views.py
import json
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from portal.models import (
    ContractorCertificateModel, ContractorCertificateVerificationModel,
    contractorsTbl, projectTbl, cocoaDistrict, staffTbl
)
import logging

logger = logging.getLogger(__name__)

# ============== WORK CERTIFICATES PAGE ==============

@login_required
def work_certificates_page(request):
    """Render the Work Certificates management page"""
    context = {
        'work_types': [
            'Rehabilitation', 'Maintenance', 'Establishment', 
            'Treatment', 'Pruning', 'Spraying', 'Harvesting',
            'Post-Harvest', 'Nursery', 'Other'
        ],
        'status_choices': [
            'Pending', 'Approved', 'Rejected', 'In Review', 'Completed'
        ]
    }
    return render(request, 'portal/certification/work_certificates.html', context)


# ============== WORK CERTIFICATE API VIEWS ==============

@login_required
@require_http_methods(["GET"])
def work_certificate_list(request):
    """Get paginated list of work certificates"""
    try:
        # Get query parameters
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Base queryset
        queryset = ContractorCertificateModel.objects.filter(delete_field='no').select_related(
            'contractor', 'projectTbl_foreignkey', 'district'
        )
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(contractor__contractor_name__icontains=search_value) |
                Q(work_type__icontains=search_value) |
                Q(status__icontains=search_value) |
                Q(remarks__icontains=search_value)
            )
        
        # Get total counts
        total_records = queryset.count()
        
        # Apply pagination
        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        page_obj = paginator.get_page(page_number)
        
        # Prepare data
        data = []
        for cert in page_obj:
            # Get verification info
            verifications = ContractorCertificateVerificationModel.objects.filter(
                certificate=cert, delete_field='no'
            ).select_related('verified_by').order_by('-verification_date')
            
            is_verified = verifications.filter(is_verified=True).exists()
            latest_verification = verifications.first()
            
            data.append({
                'id': cert.id,
                'uid': cert.uid,
                'contractor_id': cert.contractor.id if cert.contractor else None,
                'contractor_name': cert.contractor.contractor_name if cert.contractor else 'N/A',
                'work_type': cert.work_type,
                'start_date': cert.start_date.strftime('%Y-%m-%d') if cert.start_date else None,
                'end_date': cert.end_date.strftime('%Y-%m-%d') if cert.end_date else None,
                'status': cert.status,
                'remarks': cert.remarks or '',
                'project_id': cert.projectTbl_foreignkey.id if cert.projectTbl_foreignkey else None,
                'project_name': cert.projectTbl_foreignkey.name if cert.projectTbl_foreignkey else 'N/A',
                'district_id': cert.district.id if cert.district else None,
                'district_name': cert.district.name if cert.district else 'N/A',
                'is_verified': is_verified,
                'verified_by': latest_verification.verified_by.get_full_name() if latest_verification and latest_verification.verified_by else None,
                'verification_date': latest_verification.verification_date.strftime('%Y-%m-%d') if latest_verification else None,
                'verification_comments': latest_verification.comments if latest_verification else None,
                'created_date': cert.created_date.strftime('%Y-%m-%d %H:%M:%S') if cert.created_date else None,
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
        logger.error(f"Error in work_certificate_list: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e),
            'data': []
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def work_certificate_create(request):
    """Create a new work certificate"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['work_type', 'start_date', 'end_date']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required'
                })
        
        # Create certificate
        certificate = ContractorCertificateModel()
        certificate.uid = str(uuid.uuid4())
        certificate.work_type = data.get('work_type')
        certificate.start_date = data.get('start_date')
        certificate.end_date = data.get('end_date')
        certificate.status = data.get('status', 'Pending')
        certificate.remarks = data.get('remarks', '')
        
        # Set foreign keys
        if data.get('contractor_id'):
            try:
                certificate.contractor = contractorsTbl.objects.get(id=data['contractor_id'])
            except contractorsTbl.DoesNotExist:
                pass
        
        if data.get('project_id'):
            try:
                certificate.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                pass
        
        if data.get('district_id'):
            try:
                certificate.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        
        certificate.save()
        
        # Create initial verification record if needed
        if data.get('is_verified') and request.user.is_authenticated:
            try:
                staff = staffTbl.objects.get(user=request.user)
                verification = ContractorCertificateVerificationModel()
                verification.uid = str(uuid.uuid4())
                verification.certificate = certificate
                verification.verified_by = staff
                verification.verification_date = timezone.now().date()
                verification.is_verified = data.get('is_verified') == 'true' or data.get('is_verified') == True
                verification.comments = data.get('verification_comments', '')
                verification.projectTbl_foreignkey = certificate.projectTbl_foreignkey
                verification.district = certificate.district
                verification.save()
            except staffTbl.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'message': 'Work certificate created successfully',
            'data': {'id': certificate.id}
        })
        
    except Exception as e:
        logger.error(f"Error in work_certificate_create: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["GET"])
def work_certificate_detail(request, pk):
    """Get work certificate details"""
    try:
        certificate = ContractorCertificateModel.objects.select_related(
            'contractor', 'projectTbl_foreignkey', 'district'
        ).get(pk=pk, delete_field='no')
        
        # Get verification history
        verifications = ContractorCertificateVerificationModel.objects.filter(
            certificate=certificate, delete_field='no'
        ).select_related('verified_by').order_by('-verification_date')
        
        verification_history = []
        for v in verifications:
            verification_history.append({
                'id': v.id,
                'verified_by': v.verified_by.get_full_name() if v.verified_by else None,
                'verification_date': v.verification_date.strftime('%Y-%m-%d'),
                'is_verified': v.is_verified,
                'comments': v.comments,
                'created_date': v.created_date.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        data = {
            'id': certificate.id,
            'uid': certificate.uid,
            'contractor_id': certificate.contractor.id if certificate.contractor else None,
            'contractor_name': certificate.contractor.contractor_name if certificate.contractor else 'N/A',
            'contractor_contact': certificate.contractor.contact_number if certificate.contractor else None,
            'contractor_address': certificate.contractor.address if certificate.contractor else None,
            'work_type': certificate.work_type,
            'start_date': certificate.start_date.strftime('%Y-%m-%d') if certificate.start_date else None,
            'end_date': certificate.end_date.strftime('%Y-%m-%d') if certificate.end_date else None,
            'status': certificate.status,
            'remarks': certificate.remarks or '',
            'project_id': certificate.projectTbl_foreignkey.id if certificate.projectTbl_foreignkey else None,
            'project_name': certificate.projectTbl_foreignkey.name if certificate.projectTbl_foreignkey else 'N/A',
            'district_id': certificate.district.id if certificate.district else None,
            'district_name': certificate.district.name if certificate.district else 'N/A',
            'created_date': certificate.created_date.strftime('%Y-%m-%d %H:%M:%S'),
            'verification_history': verification_history
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except ContractorCertificateModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Work certificate not found'
        })
    except Exception as e:
        logger.error(f"Error in work_certificate_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def work_certificate_update(request, pk):
    """Update work certificate"""
    try:
        certificate = ContractorCertificateModel.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body)
        
        # Update fields
        if data.get('work_type'):
            certificate.work_type = data['work_type']
        if data.get('start_date'):
            certificate.start_date = data['start_date']
        if data.get('end_date'):
            certificate.end_date = data['end_date']
        if data.get('status'):
            certificate.status = data['status']
        if data.get('remarks') is not None:
            certificate.remarks = data['remarks']
        
        # Update foreign keys
        if data.get('contractor_id'):
            try:
                certificate.contractor = contractorsTbl.objects.get(id=data['contractor_id'])
            except contractorsTbl.DoesNotExist:
                pass
        elif 'contractor_id' in data and data['contractor_id'] is None:
            certificate.contractor = None
        
        if data.get('project_id'):
            try:
                certificate.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                pass
        elif 'project_id' in data and data['project_id'] is None:
            certificate.projectTbl_foreignkey = None
        
        if data.get('district_id'):
            try:
                certificate.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        elif 'district_id' in data and data['district_id'] is None:
            certificate.district = None
        
        certificate.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Work certificate updated successfully'
        })
        
    except ContractorCertificateModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Work certificate not found'
        })
    except Exception as e:
        logger.error(f"Error in work_certificate_update: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def work_certificate_delete(request, pk):
    """Soft delete work certificate"""
    try:
        certificate = ContractorCertificateModel.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', 'No reason provided')
        
        # Soft delete
        certificate.delete_field = 'yes'
        certificate.save()
        
        # Log deletion (optional - could create a deletion log model)
        
        return JsonResponse({
            'success': True,
            'message': 'Work certificate deleted successfully'
        })
        
    except ContractorCertificateModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Work certificate not found'
        })
    except Exception as e:
        logger.error(f"Error in work_certificate_delete: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def work_certificate_verify(request, pk):
    """Verify a work certificate"""
    try:
        certificate = ContractorCertificateModel.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body)
        
        # Get staff from user
        try:
            staff = staffTbl.objects.get(user=request.user)
        except staffTbl.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Staff record not found for current user'
            })
        
        # Create verification record
        verification = ContractorCertificateVerificationModel()
        verification.uid = str(uuid.uuid4())
        verification.certificate = certificate
        verification.verified_by = staff
        verification.verification_date = data.get('verification_date', timezone.now().date())
        verification.is_verified = data.get('is_verified', True)
        verification.comments = data.get('comments', '')
        verification.projectTbl_foreignkey = certificate.projectTbl_foreignkey
        verification.district = certificate.district
        verification.save()
        
        # Update certificate status if needed
        if verification.is_verified:
            certificate.status = 'Approved'
        else:
            certificate.status = 'Rejected'
        certificate.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Certificate verified successfully'
        })
        
    except ContractorCertificateModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Work certificate not found'
        })
    except Exception as e:
        logger.error(f"Error in work_certificate_verify: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# ============== HELPER API VIEWS ==============

@login_required
def get_contractors(request):
    """Get contractors for dropdown"""
    try:
        contractors = contractorsTbl.objects.filter(delete_field='no').order_by('contractor_name')
        
        search = request.GET.get('search', '')
        if search:
            contractors = contractors.filter(contractor_name__icontains=search)
        
        data = [{
            'id': c.id,
            'name': c.contractor_name,
            'contact_person': c.contact_person,
            'contact_number': c.contact_number,
            'address': c.address,
            'interested_services': c.interested_services
        } for c in contractors]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def get_projects(request):
    """Get projects for dropdown"""
    try:
        projects = projectTbl.objects.filter(delete_field='no').order_by('name')
        
        district_id = request.GET.get('district_id')
        if district_id:
            projects = projects.filter(district_id=district_id)
        
        data = [{
            'id': p.id,
            'name': p.name,
            'district_id': p.district.id if p.district else None
        } for p in projects]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def get_districts(request):
    """Get districts for dropdown"""
    try:
        districts = cocoaDistrict.objects.filter(delete_field='no').order_by('name')
        
        data = [{
            'id': d.id,
            'name': d.name,
            'region_id': d.region.id if d.region else None,
            'region_name': d.region.region if d.region else None
        } for d in districts]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })