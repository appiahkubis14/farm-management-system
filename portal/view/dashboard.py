import json
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Avg, Max, Min, F, FloatField, IntegerField, DateField, DateTimeField
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, datetime, timedelta
from collections import defaultdict

from portal.models import (
    # Personnel & Staff
    IrrigationModel, PersonnelModel, SectorModel, staffTbl, PersonnelAssignmentModel,
    
    # Contractors
    contractorsTbl, contratorDistrictAssignment, ContractorCertificateModel, ContractorCertificateVerificationModel,
    
    # Farms & Activities
    FarmdetailsTbl, Activities, DailyReportingModel, ActivityReportingModel,
    
    # Districts & Regions
    cocoaDistrict, Region, Community, projectTbl,
    QR_CodeModel, GrowthMonitoringModel
)

# ============== DASHBOARD VIEWS ==============
@login_required
def general_dashboard(request):
    """Render the main dashboard with all system statistics - Using only provided models"""
    
    # Get counts for different personnel types
    ra_count = PersonnelModel.objects.filter(
         
        personnel_type='Rehab Assistant'
    ).count()
    
    rt_count = PersonnelModel.objects.filter(
         
        personnel_type='Rehab Technician'
    ).count()
    
    # Staff counts (Project Officers, Coordinators, etc from staffTbl)
    po_count = staffTbl.objects.filter(
        delete_field='no'
    ).filter(
        Q(staffid__icontains='PO-') | Q(staffid__icontains='PC-')
    ).count()
    
    # Total staff (excluding those who might be in PersonnelModel)
    staff_count = staffTbl.objects.all().count()
    total_personnel = PersonnelModel.objects.all().count()
    
    # Sector Statistics (instead of Farms)
    total_sectors = SectorModel.objects.all().count()
    
    # Get total area from sectors
    total_sector_area = SectorModel.objects.filter(
         
        size_Ha__isnull=False
    ).aggregate(
        total=Sum('size_Ha')
    )['total'] or 0
    
    # Average soil metrics
    avg_ph = SectorModel.objects.filter(
         
        mean_pH__isnull=False
    ).aggregate(
        avg=Avg('mean_pH')
    )['avg'] or 0
    
    avg_oc = SectorModel.objects.filter(
         
        mean_OC__isnull=False
    ).aggregate(
        avg=Avg('mean_OC')
    )['avg'] or 0
    
    # Growth Monitoring Statistics
    total_growth_records = GrowthMonitoringModel.objects.all().count()
    avg_plant_height = GrowthMonitoringModel.objects.filter(
         
        height__isnull=False
    ).aggregate(
        avg=Avg('height')
    )['avg'] or 0
    
    avg_leaves = GrowthMonitoringModel.objects.filter(
         
        number_of_leaves__isnull=False
    ).aggregate(
        avg=Avg('number_of_leaves')
    )['avg'] or 0
    
    # QR Code Statistics
    total_qr_codes = QR_CodeModel.objects.all().count()
    used_qr_codes = QR_CodeModel.objects.filter( is_used=True).count()
    active_qr_codes = QR_CodeModel.objects.filter( is_active=True).count()
    
    # Assignment statistics
    active_assignments = PersonnelAssignmentModel.objects.filter(
         
        status__in=[1, 2]  # Submitted or Approved
    ).count()
    
    pending_assignments = PersonnelAssignmentModel.objects.filter(
         
        status=0  # Pending
    ).count()
    
    total_assignments = PersonnelAssignmentModel.objects.all().count()
    
    # Contractor statistics
    total_contractors = contractorsTbl.objects.all().count()
    
    # Get certified contractors through certificate model
    certified_contractors = ContractorCertificateModel.objects.filter(
        
        status='Verified'
    ).values('contractor').distinct().count()
    
    # Activity statistics (Daily and Activity Reporting)
    total_daily_reports = DailyReportingModel.objects.all().count()
    total_activity_reports = ActivityReportingModel.objects.all().count()
    
    daily_reports_today = DailyReportingModel.objects.filter(
        
        reporting_date=date.today()
    ).count()
    
    activity_reports_today = ActivityReportingModel.objects.filter(
        
        reporting_date=date.today()
    ).count()
    
    # Total area covered in reports
    total_area_covered_daily = DailyReportingModel.objects.filter(
        delete_field='no'
    ).aggregate(
        total=Sum('area_covered_ha')
    )['total'] or 0
    
    total_area_covered_activity = ActivityReportingModel.objects.filter(
        delete_field='no'
    ).aggregate(
        total=Sum('area_covered_ha')
    )['total'] or 0
    
    # Irrigation statistics
    total_irrigation_records = IrrigationModel.objects.all().count()
    total_water_volume = IrrigationModel.objects.filter(
        delete_field='no'
    ).aggregate(
        total=Sum('water_volume')
    )['total'] or 0
    
    # District and community statistics
    total_districts = cocoaDistrict.objects.all().count()
    total_regions = Region.objects.all().count()
    total_communities = Community.objects.all().count()
    total_projects = projectTbl.objects.all().count()
    
    # Activity types
    total_activities = Activities.objects.all().count()
    
    context = {
        # Personnel Stats
        'total_personnel': total_personnel,
        'ra_count': ra_count,
        'rt_count': rt_count,
        'po_count': po_count,
        'staff_count': staff_count,
        
        # Sector Stats (replacing farms)
        'total_sectors': total_sectors,
        'total_sector_area': round(total_sector_area, 2),
        'avg_ph': round(avg_ph, 2),
        'avg_oc': round(avg_oc, 2),
        
        # Growth Monitoring Stats
        'total_growth_records': total_growth_records,
        'avg_plant_height': round(avg_plant_height, 2),
        'avg_leaves': round(avg_leaves, 1),
        
        # QR Code Stats
        'total_qr_codes': total_qr_codes,
        'used_qr_codes': used_qr_codes,
        'active_qr_codes': active_qr_codes,
        'qr_usage_percentage': round((used_qr_codes / total_qr_codes * 100), 1) if total_qr_codes > 0 else 0,
        
        # Assignment Stats
        'total_assignments': total_assignments,
        'active_assignments': active_assignments,
        'pending_assignments': pending_assignments,
        
        # Contractor Stats
        'total_contractors': total_contractors,
        'certified_contractors': certified_contractors,
        
        # Report Stats
        'total_daily_reports': total_daily_reports,
        'total_activity_reports': total_activity_reports,
        'daily_reports_today': daily_reports_today,
        'activity_reports_today': activity_reports_today,
        'total_area_covered': round(total_area_covered_daily + total_area_covered_activity, 2),
        
        # Irrigation Stats
        'total_irrigation_records': total_irrigation_records,
        'total_water_volume': round(total_water_volume, 2),
        
        # Geographic Stats
        'total_districts': total_districts,
        'total_regions': total_regions,
        'total_communities': total_communities,
        'total_projects': total_projects,
        'total_activities': total_activities,
        
        # Current date/time
        'current_date': date.today().strftime('%B %d, %Y'),
        'current_time': datetime.now().strftime('%H:%M'),
    }
    
    return render(request, 'portal/dashboard/general_dashboard.html', context)


