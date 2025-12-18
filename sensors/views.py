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

def dashboard(request):
    """Main dashboard view"""
    devices = Device.objects.all()
    total_readings = SensorReading.objects.count()
    active_devices = Device.objects.filter(status='active').count()
    
    context = {
        'devices': devices,
        'total_readings': total_readings,
        'active_devices': active_devices,
    }
    return render(request, 'sensors/dashboard.html', context)


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
