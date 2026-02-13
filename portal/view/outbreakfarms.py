# views.py - Add these views for OutbreakFarms

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
import json
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404

from portal.models import (
    Community, FarmdetailsTbl, OutbreakFarm, OutbreakFarmModel, Region, projectTbl,
    staffTbl, cocoaDistrict
)

# OutbreakFarms Overview page
def outbreakfarms_overview(request):
    """Main view for OutbreakFarms Overview page"""
    context = {
        'severity_choices': ['Low', 'Medium', 'High', 'Critical'],
        'status_choices': ['Pending', 'Submitted', 'Treated', 'Resolved'],
        'disease_types': OutbreakFarm.objects.values_list('disease_type', flat=True).distinct().order_by('disease_type'),
        'disease_types_model': OutbreakFarmModel.objects.values_list('disease_type', flat=True).distinct().order_by('disease_type'),
    }
    return render(request, 'portal/outbreakfarms/outbreakfarms_overview.html', context)

# ============== API ENDPOINTS FOR OutbreakFarm MODEL ==============

@require_http_methods(["GET"])
def outbreakfarm_list_api(request):
    """API endpoint for OutbreakFarm list with server-side processing"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Base queryset
        queryset = OutbreakFarm.objects.filter(delete_field='no')
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(outbreak_id__icontains=search_value) |
                Q(farmer_name__icontains=search_value) |
                Q(farm_location__icontains=search_value) |
                Q(disease_type__icontains=search_value) |
                Q(status__icontains=search_value) |
                Q(severity__icontains=search_value)
            )
        
        # Apply filters from request
        district_id = request.GET.get('district_id')
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        
        region_id = request.GET.get('region_id')
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        
        severity = request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        status = request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        disease_type = request.GET.get('disease_type')
        if disease_type:
            queryset = queryset.filter(disease_type=disease_type)
        
        # Get total counts
        total_records = queryset.count()
        
        # Apply sorting
        order_column = request.GET.get('order[0][column]', 0)
        order_dir = request.GET.get('order[0][dir]', 'asc')
        
        columns = ['id', 'outbreak_id', 'farmer_name', 'farm_location', 'disease_type', 
                  'severity', 'status', 'inspection_date', 'district__name', 'region__name']
        
        if int(order_column) < len(columns):
            order_field = columns[int(order_column)]
            if order_dir == 'desc':
                order_field = f'-{order_field}'
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('-inspection_date')
        
        # Paginate
        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        page_obj = paginator.get_page(page_number)
        
        # Prepare data
        data = []
        for outbreak in page_obj:
            data.append({
                'id': outbreak.id,
                'outbreak_id': outbreak.outbreak_id or 'N/A',
                'farmer_name': outbreak.farmer_name or 'N/A',
                'farmer_age': outbreak.farmer_age,
                'farmer_contact': outbreak.farmer_contact,
                'farm_location': outbreak.farm_location or 'N/A',
                'farm_area': outbreak.farm_area,
                'community': outbreak.community.name if outbreak.community else outbreak.communitytbl or 'N/A',
                'disease_type': outbreak.disease_type or 'N/A',
                'severity': outbreak.severity,
                'status': outbreak.status,
                'status_display': dict(OutbreakFarm._meta.get_field('status').choices).get(outbreak.status, 'Unknown'),
                'inspection_date': outbreak.inspection_date.strftime('%Y-%m-%d') if outbreak.inspection_date else '',
                'date_reported': outbreak.date_reported.strftime('%Y-%m-%d') if outbreak.date_reported else '',
                'treatment_applied': outbreak.treatment_applied or 'N/A',
                'treatment_date': outbreak.treatment_date.strftime('%Y-%m-%d') if outbreak.treatment_date else '',
                'district': outbreak.district.name if outbreak.district else 'N/A',
                'district_id': outbreak.district.id if outbreak.district else None,
                'region': outbreak.region.name if outbreak.region else 'N/A',
                'region_id': outbreak.region.id if outbreak.region else None,
                'reported_by': outbreak.reported_by.first_name + ' ' + outbreak.reported_by.last_name if outbreak.reported_by else 'N/A',
                'coordinates': outbreak.coordinates or 'N/A',
                'severity_badge': get_severity_badge(outbreak.severity),
                'status_badge': get_status_badge(outbreak.status),
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
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'success': False,
            'message': str(e)
        })

def get_severity_badge(severity):
    """Helper to get badge class for severity"""
    badges = {
        'Low': 'success',
        'Medium': 'warning',
        'High': 'danger',
        'Critical': 'dark'
    }
    return badges.get(severity, 'secondary')

def get_status_badge(status):
    """Helper to get badge class for status"""
    status_map = {
        0: 'secondary',  # Pending
        1: 'info',       # Submitted
        2: 'warning',    # Treated
        3: 'success'     # Resolved
    }
    return status_map.get(status, 'secondary')

@require_http_methods(["GET"])
def outbreakfarm_detail_api(request, pk):
    """API endpoint for single OutbreakFarm details"""
    try:
        outbreak = OutbreakFarm.objects.get(pk=pk, delete_field='no')
        
        data = {
            'id': outbreak.id,
            'outbreak_id': outbreak.outbreak_id,
            'farm_id': outbreak.farm.id if outbreak.farm else None,
            'farm_reference': outbreak.farm.farm_reference if outbreak.farm else None,
            'farm_location': outbreak.farm_location,
            'farmer_name': outbreak.farmer_name,
            'farmer_age': outbreak.farmer_age,
            'id_type': outbreak.id_type,
            'id_number': outbreak.id_number,
            'farmer_contact': outbreak.farmer_contact,
            'cocoa_type': outbreak.cocoa_type,
            'age_class': outbreak.age_class,
            'farm_area': outbreak.farm_area,
            'communitytbl': outbreak.communitytbl,
            'community_id': outbreak.community.id if outbreak.community else None,
            'community_name': outbreak.community.name if outbreak.community else None,
            'inspection_date': outbreak.inspection_date.strftime('%Y-%m-%d') if outbreak.inspection_date else '',
            'temp_code': outbreak.temp_code,
            'disease_type': outbreak.disease_type,
            'date_reported': outbreak.date_reported.strftime('%Y-%m-%d') if outbreak.date_reported else '',
            'reported_by_id': outbreak.reported_by.id if outbreak.reported_by else None,
            'reported_by_name': f"{outbreak.reported_by.first_name} {outbreak.reported_by.last_name}" if outbreak.reported_by else None,
            'status': outbreak.status,
            'status_display': dict(OutbreakFarm._meta.get_field('status').choices).get(outbreak.status, 'Unknown'),
            'coordinates': outbreak.coordinates,
            'severity': outbreak.severity,
            'treatment_applied': outbreak.treatment_applied,
            'treatment_date': outbreak.treatment_date.strftime('%Y-%m-%d') if outbreak.treatment_date else '',
            'project_id': outbreak.projectTbl_foreignkey.id if outbreak.projectTbl_foreignkey else None,
            'project_name': outbreak.projectTbl_foreignkey.name if outbreak.projectTbl_foreignkey else None,
            'district_id': outbreak.district.id if outbreak.district else None,
            'district_name': outbreak.district.name if outbreak.district else None,
            'region_id': outbreak.region.id if outbreak.region else None,
            'region_name': outbreak.region.name if outbreak.region else None,
            'uid': outbreak.uid,
            'created_date': outbreak.created_date.strftime('%Y-%m-%d %H:%M:%S') if outbreak.created_date else '',
            'geom': outbreak.geom.geojson if outbreak.geom else None,
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except OutbreakFarm.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Outbreak farm not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def outbreakfarm_create(request):
    """API endpoint to create a new OutbreakFarm"""
    try:
        data = json.loads(request.body)
        
        outbreak = OutbreakFarm()
        outbreak = update_outbreakfarm_from_data(outbreak, data)
        outbreak.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Outbreak farm created successfully',
            'id': outbreak.id,
            'outbreak_id': outbreak.outbreak_id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def outbreakfarm_update(request, pk):
    """API endpoint to update an OutbreakFarm"""
    try:
        outbreak = OutbreakFarm.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body)
        
        outbreak = update_outbreakfarm_from_data(outbreak, data)
        outbreak.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Outbreak farm updated successfully'
        })
        
    except OutbreakFarm.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Outbreak farm not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def update_outbreakfarm_from_data(outbreak, data):
    """Helper function to update OutbreakFarm from JSON data"""
    # Basic fields
    outbreak.farm_location = data.get('farm_location', outbreak.farm_location)
    outbreak.farmer_name = data.get('farmer_name', outbreak.farmer_name)
    outbreak.farmer_age = data.get('farmer_age', outbreak.farmer_age)
    outbreak.id_type = data.get('id_type', outbreak.id_type)
    outbreak.id_number = data.get('id_number', outbreak.id_number)
    outbreak.farmer_contact = data.get('farmer_contact', outbreak.farmer_contact)
    outbreak.cocoa_type = data.get('cocoa_type', outbreak.cocoa_type)
    outbreak.age_class = data.get('age_class', outbreak.age_class)
    outbreak.farm_area = data.get('farm_area', outbreak.farm_area)
    outbreak.communitytbl = data.get('communitytbl', outbreak.communitytbl)
    outbreak.temp_code = data.get('temp_code', outbreak.temp_code)
    outbreak.disease_type = data.get('disease_type', outbreak.disease_type)
    outbreak.coordinates = data.get('coordinates', outbreak.coordinates)
    outbreak.severity = data.get('severity', outbreak.severity)
    outbreak.treatment_applied = data.get('treatment_applied', outbreak.treatment_applied)
    
    # Date fields
    if data.get('inspection_date'):
        outbreak.inspection_date = datetime.strptime(data['inspection_date'], '%Y-%m-%d').date()
    if data.get('date_reported'):
        outbreak.date_reported = datetime.strptime(data['date_reported'], '%Y-%m-%d').date()
    if data.get('treatment_date'):
        outbreak.treatment_date = datetime.strptime(data['treatment_date'], '%Y-%m-%d').date()
    
    # Foreign keys
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if data.get('reported_by_id'):
        try:
            outbreak.reported_by = staffTbl.objects.get(id=data['reported_by_id'])
        except:
            pass
    
    if data.get('community_id'):
        try:
            outbreak.community = Community.objects.get(id=data['community_id'])
        except:
            pass
    
    if data.get('district_id'):
        try:
            outbreak.district = cocoaDistrict.objects.get(id=data['district_id'])
        except:
            pass
    
    if data.get('region_id'):
        try:
            outbreak.region = Region.objects.get(id=data['region_id'])
        except:
            pass
    
    if data.get('project_id'):
        try:
            outbreak.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
        except:
            pass
    
    if data.get('farm_id'):
        try:
            outbreak.farm = FarmdetailsTbl.objects.get(id=data['farm_id'])
        except:
            pass
    
    # Status
    outbreak.status = data.get('status', outbreak.status)
    outbreak.uid = data.get('uid', outbreak.uid)
    
    # Handle geometry
    if data.get('coordinates') and ',' in data['coordinates']:
        try:
            lat, lng = data['coordinates'].split(',')
            from django.contrib.gis.geos import Point
            outbreak.geom = Point(float(lng.strip()), float(lat.strip()))
        except:
            pass
    
    return outbreak

@csrf_exempt
@require_http_methods(["POST"])
def outbreakfarm_delete(request, pk):
    """API endpoint to soft delete an OutbreakFarm"""
    try:
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', 'No reason provided')
        
        outbreak = OutbreakFarm.objects.get(pk=pk)
        outbreak.delete_field = 'yes'
        outbreak.reason4expunge = reason[:2500] if reason else None
        outbreak.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Outbreak farm deleted successfully'
        })
        
    except OutbreakFarm.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Outbreak farm not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_http_methods(["GET"])
def outbreakfarm_stats_api(request):
    """API endpoint for OutbreakFarm statistics"""
    try:
        queryset = OutbreakFarm.objects.filter(delete_field='no')
        
        # Apply filters
        district_id = request.GET.get('district_id')
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        
        region_id = request.GET.get('region_id')
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        
        # Total outbreaks
        total_outbreaks = queryset.count()
        
        # By severity
        severity_counts = queryset.values('severity').annotate(count=Count('id'))
        severity_data = {item['severity']: item['count'] for item in severity_counts}
        
        # By status
        status_counts = queryset.values('status').annotate(count=Count('id'))
        status_data = {}
        for item in status_counts:
            status_display = dict(OutbreakFarm._meta.get_field('status').choices).get(item['status'], 'Unknown')
            status_data[status_display] = item['count']
        
        # By disease type
        disease_counts = queryset.values('disease_type').annotate(count=Count('id')).order_by('-count')[:5]
        disease_data = {item['disease_type']: item['count'] for item in disease_counts if item['disease_type']}
        
        # Recent outbreaks (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_outbreaks = queryset.filter(date_reported__gte=thirty_days_ago).count()
        
        # Total farm area affected
        total_area = queryset.aggregate(total=Sum('farm_area'))['total'] or 0
        
        # Average farm size
        avg_area = queryset.aggregate(avg=Avg('farm_area'))['avg'] or 0
        
        # Critical outbreaks
        critical_outbreaks = queryset.filter(severity='Critical').count()
        
        # Outbreaks this month
        current_month = timezone.now().month
        current_year = timezone.now().year
        month_outbreaks = queryset.filter(
            date_reported__month=current_month,
            date_reported__year=current_year
        ).count()
        
        stats = {
            'total_outbreaks': total_outbreaks,
            'recent_outbreaks': recent_outbreaks,
            'critical_outbreaks': critical_outbreaks,
            'month_outbreaks': month_outbreaks,
            'total_area_affected': round(total_area, 2),
            'avg_farm_size': round(avg_area, 2),
            'severity': severity_data,
            'status': status_data,
            'disease_types': disease_data,
        }
        
        return JsonResponse({'success': True, 'data': stats})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# ============== API ENDPOINTS FOR OutbreakFarmModel MODEL ==============

@require_http_methods(["GET"])
def outbreakfarmmodel_list_api(request):
    """API endpoint for OutbreakFarmModel list with server-side processing"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Base queryset
        queryset = OutbreakFarmModel.objects.filter(delete_field='no')
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(uid__icontains=search_value) |
                Q(farmer_name__icontains=search_value) |
                Q(farm_location__icontains=search_value) |
                Q(disease_type__icontains=search_value)
            )
        
        # Apply filters from request
        district_id = request.GET.get('district_id')
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        
        region_id = request.GET.get('region_id')
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        
        disease_type = request.GET.get('disease_type')
        if disease_type:
            queryset = queryset.filter(disease_type=disease_type)
        
        status = request.GET.get('status')
        if status is not None:
            queryset = queryset.filter(status=status)
        
        # Get total counts
        total_records = queryset.count()
        
        # Apply sorting
        order_column = request.GET.get('order[0][column]', 0)
        order_dir = request.GET.get('order[0][dir]', 'asc')
        
        columns = ['id', 'uid', 'farmer_name', 'farm_location', 'disease_type', 
                  'status', 'date_reported', 'district__name', 'region__name']
        
        if int(order_column) < len(columns):
            order_field = columns[int(order_column)]
            if order_dir == 'desc':
                order_field = f'-{order_field}'
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('-date_reported')
        
        # Paginate
        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        page_obj = paginator.get_page(page_number)
        
        # Prepare data
        data = []
        for outbreak in page_obj:
            data.append({
                'id': outbreak.id,
                'uid': outbreak.uid or 'N/A',
                'farmer_name': outbreak.farmer_name or 'N/A',
                'farm_location': outbreak.farm_location or 'N/A',
                'farm_size': outbreak.farm_size,
                'community': outbreak.community.name if outbreak.community else 'N/A',
                'disease_type': outbreak.disease_type or 'N/A',
                'status': outbreak.status,
                'status_display': 'Submitted' if outbreak.status == 1 else 'Pending',
                'date_reported': outbreak.date_reported.strftime('%Y-%m-%d') if outbreak.date_reported else '',
                'coordinates': outbreak.coordinates or 'N/A',
                'district': outbreak.district.name if outbreak.district else 'N/A',
                'district_id': outbreak.district.id if outbreak.district else None,
                'region': outbreak.region.name if outbreak.region else 'N/A',
                'region_id': outbreak.region.id if outbreak.region else None,
                'reported_by': f"{outbreak.reported_by.first_name} {outbreak.reported_by.last_name}" if outbreak.reported_by else 'N/A',
                'status_badge': 'success' if outbreak.status == 1 else 'secondary',
                'created_date': outbreak.created_date.strftime('%Y-%m-%d %H:%M:%S') if outbreak.created_date else '',
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
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'success': False,
            'message': str(e)
        })

