# views.py - Add these views

import json
import uuid
import csv
from datetime import datetime, date
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from portal.models import (
    PaymentReport, DetailedPaymentReport,
    PersonnelModel, staffTbl, FarmdetailsTbl,
    Activities, cocoaDistrict, projectTbl
)
import logging

logger = logging.getLogger(__name__)

# ============== PAYMENT REPORTS PAGE ==============

@login_required
def payment_reports_page(request):
    """Render the Payment Reports management page"""
    # Get current year and months for filters
    current_year = datetime.now().year
    years = range(current_year - 5, current_year + 1)
    months = [
        {'value': 'January', 'label': 'January'},
        {'value': 'February', 'label': 'February'},
        {'value': 'March', 'label': 'March'},
        {'value': 'April', 'label': 'April'},
        {'value': 'May', 'label': 'May'},
        {'value': 'June', 'label': 'June'},
        {'value': 'July', 'label': 'July'},
        {'value': 'August', 'label': 'August'},
        {'value': 'September', 'label': 'September'},
        {'value': 'October', 'label': 'October'},
        {'value': 'November', 'label': 'November'},
        {'value': 'December', 'label': 'December'},
    ]
    
    weeks = [f'Week {i}' for i in range(1, 5)]
    
    payment_options = ['Bank Transfer', 'Mobile Money', 'Cash', 'Cheque', 'E-Zwich']
    
    context = {
        'years': years,
        'months': months,
        'weeks': weeks,
        'payment_options': payment_options,
    }
    return render(request, 'portal/payment/payment_reports.html', context)


# ============== PAYMENT REPORT API VIEWS ==============

