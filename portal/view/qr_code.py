import uuid
import qrcode
import io
import base64
import os
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
                # Generate unique ID: ACL-{UUID4}
                unique_id = f"ACL-{uuid.uuid4()}"
                timestamp = timezone.now()
                
                # Create QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                
                # Data to encode in QR code
                qr_data = f"{unique_id}\nGenerated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
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
                
                # METHOD 1: Using InMemoryUploadedFile (most reliable)
                try:
                    from PIL import Image
                    pil_image = Image.open(buffer)
                    
                    uploaded_file = InMemoryUploadedFile(
                        buffer,  # file
                        None,    # field_name
                        filename, # file name
                        'image/png', # content_type
                        len(image_data), # size
                        None     # charset
                    )
                    
                    qr_model = QR_CodeModel.objects.create(
                        uid=unique_id,
                        qr_code=uploaded_file
                    )
                except Exception as e1:
                    print(f"Method 1 failed: {e1}")
                    
                    # METHOD 2: Using SimpleUploadedFile
                    try:
                        buffer.seek(0)
                        uploaded_file = SimpleUploadedFile(
                            filename,
                            buffer.getvalue(),
                            content_type='image/png'
                        )
                        
                        qr_model = QR_CodeModel.objects.create(
                            uid=unique_id,
                            qr_code=uploaded_file
                        )
                    except Exception as e2:
                        print(f"Method 2 failed: {e2}")
                        
                        # METHOD 3: Create then save
                        qr_model = QR_CodeModel(uid=unique_id)
                        qr_model.qr_code.save(filename, ContentFile(image_data), save=True)
                
                # Refresh from DB to get the URL
                qr_model.refresh_from_db()
                
                generated_codes.append({
                    'id': qr_model.id,
                    'uid': unique_id,
                    'qr_code_url': qr_model.qr_code.url if qr_model.qr_code else '',
                    'qr_code_base64': f"data:image/png;base64,{qr_base64}",
                    'created_date': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'created_date_formatted': timestamp.strftime('%b %d, %Y %H:%M'),
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
            data.append({
                'id': qr.id,
                'uid': qr.uid,
                'qr_code_url': qr.qr_code.url if qr.qr_code else '',
                'created_date': qr.created_date.strftime('%Y-%m-%d %H:%M:%S'),
                'created_date_formatted': qr.created_date.strftime('%b %d, %Y %H:%M'),
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
        data = json.loads(request.body)
        ids = data.get('ids', [])
        
        if not ids:
            return JsonResponse({
                'success': False,
                'message': 'No QR codes selected'
            }, status=400)
        
        with transaction.atomic():
            qr_codes = QR_CodeModel.objects.filter(id__in=ids)
            
            # Delete image files
            for qr in qr_codes:
                if qr.qr_code:
                    qr.qr_code.delete(save=False)
            
            deleted_count = qr_codes.delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} QR code(s)'
        })
        
    except Exception as e:
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