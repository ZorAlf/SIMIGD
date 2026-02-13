from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from .models import User, Items, IncomingTransaction, OutgoingTransaction, RequestItems
from .forms import UserForm, UserUpdateForm, ResetPasswordForm
from .mixins import AdminOnlyMixin as AdminRequiredMixin

# Create your views here.
class DashboardView(View):    
    def get(self, request):
        user_id = request.session.get('user_id')
        
        if not user_id:
            return redirect('user_login')
        
        try:
            user = User.objects.get(user_id=user_id)
            
            if not user.is_active:
                messages.error(request, 'Akun Anda tidak aktif. Silakan hubungi administrator.')
                return redirect('user_login')
            
            # Get current month range
            now = timezone.now()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Total Stok Barang
            items_aggregate = Items.objects.filter(is_active=True).aggregate(
                total_items=Count('items_id'),
                total_stock=Sum('current_stock')
            )
            
            # Get all active items for status categorization
            all_items = Items.objects.filter(is_active=True)
            
            # Categorize items by stock status
            in_stock_items = []
            low_stock_items = []
            out_of_stock_items = []
            
            for item in all_items:
                if item.stock_status == 'out_of_stock':
                    out_of_stock_items.append(item)
                elif item.stock_status == 'low_stock':
                    low_stock_items.append(item)
                else:  # in_stock
                    in_stock_items.append(item)
            
            # Sort and limit low stock items for display
            low_stock_items_display = sorted(low_stock_items, key=lambda x: x.current_stock)[:10]
            
            # Debug: Print stock counts
            print(f"DEBUG - Stock Status Counts:")
            print(f"  In Stock: {len(in_stock_items)}")
            print(f"  Low Stock: {len(low_stock_items)}")
            print(f"  Out of Stock: {len(out_of_stock_items)}")
            print(f"  Total Items: {len(all_items)}")
            
            # Barang Masuk (bulan ini)
            incoming_this_month = IncomingTransaction.objects.filter(
                transaction_date__gte=start_of_month
            ).aggregate(
                total_transactions=Count('incoming_id'),
                total_quantity=Sum('quantity')
            )
            
            # Barang Keluar (bulan ini)
            outgoing_this_month = OutgoingTransaction.objects.filter(
                transaction_date__gte=start_of_month
            ).aggregate(
                total_transactions=Count('outgoing_id'),
                total_quantity=Sum('quantity')
            )
            
            # Permintaan Produksi (statistics)
            request_stats = RequestItems.objects.aggregate(
                total_requests=Count('request_id'),
                pending_count=Count('request_id', filter=Q(status='pending')),
                approved_count=Count('request_id', filter=Q(status='approved')),
                rejected_count=Count('request_id', filter=Q(status='rejected')),
                completed_count=Count('request_id', filter=Q(status='completed'))
            )
            
            # Recent requests (last 10)
            recent_requests = RequestItems.objects.select_related(
                'item', 'requested_by', 'approved_by'
            ).order_by('-request_date')[:10]
            
            # Chart data - Transaksi 7 hari terakhir
            last_7_days = []
            incoming_7days = []
            outgoing_7days = []
            
            for i in range(6, -1, -1):
                day = now - timedelta(days=i)
                # Gunakan filter equality ke DateField + status agar tidak menghitung pending/cancelled
                target_date = day.date()
                last_7_days.append(day.strftime('%d/%m'))

                incoming_count = IncomingTransaction.objects.filter(
                    transaction_date=target_date,
                    status='received'
                ).aggregate(total=Sum('quantity'))['total'] or 0

                outgoing_count = OutgoingTransaction.objects.filter(
                    transaction_date=target_date,
                    status='released'
                ).aggregate(total=Sum('quantity'))['total'] or 0

                incoming_7days.append(incoming_count)
                outgoing_7days.append(outgoing_count)
            
            # Build context with all data
            context = {
                'user': user,
                'role_display': user.get_role_display(),
                
                # Summary cards
                'total_items': items_aggregate['total_items'] or 0,
                'total_stock': items_aggregate['total_stock'] or 0,
                
                # Stock status statistics
                'in_stock_count': len(in_stock_items),
                'low_stock_count': len(low_stock_items),
                'out_of_stock_count': len(out_of_stock_items),
                
                # Stock status items
                'in_stock_items': in_stock_items[:10],  # Top 10
                'low_stock_items': low_stock_items_display,
                'out_of_stock_items': out_of_stock_items[:10],  # Top 10
                
                # Transactions this month
                'incoming_transactions': incoming_this_month['total_transactions'] or 0,
                'incoming_quantity': incoming_this_month['total_quantity'] or 0,
                'outgoing_transactions': outgoing_this_month['total_transactions'] or 0,
                'outgoing_quantity': outgoing_this_month['total_quantity'] or 0,
                
                # Request statistics
                'total_requests': request_stats['total_requests'] or 0,
                'pending_requests': request_stats['pending_count'] or 0,
                'approved_requests': request_stats['approved_count'] or 0,
                'rejected_requests': request_stats['rejected_count'] or 0,
                'completed_requests': request_stats['completed_count'] or 0,
                
                # Lists
                'recent_requests': recent_requests,
                
                # Chart data
                'chart_labels': last_7_days,
                'chart_incoming': incoming_7days,
                'chart_outgoing': outgoing_7days,
            }
            
            # Debug: Print context data for chart
            print(f"DEBUG - Context Data:")
            print(f"  chart_labels: {context['chart_labels']}")
            print(f"  chart_incoming: {context['chart_incoming']}")
            print(f"  chart_outgoing: {context['chart_outgoing']}")
            print(f"  Stock counts in context: In={context['in_stock_count']}, Low={context['low_stock_count']}, Out={context['out_of_stock_count']}")
            
            return render(request, 'inventory/director/dashboard.html', context)
            
        except User.DoesNotExist:
            messages.error(request, 'User tidak ditemukan.')
            return redirect('user_login')
        
