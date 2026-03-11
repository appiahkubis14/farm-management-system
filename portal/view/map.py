# views.py - Sector Mapping Views (replacing farm mapping)
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg, Sum, F, FloatField, Min, Max
import json
from portal.models import SectorModel, projectTbl, FarmdetailsTbl
from django.db import models
from django.utils import timezone
# lets import require_math_methods
from django.views.decorators.http import require_http_methods as require_math_methods

@login_required
def farm_mapping_page(request):
    """Main page for sector mapping (renamed but showing sectors)"""
    # Get all sectors instead of farms
    sectors = SectorModel.objects.all().order_by('sector')
    
    # Get stats for the sidebar
    total_sectors = sectors.count()
    sectors_with_geometry = sectors.exclude(geom__isnull=True).count()
    sectors_without_geometry = total_sectors - sectors_with_geometry
    
    # Get projects (maintain original variable names)
    projects = projectTbl.objects.all()
    
    # Calculate some sector statistics
    total_area = sectors.aggregate(total=Sum('size_Ha'))['total'] or 0
    avg_ph = sectors.aggregate(avg=Avg('mean_pH'))['avg'] or 0
    avg_oc = sectors.aggregate(avg=Avg('mean_OC'))['avg'] or 0
    
    context = {
        'page_title': 'Sector Mapping & GIS',
        'total_farms': total_sectors,  # Maintain variable name but show sectors
        'total_farm_details': sectors_with_geometry,  # Sectors with geometry
        'farms_without_details': sectors_without_geometry,  # Sectors without geometry
        'total_area': round(total_area, 2),
        'avg_ph': round(avg_ph, 2),
        'avg_oc': round(avg_oc, 2),
        'projects': projects,
        'status_choices': FarmdetailsTbl.STATUS_CHOICES,  # Keep for compatibility
    }
    return render(request, 'portal/Farms/map.html', context)

