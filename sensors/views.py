from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Avg, Count
from django.db.models.functions import TruncHour, TruncDay
import json
from datetime import timedelta

from .models import Device, SensorReading


# ==================== Web Views ====================

# def dashboard(request):
#     """Main dashboard view"""
#     devices = Device.objects.all()
#     total_readings = SensorReading.objects.count()
#     active_devices = Device.objects.filter(status='active').count()
    
#     context = {
#         'devices': devices,
#         'total_readings': total_readings,
#         'active_devices': active_devices,
#     }
#     return render(request, 'sensors/dashboard.html', context)

from datetime import datetime, timedelta
from django.db.models import Max, Min

# Enhanced dashboard view
def dashboard(request):
    """Main dashboard view with enhanced statistics"""
    devices = Device.objects.all()
    total_readings = SensorReading.objects.count()
    active_devices = Device.objects.filter(status='active').count()
    
    # Get today's readings count
    today = timezone.now().date()
    today_readings = SensorReading.objects.filter(
        timestamp__date=today
    ).count()
    
    # Get device types distribution
    device_types = {
        'soil': devices.filter(device_type='soil').count(),
        'temperature': devices.filter(device_type='temperature').count(),
        'humidity': devices.filter(device_type='humidity').count(),
        'multi': devices.filter(device_type='multi').count(),
    }
    
    # Get recent readings for charts
    recent_readings = SensorReading.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-timestamp')[:20]
    
    # Get devices with latest readings
    devices_with_data = []
    for device in devices:
        latest = device.readings.first()
        devices_with_data.append({
            'device': device,
            'latest_reading': latest,
        })
    
    context = {
        'devices': devices_with_data,
        'total_readings': total_readings,
        'active_devices': active_devices,
        'today_readings': today_readings,
        'device_types': device_types,
        'recent_readings': recent_readings,
        'total_devices': devices.count(),
    }
    return render(request, 'sensors/dashboard.html', context)



# Add new API endpoint for chart data
def api_dashboard_stats(request):
    """Get dashboard statistics for charts"""
    # Last 24 hours data grouped by hour
    hours_24 = timezone.now() - timedelta(hours=24)
    
    # Temperature trends
    temp_readings = SensorReading.objects.filter(
        timestamp__gte=hours_24,
        temperature__isnull=False
    ).extra({
        'hour': "date_trunc('hour', timestamp)"
    }).values('hour').annotate(
        avg_temp=Avg('temperature'),
        max_temp=Max('temperature'),
        min_temp=Min('temperature')
    ).order_by('hour')
    
    # Humidity trends
    hum_readings = SensorReading.objects.filter(
        timestamp__gte=hours_24,
        humidity__isnull=False
    ).extra({
        'hour': "date_trunc('hour', timestamp)"
    }).values('hour').annotate(
        avg_hum=Avg('humidity'),
    ).order_by('hour')
    
    # Device activity
    active_devices = Device.objects.filter(
        last_seen__gte=timezone.now() - timedelta(minutes=5)
    ).count()
    
    # Recent alerts (you can implement alerts based on thresholds)
    alerts = []
    
    return JsonResponse({
        'temperature_trends': list(temp_readings),
        'humidity_trends': list(hum_readings),
        'active_devices': active_devices,
        'alerts': alerts,
        'last_updated': timezone.now().isoformat(),
    })


def device_detail(request, device_id):
    """Device detail view with charts"""
    device = get_object_or_404(Device, device_id=device_id)
    recent_readings = device.readings.all()[:50]
    
    context = {
        'device': device,
        'recent_readings': recent_readings,
    }
    return render(request, 'sensors/device_detail.html', context)


def devices_list(request):
    """List all devices"""
    devices = Device.objects.all()
    context = {'devices': devices}
    return render(request, 'sensors/devices_list.html', context)


def websocket_test(request):
    """WebSocket test page"""
    return render(request, 'sensors/websocket_test.html')


# ==================== API Views ====================