@require_http_methods(["GET"])
def outbreakfarmmodel_detail_api(request, pk):
    """API endpoint for single OutbreakFarmModel details"""
    try:
        outbreak = OutbreakFarmModel.objects.get(pk=pk, delete_field='no')
        
        data = {
            'id': outbreak.id,
            'uid': outbreak.uid,
            'farmer_name': outbreak.farmer_name,
            'farm_location': outbreak.farm_location,
            'community_id': outbreak.community.id if outbreak.community else None,
            'community_name': outbreak.community.name if outbreak.community else None,
            'farm_size': outbreak.farm_size,
            'disease_type': outbreak.disease_type,
            'date_reported': outbreak.date_reported.strftime('%Y-%m-%d') if outbreak.date_reported else '',
            'reported_by_id': outbreak.reported_by.id if outbreak.reported_by else None,
            'reported_by_name': f"{outbreak.reported_by.first_name} {outbreak.reported_by.last_name}" if outbreak.reported_by else None,
            'status': outbreak.status,
            'status_display': 'Submitted' if outbreak.status == 1 else 'Pending',
            'coordinates': outbreak.coordinates,
            'project_id': outbreak.projectTbl_foreignkey.id if outbreak.projectTbl_foreignkey else None,
            'project_name': outbreak.projectTbl_foreignkey.name if outbreak.projectTbl_foreignkey else None,
            'district_id': outbreak.district.id if outbreak.district else None,
            'district_name': outbreak.district.name if outbreak.district else None,
            'region_id': outbreak.region.id if outbreak.region else None,
            'region_name': outbreak.region.name if outbreak.region else None,
            'created_date': outbreak.created_date.strftime('%Y-%m-%d %H:%M:%S') if outbreak.created_date else '',
        }
        
        # Get geometry if exists
        if outbreak.geom:
            try:
                data['geom'] = outbreak.geom.geojson
            except:
                pass
        
        return JsonResponse({'success': True, 'data': data})
        
    except OutbreakFarmModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Outbreak farm not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def outbreakfarmmodel_create(request):
    """API endpoint to create a new OutbreakFarmModel"""
    try:
        data = json.loads(request.body)
        
        outbreak = OutbreakFarmModel()
        outbreak = update_outbreakfarmmodel_from_data(outbreak, data)
        outbreak.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Outbreak farm created successfully',
            'id': outbreak.id,
            'uid': outbreak.uid
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def outbreakfarmmodel_update(request, pk):
    """API endpoint to update an OutbreakFarmModel"""
    try:
        outbreak = OutbreakFarmModel.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body)
        
        outbreak = update_outbreakfarmmodel_from_data(outbreak, data)
        outbreak.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Outbreak farm updated successfully'
        })
        
    except OutbreakFarmModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Outbreak farm not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def update_outbreakfarmmodel_from_data(outbreak, data):
    """Helper function to update OutbreakFarmModel from JSON data"""
    outbreak.farmer_name = data.get('farmer_name', outbreak.farmer_name)
    outbreak.farm_location = data.get('farm_location', outbreak.farm_location)
    outbreak.farm_size = data.get('farm_size', outbreak.farm_size)
    outbreak.disease_type = data.get('disease_type', outbreak.disease_type)
    outbreak.coordinates = data.get('coordinates', outbreak.coordinates)
    
    if data.get('date_reported'):
        outbreak.date_reported = datetime.strptime(data['date_reported'], '%Y-%m-%d').date()
    
    # Foreign keys
    if data.get('community_id'):
        try:
            outbreak.community = Community.objects.get(id=data['community_id'])
        except:
            pass
    
    if data.get('reported_by_id'):
        try:
            outbreak.reported_by = staffTbl.objects.get(id=data['reported_by_id'])
        except:
            pass
    
    if data.get('district_id'):
        try:
            outbreak.district = cocoaDistrict.objects.get(id=data['district_id'])
        except:
            pass
    
    if data.get('region_id'):
        try:
            outbreak.region = Region.objects.get(id=data['region_id'])
        except:
            pass
    
    if data.get('project_id'):
        try:
            outbreak.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
        except:
            pass
    
    outbreak.status = data.get('status', outbreak.status)
    outbreak.uid = data.get('uid', outbreak.uid)
    
    # Handle geometry
    if data.get('coordinates') and ',' in data['coordinates']:
        try:
            lat, lng = data['coordinates'].split(',')
            from django.contrib.gis.geos import Point
            outbreak.geom = Point(float(lng.strip()), float(lat.strip()))
        except:
            pass
    
    return outbreak

