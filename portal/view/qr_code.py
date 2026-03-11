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
    """Generate UID in format: ACL-PLT-YYYY-HHMM-00001"""
    
    # Fixed prefix and plantation indicator
    prefix = "ACL"
    plantation = "PLT"
    
    # Current year
    year = timezone.now().strftime('%Y')
    
    # Current time (HHMM)
    time_part = timezone.now().strftime('%H%M')
    
    # Get the last QR code with similar pattern
    try:
        last_qr = QR_CodeModel.default_objects.filter(
            uid__startswith=f"{prefix}-{plantation}-{year}-{time_part}"
        ).order_by('-id').first()
    except AttributeError:
        last_qr = QR_CodeModel.objects.filter(
            uid__startswith=f"{prefix}-{plantation}-{year}-{time_part}"
        ).order_by('-id').first()
    
    if last_qr and last_qr.uid:
        try:
            # Extract the sequential number
            parts = last_qr.uid.split('-')
            if len(parts) >= 5:
                last_num = int(parts[4])
                new_num = last_num + 1
            else:
                new_num = 1
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
                
                print(f"Generating QR code {i+1}/{quantity}: {unique_id}")
                
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
                buffer.seek(0)
                
                # Create base64 for preview
                qr_base64 = base64.b64encode(buffer.getvalue()).decode()
                
                # Create filename
                filename = f"{unique_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
                
                # Create SimpleUploadedFile from buffer
                image_file = SimpleUploadedFile(
                    filename,
                    buffer.getvalue(),
                    content_type='image/png'
                )
                
                # Create QR code model and assign the image
                qr_model = QR_CodeModel(
                    uid=unique_id,
                    qr_code=image_file
                )
                qr_model.save()
                
                # Get the URL
                qr_model.refresh_from_db()
                qr_code_url = qr_model.qr_code.url if qr_model.qr_code else ''
                print(f"Saved QR code with URL: {qr_code_url}")
                
                generated_codes.append({
                    'id': qr_model.id,
                    'uid': unique_id,
                    'qr_code_url': qr_code_url,
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
        page_size = int(request.GET.get('page_size', 12))  # Default to 12, not 100
        search = request.GET.get('search', '')
        
        print(f"=== get_qr_codes called ===")
        print(f"Page: {page}, Page Size: {page_size}, Search: '{search}'")
        
        # Use objects.all() which uses timeStampManager and filters delete_field="no"
        qr_codes = QR_CodeModel.objects.all().order_by('-created_date')
        
        # Debug: print the SQL query
        print(f"SQL Query: {qr_codes.query}")
        
        if search:
            qr_codes = qr_codes.filter(uid__icontains=search)
            print(f"After search filter: {qr_codes.count()} records")
        
        # Get total count BEFORE pagination
        total_count = qr_codes.count()
        print(f"Total active QR codes: {total_count}")
        
        # If no records found, return empty data
        if total_count == 0:
            print("No active QR codes found")
            return JsonResponse({
                'success': True,
                'data': [],
                'page': page,
                'total_pages': 0,
                'total_count': 0,
                'has_next': False,
                'has_previous': False,
            })
        
        # Create paginator
        paginator = Paginator(qr_codes, page_size)
        
        # Get the page
        try:
            qr_page = paginator.get_page(page)
        except Exception as e:
            print(f"Error getting page {page}: {e}")
            qr_page = paginator.get_page(1)
            page = 1
        
        print(f"Paginator: total={paginator.count}, pages={paginator.num_pages}")
        print(f"Current page: {qr_page.number}, has_next={qr_page.has_next()}, has_previous={qr_page.has_previous()}")
        print(f"Records on this page: {len(qr_page.object_list)}")
        
        data = []
        for qr in qr_page:
            # Build absolute URL for the QR code
            qr_code_url = ''
            if qr.qr_code and qr.qr_code.name:
                try:
                    qr_code_url = qr.qr_code.url
                    if qr_code_url.startswith('/'):
                        qr_code_url = request.build_absolute_uri(qr_code_url)
                except Exception as e:
                    print(f"Error getting URL for QR {qr.id}: {e}")
                    qr_code_url = ''
            
            # Parse UID components for display
            uid_parts = qr.uid.split('-') if qr.uid else []
            
            data.append({
                'id': qr.id,
                'uid': qr.uid,
                'qr_code_url': qr_code_url,
                'created_date': qr.created_date.strftime('%Y-%m-%d %H:%M:%S'),
                'created_date_formatted': qr.created_date.strftime('%b %d, %Y %H:%M'),
                'prefix': uid_parts[0] if len(uid_parts) > 0 else '',
                'plantation': uid_parts[1] if len(uid_parts) > 1 else '',
                'year': uid_parts[2] if len(uid_parts) > 2 else '',
                'time': uid_parts[3] if len(uid_parts) > 3 else '',
                'sequential': uid_parts[4] if len(uid_parts) > 4 else '',
            })
        
        response_data = {
            'success': True,
            'data': data,
            'page': qr_page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': qr_page.has_next(),
            'has_previous': qr_page.has_previous(),
        }
        
        print(f"Response: page={response_data['page']}, total_pages={response_data['total_pages']}, total_count={response_data['total_count']}")
        print(f"Returning {len(data)} records")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"Error fetching QR codes: {e}")
        import traceback
        traceback.print_exc()
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
    """Download multiple QR codes as a single PDF"""
    try:
        import json
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO

        data = json.loads(request.body)
        ids = data.get('ids', [])

        if not ids:
            return JsonResponse({'success': False, 'message': 'No QR codes selected'}, status=400)

        # Fetch QR codes that actually have an image file set
        qr_codes = QR_CodeModel.objects.filter(id__in=ids).exclude(qr_code='').order_by('id')

        if not qr_codes.exists():
            return JsonResponse({'success': False, 'message': 'No QR codes with images found'}, status=404)

        # ── Grid settings ──────────────────────────────────────────────
        COLS          = 3
        ROWS_PER_PAGE = 3
        QR_SIZE       = 55 * mm   # width & height of the QR image
        LABEL_HEIGHT  = 12 * mm   # space below image for UID text
        CELL_HEIGHT   = QR_SIZE + LABEL_HEIGHT
        CELL_WIDTH    = QR_SIZE
        PAGE_GAP      = COLS * ROWS_PER_PAGE   # QRs per page

        # ── Styles ─────────────────────────────────────────────────────
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'BulkTitle',
            parent=styles['Heading1'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
        sub_style = ParagraphStyle(
            'BulkSub',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666666'),
            spaceAfter=10,
        )
        label_style = ParagraphStyle(
            'QRLabel',
            parent=styles['Normal'],
            fontSize=6,
            alignment=TA_CENTER,
            textColor=colors.black,
            leading=8,
        )

        # ── Build elements ─────────────────────────────────────────────
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=10 * mm,
            leftMargin=10 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
        )

        elements = []
        elements.append(Paragraph("QR Codes Report", title_style))
        elements.append(Paragraph(
            f"Total: {qr_codes.count()} &nbsp;|&nbsp; Generated: {timezone.now().strftime('%d %b %Y %H:%M')}",
            sub_style,
        ))
        elements.append(Spacer(1, 5 * mm))

        qr_list = list(qr_codes)

        def build_cell(qr):
            """
            Return a ReportLab flowable for one QR code cell, or None if the
            file cannot be read (missing / permission error / bad path).
            """
            if not qr.qr_code:
                return None
            try:
                # ★ KEY FIX: read the file through Django's storage backend
                # into a BytesIO so ReportLab never touches the raw filesystem
                # path (which breaks on external / mounted drives).
                with qr.qr_code.open('rb') as fh:
                    img_bytes = BytesIO(fh.read())

                img = Image(img_bytes, width=QR_SIZE, height=QR_SIZE)

                uid_text = qr.uid if qr.uid else f'ID-{qr.pk}'
                label = Paragraph(uid_text, label_style)

                # Stack image + label in a tiny inner table
                inner = Table(
                    [[img], [label]],
                    colWidths=[CELL_WIDTH],
                    rowHeights=[QR_SIZE, LABEL_HEIGHT],
                )
                inner.setStyle(TableStyle([
                    ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING',   (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
                    ('TOPPADDING',    (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                return inner

            except (FileNotFoundError, OSError, Exception):
                # Gracefully skip unreadable files instead of crashing
                return None

        # Chunk the full list into pages
        for page_start in range(0, len(qr_list), PAGE_GAP):
            page_qrs = qr_list[page_start: page_start + PAGE_GAP]

            table_data = []
            for row_idx in range(ROWS_PER_PAGE):
                row = []
                for col_idx in range(COLS):
                    flat_idx = row_idx * COLS + col_idx
                    if flat_idx < len(page_qrs):
                        cell = build_cell(page_qrs[flat_idx])
                        row.append(cell if cell is not None else '')
                    else:
                        row.append('')   # empty filler cell
                table_data.append(row)

            # Only add a table if at least one cell has content
            if any(cell != '' for row in table_data for cell in row):
                grid = Table(
                    table_data,
                    colWidths=[CELL_WIDTH] * COLS,
                    rowHeights=[CELL_HEIGHT] * ROWS_PER_PAGE,
                )
                grid.setStyle(TableStyle([
                    ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#fafafa')),
                    ('TOPPADDING',    (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING',   (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
                ]))
                elements.append(grid)

            # Page break between pages, but not after the very last one
            if page_start + PAGE_GAP < len(qr_list):
                elements.append(PageBreak())

        # ── Render PDF ─────────────────────────────────────────────────
        doc.build(elements)
        pdf_buffer.seek(0)

        filename = f"qr_codes_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except ImportError:
        return JsonResponse({
            'success': False,
            'message': 'ReportLab is required. Install it with: pip install reportlab',
        }, status=500)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request body'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'Error generating PDF: {str(e)}'}, status=500)
    
    
# @login_required
# @require_http_methods(["POST"])
# def download_bulk_qr_codes(request):
#     """Download multiple QR codes as a single PDF"""
#     try:
#         import json
#         from reportlab.lib import colors
#         from reportlab.lib.pagesizes import A4, letter
#         from reportlab.lib.units import mm, inch
#         from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
#         from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
#         from reportlab.lib.enums import TA_CENTER
#         from io import BytesIO
        
#         data = json.loads(request.body)
#         ids = data.get('ids', [])
        
#         if not ids:
#             return JsonResponse({
#                 'success': False,
#                 'message': 'No QR codes selected'
#             }, status=400)
        
#         # Get QR codes with images
#         qr_codes = QR_CodeModel.objects.filter(id__in=ids).exclude(qr_code='')
        
#         if not qr_codes.exists():
#             return JsonResponse({
#                 'success': False,
#                 'message': 'No QR codes with images found'
#             }, status=404)
        
#         # Create PDF in memory
#         pdf_buffer = BytesIO()
        
#         # Set up the document
#         doc = SimpleDocTemplate(
#             pdf_buffer,
#             pagesize=A4,
#             rightMargin=10*mm,
#             leftMargin=10*mm,
#             topMargin=10*mm,
#             bottomMargin=10*mm
#         )
        
#         # Container for the 'Flowable' objects
#         elements = []
        
#         # Styles
#         styles = getSampleStyleSheet()
#         title_style = ParagraphStyle(
#             'CustomTitle',
#             parent=styles['Heading1'],
#             fontSize=16,
#             alignment=TA_CENTER,
#             spaceAfter=20
#         )
        
#         # Add title
#         elements.append(Paragraph(f"QR Codes - {len(qr_codes)} selected", title_style))
#         elements.append(Spacer(1, 10*mm))
        
#         # Calculate grid layout (3x3 per page for A4)
#         cols = 3
#         rows_per_page = 3
#         qr_size = 60*mm  # 60mm x 60mm for QR code
#         label_height = 10*mm  # Height for the label
        
#         # Create table data
#         qr_list = list(qr_codes)
#         total_qrs = len(qr_list)
        
#         for i in range(0, total_qrs, cols * rows_per_page):
#             # Get QR codes for this page
#             page_qrs = qr_list[i:i + (cols * rows_per_page)]
            
#             # Prepare table data for this page
#             table_data = []
            
#             for row in range(rows_per_page):
#                 row_data = []
#                 for col in range(cols):
#                     idx = row * cols + col
#                     if idx < len(page_qrs):
#                         qr = page_qrs[idx]
                        
#                         # Create cell content
#                         cell_content = []
                        
#                         # Add QR code image
#                         if qr.qr_code:
#                             qr_file = qr.qr_code.open('rb')
#                             img = Image(qr_file, width=qr_size, height=qr_size)
#                             cell_content.append(img)
                            
#                             # Add QR code number/label
#                             label_style = ParagraphStyle(
#                                 'Label',
#                                 parent=styles['Normal'],
#                                 fontSize=8,
#                                 alignment=TA_CENTER,
#                                 textColor=colors.black
#                             )
#                             cell_content.append(Paragraph(f"QR Code: {qr.uid}", label_style))
                            
#                             # Create a table for each cell to stack image and label
#                             cell_table = Table([[cell_content[0]], [cell_content[1]]], 
#                                              colWidths=[qr_size])
#                             cell_table.setStyle(TableStyle([
#                                 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#                                 ('LEFTPADDING', (0, 0), (-1, -1), 0),
#                                 ('RIGHTPADDING', (0, 0), (-1, -1), 0),
#                                 ('TOPPADDING', (0, 0), (-1, -1), 0),
#                                 ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
#                             ]))
                            
#                             row_data.append(cell_table)
                            
#                             # Close the file
#                             qr.qr_code.close()
#                         else:
#                             row_data.append('')
#                     else:
#                         row_data.append('')
                
#                 if row_data:
#                     table_data.append(row_data)
            
#             # Create table for this page
#             if table_data:
#                 # Calculate column widths
#                 col_widths = [qr_size] * cols
                
#                 # Create the table
#                 table = Table(table_data, colWidths=col_widths, rowHeights=[qr_size + label_height] * len(table_data))
#                 table.setStyle(TableStyle([
#                     ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                     ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#                     ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
#                     ('TOPPADDING', (0, 0), (-1, -1), 5),
#                     ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
#                     ('LEFTPADDING', (0, 0), (-1, -1), 5),
#                     ('RIGHTPADDING', (0, 0), (-1, -1), 5),
#                 ]))
                
#                 elements.append(table)
                
#                 # Add page break if not last page
#                 if i + (cols * rows_per_page) < total_qrs:
#                     elements.append(PageBreak())
        
#         # Build PDF
#         doc.build(elements)
#         pdf_buffer.seek(0)
        
#         # Create response
#         response = HttpResponse(pdf_buffer, content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="qr_codes_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
#         return response
        
#     except ImportError as e:
#         return JsonResponse({
#             'success': False,
#             'message': 'ReportLab is required for PDF generation. Please install it: pip install reportlab'
#         }, status=500)
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return JsonResponse({
#             'success': False,
#             'message': f'Error generating PDF: {str(e)}'
#         }, status=500)

# @login_required
# @require_http_methods(["POST"])
# def download_bulk_qr_codes(request):
#     """Download multiple QR codes as ZIP"""
#     try:
#         import json
#         import zipfile
#         from io import BytesIO
        
#         data = json.loads(request.body)
#         ids = data.get('ids', [])
        
#         if not ids:
#             return JsonResponse({
#                 'success': False,
#                 'message': 'No QR codes selected'
#             }, status=400)
        
#         qr_codes = QR_CodeModel.objects.filter(id__in=ids)
        
#         # Create ZIP file in memory
#         zip_buffer = BytesIO()
#         with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
#             for qr in qr_codes:
#                 if qr.qr_code and qr.qr_code.name:
#                     try:
#                         qr.qr_code.open('rb')
#                         file_content = qr.qr_code.read()
#                         zip_file.writestr(f"{qr.uid}.png", file_content)
#                         qr.qr_code.close()
#                     except Exception as e:
#                         print(f"Error adding {qr.uid} to zip: {e}")
#                         continue
        
#         zip_buffer.seek(0)
        
#         response = HttpResponse(zip_buffer, content_type='application/zip')
#         response['Content-Disposition'] = f'attachment; filename="qr_codes_{timezone.now().strftime("%Y%m%d_%H%M%S")}.zip"'
        
#         return response
        
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'message': f'Error downloading QR codes: {str(e)}'
#         }, status=500)