@csrf_exempt
@require_http_methods(["POST"])
def register_device(request):
    """API endpoint to register a new device"""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        device_name = data.get('device_name')
        device_type = data.get('device_type', 'multi')
        location = data.get('location', '')
        
        if not device_id or not device_name:
            return JsonResponse({
                'success': False,
                'error': 'device_id and device_name are required'
            }, status=400)
        
        device, created = Device.objects.get_or_create(
            device_id=device_id,
            defaults={
                'device_name': device_name,
                'device_type': device_type,
                'location': location,
            }
        )
        
        if not created:
            device.last_seen = timezone.now()
            device.save()
        
        return JsonResponse({
            'success': True,
            'device_id': device.device_id,
            'api_key': str(device.api_key),
            'created': created
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def submit_reading(request):
    """API endpoint for sensors to submit readings"""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        api_key = data.get('api_key')
        
        if not device_id or not api_key:
            return JsonResponse({
                'success': False,
                'error': 'device_id and api_key are required'
            }, status=400)
        
        # Authenticate device
        try:
            device = Device.objects.get(device_id=device_id, api_key=api_key)
        except Device.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid device_id or api_key'
            }, status=401)
        
        # Update device last seen
        device.last_seen = timezone.now()
        device.save()
        
        # Create sensor reading
        reading = SensorReading.objects.create(
            device=device,
            temperature=data.get('temperature'),
            humidity=data.get('humidity'),
            soil_moisture=data.get('soil_moisture'),
            soil_raw=data.get('soil_raw'),
            battery_level=data.get('battery_level'),
            signal_strength=data.get('signal_strength'),
        )
        
        # Broadcast to WebSocket (will be handled by channels)
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"device_{device_id}",
                {
                    "type": "sensor_update",
                    "data": reading.to_dict()
                }
            )
            # Also send to general dashboard group
            async_to_sync(channel_layer.group_send)(
                "dashboard",
                {
                    "type": "sensor_update",
                    "data": reading.to_dict()
                }
            )
        
        return JsonResponse({
            'success': True,
            'reading_id': reading.id,
            'timestamp': reading.timestamp.isoformat()
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def api_device_readings(request, device_id):
    """Get recent readings for a device"""
    device = get_object_or_404(Device, device_id=device_id)
    limit = int(request.GET.get('limit', 100))
    
    readings = device.readings.all()[:limit]
    data = [reading.to_dict() for reading in readings]
    
    return JsonResponse({
        'device_id': device_id,
        'device_name': device.device_name,
        'readings': data
    })


def api_device_stats(request, device_id):
    """Get statistics for a device"""
    device = get_object_or_404(Device, device_id=device_id)
    
    # Get time range
    hours = int(request.GET.get('hours', 24))
    since = timezone.now() - timedelta(hours=hours)
    
    readings = device.readings.filter(timestamp__gte=since)
    
    stats = readings.aggregate(
        avg_temperature=Avg('temperature'),
        avg_humidity=Avg('humidity'),
        avg_soil_moisture=Avg('soil_moisture'),
        count=Count('id')
    )
    
    return JsonResponse({
        'device_id': device_id,
        'device_name': device.device_name,
        'time_range_hours': hours,
        'statistics': stats
    })


def api_all_devices(request):
    """Get list of all devices with their latest reading"""
    devices = Device.objects.all()
    data = []
    
    for device in devices:
        latest = device.readings.first()
        device_data = {
            'device_id': device.device_id,
            'device_name': device.device_name,
            'device_type': device.device_type,
            'location': device.location,
            'status': device.status,
            'last_seen': device.last_seen.isoformat(),
            'latest_reading': latest.to_dict() if latest else None
        }
        data.append(device_data)
    
    return JsonResponse({'devices': data})












#############################################################################################

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncHour, TruncDay
import json
from datetime import timedelta
# sensors/views.py - Add these views

def devices_management(request):
    """Device management page"""
    return render(request, 'sensors/devices_management.html')


def api_devices_list(request):
    """API endpoint for devices list (DataTables server-side)"""
    # Get DataTables parameters
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    
    # Build query
    devices = Device.objects.all()
    
    # Apply search
    if search_value:
        devices = devices.filter(
            Q(device_id__icontains=search_value) |
            Q(device_name__icontains=search_value) |
            Q(location__icontains=search_value) |
            Q(device_type__icontains=search_value) |
            Q(status__icontains=search_value)
        )
    
    # Get total count
    total_records = devices.count()
    
    # Apply ordering
    order_column = int(request.GET.get('order[0][column]', 0))
    order_dir = request.GET.get('order[0][dir]', 'asc')
    order_fields = ['device_id', 'device_name', 'device_type', 'location', 'status', 'last_seen']
    
    if order_column < len(order_fields):
        order_field = order_fields[order_column]
        if order_dir == 'desc':
            order_field = '-' + order_field
        devices = devices.order_by(order_field)
    
    # Paginate
    devices = devices[start:start + length]
    
    # Prepare response data
    data = []
    for device in devices:
        latest_reading = device.readings.first()
        data.append({
            'id': device.device_id,
            'device_id': device.device_id,
            'device_name': device.device_name,
            'device_type': device.get_device_type_display(),
            'location': device.location or 'Not set',
            'status': device.get_status_display(),
            'last_seen': device.last_seen.strftime('%Y-%m-%d %H:%M:%S'),
            'registered_at': device.registered_at.strftime('%Y-%m-%d'),
            'temperature': latest_reading.temperature if latest_reading else '--',
            'humidity': latest_reading.humidity if latest_reading else '--',
            'soil_moisture': latest_reading.soil_moisture if latest_reading else '--',
        })
    
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })


