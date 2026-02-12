from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import json
from portal.models import (
    ActivityReportingModel, Activities, staffTbl, 
    PersonnelModel, FarmdetailsTbl, Community, 
    cocoaDistrict, projectTbl
)

# ============== ACTIVITY REPORTING VIEWS ==============

@login_required
def activity_reporting(request):
    """Render the Activity Reporting page"""
    context = {
        'status_choices': [
            (0, 'Draft'),
            (1, 'Submitted'),
            (2, 'Approved'),
            (3, 'Rejected'),
        ],
        'group_work_choices': [
            ('No', 'No'),
            ('Yes', 'Yes'),
        ]
    }
    return render(request, 'portal/activity_reporting/activity_reporting.html', context)

@csrf_exempt
@require_http_methods(["GET"])
def activity_report_list_api(request):
    """API endpoint for DataTables to get activity reports"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Base queryset
        queryset = ActivityReportingModel.objects.select_related(
            'agent', 'main_activity', 'activity', 'farm', 
            'community', 'projectTbl_foreignkey', 'district'
        ).prefetch_related('ras').all()
        
        # Filter by user role
        user = request.user
        if not user.is_superuser:
            try:
                staff = staffTbl.objects.get(user=user)
                if user.groups.filter(name='Project Officer').exists():
                    queryset = queryset.filter(agent=staff)
                elif user.groups.filter(name='Rehab Assistant').exists():
                    personnel = PersonnelModel.objects.filter(
                        primary_phone_number=user.username
                    ).first()
                    if personnel:
                        queryset = queryset.filter(ras=personnel)
            except staffTbl.DoesNotExist:
                pass
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(agent__first_name__icontains=search_value) |
                Q(agent__last_name__icontains=search_value) |
                Q(farm_ref_number__icontains=search_value) |
                Q(main_activity__main_activity__icontains=search_value) |
                Q(activity__sub_activity__icontains=search_value) |
                Q(community__name__icontains=search_value)
            )
        
        # Apply filters from request
        status_filter = request.GET.get('status')
        if status_filter and status_filter.strip():
            queryset = queryset.filter(status=status_filter)
        
        date_filter = request.GET.get('date')
        if date_filter and date_filter.strip():
            queryset = queryset.filter(reporting_date=date_filter)
        
        po_filter = request.GET.get('po_id')
        if po_filter and po_filter.strip():
            queryset = queryset.filter(agent_id=po_filter)
        
        # Get total count
        total_records = queryset.count()
        
        # Apply pagination
        reports = queryset.order_by('-reporting_date')[start:start + length]
        
        # Prepare data for DataTables
        data = []
        for report in reports:
            # Get assigned RAs
            ras_list = []
            for ra in report.ras.all():
                ras_list.append({
                    'id': ra.id,
                    'name': f"{ra.first_name} {ra.surname}" if hasattr(ra, 'first_name') else str(ra),
                    'contact': getattr(ra, 'primary_phone_number', ''),
                    'momo_number': getattr(ra, 'momo_number', '')
                })
            
            data.append({
                'id': report.id,
                'uid': report.uid or '',
                'reporting_date': report.reporting_date.strftime('%Y-%m-%d') if report.reporting_date else '',
                'completion_date': report.completion_date.strftime('%Y-%m-%d') if report.completion_date else '',
                'agent_id': report.agent.id if report.agent else '',
                'agent_name': f"{report.agent.first_name} {report.agent.last_name}" if report.agent else 'N/A',
                'agent_contact': report.agent.contact if report.agent else '',
                'main_activity': report.main_activity.main_activity if report.main_activity else 'N/A',
                'main_activity_id': report.main_activity.id if report.main_activity else '',
                'sub_activity': report.activity.sub_activity if report.activity else 'N/A',
                'sub_activity_id': report.activity.id if report.activity else '',
                'no_rehab_assistants': report.no_rehab_assistants or 0,
                'area_covered_ha': float(report.area_covered_ha) if report.area_covered_ha else 0,
                'farm_ref_number': report.farm_ref_number or '',
                'farm_id': report.farm.id if report.farm else '',
                'farm_size_ha': float(report.farm_size_ha) if report.farm_size_ha else 0,
                'community': report.community.name if report.community else 'N/A',
                'community_id': report.community.id if report.community else '',
                'sector': report.sector or '',
                'group_work': report.group_work or 'No',
                'number_of_people_in_group': report.number_of_people_in_group or 0,
                'remark': report.remark or '',
                'status': report.status,
                'status_display': get_status_display(report.status),
                'project': report.projectTbl_foreignkey.name if report.projectTbl_foreignkey else 'N/A',
                'project_id': report.projectTbl_foreignkey.id if report.projectTbl_foreignkey else '',
                'district': report.district.name if report.district else 'N/A',
                'district_id': report.district.id if report.district else '',
                'ras': ras_list,
                'ras_count': len(ras_list),
                'created_date': report.created_date.strftime('%Y-%m-%d %H:%M:%S') if report.created_date else '',
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
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def activity_report_create(request):
    """Create a new activity report"""
    try:
        data = json.loads(request.body)
        
        # Get related objects
        agent = staffTbl.objects.get(id=data.get('agent_id')) if data.get('agent_id') else None
        main_activity = Activities.objects.get(id=data.get('main_activity_id')) if data.get('main_activity_id') else None
        sub_activity = Activities.objects.get(id=data.get('sub_activity_id')) if data.get('sub_activity_id') else None
        farm = FarmdetailsTbl.objects.filter(farm_reference=data.get('farm_ref_number')).first() if data.get('farm_ref_number') else None
        community = Community.objects.get(id=data.get('community_id')) if data.get('community_id') else None
        district = cocoaDistrict.objects.get(id=data.get('district_id')) if data.get('district_id') else None
        project = projectTbl.objects.get(id=data.get('project_id')) if data.get('project_id') else None
        
        # Generate UID if not provided
        uid = data.get('uid')
        if not uid:
            import uuid
            uid = f"AR-{uuid.uuid4().hex[:8].upper()}"
        
        # Create the activity report
        report = ActivityReportingModel.objects.create(
            uid=uid,
            agent=agent,
            completion_date=data.get('completion_date') or timezone.now().date(),
            reporting_date=data.get('reporting_date') or timezone.now().date(),
            main_activity=main_activity,
            activity=sub_activity,
            no_rehab_assistants=data.get('no_rehab_assistants', 0),
            area_covered_ha=data.get('area_covered_ha', 0),
            remark=data.get('remark', ''),
            status=data.get('status', 0),
            farm=farm,
            farm_ref_number=data.get('farm_ref_number', ''),
            farm_size_ha=data.get('farm_size_ha', 0),
            community=community,
            number_of_people_in_group=data.get('number_of_people_in_group', 0),
            group_work=data.get('group_work', 'No'),
            sector=data.get('sector'),
            projectTbl_foreignkey=project,
            district=district
        )
        
        # Add RAs if provided
        ra_ids = data.get('ra_ids', [])
        if ra_ids:
            ras = PersonnelModel.objects.filter(id__in=ra_ids)
            report.ras.set(ras)
            report.no_rehab_assistants = len(ra_ids)
            report.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Activity report created successfully',
            'data': {'id': report.id, 'uid': report.uid}
        })
        
    except staffTbl.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Project Officer not found'}, status=404)
    except Activities.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def activity_report_detail(request, report_id):
    """Get details of a specific activity report"""
    try:
        report = ActivityReportingModel.objects.select_related(
            'agent', 'main_activity', 'activity', 'farm', 
            'community', 'projectTbl_foreignkey', 'district'
        ).prefetch_related('ras').get(id=report_id)
        
        # Get RAs assigned to this report
        ras = []
        for ra in report.ras.all():
            ras.append({
                'id': ra.id,
                'name': f"{ra.first_name} {ra.surname}" if hasattr(ra, 'first_name') else str(ra),
                'contact': getattr(ra, 'primary_phone_number', ''),
                'momo_number': getattr(ra, 'momo_number', ''),
                'id_number': getattr(ra, 'id_number', '')
            })
        
        data = {
            'id': report.id,
            'uid': report.uid or '',
            'reporting_date': report.reporting_date.strftime('%Y-%m-%d') if report.reporting_date else '',
            'completion_date': report.completion_date.strftime('%Y-%m-%d') if report.completion_date else '',
            'agent_id': report.agent.id if report.agent else '',
            'agent_name': f"{report.agent.first_name} {report.agent.last_name}" if report.agent else 'N/A',
            'agent_contact': report.agent.contact if report.agent else '',
            'main_activity_id': report.main_activity.id if report.main_activity else '',
            'main_activity': report.main_activity.main_activity if report.main_activity else 'N/A',
            'sub_activity_id': report.activity.id if report.activity else '',
            'sub_activity': report.activity.sub_activity if report.activity else 'N/A',
            'no_rehab_assistants': report.no_rehab_assistants or 0,
            'area_covered_ha': float(report.area_covered_ha) if report.area_covered_ha else 0,
            'farm_ref_number': report.farm_ref_number or '',
            'farm_id': report.farm.id if report.farm else '',
            'farm_size_ha': float(report.farm_size_ha) if report.farm_size_ha else 0,
            'community': report.community.name if report.community else '',
            'community_id': report.community.id if report.community else '',
            'sector': report.sector or '',
            'group_work': report.group_work or 'No',
            'number_of_people_in_group': report.number_of_people_in_group or 0,
            'remark': report.remark or '',
            'status': report.status,
            'status_display': get_status_display(report.status),
            'project_id': report.projectTbl_foreignkey.id if report.projectTbl_foreignkey else '',
            'project': report.projectTbl_foreignkey.name if report.projectTbl_foreignkey else 'N/A',
            'district_id': report.district.id if report.district else '',
            'district': report.district.name if report.district else 'N/A',
            'ras': ras,
            'ras_ids': [ra['id'] for ra in ras],
            'created_date': report.created_date.strftime('%Y-%m-%d %H:%M:%S') if report.created_date else '',
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except ActivityReportingModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def activity_report_update(request, report_id):
    """Update an existing activity report"""
    try:
        report = ActivityReportingModel.objects.get(id=report_id)
        data = json.loads(request.body)
        
        # Only allow updates if status is Draft (0)
        if report.status != 0 and not request.user.is_superuser:
            return JsonResponse({
                'success': False, 
                'message': 'Cannot update report that has been submitted or approved'
            }, status=400)
        
        # Update fields
        if 'reporting_date' in data:
            report.reporting_date = data['reporting_date']
        if 'completion_date' in data:
            report.completion_date = data['completion_date']
        if 'agent_id' in data:
            report.agent = staffTbl.objects.get(id=data['agent_id'])
        if 'main_activity_id' in data:
            report.main_activity = Activities.objects.get(id=data['main_activity_id'])
        if 'sub_activity_id' in data:
            report.activity = Activities.objects.get(id=data['sub_activity_id'])
        if 'no_rehab_assistants' in data:
            report.no_rehab_assistants = data['no_rehab_assistants']
        if 'area_covered_ha' in data:
            report.area_covered_ha = data['area_covered_ha']
        if 'farm_ref_number' in data:
            report.farm_ref_number = data['farm_ref_number']
            report.farm = FarmdetailsTbl.objects.filter(farm_reference=data['farm_ref_number']).first()
        if 'farm_size_ha' in data:
            report.farm_size_ha = data['farm_size_ha']
        if 'community_id' in data:
            report.community = Community.objects.get(id=data['community_id'])
        if 'sector' in data:
            report.sector = data['sector']
        if 'group_work' in data:
            report.group_work = data['group_work']
        if 'number_of_people_in_group' in data:
            report.number_of_people_in_group = data['number_of_people_in_group']
        if 'remark' in data:
            report.remark = data['remark']
        if 'district_id' in data:
            report.district = cocoaDistrict.objects.get(id=data['district_id'])
        if 'project_id' in data:
            report.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
        if 'status' in data:
            report.status = data['status']
        
        # Update RAs
        if 'ra_ids' in data:
            ras = PersonnelModel.objects.filter(id__in=data['ra_ids'])
            report.ras.set(ras)
            report.no_rehab_assistants = len(data['ra_ids'])
        
        report.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Activity report updated successfully'
        })
        
    except ActivityReportingModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def activity_report_delete(request, report_id):
    """Delete an activity report (soft delete)"""
    try:
        report = ActivityReportingModel.objects.get(id=report_id)
        data = json.loads(request.body)
        
        # Only allow delete if status is Draft (0)
        if report.status != 0 and not request.user.is_superuser:
            return JsonResponse({
                'success': False, 
                'message': 'Cannot delete report that has been submitted or approved'
            }, status=400)
        
        # Soft delete
        report.delete_field = 'yes'
        report.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Activity report deleted successfully'
        })
        
    except ActivityReportingModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def activity_report_submit(request, report_id):
    """Submit an activity report for approval"""
    try:
        report = ActivityReportingModel.objects.get(id=report_id)
        
        # Update status to Submitted (1)
        report.status = 1
        report.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Activity report submitted successfully'
        })
        
    except ActivityReportingModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def activity_report_approve(request, report_id):
    """Approve an activity report"""
    try:
        report = ActivityReportingModel.objects.get(id=report_id)
        
        # Update status to Approved (2)
        report.status = 2
        report.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Activity report approved successfully'
        })
        
    except ActivityReportingModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def activity_report_reject(request, report_id):
    """Reject an activity report"""
    try:
        report = ActivityReportingModel.objects.get(id=report_id)
        data = json.loads(request.body)
        
        # Update status to Rejected (3) and add rejection reason
        report.status = 3
        report.remark = f"REJECTED: {data.get('reason', 'No reason provided')}\n{report.remark or ''}"
        report.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Activity report rejected successfully'
        })
        
    except ActivityReportingModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# Helper function for status display
def get_status_display(status):
    status_map = {
        0: 'Draft',
        1: 'Submitted',
        2: 'Approved',
        3: 'Rejected'
    }
    return status_map.get(status, 'Unknown')