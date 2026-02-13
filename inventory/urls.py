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


