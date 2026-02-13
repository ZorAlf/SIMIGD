from django.urls import path
from .views import (
    DashboardView,
    UserListView,
    UserCreateView,
    UserUpdateView,
    UserDeleteView,
    UserResetPasswordView,
    UserDetailView,
    UserToggleActiveView,
    UserLoginView,
    UserLogoutView,
)

from .inventory_views import (
    # Category views
    CategoryListView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDeleteView,

# Supplier views
    SupplierListView,
    SupplierCreateView,
    SupplierUpdateView,
    SupplierDetailView,
    SupplierDeleteView,
    
    # Items views
    ItemListView,
    ItemCreateView,
    ItemUpdateView,
    ItemDetailView,
    ItemDeleteView,
    
    # Incoming transaction views
    IncomingListView,
    IncomingCreateView,
    IncomingDetailView,
    IncomingUpdateView,
    
    # Outgoing transaction views
    OutgoingListView,
    OutgoingCreateView,
    OutgoingDetailView,
    OutgoingUpdateView,
)

from .production_views import (
    RequestItemListView,
    RequestItemCreateView,
    RequestItemDetailView,
    RequestItemApproveView,
    ProduksiDashboardView,
)

from .directur_views import (
    DirekturDashboardView,
    LaporanListView,
    HistoriAktivitasView,
    ExportPDFBarangMasukView,
    ExportPDFBarangKeluarView,
)

urlpatterns = [
    # Authentication URLs
    path('', UserLoginView.as_view(), name='user_login'),
    path('login/', UserLoginView.as_view(), name='login'),  # Alternative URL
    path('logout/', UserLogoutView.as_view(), name='user_logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # User Management URLs
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user_detail'),
    path('users/<int:user_id>/edit/', UserUpdateView.as_view(), name='user_update'),
    path('users/<int:user_id>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('users/<int:user_id>/reset-password/', UserResetPasswordView.as_view(), name='user_reset_password'),
    path('users/<int:user_id>/toggle-active/', UserToggleActiveView.as_view(), name='user_toggle_active'),
    
    # Category URLs
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:category_id>/edit/', CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:category_id>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
    
    # Supplier URLs
    path('suppliers/', SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:supplier_id>/', SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:supplier_id>/edit/', SupplierUpdateView.as_view(), name='supplier_update'),
    path('suppliers/<int:supplier_id>/delete/', SupplierDeleteView.as_view(), name='supplier_delete'),
    
    # Items (Barang Master) URLs
    path('items/', ItemListView.as_view(), name='item_list'),
    path('items/create/', ItemCreateView.as_view(), name='item_create'),
    path('items/<int:item_id>/', ItemDetailView.as_view(), name='item_detail'),
    path('items/<int:item_id>/edit/', ItemUpdateView.as_view(), name='item_update'),
    path('items/<int:item_id>/delete/', ItemDeleteView.as_view(), name='item_delete'),
    
    # Incoming Transaction URLs
    path('incoming/', IncomingListView.as_view(), name='incoming_list'),
    path('incoming/create/', IncomingCreateView.as_view(), name='incoming_create'),
    path('incoming/<int:incoming_id>/', IncomingDetailView.as_view(), name='incoming_detail'),
    path('incoming/<int:incoming_id>/edit/', IncomingUpdateView.as_view(), name='incoming_update'),
    
    # Outgoing Transaction URLs
    path('outgoing/', OutgoingListView.as_view(), name='outgoing_list'),
    path('outgoing/create/', OutgoingCreateView.as_view(), name='outgoing_create'),
    path('outgoing/<int:outgoing_id>/', OutgoingDetailView.as_view(), name='outgoing_detail'),
    path('outgoing/<int:outgoing_id>/edit/', OutgoingUpdateView.as_view(), name='outgoing_update'),
    
    # Request Items URLs (Pegawai Produksi)
    path('produksi/dashboard/', ProduksiDashboardView.as_view(), name='produksi_dashboard'),
    path('requests/', RequestItemListView.as_view(), name='request_list'),
    path('requests/create/', RequestItemCreateView.as_view(), name='request_create'),
    path('requests/<int:request_id>/', RequestItemDetailView.as_view(), name='request_detail'),
    path('requests/<int:request_id>/approve/', RequestItemApproveView.as_view(), name='request_approve'),
    
    # Direktur URLs (Read Only Reports & Dashboard)
    path('direktur/dashboard/', DirekturDashboardView.as_view(), name='direktur_dashboard'),
    path('direktur/laporan/', LaporanListView.as_view(), name='direktur_laporan'),
    path('direktur/histori/', HistoriAktivitasView.as_view(), name='direktur_histori'),
    
    # Direktur PDF Export URLs
    path('direktur/export-pdf/barang-masuk/', ExportPDFBarangMasukView.as_view(), name='export_pdf_barang_masuk'),
    path('direktur/export-pdf/barang-keluar/', ExportPDFBarangKeluarView.as_view(), name='export_pdf_barang_keluar'),
]

