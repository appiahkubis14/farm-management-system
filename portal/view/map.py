from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json
from portal.models import Farms, FarmdetailsTbl, cocoaDistrict
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from django.db import models

@login_required
def farm_mapping_page(request):
    """Main page for farm mapping"""
    farms = Farms.objects.all()
    farm_details = FarmdetailsTbl.objects.filter(expunge=False).select_related('districtTbl_foreignkey')
    districts = cocoaDistrict.objects.all()
    
    # Get stats for the sidebar
    total_farms = farms.count()
    total_farm_details = farm_details.count()
    farms_without_details = farms.exclude(farmdetailstbl__isnull=False).count()
    
    context = {
        'page_title': 'Farm Mapping & GIS',
        'total_farms': total_farms,
        'total_farm_details': total_farm_details,
        'farms_without_details': farms_without_details,
        'districts': districts,
        'status_choices': FarmdetailsTbl.STATUS_CHOICES,
    }
    return render(request, 'portal/Farms/map.html', context)

@login_required
@require_http_methods(["GET"])
def get_farm_geojson(request):
    """Get all farms as GeoJSON"""
    try:
        farms = Farms.objects.all()
        
        # Create GeoJSON FeatureCollection
        features = []
        for farm in farms:
            if farm.geom:
                # Get farm details if exists
                farm_detail = FarmdetailsTbl.objects.filter(farm_foreignkey=farm).first()
                
                # Create properties
                properties = {
                    'id': farm.id,
                    'farm_id': farm.farm_id or f'Farm-{farm.id}',
                    'has_details': farm_detail is not None,
                    'popup_content': f'<h5>Farm ID: {farm.farm_id or f"Farm-{farm.id}"}</h5>'
                }
                
                # Add details if available
                if farm_detail:
                    properties.update({
                        'farm_reference': farm_detail.farm_reference,
                        'farmer_name': farm_detail.farmername,
                        'region': farm_detail.region,
                        'district': farm_detail.district,
                        'location': farm_detail.location,
                        'farm_size': farm_detail.farm_size,
                        'status': farm_detail.status,
                        'sector': farm_detail.sector,
                        'year_established': farm_detail.year_of_establishment.strftime('%Y') if farm_detail.year_of_establishment else None,
                        'popup_content': f'''
                            <div class="farm-popup">
                                <h5>Farm: {farm_detail.farm_reference}</h5>
                                <p><strong>Farmer:</strong> {farm_detail.farmername}</p>
                                <p><strong>Location:</strong> {farm_detail.location}, {farm_detail.district}</p>
                                <p><strong>Size:</strong> {farm_detail.farm_size or "N/A"} acres</p>
                                <p><strong>Status:</strong> <span class="badge badge-{farm_detail.status.lower()}">{farm_detail.status}</span></p>
                                <p><strong>Sector:</strong> {farm_detail.sector or "N/A"}</p>
                                <div class="text-center mt-2">
                                    <a href="/farms/farm-details/" target="_blank" class="btn btn-sm btn-primary">View Details</a>
                                </div>
                            </div>
                        '''
                    })
                
                # Create feature
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(farm.geom.geojson),
                    'properties': properties
                }
                features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        return JsonResponse(geojson)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_district_boundaries(request):
    """Get district boundaries as GeoJSON"""
    try:
        districts = cocoaDistrict.objects.all()
        
        features = []
        for district in districts:
            if district.geom:
                # Count farms in this district
                farm_count = FarmdetailsTbl.objects.filter(
                    district=district.district, 
                    expunge=False
                ).count()
                
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(district.geom.geojson),
                    'properties': {
                        'district': district.district,
                        'district_code': district.district_code,
                        'farm_count': farm_count,
                        'area_sqkm': district.shape_area / 1000000 if district.shape_area else 0
                    }
                }
                features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        return JsonResponse(geojson)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_farm_stats(request):
    """Get farm statistics"""
    try:
        total_farms = Farms.objects.count()
        farms_with_details = Farms.objects.filter(farmdetailstbl__isnull=False).distinct().count()
        farms_without_details = total_farms - farms_with_details
        
        # Status distribution
        status_stats = FarmdetailsTbl.objects.filter(expunge=False)\
            .values('status')\
            .annotate(count=models.Count('id'))
        
        # District-wise distribution
        district_stats = FarmdetailsTbl.objects.filter(expunge=False)\
            .values('district')\
            .annotate(count=models.Count('id'))\
            .order_by('-count')[:10]
        
        # Size distribution
        small_farms = FarmdetailsTbl.objects.filter(
            expunge=False, 
            farm_size__lt=5
        ).count()
        medium_farms = FarmdetailsTbl.objects.filter(
            expunge=False, 
            farm_size__gte=5, 
            farm_size__lte=20
        ).count()
        large_farms = FarmdetailsTbl.objects.filter(
            expunge=False, 
            farm_size__gt=20
        ).count()
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_farms': total_farms,
                'farms_with_details': farms_with_details,
                'farms_without_details': farms_without_details,
                'status_distribution': list(status_stats),
                'top_districts': list(district_stats),
                'size_distribution': {
                    'small': small_farms,
                    'medium': medium_farms,
                    'large': large_farms
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def search_farms(request):
    """Search farms by various criteria"""
    try:
        data = json.loads(request.body)
        search_type = data.get('type', 'all')
        query = data.get('query', '')
        
        if search_type == 'farm_id':
            farms = Farms.objects.filter(
                Q(farm_id__icontains=query)
            )
        elif search_type == 'farmer_name':
            farms = Farms.objects.filter(
                farmdetailstbl__farmername__icontains=query,
                farmdetailstbl__expunge=False
            ).distinct()
        elif search_type == 'location':
            farms = Farms.objects.filter(
                farmdetailstbl__location__icontains=query,
                farmdetailstbl__expunge=False
            ).distinct()
        elif search_type == 'district':
            farms = Farms.objects.filter(
                farmdetailstbl__district__icontains=query,
                farmdetailstbl__expunge=False
            ).distinct()
        else:
            farms = Farms.objects.all()
        
        # Convert to GeoJSON
        features = []
        for farm in farms:
            if farm.geom:
                farm_detail = FarmdetailsTbl.objects.filter(farm_foreignkey=farm).first()
                
                properties = {
                    'id': farm.id,
                    'farm_id': farm.farm_id or f'Farm-{farm.id}',
                    'has_details': farm_detail is not None,
                }
                
                if farm_detail:
                    properties.update({
                        'farm_reference': farm_detail.farm_reference,
                        'farmer_name': farm_detail.farmername,
                        'district': farm_detail.district,
                        'location': farm_detail.location,
                    })
                
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(farm.geom.geojson),
                    'properties': properties
                }
                features.append(feature)
        
        return JsonResponse({
            'success': True,
            'count': len(features),
            'features': features
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["GET"])
def get_farm_by_id(request, farm_id):
    """Get specific farm details"""
    try:
        farm = Farms.objects.get(id=farm_id)
        farm_detail = FarmdetailsTbl.objects.filter(farm_foreignkey=farm).first()
        
        data = {
            'id': farm.id,
            'farm_id': farm.farm_id,
            'geom': json.loads(farm.geom.geojson) if farm.geom else None
        }
        
        if farm_detail:
            data['details'] = {
                'farm_reference': farm_detail.farm_reference,
                'farmer_name': farm_detail.farmername,
                'region': farm_detail.region,
                'district': farm_detail.district,
                'location': farm_detail.location,
                'farm_size': farm_detail.farm_size,
                'status': farm_detail.status,
                'sector': farm_detail.sector,
                'year_established': farm_detail.year_of_establishment.strftime('%Y-%m-%d') if farm_detail.year_of_establishment else None,
            }
        
        return JsonResponse({'success': True, 'data': data})
        
    except Farms.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Farm not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})