@require_http_methods(["GET"])
def get_dashboard_stats(request):
    """API endpoint to get real-time dashboard statistics - Using only provided models"""
    try:
        # Get date range from request (default to last 30 days)
        days = int(request.GET.get('days', 30))
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Personnel Statistics
        personnel_stats = {
            'total': PersonnelModel.objects.all().count(),
            'by_type': list(PersonnelModel.objects.all()
                           .values('personnel_type')
                           .annotate(count=Count('id'))
                           .order_by('-count')),
            'by_gender': list(PersonnelModel.objects.all()
                            .values('gender')
                            .annotate(count=Count('id'))),
            'by_district': list(PersonnelModel.objects.filter( district__isnull=False)
                               .values('district__name')
                               .annotate(count=Count('id'))
                               .order_by('-count')[:10]),
        }
        
        # Staff Statistics
        staff_stats = {
            'total': staffTbl.objects.all().count(),
            'by_project': list(staffTbl.objects.filter( projectTbl_foreignkey__isnull=False)
                              .values('projectTbl_foreignkey__name')
                              .annotate(count=Count('id'))
                              .order_by('-count')[:10]),
        }
        
        # Sector Statistics
        sector_stats = {
            'total': SectorModel.objects.all().count(),
            'total_area': float(SectorModel.objects.filter( size_Ha__isnull=False)
                               .aggregate(total=Sum('size_Ha'))['total'] or 0),
            'avg_ph': float(SectorModel.objects.filter( mean_pH__isnull=False)
                           .aggregate(avg=Avg('mean_pH'))['avg'] or 0),
            'avg_oc': float(SectorModel.objects.filter( mean_OC__isnull=False)
                           .aggregate(avg=Avg('mean_OC'))['avg'] or 0),
            'by_district': list(SectorModel.objects.all()
                               .annotate(district_name=F('created_by__staffTbl__district__name'))
                               .values('district_name')
                               .annotate(
                                   count=Count('id'),
                                   total_area=Sum('size_Ha')
                               )
                               .order_by('-count')[:10]),
        }
        
        # Growth Monitoring Statistics
        growth_stats = {
            'total': GrowthMonitoringModel.objects.all().count(),
            'avg_height': float(GrowthMonitoringModel.objects.filter( height__isnull=False)
                               .aggregate(avg=Avg('height'))['avg'] or 0),
            'avg_leaves': float(GrowthMonitoringModel.objects.filter( number_of_leaves__isnull=False)
                               .aggregate(avg=Avg('number_of_leaves'))['avg'] or 0),
            'by_leaf_color': list(GrowthMonitoringModel.objects.all()
                                 .values('leaf_color')
                                 .annotate(count=Count('id'))),
            'by_district': list(GrowthMonitoringModel.objects.filter( district__isnull=False)
                               .values('district__name')
                               .annotate(count=Count('id'))
                               .order_by('-count')[:10]),
            'recent': list(GrowthMonitoringModel.objects.all()
                          .order_by('-date')[:10]
                          .values('plant_uid', 'height', 'number_of_leaves', 'date')),
        }
        
        # QR Code Statistics
        qr_stats = {
            'total': QR_CodeModel.objects.all().count(),
            'used': QR_CodeModel.objects.filter( is_used=True).count(),
            'active': QR_CodeModel.objects.filter( is_active=True).count(),
            'usage_percentage': 0,
        }
        if qr_stats['total'] > 0:
            qr_stats['usage_percentage'] = round((qr_stats['used'] / qr_stats['total'] * 100), 1)
        
        # Assignment Statistics
        assignment_stats = {
            'total': PersonnelAssignmentModel.objects.all().count(),
            'by_status': list(PersonnelAssignmentModel.objects.all()
                             .values('status')
                             .annotate(count=Count('id'))),
            'by_district': list(PersonnelAssignmentModel.objects.filter( district__isnull=False)
                               .values('district__name')
                               .annotate(count=Count('id'))
                               .order_by('-count')[:10]),
            'active': PersonnelAssignmentModel.objects.filter( status__in=[1, 2]).count(),
            'pending': PersonnelAssignmentModel.objects.filter( status=0).count(),
        }
        
        # Contractor Statistics
        contractor_stats = {
            'total': contractorsTbl.objects.all().count(),
            'by_service': list(contractorsTbl.objects.all()
                              .values('interested_services')
                              .annotate(count=Count('id'))
                              .order_by('-count')),
            'by_district': list(contratorDistrictAssignment.objects.filter(
                                    
                                   contractor__isnull=False
                               )
                               .values('district__name')
                               .annotate(count=Count('contractor', distinct=True))
                               .order_by('-count')[:10]),
            'certified': ContractorCertificateModel.objects.filter( status='Verified')
                        .values('contractor').distinct().count(),
            'pending_certificates': ContractorCertificateModel.objects.filter( status='Pending').count(),
            'verified_certificates': ContractorCertificateModel.objects.filter( status='Verified').count(),
        }
        
        # Daily Reporting Statistics
        daily_report_stats = {
            'total': DailyReportingModel.objects.all().count(),
            'today': DailyReportingModel.objects.filter( reporting_date=date.today()).count(),
            'this_week': DailyReportingModel.objects.filter(
                
                reporting_date__gte=start_date
            ).count(),
            'total_area': float(DailyReportingModel.objects.all()
                               .aggregate(total=Sum('area_covered_ha'))['total'] or 0),
            'by_activity': list(DailyReportingModel.objects.filter( activity__isnull=False)
                               .values('activity__sub_activity')
                               .annotate(count=Count('id'))
                               .order_by('-count')[:10]),
            'by_district': list(DailyReportingModel.objects.filter( district__isnull=False)
                               .values('district__name')
                               .annotate(
                                   count=Count('id'),
                                   total_area=Sum('area_covered_ha')
                               )
                               .order_by('-count')[:10]),
        }
        
        # Activity Reporting Statistics
        activity_report_stats = {
            'total': ActivityReportingModel.objects.all().count(),
            'today': ActivityReportingModel.objects.filter( reporting_date=date.today()).count(),
            'this_week': ActivityReportingModel.objects.filter(
                
                reporting_date__gte=start_date
            ).count(),
            'total_area': float(ActivityReportingModel.objects.all()
                               .aggregate(total=Sum('area_covered_ha'))['total'] or 0),
            'by_activity': list(ActivityReportingModel.objects.filter( activity__isnull=False)
                               .values('activity__sub_activity')
                               .annotate(count=Count('id'))
                               .order_by('-count')[:10]),
        }
        
        # Irrigation Statistics
        irrigation_stats = {
            'total': IrrigationModel.objects.all().count(),
            'total_volume': float(IrrigationModel.objects.all()
                                 .aggregate(total=Sum('water_volume'))['total'] or 0),
            'by_type': list(IrrigationModel.objects.filter( irrigation_type__isnull=False)
                           .values('irrigation_type__irrigation_type')
                           .annotate(
                               count=Count('id'),
                               total_volume=Sum('water_volume')
                           )
                           .order_by('-count')),
            'by_district': list(IrrigationModel.objects.filter( district__isnull=False)
                               .values('district__name')
                               .annotate(
                                   count=Count('id'),
                                   total_volume=Sum('water_volume')
                               )
                               .order_by('-count')[:10]),
        }
        
        # Geographic Statistics
        geo_stats = {
            'regions': Region.objects.all().count(),
            'districts': cocoaDistrict.objects.all().count(),
            'communities': Community.objects.all().count(),
            'projects': projectTbl.objects.all().count(),
            'sectors': SectorModel.objects.all().count(),
            'top_districts_sectors': list(SectorModel.objects.all()
                                         .annotate(district_name=F('created_by__staffTbl__district__name'))
                                         .values('district_name')
                                         .annotate(count=Count('id'))
                                         .order_by('-count')[:10]),
            'top_districts_ras': list(PersonnelModel.objects.filter(
                                         
                                        district__isnull=False,
                                        personnel_type='Rehab Assistant'
                                    )
                                    .values('district__name')
                                    .annotate(count=Count('id'))
                                    .order_by('-count')[:10]),
            'top_districts_reports': list(DailyReportingModel.objects.filter(
                                             
                                            district__isnull=False
                                        )
                                        .values('district__name')
                                        .annotate(count=Count('id'))
                                        .order_by('-count')[:10]),
        }
        
        # Activity Types
        activity_types = {
            'total': Activities.objects.all().count(),
            'by_main': list(Activities.objects.all()
                           .values('main_activity')
                           .annotate(count=Count('id'))
                           .order_by('-count')),
        }
        
        # Trend data for charts
        trend_data = {
            'growth_records': list(GrowthMonitoringModel.objects.filter(
                                    
                                    date__gte=start_date
                                )
                                .annotate(day=TruncDay('date'))
                                .values('day')
                                .annotate(count=Count('id'))
                                .order_by('day')),
            
            'daily_reports': list(DailyReportingModel.objects.filter(
                                    
                                    reporting_date__gte=start_date
                                )
                                .annotate(day=TruncDay('reporting_date'))
                                .values('day')
                                .annotate(count=Count('id'))
                                .order_by('day')),
            
            'activity_reports': list(ActivityReportingModel.objects.filter(
                                        
                                        reporting_date__gte=start_date
                                    )
                                    .annotate(day=TruncDay('reporting_date'))
                                    .values('day')
                                    .annotate(count=Count('id'))
                                    .order_by('day')),
            
            'assignments': list(PersonnelAssignmentModel.objects.filter(
                                    
                                    created_date__gte=start_date
                                )
                                .annotate(day=TruncDay('created_date'))
                                .values('day')
                                .annotate(count=Count('id'))
                                .order_by('day')),
            
            'irrigation': list(IrrigationModel.objects.filter(
                                    
                                    date__gte=start_date
                                )
                                .annotate(day=TruncDay('date'))
                                .values('day')
                                .annotate(
                                    count=Count('id'),
                                    volume=Sum('water_volume')
                                )
                                .order_by('day')),
        }
        
        response = {
            'success': True,
            'personnel_stats': personnel_stats,
            'staff_stats': staff_stats,
            'sector_stats': sector_stats,
            'growth_stats': growth_stats,
            'qr_stats': qr_stats,
            'assignment_stats': assignment_stats,
            'contractor_stats': contractor_stats,
            'daily_report_stats': daily_report_stats,
            'activity_report_stats': activity_report_stats,
            'irrigation_stats': irrigation_stats,
            'geo_stats': geo_stats,
            'activity_types': activity_types,
            'trend_data': trend_data,
            'period': {
                'days': days,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        print(f"Error in get_dashboard_stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_chart_data(request):
    """Get data for dashboard charts - Using only provided models"""
    try:
        chart_type = request.GET.get('type', 'personnel_by_type')
        limit = int(request.GET.get('limit', 10))
        
        data = []
        labels = []
        
        if chart_type == 'personnel_by_type':
            queryset = PersonnelModel.objects.filter(
                delete_field='no'
            ).values('personnel_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            for item in queryset:
                labels.append(item['personnel_type'])
                data.append(item['count'])
                
        elif chart_type == 'personnel_by_region':  # Changed from personnel_by_district
            # Using region through staffTbl or just removing if not available
            # Since region isn't directly in PersonnelModel, we'll skip or use alternative
            # For now, let's return empty data
            labels = []
            data = []
                
        elif chart_type == 'sectors_by_region':  # Changed from sectors_by_district
            # Since we can't use district, let's return empty or use created_by region if available
            # For now, return empty
            labels = []
            data = []
                    
        elif chart_type == 'sectors_by_area':  # Changed from sectors_by_area with district
            # Remove district dependency
            queryset = SectorModel.objects.filter(
                
                size_Ha__isnull=False
            ).values('sector').annotate(
                area=Sum('size_Ha')
            ).order_by('-area')[:limit]
            
            for item in queryset:
                labels.append(item['sector'])
                data.append(float(item['area']))
                    
        elif chart_type == 'assignments_by_status':
            status_map = {0: 'Pending', 1: 'Submitted', 2: 'Approved', 
                         3: 'Rejected', 4: 'Completed', 5: 'Revoked'}
            
            queryset = PersonnelAssignmentModel.objects.filter(
                delete_field='no'
            ).values('status').annotate(
                count=Count('id')
            )
            
            for item in queryset:
                labels.append(status_map.get(item['status'], f'Status {item["status"]}'))
                data.append(item['count'])
                
        elif chart_type == 'growth_by_leaf_color':
            queryset = GrowthMonitoringModel.objects.filter(
                delete_field='no'
            ).values('leaf_color').annotate(
                count=Count('id')
            )
            
            for item in queryset:
                labels.append(item['leaf_color'])
                data.append(item['count'])
                
        elif chart_type == 'contractors_by_service':
            queryset = contractorsTbl.objects.filter(
                delete_field='no'
            ).values('interested_services').annotate(
                count=Count('id')
            ).order_by('-count')[:limit]
            
            for item in queryset:
                labels.append(item['interested_services'])
                data.append(item['count'])
                
        elif chart_type == 'reports_by_activity':
            queryset = DailyReportingModel.objects.filter(
                
                activity__isnull=False
            ).values('activity__sub_activity').annotate(
                count=Count('id')
            ).order_by('-count')[:limit]
            
            for item in queryset:
                activity_name = item['activity__sub_activity'] or ''
                labels.append(activity_name[:30] + '...' if len(activity_name) > 30 else activity_name)
                data.append(item['count'])
                
        elif chart_type == 'reports_by_main_activity':  # New chart type
            queryset = DailyReportingModel.objects.filter(
                
                main_activity__isnull=False
            ).values('main_activity__main_activity').annotate(
                count=Count('id')
            ).order_by('-count')[:limit]
            
            for item in queryset:
                labels.append(item['main_activity__main_activity'])
                data.append(item['count'])
                
        elif chart_type == 'irrigation_by_type':
            queryset = IrrigationModel.objects.filter(
                
                irrigation_type__isnull=False
            ).values('irrigation_type__irrigation_type').annotate(
                count=Count('id'),
                total_volume=Sum('water_volume')
            )
            
            for item in queryset:
                labels.append(item['irrigation_type__irrigation_type'])
                data.append(item['count'])
                
        elif chart_type == 'daily_reports_trend':
            days = int(request.GET.get('days', 30))
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            queryset = DailyReportingModel.objects.filter(
                
                reporting_date__gte=start_date
            ).annotate(
                day=TruncDay('reporting_date')
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')
            
            for item in queryset:
                labels.append(item['day'].strftime('%Y-%m-%d') if item['day'] else '')
                data.append(item['count'])
                
        elif chart_type == 'activity_reports_trend':  # New chart type
            days = int(request.GET.get('days', 30))
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            queryset = ActivityReportingModel.objects.filter(
                
                reporting_date__gte=start_date
            ).annotate(
                day=TruncDay('reporting_date')
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')
            
            for item in queryset:
                labels.append(item['day'].strftime('%Y-%m-%d') if item['day'] else '')
                data.append(item['count'])
                
        elif chart_type == 'growth_trend':
            days = int(request.GET.get('days', 30))
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            queryset = GrowthMonitoringModel.objects.filter(
                
                date__gte=start_date
            ).annotate(
                day=TruncDay('date')
            ).values('day').annotate(
                count=Count('id'),
                avg_height=Avg('height'),
                avg_leaves=Avg('number_of_leaves')
            ).order_by('day')
            
            for item in queryset:
                labels.append(item['day'].strftime('%Y-%m-%d') if item['day'] else '')
                data.append(float(item['avg_height'] or 0))
                
        elif chart_type == 'assignments_trend':  # New chart type
            days = int(request.GET.get('days', 30))
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            queryset = PersonnelAssignmentModel.objects.filter(
                
                created_date__gte=start_date
            ).annotate(
                day=TruncDay('created_date')
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')
            
            for item in queryset:
                labels.append(item['day'].strftime('%Y-%m-%d') if item['day'] else '')
                data.append(item['count'])
                
        elif chart_type == 'irrigation_trend':
            days = int(request.GET.get('days', 30))
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get daily irrigation counts and volume
            queryset = IrrigationModel.objects.filter(
                delete_field='no',
                date__gte=start_date,
                date__lte=end_date
            ).annotate(
                day=TruncDay('date')
            ).values('day').annotate(
                count=Count('id'),
                total_volume=Sum('water_volume')
            ).order_by('day')
            
            # Create date range
            date_range = []
            current_date = start_date
            while current_date <= end_date:
                date_range.append(current_date)
                current_date += timedelta(days=1)
            
            # Map data - item['day'] is already a date object
            data_dict = {}
            volume_dict = {}
            for item in queryset:
                if item['day']:
                    day_key = item['day']  # This is already a date, don't call .date()
                    data_dict[day_key] = item['count']
                    volume_dict[day_key] = float(item['total_volume'] or 0)
            
            # Build labels and data
            labels = []
            data = []
            volume_data = []
            
            for day in date_range:
                labels.append(day.strftime('%Y-%m-%d'))
                if day in data_dict:
                    data.append(data_dict[day])
                    volume_data.append(volume_dict[day])
                else:
                    data.append(0)
                    volume_data.append(0)
            
            return JsonResponse({
                'success': True,
                'labels': labels,
                'data': data,
                'volume_data': volume_data,
                'chart_type': chart_type
            })
                        
        elif chart_type == 'qr_usage':
            total = QR_CodeModel.objects.filter(delete_field='no').count()
            used = QR_CodeModel.objects.filter( is_used=True).count()
            active = QR_CodeModel.objects.filter( is_active=True).count()
            
            labels = ['Used', 'Available', 'Inactive']
            data = [
                used,
                active - used if active > used else 0,
                total - active
            ]
        
        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data,
            'chart_type': chart_type
        })
        
    except Exception as e:
        print(f"Error in get_chart_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_recent_activities(request):
    """Get recent activities across all modules - Using only provided models"""
    try:
        limit = int(request.GET.get('limit', 5))
        activities = []
        
        # Recent growth monitoring records
        growth_records = GrowthMonitoringModel.objects.filter(
            delete_field='no'
        ).select_related('agent', 'district').order_by('-created_date')[:1]
        
        for record in growth_records:
            activities.append({
                'id': record.id,
                'type': 'growth',
                'icon': 'fas fa-seedling',
                'icon_bg': 'bg-success',
                'title': f"Growth Monitoring: {record.plant_uid}",
                'description': f"Height: {record.height}cm, Leaves: {record.number_of_leaves} - {record.district.name if record.district else 'N/A'}",
                'time': record.created_date.strftime('%Y-%m-%d %H:%M') if record.created_date else '',
                'timestamp': record.created_date.isoformat() if record.created_date else None,
                'url': f"/growth/{record.id}/"
            })
        
        # Recent personnel additions
        personnel = PersonnelModel.objects.filter(
            delete_field='no'
        ).select_related('district').order_by('-created_date')[:1]
        
        for person in personnel:
            activities.append({
                'id': person.id,
                'type': 'personnel',
                'icon': 'fas fa-user-tie',
                'icon_bg': 'bg-primary',
                'title': f"New {person.personnel_type}: {person.first_name} {person.surname}",
                'description': f"ID: {person.staff_id} - {person.district.name if person.district else 'N/A'}",
                'time': person.created_date.strftime('%Y-%m-%d %H:%M') if person.created_date else '',
                'timestamp': person.created_date.isoformat() if person.created_date else None,
                'url': f"/personnel/{person.id}/"
            })
        
        # Recent assignments
        assignments = PersonnelAssignmentModel.objects.filter(
            delete_field='no'
        ).select_related('ra', 'po', 'district').order_by('-created_date')[:1]
        
        for assign in assignments:
            ra_name = f"{assign.ra.first_name} {assign.ra.surname}" if assign.ra else 'Unknown'
            po_name = f"{assign.po.first_name} {assign.po.last_name}" if assign.po else 'Unknown'
            activities.append({
                'id': assign.id,
                'type': 'assignment',
                'icon': 'fas fa-user-tag',
                'icon_bg': 'bg-info',
                'title': f"RA Assigned: {ra_name}",
                'description': f"To: {po_name} - {assign.district.name if assign.district else 'N/A'}",
                'time': assign.created_date.strftime('%Y-%m-%d %H:%M') if assign.created_date else '',
                'timestamp': assign.created_date.isoformat() if assign.created_date else None,
                'url': f"/assignments/{assign.id}/"
            })
        
        # Recent daily reports
        reports = DailyReportingModel.objects.filter(
            delete_field='no'
        ).select_related('agent', 'activity', 'district').order_by('-created_date')[:1]
        
        for report in reports:
            agent_name = f"{report.agent.first_name} {report.agent.last_name}" if report.agent else 'Unknown'
            activities.append({
                'id': report.id,
                'type': 'daily_report',
                'icon': 'fas fa-file-alt',
                'icon_bg': 'bg-warning',
                'title': f"Daily Report: {report.activity.sub_activity if report.activity else 'N/A'}",
                'description': f"By: {agent_name} - Area: {report.area_covered_ha}ha",
                'time': report.created_date.strftime('%Y-%m-%d %H:%M') if report.created_date else '',
                'timestamp': report.created_date.isoformat() if report.created_date else None,
                'url': f"/daily-reports/{report.id}/"
            })
        
        # Recent activity reports
        activity_reports = ActivityReportingModel.objects.filter(
            delete_field='no'
        ).select_related('agent', 'activity', 'district').order_by('-created_date')[:1]
        
        for report in activity_reports:
            agent_name = f"{report.agent.first_name} {report.agent.last_name}" if report.agent else 'Unknown'
            activities.append({
                'id': report.id,
                'type': 'activity_report',
                'icon': 'fas fa-clipboard-list',
                'icon_bg': 'bg-secondary',
                'title': f"Activity Report: {report.activity.sub_activity if report.activity else 'N/A'}",
                'description': f"By: {agent_name} - Area: {report.area_covered_ha}ha",
                'time': report.created_date.strftime('%Y-%m-%d %H:%M') if report.created_date else '',
                'timestamp': report.created_date.isoformat() if report.created_date else None,
                'url': f"/activity-reports/{report.id}/"
            })
        
        # Recent irrigation records
        irrigation = IrrigationModel.objects.filter(
            delete_field='no'
        ).select_related('agent', 'irrigation_type', 'district').order_by('-created_date')[:1]
        
        for record in irrigation:
            agent_name = f"{record.agent.first_name} {record.agent.last_name}" if record.agent else 'Unknown'
            activities.append({
                'id': record.id,
                'type': 'irrigation',
                'icon': 'fas fa-water',
                'icon_bg': 'bg-info',
                'title': f"Irrigation: {record.irrigation_type.irrigation_type if record.irrigation_type else 'N/A'}",
                'description': f"Volume: {record.water_volume}L - By: {agent_name}",
                'time': record.created_date.strftime('%Y-%m-%d %H:%M') if record.created_date else '',
                'timestamp': record.created_date.isoformat() if record.created_date else None,
                'url': f"/irrigation/{record.id}/"
            })
        
        # Recent contractors
        contractors = contractorsTbl.objects.filter(
            delete_field='no'
        ).order_by('-created_date')[:1]
        
        for contractor in contractors:
            activities.append({
                'id': contractor.id,
                'type': 'contractor',
                'icon': 'fas fa-handshake',
                'icon_bg': 'bg-success',
                'title': f"New Contractor: {contractor.contractor_name}",
                'description': f"Service: {contractor.interested_services} - Contact: {contractor.contact_person}",
                'time': contractor.created_date.strftime('%Y-%m-%d %H:%M') if contractor.created_date else '',
                'timestamp': contractor.created_date.isoformat() if contractor.created_date else None,
                'url': f"/contractors/{contractor.id}/"
            })
        
        # Recent QR codes
        qr_codes = QR_CodeModel.objects.filter(
            delete_field='no'
        ).order_by('-created_date')[:1]
        
        for qr in qr_codes:
            activities.append({
                'id': qr.id,
                'type': 'qr_code',
                'icon': 'fas fa-qrcode',
                'icon_bg': 'bg-dark',
                'title': f"QR Code Generated: {qr.uid}",
                'description': f"Status: {'Used' if qr.is_used else 'Available'} - {'Active' if qr.is_active else 'Inactive'}",
                'time': qr.created_date.strftime('%Y-%m-%d %H:%M') if qr.created_date else '',
                'timestamp': qr.created_date.isoformat() if qr.created_date else None,
                'url': f"/qr-codes/{qr.id}/"
            })
        
        # Sort by timestamp descending and limit
        activities.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        activities = activities[:limit]
        
        return JsonResponse({
            'success': True,
            'activities': activities
        })
        
    except Exception as e:
        print(f"Error in get_recent_activities: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_upcoming_tasks(request):
    """Get upcoming tasks and deadlines - Using only provided models"""
    try:
        tasks = []
        
        # Expiring certificates
        expiring_certs = ContractorCertificateModel.objects.filter(
            
            end_date__gte=date.today(),
            end_date__lte=date.today() + timedelta(days=30)
        ).select_related('contractor')[:5]
        
        for cert in expiring_certs:
            days_left = (cert.end_date - date.today()).days
            tasks.append({
                'id': cert.id,
                'type': 'certificate',
                'title': f"Certificate Expiring: {cert.contractor.contractor_name if cert.contractor else 'Unknown'}",
                'description': f"{cert.work_type} - Expires in {days_left} days",
                'due_date': cert.end_date.strftime('%Y-%m-%d'),
                'priority': 'high' if days_left < 7 else 'medium' if days_left < 15 else 'low',
                'url': f"/contractors/{cert.contractor.id}/" if cert.contractor else '#'
            })
        
        # Pending assignments
        pending_assignments = PersonnelAssignmentModel.objects.filter(
            
            status=0
        ).select_related('ra', 'po')[:5]
        
        for assign in pending_assignments:
            days_pending = (date.today() - assign.date_assigned).days if assign.date_assigned else 0
            ra_name = f"{assign.ra.first_name} {assign.ra.surname}" if assign.ra else 'Unknown'
            po_name = f"{assign.po.first_name} {assign.po.last_name}" if assign.po else 'Unknown'
            tasks.append({
                'id': assign.id,
                'type': 'assignment',
                'title': f"Pending Assignment: {ra_name}",
                'description': f"Assigned to {po_name} - {days_pending} days pending",
                'due_date': assign.date_assigned.strftime('%Y-%m-%d') if assign.date_assigned else '',
                'priority': 'high' if days_pending > 7 else 'medium',
                'url': f"/assignments/{assign.id}/"
            })
        
        # Pending verifications
        pending_verifications = ContractorCertificateVerificationModel.objects.filter(
            
            is_verified=False
        ).select_related('certificate', 'certificate__contractor')[:5]
        
        for verif in pending_verifications:
            tasks.append({
                'id': verif.id,
                'type': 'verification',
                'title': f"Pending Verification: {verif.certificate.contractor.contractor_name if verif.certificate and verif.certificate.contractor else 'Unknown'}",
                'description': f"{verif.certificate.work_type if verif.certificate else 'Certificate'} - Awaiting verification",
                'due_date': verif.created_date.strftime('%Y-%m-%d') if verif.created_date else '',
                'priority': 'medium',
                'url': f"/contractors/{verif.certificate.contractor.id}/" if verif.certificate and verif.certificate.contractor else '#'
            })
        
        # Growth monitoring tasks (if any scheduled)
        upcoming_growth = GrowthMonitoringModel.objects.filter(
            
            date__gte=date.today(),
            date__lte=date.today() + timedelta(days=7)
        ).select_related('agent')[:5]
        
        for growth in upcoming_growth:
            tasks.append({
                'id': growth.id,
                'type': 'growth',
                'title': f"Growth Monitoring Scheduled: {growth.plant_uid}",
                'description': f"Plant monitoring on {growth.date}",
                'due_date': growth.date.strftime('%Y-%m-%d'),
                'priority': 'medium',
                'url': f"/growth/{growth.id}/"
            })
        
        # Sort by priority and due date
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        tasks.sort(key=lambda x: (priority_order.get(x['priority'], 3), x['due_date']))
        
        return JsonResponse({
            'success': True,
            'tasks': tasks[:15]  # Limit to 15 tasks
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in get_upcoming_tasks: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_notifications(request):
    """Get user notifications - Using only provided models"""
    try:
        notifications = []
        
        # Today's reports
        reports_today = DailyReportingModel.objects.filter(
            
            reporting_date=date.today()
        ).count()
        
        if reports_today > 0:
            notifications.append({
                'id': f'reports_{date.today()}',
                'type': 'info',
                'icon': 'fas fa-file-alt',
                'icon_bg': 'bg-info',
                'title': f'{reports_today} Daily Report(s) Submitted Today',
                'description': 'New reports are ready for review',
                'time': 'Just now',
                'read': False
            })
        
        # Activity reports today
        activity_today = ActivityReportingModel.objects.filter(
            
            reporting_date=date.today()
        ).count()
        
        if activity_today > 0:
            notifications.append({
                'id': f'activity_{date.today()}',
                'type': 'info',
                'icon': 'fas fa-clipboard-list',
                'icon_bg': 'bg-secondary',
                'title': f'{activity_today} Activity Report(s) Submitted Today',
                'description': 'New activity reports require attention',
                'time': 'Today',
                'read': False
            })
        
        # Pending assignments
        pending_assignments = PersonnelAssignmentModel.objects.filter(
            
            status=0
        ).count()
        
        if pending_assignments > 0:
            notifications.append({
                'id': f'assignments_{date.today()}',
                'type': 'warning',
                'icon': 'fas fa-user-tag',
                'icon_bg': 'bg-warning',
                'title': f'{pending_assignments} Pending RA Assignment(s)',
                'description': 'New assignments require approval',
                'time': 'Today',
                'read': False
            })
        
        # Pending verifications
        pending_verifications = ContractorCertificateVerificationModel.objects.filter(
            
            is_verified=False
        ).count()
        
        if pending_verifications > 0:
            notifications.append({
                'id': f'verifications_{date.today()}',
                'type': 'warning',
                'icon': 'fas fa-certificate',
                'icon_bg': 'bg-warning',
                'title': f'{pending_verifications} Certificate(s) Pending Verification',
                'description': 'Contractor certificates need verification',
                'time': 'Today',
                'read': False
            })
        
        # QR codes nearing usage limit
        unused_qr = QR_CodeModel.objects.filter(
            
            is_used=False,
            is_active=True
        ).count()
        
        if unused_qr < 10:
            notifications.append({
                'id': 'qr_low',
                'type': 'warning',
                'icon': 'fas fa-qrcode',
                'icon_bg': 'bg-warning',
                'title': f'Low QR Codes: {unused_qr} Remaining',
                'description': 'Generate new QR codes soon',
                'time': 'Today',
                'read': False
            })
        
        # Growth monitoring overdue
        overdue_growth = GrowthMonitoringModel.objects.filter(
            
            date__lt=date.today() - timedelta(days=30)
        ).count()
        
        if overdue_growth > 0:
            notifications.append({
                'id': 'growth_overdue',
                'type': 'danger',
                'icon': 'fas fa-seedling',
                'icon_bg': 'bg-danger',
                'title': f'{overdue_growth} Growth Records Overdue',
                'description': 'Plants need to be monitored',
                'time': 'Today',
                'read': False
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications
        })
        
    except Exception as e:
        print(f"Error in get_notifications: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)