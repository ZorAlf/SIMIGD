from django.views.generic import TemplateView, ListView
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
from .models import Items, IncomingTransaction, OutgoingTransaction, RequestItems, User
from .mixins import DirekturRequiredMixin
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO

class DirekturDashboardView(DirekturRequiredMixin, TemplateView):
    """
    Dashboard Direktur with unified template - redirects to main dashboard
    All roles now use the same dashboard view for consistency
    """
    
    def get(self, request, *args, **kwargs):
        # Redirect to unified dashboard
        from django.shortcuts import redirect
        return redirect('dashboard')


class LaporanListView(DirekturRequiredMixin, TemplateView):
    """
    Laporan Gudang dengan tabs:
    - Laporan Stok Barang
    - Laporan Barang Masuk
    - Laporan Barang Keluar
    - Laporan Permintaan Barang
    """
    template_name = 'inventory/director/report_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Active tab (default: stok)
        active_tab = self.request.GET.get('tab', 'stok')
        
        # Filter parameters
        search = self.request.GET.get('search', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        # Laporan Stok Barang
        stok_items = Items.objects.filter(is_active=True)
        if search:
            stok_items = stok_items.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(category__name__icontains=search)
            )
        stok_items = stok_items.select_related('category').order_by('-current_stock')
        
        # Categorize items by stock status
        stok_items_list = list(stok_items)
        in_stock_items = [item for item in stok_items_list if item.stock_status == 'in_stock']
        low_stock_items = [item for item in stok_items_list if item.stock_status == 'low_stock']
        out_of_stock_items = [item for item in stok_items_list if item.stock_status == 'out_of_stock']
        
        # Laporan Barang Masuk
        incoming = IncomingTransaction.objects.all()
        if search:
            incoming = incoming.filter(
                Q(item__name__icontains=search) |
                Q(supplier__name__icontains=search) |
                Q(notes__icontains=search)
            )
        if date_from:
            incoming = incoming.filter(transaction_date__gte=date_from)
        if date_to:
            incoming = incoming.filter(transaction_date__lte=date_to)
        incoming = incoming.select_related('item', 'supplier', 'received_by').order_by('-transaction_date')
        
        # Laporan Barang Keluar
        outgoing = OutgoingTransaction.objects.all()
        if search:
            outgoing = outgoing.filter(
                Q(item__name__icontains=search) |
                Q(purpose__icontains=search) |
                Q(notes__icontains=search)
            )
        if date_from:
            outgoing = outgoing.filter(transaction_date__gte=date_from)
        if date_to:
            outgoing = outgoing.filter(transaction_date__lte=date_to)
        outgoing = outgoing.select_related('item', 'released_by').order_by('-transaction_date')
        
        # Laporan Permintaan Barang
        requests = RequestItems.objects.all()
        if search:
            requests = requests.filter(
                Q(request_number__icontains=search) |
                Q(item__name__icontains=search) |
                Q(purpose__icontains=search)
            )
        if date_from:
            requests = requests.filter(request_date__gte=date_from)
        if date_to:
            requests = requests.filter(request_date__lte=date_to)
        requests = requests.select_related('item', 'requested_by', 'approved_by').order_by('-request_date')
        
        # Summary statistics per tab
        stok_summary = {
            'total_items': stok_items.count(),
            'total_stock': stok_items.aggregate(total=Sum('current_stock'))['total'] or 0,
            'low_stock_count': stok_items.filter(current_stock__lt=F('minimum_stock')).count(),
            'in_stock_count': len(in_stock_items),
            'out_of_stock_count': len(out_of_stock_items),
        }
        
        incoming_summary = {
            'total_transactions': incoming.count(),
            'total_quantity': incoming.aggregate(total=Sum('quantity'))['total'] or 0,
        }
        
        outgoing_summary = {
            'total_transactions': outgoing.count(),
            'total_quantity': outgoing.aggregate(total=Sum('quantity'))['total'] or 0,
        }
        
        request_summary = {
            'total_requests': requests.count(),
            'pending': requests.filter(status='pending').count(),
            'approved': requests.filter(status='approved').count(),
            'rejected': requests.filter(status='rejected').count(),
        }
        
        context.update({
            'active_tab': active_tab,
            'search': search,
            'date_from': date_from,
            'date_to': date_to,
            
            # Data per tab
            'stok_items': stok_items,
            'in_stock_items': in_stock_items,
            'low_stock_items': low_stock_items,
            'out_of_stock_items': out_of_stock_items,
            'incoming_transactions': incoming,
            'outgoing_transactions': outgoing,
            'request_items': requests,
            
            # Summaries
            'stok_summary': stok_summary,
            'incoming_summary': incoming_summary,
            'outgoing_summary': outgoing_summary,
            'request_summary': request_summary,
        })
        
        return context