@login_required
@require_http_methods(["GET"])
def payment_report_list(request):
    """Get paginated list of payment reports"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Filter parameters
        year = request.GET.get('year')
        month = request.GET.get('month')
        week = request.GET.get('week')
        district_id = request.GET.get('district_id')
        project_id = request.GET.get('project_id')
        payment_option = request.GET.get('payment_option')
        
        # Base queryset
        queryset = PaymentReport.objects.filter(delete_field='no').select_related(
            'ra', 'district', 'projectTbl_foreignkey'
        ).order_by('-created_date')
        
        # Apply filters
        if year:
            queryset = queryset.filter(year=year)
        if month:
            queryset = queryset.filter(month=month)
        if week:
            queryset = queryset.filter(week=week)
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        if project_id:
            queryset = queryset.filter(projectTbl_foreignkey_id=project_id)
        if payment_option:
            queryset = queryset.filter(payment_option=payment_option)
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(ra_name__icontains=search_value) |
                Q(po_number__icontains=search_value) |
                Q(month__icontains=search_value) |
                Q(district__name__icontains=search_value)
            )
        
        # Get total counts
        total_records = queryset.count()
        
        # Apply pagination
        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        page_obj = paginator.get_page(page_number)
        
        # Prepare data
        data = []
        for report in page_obj:
            data.append({
                'id': report.id,
                'uid': report.uid,
                'ra_id': report.ra.id if report.ra else None,
                'ra_name': report.ra_name or (report.ra.get_full_name() if report.ra else 'N/A'),
                'district_id': report.district.id if report.district else None,
                'district_name': report.district.name if report.district else 'N/A',
                'bank_name': report.bank_name,
                'bank_branch': report.bank_branch,
                'snnit_no': report.snnit_no,
                'salary': float(report.salary) if report.salary else 0,
                'year': report.year,
                'month': report.month,
                'week': report.week,
                'po_number': report.po_number,
                'payment_option': report.payment_option,
                'momo_acc': report.momo_acc,
                'project_id': report.projectTbl_foreignkey.id if report.projectTbl_foreignkey else None,
                'project_name': report.projectTbl_foreignkey.name if report.projectTbl_foreignkey else 'N/A',
                'created_date': report.created_date.strftime('%Y-%m-%d %H:%M:%S') if report.created_date else None,
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
        logger.error(f"Error in payment_report_list: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e),
            'data': []
        })


@login_required
@require_http_methods(["GET"])
def payment_report_summary(request):
    """Get summary statistics for payment reports"""
    try:
        # Get filter parameters
        year = request.GET.get('year')
        month = request.GET.get('month')
        district_id = request.GET.get('district_id')
        
        # Base queryset
        queryset = PaymentReport.objects.filter(delete_field='no')
        
        if year:
            queryset = queryset.filter(year=year)
        if month:
            queryset = queryset.filter(month=month)
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        
        # Get summary stats
        total_reports = queryset.count()
        total_salary = queryset.aggregate(Sum('salary'))['salary__sum'] or 0
        avg_salary = queryset.aggregate(Avg('salary'))['salary__avg'] or 0
        
        # Count by payment option
        payment_options = queryset.values('payment_option').annotate(
            count=Count('id'),
            total=Sum('salary')
        ).order_by('payment_option')
        
        # Count by month if year filter applied
        monthly_breakdown = []
        if year:
            monthly_breakdown = queryset.values('month').annotate(
                count=Count('id'),
                total=Sum('salary')
            ).order_by('month')
        
        # Get recent reports
        recent_reports = queryset.order_by('-created_date')[:5].values(
            'ra_name', 'month', 'year', 'salary'
        )
        
        data = {
            'total_reports': total_reports,
            'total_salary': float(total_salary),
            'avg_salary': float(avg_salary),
            'payment_options': list(payment_options),
            'monthly_breakdown': list(monthly_breakdown),
            'recent_reports': list(recent_reports),
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error in payment_report_summary: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def payment_report_create(request):
    """Create a new payment report"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['ra_id', 'year', 'month', 'salary']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required'
                })
        
        # Create payment report
        report = PaymentReport()
        report.uid = str(uuid.uuid4())
        
        # Set RA
        if data.get('ra_id'):
            try:
                ra = PersonnelModel.objects.get(id=data['ra_id'])
                report.ra = ra
                report.ra_name = f"{ra.first_name} {ra.surname}"
            except PersonnelModel.DoesNotExist:
                pass
        
        # Set other fields
        report.bank_name = data.get('bank_name')
        report.bank_branch = data.get('bank_branch')
        report.snnit_no = data.get('snnit_no')
        report.salary = data.get('salary')
        report.year = data.get('year')
        report.month = data.get('month')
        report.week = data.get('week')
        report.po_number = data.get('po_number')
        report.payment_option = data.get('payment_option')
        report.momo_acc = data.get('momo_acc')
        
        # Set foreign keys
        if data.get('district_id'):
            try:
                report.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        
        if data.get('project_id'):
            try:
                report.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                pass
        
        report.save()
        
        # Create detailed payment records if provided
        if data.get('detailed_payments'):
            for detail in data['detailed_payments']:
                detailed = DetailedPaymentReport()
                detailed.uid = str(uuid.uuid4())
                detailed.group_code = detail.get('group_code')
                
                if detail.get('ra_id'):
                    try:
                        detailed.ra = PersonnelModel.objects.get(id=detail['ra_id'])
                    except PersonnelModel.DoesNotExist:
                        pass
                
                detailed.ra_name = detail.get('ra_name') or report.ra_name
                detailed.ra_account = detail.get('ra_account')
                
                if detail.get('po_id'):
                    try:
                        detailed.po = staffTbl.objects.get(id=detail['po_id'])
                    except staffTbl.DoesNotExist:
                        pass
                
                detailed.po_name = detail.get('po_name')
                detailed.po_number = detail.get('po_number') or report.po_number
                
                if detail.get('district_id'):
                    try:
                        detailed.district = cocoaDistrict.objects.get(id=detail['district_id'])
                    except cocoaDistrict.DoesNotExist:
                        pass
                
                if detail.get('project_id'):
                    try:
                        detailed.projectTbl_foreignkey = projectTbl.objects.get(id=detail['project_id'])
                    except projectTbl.DoesNotExist:
                        pass
                
                detailed.farmhands_type = detail.get('farmhands_type')
                
                if detail.get('farm_id'):
                    try:
                        detailed.farm = FarmdetailsTbl.objects.get(id=detail['farm_id'])
                    except FarmdetailsTbl.DoesNotExist:
                        pass
                
                detailed.farm_reference = detail.get('farm_reference')
                detailed.number_in_a_group = detail.get('number_in_a_group')
                
                if detail.get('activity_id'):
                    try:
                        detailed.activity = Activities.objects.get(id=detail['activity_id'])
                    except Activities.DoesNotExist:
                        pass
                
                detailed.farmsize = detail.get('farmsize')
                detailed.achievement = detail.get('achievement')
                detailed.amount = detail.get('amount')
                detailed.week = detail.get('week') or report.week
                detailed.month = detail.get('month') or report.month
                detailed.year = detail.get('year') or report.year
                detailed.issue = detail.get('issue')
                detailed.sector = detail.get('sector')
                detailed.act_code = detail.get('act_code')
                
                detailed.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment report created successfully',
            'data': {'id': report.id}
        })
        
    except Exception as e:
        logger.error(f"Error in payment_report_create: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["GET"])
def payment_report_detail(request, pk):
    """Get payment report details with detailed records"""
    try:
        report = PaymentReport.objects.select_related(
            'ra', 'district', 'projectTbl_foreignkey'
        ).get(pk=pk, delete_field='no')
        
        # Get detailed payment records
        detailed_payments = DetailedPaymentReport.objects.filter(
            delete_field='no'
        ).select_related('ra', 'po', 'farm', 'activity').order_by('-created_date')
        
        # Filter by report criteria (month, year, ra, etc.)
        if report.ra:
            detailed_payments = detailed_payments.filter(ra=report.ra)
        if report.month:
            detailed_payments = detailed_payments.filter(month=report.month)
        if report.year:
            detailed_payments = detailed_payments.filter(year=report.year)
        if report.week:
            detailed_payments = detailed_payments.filter(week=report.week)
        
        detailed_data = []
        for d in detailed_payments:
            detailed_data.append({
                'id': d.id,
                'uid': d.uid,
                'group_code': d.group_code,
                'ra_id': d.ra.id if d.ra else None,
                'ra_name': d.ra_name or (d.ra.get_full_name() if d.ra else 'N/A'),
                'ra_account': d.ra_account,
                'po_id': d.po.id if d.po else None,
                'po_name': d.po_name or (d.po.get_full_name() if d.po else 'N/A'),
                'po_number': d.po_number,
                'district_id': d.district.id if d.district else None,
                'district_name': d.district.name if d.district else 'N/A',
                'project_id': d.projectTbl_foreignkey.id if d.projectTbl_foreignkey else None,
                'project_name': d.projectTbl_foreignkey.name if d.projectTbl_foreignkey else 'N/A',
                'farmhands_type': d.farmhands_type,
                'farm_id': d.farm.id if d.farm else None,
                'farm_reference': d.farm_reference,
                'number_in_a_group': d.number_in_a_group,
                'activity_id': d.activity.id if d.activity else None,
                'activity_name': d.activity.sub_activity if d.activity else 'N/A',
                'farmsize': float(d.farmsize) if d.farmsize else 0,
                'achievement': float(d.achievement) if d.achievement else 0,
                'amount': float(d.amount) if d.amount else 0,
                'week': d.week,
                'month': d.month,
                'year': d.year,
                'issue': d.issue,
                'sector': d.sector,
                'act_code': d.act_code,
                'created_date': d.created_date.strftime('%Y-%m-%d %H:%M:%S') if d.created_date else None,
            })
        
        data = {
            'id': report.id,
            'uid': report.uid,
            'ra_id': report.ra.id if report.ra else None,
            'ra_name': report.ra_name or (report.ra.get_full_name() if report.ra else 'N/A'),
            'district_id': report.district.id if report.district else None,
            'district_name': report.district.name if report.district else 'N/A',
            'bank_name': report.bank_name,
            'bank_branch': report.bank_branch,
            'snnit_no': report.snnit_no,
            'salary': float(report.salary) if report.salary else 0,
            'year': report.year,
            'month': report.month,
            'week': report.week,
            'po_number': report.po_number,
            'payment_option': report.payment_option,
            'momo_acc': report.momo_acc,
            'project_id': report.projectTbl_foreignkey.id if report.projectTbl_foreignkey else None,
            'project_name': report.projectTbl_foreignkey.name if report.projectTbl_foreignkey else 'N/A',
            'created_date': report.created_date.strftime('%Y-%m-%d %H:%M:%S') if report.created_date else None,
            'detailed_payments': detailed_data,
            'total_detailed_amount': sum(d['amount'] for d in detailed_data),
            'total_detailed_count': len(detailed_data)
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except PaymentReport.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Payment report not found'
        })
    except Exception as e:
        logger.error(f"Error in payment_report_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def payment_report_update(request, pk):
    """Update payment report"""
    try:
        report = PaymentReport.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body)
        
        # Update RA if provided
        if data.get('ra_id'):
            try:
                ra = PersonnelModel.objects.get(id=data['ra_id'])
                report.ra = ra
                report.ra_name = f"{ra.first_name} {ra.surname}"
            except PersonnelModel.DoesNotExist:
                pass
        
        # Update other fields
        if data.get('bank_name') is not None:
            report.bank_name = data['bank_name']
        if data.get('bank_branch') is not None:
            report.bank_branch = data['bank_branch']
        if data.get('snnit_no') is not None:
            report.snnit_no = data['snnit_no']
        if data.get('salary') is not None:
            report.salary = data['salary']
        if data.get('year') is not None:
            report.year = data['year']
        if data.get('month') is not None:
            report.month = data['month']
        if data.get('week') is not None:
            report.week = data['week']
        if data.get('po_number') is not None:
            report.po_number = data['po_number']
        if data.get('payment_option') is not None:
            report.payment_option = data['payment_option']
        if data.get('momo_acc') is not None:
            report.momo_acc = data['momo_acc']
        
        # Update foreign keys
        if data.get('district_id'):
            try:
                report.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        elif 'district_id' in data and data['district_id'] is None:
            report.district = None
        
        if data.get('project_id'):
            try:
                report.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                pass
        elif 'project_id' in data and data['project_id'] is None:
            report.projectTbl_foreignkey = None
        
        report.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment report updated successfully'
        })
        
    except PaymentReport.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Payment report not found'
        })
    except Exception as e:
        logger.error(f"Error in payment_report_update: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def payment_report_delete(request, pk):
    """Soft delete payment report"""
    try:
        report = PaymentReport.objects.get(pk=pk, delete_field='no')
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', 'No reason provided')
        
        # Soft delete
        report.delete_field = 'yes'
        report.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment report deleted successfully'
        })
        
    except PaymentReport.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Payment report not found'
        })
    except Exception as e:
        logger.error(f"Error in payment_report_delete: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# ============== DETAILED PAYMENT REPORT API VIEWS ==============

@login_required
@require_http_methods(["GET"])
def detailed_payment_report_list(request):
    """Get paginated list of detailed payment reports"""
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Filter parameters
        report_id = request.GET.get('report_id')
        ra_id = request.GET.get('ra_id')
        po_id = request.GET.get('po_id')
        month = request.GET.get('month')
        year = request.GET.get('year')
        week = request.GET.get('week')
        district_id = request.GET.get('district_id')
        
        # Base queryset
        queryset = DetailedPaymentReport.objects.filter(delete_field='no').select_related(
            'ra', 'po', 'farm', 'activity', 'district', 'projectTbl_foreignkey'
        ).order_by('-created_date')
        
        # Apply filters
        if report_id:
            # Filter by report - need to match criteria
            try:
                report = PaymentReport.objects.get(id=report_id)
                if report.ra:
                    queryset = queryset.filter(ra=report.ra)
                if report.month:
                    queryset = queryset.filter(month=report.month)
                if report.year:
                    queryset = queryset.filter(year=report.year)
                if report.week:
                    queryset = queryset.filter(week=report.week)
            except PaymentReport.DoesNotExist:
                pass
        
        if ra_id:
            queryset = queryset.filter(ra_id=ra_id)
        if po_id:
            queryset = queryset.filter(po_id=po_id)
        if month:
            queryset = queryset.filter(month=month)
        if year:
            queryset = queryset.filter(year=year)
        if week:
            queryset = queryset.filter(week=week)
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        
        # Apply search
        if search_value:
            queryset = queryset.filter(
                Q(ra_name__icontains=search_value) |
                Q(po_name__icontains=search_value) |
                Q(farm_reference__icontains=search_value) |
                Q(group_code__icontains=search_value) |
                Q(month__icontains=search_value)
            )
        
        # Get total counts
        total_records = queryset.count()
        
        # Apply pagination
        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        page_obj = paginator.get_page(page_number)
        
        # Prepare data
        data = []
        for d in page_obj:
            data.append({
                'id': d.id,
                'uid': d.uid,
                'group_code': d.group_code,
                'ra_id': d.ra.id if d.ra else None,
                'ra_name': d.ra_name or (d.ra.get_full_name() if d.ra else 'N/A'),
                'ra_account': d.ra_account,
                'po_id': d.po.id if d.po else None,
                'po_name': d.po_name or (d.po.get_full_name() if d.po else 'N/A'),
                'po_number': d.po_number,
                'district_id': d.district.id if d.district else None,
                'district_name': d.district.name if d.district else 'N/A',
                'project_id': d.projectTbl_foreignkey.id if d.projectTbl_foreignkey else None,
                'project_name': d.projectTbl_foreignkey.name if d.projectTbl_foreignkey else 'N/A',
                'farmhands_type': d.farmhands_type,
                'farm_id': d.farm.id if d.farm else None,
                'farm_reference': d.farm_reference,
                'number_in_a_group': d.number_in_a_group,
                'activity_id': d.activity.id if d.activity else None,
                'activity_name': d.activity.sub_activity if d.activity else 'N/A',
                'farmsize': float(d.farmsize) if d.farmsize else 0,
                'achievement': float(d.achievement) if d.achievement else 0,
                'amount': float(d.amount) if d.amount else 0,
                'week': d.week,
                'month': d.month,
                'year': d.year,
                'issue': d.issue,
                'sector': d.sector,
                'act_code': d.act_code,
                'created_date': d.created_date.strftime('%Y-%m-%d %H:%M:%S') if d.created_date else None,
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
        logger.error(f"Error in detailed_payment_report_list: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e),
            'data': []
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def detailed_payment_report_create(request):
    """Create a new detailed payment record"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['ra_id', 'amount', 'month', 'year']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required'
                })
        
        # Create detailed payment
        detailed = DetailedPaymentReport()
        detailed.uid = str(uuid.uuid4())
        detailed.group_code = data.get('group_code')
        
        # Set RA
        if data.get('ra_id'):
            try:
                ra = PersonnelModel.objects.get(id=data['ra_id'])
                detailed.ra = ra
                detailed.ra_name = f"{ra.first_name} {ra.surname}"
            except PersonnelModel.DoesNotExist:
                pass
        
        detailed.ra_account = data.get('ra_account')
        
        # Set PO
        if data.get('po_id'):
            try:
                po = staffTbl.objects.get(id=data['po_id'])
                detailed.po = po
                detailed.po_name = f"{po.first_name} {po.last_name}"
            except staffTbl.DoesNotExist:
                pass
        
        detailed.po_number = data.get('po_number')
        
        # Set foreign keys
        if data.get('district_id'):
            try:
                detailed.district = cocoaDistrict.objects.get(id=data['district_id'])
            except cocoaDistrict.DoesNotExist:
                pass
        
        if data.get('project_id'):
            try:
                detailed.projectTbl_foreignkey = projectTbl.objects.get(id=data['project_id'])
            except projectTbl.DoesNotExist:
                pass
        
        detailed.farmhands_type = data.get('farmhands_type')
        
        # Set farm
        if data.get('farm_id'):
            try:
                detailed.farm = FarmdetailsTbl.objects.get(id=data['farm_id'])
                if not detailed.farm_reference:
                    detailed.farm_reference = detailed.farm.farm_reference
            except FarmdetailsTbl.DoesNotExist:
                pass
        
        detailed.farm_reference = data.get('farm_reference') or detailed.farm_reference
        detailed.number_in_a_group = data.get('number_in_a_group')
        
        # Set activity
        if data.get('activity_id'):
            try:
                detailed.activity = Activities.objects.get(id=data['activity_id'])
            except Activities.DoesNotExist:
                pass
        
        detailed.farmsize = data.get('farmsize')
        detailed.achievement = data.get('achievement')
        detailed.amount = data.get('amount')
        detailed.week = data.get('week')
        detailed.month = data.get('month')
        detailed.year = data.get('year')
        detailed.issue = data.get('issue')
        detailed.sector = data.get('sector')
        detailed.act_code = data.get('act_code')
        
        detailed.save()
        
        # Check if we need to update/create summary report
        if detailed.ra and detailed.month and detailed.year:
            # Try to find existing summary report
            summary = PaymentReport.objects.filter(
                ra=detailed.ra,
                month=detailed.month,
                year=detailed.year,
                delete_field='no'
            ).first()
            
            if not summary:
                # Create new summary
                summary = PaymentReport()
                summary.uid = str(uuid.uuid4())
                summary.ra = detailed.ra
                summary.ra_name = detailed.ra_name
                summary.district = detailed.district
                summary.projectTbl_foreignkey = detailed.projectTbl_foreignkey
                summary.month = detailed.month
                summary.year = detailed.year
                summary.week = detailed.week
                summary.po_number = detailed.po_number
                summary.payment_option = data.get('payment_option', 'Bank Transfer')
                summary.save()
            
            # Update summary salary
            if summary:
                total_amount = DetailedPaymentReport.objects.filter(
                    ra=detailed.ra,
                    month=detailed.month,
                    year=detailed.year,
                    delete_field='no'
                ).aggregate(Sum('amount'))['amount__sum'] or 0
                
                summary.salary = total_amount
                summary.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Detailed payment record created successfully',
            'data': {'id': detailed.id}
        })
        
    except Exception as e:
        logger.error(f"Error in detailed_payment_report_create: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def generate_payment_report(request):
    """Generate payment report for selected period"""
    try:
        data = json.loads(request.body)
        
        month = data.get('month')
        year = data.get('year')
        week = data.get('week')
        district_id = data.get('district_id')
        project_id = data.get('project_id')
        
        if not month or not year:
            return JsonResponse({
                'success': False,
                'message': 'Month and year are required'
            })
        
        # Get all detailed payments for the period
        detailed_payments = DetailedPaymentReport.objects.filter(
            month=month,
            year=year,
            delete_field='no'
        )
        
        if week:
            detailed_payments = detailed_payments.filter(week=week)
        if district_id:
            detailed_payments = detailed_payments.filter(district_id=district_id)
        if project_id:
            detailed_payments = detailed_payments.filter(projectTbl_foreignkey_id=project_id)
        
        # Group by RA
        ra_groups = {}
        for payment in detailed_payments:
            key = f"{payment.ra_id}_{payment.month}_{payment.year}"
            if key not in ra_groups:
                ra_groups[key] = {
                    'ra_id': payment.ra_id,
                    'ra_name': payment.ra_name,
                    'district_id': payment.district_id,
                    'project_id': payment.projectTbl_foreignkey_id,
                    'month': payment.month,
                    'year': payment.year,
                    'week': payment.week,
                    'total_amount': 0,
                    'payment_count': 0,
                    'po_numbers': set()
                }
            
            ra_groups[key]['total_amount'] += float(payment.amount or 0)
            ra_groups[key]['payment_count'] += 1
            if payment.po_number:
                ra_groups[key]['po_numbers'].add(payment.po_number)
        
        # Create or update summary reports
        created_count = 0
        updated_count = 0
        
        for key, group in ra_groups.items():
            # Find existing summary
            summary = PaymentReport.objects.filter(
                ra_id=group['ra_id'],
                month=group['month'],
                year=group['year'],
                delete_field='no'
            ).first()
            
            if summary:
                # Update existing
                summary.salary = group['total_amount']
                if group['po_numbers']:
                    summary.po_number = ', '.join(group['po_numbers'])
                if group['week']:
                    summary.week = group['week']
                summary.save()
                updated_count += 1
            else:
                # Create new
                summary = PaymentReport()
                summary.uid = str(uuid.uuid4())
                summary.ra_id = group['ra_id']
                summary.ra_name = group['ra_name']
                summary.district_id = group['district_id']
                summary.projectTbl_foreignkey_id = group['project_id']
                summary.month = group['month']
                summary.year = group['year']
                summary.week = group['week']
                summary.salary = group['total_amount']
                if group['po_numbers']:
                    summary.po_number = ', '.join(group['po_numbers'])
                summary.payment_option = 'Bank Transfer'  # Default
                summary.save()
                created_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Payment report generated successfully. Created: {created_count}, Updated: {updated_count}',
            'data': {
                'created': created_count,
                'updated': updated_count,
                'total_payments': len(detailed_payments),
                'total_summaries': len(ra_groups)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in generate_payment_report: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["GET"])
def export_payment_report(request):
    """Export payment report to CSV"""
    try:
        # Get filter parameters
        year = request.GET.get('year')
        month = request.GET.get('month')
        week = request.GET.get('week')
        district_id = request.GET.get('district_id')
        format_type = request.GET.get('format', 'summary')  # summary or detailed
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="payment_report_{timestamp}.csv"'
        
        writer = csv.writer(response)
        
        if format_type == 'summary':
            # Export summary reports
            queryset = PaymentReport.objects.filter(delete_field='no').select_related('ra', 'district')
            
            if year:
                queryset = queryset.filter(year=year)
            if month:
                queryset = queryset.filter(month=month)
            if week:
                queryset = queryset.filter(week=week)
            if district_id:
                queryset = queryset.filter(district_id=district_id)
            
            # Write headers
            writer.writerow([
                'RA Name', 'District', 'Month', 'Year', 'Week',
                'Salary', 'Payment Option', 'PO Number', 'Bank Name',
                'Bank Branch', 'Momo Account', 'Created Date'
            ])
            
            # Write data
            for report in queryset.order_by('-created_date'):
                writer.writerow([
                    report.ra_name,
                    report.district.name if report.district else '',
                    report.month,
                    report.year,
                    report.week or '',
                    report.salary,
                    report.payment_option or '',
                    report.po_number or '',
                    report.bank_name or '',
                    report.bank_branch or '',
                    report.momo_acc or '',
                    report.created_date.strftime('%Y-%m-%d') if report.created_date else ''
                ])
        
        else:
            # Export detailed reports
            queryset = DetailedPaymentReport.objects.filter(delete_field='no').select_related(
                'ra', 'po', 'farm', 'activity', 'district'
            )
            
            if year:
                queryset = queryset.filter(year=year)
            if month:
                queryset = queryset.filter(month=month)
            if week:
                queryset = queryset.filter(week=week)
            if district_id:
                queryset = queryset.filter(district_id=district_id)
            
            # Write headers
            writer.writerow([
                'Group Code', 'RA Name', 'RA Account', 'PO Name',
                'District', 'Farm Reference', 'Activity', 'Farm Size (ha)',
                'Achievement (ha)', 'Amount', 'Month', 'Year', 'Week',
                'Number in Group', 'Issue', 'Sector', 'Act Code',
                'Created Date'
            ])
            
            # Write data
            for d in queryset.order_by('-created_date'):
                writer.writerow([
                    d.group_code or '',
                    d.ra_name,
                    d.ra_account or '',
                    d.po_name or '',
                    d.district.name if d.district else '',
                    d.farm_reference or '',
                    d.activity.sub_activity if d.activity else '',
                    d.farmsize,
                    d.achievement,
                    d.amount,
                    d.month,
                    d.year,
                    d.week or '',
                    d.number_in_a_group or '',
                    d.issue or '',
                    d.sector or '',
                    d.act_code or '',
                    d.created_date.strftime('%Y-%m-%d') if d.created_date else ''
                ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error in export_payment_report: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# ============== HELPER API VIEWS ==============

@login_required
def get_rehab_assistants(request):
    """Get rehab assistants for dropdown"""
    try:
        ras = PersonnelModel.objects.filter(
            delete_field='no',
            personnel_type='Rehab Assistant'
        ).order_by('first_name', 'surname')
        
        search = request.GET.get('search', '')
        if search:
            ras = ras.filter(
                Q(first_name__icontains=search) |
                Q(surname__icontains=search) |
                Q(staff_id__icontains=search)
            )
        
        data = [{
            'id': r.id,
            'name': f"{r.first_name} {r.surname}",
            'staff_id': r.staff_id,
            'bank_name': r.bank_name,
            'account_number': r.account_number,
            'momo_number': r.momo_number,
            'snnit_no': r.SSNIT_number
        } for r in ras]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def get_pos(request):
    """Get Project Officers for dropdown"""
    try:
        pos = staffTbl.objects.filter(delete_field='no').order_by('first_name', 'last_name')
        
        search = request.GET.get('search', '')
        if search:
            pos = pos.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(staffid__icontains=search)
            )
        
        data = [{
            'id': p.id,
            'name': f"{p.first_name} {p.last_name}",
            'staff_id': p.staffid
        } for p in pos]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def get_farms(request):
    """Get farms for dropdown"""
    try:
        farms = FarmdetailsTbl.objects.filter(delete_field='no').order_by('farm_reference')
        
        search = request.GET.get('search', '')
        if search:
            farms = farms.filter(
                Q(farm_reference__icontains=search) |
                Q(farmername__icontains=search)
            )
        
        district_id = request.GET.get('district_id')
        if district_id:
            farms = farms.filter(district_id=district_id)
        
        data = [{
            'id': f.id,
            'farm_reference': f.farm_reference,
            'farmername': f.farmername,
            'farm_size': f.farm_size,
            'district_id': f.district.id if f.district else None
        } for f in farms[:100]]  # Limit to 100 for performance
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def get_activities(request):
    """Get activities for dropdown"""
    try:
        activities = Activities.objects.all().order_by('sub_activity')
        
        search = request.GET.get('search', '')
        if search:
            activities = activities.filter(
                Q(sub_activity__icontains=search) |
                Q(main_activity__icontains=search)
            )
        
        data = [{
            'id': a.id,
            'name': a.sub_activity,
            'main_activity': a.main_activity,
            'activity_code': a.activity_code
        } for a in activities]
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })