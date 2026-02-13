from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.views import View
from django.contrib import messages
from django.db.models import Q, F
from django.db import transaction
from datetime import datetime, date
from .models import RequestItems, Items, User, OutgoingTransaction
from .forms import RequestItemForm, ApproveRequestForm
from .mixins import ProduksiRequiredMixin, GudangRequiredMixin, ProduksiOrGudangMixin
from django.contrib.auth.mixins import UserPassesTestMixin

class RequestItemListView(ProduksiOrGudangMixin, ListView):
    """List all request items - accessible by produksi and gudang (both see all requests)"""
    model = RequestItems
    template_name = 'inventory/production/request_list.html'
    context_object_name = 'requests'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.session.get('user_id')
        user = User.objects.get(user_id=user_id)
        
        # Both Produksi and Gudang should see all requests for consistency
        # No filtering by user - everyone sees the same data
        
        # Apply filters
        search = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if search:
            queryset = queryset.filter(
                Q(request_number__icontains=search) |
                Q(item__name__icontains=search) |
                Q(purpose__icontains=search)
            )
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if date_from:
            queryset = queryset.filter(request_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(request_date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.request.session.get('user_id')
        user = User.objects.get(user_id=user_id)
        
        context['user'] = user
        context['is_admin_or_gudang'] = user.role in ['admin', 'pegawai_gudang']
        context['is_produksi'] = user.role == 'pegawai_produksi'
        
        # Count statistics - same for all users (consistent data)
        context['pending_count'] = RequestItems.objects.filter(status='pending').count()
        context['approved_count'] = RequestItems.objects.filter(status='approved').count()
        context['rejected_count'] = RequestItems.objects.filter(status='rejected').count()
        
        return context

class RequestItemCreateView(ProduksiRequiredMixin, CreateView):
    """Create new request item - only accessible by produksi"""
    model = RequestItems
    form_class = RequestItemForm
    template_name = 'inventory/production/request_form.html'
    success_url = reverse_lazy('request_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add stock info for all items
        context['items_with_stock'] = Items.objects.filter(is_active=True).select_related('category')
        return context
    
    def form_valid(self, form):
        # Set requested_by to current user
        user_id = self.request.session.get('user_id')
        if user_id:
            form.instance.requested_by_id = user_id
        
        # Check stock and show appropriate message
        item = form.instance.item
        quantity = form.instance.quantity
        
        if item.current_stock >= quantity:
            messages.success(
                self.request,
                f'Permintaan barang {item.name} berhasil dibuat. '
                f'Stok tersedia: {item.current_stock} {item.get_unit_display()}.'
            )
        else:
            messages.warning(
                self.request,
                f'Permintaan barang {item.name} berhasil dibuat. '
                f'Stok saat ini: {item.current_stock} {item.get_unit_display()} (kurang dari permintaan). '
                f'Menunggu persetujuan admin/gudang.'
            )
        
        return super().form_valid(form)

class RequestItemDetailView(ProduksiOrGudangMixin, DetailView):
    """View request item details - accessible by produksi and gudang"""
    model = RequestItems
    template_name = 'inventory/production/request_detail.html'
    context_object_name = 'request'
    pk_url_kwarg = 'request_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.request.session.get('user_id')
        user = User.objects.get(user_id=user_id)
        
        context['user'] = user
        context['is_admin_or_gudang'] = user.role in ['admin', 'pegawai_gudang']
        context['can_approve'] = user.role in ['admin', 'pegawai_gudang'] and self.object.status == 'pending'
        
        # Check current stock availability
        request_obj = self.get_object()
        context['stock_available'] = request_obj.item.current_stock >= request_obj.quantity
        context['stock_info'] = {
            'current': request_obj.item.current_stock,
            'requested': request_obj.quantity,
            'unit': request_obj.item.get_unit_display(),
            'deficit': max(0, request_obj.quantity - request_obj.item.current_stock)
        }
        
        return context

class RequestItemApproveView(GudangRequiredMixin, UpdateView):
    """Approve or reject request item (Admin/Gudang only)"""
    model = RequestItems
    form_class = ApproveRequestForm
    template_name = 'inventory/production/request_approve.html'
    pk_url_kwarg = 'request_id'
    success_url = reverse_lazy('request_list')
    
    def get_queryset(self):
        # Only allow approval of pending requests
        return super().get_queryset().filter(status='pending')
    
    def form_valid(self, form):
        user_id = self.request.session.get('user_id')
        request_obj = form.instance
        new_status = form.cleaned_data.get('status')
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Set approved_by and approved_date
            if new_status in ['approved', 'rejected']:
                form.instance.approved_by_id = user_id
                form.instance.approved_date = datetime.now()
            
            # If approved, check stock and create outgoing transaction
            if new_status == 'approved':
                item = request_obj.item
                requested_qty = request_obj.quantity
                
                # Check if stock is sufficient
                if item.current_stock < requested_qty:
                    messages.error(
                        self.request,
                        f'Stok tidak mencukupi! Stok tersedia: {item.current_stock} {item.get_unit_display()}, '
                        f'diminta: {requested_qty} {item.get_unit_display()}. '
                        f'Permintaan tidak dapat disetujui.'
                    )
                    return redirect('request_detail', request_id=request_obj.request_id)
                
                # Save the request first
                response = super().form_valid(form)
                
                # Create outgoing transaction automatically
                today = date.today()
                last_outgoing = OutgoingTransaction.objects.filter(
                    transaction_number__startswith=f'OUT{today.strftime("%Y%m%d")}'
                ).order_by('-transaction_number').first()
                
                if last_outgoing:
                    last_number = int(last_outgoing.transaction_number[-4:])
                    new_number = last_number + 1
                else:
                    new_number = 1
                
                transaction_number = f'OUT{today.strftime("%Y%m%d")}{str(new_number).zfill(4)}'
                
                # Create the outgoing transaction
                # Stock will be automatically reduced by OutgoingTransaction.save() method
                outgoing = OutgoingTransaction.objects.create(
                    transaction_number=transaction_number,
                    request_item=request_obj,
                    item=item,
                    quantity=requested_qty,
                    transaction_date=today,
                    purpose=f'Permintaan: {request_obj.request_number} - {request_obj.purpose}',
                    status='released',
                    notes=f'Dibuat otomatis dari persetujuan permintaan {request_obj.request_number}',
                    released_by_id=user_id
                )
                
                # Stock reduction is handled automatically in OutgoingTransaction.save()
                # No need to manually reduce stock here to avoid double reduction
                
                messages.success(
                    self.request,
                    f'Permintaan {request_obj.request_number} telah disetujui. '
                    f'Transaksi barang keluar {transaction_number} telah dibuat. '
                    f'Stok {item.name} berkurang {requested_qty} {item.get_unit_display()}.'
                )
                
                return response
                
            elif new_status == 'rejected':
                messages.warning(
                    self.request,
                    f'Permintaan {request_obj.request_number} telah ditolak. '
                    f'Alasan: {form.cleaned_data.get("rejection_reason", "Tidak disebutkan")}'
                )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_obj = self.get_object()
        
        # Add stock info
        context['stock_info'] = {
            'current': request_obj.item.current_stock,
            'requested': request_obj.quantity,
            'unit': request_obj.item.get_unit_display(),
            'deficit': max(0, request_obj.quantity - request_obj.item.current_stock),
            'available': request_obj.item.current_stock >= request_obj.quantity
        }
        
        return context

class ProduksiDashboardView(ProduksiOrGudangMixin, View):
    """Redirect to unified dashboard - all roles now use the same dashboard template"""
    def get(self, request):
        # Redirect to main dashboard which now serves all roles
        return redirect('dashboard')