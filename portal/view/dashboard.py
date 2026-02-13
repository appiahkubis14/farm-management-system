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
    PersonnelModel, staffTbl, PersonnelAssignmentModel,
    
    # Contractors
    contractorsTbl, contratorDistrictAssignment, ContractorCertificateModel, ContractorCertificateVerificationModel,
    
    # Farms & Activities
    FarmdetailsTbl, Activities, DailyReportingModel, ActivityReportingModel,
    
    # Districts & Regions
    cocoaDistrict, Region, Community, projectTbl,
    
    # Outbreak & Equipment
    OutbreakFarm, EquipmentModel, EquipmentAssignmentModel,
    
    # Payments
    PaymentReport, DetailedPaymentReport,
    
    # Other
    Feedback, IssueModel, IrrigationModel, VerifyRecord, CalculatedArea,
    mappedFarms, FarmValidation, Joborder, posRoutemonitoring, QR_CodeModel, GrowthMonitoringModel
)

# ============== DASHBOARD VIEWS ==============

@login_required
def general_dashboard(request):
    """Render the main dashboard with all system statistics"""
    
    # Get counts for different personnel types
    ra_count = PersonnelModel.objects.filter(
        delete_field='no', 
        personnel_type='Rehab Assistant'
    ).count()
    
    rt_count = PersonnelModel.objects.filter(
        delete_field='no', 
        personnel_type='Rehab Technician'
    ).count()
    
    po_count = staffTbl.objects.filter(
        delete_field='no'
    ).filter(
        Q(staffid__icontains='PO-') | Q(staffid__icontains='PC-')
    ).count()
    
    staff_count = staffTbl.objects.filter(delete_field='no').count()
    total_personnel = PersonnelModel.objects.filter(delete_field='no').count()
    
    # Get farm statistics
    total_farms = FarmdetailsTbl.objects.filter(delete_field='no').count()
    treatment_farms = FarmdetailsTbl.objects.filter(delete_field='no', status='Treatment').count()
    establishment_farms = FarmdetailsTbl.objects.filter(delete_field='no', status='Establishment').count()
    maintenance_farms = FarmdetailsTbl.objects.filter(delete_field='no', status='Maintenance').count()
    
    # Get mapped farms
    mapped_farms_count = mappedFarms.objects.filter(delete_field='no').count()
    validated_farms_count = FarmValidation.objects.filter(delete_field='no').count()
    
    # Get assignment statistics
    active_assignments = PersonnelAssignmentModel.objects.filter(
        delete_field='no', 
        status__in=[1, 2]  # Submitted or Approved
    ).count()
    
    pending_assignments = PersonnelAssignmentModel.objects.filter(
        delete_field='no', 
        status=0  # Pending
    ).count()
    
    total_assignments = PersonnelAssignmentModel.objects.filter(delete_field='no').count()
    
    # Get contractor statistics
    total_contractors = contractorsTbl.objects.filter(delete_field='no').count()
    certified_contractors = ContractorCertificateModel.objects.filter(
        delete_field='no',
        status='Verified'
    ).values('contractor').distinct().count()
    
    # Get equipment statistics
    total_equipment = EquipmentModel.objects.filter(delete_field='no').count()
    equipment_assigned = EquipmentAssignmentModel.objects.filter(
        delete_field='no',
        status='Assigned'
    ).count()
    equipment_under_repair = EquipmentModel.objects.filter(
        delete_field='no',
        status='Under Repair'
    ).count()
    
    # Get outbreak statistics
    active_outbreaks = OutbreakFarm.objects.filter(
        delete_field='no',
        status__in=[0, 1, 2]  # Pending, Submitted, Treated
    ).count()
    
    resolved_outbreaks = OutbreakFarm.objects.filter(
        delete_field='no',
        status=3  # Resolved
    ).count()
    
    # Get activity statistics
    total_activities = Activities.objects.filter(delete_field='no').count()
    daily_reports_today = DailyReportingModel.objects.filter(
        delete_field='no',
        reporting_date=date.today()
    ).count()
    
    # Get payment statistics
    pending_payments = PaymentReport.objects.filter(
        delete_field='no'
    ).aggregate(
        total=Sum('salary')
    )['total'] or 0
    
    # Get district and community statistics
    total_districts = cocoaDistrict.objects.filter(delete_field='no').count()
    total_regions = Region.objects.filter(delete_field='no').count()
    total_communities = Community.objects.filter(delete_field='no').count()
    total_projects = projectTbl.objects.filter(delete_field='no').count()
    
    # Get feedback/issues
    open_feedback = Feedback.objects.filter(
        delete_field='no',
        Status='Open'
    ).count()
    
    open_issues = IssueModel.objects.filter(
        delete_field='no',
        status=0  # Pending
    ).count()
    
    context = {
        # Personnel Stats
        'total_personnel': total_personnel,
        'ra_count': ra_count,
        'rt_count': rt_count,
        'po_count': po_count,
        'staff_count': staff_count,
        
        # Farm Stats
        'total_farms': total_farms,
        'treatment_farms': treatment_farms,
        'establishment_farms': establishment_farms,
        'maintenance_farms': maintenance_farms,
        'mapped_farms_count': mapped_farms_count,
        'validated_farms_count': validated_farms_count,
        
        # Assignment Stats
        'total_assignments': total_assignments,
        'active_assignments': active_assignments,
        'pending_assignments': pending_assignments,
        
        # Contractor Stats
        'total_contractors': total_contractors,
        'certified_contractors': certified_contractors,
        
        # Equipment Stats
        'total_equipment': total_equipment,
        'equipment_assigned': equipment_assigned,
        'equipment_under_repair': equipment_under_repair,
        
        # Outbreak Stats
        'active_outbreaks': active_outbreaks,
        'resolved_outbreaks': resolved_outbreaks,
        
        # Activity Stats
        'total_activities': total_activities,
        'daily_reports_today': daily_reports_today,
        
        # Payment Stats
        'pending_payments': pending_payments,
        
        # Geographic Stats
        'total_districts': total_districts,
        'total_regions': total_regions,
        'total_communities': total_communities,
        'total_projects': total_projects,
        
        # Feedback Stats
        'open_feedback': open_feedback,
        'open_issues': open_issues,
        
        # Current date/time
        'current_date': date.today().strftime('%B %d, %Y'),
        'current_time': datetime.now().strftime('%H:%M'),
    }
    
    return render(request, 'portal/dashboard/general_dashboard.html', context)