def api_device_detail(request, device_id):
    """API endpoint for single device details"""
    try:
        device = Device.objects.get(device_id=device_id)
        latest_reading = device.readings.first()
        
        data = {
            'device_id': device.device_id,
            'device_name': device.device_name,
            'device_type': device.device_type,
            'location': device.location,
            'status': device.status,
            'api_key': str(device.api_key),
            'registered_at': device.registered_at.strftime('%Y-%m-%d %H:%M:%S'),
            'last_seen': device.last_seen.strftime('%Y-%m-%d %H:%M:%S'),
            'latest_reading': {
                'temperature': latest_reading.temperature if latest_reading else None,
                'humidity': latest_reading.humidity if latest_reading else None,
                'soil_moisture': latest_reading.soil_moisture if latest_reading else None,
                'soil_raw': latest_reading.soil_raw if latest_reading else None,
                'battery_level': latest_reading.battery_level if latest_reading else None,
                'signal_strength': latest_reading.signal_strength if latest_reading else None,
                'timestamp': latest_reading.timestamp.strftime('%Y-%m-%d %H:%M:%S') if latest_reading else None,
            } if latest_reading else None
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Device.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Device not found'
        }, status=404)


@csrf_exempt
def api_device_create(request):
    """API endpoint to create a new device"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['device_id', 'device_name']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'message': f'{field} is required'
                    }, status=400)
            
            # Check if device already exists
            if Device.objects.filter(device_id=data['device_id']).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Device ID already exists'
                }, status=400)
            
            # Create device
            device = Device.objects.create(
                device_id=data['device_id'],
                device_name=data['device_name'],
                device_type=data.get('device_type', 'multi'),
                location=data.get('location', ''),
                status=data.get('status', 'active')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Device created successfully',
                'data': {
                    'device_id': device.device_id,
                    'api_key': str(device.api_key)
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)


@csrf_exempt
def api_device_update(request, device_id):
    """API endpoint to update a device"""
    if request.method == 'POST':
        try:
            device = Device.objects.get(device_id=device_id)
            data = json.loads(request.body)
            
            # Update fields
            if 'device_name' in data:
                device.device_name = data['device_name']
            if 'device_type' in data:
                device.device_type = data['device_type']
            if 'location' in data:
                device.location = data['location']
            if 'status' in data:
                device.status = data['status']
            
            device.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Device updated successfully'
            })
            
        except Device.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found'
            }, status=404)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)


@csrf_exempt
def api_device_delete(request, device_id):
    """API endpoint to delete a device"""
    if request.method == 'POST':
        try:
            device = Device.objects.get(device_id=device_id)
            
            # Delete associated readings first
            device.readings.all().delete()
            
            # Delete device
            device.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Device deleted successfully'
            })
            
        except Device.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)


def api_device_generate_key(request, device_id):
    """API endpoint to generate new API key for device"""
    if request.method == 'POST':
        try:
            device = Device.objects.get(device_id=device_id)
            device.api_key = uuid.uuid4()
            device.save()
            
            return JsonResponse({
                'success': True,
                'message': 'New API key generated successfully',
                'api_key': str(device.api_key)
            })
            
        except Device.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Device not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)