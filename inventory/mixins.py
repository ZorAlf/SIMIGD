from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin


class AdminOnlyMixin(UserPassesTestMixin):    
    def test_func(self):
        user_id = self.request.session.get('user_id')
        if user_id:
            try:
                from .models import User
                user = User.objects.get(user_id=user_id)
                return user.role == 'admin' and user.is_active
            except User.DoesNotExist:
                return False
        return False
    
    def handle_no_permission(self):
        messages.error(
            self.request,
            'Anda tidak memiliki akses ke halaman ini. Hanya Admin yang diizinkan.'
        )
        return redirect('dashboard')


class GudangRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        # Check if user is logged in and has pegawai_gudang role
        user_id = self.request.session.get('user_id')
        if user_id:
            try:
                from .models import User
                user = User.objects.get(user_id=user_id)
                # ONLY pegawai_gudang - Admin EXCLUDED
                return user.role == 'pegawai_gudang' and user.is_active
            except User.DoesNotExist:
                return False
        return False
    
    def handle_no_permission(self):
        messages.error(
            self.request,
            'Anda tidak memiliki akses ke halaman ini. Hanya Pegawai Gudang yang diizinkan.'
        )
        return redirect('dashboard')


class ProduksiRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user_id = self.request.session.get('user_id')
        if user_id:
            try:
                from .models import User
                user = User.objects.get(user_id=user_id)
                # ONLY pegawai_produksi - Admin EXCLUDED
                return user.role == 'pegawai_produksi' and user.is_active
            except User.DoesNotExist:
                return False
        return False
    
    def handle_no_permission(self):
        messages.error(
            self.request,
            'Anda tidak memiliki akses ke halaman ini. Hanya Pegawai Produksi yang diizinkan.'
        )
        return redirect('dashboard')


class ProduksiOrGudangMixin(UserPassesTestMixin):
    """
    Mixin for views that can be accessed by both Produksi and Gudang roles
    Admin is EXCLUDED from operational tasks
    """
    
    def test_func(self):
        user_id = self.request.session.get('user_id')
        if user_id:
            try:
                from .models import User
                user = User.objects.get(user_id=user_id)
                # ONLY pegawai_produksi OR pegawai_gudang - Admin EXCLUDED
                return user.role in ['pegawai_produksi', 'pegawai_gudang'] and user.is_active
            except User.DoesNotExist:
                return False
        return False
    
    def handle_no_permission(self):
        messages.error(
            self.request,
            'Anda tidak memiliki akses ke halaman ini. Hanya Pegawai Produksi atau Pegawai Gudang yang diizinkan.'
        )
        return redirect('dashboard')


class DirekturRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure only Direktur can access the view
    Admin is EXCLUDED from operational reports
    """
    
    def test_func(self):
        user_id = self.request.session.get('user_id')
        if user_id:
            try:
                from .models import User
                user = User.objects.get(user_id=user_id)
                # ONLY direktur - Admin EXCLUDED
                return user.role == 'direktur' and user.is_active
            except User.DoesNotExist:
                return False
        return False
    
    def handle_no_permission(self):
        messages.error(
            self.request,
            'Anda tidak memiliki akses ke halaman ini. Hanya Direktur yang diizinkan.'
        )
        return redirect('dashboard')