@csrf_exempt
@require_http_methods(["POST"])
def outbreakfarmmodel_delete(request, pk):
    """API endpoint to soft delete an OutbreakFarmModel"""
    try:
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', 'No reason provided')
        
        outbreak = OutbreakFarmModel.objects.get(pk=pk)
        outbreak.delete_field = 'yes'
        outbreak.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Outbreak farm deleted successfully'
        })
        
    except OutbreakFarmModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Outbreak farm not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_http_methods(["GET"])
def outbreakfarmmodel_stats_api(request):
    """API endpoint for OutbreakFarmModel statistics"""
    try:
        queryset = OutbreakFarmModel.objects.filter(delete_field='no')
        
        # Apply filters
        district_id = request.GET.get('district_id')
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        
        region_id = request.GET.get('region_id')
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        
        total_outbreaks = queryset.count()
        
        # By status
        status_counts = queryset.values('status').annotate(count=Count('id'))
        status_data = {'Pending': 0, 'Submitted': 0}
        for item in status_counts:
            if item['status'] == 0:
                status_data['Pending'] = item['count']
            else:
                status_data['Submitted'] = item['count']
        
        # By disease type
        disease_counts = queryset.values('disease_type').annotate(count=Count('id')).order_by('-count')[:5]
        disease_data = {item['disease_type']: item['count'] for item in disease_counts if item['disease_type']}
        
        # Recent outbreaks (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_outbreaks = queryset.filter(date_reported__gte=thirty_days_ago).count()
        
        # Total farm area affected
        total_area = queryset.aggregate(total=Sum('farm_size'))['total'] or 0
        
        stats = {
            'total_outbreaks': total_outbreaks,
            'recent_outbreaks': recent_outbreaks,
            'total_area_affected': round(total_area, 2),
            'pending': status_data.get('Pending', 0),
            'submitted': status_data.get('Submitted', 0),
            'disease_types': disease_data,
        }
        
        return JsonResponse({'success': True, 'data': stats})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
    


