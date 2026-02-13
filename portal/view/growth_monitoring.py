# views/growth_monitoring_views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.utils import timezone
import json
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

from portal.models import (
    GrowthMonitoringModel, 
    QR_CodeModel, 
    staffTbl, 
    projectTbl, 
    cocoaDistrict,
    
)

User = get_user_model()

@login_required
def growth_monitoring_page(request):
    """Render the Growth Monitoring page"""
    return render(request, 'portal/qr_code/growth_monitoring.html')

@csrf_exempt
@require_http_methods(["GET"])
def get_growth_monitoring_list(request):
    """Get paginated list of growth monitoring records - OPTIMIZED for performance"""
    try:
        # Get parameters from DataTable
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        
        # Limit maximum page size to prevent overload
        if length > 100:
            length = 100
            
        search_value = request.GET.get('search[value]', '')
        
        # Base queryset - only select needed fields, no select_related for large datasets
        queryset = GrowthMonitoringModel.objects.filter(delete_field='no')
        
        # Apply user permissions filter
        user = request.user
        if not user.is_superuser:
            groups = user.groups.values_list('name', flat=True)
            
            try:
                staff = staffTbl.objects.get(user=user)
                
                if 'Project Officer' in groups:
                    queryset = queryset.filter(agent=staff)
                elif 'Monitoring and Evaluation' in groups:
                    staff_districts = staff.districtStaffTbl_set.values_list('districtTbl_foreignkey', flat=True)
                    queryset = queryset.filter(district_id__in=staff_districts)
                elif 'Regional Manager' in groups:
                    staff_regions = staff.regionStaffTbl_set.values_list('regionTbl_foreignkey', flat=True)
                    districts = cocoaDistrict.objects.filter(region_id__in=staff_regions).values_list('id', flat=True)
                    queryset = queryset.filter(district_id__in=districts)
                elif 'District Officer' in groups:
                    staff_districts = staff.districtStaffTbl_set.values_list('districtTbl_foreignkey', flat=True)
                    queryset = queryset.filter(district_id__in=staff_districts)
            except staffTbl.DoesNotExist:
                pass
        
        # Apply search filter - optimized with only necessary fields
        if search_value:
            queryset = queryset.filter(
                Q(plant_uid__icontains=search_value) |
                Q(uid__icontains=search_value)
            )
        
        # Apply date filters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Apply district filter
        district_id = request.GET.get('district_id')
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        
        # Apply agent filter
        agent_id = request.GET.get('agent_id')
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        # Apply leaf color filter
        leaf_color = request.GET.get('leaf_color')
        if leaf_color:
            queryset = queryset.filter(leaf_color=leaf_color)
        
        # Get total count
        total_records = queryset.count()
        
        # Ordering
        order_column = request.GET.get('order[0][column]', 0)
        order_dir = request.GET.get('order[0][dir]', 'desc')
        
        columns = ['id', 'date', 'plant_uid', 'agent', 'height', 
                  'stem_size', 'number_of_leaves', 'district', 'qr_code']
        
        if int(order_column) < len(columns):
            order_field = columns[int(order_column)]
            if order_dir == 'desc':
                order_field = f'-{order_field}'
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('-date')
        
        # Apply pagination - VERY IMPORTANT for performance
        paginated_queryset = queryset[start:start + length]
        
        # Prepare data - fetch related data in separate queries to avoid N+1
        agent_ids = [record.agent_id for record in paginated_queryset if record.agent_id]
        district_ids = [record.district_id for record in paginated_queryset if record.district_id]
        qr_code_ids = [record.qr_code_id for record in paginated_queryset if record.qr_code_id]
        
        # Batch fetch related data
        agents = {a.id: a for a in staffTbl.objects.filter(id__in=agent_ids)} if agent_ids else {}
        districts = {d.id: d for d in cocoaDistrict.objects.filter(id__in=district_ids)} if district_ids else {}
        qr_codes = {q.id: q for q in QR_CodeModel.objects.filter(id__in=qr_code_ids)} if qr_code_ids else {}
        
        # Prepare data
        data = []
        for record in paginated_queryset:
            agent = agents.get(record.agent_id)
            district = districts.get(record.district_id)
            qr_code = qr_codes.get(record.qr_code_id)
            
            data.append({
                'id': record.id,
                'uid': record.uid,
                'plant_uid': record.plant_uid,
                'number_of_leaves': record.number_of_leaves,
                'height': float(record.height) if record.height else 0,
                'stem_size': float(record.stem_size) if record.stem_size else 0,
                'leaf_color': record.leaf_color,
                'date': record.date.strftime('%Y-%m-%d') if record.date else '',
                'lat': float(record.lat) if record.lat else 0,
                'lng': float(record.lng) if record.lng else 0,
                'agent_id': record.agent_id,
                'agent_name': f"{agent.first_name} {agent.last_name}"[:30] if agent else 'N/A',  # Limit string length
                'district_id': record.district_id,
                'district_name': district.name[:50] if district else 'N/A',  # Limit string length
                'project_id': record.projectTbl_foreignkey_id,
                'qr_code_id': record.qr_code_id,
                'qr_code_uid': qr_code.uid[:50] if qr_code else 'N/A',  # Limit string length
                'qr_code_image': qr_code.qr_code.url if qr_code and qr_code.qr_code else None,
            })
        
        response_data = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data,
            'success': True
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    


