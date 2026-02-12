import traceback
import uuid
import qrcode
import io
import base64
import os
import random
import string
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from django.conf import settings

from portal.models import QR_CodeModel

@login_required
def qr_code_generator(request):
    """QR Code Generator page view"""
    context = {
        'page_title': 'QR Code Generator',
    }
    return render(request, 'portal/qr_code/qr_code_generator.html', context)

def generate_plantation_uid():
    """Generate UID in format: ACL-PLANTATION-YEAR-TIME-00001"""
    
    # Fixed prefix and plantation indicator
    prefix = "ACL"
    plantation = "PLT"
    
    # Current year
    year = timezone.now().strftime('%Y')
    
    # Current time (HHMM)
    time_part = timezone.now().strftime('%H%M')
    
    # Get the last QR code for today to generate sequential number
    last_qr = QR_CodeModel.objects.filter(
        uid__startswith=f"{prefix}-{plantation}-{year}-{time_part}"
    ).order_by('-id').first()
    
    if last_qr and last_qr.uid:
        try:
            # Extract the sequential number
            last_num = int(last_qr.uid.split('-')[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    
    # Format with leading zeros (5 digits)
    sequential = f"{new_num:05d}"
    
    uid = f"{prefix}-{plantation}-{year}-{time_part}-{sequential}"
    
    return {
        'uid': uid,
        'prefix': prefix,
        'plantation': plantation,
        'year': year,
        'time': time_part,
        'sequential': sequential
    }

@login_required
@require_http_methods(["POST"])
def generate_qr_codes(request):
    """Generate QR codes with unique identifiers"""
    try:
        import json
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1 or quantity > 100:
            return JsonResponse({
                'success': False,
                'message': 'Quantity must be between 1 and 100'
            }, status=400)
        
        generated_codes = []
        
        with transaction.atomic():
            for i in range(quantity):
                # Generate unique ID using the plantation format
                uid_data = generate_plantation_uid()
                unique_id = uid_data['uid']
                timestamp = timezone.now()
                
                # Create QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                
                # Data to encode in QR code
                qr_data = f"{unique_id}\nGenerated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\nPlantation ID"
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                # Create QR code image
                qr_image = qr.make_image(fill_color="black", back_color="white")
                
                # Save to BytesIO
                buffer = io.BytesIO()
                qr_image.save(buffer, format='PNG')
                image_data = buffer.getvalue()
                buffer.seek(0)
                
                # Create base64 for preview
                qr_base64 = base64.b64encode(image_data).decode()
                
                # Create filename
                filename = f"{unique_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
                
                # Create QR code model
                qr_model = QR_CodeModel(uid=unique_id)
                
                # Save the image file
                qr_model.qr_code.save(filename, ContentFile(image_data), save=False)
                qr_model.save()
                
                # Refresh from DB to get the URL
                qr_model.refresh_from_db()
                
                generated_codes.append({
                    'id': qr_model.id,
                    'uid': unique_id,
                    'qr_code_url': qr_model.qr_code.url if qr_model.qr_code else '',
                    'qr_code_base64': f"data:image/png;base64,{qr_base64}",
                    'created_date': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'created_date_formatted': timestamp.strftime('%b %d, %Y %H:%M'),
                    'prefix': uid_data['prefix'],
                    'plantation': uid_data['plantation'],
                    'year': uid_data['year'],
                    'time': uid_data['time'],
                    'sequential': uid_data['sequential']
                })
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully generated {quantity} QR code(s)',
            'data': generated_codes
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error generating QR codes: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_qr_codes(request):
    """Get paginated list of QR codes"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 12))
        search = request.GET.get('search', '')
        
        qr_codes = QR_CodeModel.objects.all().order_by('-created_date')
        
        if search:
            qr_codes = qr_codes.filter(uid__icontains=search)
        
        paginator = Paginator(qr_codes, page_size)
        qr_page = paginator.get_page(page)
        
        data = []
        for qr in qr_page:
            # Parse UID components for display
            uid_parts = qr.uid.split('-') if qr.uid else []
            
            data.append({
                'id': qr.id,
                'uid': qr.uid,
                'qr_code_url': qr.qr_code.url if qr.qr_code else '',
                'created_date': qr.created_date.strftime('%Y-%m-%d %H:%M:%S'),
                'created_date_formatted': qr.created_date.strftime('%b %d, %Y %H:%M'),
                'prefix': uid_parts[0] if len(uid_parts) > 0 else '',
                'plantation': uid_parts[1] if len(uid_parts) > 1 else '',
                'year': uid_parts[2] if len(uid_parts) > 2 else '',
                'time': uid_parts[3] if len(uid_parts) > 3 else '',
                'sequential': uid_parts[4] if len(uid_parts) > 4 else '',
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'page': page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': qr_page.has_next(),
            'has_previous': qr_page.has_previous(),
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching QR codes: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["DELETE"])
def delete_qr_code(request, qr_id):
    """Delete a specific QR code"""
    try:
        qr_code = QR_CodeModel.objects.get(id=qr_id)
        
        # Delete the image file
        if qr_code.qr_code:
            qr_code.qr_code.delete(save=False)
        
        qr_code.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'QR code deleted successfully'
        })
        
    except QR_CodeModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'QR code not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting QR code: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["DELETE"])
def bulk_delete_qr_codes(request):
    """Delete multiple QR codes"""
    try:
        import json
        import traceback
        data = json.loads(request.body)
        ids = data.get('ids', [])
        print(f"Deleting QR codes: {ids}")
        
        if not ids:
            return JsonResponse({
                'success': False,
                'message': 'No QR codes selected'
            }, status=400)
        
        deleted_count = 0
        
        with transaction.atomic():
            # Get all QR codes to delete
            qr_codes = QR_CodeModel.default_objects.filter(id__in=ids)
            
            # Delete image files first
            for qr in qr_codes:
                if qr.qr_code:
                    try:
                        qr.qr_code.delete(save=False)
                        print(f"Deleted image for QR code {qr.uid}")
                    except Exception as e:
                        print(f"Error deleting image for {qr.uid}: {e}")
            
            # Method 1: Delete each object individually (works with custom delete method)
            for qr in qr_codes:
                qr.delete()
                deleted_count += 1
            
            # OR Method 2: Use hard_delete if you want to bypass soft delete
            # deleted_count = qr_codes.hard_delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} QR code(s)'
        })
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Error in bulk delete: {e}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error deleting QR codes: {str(e)}'
        }, status=500)
    

    
@login_required
@require_http_methods(["GET"])
def download_qr_code(request, qr_id):
    """Download a single QR code"""
    try:
        qr_code = QR_CodeModel.objects.get(id=qr_id)
        
        if not qr_code.qr_code:
            return JsonResponse({
                'success': False,
                'message': 'QR code image not found'
            }, status=404)
        
        response = FileResponse(
            qr_code.qr_code.open('rb'), 
            filename=f"{qr_code.uid}.png",
            content_type='image/png'
        )
        return response
        
    except QR_CodeModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'QR code not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error downloading QR code: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def download_bulk_qr_codes(request):
    """Download multiple QR codes as ZIP"""
    try:
        import json
        import zipfile
        from io import BytesIO
        
        data = json.loads(request.body)
        ids = data.get('ids', [])
        
        if not ids:
            return JsonResponse({
                'success': False,
                'message': 'No QR codes selected'
            }, status=400)
        
        qr_codes = QR_CodeModel.objects.filter(id__in=ids)
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for qr in qr_codes:
                if qr.qr_code and qr.qr_code.name:
                    try:
                        qr.qr_code.open('rb')
                        file_content = qr.qr_code.read()
                        zip_file.writestr(f"{qr.uid}.png", file_content)
                        qr.qr_code.close()
                    except Exception as e:
                        print(f"Error adding {qr.uid} to zip: {e}")
                        continue
        
        zip_buffer.seek(0)
        
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="qr_codes_{timezone.now().strftime("%Y%m%d_%H%M%S")}.zip"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error downloading QR codes: {str(e)}'
        }, status=500)