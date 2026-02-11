# views.py - Farm Mapping Views
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json
from portal.models import Farms, FarmdetailsTbl, projectTbl
from django.db import models

@login_required
def farm_mapping_page(request):
    """Main page for farm mapping"""
    farms = Farms.objects.all()
    farm_details = FarmdetailsTbl.objects.filter(expunge=False).select_related('projectTbl_foreignkey')
    projects = projectTbl.objects.all()
    
    # Get stats for the sidebar
    total_farms = farms.count()
    total_farm_details = farm_details.count()
    farms_without_details = farms.exclude(farmdetailstbl__isnull=False).count()
    
    context = {
        'page_title': 'Farm Mapping & GIS',
        'total_farms': total_farms,
        'total_farm_details': total_farm_details,
        'farms_without_details': farms_without_details,
        'projects': projects,
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
                    project_name = farm_detail.projectTbl_foreignkey.name if farm_detail.projectTbl_foreignkey else 'N/A'
                    properties.update({
                        'farm_reference': farm_detail.farm_reference,
                        'farmer_name': farm_detail.farmername,
                        'region': farm_detail.region,
                        'project': project_name,
                        'location': farm_detail.location,
                        'farm_size': farm_detail.farm_size,
                        'status': farm_detail.status,
                        'sector': farm_detail.sector,
                        'year_established': farm_detail.year_of_establishment.strftime('%Y') if farm_detail.year_of_establishment else None,
                        'popup_content': f'''
                            <div class="farm-popup">
                                <h5>Farm: {farm_detail.farm_reference}</h5>
                                <p><strong>Farmer:</strong> {farm_detail.farmername}</p>
                                <p><strong>Location:</strong> {farm_detail.location}</p>
                                <p><strong>Project:</strong> {project_name}</p>
                                <p><strong>Region:</strong> {farm_detail.region or "N/A"}</p>
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
def get_project_farms(request):
    """Get farms grouped by project"""
    try:
        projects = projectTbl.objects.all()
        
        project_data = []
        for project in projects:
            # Count farms in this project
            farm_count = FarmdetailsTbl.objects.filter(
                projectTbl_foreignkey=project, 
                expunge=False
            ).count()
            
            # Get farm details for this project
            farm_details = FarmdetailsTbl.objects.filter(
                projectTbl_foreignkey=project,
                expunge=False
            )[:5]  # Limit to 5 farms for the summary
            
            farms_list = []
            for farm in farm_details:
                farms_list.append({
                    'farm_reference': farm.farm_reference,
                    'farmer_name': farm.farmername,
                    'location': farm.location,
                    'farm_size': farm.farm_size,
                    'status': farm.status
                })
            
            project_data.append({
                'project_id': project.id,
                'project_name': project.name,
                'farm_count': farm_count,
                'recent_farms': farms_list
            })
        
        return JsonResponse({
            'success': True,
            'projects': project_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

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
        
        # Project-wise distribution
        project_stats = FarmdetailsTbl.objects.filter(expunge=False)\
            .values('projectTbl_foreignkey__name')\
            .annotate(count=models.Count('id'))\
            .order_by('-count')[:10]
        
        # Region-wise distribution
        region_stats = FarmdetailsTbl.objects.filter(expunge=False)\
            .exclude(region__isnull=True)\
            .exclude(region='')\
            .values('region')\
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
        
        # Sector distribution
        sector_stats = FarmdetailsTbl.objects.filter(
            expunge=False,
            sector__isnull=False
        ).values('sector')\
         .annotate(count=models.Count('id'))\
         .order_by('sector')
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_farms': total_farms,
                'farms_with_details': farms_with_details,
                'farms_without_details': farms_without_details,
                'status_distribution': list(status_stats),
                'project_distribution': list(project_stats),
                'region_distribution': list(region_stats),
                'size_distribution': {
                    'small': small_farms,
                    'medium': medium_farms,
                    'large': large_farms
                },
                'sector_distribution': list(sector_stats)
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
        elif search_type == 'project':
            farms = Farms.objects.filter(
                farmdetailstbl__projectTbl_foreignkey__name__icontains=query,
                farmdetailstbl__expunge=False
            ).distinct()
        elif search_type == 'farm_reference':
            farms = Farms.objects.filter(
                farmdetailstbl__farm_reference__icontains=query,
                farmdetailstbl__expunge=False
            ).distinct()
        elif search_type == 'region':
            farms = Farms.objects.filter(
                farmdetailstbl__region__icontains=query,
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
                    project_name = farm_detail.projectTbl_foreignkey.name if farm_detail.projectTbl_foreignkey else 'N/A'
                    properties.update({
                        'farm_reference': farm_detail.farm_reference,
                        'farmer_name': farm_detail.farmername,
                        'project': project_name,
                        'region': farm_detail.region,
                        'location': farm_detail.location,
                        'farm_size': farm_detail.farm_size,
                        'status': farm_detail.status,
                        'sector': farm_detail.sector
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
            project_name = farm_detail.projectTbl_foreignkey.name if farm_detail.projectTbl_foreignkey else 'N/A'
            data['details'] = {
                'farm_reference': farm_detail.farm_reference,
                'farmer_name': farm_detail.farmername,
                'region': farm_detail.region,
                'project': project_name,
                'project_id': farm_detail.projectTbl_foreignkey.id if farm_detail.projectTbl_foreignkey else None,
                'location': farm_detail.location,
                'farm_size': farm_detail.farm_size,
                'status': farm_detail.status,
                'sector': farm_detail.sector,
                'year_established': farm_detail.year_of_establishment.strftime('%Y-%m-%d') if farm_detail.year_of_establishment else None,
                'expunge': farm_detail.expunge,
                'reason4expunge': farm_detail.reason4expunge
            }
        
        return JsonResponse({'success': True, 'data': data})
        
    except Farms.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Farm not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["GET"])
def get_farms_by_project(request, project_id):
    """Get all farms for a specific project"""
    try:
        project = projectTbl.objects.get(id=project_id)
        
        # Get farm details for this project
        farm_details = FarmdetailsTbl.objects.filter(
            projectTbl_foreignkey=project,
            expunge=False
        ).select_related('farm_foreignkey')
        
        # Create GeoJSON
        features = []
        for farm_detail in farm_details:
            farm = farm_detail.farm_foreignkey
            if farm and farm.geom:
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(farm.geom.geojson),
                    'properties': {
                        'id': farm.id,
                        'farm_id': farm.farm_id or f'Farm-{farm.id}',
                        'farm_reference': farm_detail.farm_reference,
                        'farmer_name': farm_detail.farmername,
                        'region': farm_detail.region,
                        'location': farm_detail.location,
                        'farm_size': farm_detail.farm_size,
                        'status': farm_detail.status,
                        'sector': farm_detail.sector,
                        'year_established': farm_detail.year_of_establishment.strftime('%Y') if farm_detail.year_of_establishment else None,
                    }
                }
                features.append(feature)
        
        return JsonResponse({
            'success': True,
            'project': project.name,
            'count': len(features),
            'features': features
        })
        
    except projectTbl.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["GET"])
def get_farms_by_status(request, status):
    """Get farms by status"""
    try:
        # Validate status
        valid_statuses = [choice[0] for choice in FarmdetailsTbl.STATUS_CHOICES]
        if status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
        
        # Get farm details with this status
        farm_details = FarmdetailsTbl.objects.filter(
            status=status,
            expunge=False
        ).select_related('farm_foreignkey', 'projectTbl_foreignkey')
        
        # Create GeoJSON
        features = []
        status_stats = {
            'count': 0,
            'total_area': 0,
            'projects': {}
        }
        
        for farm_detail in farm_details:
            farm = farm_detail.farm_foreignkey
            if farm and farm.geom:
                project_name = farm_detail.projectTbl_foreignkey.name if farm_detail.projectTbl_foreignkey else 'N/A'
                
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(farm.geom.geojson),
                    'properties': {
                        'id': farm.id,
                        'farm_id': farm.farm_id or f'Farm-{farm.id}',
                        'farm_reference': farm_detail.farm_reference,
                        'farmer_name': farm_detail.farmername,
                        'project': project_name,
                        'region': farm_detail.region,
                        'location': farm_detail.location,
                        'farm_size': farm_detail.farm_size,
                        'sector': farm_detail.sector,
                    }
                }
                features.append(feature)
                
                # Update stats
                status_stats['count'] += 1
                status_stats['total_area'] += farm_detail.farm_size or 0
                
                # Update project stats
                if project_name not in status_stats['projects']:
                    status_stats['projects'][project_name] = {
                        'count': 1,
                        'total_area': farm_detail.farm_size or 0
                    }
                else:
                    status_stats['projects'][project_name]['count'] += 1
                    status_stats['projects'][project_name]['total_area'] += farm_detail.farm_size or 0
        
        return JsonResponse({
            'success': True,
            'status': status,
            'count': len(features),
            'stats': status_stats,
            'features': features
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["GET"])
def export_farms_geojson(request):
    """Export all farms as GeoJSON file"""
    try:
        farms = Farms.objects.all()
        
        features = []
        for farm in farms:
            if farm.geom:
                farm_detail = FarmdetailsTbl.objects.filter(farm_foreignkey=farm).first()
                
                properties = {
                    'id': farm.id,
                    'farm_id': farm.farm_id or f'Farm-{farm.id}',
                }
                
                if farm_detail:
                    project_name = farm_detail.projectTbl_foreignkey.name if farm_detail.projectTbl_foreignkey else 'N/A'
                    properties.update({
                        'farm_reference': farm_detail.farm_reference,
                        'farmer_name': farm_detail.farmername,
                        'region': farm_detail.region,
                        'project': project_name,
                        'location': farm_detail.location,
                        'farm_size': farm_detail.farm_size,
                        'status': farm_detail.status,
                        'sector': farm_detail.sector,
                        'year_established': farm_detail.year_of_establishment.strftime('%Y-%m-%d') if farm_detail.year_of_establishment else None,
                    })
                
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
        
        # Create response with download header
        response = JsonResponse(geojson)
        response['Content-Disposition'] = 'attachment; filename="farms_export.geojson"'
        response['Content-Type'] = 'application/geo+json'
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)