class ExportPDFBarangMasukView(DirekturRequiredMixin, TemplateView):
    """
    Export Laporan Barang Masuk ke PDF
    """
    def get(self, request, *args, **kwargs):
        # Get filter parameters
        search = request.GET.get('search', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Query data
        incoming = IncomingTransaction.objects.all()
        if search:
            incoming = incoming.filter(
                Q(item__name__icontains=search) |
                Q(supplier__name__icontains=search) |
                Q(notes__icontains=search)
            )
        if date_from:
            incoming = incoming.filter(transaction_date__gte=date_from)
        if date_to:
            incoming = incoming.filter(transaction_date__lte=date_to)
        incoming = incoming.select_related('item', 'supplier', 'received_by').order_by('-transaction_date')
        
        # Calculate summary
        total_quantity = incoming.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Header Section
        elements.append(Paragraph("LAPORAN BARANG MASUK", title_style))
        elements.append(Paragraph("Sistem Informasi Manajemen Inventaris Gudang - PT Delimajaya", subtitle_style))
        
        # Info Section
        info_data = [
            ['Dicetak oleh:', request.session.get('name', 'Direktur'), 'Tanggal Cetak:', datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Periode:', f"{date_from or 'Semua'} s/d {date_to or 'Sekarang'}", 'Total Transaksi:', str(incoming.count())],
            ['Filter Pencarian:', search or '-', 'Total Quantity:', f"{total_quantity:,}"],
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e9ecef')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Table Header
        table_data = [[
            'No',
            'No. Transaksi',
            'Tanggal',
            'Kode Barang',
            'Nama Barang',
            'Supplier',
            'Quantity',
            'Satuan',
            'Status',
            'Diterima Oleh'
        ]]
        
        # Table Data
        for idx, trans in enumerate(incoming, 1):
            table_data.append([
                str(idx),
                trans.transaction_number,
                trans.transaction_date.strftime('%d/%m/%Y'),
                trans.item.code,
                trans.item.name[:30] + '...' if len(trans.item.name) > 30 else trans.item.name,
                trans.supplier.name[:20] + '...' if trans.supplier and len(trans.supplier.name) > 20 else (trans.supplier.name if trans.supplier else '-'),
                str(trans.quantity),
                trans.item.get_unit_display(),
                trans.get_status_display(),
                trans.received_by.name[:15] + '...' if trans.received_by and len(trans.received_by.name) > 15 else (trans.received_by.name if trans.received_by else '-'),
            ])
        
        # Create table
        table = Table(table_data, colWidths=[1*cm, 3*cm, 2.2*cm, 2.2*cm, 4*cm, 3.5*cm, 1.8*cm, 1.8*cm, 2*cm, 2.5*cm])
        
        # Table Style
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows style
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # No
            ('ALIGN', (6, 1), (6, -1), 'RIGHT'),   # Quantity
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            
            # Alternating row colors
            *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')) for i in range(2, len(table_data), 2)]
        ]))
        
        elements.append(table)
        
        # Footer
        elements.append(Spacer(1, 0.5*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_RIGHT
        )
        elements.append(Paragraph(f"Dicetak pada: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}", footer_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF from buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = HttpResponse(content_type='application/pdf')
        filename = f"laporan_barang_masuk_{datetime.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)
        
        return response


class ExportPDFBarangKeluarView(DirekturRequiredMixin, TemplateView):
    """
    Export Laporan Barang Keluar ke PDF
    """
    def get(self, request, *args, **kwargs):
        # Get filter parameters
        search = request.GET.get('search', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Query data
        outgoing = OutgoingTransaction.objects.all()
        if search:
            outgoing = outgoing.filter(
                Q(item__name__icontains=search) |
                Q(purpose__icontains=search) |
                Q(notes__icontains=search)
            )
        if date_from:
            outgoing = outgoing.filter(transaction_date__gte=date_from)
        if date_to:
            outgoing = outgoing.filter(transaction_date__lte=date_to)
        outgoing = outgoing.select_related('item', 'released_by').order_by('-transaction_date')
        
        # Calculate summary
        total_quantity = outgoing.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Header Section
        elements.append(Paragraph("LAPORAN BARANG KELUAR", title_style))
        elements.append(Paragraph("Sistem Informasi Manajemen Inventaris Gudang - PT Delimajaya", subtitle_style))
        
        # Info Section
        info_data = [
            ['Dicetak oleh:', request.session.get('name', 'Direktur'), 'Tanggal Cetak:', datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Periode:', f"{date_from or 'Semua'} s/d {date_to or 'Sekarang'}", 'Total Transaksi:', str(outgoing.count())],
            ['Filter Pencarian:', search or '-', 'Total Quantity:', f"{total_quantity:,}"],
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e9ecef')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Table Header
        table_data = [[
            'No',
            'No. Transaksi',
            'Tanggal',
            'Kode Barang',
            'Nama Barang',
            'Tujuan/Keperluan',
            'Quantity',
            'Satuan',
            'Status',
            'Dikeluarkan Oleh'
        ]]
        
        # Table Data
        for idx, trans in enumerate(outgoing, 1):
            table_data.append([
                str(idx),
                trans.transaction_number,
                trans.transaction_date.strftime('%d/%m/%Y'),
                trans.item.code,
                trans.item.name[:30] + '...' if len(trans.item.name) > 30 else trans.item.name,
                trans.purpose[:25] + '...' if len(trans.purpose) > 25 else trans.purpose,
                str(trans.quantity),
                trans.item.get_unit_display(),
                trans.get_status_display(),
                trans.released_by.name[:15] + '...' if trans.released_by and len(trans.released_by.name) > 15 else (trans.released_by.name if trans.released_by else '-'),
            ])
        
        # Create table
        table = Table(table_data, colWidths=[1*cm, 3*cm, 2.2*cm, 2.2*cm, 4*cm, 4*cm, 1.8*cm, 1.8*cm, 2*cm, 2.5*cm])
        
        # Table Style
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows style
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # No
            ('ALIGN', (6, 1), (6, -1), 'RIGHT'),   # Quantity
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            
            # Alternating row colors
            *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')) for i in range(2, len(table_data), 2)]
        ]))
        
        elements.append(table)
        
        # Footer
        elements.append(Spacer(1, 0.5*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_RIGHT
        )
        elements.append(Paragraph(f"Dicetak pada: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}", footer_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF from buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = HttpResponse(content_type='application/pdf')
        filename = f"laporan_barang_keluar_{datetime.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)
        
        return response


class HistoriAktivitasView(DirekturRequiredMixin, ListView):
    """
    Histori Aktivitas - All transactions in one place
    Menampilkan gabungan dari:
    - IncomingTransaction
    - OutgoingTransaction
    - RequestItems
    """
    template_name = 'inventory/director/activity_history.html'
    context_object_name = 'activities'
    paginate_by = 20
    
    def get_queryset(self):
        # Collect all activities with type indicator
        activities = []
        
        # Get filter parameters
        search = self.request.GET.get('search', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        activity_type = self.request.GET.get('type', '')  # incoming, outgoing, request
        
        # Incoming Transactions
        if activity_type == '' or activity_type == 'incoming':
            incoming = IncomingTransaction.objects.all()
            if search:
                incoming = incoming.filter(
                    Q(item__name__icontains=search) |
                    Q(supplier__name__icontains=search)
                )
            if date_from:
                incoming = incoming.filter(transaction_date__gte=date_from)
            if date_to:
                incoming = incoming.filter(transaction_date__lte=date_to)
            
            for trans in incoming.select_related('item', 'supplier', 'received_by'):
                activities.append({
                    'type': 'incoming',
                    'type_label': 'Barang Masuk',
                    'date': trans.transaction_date,
                    'item_name': trans.item.name,
                    'quantity': trans.quantity,
                    'unit': trans.item.get_unit_display(),
                    'user': trans.received_by.name if trans.received_by else '-',
                    'reference': f"Supplier: {trans.supplier.name if trans.supplier else '-'}",
                    'notes': trans.notes or '-',
                    'id': trans.incoming_id,
                })
        
        # Outgoing Transactions
        if activity_type == '' or activity_type == 'outgoing':
            outgoing = OutgoingTransaction.objects.all()
            if search:
                outgoing = outgoing.filter(
                    Q(item__name__icontains=search) |
                    Q(purpose__icontains=search)
                )
            if date_from:
                outgoing = outgoing.filter(transaction_date__gte=date_from)
            if date_to:
                outgoing = outgoing.filter(transaction_date__lte=date_to)
            
            for trans in outgoing.select_related('item', 'released_by'):
                activities.append({
                    'type': 'outgoing',
                    'type_label': 'Barang Keluar',
                    'date': trans.transaction_date,
                    'item_name': trans.item.name,
                    'quantity': trans.quantity,
                    'unit': trans.item.get_unit_display(),
                    'user': trans.released_by.name if trans.released_by else '-',
                    'reference': f"Tujuan: {trans.purpose}",
                    'notes': trans.notes or '-',
                    'id': trans.outgoing_id,
                })
        
        # Request Items
        if activity_type == '' or activity_type == 'request':
            requests = RequestItems.objects.all()
            if search:
                requests = requests.filter(
                    Q(request_number__icontains=search) |
                    Q(item__name__icontains=search) |
                    Q(purpose__icontains=search)
                )
            if date_from:
                requests = requests.filter(request_date__gte=date_from)
            if date_to:
                requests = requests.filter(request_date__lte=date_to)
            
            for req in requests.select_related('item', 'requested_by', 'approved_by'):
                activities.append({
                    'type': 'request',
                    'type_label': 'Permintaan Barang',
                    'date': req.request_date,
                    'item_name': req.item.name,
                    'quantity': req.quantity,
                    'unit': req.item.get_unit_display(),
                    'user': req.requested_by.name if req.requested_by else '-',
                    'reference': f"No: {req.request_number} - {req.get_status_display()}",
                    'notes': req.purpose,
                    'status': req.status,
                    'id': req.request_id,
                })
        
        # Sort by date descending
        activities.sort(key=lambda x: x['date'], reverse=True)
        
        return activities
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filter parameters
        context['search'] = self.request.GET.get('search', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['activity_type'] = self.request.GET.get('type', '')
        
        # Statistics
        all_activities = self.get_queryset()
        context['total_activities'] = len(all_activities)
        context['incoming_count'] = sum(1 for a in all_activities if a['type'] == 'incoming')
        context['outgoing_count'] = sum(1 for a in all_activities if a['type'] == 'outgoing')
        context['request_count'] = sum(1 for a in all_activities if a['type'] == 'request')
        
        return context
