from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from portal.models import SectorModel, staffTbl
import json
from datetime import datetime
import csv
from django.http import HttpResponse
from django.db import transaction
from django.db import models

@login_required
def sector_management_page(request):
    """Main page for sector management"""
    context = {
        'page_title': 'Sector Management',
        'sectors': SectorModel.objects.all().order_by('-create_at'),
    }
    return render(request, 'portal/Farms/sector.html', context)

@login_required
def sector_api(request):
    """API endpoint for datatable - Server-side processing"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Base queryset
        queryset = SectorModel.objects.all().select_related(
            'created_by', 'modified_by'
        )
        
        # Search functionality
        if search_value:
            queryset = queryset.filter(
                Q(sector__icontains=search_value) |
                Q(Texture_co__icontains=str(search_value)) |
                Q(created_by__full_name__icontains=search_value) |
                Q(modified_by__full_name__icontains=search_value)
            )
        
        # Filter by size range if provided
        min_size = request.GET.get('min_size')
        max_size = request.GET.get('max_size')
        if min_size:
            queryset = queryset.filter(size_Ha__gte=float(min_size))
        if max_size:
            queryset = queryset.filter(size_Ha__lte=float(max_size))
        
        # Filter by pH range if provided
        min_ph = request.GET.get('min_ph')
        max_ph = request.GET.get('max_ph')
        if min_ph:
            queryset = queryset.filter(mean_pH__gte=float(min_ph))
        if max_ph:
            queryset = queryset.filter(mean_pH__lte=float(max_ph))
        
        # Ordering
        order_column = request.GET.get('order[0][column]', 0)
        order_dir = request.GET.get('order[0][dir]', 'desc')
        
        columns = ['sector', 'size_Ha', 'mean_pH', 'mean_OC', 'Texture_co', 'create_at', 'actions']
        order_field = columns[int(order_column)] if int(order_column) < len(columns) else 'sector'
        
        if order_dir == 'desc':
            order_field = f'-{order_field}'
        
        queryset = queryset.order_by(order_field)
        
        # Total records
        total_records = queryset.count()
        
        # Apply pagination
        queryset = queryset[start:start + length]
        
        # Prepare data
        data = []
        for sector in queryset:
            data.append({
                'id': sector.id,
                'sector': sector.sector,
                'size_Ha': round(sector.size_Ha, 2) if sector.size_Ha else 0,
                'mean_pH': round(sector.mean_pH, 2) if sector.mean_pH else 0,
                'mean_OC': round(sector.mean_OC, 2) if sector.mean_OC else 0,
                'Texture_co': sector.Texture_co if sector.Texture_co else 0,
                'created_at': sector.create_at.strftime('%Y-%m-%d %H:%M') if sector.create_at else None,
                'updated_at': sector.update_at.strftime('%Y-%m-%d %H:%M') if sector.update_at else None,
                'created_by': sector.created_by.full_name if sector.created_by else None,
                'modified_by': sector.modified_by.full_name if sector.modified_by else None,
                'has_geometry': 'Yes' if sector.geom else 'No',
            })
        
        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data
        })
        
    except Exception as e:
        print(f"Error in sector_api: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'message': f'Error fetching sectors: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_sector_details(request, sector_id):
    """Get single sector details"""
    try:
        sector = SectorModel.objects.get(id=sector_id)
        
        # Convert geometry to GeoJSON if exists
        geojson = None
        if sector.geom:
            geojson = {
                'type': 'Feature',
                'geometry': json.loads(sector.geom.geojson),
                'properties': {
                    'id': sector.id,
                    'sector': sector.sector
                }
            }
        
        data = {
            'id': sector.id,
            'sector': sector.sector,
            'size_Ha': sector.size_Ha,
            'mean_pH': sector.mean_pH,
            'mean_OC': sector.mean_OC,
            'Texture_co': sector.Texture_co,
            'created_at': sector.create_at.strftime('%Y-%m-%d %H:%M') if sector.create_at else None,
            'updated_at': sector.update_at.strftime('%Y-%m-%d %H:%M') if sector.update_at else None,
            'created_by': sector.created_by.full_name if sector.created_by else None,
            'modified_by': sector.modified_by.full_name if sector.modified_by else None,
            'geometry': geojson,
            'geometry_type': sector.geom.geom_type if sector.geom else None,
            'geometry_srid': sector.geom.srid if sector.geom else None,
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except SectorModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Sector not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def create_sector(request):
    """Create new sector"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if not data.get('sector'):
            return JsonResponse({'success': False, 'message': 'Sector name is required'})
        
        # Check if sector name already exists
        if SectorModel.objects.filter(sector=data['sector']).exists():
            return JsonResponse({'success': False, 'message': 'Sector with this name already exists'})
        
        # Get current user (staff)
        current_user = None
        if request.user.is_authenticated:
            try:
                current_user = staffTbl.objects.get(user=request.user)
            except staffTbl.DoesNotExist:
                pass
        
        # Create sector
        with transaction.atomic():
            sector = SectorModel.objects.create(
                sector=data['sector'],
                size_Ha=data.get('size_Ha'),
                mean_pH=data.get('mean_pH'),
                mean_OC=data.get('mean_OC'),
                Texture_co=data.get('Texture_co'),
                created_by=current_user,
                modified_by=current_user
            )
            
            # Handle geometry if provided (as GeoJSON)
            if data.get('geometry'):
                from django.contrib.gis.geos import GEOSGeometry
                geom = GEOSGeometry(json.dumps(data['geometry']))
                sector.geom = geom
                sector.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Sector created successfully',
            'sector_id': sector.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Error creating sector: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def update_sector(request, sector_id):
    """Update sector details"""
    try:
        data = json.loads(request.body)
        sector = SectorModel.objects.get(id=sector_id)
        
        # Check if sector name is being changed and already exists
        if data.get('sector') and data['sector'] != sector.sector:
            if SectorModel.objects.filter(sector=data['sector']).exists():
                return JsonResponse({'success': False, 'message': 'Sector with this name already exists'})
        
        # Get current user for modified_by
        current_user = None
        if request.user.is_authenticated:
            try:
                current_user = staffTbl.objects.get(user=request.user)
            except staffTbl.DoesNotExist:
                pass
        
        # Update fields
        with transaction.atomic():
            if data.get('sector'):
                sector.sector = data['sector']
            if 'size_Ha' in data:
                sector.size_Ha = data['size_Ha']
            if 'mean_pH' in data:
                sector.mean_pH = data['mean_pH']
            if 'mean_OC' in data:
                sector.mean_OC = data['mean_OC']
            if 'Texture_co' in data:
                sector.Texture_co = data['Texture_co']
            
            # Update geometry if provided
            if data.get('geometry'):
                from django.contrib.gis.geos import GEOSGeometry
                geom = GEOSGeometry(json.dumps(data['geometry']))
                sector.geom = geom
            elif data.get('remove_geometry'):
                sector.geom = None
            
            sector.modified_by = current_user
            sector.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Sector updated successfully'
        })
        
    except SectorModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Sector not found'}, status=404)
    except Exception as e:
        print(f"Error updating sector: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def delete_sector(request, sector_id):
    """Delete sector"""
    try:
        data = json.loads(request.body) if request.body else {}
        sector = SectorModel.objects.get(id=sector_id)
        
        # Optional: Check if sector is being used elsewhere
        # if sector.farm_set.exists():
        #     return JsonResponse({'success': False, 'message': 'Cannot delete sector that is assigned to farms'})
        
        sector_name = sector.sector
        sector.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Sector "{sector_name}" deleted successfully'
        })
        
    except SectorModel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Sector not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def export_sectors_csv(request):
    """Export sectors to CSV"""
    try:
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sectors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Sector Name', 'Size (Ha)', 'Mean pH', 'Mean OC', 'Texture', 'Has Geometry', 'Created At', 'Updated At'])
        
        sectors = SectorModel.objects.all()
        for sector in sectors:
            writer.writerow([
                sector.sector,
                sector.size_Ha,
                sector.mean_pH,
                sector.mean_OC,
                sector.Texture_co,
                'Yes' if sector.geom else 'No',
                sector.create_at.strftime('%Y-%m-%d %H:%M') if sector.create_at else '',
                sector.update_at.strftime('%Y-%m-%d %H:%M') if sector.update_at else ''
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def export_sectors_pdf(request):
    """Export sectors to PDF"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from io import BytesIO
        from datetime import datetime
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"Sectors Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Table data
        data = [['Sector', 'Size (Ha)', 'Mean pH', 'Mean OC', 'Texture', 'Has Geometry']]
        
        sectors = SectorModel.objects.all()
        for sector in sectors:
            data.append([
                sector.sector,
                f"{sector.size_Ha:.2f}" if sector.size_Ha else 'N/A',
                f"{sector.mean_pH:.2f}" if sector.mean_pH else 'N/A',
                f"{sector.mean_OC:.2f}" if sector.mean_OC else 'N/A',
                sector.Texture_co or 'N/A',
                'Yes' if sector.geom else 'No'
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="sectors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_sector_statistics(request):
    """Get statistics about sectors"""
    try:
        sectors = SectorModel.objects.all()
        print(f"Total sectors in database: {sectors.count()}")
        
        # Get texture distribution and convert to list of dicts
        texture_dist = list(sectors.values('Texture_co').annotate(
            count=models.Count('id')
        ).order_by('-count'))
        
        # Also get pH distribution
        ph_distribution = {
            'acidic': sectors.filter(mean_pH__lt=5.5).count(),
            'neutral': sectors.filter(mean_pH__gte=5.5, mean_pH__lte=7.5).count(),
            'alkaline': sectors.filter(mean_pH__gt=7.5).count()
        }
        
        # Get OC distribution
        oc_distribution = {
            'low': sectors.filter(mean_OC__lt=2).count(),
            'medium': sectors.filter(mean_OC__gte=2, mean_OC__lte=4).count(),
            'high': sectors.filter(mean_OC__gt=4).count()
        }
        
        # Get size distribution
        size_distribution = {
            'small': sectors.filter(size_Ha__lt=5).count(),
            'medium': sectors.filter(size_Ha__gte=5, size_Ha__lte=20).count(),
            'large': sectors.filter(size_Ha__gt=20).count()
        }
        
        stats = {
            'total_sectors': sectors.count(),
            'sectors_with_geometry': sectors.exclude(geom__isnull=True).count(),
            'avg_size': sectors.aggregate(avg=models.Avg('size_Ha'))['avg'],
            'avg_ph': sectors.aggregate(avg=models.Avg('mean_pH'))['avg'],
            'avg_oc': sectors.aggregate(avg=models.Avg('mean_OC'))['avg'],
            'min_size': sectors.aggregate(min=models.Min('size_Ha'))['min'],
            'max_size': sectors.aggregate(max=models.Max('size_Ha'))['max'],
            'min_ph': sectors.aggregate(min=models.Min('mean_pH'))['min'],
            'max_ph': sectors.aggregate(max=models.Max('mean_pH'))['max'],
            'min_oc': sectors.aggregate(min=models.Min('mean_OC'))['min'],
            'max_oc': sectors.aggregate(max=models.Max('mean_OC'))['max'],
            'total_area': sectors.aggregate(total=models.Sum('size_Ha'))['total'] or 0,
            'texture_distribution': texture_dist,
            'ph_distribution': ph_distribution,
            'oc_distribution': oc_distribution,
            'size_distribution': size_distribution
        }
        
        return JsonResponse({'success': True, 'stats': stats})
        
    except Exception as e:
        print(f"Error in get_sector_statistics: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)