@csrf_exempt
@require_http_methods(["GET"])
def get_growth_monitoring_detail(request, record_id):
    """Get single growth monitoring record details"""
    try:
        record = GrowthMonitoringModel.objects.select_related(
            'agent', 'district', 'projectTbl_foreignkey', 'qr_code'
        ).get(id=record_id, delete_field='no')
        
        data = {
            'id': record.id,
            'uid': record.uid,
            'plant_uid': record.plant_uid,
            'number_of_leaves': record.number_of_leaves,
            'height': record.height,
            'stem_size': record.stem_size,
            'leaf_color': record.leaf_color,
            'date': record.date.strftime('%Y-%m-%d') if record.date else '',
            'lat': record.lat,
            'lng': record.lng,
            'agent_id': record.agent.id if record.agent else None,
            'agent_name': f"{record.agent.first_name} {record.agent.last_name}" if record.agent else 'N/A',
            'district_id': record.district.id if record.district else None,
            'district_name': record.district.name if record.district else 'N/A',
            'project_id': record.projectTbl_foreignkey.id if record.projectTbl_foreignkey else None,
            'project_name': record.projectTbl_foreignkey.name if record.projectTbl_foreignkey else 'N/A',
            'qr_code_id': record.qr_code.id if record.qr_code else None,
            'qr_code_uid': record.qr_code.uid if record.qr_code else 'N/A',
            'qr_code_image': record.qr_code.qr_code.url if record.qr_code and record.qr_code.qr_code else None,
            'created_date': record.created_date.strftime('%Y-%m-%d %H:%M:%S') if record.created_date else '',
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except GrowthMonitoringModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Record not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_growth_monitoring(request):
    """Create a new growth monitoring record"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['plant_uid', 'number_of_leaves', 'height', 
                          'stem_size', 'leaf_color', 'date', 'lat', 'lng']
        for field in required_fields:
            if field not in data or data[field] is None:
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)
        
        # Create record
        record = GrowthMonitoringModel()
        record.plant_uid = data['plant_uid']
        record.number_of_leaves = data['number_of_leaves']
        record.height = data['height']
        record.stem_size = data['stem_size']
        record.leaf_color = data['leaf_color']
        record.date = data['date']
        record.lat = data['lat']
        record.lng = data['lng']
        
        # Optional fields
        if data.get('uid'):
            record.uid = data['uid']
        else:
            # Generate UID: GM-YYYYMMDD-XXXX
            import random
            import string
            date_str = datetime.now().strftime('%Y%m%d')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            record.uid = f"GM-{date_str}-{random_str}"
        
        # Foreign keys
        if data.get('agent_id'):
            try:
                record.agent = staffTbl.objects.get(id=data['agent_id'])
            except staffTbl.DoesNotExist:
                pass
        
        if data.get('qr_code_id'):
            try:
                record.qr_code = QR_CodeModel.objects.get(id=data['qr_code_id'])
            except QR_CodeModel.DoesNotExist:
                pass
        
        if data.get('project_id'):
            try:
                record.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                pass
        
        if data.get('district_id'):
            try:
                record.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        
        record.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Growth monitoring record created successfully',
            'data': {'id': record.id, 'uid': record.uid}
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["PUT", "POST"])
def update_growth_monitoring(request, record_id):
    """Update an existing growth monitoring record"""
    try:
        record = GrowthMonitoringModel.objects.get(id=record_id, delete_field='no')
        data = json.loads(request.body)
        
        # Update fields
        if data.get('plant_uid'):
            record.plant_uid = data['plant_uid']
        if data.get('number_of_leaves') is not None:
            record.number_of_leaves = data['number_of_leaves']
        if data.get('height') is not None:
            record.height = data['height']
        if data.get('stem_size') is not None:
            record.stem_size = data['stem_size']
        if data.get('leaf_color'):
            record.leaf_color = data['leaf_color']
        if data.get('date'):
            record.date = data['date']
        if data.get('lat') is not None:
            record.lat = data['lat']
        if data.get('lng') is not None:
            record.lng = data['lng']
        
        # Foreign keys
        if data.get('agent_id'):
            try:
                record.agent = staffTbl.objects.get(id=data['agent_id'])
            except staffTbl.DoesNotExist:
                pass
        
        if data.get('qr_code_id'):
            try:
                record.qr_code = QR_CodeModel.objects.get(id=data['qr_code_id'])
            except QR_CodeModel.DoesNotExist:
                pass
        
        if data.get('project_id'):
            try:
                record.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                pass
        
        if data.get('district_id'):
            try:
                record.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        
        record.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Growth monitoring record updated successfully'
        })
        
    except GrowthMonitoringModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Record not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def delete_growth_monitoring(request, record_id):
    """Soft delete a growth monitoring record"""
    try:
        record = GrowthMonitoringModel.objects.get(id=record_id, delete_field='no')
        
        # Soft delete
        record.delete_field = 'yes'
        record.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Growth monitoring record deleted successfully'
        })
        
    except GrowthMonitoringModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Record not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_growth_stats(request):
    """Get statistics for growth monitoring dashboard"""
    try:
        queryset = GrowthMonitoringModel.objects.filter(delete_field='no')
        
        # Filter by user permissions (similar to list view)
        user = request.user
        if not user.is_superuser:
            groups = user.groups.values_list('name', flat=True)
            try:
                staff = staffTbl.objects.get(user=user)
                
                if 'Project Officer' in groups:
                    queryset = queryset.filter(agent=staff)
                elif 'Monitoring and Evaluation' in groups:
                    staff_districts = staff.districtStaffTbl_set.values_list('districtTbl_foreignkey', flat=True)
                    queryset = queryset.filter(district_id__in=staff_districts)
                elif 'Regional Manager' in groups:
                    staff_regions = staff.regionStaffTbl_set.values_list('regionTbl_foreignkey', flat=True)
                    districts = cocoaDistrict.objects.filter(region_id__in=staff_regions)
                    queryset = queryset.filter(district_id__in=districts)
                elif 'District Officer' in groups:
                    staff_districts = staff.districtStaffTbl_set.values_list('districtTbl_foreignkey', flat=True)
                    queryset = queryset.filter(district_id__in=staff_districts)
            except staffTbl.DoesNotExist:
                pass
        
        # Apply date filters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Calculate stats
        total_records = queryset.count()
        
        # Average measurements
        avg_height = queryset.aggregate(Avg('height'))['height__avg'] or 0
        avg_stem_size = queryset.aggregate(Avg('stem_size'))['stem_size__avg'] or 0
        avg_leaves = queryset.aggregate(Avg('number_of_leaves'))['number_of_leaves__avg'] or 0
        
        # Today's records
        today = timezone.now().date()
        today_records = queryset.filter(date=today).count()
        
        # This week
        week_start = today - timedelta(days=today.weekday())
        week_records = queryset.filter(date__gte=week_start).count()
        
        # This month
        month_start = today.replace(day=1)
        month_records = queryset.filter(date__gte=month_start).count()
        
        # Leaf color distribution
        leaf_colors = queryset.values('leaf_color').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent activity (last 7 days)
        last_7_days = today - timedelta(days=7)
        recent_dates = queryset.filter(date__gte=last_7_days).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Top plants by height
        top_plants = queryset.order_by('-height')[:10].values('plant_uid', 'height', 'date')
        
        return JsonResponse({
            'success': True,
            'data': {
                'total_records': total_records,
                'today_records': today_records,
                'week_records': week_records,
                'month_records': month_records,
                'avg_height': round(avg_height, 2),
                'avg_stem_size': round(avg_stem_size, 2),
                'avg_leaves': round(avg_leaves, 2),
                'leaf_colors': list(leaf_colors),
                'recent_activity': list(recent_dates),
                'top_plants': list(top_plants)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_qr_code(request):
    """Get QR codes for dropdown"""
    try:
        qr_codes = QR_CodeModel.objects.filter(delete_field='no').order_by('-created_date')
        
        # Search filter
        search = request.GET.get('search', '')
        if search:
            qr_codes = qr_codes.filter(
                Q(uid__icontains=search) |
                Q(id__icontains=search)
            )
        
        # Limit results
        qr_codes = qr_codes[:50]
        
        data = []
        for qr in qr_codes:
            data.append({
                'id': qr.id,
                'uid': qr.uid,
                'qr_code_url': qr.qr_code.url if qr.qr_code else None
            })
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_plant_uids(request):
    """Get existing plant UIDs for autocomplete"""
    try:
        search = request.GET.get('search', '')
        
        plant_uids = GrowthMonitoringModel.objects.filter(
            delete_field='no'
        ).values_list('plant_uid', flat=True).distinct()
        
        if search:
            plant_uids = plant_uids.filter(plant_uid__icontains=search)
        
        plant_uids = plant_uids[:50]
        
        return JsonResponse({
            'success': True,
            'data': list(plant_uids)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    

######################################################################################################################



@csrf_exempt
@require_http_methods(["GET"])
def get_plant_growth_history(request, plant_uid):
    """Get complete growth history for a specific plant"""
    try:
        # Get all records for this plant
        records = GrowthMonitoringModel.objects.filter(
            delete_field='no',
            plant_uid=plant_uid
        ).select_related(
            'agent', 'district', 'qr_code'
        ).order_by('date')
        
        if not records.exists():
            return JsonResponse({
                'success': False,
                'error': 'No growth records found for this plant'
            }, status=404)
        
        # Calculate statistics
        first_record = records.first()
        last_record = records.last()
        
        # Growth metrics
        height_progress = last_record.height - first_record.height
        leaves_progress = last_record.number_of_leaves - first_record.number_of_leaves
        stem_progress = last_record.stem_size - first_record.stem_size
        
        # Days between first and last measurement
        days_diff = (last_record.date - first_record.date).days or 1
        
        # Daily growth rates
        daily_height_growth = height_progress / days_diff
        daily_leaves_growth = leaves_progress / days_diff
        
        # Health score calculation
        def calculate_health_score(height, leaves, leaf_color):
            height_score = min(40, (height / 100) * 40) if height else 0
            leaves_score = min(30, (leaves / 50) * 30) if leaves else 0
            color_scores = {
                'Dark Green': 30, 'Green': 25, 'Light Green': 20,
                'Yellowish': 10, 'Spotted': 5, 'Brown': 0
            }
            color_score = color_scores.get(leaf_color, 15)
            return round(height_score + leaves_score + color_score)
        
        # Prepare chart data
        chart_data = {
            'dates': [],
            'height': [],
            'leaves': [],
            'stem': [],
            'health': []
        }
        
        health_scores = []
        for record in records:
            chart_data['dates'].append(record.date.strftime('%Y-%m-%d'))
            chart_data['height'].append(round(record.height, 1))
            chart_data['leaves'].append(record.number_of_leaves)
            chart_data['stem'].append(round(record.stem_size, 1))
            
            health_score = calculate_health_score(
                record.height, 
                record.number_of_leaves, 
                record.leaf_color
            )
            chart_data['health'].append(health_score)
            health_scores.append(health_score)
        
        # Current health status
        current_health = calculate_health_score(
            last_record.height,
            last_record.number_of_leaves,
            last_record.leaf_color
        )
        
        # Get health trend
        if len(health_scores) >= 2:
            health_trend = health_scores[-1] - health_scores[-2]
        else:
            health_trend = 0
        
        # Determine health status category
        if current_health >= 80:
            health_status = 'Excellent'
            health_color = 'success'
        elif current_health >= 60:
            health_status = 'Good'
            health_color = 'info'
        elif current_health >= 40:
            health_status = 'Fair'
            health_color = 'warning'
        else:
            health_status = 'Poor'
            health_color = 'danger'
        
        # Get officer performance
        officer_records = {}
        for record in records:
            if record.agent:
                officer_name = f"{record.agent.first_name} {record.agent.last_name}"
                if officer_name not in officer_records:
                    officer_records[officer_name] = {
                        'count': 0,
                        'avg_height': 0,
                        'avg_health': 0
                    }
                officer_records[officer_name]['count'] += 1
                officer_records[officer_name]['avg_height'] += record.height
                officer_records[officer_name]['avg_health'] += calculate_health_score(
                    record.height, record.number_of_leaves, record.leaf_color
                )
        
        # Calculate averages for officers
        for officer, stats in officer_records.items():
            if stats['count'] > 0:
                stats['avg_height'] = round(stats['avg_height'] / stats['count'], 1)
                stats['avg_health'] = round(stats['avg_health'] / stats['count'], 1)
        
        # Prepare response
        response_data = {
            'success': True,
            'data': {
                'plant_info': {
                    'plant_uid': plant_uid,
                    'qr_code_uid': last_record.qr_code.uid if last_record.qr_code else 'N/A',
                    'qr_code_image': last_record.qr_code.qr_code.url if last_record.qr_code and last_record.qr_code.qr_code else None,
                    'district': last_record.district.name if last_record.district else 'N/A',
                    'current_officer': f"{last_record.agent.first_name} {last_record.agent.last_name}" if last_record.agent else 'N/A',
                    'first_measured': first_record.date.strftime('%Y-%m-%d'),
                    'last_measured': last_record.date.strftime('%Y-%m-%d'),
                    'total_measurements': records.count(),
                    'monitoring_days': days_diff,
                },
                'current_metrics': {
                    'height': round(last_record.height, 1),
                    'leaves': last_record.number_of_leaves,
                    'stem': round(last_record.stem_size, 1),
                    'leaf_color': last_record.leaf_color,
                    'health_score': current_health,
                    'health_status': health_status,
                    'health_color': health_color,
                    'health_trend': health_trend,
                    'location': {
                        'lat': last_record.lat,
                        'lng': last_record.lng
                    }
                },
                'growth_progress': {
                    'height_progress': round(height_progress, 1),
                    'leaves_progress': leaves_progress,
                    'stem_progress': round(stem_progress, 1),
                    'height_percentage': round((height_progress / (first_record.height or 1)) * 100, 1) if first_record.height else 0,
                    'leaves_percentage': round((leaves_progress / (first_record.number_of_leaves or 1)) * 100, 1) if first_record.number_of_leaves else 0,
                    'daily_height_growth': round(daily_height_growth, 2),
                    'daily_leaves_growth': round(daily_leaves_growth, 2),
                },
                'chart_data': chart_data,
                'officer_history': officer_records,
                'measurement_history': [
                    {
                        'date': r.date.strftime('%Y-%m-%d'),
                        'height': round(r.height, 1),
                        'leaves': r.number_of_leaves,
                        'stem': round(r.stem_size, 1),
                        'leaf_color': r.leaf_color,
                        'officer': f"{r.agent.first_name} {r.agent.last_name}" if r.agent else 'N/A',
                        'health_score': calculate_health_score(r.height, r.number_of_leaves, r.leaf_color)
                    } for r in records[:]  # Last 10 records
                ]
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# Add this URL pattern
