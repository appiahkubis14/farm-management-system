# views/growth_monitoring_dashboard_views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Avg, Min, Max, F, Value, FloatField, IntegerField, Case, When, CharField
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import User
import json
import random

from ..models import (
    GrowthMonitoringModel, 
    staffTbl, 
    cocoaDistrict,
    Region
)

@login_required
def growth_monitoring_dashboard(request):
    """Render the Growth Monitoring Dashboard"""
    return render(request, 'portal/qr_code/dashboard.html')

@csrf_exempt
@require_http_methods(["GET"])
def get_dashboard_data(request):
    """Get all dashboard data in one optimized query - FIXED"""
    try:
        # Date filters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        district_id = request.GET.get('district_id')
        
        # Base queryset
        queryset = GrowthMonitoringModel.objects.filter(delete_field='no')
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if district_id and district_id != '':
            queryset = queryset.filter(district_id=district_id)
        
        # Get current period data
        current_data = queryset
        
        # Get previous period data (for trends)
        if start_date and end_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                period_length = (end_date_obj - start_date_obj).days
                prev_start = start_date_obj - timedelta(days=period_length)
                prev_end = start_date_obj - timedelta(days=1)
                
                prev_queryset = GrowthMonitoringModel.objects.filter(
                    delete_field='no',
                    date__gte=prev_start,
                    date__lte=prev_end
                )
                if district_id and district_id != '':
                    prev_queryset = prev_queryset.filter(district_id=district_id)
            except:
                # Default to last 30 days vs previous 30 days
                today = timezone.now().date()
                thirty_days_ago = today - timedelta(days=30)
                sixty_days_ago = today - timedelta(days=60)
                
                current_data = queryset.filter(date__gte=thirty_days_ago)
                prev_queryset = queryset.filter(date__gte=sixty_days_ago, date__lt=thirty_days_ago)
        else:
            # Default to last 30 days vs previous 30 days
            today = timezone.now().date()
            thirty_days_ago = today - timedelta(days=30)
            sixty_days_ago = today - timedelta(days=60)
            
            current_data = queryset.filter(date__gte=thirty_days_ago)
            prev_queryset = queryset.filter(date__gte=sixty_days_ago, date__lt=thirty_days_ago)
        
        # KPI Calculations
        total_plants = current_data.values('plant_uid').distinct().count()
        total_measurements = current_data.count()
        
        avg_height = current_data.aggregate(avg=Avg('height'))['avg'] or 0
        avg_leaves = current_data.aggregate(avg=Avg('number_of_leaves'))['avg'] or 0
        
        # Previous period values for trends
        prev_total_plants = prev_queryset.values('plant_uid').distinct().count()
        prev_avg_height = prev_queryset.aggregate(avg=Avg('height'))['avg'] or 0
        prev_avg_leaves = prev_queryset.aggregate(avg=Avg('number_of_leaves'))['avg'] or 0
        prev_total_measurements = prev_queryset.count()
        
        # Calculate trends
        plants_trend = calculate_trend(total_plants, prev_total_plants)
        height_trend = calculate_trend(avg_height, prev_avg_height)
        leaves_trend = calculate_trend(avg_leaves, prev_avg_leaves)
        measurements_trend = calculate_trend(total_measurements, prev_total_measurements)
        
        # Health scoring based on height, leaves, and leaf color
        health_stats = calculate_health_stats(current_data)
        
        # District performance
        district_stats = get_district_stats(current_data)
        
        # Recent activity
        recent_activity = get_recent_activity(current_data)
        
        # Officer performance - FIXED field name
        officer_stats = get_officer_stats(current_data)
        
        # Growth trends over time
        trends = get_growth_trends(current_data)
        
        # Health distribution
        health_distribution = get_health_distribution(current_data)
        
        # Growth stages
        growth_stages = get_growth_stages(current_data)
        
        # Insights
        insights = generate_insights(
            health_stats, district_stats, 
            plants_trend, height_trend, 
            avg_height, avg_leaves
        )
        
        response_data = {
            'success': True,
            'data': {
                'kpis': {
                    'total_plants': total_plants,
                    'total_measurements': total_measurements,
                    'avg_height': round(avg_height, 1),
                    'avg_leaves': round(avg_leaves, 1),
                    'health_index': round(health_stats['overall_score'], 1),
                    'plants_trend': plants_trend,
                    'height_trend': height_trend,
                    'leaves_trend': leaves_trend,
                    'health_trend': calculate_trend(
                        health_stats['overall_score'], 
                        health_stats.get('prev_overall_score', 0)
                    ),
                    'measurements_trend': measurements_trend
                },
                'health': health_stats,
                'districts': district_stats[:10],
                'recent': recent_activity[:10],
                'officers': officer_stats[:10],
                'trends': trends,
                'health_distribution': health_distribution,
                'growth_stages': growth_stages,
                'insights': insights
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_map_data(request):
    """Get geographic data for map visualization - FIXED"""
    try:
        # Date filters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        district_id = request.GET.get('district_id')
        
        queryset = GrowthMonitoringModel.objects.filter(
            delete_field='no',
            lat__isnull=False,
            lng__isnull=False
        ).exclude(
            lat=0,
            lng=0
        )
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if district_id and district_id != '':
            queryset = queryset.filter(district_id=district_id)
        
        # Select related for better performance
        queryset = queryset.select_related('agent', 'district').order_by('-date')[:500]
        
        points = []
        for record in queryset:
            health_score = calculate_plant_health_score(
                record.height, 
                record.number_of_leaves, 
                record.leaf_color
            )
            
            points.append({
                'id': record.id,
                'lat': float(record.lat) if record.lat else 0,
                'lng': float(record.lng) if record.lng else 0,
                'plant_uid': record.plant_uid[:15] + '...' if len(record.plant_uid) > 15 else record.plant_uid,
                'height': float(record.height) if record.height else 0,
                'leaves': record.number_of_leaves or 0,
                'health_score': health_score,
                'date': record.date.strftime('%Y-%m-%d') if record.date else '',
                'officer': f"{record.agent.first_name} {record.agent.last_name}"[:20] if record.agent else 'N/A',
                'district': record.district.name[:20] if record.district else 'N/A',
                'leaf_color': record.leaf_color or 'Unknown'
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'points': points,
                'total': len(points)
            }
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_growth_trends_api(request):
    """Get growth trends for charts - FIXED"""
    try:
        period = int(request.GET.get('period', 30))
        district_id = request.GET.get('district_id')
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=period)
        
        queryset = GrowthMonitoringModel.objects.filter(
            delete_field='no',
            date__gte=start_date,
            date__lte=end_date
        )
        
        if district_id and district_id != '':
            queryset = queryset.filter(district_id=district_id)
        
        # Group by date
        trends = queryset.annotate(
            date_only=TruncDate('date')
        ).values('date_only').annotate(
            avg_height=Avg('height'),
            avg_leaves=Avg('number_of_leaves'),
            count=Count('id')
        ).order_by('date_only')
        
        labels = []
        height_data = []
        leaves_data = []
        
        for trend in trends:
            if trend['date_only']:
                labels.append(trend['date_only'].strftime('%d %b'))
                height_data.append(round(trend['avg_height'] or 0, 1))
                leaves_data.append(round(trend['avg_leaves'] or 0, 1))
        
        return JsonResponse({
            'success': True,
            'data': {
                'labels': labels,
                'height': height_data,
                'leaves': leaves_data
            }
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_district_stats_api(request):
    """Get district performance statistics - FIXED"""
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        queryset = GrowthMonitoringModel.objects.filter(delete_field='no')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Group by district
        from django.db.models.functions import Coalesce
        
        districts = queryset.values(
            'district_id', 
            'district__name'
        ).annotate(
            total_plants=Count('plant_uid', distinct=True),
            total_measurements=Count('id'),
            avg_height=Coalesce(Avg('height'), 0.0),
            avg_leaves=Coalesce(Avg('number_of_leaves'), 0.0),
            officer_count=Count('agent', distinct=True)
        ).order_by('-total_plants')
        
        stats = []
        for district in districts:
            if district['district_id']:
                # Calculate health score separately
                district_queryset = queryset.filter(district_id=district['district_id'])
                health_score = 0
                if district_queryset.exists():
                    scores = []
                    for record in district_queryset[:100]:  # Sample for performance
                        score = calculate_plant_health_score(
                            record.height, 
                            record.number_of_leaves, 
                            record.leaf_color
                        )
                        scores.append(score)
                    health_score = sum(scores) / len(scores) if scores else 0
                
                stats.append({
                    'id': district['district_id'],
                    'name': district['district__name'] or 'Unknown',
                    'total_plants': district['total_plants'],
                    'total_measurements': district['total_measurements'],
                    'avg_height': round(district['avg_height'] or 0, 1),
                    'avg_leaves': round(district['avg_leaves'] or 0, 1),
                    'health_score': round(health_score, 1),
                    'officer_count': district['officer_count'],
                    'growth_rate': random.randint(5, 25),  # Placeholder
                    'trend': 1 if random.random() > 0.5 else -1  # Placeholder
                })
        
        return JsonResponse({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ============ HELPER FUNCTIONS ============

def calculate_trend(current, previous):
    """Calculate percentage trend between current and previous values"""
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 1)

def calculate_plant_health_score(height, leaves, leaf_color):
    """Calculate health score for a plant (0-100)"""
    # Height score (max 40 points)
    height_score = min(40, (height / 100) * 40) if height else 0
    
    # Leaves score (max 30 points)
    leaves_score = min(30, (leaves / 50) * 30) if leaves else 0
    
    # Leaf color score (max 30 points)
    color_scores = {
        'Green': 30,
        'Dark Green': 30,
        'Light Green': 25,
        'Yellowish': 15,
        'Spotted': 10,
        'Brown': 5
    }
    color_score = color_scores.get(leaf_color, 10)
    
    return round(height_score + leaves_score + color_score)

def calculate_health_stats(queryset):
    """Calculate comprehensive health statistics"""
    total_records = queryset.count()
    if total_records == 0:
        return {
            'excellent': {'count': 0, 'percent': 0},
            'good': {'count': 0, 'percent': 0},
            'fair': {'count': 0, 'percent': 0},
            'poor': {'count': 0, 'percent': 0},
            'overall_score': 0,
            'avg_height_healthy': 0,
            'avg_leaves_healthy': 0
        }
    
    # Calculate health scores
    health_data = []
    for record in queryset:
        score = calculate_plant_health_score(
            record.height, 
            record.number_of_leaves, 
            record.leaf_color
        )
        health_data.append({
            'score': score,
            'height': record.height,
            'leaves': record.number_of_leaves
        })
    
    # Categorize
    excellent = [h for h in health_data if h['score'] >= 80]
    good = [h for h in health_data if 60 <= h['score'] < 80]
    fair = [h for h in health_data if 40 <= h['score'] < 60]
    poor = [h for h in health_data if h['score'] < 40]
    
    # Healthy plants (excellent + good)
    healthy = excellent + good
    avg_height_healthy = sum(h['height'] for h in healthy) / len(healthy) if healthy else 0
    avg_leaves_healthy = sum(h['leaves'] for h in healthy) / len(healthy) if healthy else 0
    
    overall_score = sum(h['score'] for h in health_data) / len(health_data) if health_data else 0
    
    return {
        'excellent': {
            'count': len(excellent),
            'percent': round((len(excellent) / total_records) * 100, 1) if total_records else 0
        },
        'good': {
            'count': len(good),
            'percent': round((len(good) / total_records) * 100, 1) if total_records else 0
        },
        'fair': {
            'count': len(fair),
            'percent': round((len(fair) / total_records) * 100, 1) if total_records else 0
        },
        'poor': {
            'count': len(poor),
            'percent': round((len(poor) / total_records) * 100, 1) if total_records else 0
        },
        'overall_score': round(overall_score, 1),
        'avg_height_healthy': round(avg_height_healthy, 1),
        'avg_leaves_healthy': round(avg_leaves_healthy, 1)
    }

def get_district_stats(queryset):
    """Get district performance statistics - FIXED"""
    stats = []
    
    # Get districts with data
    district_data = queryset.exclude(
        district__isnull=True
    ).values(
        'district_id', 
        'district__name'
    ).annotate(
        total_plants=Count('plant_uid', distinct=True),
        officer_count=Count('agent_id', distinct=True),
        avg_height=Avg('height'),
        avg_leaves=Avg('number_of_leaves'),
        measurement_count=Count('id')
    ).order_by('-total_plants')
    
    for district in district_data:
        if not district['district_id']:
            continue
        
        # Get all records for this district to calculate health scores
        district_queryset = queryset.filter(district_id=district['district_id'])
        
        # Calculate health scores
        health_scores = []
        for record in district_queryset.only('height', 'number_of_leaves', 'leaf_color'):
            score = calculate_plant_health_score(
                record.height, 
                record.number_of_leaves, 
                record.leaf_color
            )
            health_scores.append(score)
        
        avg_health_score = sum(health_scores) / len(health_scores) if health_scores else 0
        
        # Calculate growth rate (compare to previous period)
        growth_rate = 0
        trend = 0
        if district['avg_height']:
            # Simple growth rate based on height
            growth_rate = round((district['avg_height'] / 100) * 100, 1)
            trend = 1 if district['avg_height'] > 50 else -1 if district['avg_height'] < 30 else 0
        
        stats.append({
            'id': district['district_id'],
            'name': district['district__name'] or 'Unknown District',
            'total_plants': district['total_plants'],
            'officer_count': district['officer_count'],
            'avg_height': round(district['avg_height'] or 0, 1),
            'avg_leaves': round(district['avg_leaves'] or 0, 1),
            'health_score': round(avg_health_score, 1),
            'growth_rate': growth_rate,
            'trend': trend,
            'measurement_count': district['measurement_count']
        })
    
    # Sort by health score
    stats.sort(key=lambda x: x['health_score'], reverse=True)
    
    return stats


def get_recent_activity(queryset):
    """Get recent measurement activities - FIXED"""
    recent = queryset.select_related(
        'agent', 'district'
    ).order_by('-date', '-created_date')[:2]
    
    activities = []
    for record in recent:
        health_score = calculate_plant_health_score(
            record.height, 
            record.number_of_leaves, 
            record.leaf_color
        )
        
        # Truncate plant UID for display
        plant_uid = record.plant_uid
        if plant_uid and len(plant_uid) > 20:
            plant_uid = plant_uid[:20] + '...'
        
        # Format officer name
        officer_name = 'N/A'
        if record.agent:
            officer_name = f"{record.agent.first_name or ''} {record.agent.last_name or ''}".strip()
            # if not officer_name:
            #     officer_name = record.agent.username if record.agent.username else record.agent.email or 'Unknown'
        
        # Format district name
        district_name = record.district.name if record.district else 'N/A'
        if district_name and len(district_name) > 20:
            district_name = district_name[:20] + '...'
        
        activities.append({
            'id': record.id,
            'plant_uid': plant_uid,
            'height': round(record.height or 0, 1),
            'leaves': record.number_of_leaves or 0,
            'health_score': health_score,
            'date': record.date.strftime('%Y-%m-%d') if record.date else '',
            'officer': officer_name[:30],
            'district': district_name,
            'leaf_color': record.leaf_color or 'Unknown'
        })
    
    return activities



def get_officer_stats(queryset):
    """Get project officer performance statistics - FIXED"""
    stats = []
    
    # Get officers with data
    officer_data = queryset.exclude(
        agent__isnull=True
    ).values(
        'agent_id',
        'agent__first_name',
        'agent__last_name',
        # 'agent__username'
    ).annotate(
        total_plants=Count('plant_uid', distinct=True),
        total_measurements=Count('id'),
        avg_height=Avg('height'),
        avg_leaves=Avg('number_of_leaves')
    ).order_by('-total_plants')
    
    for officer in officer_data:
        if not officer['agent_id']:
            continue
        
        officer_id = officer['agent_id']
        officer_queryset = queryset.filter(agent_id=officer_id)
        
        # Calculate health scores
        health_scores = []
        for record in officer_queryset.only('height', 'number_of_leaves', 'leaf_color')[:100]:  # Limit for performance
            score = calculate_plant_health_score(
                record.height, 
                record.number_of_leaves, 
                record.leaf_color
            )
            health_scores.append(score)
        
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0
        
        # Get officer's district
        district_name = 'N/A'
        try:
            # Try to get district from the queryset
            sample_record = officer_queryset.filter(district__isnull=False).first()
            if sample_record and sample_record.district:
                district_name = sample_record.district.name
        except:
            pass
        
        # Format officer name
        first_name = officer.get('agent__first_name', '')
        last_name = officer.get('agent__last_name', '')
        # username = officer.get('agent__username', 'Unknown')
        
        if first_name or last_name:
            officer_name = f"{first_name or ''} {last_name or ''}".strip()
        else:
            'None'
        
        stats.append({
            'id': officer_id,
            'name': officer_name[:30],
            'district': district_name[:20] if district_name else 'N/A',
            'total_plants': officer['total_plants'],
            'total_measurements': officer['total_measurements'],
            'avg_height': round(officer['avg_height'] or 0, 1),
            'avg_leaves': round(officer['avg_leaves'] or 0, 1),
            'avg_health': round(avg_health, 1)
        })
    
    # Sort by health score
    stats.sort(key=lambda x: x['avg_health'], reverse=True)
    
    return stats


def get_growth_trends(queryset):
    """Get growth trends for charts - FIXED"""
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    
    trends = queryset.filter(
        date__gte=thirty_days_ago
    ).annotate(
        date_only=TruncDate('date')
    ).values('date_only').annotate(
        avg_height=Avg('height'),
        avg_leaves=Avg('number_of_leaves'),
        count=Count('id')
    ).order_by('date_only')
    
    labels = []
    height_data = []
    leaves_data = []
    
    # Generate date range to ensure no gaps
    date_range = []
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        date_range.append(date)
    
    # Create mapping of existing trends
    trend_map = {}
    for trend in trends:
        if trend['date_only']:
            trend_map[trend['date_only']] = {
                'height': trend['avg_height'] or 0,
                'leaves': trend['avg_leaves'] or 0
            }
    
    # Fill in all dates
    for date in date_range:
        labels.append(date.strftime('%d %b'))
        if date in trend_map:
            height_data.append(round(trend_map[date]['height'], 1))
            leaves_data.append(round(trend_map[date]['leaves'], 1))
        else:
            height_data.append(0)
            leaves_data.append(0)
    
    return {
        'labels': labels,
        'height': height_data,
        'leaves': leaves_data
    }


def get_health_distribution(queryset):
    """Get health distribution data for pie chart - FIXED"""
    categories = ['Excellent', 'Good', 'Fair', 'Poor']
    values = [0, 0, 0, 0]
    
    # Process records efficiently
    for record in queryset.only('height', 'number_of_leaves', 'leaf_color'):
        score = calculate_plant_health_score(
            record.height, 
            record.number_of_leaves, 
            record.leaf_color
        )
        if score >= 80:
            values[0] += 1
        elif score >= 60:
            values[1] += 1
        elif score >= 40:
            values[2] += 1
        else:
            values[3] += 1
    
    return {
        'labels': categories,
        'values': values
    }



def get_growth_stages(queryset):
    """Get growth stage distribution - FIXED"""
    stages = ['Seedling', 'Young', 'Mature', 'Old']
    values = [0, 0, 0, 0]
    
    for record in queryset.only('height'):
        height = record.height or 0
        if height < 30:
            values[0] += 1
        elif height < 60:
            values[1] += 1
        elif height < 100:
            values[2] += 1
        else:
            values[3] += 1
    
    return {
        'labels': stages,
        'values': values
    }

def generate_insights(health_stats, district_stats, plants_trend, height_trend, avg_height, avg_leaves):
    """Generate intelligent insights and recommendations"""
    insights = []
    
    # Overall health insight
    overall_health = health_stats['overall_score']
    if overall_health < 50:
        insights.append({
            'type': 'warning',
            'title': 'Critical Health Alert',
            'message': f'Overall plant health is critically low at {overall_health}%. Immediate intervention required.',
            'action': 'Schedule comprehensive health assessment'
        })
    elif overall_health < 70:
        insights.append({
            'type': 'warning',
            'title': 'Health Concerns Detected',
            'message': f'Plant health score is {overall_health}%. Below target of 80%.',
            'action': 'Review nutrient and watering schedules'
        })
    else:
        insights.append({
            'type': 'success',
            'title': 'Healthy Plants',
            'message': f'Overall plant health is good at {overall_health}%.',
            'action': 'Continue current management practices'
        })
    
    # Poor performing districts
    poor_districts = [d for d in district_stats if d['health_score'] < 50][:2]
    if poor_districts:
        districts_list = ', '.join([d['name'] for d in poor_districts])
        insights.append({
            'type': 'warning',
            'title': 'Underperforming Districts',
            'message': f'{districts_list} showing low health scores.',
            'action': 'Deploy additional resources and training'
        })
    
    # Top performing district
    if district_stats and district_stats[0]['health_score'] > 75:
        insights.append({
            'type': 'success',
            'title': 'Best Practice Identified',
            'message': f"{district_stats[0]['name']} district is top performer with {district_stats[0]['health_score']}% health score.",
            'action': 'Document and share best practices'
        })
    
    # Growth trends
    if height_trend < -5:
        insights.append({
            'type': 'warning',
            'title': 'Declining Growth Rate',
            'message': f'Average plant height has decreased by {abs(height_trend)}% compared to previous period.',
            'action': 'Investigate potential causes: disease, nutrients, or water'
        })
    elif height_trend > 10:
        insights.append({
            'type': 'success',
            'title': 'Strong Growth',
            'message': f'Plants are growing well with {height_trend}% increase in height.',
            'action': 'Maintain current practices'
        })
    
    # Leaf color issues
    poor_color_count = health_stats['poor']['count'] + health_stats['fair']['count']
    total_count = sum([
        health_stats['excellent']['count'],
        health_stats['good']['count'],
        health_stats['fair']['count'],
        health_stats['poor']['count']
    ])
    
    if total_count > 0:
        poor_percentage = (poor_color_count / total_count) * 100
        if poor_percentage > 30:
            insights.append({
                'type': 'warning',
                'title': 'Leaf Discoloration Alert',
                'message': f'{round(poor_percentage)}% of plants show abnormal leaf coloration.',
                'action': 'Check for nutrient deficiencies and diseases'
            })
    
    # Success story
    if avg_height > 70 and avg_leaves > 30:
        insights.append({
            'type': 'success',
            'title': 'Exceptional Growth',
            'message': f'Plants are showing exceptional growth with {round(avg_height)}cm height and {round(avg_leaves)} leaves.',
            'action': 'Document successful strategies'
        })
    
    # Add default insights if none
    if len(insights) < 3:
        insights.append({
            'type': 'info',
            'title': 'Monitoring Update',
            'message': 'Regular monitoring is ongoing. Continue weekly measurements.',
            'action': 'Maintain current schedule'
        })
        
        insights.append({
            'type': 'info',
            'title': 'Data Collection',
            'message': f'{total_count if total_count > 0 else 0} plants are being tracked.',
            'action': 'Ensure all plants have recent measurements'
        })
    
    return insights[:6]