# User List View
class UserListView(AdminRequiredMixin, ListView):
    """Display list of all users"""
    model = User
    template_name = 'inventory/admin/user_list.html'
    context_object_name = 'users'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        role_filter = self.request.GET.get('role')
        status_filter = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                name__icontains=search
            ) | queryset.filter(
                username__icontains=search
            )
        
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        if status_filter:
            if status_filter == 'active':
                queryset = queryset.filter(is_active=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = User.ROLE_CHOICES
        context['search'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


# User Create View
class UserCreateView(AdminRequiredMixin, CreateView):
    """Create new user"""
    model = User
    form_class = UserForm
    template_name = 'inventory/admin/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'User {form.instance.username} berhasil ditambahkan.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Terjadi kesalahan. Silakan periksa form kembali.')
        return super().form_invalid(form)


# User Update View
class UserUpdateView(AdminRequiredMixin, UpdateView):
    """Update existing user"""
    model = User
    form_class = UserUpdateForm
    template_name = 'inventory/admin/user_form.html'
    success_url = reverse_lazy('user_list')
    pk_url_kwarg = 'user_id'
    
    def form_valid(self, form):
        messages.success(self.request, f'User {form.instance.username} berhasil diperbarui.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Terjadi kesalahan. Silakan periksa form kembali.')
        return super().form_invalid(form)


# User Delete View
class UserDeleteView(AdminRequiredMixin, DeleteView):
    """Delete user (soft delete by setting is_active to False)"""
    model = User
    template_name = 'inventory/admin/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    pk_url_kwarg = 'user_id'
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Prevent admin from deleting themselves
        current_user_id = request.session.get('user_id')
        if user.user_id == current_user_id:
            messages.error(request, 'Anda tidak dapat menghapus akun Anda sendiri.')
            return redirect('user_list')
        
        # Soft delete: set is_active to False instead of deleting
        user.is_active = False
        user.save()
        
        messages.success(request, f'User {user.username} berhasil dinonaktifkan.')
        return redirect(self.success_url)


# Reset Password View
class UserResetPasswordView(AdminRequiredMixin, View):
    """Reset user password"""
    template_name = 'inventory/admin/user_reset_password.html'
    
    def get(self, request, user_id):
        user = get_object_or_404(User, user_id=user_id)
        form = ResetPasswordForm()
        return render(request, self.template_name, {
            'form': form,
            'user': user
        })
    
    def post(self, request, user_id):
        user = get_object_or_404(User, user_id=user_id)
        form = ResetPasswordForm(request.POST)
        
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            require_reset = form.cleaned_data.get('require_reset', False)
            
            # Set new password
            user.set_password(new_password)
            user.reset_password = require_reset
            user.save()
            
            messages.success(request, f'Password untuk user {user.username} berhasil direset.')
            return redirect('user_list')
        else:
            messages.error(request, 'Terjadi kesalahan. Silakan periksa form kembali.')
        
        return render(request, self.template_name, {
            'form': form,
            'user': user
        })


# User Detail View
class UserDetailView(AdminRequiredMixin, View):
    """View user details"""
    template_name = 'inventory/admin/user_detail.html'
    
    def get(self, request, user_id):
        user = get_object_or_404(User, user_id=user_id)
        return render(request, self.template_name, {'user': user})


# Toggle User Active Status
class UserToggleActiveView(AdminRequiredMixin, View):
    """Toggle user active status"""
    
    def post(self, request, user_id):
        user = get_object_or_404(User, user_id=user_id)
        
        # Prevent admin from deactivating themselves
        current_user_id = request.session.get('user_id')
        if user.user_id == current_user_id:
            messages.error(request, 'Anda tidak dapat menonaktifkan akun Anda sendiri.')
            return redirect('user_list')
        
        # Toggle active status
        user.is_active = not user.is_active
        user.save()
        
        status = 'diaktifkan' if user.is_active else 'dinonaktifkan'
        messages.success(request, f'User {user.username} berhasil {status}.')
        
        return redirect('user_list')


# Login View
class UserLoginView(View):
    """User login view"""
    template_name = 'inventory/login.html'
    
    def get(self, request):
        # If already logged in, redirect to dashboard
        if request.session.get('user_id'):
            return redirect('dashboard')
        return render(request, self.template_name)
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Username dan password harus diisi.')
            return render(request, self.template_name)
        
        try:
            user = User.objects.get(username=username, is_active=True)
            
            # Check password
            if user.check_password(password):
                # Set session
                request.session['user_id'] = user.user_id
                request.session['username'] = user.username
                request.session['role'] = user.role
                request.session['name'] = user.name
                
                messages.success(request, f'Selamat datang, {user.name}!')
                
                # Redirect to dashboard
                return redirect('dashboard')
            else:
                messages.error(request, 'Username atau password salah.')
        except User.DoesNotExist:
            messages.error(request, 'Username atau password salah.')
        
        return render(request, self.template_name)


# Logout View
class UserLogoutView(View):
    """User logout view"""
    
    def get(self, request):
        # Clear session
        request.session.flush()
        messages.success(request, 'Anda telah berhasil logout.')
        return redirect('user_login')