@require_http_methods(["GET"])
def get_dashboard_stats(request):
    """API endpoint to get real-time dashboard statistics"""
    try:
        # Get date range from request (default to last 30 days)
        days = int(request.GET.get('days', 30))
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Personnel Statistics
        personnel_stats = {
            'total': PersonnelModel.objects.filter(delete_field='no').count(),
            'by_type': list(PersonnelModel.objects.filter(delete_field='no')
                           .values('personnel_type')
                           .annotate(count=Count('id'))
                           .order_by('-count')),
            'by_gender': list(PersonnelModel.objects.filter(delete_field='no')
                            .values('gender')
                            .annotate(count=Count('id'))),
            'by_district': list(PersonnelModel.objects.filter(delete_field='no', district__isnull=False)
                               .values('district__name')
                               .annotate(count=Count('id'))
                               .order_by('-count')[:10]),
        }
        
        # Staff Statistics
        staff_stats = {
            'total': staffTbl.objects.filter(delete_field='no').count(),
            'by_project': list(staffTbl.objects.filter(delete_field='no', projectTbl_foreignkey__isnull=False)
                              .values('projectTbl_foreignkey__name')
                              .annotate(count=Count('id'))
                              .order_by('-count')[:10]),
        }
        
        # Farm Statistics
        farm_stats = {
            'total': FarmdetailsTbl.objects.filter(delete_field='no').count(),
            'by_status': list(FarmdetailsTbl.objects.filter(delete_field='no')
                             .values('status')
                             .annotate(count=Count('id'))),
            'by_district': list(FarmdetailsTbl.objects.filter(delete_field='no', district__isnull=False)
                               .values('district__name')
                               .annotate(count=Count('id'))
                               .order_by('-count')[:10]),
            'by_region': list(FarmdetailsTbl.objects.filter(delete_field='no', region__isnull=False)
                             .values('region__region')
                             .annotate(count=Count('id'))
                             .order_by('-count')[:10]),
            'mapped': mappedFarms.objects.filter(delete_field='no').count(),
            'validated': FarmValidation.objects.filter(delete_field='no').count(),
            'avg_size': FarmdetailsTbl.objects.filter(delete_field='no', farm_size__isnull=False)
                       .aggregate(avg=Avg('farm_size'))['avg'] or 0,
        }
        
        # Assignment Statistics
        assignment_stats = {
            'total': PersonnelAssignmentModel.objects.filter(delete_field='no').count(),
            'by_status': list(PersonnelAssignmentModel.objects.filter(delete_field='no')
                             .values('status')
                             .annotate(count=Count('id'))),
            'by_district': list(PersonnelAssignmentModel.objects.filter(delete_field='no', district__isnull=False)
                               .values('district__name')
                               .annotate(count=Count('id'))
                               .order_by('-count')[:10]),
            'active': PersonnelAssignmentModel.objects.filter(delete_field='no', status__in=[1, 2]).count(),
            'pending': PersonnelAssignmentModel.objects.filter(delete_field='no', status=0).count(),
            'completed': PersonnelAssignmentModel.objects.filter(delete_field='no', status=4).count(),
            'revoked': PersonnelAssignmentModel.objects.filter(delete_field='no', status=5).count(),
        }
        
        # Contractor Statistics
        contractor_stats = {
            'total': contractorsTbl.objects.filter(delete_field='no').count(),
            'by_service': list(contractorsTbl.objects.filter(delete_field='no')
                              .values('interested_services')
                              .annotate(count=Count('id'))
                              .order_by('-count')),
            'by_district': list(contractorsTbl.objects.filter(delete_field='no', district__isnull=False)
                               .values('district__name')
                               .annotate(count=Count('id'))
                               .order_by('-count')[:10]),
            'certified': ContractorCertificateModel.objects.filter(delete_field='no', status='Verified')
                        .values('contractor').distinct().count(),
            'pending_certificates': ContractorCertificateModel.objects.filter(delete_field='no', status='Pending').count(),
            'verified_certificates': ContractorCertificateModel.objects.filter(delete_field='no', status='Verified').count(),
        }
        
        # Equipment Statistics
        equipment_stats = {
            'total': EquipmentModel.objects.filter(delete_field='no').count(),
            'by_status': list(EquipmentModel.objects.filter(delete_field='no')
                             .values('status')
                             .annotate(count=Count('id'))),
            'assigned': EquipmentAssignmentModel.objects.filter(delete_field='no', status='Assigned').count(),
            'available': EquipmentModel.objects.filter(delete_field='no', status='Good')
                        .exclude(id__in=EquipmentAssignmentModel.objects.filter(
                            delete_field='no', 
                            status='Assigned',
                            return_date__isnull=True
                        ).values_list('equipment_id', flat=True)).count(),
        }
        
        # Outbreak Statistics
        outbreak_stats = {
            'total': OutbreakFarm.objects.filter(delete_field='no').count(),
            'by_status': list(OutbreakFarm.objects.filter(delete_field='no')
                             .values('status')
                             .annotate(count=Count('id'))),
            'by_severity': list(OutbreakFarm.objects.filter(delete_field='no')
                               .values('severity')
                               .annotate(count=Count('id'))),
            'by_disease': list(OutbreakFarm.objects.filter(delete_field='no')
                              .values('disease_type')
                              .annotate(count=Count('id'))
                              .order_by('-count')[:10]),
            'by_district': list(OutbreakFarm.objects.filter(delete_field='no', district__isnull=False)
                               .values('district__name')
                               .annotate(count=Count('id'))
                               .order_by('-count')[:10]),
            'active': OutbreakFarm.objects.filter(delete_field='no', status__in=[0, 1, 2]).count(),
            'resolved': OutbreakFarm.objects.filter(delete_field='no', status=3).count(),
        }
        
        # Activity Statistics
        activity_stats = {
            'total_reports': DailyReportingModel.objects.filter(delete_field='no').count(),
            'reports_today': DailyReportingModel.objects.filter(
                delete_field='no', 
                reporting_date=date.today()
            ).count(),
            'reports_this_week': DailyReportingModel.objects.filter(
                delete_field='no',
                reporting_date__gte=start_date
            ).count(),
            'total_area_covered': DailyReportingModel.objects.filter(delete_field='no')
                                 .aggregate(total=Sum('area_covered_ha'))['total'] or 0,
            'by_activity': list(DailyReportingModel.objects.filter(delete_field='no', activity__isnull=False)
                               .values('activity__sub_activity')
                               .annotate(count=Count('id'))
                               .order_by('-count')[:10]),
        }
        
        # Payment Statistics
        payment_stats = {
            'total_payments': PaymentReport.objects.filter(delete_field='no').count(),
            'total_amount': float(PaymentReport.objects.filter(delete_field='no')
                                 .aggregate(total=Sum('salary'))['total'] or 0),
            'pending_amount': float(PaymentReport.objects.filter(delete_field='no')
                                   .aggregate(total=Sum('salary'))['total'] or 0),
            'by_month': list(PaymentReport.objects.filter(delete_field='no')
                            .values('month', 'year')
                            .annotate(
                                count=Count('id'),
                                total=Sum('salary')
                            )
                            .order_by('-year', '-month')[:12]),
        }
        
        # Geographic Statistics
        geo_stats = {
            'regions': Region.objects.filter(delete_field='no').count(),
            'districts': cocoaDistrict.objects.filter(delete_field='no').count(),
            'communities': Community.objects.filter(delete_field='no').count(),
            'projects': projectTbl.objects.filter(delete_field='no').count(),
            'top_districts_farms': list(FarmdetailsTbl.objects.filter(delete_field='no', district__isnull=False)
                                        .values('district__name')
                                        .annotate(count=Count('id'))
                                        .order_by('-count')[:10]),
            'top_districts_ras': list(PersonnelModel.objects.filter(
                                        delete_field='no', 
                                        district__isnull=False,
                                        personnel_type='Rehab Assistant'
                                    )
                                    .values('district__name')
                                    .annotate(count=Count('id'))
                                    .order_by('-count')[:10]),
        }
        
        # Feedback and Issues
        feedback_stats = {
            'open_feedback': Feedback.objects.filter(delete_field='no', Status='Open').count(),
            'in_progress_feedback': Feedback.objects.filter(delete_field='no', Status='In Progress').count(),
            'resolved_feedback': Feedback.objects.filter(delete_field='no', Status='Resolved').count(),
            'open_issues': IssueModel.objects.filter(delete_field='no', status=0).count(),
            'submitted_issues': IssueModel.objects.filter(delete_field='no', status=1).count(),
        }
        
        # Trend data for charts
        trend_data = {
            'farms_created': list(FarmdetailsTbl.objects.filter(
                                    delete_field='no',
                                    created_date__gte=start_date
                                )
                                .annotate(day=TruncDay('created_date'))
                                .values('day')
                                .annotate(count=Count('id'))
                                .order_by('day')),
            
            'reports_submitted': list(DailyReportingModel.objects.filter(
                                        delete_field='no',
                                        reporting_date__gte=start_date
                                    )
                                    .annotate(day=TruncDay('reporting_date'))
                                    .values('day')
                                    .annotate(count=Count('id'))
                                    .order_by('day')),
            
            'assignments_created': list(PersonnelAssignmentModel.objects.filter(
                                        delete_field='no',
                                        created_date__gte=start_date
                                    )
                                    .annotate(day=TruncDay('created_date'))
                                    .values('day')
                                    .annotate(count=Count('id'))
                                    .order_by('day')),
            
            'outbreaks_reported': list(OutbreakFarm.objects.filter(
                                        delete_field='no',
                                        date_reported__gte=start_date
                                    )
                                    .annotate(day=TruncDay('date_reported'))
                                    .values('day')
                                    .annotate(count=Count('id'))
                                    .order_by('day')),
        }
        
        response = {
            'success': True,
            'personnel_stats': personnel_stats,
            'staff_stats': staff_stats,
            'farm_stats': farm_stats,
            'assignment_stats': assignment_stats,
            'contractor_stats': contractor_stats,
            'equipment_stats': equipment_stats,
            'outbreak_stats': outbreak_stats,
            'activity_stats': activity_stats,
            'payment_stats': payment_stats,
            'geo_stats': geo_stats,
            'feedback_stats': feedback_stats,
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
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_recent_activities(request):
    """Get recent activities across all modules"""
    try:
        limit = int(request.GET.get('limit', 20))
        activities = []
        
        # Recent farm creations
        farms = FarmdetailsTbl.objects.filter(delete_field='no').order_by('-created_date')[:5]
        for farm in farms:
            activities.append({
                'id': farm.id,
                'type': 'farm',
                'icon': 'fas fa-tractor',
                'icon_bg': 'bg-primary',
                'title': f"Farm Created: {farm.farm_reference}",
                'description': f"{farm.farmername} - {farm.district.name if farm.district else 'N/A'}",
                'time': farm.created_date.strftime('%Y-%m-%d %H:%M'),
                'timestamp': farm.created_date.isoformat() if farm.created_date else None,
                'url': f"/farms/{farm.id}/"
            })
        
        # Recent personnel additions
        personnel = PersonnelModel.objects.filter(delete_field='no').order_by('-created_date')[:5]
        for person in personnel:
            activities.append({
                'id': person.id,
                'type': 'personnel',
                'icon': 'fas fa-user-tie',
                'icon_bg': 'bg-success',
                'title': f"New Staff: {person.first_name} {person.surname}",
                'description': f"{person.personnel_type} - {person.staff_id}",
                'time': person.created_date.strftime('%Y-%m-%d %H:%M'),
                'timestamp': person.created_date.isoformat() if person.created_date else None,
                'url': f"/personnel/staff/{person.id}/"
            })
        
        # Recent assignments
        assignments = PersonnelAssignmentModel.objects.filter(delete_field='no').select_related('ra', 'po').order_by('-created_date')[:5]
        for assign in assignments:
            ra_name = f"{assign.ra.first_name} {assign.ra.surname}" if assign.ra else 'Unknown'
            po_name = f"{assign.po.first_name} {assign.po.last_name}" if assign.po else 'Unknown'
            activities.append({
                'id': assign.id,
                'type': 'assignment',
                'icon': 'fas fa-user-tag',
                'icon_bg': 'bg-info',
                'title': f"RA Assigned: {ra_name}",
                'description': f"To PO: {po_name} - {assign.district.name if assign.district else 'N/A'}",
                'time': assign.created_date.strftime('%Y-%m-%d %H:%M'),
                'timestamp': assign.created_date.isoformat() if assign.created_date else None,
                'url': f"/personnel/assignments/{assign.id}/"
            })
        
        # Recent daily reports
        reports = DailyReportingModel.objects.filter(delete_field='no').select_related('agent', 'activity').order_by('-created_date')[:5]
        for report in reports:
            activities.append({
                'id': report.id,
                'type': 'report',
                'icon': 'fas fa-file-alt',
                'icon_bg': 'bg-warning',
                'title': f"Activity Report: {report.activity.sub_activity if report.activity else 'N/A'}",
                # 'description': f"By: {report.agent.first_name} {report.agent.last_name if report.agent else 'Unknown'} - {report.area_covered_ha} ha",
                'time': report.created_date.strftime('%Y-%m-%d %H:%M'),
                'timestamp': report.created_date.isoformat() if report.created_date else None,
                'url': f"/reports/{report.id}/"
            })
        
        # Recent outbreaks
        outbreaks = OutbreakFarm.objects.filter(delete_field='no').select_related('reported_by', 'district').order_by('-created_date')[:5]
        for outbreak in outbreaks:
            activities.append({
                'id': outbreak.id,
                'type': 'outbreak',
                'icon': 'fas fa-exclamation-triangle',
                'icon_bg': 'bg-danger',
                'title': f"Outbreak: {outbreak.disease_type}",
                'description': f"{outbreak.farmer_name} - {outbreak.district.name if outbreak.district else 'N/A'}",
                'time': outbreak.created_date.strftime('%Y-%m-%d %H:%M'),
                'timestamp': outbreak.created_date.isoformat() if outbreak.created_date else None,
                'url': f"/outbreaks/{outbreak.id}/"
            })
        
        # Recent contractors
        contractors = contractorsTbl.objects.filter(delete_field='no').order_by('-created_date')[:5]
        for contractor in contractors:
            activities.append({
                'id': contractor.id,
                'type': 'contractor',
                'icon': 'fas fa-handshake',
                'icon_bg': 'bg-secondary',
                'title': f"New Contractor: {contractor.contractor_name}",
                'description': f"{contractor.interested_services} - {contractor.contact_person}",
                'time': contractor.created_date.strftime('%Y-%m-%d %H:%M'),
                'timestamp': contractor.created_date.isoformat() if contractor.created_date else None,
                'url': f"/personnel/contractors/{contractor.id}/"
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
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_chart_data(request):
    """Get data for dashboard charts"""
    try:
        chart_type = request.GET.get('type', 'farms_by_district')
        limit = int(request.GET.get('limit', 10))
        
        data = []
        labels = []
        
        if chart_type == 'farms_by_district':
            queryset = FarmdetailsTbl.objects.filter(
                delete_field='no', 
                district__isnull=False
            ).values('district__name').annotate(
                count=Count('id')
            ).order_by('-count')[:limit]
            
            for item in queryset:
                labels.append(item['district__name'])
                data.append(item['count'])
                
        elif chart_type == 'personnel_by_type':
            queryset = PersonnelModel.objects.filter(
                delete_field='no'
            ).values('personnel_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            for item in queryset:
                labels.append(item['personnel_type'])
                data.append(item['count'])
                
        elif chart_type == 'farms_by_status':
            queryset = FarmdetailsTbl.objects.filter(
                delete_field='no'
            ).values('status').annotate(
                count=Count('id')
            )
            
            for item in queryset:
                labels.append(item['status'] or 'Unknown')
                data.append(item['count'])
                
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
                
        elif chart_type == 'outbreaks_by_severity':
            queryset = OutbreakFarm.objects.filter(
                delete_field='no'
            ).values('severity').annotate(
                count=Count('id')
            )
            
            for item in queryset:
                labels.append(item['severity'])
                data.append(item['count'])
                
        elif chart_type == 'equipment_by_status':
            queryset = EquipmentModel.objects.filter(
                delete_field='no'
            ).values('status').annotate(
                count=Count('id')
            )
            
            for item in queryset:
                labels.append(item['status'])
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
                
        elif chart_type == 'daily_reports_trend':
            days = int(request.GET.get('days', 30))
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            queryset = DailyReportingModel.objects.filter(
                delete_field='no',
                reporting_date__gte=start_date
            ).annotate(
                day=TruncDay('reporting_date')
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')
            
            for item in queryset:
                labels.append(item['day'].strftime('%Y-%m-%d') if item['day'] else '')
                data.append(item['count'])
                
        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data,
            'chart_type': chart_type
        })
        
    except Exception as e:
        print(f"Error in get_chart_data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_upcoming_tasks(request):
    """Get upcoming tasks and deadlines"""
    try:
        tasks = []
        
        # Expiring certificates
        expiring_certs = ContractorCertificateModel.objects.filter(
            delete_field='no',
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
                'url': f"/personnel/contractors/{cert.contractor.id}/" if cert.contractor else '#'
            })
        
        # Overdue equipment returns
        overdue_equipment = EquipmentAssignmentModel.objects.filter(
            delete_field='no',
            return_date__isnull=False,
            return_date__lt=date.today(),
            status='Assigned'
        ).select_related('equipment', 'assigned_to')[:5]
        
        for equip in overdue_equipment:
            days_overdue = (date.today() - equip.return_date).days
            tasks.append({
                'id': equip.id,
                'type': 'equipment',
                'title': f"Equipment Overdue: {equip.equipment.equipment if equip.equipment else 'Unknown'}",
                'description': f"Assigned to {equip.assigned_to.first_name} {equip.assigned_to.last_name} - {days_overdue} days overdue",
                'due_date': equip.return_date.strftime('%Y-%m-%d'),
                'priority': 'high',
                'url': f"/equipment/assignments/{equip.id}/"
            })
        
        # Pending assignments
        pending_assignments = PersonnelAssignmentModel.objects.filter(
            delete_field='no',
            status=0
        ).select_related('ra', 'po')[:5]
        
        for assign in pending_assignments:
            days_pending = (date.today() - assign.date_assigned).days if assign.date_assigned else 0
            tasks.append({
                'id': assign.id,
                'type': 'assignment',
                # 'title': f"Pending Assignment: {assign.ra.first_name} {assign.ra.surname if assign.ra else 'Unknown'}",
                # 'description': f"Assigned to {assign.po.first_name} {assign.po.last_name if assign.po else 'Unknown'} - {days_pending} days pending",
                'due_date': assign.date_assigned.strftime('%Y-%m-%d') if assign.date_assigned else '',
                'priority': 'high' if days_pending > 7 else 'medium',
                'url': f"/personnel/assignments/{assign.id}/"
            })
        
        # Pending verifications
        pending_verifications = ContractorCertificateVerificationModel.objects.filter(
            delete_field='no',
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
                'url': f"/personnel/contractors/{verif.certificate.contractor.id}/" if verif.certificate and verif.certificate.contractor else '#'
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
    """Get user notifications"""
    try:
        # This is a simplified version - you can expand based on your notification model
        notifications = []
        
        # Today's reports
        reports_today = DailyReportingModel.objects.filter(
            delete_field='no',
            reporting_date=date.today()
        ).count()
        
        if reports_today > 0:
            notifications.append({
                'id': f'reports_{date.today()}',
                'type': 'info',
                'icon': 'fas fa-file-alt',
                'icon_bg': 'bg-info',
                'title': f'{reports_today} Activity Report(s) Submitted Today',
                'description': 'New reports are ready for review',
                'time': 'Just now',
                'read': False
            })
        
        # Pending outbreaks
        pending_outbreaks = OutbreakFarm.objects.filter(
            delete_field='no',
            status=0
        ).count()
        
        if pending_outbreaks > 0:
            notifications.append({
                'id': f'outbreaks_{date.today()}',
                'type': 'warning',
                'icon': 'fas fa-exclamation-triangle',
                'icon_bg': 'bg-warning',
                'title': f'{pending_outbreaks} Pending Outbreak Report(s)',
                'description': 'New outbreak reports require attention',
                'time': 'Today',
                'read': False
            })
        
        # Low equipment
        low_equipment = EquipmentModel.objects.filter(
            delete_field='no',
            status='Bad'
        ).count()
        
        if low_equipment > 0:
            notifications.append({
                'id': 'equipment_low',
                'type': 'danger',
                'icon': 'fas fa-tools',
                'icon_bg': 'bg-danger',
                'title': f'{low_equipment} Equipment Item(s) in Bad Condition',
                'description': 'Equipment requires maintenance or replacement',
                'time': 'Today',
                'read': False
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications
        })
        
    except Exception as e:
        print(f"Error in get_notifications: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)