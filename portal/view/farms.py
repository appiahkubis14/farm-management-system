from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from portal.models import FarmdetailsTbl, cocoaDistrict
import json
from django.core.paginator import Paginator
from django.db import transaction
from datetime import datetime

@login_required
def farm_details_page(request):
    """Main page for farm details management"""
    districts = cocoaDistrict.objects.all().order_by('district')
    farms = FarmdetailsTbl.objects.filter(expunge=False).select_related('farm_foreignkey', 'districtTbl_foreignkey')
    
    context = {
        'page_title': 'Farm Details Management',
        'districts': districts,
        'status_choices': FarmdetailsTbl.STATUS_CHOICES,
        'farms': farms,
    }
    return render(request, 'portal/Farms/farms.html', context)

@login_required
def farm_details_api(request):
    """API endpoint for datatable"""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    
    # Base queryset
    queryset = FarmdetailsTbl.objects.filter(expunge=False).select_related(
        'farm_foreignkey', 'districtTbl_foreignkey'
    )
    
    # Search functionality
    if search_value:
        queryset = queryset.filter(
            Q(farm_reference__icontains=search_value) |
            Q(farmername__icontains=search_value) |
            Q(location__icontains=search_value) |
            Q(district__icontains=search_value) |
            Q(region__icontains=search_value) |
            Q(status__icontains=search_value)
        )
    
    # Total records
    total_records = queryset.count()
    
    # Apply pagination
    queryset = queryset.order_by('-id')[start:start + length]
    
    # Prepare data
    data = []
    for farm in queryset:
        data.append({
            'id': farm.id,
            'farm_reference': farm.farm_reference,
            'farmer_name': farm.farmername,
            'region': farm.region,
            'district': farm.district,
            'location': farm.location,
            'farm_size': f"{farm.farm_size} acres" if farm.farm_size else "N/A",
            'status': farm.status,
            'year_of_establishment': farm.year_of_establishment.strftime('%Y-%m-%d') if farm.year_of_establishment else "N/A",
            'sector': farm.sector if farm.sector else "N/A",
            'created_at': farm.created_date.strftime('%Y-%m-%d %H:%M') if farm.created_date else "N/A",
        })
    
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })

@login_required
@require_http_methods(["GET"])
def get_farm_details(request, farm_id):
    """Get single farm details"""
    try:
        farm = FarmdetailsTbl.objects.get(id=farm_id)
        
        data = {
            'id': farm.id,
            'farm_reference': farm.farm_reference,
            'farmer_name': farm.farmername,
            'region': farm.region,
            'district': farm.district,
            'location': farm.location,
            'farm_size': farm.farm_size,
            'status': farm.status,
            'year_of_establishment': farm.year_of_establishment.strftime('%Y-%m-%d') if farm.year_of_establishment else None,
            'sector': farm.sector,
            'created_at': farm.created_date.strftime('%Y-%m-%d %H:%M') if farm.created_date else None,
            # 'updated_at': farm.updated_at.strftime('%Y-%m-%d %H:%M') if farm.updated_at else None,
        }
        
        return JsonResponse({'success': True, 'data': data})
    except FarmdetailsTbl.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Farm not found'}, status=404)

@login_required
@require_http_methods(["POST"])
def create_farm(request):
    """Create new farm"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['farm_reference', 'farmer_name', 'region', 'district', 'location']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'{field.replace("_", " ").title()} is required'})
        
        # Check if farm reference already exists
        if FarmdetailsTbl.objects.filter(farm_reference=data['farm_reference']).exists():
            return JsonResponse({'success': False, 'message': 'Farm reference already exists'})
        
        # Get or create cocoa district
        district_obj, created = cocoaDistrict.objects.get_or_create(
            district=data['district'],
            defaults={'district_code': data['district'][:3].upper()}
        )
        
        # Parse date
        year_of_establishment = None
        if data.get('year_of_establishment'):
            try:
                year_of_establishment = datetime.strptime(data['year_of_establishment'], '%Y-%m-%d').date()
            except:
                pass
        
        # Create farm
        farm = FarmdetailsTbl.objects.create(
            farm_reference=data['farm_reference'],
            farmername=data['farmer_name'],
            region=data['region'],
            district=data['district'],
            location=data['location'],
            farm_size=data.get('farm_size'),
            status=data.get('status', 'Maintenance'),
            sector=data.get('sector'),
            year_of_establishment=year_of_establishment,
            districtTbl_foreignkey=district_obj
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Farm created successfully',
            'farm_id': farm.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def update_farm(request, farm_id):
    """Update farm details"""
    try:
        data = json.loads(request.body)
        farm = FarmdetailsTbl.objects.get(id=farm_id)
        
        # Check if farm reference is being changed and already exists
        if data.get('farm_reference') and data['farm_reference'] != farm.farm_reference:
            if FarmdetailsTbl.objects.filter(farm_reference=data['farm_reference']).exists():
                return JsonResponse({'success': False, 'message': 'Farm reference already exists'})
        
        # Update district if changed
        if data.get('district') and data['district'] != farm.district:
            district_obj, created = cocoaDistrict.objects.get_or_create(
                district=data['district'],
                defaults={'district_code': data['district'][:3].upper()}
            )
            farm.districtTbl_foreignkey = district_obj
        
        # Parse date
        if data.get('year_of_establishment'):
            try:
                farm.year_of_establishment = datetime.strptime(data['year_of_establishment'], '%Y-%m-%d').date()
            except:
                pass
        
        # Update fields
        farm.farm_reference = data.get('farm_reference', farm.farm_reference)
        farm.farmername = data.get('farmer_name', farm.farmername)
        farm.region = data.get('region', farm.region)
        farm.district = data.get('district', farm.district)
        farm.location = data.get('location', farm.location)
        farm.farm_size = data.get('farm_size', farm.farm_size)
        farm.status = data.get('status', farm.status)
        farm.sector = data.get('sector', farm.sector)
        
        farm.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Farm updated successfully'
        })
        
    except FarmdetailsTbl.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Farm not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def delete_farm(request, farm_id):
    """Soft delete farm (mark as expunged)"""
    try:
        data = json.loads(request.body)
        farm = FarmdetailsTbl.objects.get(id=farm_id)
        
        farm.expunge = True
        farm.reason4expunge = data.get('reason', 'No reason provided')
        farm.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Farm deleted successfully'
        })
        
    except FarmdetailsTbl.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Farm not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_districts_by_region(request):
    """Get districts by region for dropdown"""
    region = request.GET.get('region', '')
    
    if region:
        districts = cocoaDistrict.objects.filter(
            farmdetailstbl__region=region
        ).distinct().values_list('district', flat=True)
    else:
        districts = cocoaDistrict.objects.all().values_list('district', flat=True)
    
    return JsonResponse({
        'success': True,
        'districts': list(districts)
    })