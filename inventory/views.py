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
            
            return render(request, 'inventory/direktur/dashboard_direktur.html', context)
            
        except User.DoesNotExist:
            messages.error(request, 'User tidak ditemukan.')
            return redirect('user_login')