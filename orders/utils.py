from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, Frame, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
from decimal import Decimal
import os
from django.conf import settings
import requests
from PIL import Image as PILImage
from io import BytesIO as PILBytesIO

# Register a Unicode font that supports the Rupee symbol
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf')))
except:
    print("Warning: DejaVuSans font not found, falling back to default font")

def generate_invoice_pdf(order):
    # Create a buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object with optimized margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=30,
        bottomMargin=30,
        encoding='utf-8'
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Modern color scheme - New Theme
    primary_color = colors.HexColor('#2c3e50')  # Dark Blue
    secondary_color = colors.HexColor('#34495e')  # Darker Blue
    text_color = colors.HexColor('#2c3e50')  # Dark Blue for text
    light_bg = colors.HexColor('#ecf0f1')  # Light Gray
    border_color = colors.HexColor('#bdc3c7')  # Medium Gray
    success_color = colors.HexColor('#27ae60')  # Green
    
    # Custom styles with modern design
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=10,
        textColor=primary_color,
        alignment=1,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=10,
        spaceAfter=5,
        textColor=secondary_color,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=3,
        textColor=text_color,
        fontName='Helvetica',
        leading=12
    )
    
    # Add logo with adjusted size
    try:
        logo_url = "https://i.postimg.cc/wxtWnxzs/TRENDY.jpg"
        logo_response = requests.get(logo_url)
        if logo_response.status_code == 200:
            img = PILImage.open(PILBytesIO(logo_response.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            temp_buffer = BytesIO()
            img.save(temp_buffer, format='JPEG', quality=95)
            temp_buffer.seek(0)
            
            logo = Image(temp_buffer)
            logo.drawHeight = 0.8*inch
            logo.drawWidth = 2.5*inch
            elements.append(logo)
            elements.append(Spacer(1, 10))
    except Exception as e:
        print(f"Error processing logo: {e}")

    # Add invoice header with reduced spacing
    elements.append(Paragraph(f"ORDER #{order.order_id}", title_style))
    elements.append(Spacer(1, 5))
    
    # Create header info table with reduced spacing
    header_data = [
        [Paragraph("INVOICE DATE", heading_style), Paragraph("ORDER STATUS", heading_style)],
        [Paragraph(order.created_at.strftime('%B %d, %Y'), normal_style), 
         Paragraph(order.get_status_display() if hasattr(order, 'get_status_display') else order.status.upper(), normal_style)]
    ]
    
    header_table = Table(header_data, colWidths=[doc.width/2.0]*2)
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, -1), text_color),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, border_color),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 8),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # Create billing and shipping info with reduced spacing
    info_data = [
        [Paragraph("BILL TO", heading_style), Paragraph("SHIP TO", heading_style)],
        [
            Paragraph(f"{order.first_name} {order.last_name}<br/>"
                     f"{order.email}<br/>"
                     f"{order.phone}", normal_style),
            Paragraph(f"{order.shipping_address}", normal_style)
        ]
    ]
    
    info_table = Table(info_data, colWidths=[doc.width/2.0]*2)
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, -1), text_color),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, border_color),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 8),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # Order items table with adjusted styling
    elements.append(Paragraph("ORDER DETAILS", heading_style))
    elements.append(Spacer(1, 5))
    
    # Table headers
    table_data = [['ITEM', 'QTY', 'PRICE', 'TOTAL']]
    
    # Calculate subtotal
    items_subtotal = Decimal('0.00')
    for item in order.items.all():
        item_total = item.price * item.quantity
        items_subtotal += item_total
        table_data.append([
            Paragraph(item.product.name, normal_style),
            str(item.quantity),
            f"Rs. {item.price:.2f}",
            f"Rs. {item_total:.2f}"
        ])
    
    # Calculate totals
    subtotal = getattr(order, 'subtotal', None) or items_subtotal
    shipping_cost = getattr(order, 'shipping_cost', None) or Decimal('0.00')
    tax = getattr(order, 'tax', None) or (subtotal * Decimal('0.10'))
    discount = getattr(order, 'discount', None) or Decimal('0.00')
    total = getattr(order, 'total', None) or (subtotal + shipping_cost + tax - discount)
    
    # Add summary rows with minimal spacing
    table_data.extend([
        ['', '', Paragraph('Subtotal:', normal_style), f"Rs. {subtotal:.2f}"],
        ['', '', Paragraph('Shipping:', normal_style), f"Rs. {shipping_cost:.2f}"],
        ['', '', Paragraph('Tax:', normal_style), f"Rs. {tax:.2f}"],
        ['', '', Paragraph('Discount:', normal_style), f"Rs. {discount:.2f}"],
        ['', '', Paragraph('<b>TOTAL</b>', normal_style), f"Rs. {total:.2f}"]
    ])
    
    # Create table with improved styling
    order_table = Table(table_data, colWidths=[doc.width*0.4, doc.width*0.1, doc.width*0.25, doc.width*0.25])
    order_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('PADDING', (0, 0), (-1, 0), 8),
        
        # Body styling
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('PADDING', (0, 1), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -6), 0.5, border_color),
        
        # Total section styling
        ('LINEABOVE', (-2, -5), (-1, -5), 0.5, border_color),
        ('LINEABOVE', (-2, -1), (-1, -1), 1, text_color),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (-2, -1), (-1, -1), 10),
        ('TEXTCOLOR', (-2, -1), (-1, -1), text_color),
    ]))
    
    elements.append(order_table)
    elements.append(Spacer(1, 15))

    # Payment information with minimal styling
    elements.append(Paragraph("PAYMENT INFORMATION", heading_style))
    elements.append(Spacer(1, 5))
    
    payment_method = getattr(order, 'payment_method', None)
    payment_status = getattr(order, 'payment_status', None)
    
    payment_data = [
        ['Payment Method', order.get_payment_method_display() if hasattr(order, 'get_payment_method_display') else payment_method or 'N/A'],
        ['Payment Status', order.get_payment_status_display() if hasattr(order, 'get_payment_status_display') else payment_status or 'N/A']
    ]
    
    if order.transaction_id:
        payment_data.append(['Transaction ID', order.transaction_id])
    
    payment_table = Table(payment_data, colWidths=[doc.width*0.3, doc.width*0.7])
    payment_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), text_color),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, border_color),
    ]))
    
    elements.append(payment_table)
    elements.append(Spacer(1, 15))

    # Footer with minimal styling
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=text_color,
        alignment=1,
        fontName='Helvetica',
        spaceBefore=10
    )
    
    elements.append(Paragraph("Thank you for shopping with us!", footer_style))
    elements.append(Paragraph("For any questions or concerns, please contact our customer support.", footer_style))
    
    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{order.order_id}.pdf"'
    response.write(pdf)
    
    return response
