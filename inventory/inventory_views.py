from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.db.models import Q, Sum
from datetime import datetime
from .models import Category, Supplier, Items, IncomingTransaction, OutgoingTransaction, User
from .forms import CategoryForm, SupplierForm, ItemForm, IncomingTransactionForm, OutgoingTransactionForm
from .mixins import GudangRequiredMixin

"""
Views untuk Fitur Pegawai Gudang
- CRUD Barang Master (Items)
- CRUD Supplier
- CRUD Transaksi Barang Masuk (Incoming)
- CRUD Transaksi Barang Keluar (Outgoing)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.db.models import Q, Sum
from datetime import datetime

from .models import Category, Supplier, Items, IncomingTransaction, OutgoingTransaction, User
from .forms import CategoryForm, SupplierForm, ItemForm, IncomingTransactionForm, OutgoingTransactionForm
from .mixins import GudangRequiredMixin

class CategoryListView(GudangRequiredMixin, ListView):
    """List all categories"""
    model = Category
    template_name = 'inventory/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset

class CategoryCreateView(GudangRequiredMixin, CreateView):
    """Create new category"""
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'
    success_url = reverse_lazy('category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Kategori {form.instance.name} berhasil ditambahkan.')
        return super().form_valid(form)

class CategoryUpdateView(GudangRequiredMixin, UpdateView):
    """Update existing category"""
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'
    success_url = reverse_lazy('category_list')
    pk_url_kwarg = 'category_id'
    
    def form_valid(self, form):
        messages.success(self.request, f'Kategori {form.instance.name} berhasil diperbarui.')
        return super().form_valid(form)

class CategoryDeleteView(GudangRequiredMixin, DeleteView):
    """Delete category"""
    model = Category
    template_name = 'inventory/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')
    pk_url_kwarg = 'category_id'
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        messages.success(request, f'Kategori {category.name} berhasil dihapus.')
        return super().delete(request, *args, **kwargs)

class SupplierListView(GudangRequiredMixin, ListView):
    """List all suppliers"""
    model = Supplier
    template_name = 'inventory/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(contact_person__icontains=search)
            )
        
        if status_filter:
            if status_filter == 'active':
                queryset = queryset.filter(is_active=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(is_active=False)
        
        return queryset

class SupplierCreateView(GudangRequiredMixin, CreateView):
    """Create new supplier"""
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    success_url = reverse_lazy('supplier_list')
    
    def form_valid(self, form):
        # Pastikan kode supplier diambil dari hasil clean form (bukan dari POST user)
        self.object = form.save(commit=False)
        self.object.code = form.cleaned_data['code']
        self.object.save()
        messages.success(self.request, f'Supplier {form.instance.name} berhasil ditambahkan.')
        return super().form_valid(form)

class SupplierUpdateView(GudangRequiredMixin, UpdateView):
    """Update existing supplier"""
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    success_url = reverse_lazy('supplier_list')
    pk_url_kwarg = 'supplier_id'
    
    def form_valid(self, form):
        messages.success(self.request, f'Supplier {form.instance.name} berhasil diperbarui.')
        return super().form_valid(form)

class SupplierDetailView(GudangRequiredMixin, DetailView):
    """View supplier details"""
    model = Supplier
    template_name = 'inventory/supplier_detail.html'
    context_object_name = 'supplier'
    pk_url_kwarg = 'supplier_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier = self.get_object()
        
        # Get incoming transactions from this supplier (last 5)
        from .models import IncomingTransaction
        from django.db.models import Sum
        
        incoming_transactions = IncomingTransaction.objects.filter(
            supplier=supplier
        ).select_related('item').order_by('-transaction_date')[:5]
        
        # Get statistics
        all_transactions = IncomingTransaction.objects.filter(supplier=supplier)
        total_transactions = all_transactions.count()
        total_quantity = all_transactions.aggregate(total=Sum('quantity'))['total'] or 0
        last_transaction = all_transactions.order_by('-transaction_date').first()
        
        context['incoming_transactions'] = incoming_transactions
        context['total_transactions'] = total_transactions
        context['total_quantity'] = total_quantity
        context['last_transaction'] = last_transaction
        
        return context

class SupplierDeleteView(GudangRequiredMixin, DeleteView):
    """Delete supplier"""
    model = Supplier
    template_name = 'inventory/supplier_confirm_delete.html'
    success_url = reverse_lazy('supplier_list')
    pk_url_kwarg = 'supplier_id'
    
    def delete(self, request, *args, **kwargs):
        supplier = self.get_object()
        messages.success(request, f'Supplier {supplier.name} berhasil dihapus.')
        return super().delete(request, *args, **kwargs)

class ItemListView(GudangRequiredMixin, ListView):
    """List all items"""
    model = Items
    template_name = 'inventory/item_list.html'
    context_object_name = 'items'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        category_filter = self.request.GET.get('category')
        stock_status = self.request.GET.get('stock_status')
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )
        
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)
        
        if stock_status:
            if stock_status == 'low':
                queryset = [item for item in queryset if item.stock_status == 'low_stock']
            elif stock_status == 'out':
                queryset = [item for item in queryset if item.stock_status == 'out_of_stock']
            elif stock_status == 'in':
                queryset = [item for item in queryset if item.stock_status == 'in_stock']
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search'] = self.request.GET.get('search', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['stock_status'] = self.request.GET.get('stock_status', '')
        return context

class ItemCreateView(GudangRequiredMixin, CreateView):
    """Create new item"""
    model = Items
    form_class = ItemForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('item_list')
    
    def form_valid(self, form):
        # Set created_by to current user
        user_id = self.request.session.get('user_id')
        if user_id:
            form.instance.created_by_id = user_id
            form.instance.updated_by_id = user_id
        
        messages.success(self.request, f'Barang {form.instance.name} berhasil ditambahkan.')
        return super().form_valid(form)

class ItemUpdateView(GudangRequiredMixin, UpdateView):
    """Update existing item"""
    model = Items
    form_class = ItemForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('item_list')
    pk_url_kwarg = 'item_id'
    
    def form_valid(self, form):
        # Set updated_by to current user
        user_id = self.request.session.get('user_id')
        if user_id:
            form.instance.updated_by_id = user_id
        
        messages.success(self.request, f'Barang {form.instance.name} berhasil diperbarui.')
        return super().form_valid(form)

class ItemDetailView(GudangRequiredMixin, DetailView):
    """View item details"""
    model = Items
    template_name = 'inventory/item_detail.html'
    context_object_name = 'item'
    pk_url_kwarg = 'item_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.get_object()
        
        # Get recent incoming transactions
        context['recent_incoming'] = IncomingTransaction.objects.filter(
            item=item
        ).order_by('-transaction_date')[:5]
        
        # Get recent outgoing transactions
        context['recent_outgoing'] = OutgoingTransaction.objects.filter(
            item=item
        ).order_by('-transaction_date')[:5]
        
        return context

class ItemDeleteView(GudangRequiredMixin, DeleteView):
    """Delete item"""
    model = Items
    template_name = 'inventory/item_confirm_delete.html'
    success_url = reverse_lazy('item_list')
    pk_url_kwarg = 'item_id'
    
    def delete(self, request, *args, **kwargs):
        item = self.get_object()
        messages.success(request, f'Barang {item.name} berhasil dihapus.')
        return super().delete(request, *args, **kwargs)

class IncomingListView(GudangRequiredMixin, ListView):
    """List all incoming transactions"""
    model = IncomingTransaction
    template_name = 'inventory/incoming_list.html'
    context_object_name = 'transactions'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if search:
            queryset = queryset.filter(
                Q(transaction_number__icontains=search) |
                Q(item__name__icontains=search) |
                Q(supplier__name__icontains=search)
            )
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        
        return queryset

class IncomingCreateView(GudangRequiredMixin, CreateView):
    """Create new incoming transaction"""
    model = IncomingTransaction
    form_class = IncomingTransactionForm
    template_name = 'inventory/incoming_form.html'
    success_url = reverse_lazy('incoming_list')
    
    def form_valid(self, form):
        # Set received_by to current user
        user_id = self.request.session.get('user_id')
        if user_id:
            form.instance.received_by_id = user_id
        
        messages.success(
            self.request,
            f'Transaksi barang masuk {form.instance.item.name} berhasil ditambahkan.'
        )
        return super().form_valid(form)

class IncomingDetailView(GudangRequiredMixin, DetailView):
    """View incoming transaction details"""
    model = IncomingTransaction
    template_name = 'inventory/incoming_detail.html'
    context_object_name = 'transaction'
    pk_url_kwarg = 'incoming_id'


class IncomingUpdateView(GudangRequiredMixin, UpdateView):
    """Update existing incoming transaction"""
    model = IncomingTransaction
    form_class = IncomingTransactionForm
    template_name = 'inventory/incoming_form.html'
    success_url = reverse_lazy('incoming_list')
    pk_url_kwarg = 'incoming_id'
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Transaksi barang masuk berhasil diperbarui.'
        )
        return super().form_valid(form)

class OutgoingListView(GudangRequiredMixin, ListView):
    """List all outgoing transactions"""
    model = OutgoingTransaction
    template_name = 'inventory/outgoing_list.html'
    context_object_name = 'transactions'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if search:
            queryset = queryset.filter(
                Q(transaction_number__icontains=search) |
                Q(item__name__icontains=search) |
                Q(purpose__icontains=search)
            )
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        
        return queryset

class OutgoingCreateView(GudangRequiredMixin, CreateView):
    """Create new outgoing transaction"""
    model = OutgoingTransaction
    form_class = OutgoingTransactionForm
    template_name = 'inventory/outgoing_form.html'
    success_url = reverse_lazy('outgoing_list')
    
    def form_valid(self, form):
        # Set released_by to current user
        user_id = self.request.session.get('user_id')
        if user_id:
            form.instance.released_by_id = user_id
        
        messages.success(
            self.request,
            f'Transaksi barang keluar {form.instance.item.name} berhasil ditambahkan.'
        )
        return super().form_valid(form)

class OutgoingDetailView(GudangRequiredMixin, DetailView):
    """View outgoing transaction details"""
    model = OutgoingTransaction
    template_name = 'inventory/outgoing_detail.html'
    context_object_name = 'transaction'
    pk_url_kwarg = 'outgoing_id'

class OutgoingUpdateView(GudangRequiredMixin, UpdateView):
    """Update existing outgoing transaction"""
    model = OutgoingTransaction
    form_class = OutgoingTransactionForm
    template_name = 'inventory/outgoing_form.html'
    success_url = reverse_lazy('outgoing_list')
    pk_url_kwarg = 'outgoing_id'
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Transaksi barang keluar berhasil diperbarui.'
        )
        return super().form_valid(form)