# Add these helper views if not already present

@require_http_methods(["GET"])
def get_districts(request):
    """API endpoint to get districts for dropdown"""
    try:
        districts = cocoaDistrict.objects.filter(delete_field='no').values('id', 'name')
        return JsonResponse({'success': True, 'data': list(districts)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_http_methods(["GET"])
def get_regions(request):
    """API endpoint to get regions for dropdown"""
    try:
        regions = Region.objects.filter(delete_field='no').values('id', 'region')
        return JsonResponse({'success': True, 'data': list(regions)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_http_methods(["GET"])
def get_communities(request):
    """API endpoint to get communities for dropdown, optionally filtered by district"""
    try:
        district_id = request.GET.get('district_id')
        queryset = Community.objects.filter(delete_field='no')
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        communities = queryset.values('id', 'name', 'district_id')
        return JsonResponse({'success': True, 'data': list(communities)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_http_methods(["GET"])
def get_projects(request):
    """API endpoint to get projects for dropdown"""
    try:
        projects = projectTbl.objects.filter(delete_field='no').values('id', 'name')
        return JsonResponse({'success': True, 'data': list(projects)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_http_methods(["GET"])
def farm_list_api(request):
    """API endpoint for farms list (for dropdown)"""
    try:
        farms = FarmdetailsTbl.objects.filter(delete_field='no').values('id', 'farm_reference', 'farmername')[:100]
        return JsonResponse({'success': True, 'data': list(farms)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})