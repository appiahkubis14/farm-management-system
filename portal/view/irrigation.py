# views.py - Add these views for Irrigation

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
import json
from datetime import datetime, timedelta
from django.shortcuts import render

from portal.models import FarmdetailsTbl, IrrigationModel, cocoaDistrict, projectTbl, staffTbl

# Irrigation Overview page
def irrigation_overview(request):
    """Main view for Irrigation Overview page"""
    context = {
        'irrigation_types': ['drip', 'sprinkler', 'furrow', 'basin', 'center pivot'],
    }
    return render(request, 'portal/irrigation/irrigation_overview.html', context)

# ============== API ENDPOINTS FOR IrrigationModel ==============

@require_http_methods(["GET"])
def irrigation_list_api(request):
    """API endpoint for Irrigation list with server-side processing"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Base queryset
        queryset = IrrigationModel.objects.filter(delete_field='no')
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(uid__icontains=search_value) |
                Q(irrigation_type__icontains=search_value) |
                Q(farm__farm_reference__icontains=search_value) |
                Q(farm__farmername__icontains=search_value) |
                Q(agent__first_name__icontains=search_value) |
                Q(agent__last_name__icontains=search_value)
            )
        
        # Apply filters from request
        district_id = request.GET.get('district_id')
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        
        project_id = request.GET.get('project_id')
        if project_id:
            queryset = queryset.filter(projectTbl_foreignkey_id=project_id)
        
        irrigation_type = request.GET.get('irrigation_type')
        if irrigation_type:
            queryset = queryset.filter(irrigation_type=irrigation_type)
        
        start_date = request.GET.get('start_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        end_date = request.GET.get('end_date')
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Get total counts
        total_records = queryset.count()
        
        # Apply sorting
        order_column = request.GET.get('order[0][column]', 0)
        order_dir = request.GET.get('order[0][dir]', 'asc')
        
        columns = ['id', 'uid', 'farm__farm_reference', 'farm__farmername', 'irrigation_type', 
                  'water_volume', 'date', 'agent__first_name', 'district__name']
        
        if int(order_column) < len(columns):
            order_field = columns[int(order_column)]
            if order_dir == 'desc':
                order_field = f'-{order_field}'
            queryset = queryset.order_by(order_field)
        else:
            queryset = queryset.order_by('-date')
        
        # Paginate
        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        page_obj = paginator.get_page(page_number)
        
        # Prepare data
        data = []
        for irrigation in page_obj:
            data.append({
                'id': irrigation.id,
                'uid': irrigation.uid or 'N/A',
                'farm_id': irrigation.farm.id if irrigation.farm else None,
                'farm_reference': irrigation.farm.farm_reference if irrigation.farm else 'N/A',
                'farmer_name': irrigation.farm.farmername if irrigation.farm else 'N/A',
                'irrigation_type': irrigation.irrigation_type,
                'irrigation_type_display': irrigation.irrigation_type.title() if irrigation.irrigation_type else 'N/A',
                'water_volume': irrigation.water_volume,
                'date': irrigation.date.strftime('%Y-%m-%d') if irrigation.date else '',
                'agent_id': irrigation.agent.id if irrigation.agent else None,
                'agent_name': f"{irrigation.agent.first_name} {irrigation.agent.last_name}" if irrigation.agent else 'N/A',
                'project_id': irrigation.projectTbl_foreignkey.id if irrigation.projectTbl_foreignkey else None,
                'project_name': irrigation.projectTbl_foreignkey.name if irrigation.projectTbl_foreignkey else 'N/A',
                'district_id': irrigation.district.id if irrigation.district else None,
                'district_name': irrigation.district.name if irrigation.district else 'N/A',
                'created_date': irrigation.created_date.strftime('%Y-%m-%d %H:%M:%S') if irrigation.created_date else '',
                'irrigation_type_badge': get_irrigation_type_badge(irrigation.irrigation_type),
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

def get_irrigation_type_badge(irrigation_type):
    """Helper to get badge class for irrigation type"""
    badges = {
        'drip': 'success',
        'sprinkler': 'info',
        'furrow': 'warning',
        'basin': 'primary',
        'center pivot': 'danger'
    }
    return badges.get(irrigation_type, 'secondary')

@require_http_methods(["GET"])
def irrigation_detail_api(request, pk):
    """API endpoint for single Irrigation details"""
    try:
        irrigation = IrrigationModel.objects.get(pk=pk, delete_field='no')
        
        data = {
            'id': irrigation.id,
            'uid': irrigation.uid,
            'farm_id': irrigation.farm.id if irrigation.farm else None,
            'farm_reference': irrigation.farm.farm_reference if irrigation.farm else None,
            'farmer_name': irrigation.farm.farmername if irrigation.farm else None,
            'farm_location': irrigation.farm.location if irrigation.farm else None,
            'farm_size': irrigation.farm.farm_size if irrigation.farm else None,
            'irrigation_type': irrigation.irrigation_type,
            'water_volume': irrigation.water_volume,
            'date': irrigation.date.strftime('%Y-%m-%d') if irrigation.date else '',
            'agent_id': irrigation.agent.id if irrigation.agent else None,
            'agent_name': f"{irrigation.agent.first_name} {irrigation.agent.last_name}" if irrigation.agent else None,
            'agent_contact': irrigation.agent.contact if irrigation.agent else None,
            'project_id': irrigation.projectTbl_foreignkey.id if irrigation.projectTbl_foreignkey else None,
            'project_name': irrigation.projectTbl_foreignkey.name if irrigation.projectTbl_foreignkey else None,
            'district_id': irrigation.district.id if irrigation.district else None,
            'district_name': irrigation.district.name if irrigation.district else None,
            'created_date': irrigation.created_date.strftime('%Y-%m-%d %H:%M:%S') if irrigation.created_date else '',
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except IrrigationModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Irrigation record not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def irrigation_create(request):
    """API endpoint to create a new Irrigation record"""
    try:
        data = json.loads(request.body)
        
        irrigation = IrrigationModel()
        irrigation = update_irrigation_from_data(irrigation, data)
        irrigation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Irrigation record created successfully',
            'id': irrigation.id,
            'uid': irrigation.uid
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def irrigation_update(request, pk):
    """API endpoint to update an Irrigation record"""
    try:
        irrigation = IrrigationModel.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body)
        
        irrigation = update_irrigation_from_data(irrigation, data)
        irrigation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Irrigation record updated successfully'
        })
        
    except IrrigationModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Irrigation record not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def update_irrigation_from_data(irrigation, data):
    """Helper function to update Irrigation from JSON data"""
    
    irrigation.irrigation_type = data.get('irrigation_type', irrigation.irrigation_type)
    irrigation.water_volume = data.get('water_volume', irrigation.water_volume)
    
    if data.get('date'):
        irrigation.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    irrigation.uid = data.get('uid', irrigation.uid)
    
    # Foreign keys
    if data.get('farm_id'):
        try:
            irrigation.farm = FarmdetailsTbl.objects.get(id=data['farm_id'])
        except FarmdetailsTbl.DoesNotExist:
            pass
    
    if data.get('agent_id'):
        try:
            irrigation.agent = staffTbl.objects.get(id=data['agent_id'])
        except staffTbl.DoesNotExist:
            pass
    
    if data.get('project_id'):
        try:
            irrigation.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
        except projectTbl.DoesNotExist:
            pass
    
    if data.get('district_id'):
        try:
            irrigation.district = cocoaDistrict.objects.get(id=data['district_id'])
        except cocoaDistrict.DoesNotExist:
            pass
    
    return irrigation

@csrf_exempt
@require_http_methods(["POST"])
def irrigation_delete(request, pk):
    """API endpoint to soft delete an Irrigation record"""
    try:
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', 'No reason provided')
        
        irrigation = IrrigationModel.objects.get(pk=pk)
        irrigation.delete_field = 'yes'
        # Add reason field if your model has it, otherwise just soft delete
        # irrigation.reason4expunge = reason[:2500] if reason else None
        irrigation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Irrigation record deleted successfully'
        })
        
    except IrrigationModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Irrigation record not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_http_methods(["GET"])
def irrigation_stats_api(request):
    """API endpoint for Irrigation statistics"""
    try:
        queryset = IrrigationModel.objects.filter(delete_field='no')
        
        # Apply filters
        district_id = request.GET.get('district_id')
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        
        project_id = request.GET.get('project_id')
        if project_id:
            queryset = queryset.filter(projectTbl_foreignkey_id=project_id)
        
        start_date = request.GET.get('start_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        end_date = request.GET.get('end_date')
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Total records
        total_records = queryset.count()
        
        # Total water volume
        total_volume = queryset.aggregate(total=Sum('water_volume'))['total'] or 0
        
        # Average water volume per irrigation
        avg_volume = queryset.aggregate(avg=Avg('water_volume'))['avg'] or 0
        
        # By irrigation type
        type_counts = queryset.values('irrigation_type').annotate(
            count=Count('id'),
            volume=Sum('water_volume')
        )
        
        type_data = {}
        for item in type_counts:
            type_data[item['irrigation_type']] = {
                'count': item['count'],
                'volume': item['volume'] or 0
            }
        
        # Recent irrigations (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_count = queryset.filter(date__gte=thirty_days_ago).count()
        recent_volume = queryset.filter(date__gte=thirty_days_ago).aggregate(total=Sum('water_volume'))['total'] or 0
        
        # This month's irrigations
        current_month = timezone.now().month
        current_year = timezone.now().year
        month_count = queryset.filter(
            date__month=current_month,
            date__year=current_year
        ).count()
        month_volume = queryset.filter(
            date__month=current_month,
            date__year=current_year
        ).aggregate(total=Sum('water_volume'))['total'] or 0
        
        # Unique farms irrigated
        unique_farms = queryset.values('farm').distinct().count()
        
        stats = {
            'total_records': total_records,
            'total_volume': round(total_volume, 2),
            'avg_volume': round(avg_volume, 2),
            'recent_count': recent_count,
            'recent_volume': round(recent_volume, 2),
            'month_count': month_count,
            'month_volume': round(month_volume, 2),
            'unique_farms': unique_farms,
            'by_type': type_data,
        }
        
        return JsonResponse({'success': True, 'data': stats})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_http_methods(["GET"])
def irrigation_chart_api(request):
    """API endpoint for irrigation chart data"""
    try:
        queryset = IrrigationModel.objects.filter(delete_field='no')
        
        # Apply filters
        district_id = request.GET.get('district_id')
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        
        project_id = request.GET.get('project_id')
        if project_id:
            queryset = queryset.filter(projectTbl_foreignkey_id=project_id)
        
        # Get last 30 days of data
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=29)
        
        daily_data = []
        for i in range(30):
            date = start_date + timedelta(days=i)
            day_records = queryset.filter(date=date)
            count = day_records.count()
            volume = day_records.aggregate(total=Sum('water_volume'))['total'] or 0
            
            daily_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count,
                'volume': round(volume, 2)
            })
        
        # Data by irrigation type
        type_data = queryset.values('irrigation_type').annotate(
            count=Count('id'),
            volume=Sum('water_volume')
        )
        
        chart_data = {
            'daily': daily_data,
            'by_type': list(type_data)
        }
        
        return JsonResponse({'success': True, 'data': chart_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# Farm list for dropdown
@require_http_methods(["GET"])
def farm_list_api(request):
    """API endpoint for farms list (for dropdown)"""
    try:
        farms = FarmdetailsTbl.objects.filter(
            delete_field='no'
        ).values(
            'id', 'farm_reference', 'farmername', 'location', 'district__name'
        ).order_by('farm_reference')[:200]
        
        farm_list = []
        for farm in farms:
            farm_list.append({
                'id': farm['id'],
                'farm_reference': farm['farm_reference'],
                'farmername': farm['farmername'],
                'location': farm['location'],
                'district': farm['district__name'],
                'display': f"{farm['farm_reference']} - {farm['farmername']} ({farm['district__name']})"
            })
        
        return JsonResponse({'success': True, 'data': farm_list})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# Staff list for dropdown
@require_http_methods(["GET"])
def staff_list_dropdown_api(request):
    """API endpoint for staff list (for dropdown)"""
    try:
        staff = staffTbl.objects.filter(
            delete_field='no'
        ).values(
            'id', 'first_name', 'last_name', 'staffid', 'contact'
        ).order_by('first_name')[:200]
        
        staff_list = []
        for s in staff:
            staff_list.append({
                'id': s['id'],
                'name': f"{s['first_name']} {s['last_name']}",
                'staffid': s['staffid'],
                'contact': s['contact'],
                'display': f"{s['first_name']} {s['last_name']} ({s['staffid']})"
            })
        
        return JsonResponse({'success': True, 'data': staff_list})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})