import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone
from portal.models import DailyReportingModel, ActivityReportingModel, Activities, staffTbl
from django.contrib.auth.decorators import login_required

@login_required
def activities_overview(request):
    """Render the Activities Overview page"""
    context = {
        'status_choices': [
            (0, 'Pending'),
            (1, 'Submitted'),
            (2, 'Approved'),
            (3, 'Rejected'),
        ]
    }
    return render(request, 'portal/activity_reporting/activities.html', context)

@csrf_exempt
@require_http_methods(["GET"])
def activity_list_api(request):
    """API endpoint for DataTables to get activities"""
    try:
        # Get parameters from DataTables
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Base queryset - you can combine both DailyReportingModel and ActivityReportingModel
        # For Activities Overview, let's show DailyReportingModel entries
        queryset = DailyReportingModel.objects.select_related(
            'agent', 'main_activity', 'activity', 'farm', 'community', 
            'projectTbl_foreignkey', 'district'
        ).all()
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(agent__first_name__icontains=search_value) |
                Q(agent__last_name__icontains=search_value) |
                Q(farm_ref_number__icontains=search_value) |
                Q(main_activity__main_activity__icontains=search_value) |
                Q(activity__sub_activity__icontains=search_value)
            )
        
        # Get total count
        total_records = queryset.count()
        
        # Apply pagination
        activities = queryset.order_by('-reporting_date')[start:start + length]
        
        # Prepare data for DataTables
        data = []
        for activity in activities:
            data.append({
                'id': activity.id,
                'uid': activity.uid or '',
                'reporting_date': activity.reporting_date.strftime('%Y-%m-%d') if activity.reporting_date else '',
                'completion_date': activity.completion_date.strftime('%Y-%m-%d') if activity.completion_date else '',
                'agent_id': activity.agent.id if activity.agent else '',
                'agent_name': f"{activity.agent.first_name} {activity.agent.last_name}" if activity.agent else 'N/A',
                'main_activity': activity.main_activity.main_activity if activity.main_activity else 'N/A',
                'main_activity_id': activity.main_activity.id if activity.main_activity else '',
                'sub_activity': activity.activity.sub_activity if activity.activity else 'N/A',
                'sub_activity_id': activity.activity.id if activity.activity else '',
                'no_rehab_assistants': activity.no_rehab_assistants or 0,
                'area_covered_ha': activity.area_covered_ha or 0,
                'farm_ref_number': activity.farm_ref_number or '',
                'farm_size_ha': activity.farm_size_ha or 0,
                'community': activity.community.name if activity.community else 'N/A',
                'sector': activity.sector or '',
                'group_work': activity.group_work or 'No',
                'number_of_people_in_group': activity.number_of_people_in_group or 0,
                'remark': activity.remark or '',
                'status': activity.status,
                'project': activity.projectTbl_foreignkey.name if activity.projectTbl_foreignkey else 'N/A',
                'district': activity.district.name if activity.district else 'N/A',
                'created_date': activity.created_date.strftime('%Y-%m-%d %H:%M:%S') if activity.created_date else '',
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
def activity_create(request):
    """Create a new activity report"""
    try:
        data = json.loads(request.body)
        
        # Get related objects
        agent = staffTbl.objects.get(id=data.get('agent_id')) if data.get('agent_id') else None
        main_activity = Activities.objects.get(id=data.get('main_activity_id')) if data.get('main_activity_id') else None
        sub_activity = Activities.objects.get(id=data.get('sub_activity_id')) if data.get('sub_activity_id') else None
        
        # Create the activity report
        activity = DailyReportingModel.objects.create(
            uid=data.get('uid', ''),
            agent=agent,
            completion_date=data.get('completion_date') or timezone.now().date(),
            reporting_date=data.get('reporting_date') or timezone.now().date(),
            main_activity=main_activity,
            activity=sub_activity,
            no_rehab_assistants=data.get('no_rehab_assistants', 0),
            area_covered_ha=data.get('area_covered_ha', 0),
            remark=data.get('remark', ''),
            status=data.get('status', 0),
            farm_ref_number=data.get('farm_ref_number', ''),
            farm_size_ha=data.get('farm_size_ha', 0),
            number_of_people_in_group=data.get('number_of_people_in_group', 0),
            group_work=data.get('group_work', 'No'),
            sector=data.get('sector'),
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Activity report created successfully',
            'data': {'id': activity.id}
        })
        
    except staffTbl.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Agent not found'}, status=404)
    except Activities.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def activity_detail(request, activity_id):
    """Get details of a specific activity report"""
    try:
        activity = DailyReportingModel.objects.select_related(
            'agent', 'main_activity', 'activity', 'farm', 'community', 
            'projectTbl_foreignkey', 'district'
        ).get(id=activity_id)
        
        # Get RAs assigned to this activity
        ras = []
        for ra in activity.ras.all():
            ras.append({
                'id': ra.id,
                'name': f"{ra.first_name} {ra.surname}" if hasattr(ra, 'first_name') else str(ra)
            })
        
        data = {
            'id': activity.id,
            'uid': activity.uid or '',
            'reporting_date': activity.reporting_date.strftime('%Y-%m-%d') if activity.reporting_date else '',
            'completion_date': activity.completion_date.strftime('%Y-%m-%d') if activity.completion_date else '',
            'agent_id': activity.agent.id if activity.agent else '',
            'agent_name': f"{activity.agent.first_name} {activity.agent.last_name}" if activity.agent else 'N/A',
            'main_activity_id': activity.main_activity.id if activity.main_activity else '',
            'main_activity': activity.main_activity.main_activity if activity.main_activity else 'N/A',
            'sub_activity_id': activity.activity.id if activity.activity else '',
            'sub_activity': activity.activity.sub_activity if activity.activity else 'N/A',
            'no_rehab_assistants': activity.no_rehab_assistants or 0,
            'area_covered_ha': activity.area_covered_ha or 0,
            'farm_ref_number': activity.farm_ref_number or '',
            'farm_size_ha': activity.farm_size_ha or 0,
            'community': activity.community.name if activity.community else '',
            'community_id': activity.community.id if activity.community else '',
            'sector': activity.sector or '',
            'group_work': activity.group_work or 'No',
            'number_of_people_in_group': activity.number_of_people_in_group or 0,
            'remark': activity.remark or '',
            'status': activity.status,
            'ras': ras,
            'project_id': activity.projectTbl_foreignkey.id if activity.projectTbl_foreignkey else '',
            'district_id': activity.district.id if activity.district else '',
            'created_date': activity.created_date.strftime('%Y-%m-%d %H:%M:%S') if activity.created_date else '',
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except DailyReportingModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def activity_update(request, activity_id):
    """Update an existing activity report"""
    try:
        activity = DailyReportingModel.objects.get(id=activity_id)
        data = json.loads(request.body)
        
        # Update fields
        if 'agent_id' in data:
            activity.agent = staffTbl.objects.get(id=data['agent_id'])
        if 'main_activity_id' in data:
            activity.main_activity = Activities.objects.get(id=data['main_activity_id'])
        if 'sub_activity_id' in data:
            activity.activity = Activities.objects.get(id=data['sub_activity_id'])
        if 'completion_date' in data:
            activity.completion_date = data['completion_date']
        if 'reporting_date' in data:
            activity.reporting_date = data['reporting_date']
        if 'no_rehab_assistants' in data:
            activity.no_rehab_assistants = data['no_rehab_assistants']
        if 'area_covered_ha' in data:
            activity.area_covered_ha = data['area_covered_ha']
        if 'remark' in data:
            activity.remark = data['remark']
        if 'status' in data:
            activity.status = data['status']
        if 'farm_ref_number' in data:
            activity.farm_ref_number = data['farm_ref_number']
        if 'farm_size_ha' in data:
            activity.farm_size_ha = data['farm_size_ha']
        if 'number_of_people_in_group' in data:
            activity.number_of_people_in_group = data['number_of_people_in_group']
        if 'group_work' in data:
            activity.group_work = data['group_work']
        if 'sector' in data:
            activity.sector = data['sector']
        
        activity.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Activity report updated successfully'
        })
        
    except DailyReportingModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def activity_delete(request, activity_id):
    """Delete an activity report (soft delete)"""
    try:
        activity = DailyReportingModel.objects.get(id=activity_id)
        data = json.loads(request.body)
        
        # Soft delete by setting delete_field
        activity.delete_field = 'yes'
        activity.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Activity report deleted successfully'
        })
        
    except DailyReportingModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# Additional helper endpoints
@csrf_exempt
@require_http_methods(["GET"])
def get_main_activities(request):
    """Get all main activities for dropdown"""
    try:
        activities = Activities.objects.values('id', 'main_activity').distinct()
        return JsonResponse({
            'success': True,
            'data': list(activities)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_sub_activities(request):
    """Get sub activities filtered by main activity"""
    try:
        main_activity_id = request.GET.get('main_activity_id')
        if main_activity_id:
            sub_activities = Activities.objects.filter(
                id=main_activity_id
            ).values('id', 'sub_activity', 'activity_code')
        else:
            sub_activities = Activities.objects.values('id', 'sub_activity', 'activity_code')
        
        return JsonResponse({
            'success': True,
            'data': list(sub_activities)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_agents(request):
    """Get all project officers/agents for dropdown"""
    try:
        # Assuming Project Officers are staff members with specific group
        agents = staffTbl.objects.values('id', 'first_name', 'last_name', 'staffid')
        data = []
        for agent in agents:
            data.append({
                'id': agent['id'],
                'name': f"{agent['first_name']} {agent['last_name']}",
                'staffid': agent['staffid']
            })
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)