@login_required
@require_http_methods(["GET"])
def get_farm_geojson(request):
    """Get all sectors as GeoJSON (maintaining function name)"""
    try:
        sectors = SectorModel.objects.all()
        
        # Create GeoJSON FeatureCollection
        features = []
        for sector in sectors:
            if sector.geom:
                # Create properties
                properties = {
                    'id': sector.id,
                    'sector_name': sector.sector,
                    'type': 'sector',
                    'popup_content': f'''
                        <div class="sector-popup">
                            <h5>Sector: {sector.sector}</h5>
                            <table class="table table-sm table-borderless">
                                <tr>
                                    <th>Size:</th>
                                    <td>{sector.size_Ha or 'N/A'} Ha</td>
                                </tr>
                                <tr>
                                    <th>Mean pH:</th>
                                    <td>{sector.mean_pH or 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th>Mean OC:</th>
                                    <td>{sector.mean_OC or 'N/A'}%</td>
                                </tr>
                                <tr>
                                    <th>Texture:</th>
                                    <td>{sector.Texture_co or 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th>Created:</th>
                                    <td>{sector.create_at.strftime('%Y-%m-%d') if sector.create_at else 'N/A'}</td>
                                </tr>
                            </table>
                            <div class="text-center mt-2">
                                <button class="btn btn-sm btn-primary view-sector-btn" data-id="{sector.id}">
                                    <i class="fas fa-eye"></i> View Details
                                </button>
                            </div>
                        </div>
                    '''
                }
                
                # Add all sector data to properties
                properties.update({
                    'size_Ha': sector.size_Ha,
                    'mean_pH': sector.mean_pH,
                    'mean_OC': sector.mean_OC,
                    'texture': sector.Texture_co,
                    'created_at': sector.create_at.strftime('%Y-%m-%d %H:%M') if sector.create_at else None,
                    'updated_at': sector.update_at.strftime('%Y-%m-%d %H:%M') if sector.update_at else None,
                    'created_by': sector.created_by.full_name if sector.created_by else None,
                    'modified_by': sector.modified_by.full_name if sector.modified_by else None,
                })
                
                # Create feature
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(sector.geom.geojson),
                    'properties': properties
                }
                features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        return JsonResponse(geojson)
        
    except Exception as e:
        print(f'Error in get_farm_geojson: {str(e)}')
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_project_farms(request):
    """Get sectors grouped by texture/characteristics (maintaining function name)"""
    try:
        # Group sectors by texture instead of projects
        texture_groups = SectorModel.objects.exclude(
            Texture_co__isnull=True
        ).exclude(
            Texture_co=''
        ).values('Texture_co').annotate(
            sector_count=Count('id'),
            total_area=Sum('size_Ha'),
            avg_ph=Avg('mean_pH'),
            avg_oc=Avg('mean_OC')
        ).order_by('-sector_count')
        
        texture_data = []
        for group in texture_groups:
            # Get sample sectors for this texture
            sectors = SectorModel.objects.filter(
                Texture_co=group['Texture_co']
            )[:5]  # Limit to 5 sectors for the summary
            
            sectors_list = []
            for sector in sectors:
                sectors_list.append({
                    'id': sector.id,
                    'sector': sector.sector,
                    'size_Ha': sector.size_Ha,
                    'mean_pH': sector.mean_pH,
                    'mean_OC': sector.mean_OC
                })
            
            texture_data.append({
                'project_id': group['Texture_co'],  # Using texture as "project_id"
                'project_name': f"Texture: {group['Texture_co']}",  # Using texture as "project_name"
                'farm_count': group['sector_count'],
                'total_area': round(group['total_area'] or 0, 2),
                'avg_ph': round(group['avg_ph'] or 0, 2),
                'avg_oc': round(group['avg_oc'] or 0, 2),
                'recent_farms': sectors_list
            })
        
        return JsonResponse({
            'success': True,
            'projects': texture_data
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_math_methods(["GET"])
def get_farm_stats(request):
    """Get sector statistics (maintaining function name)"""
    try:
        total_sectors = SectorModel.objects.count()
        sectors_with_geometry = SectorModel.objects.exclude(geom__isnull=True).count()
        sectors_without_geometry = total_sectors - sectors_with_geometry
        
        # Texture distribution (replacing status distribution)
        texture_stats = SectorModel.objects.exclude(
            Texture_co__isnull=True
        ).exclude(
            Texture_co=''
        ).values('Texture_co').annotate(
            count=Count('id'),
            total_area=Sum('size_Ha'),
            avg_ph=Avg('mean_pH'),
            avg_oc=Avg('mean_OC')
        ).order_by('-count')
        
        # Size distribution (using size_Ha)
        small_sectors = SectorModel.objects.filter(
            size_Ha__lt=5
        ).count() if SectorModel.objects.exists() else 0
        medium_sectors = SectorModel.objects.filter(
            size_Ha__gte=5, 
            size_Ha__lte=20
        ).count() if SectorModel.objects.exists() else 0
        large_sectors = SectorModel.objects.filter(
            size_Ha__gt=20
        ).count() if SectorModel.objects.exists() else 0
        
        # pH distribution categories
        acidic_sectors = SectorModel.objects.filter(
            mean_pH__lt=5.5
        ).count() if SectorModel.objects.exists() else 0
        neutral_sectors = SectorModel.objects.filter(
            mean_pH__gte=5.5, 
            mean_pH__lte=7.5
        ).count() if SectorModel.objects.exists() else 0
        alkaline_sectors = SectorModel.objects.filter(
            mean_pH__gt=7.5
        ).count() if SectorModel.objects.exists() else 0
        
        # OC distribution
        low_oc_sectors = SectorModel.objects.filter(
            mean_OC__lt=2
        ).count() if SectorModel.objects.exists() else 0
        medium_oc_sectors = SectorModel.objects.filter(
            mean_OC__gte=2, 
            mean_OC__lte=4
        ).count() if SectorModel.objects.exists() else 0
        high_oc_sectors = SectorModel.objects.filter(
            mean_OC__gt=4
        ).count() if SectorModel.objects.exists() else 0
        
        # Overall statistics
        overall_stats = SectorModel.objects.aggregate(
            total_area=Sum('size_Ha'),
            avg_ph=Avg('mean_pH'),
            avg_oc=Avg('mean_OC'),
            min_ph=Min('mean_pH'),
            max_ph=Max('mean_pH'),
            min_oc=Min('mean_OC'),
            max_oc=Max('mean_OC'),
            min_size=Min('size_Ha'),
            max_size=Max('size_Ha')
        )

        print(f"Total Sectors: {total_sectors}, With Geometry: {sectors_with_geometry}, Without Geometry: {sectors_without_geometry}")
        print(f"Texture Stats: {list(texture_stats)}")
        print(f"Overall Stats: {overall_stats}")
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_farms': total_sectors,
                'farms_with_details': sectors_with_geometry,
                'farms_without_details': sectors_without_geometry,
                'status_distribution': list(texture_stats),  # Replacing status with texture
                'project_distribution': list(texture_stats),  # Replacing project with texture
                'region_distribution': [],  # Can be populated if needed
                'size_distribution': {
                    'small': small_sectors,
                    'medium': medium_sectors,
                    'large': large_sectors
                },
                'sector_distribution': [],  # Can be populated if needed
                'ph_distribution': {
                    'acidic': acidic_sectors,
                    'neutral': neutral_sectors,
                    'alkaline': alkaline_sectors
                },
                'oc_distribution': {
                    'low': low_oc_sectors,
                    'medium': medium_oc_sectors,
                    'high': high_oc_sectors
                },
                'overall': {
                    'total_area': round(overall_stats['total_area'] or 0, 2),
                    'avg_ph': round(overall_stats['avg_ph'] or 0, 2),
                    'avg_oc': round(overall_stats['avg_oc'] or 0, 2),
                    'ph_range': f"{round(overall_stats['min_ph'] or 0, 2)} - {round(overall_stats['max_ph'] or 0, 2)}",
                    'oc_range': f"{round(overall_stats['min_oc'] or 0, 2)}% - {round(overall_stats['max_oc'] or 0, 2)}%",
                    'size_range': f"{round(overall_stats['min_size'] or 0, 2)} - {round(overall_stats['max_size'] or 0, 2)} Ha"
                }
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def search_farms(request):
    """Search sectors by various criteria (maintaining function name)"""
    try:
        data = json.loads(request.body)
        search_type = data.get('type', 'all')
        query = data.get('query', '')
        
        if search_type == 'farm_id':
            # Search by sector name
            sectors = SectorModel.objects.filter(
                Q(sector__icontains=query)
            )
        elif search_type == 'farmer_name':
            # Search by texture (since farmer name doesn't exist)
            sectors = SectorModel.objects.filter(
                Q(Texture_co__icontains=query)
            )
        elif search_type == 'location':
            # Search by pH range or other numeric fields
            try:
                if ' - ' in query:
                    min_val, max_val = query.split(' - ')
                    sectors = SectorModel.objects.filter(
                        Q(mean_pH__gte=float(min_val)) & 
                        Q(mean_pH__lte=float(max_val))
                    )
                else:
                    sectors = SectorModel.objects.filter(
                        Q(mean_pH__icontains=query) |
                        Q(mean_OC__icontains=query) |
                        Q(size_Ha__icontains=query)
                    )
            except:
                sectors = SectorModel.objects.none()
        elif search_type == 'project':
            # Search by size range or other attributes
            try:
                sectors = SectorModel.objects.filter(
                    Q(size_Ha__icontains=query)
                )
            except:
                sectors = SectorModel.objects.none()
        elif search_type == 'farm_reference':
            # Search by sector name (exact match)
            sectors = SectorModel.objects.filter(
                Q(sector__icontains=query)
            )
        elif search_type == 'region':
            # Search by texture
            sectors = SectorModel.objects.filter(
                Q(Texture_co__icontains=query)
            )
        else:
            # Search all fields
            sectors = SectorModel.objects.filter(
                Q(sector__icontains=query) |
                Q(Texture_co__icontains=query) |
                Q(size_Ha__icontains=query) |
                Q(mean_pH__icontains=query) |
                Q(mean_OC__icontains=query)
            )
        
        # Convert to GeoJSON
        features = []
        for sector in sectors:
            if sector.geom:
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(sector.geom.geojson),
                    'properties': {
                        'id': sector.id,
                        'sector_name': sector.sector,
                        'size_Ha': sector.size_Ha,
                        'mean_pH': sector.mean_pH,
                        'mean_OC': sector.mean_OC,
                        'texture': sector.Texture_co,
                        'created_at': sector.create_at.strftime('%Y-%m-%d') if sector.create_at else None,
                        'has_geometry': True
                    }
                }
                features.append(feature)
        
        return JsonResponse({
            'success': True,
            'count': len(features),
            'features': features
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["GET"])
def get_farm_by_id(request, farm_id):
    """Get specific sector details (maintaining function name)"""
    try:
        sector = SectorModel.objects.get(id=farm_id)
        
        data = {
            'id': sector.id,
            'farm_id': sector.sector,  # Using sector name as farm_id
            'geom': json.loads(sector.geom.geojson) if sector.geom else None,
            'details': {
                'farm_reference': sector.sector,
                'farmer_name': sector.Texture_co or 'N/A',  # Using texture as farmer_name
                'region': f"{sector.size_Ha or 'N/A'} Ha",  # Using size as region
                'project': f"pH: {sector.mean_pH or 'N/A'}",  # Using pH as project
                'project_id': sector.id,
                'location': f"OC: {sector.mean_OC or 'N/A'}%",  # Using OC as location
                'farm_size': sector.size_Ha,
                'status': 'Active' if sector.id else 'Inactive',  # Default status
                'sector': sector.sector,
                'year_established': sector.create_at.strftime('%Y-%m-%d') if sector.create_at else None,
                'expunge': False,
                'reason4expunge': None,
                # Add actual sector data
                'mean_pH': sector.mean_pH,
                'mean_OC': sector.mean_OC,
                'texture': sector.Texture_co,
                'created_by': sector.created_by.full_name if sector.created_by else None,
                'modified_by': sector.modified_by.full_name if sector.modified_by else None,
                'created_at': sector.create_at.strftime('%Y-%m-%d %H:%M') if sector.create_at else None,
                'updated_at': sector.update_at.strftime('%Y-%m-%d %H:%M') if sector.update_at else None
            }
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except SectorModel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sector not found'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["GET"])
def get_farms_by_project(request, project_id):
    """Get sectors by texture (maintaining function name and signature)"""
    try:
        # project_id here is actually texture value
        texture = project_id if isinstance(project_id, str) else str(project_id)
        
        sectors = SectorModel.objects.filter(
            Texture_co__iexact=texture
        )
        
        # Create GeoJSON
        features = []
        texture_stats = {
            'count': 0,
            'total_area': 0,
            'avg_ph': 0,
            'avg_oc': 0
        }
        
        total_ph = 0
        total_oc = 0
        
        for sector in sectors:
            if sector and sector.geom:
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(sector.geom.geojson),
                    'properties': {
                        'id': sector.id,
                        'farm_id': sector.sector,
                        'farm_reference': sector.sector,
                        'farmer_name': sector.Texture_co,
                        'region': f"{sector.size_Ha or 'N/A'} Ha",
                        'location': f"pH: {sector.mean_pH or 'N/A'}",
                        'farm_size': sector.size_Ha,
                        'status': 'Active',
                        'sector': sector.sector,
                        'year_established': sector.create_at.strftime('%Y') if sector.create_at else None,
                        'mean_pH': sector.mean_pH,
                        'mean_OC': sector.mean_OC
                    }
                }
                features.append(feature)
                
                # Update stats
                texture_stats['count'] += 1
                texture_stats['total_area'] += sector.size_Ha or 0
                if sector.mean_pH:
                    total_ph += sector.mean_pH
                if sector.mean_OC:
                    total_oc += sector.mean_OC
        
        if texture_stats['count'] > 0:
            texture_stats['avg_ph'] = round(total_ph / texture_stats['count'], 2)
            texture_stats['avg_oc'] = round(total_oc / texture_stats['count'], 2)
        
        return JsonResponse({
            'success': True,
            'project': f"Texture: {texture}",
            'count': len(features),
            'stats': texture_stats,
            'features': features
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["GET"])
def get_farms_by_status(request, status):
    """Get sectors by size range or pH range (maintaining function name)"""
    try:
        # Parse status to determine what to filter
        if status == 'Treatment':
            # Sectors with pH < 5.5 (acidic)
            sectors = SectorModel.objects.filter(
                mean_pH__lt=5.5,
                mean_pH__isnull=False
            )
            filter_type = 'acidic_soils'
        elif status == 'Establishment':
            # Small sectors (< 10 Ha)
            sectors = SectorModel.objects.filter(
                size_Ha__lt=10,
                size_Ha__isnull=False
            )
            filter_type = 'small_sectors'
        elif status == 'Maintenance':
            # Sectors with good conditions (pH 5.5-7.5, OC > 2)
            sectors = SectorModel.objects.filter(
                mean_pH__gte=5.5,
                mean_pH__lte=7.5,
                mean_OC__gt=2
            )
            filter_type = 'optimal_conditions'
        else:
            # Default - all sectors
            sectors = SectorModel.objects.all()
            filter_type = 'all_sectors'
        
        # Create GeoJSON
        features = []
        status_stats = {
            'count': 0,
            'total_area': 0,
            'avg_ph': 0,
            'avg_oc': 0,
            'textures': {}
        }
        
        total_ph = 0
        total_oc = 0
        
        for sector in sectors:
            if sector.geom:
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(sector.geom.geojson),
                    'properties': {
                        'id': sector.id,
                        'farm_id': sector.sector,
                        'farm_reference': sector.sector,
                        'farmer_name': sector.Texture_co or 'Unknown',
                        'project': f"pH: {sector.mean_pH or 'N/A'}",
                        'region': f"{sector.size_Ha or 'N/A'} Ha",
                        'location': f"OC: {sector.mean_OC or 'N/A'}%",
                        'farm_size': sector.size_Ha,
                        'status': status,
                        'sector': sector.sector,
                        'mean_pH': sector.mean_pH,
                        'mean_OC': sector.mean_OC,
                        'texture': sector.Texture_co
                    }
                }
                features.append(feature)
                
                # Update stats
                status_stats['count'] += 1
                status_stats['total_area'] += sector.size_Ha or 0
                if sector.mean_pH:
                    total_ph += sector.mean_pH
                if sector.mean_OC:
                    total_oc += sector.mean_OC
                
                # Update texture stats
                texture = sector.Texture_co or 'Unknown'
                if texture not in status_stats['textures']:
                    status_stats['textures'][texture] = 1
                else:
                    status_stats['textures'][texture] += 1
        
        if status_stats['count'] > 0:
            status_stats['avg_ph'] = round(total_ph / status_stats['count'], 2) if total_ph > 0 else 0
            status_stats['avg_oc'] = round(total_oc / status_stats['count'], 2) if total_oc > 0 else 0
        
        return JsonResponse({
            'success': True,
            'status': status,
            'filter_type': filter_type,
            'count': len(features),
            'stats': status_stats,
            'features': features
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["GET"])
def export_farms_geojson(request):
    """Export all sectors as GeoJSON file (maintaining function name)"""
    try:
        sectors = SectorModel.objects.all()
        
        features = []
        for sector in sectors:
            if sector.geom:
                properties = {
                    'id': sector.id,
                    'sector_name': sector.sector,
                    'size_Ha': sector.size_Ha,
                    'mean_pH': sector.mean_pH,
                    'mean_OC': sector.mean_OC,
                    'texture': sector.Texture_co,
                    'created_at': sector.create_at.strftime('%Y-%m-%d %H:%M') if sector.create_at else None,
                    'updated_at': sector.update_at.strftime('%Y-%m-%d %H:%M') if sector.update_at else None,
                    'created_by': sector.created_by.full_name if sector.created_by else None,
                    'modified_by': sector.modified_by.full_name if sector.modified_by else None,
                }
                
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(sector.geom.geojson),
                    'properties': properties
                }
                features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'export_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_sectors': len(features),
                'total_area': round(sum(f['properties'].get('size_Ha') or 0 for f in features), 2)
            }
        }
        
        # Create response with download header
        response = JsonResponse(geojson)
        response['Content-Disposition'] = f'attachment; filename="sectors_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.geojson"'
        response['Content-Type'] = 'application/geo+json'
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Optional: Add a helper view to get sector details for the popup
@login_required
@require_http_methods(["GET"])
def get_sector_details_popup(request, sector_id):
    """Get sector details for popup display"""
    try:
        sector = SectorModel.objects.get(id=sector_id)
        
        html = f'''
        <div class="sector-popup-details">
            <h5>{sector.sector}</h5>
            <hr>
            <table class="table table-sm table-borderless">
                <tr>
                    <th>Size:</th>
                    <td>{sector.size_Ha or 'N/A'} Ha</td>
                </tr>
                <tr>
                    <th>Mean pH:</th>
                    <td>{sector.mean_pH or 'N/A'}</td>
                </tr>
                <tr>
                    <th>Mean OC:</th>
                    <td>{sector.mean_OC or 'N/A'}%</td>
                </tr>
                <tr>
                    <th>Texture:</th>
                    <td>{sector.Texture_co or 'N/A'}</td>
                </tr>
                <tr>
                    <th>Created:</th>
                    <td>{sector.create_at.strftime('%Y-%m-%d') if sector.create_at else 'N/A'}</td>
                </tr>
                <tr>
                    <th>Created By:</th>
                    <td>{sector.created_by.full_name if sector.created_by else 'N/A'}</td>
                </tr>
            </table>
        </div>
        '''
        
        return JsonResponse({
            'success': True,
            'html': html,
            'sector': {
                'id': sector.id,
                'name': sector.sector,
                'size': sector.size_Ha,
                'ph': sector.mean_pH,
                'oc': sector.mean_OC,
                'texture': sector.Texture_co
            }
        })
        
    except SectorModel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sector not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})