from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.
class User(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('pegawai_gudang', 'Pegawai Gudang'),
        ('pegawai_produksi', 'Pegawai Produksi'),
        ('direktur', 'Direktur'),
    ]

    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name='Nama Lengkap')
    username = models.CharField(max_length=100, unique=True, verbose_name='Username')
    password = models.CharField(max_length=255, verbose_name='Password')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='pegawai_gudang', verbose_name='Role')
    reset_password = models.BooleanField(default=False, verbose_name='Reset Password Required')
    is_active = models.BooleanField(default=True, verbose_name='Active Status')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, verbose_name='Nama Kategori')
    description = models.TextField(blank=True, null=True, verbose_name='Deskripsi')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name
class Supplier(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True, verbose_name='Kode Supplier')
    name = models.CharField(max_length=200, verbose_name='Nama Supplier')
    contact_person = models.CharField(max_length=100, blank=True, null=True, verbose_name='Kontak Person')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telepon')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    address = models.TextField(blank=True, null=True, verbose_name='Alamat')
    is_active = models.BooleanField(default=True, verbose_name='Status Aktif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.name}"
    
class Items(models.Model):
    """Model untuk master barang"""
    UNIT_CHOICES = [
        ('pcs', 'Pcs (Pieces)'),
        ('box', 'Box'),
        ('kg', 'Kilogram'),
        ('liter', 'Liter'),
        ('meter', 'Meter'),
        ('unit', 'Unit'),
    ]

    items_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=100, unique=True, verbose_name='Kode Barang')
    name = models.CharField(max_length=200, verbose_name='Nama Barang')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Kategori')
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='pcs', verbose_name='Satuan')
    minimum_stock = models.IntegerField(default=0, verbose_name='Stok Minimum')
    current_stock = models.IntegerField(default=0, verbose_name='Stok Saat Ini')
    description = models.TextField(blank=True, null=True, verbose_name='Deskripsi')
    is_active = models.BooleanField(default=True, verbose_name='Status Aktif')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_items', verbose_name='Dibuat Oleh')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_items', verbose_name='Diupdate Oleh')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def stock_status(self):
        """Return stock status"""
        if self.current_stock <= 0:
            return 'out_of_stock'
        elif self.current_stock <= self.minimum_stock:
            return 'low_stock'
        return 'in_stock'
    
    @property
    def stock_status_display(self):
        """Return human-readable stock status"""
        status_map = {
            'in_stock': 'In Stock',
            'low_stock': 'Low Stock',
            'out_of_stock': 'Out of Stock'
        }
        return status_map.get(self.stock_status, 'Unknown')
    
    @property
    def stock_status_badge(self):
        """Return Bootstrap badge class for stock status"""
        badge_map = {
            'in_stock': 'bg-success',
            'low_stock': 'bg-warning text-dark',
            'out_of_stock': 'bg-danger'
        }
        return badge_map.get(self.stock_status, 'bg-secondary')
    
    @property
    def stock_status_icon(self):
        """Return Bootstrap icon for stock status"""
        icon_map = {
            'in_stock': 'bi-check-circle-fill',
            'low_stock': 'bi-exclamation-triangle-fill',
            'out_of_stock': 'bi-x-circle-fill'
        }
        return icon_map.get(self.stock_status, 'bi-question-circle')
    
    def get_stock_percentage(self):
        """Return stock percentage relative to minimum stock"""
        if self.minimum_stock == 0:
            return 100 if self.current_stock > 0 else 0
        return (self.current_stock / self.minimum_stock) * 100
    
class IncomingTransaction(models.Model):
    """Model untuk transaksi barang masuk"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('received', 'Diterima'),
        ('cancelled', 'Dibatalkan'),
    ]

    incoming_id = models.AutoField(primary_key=True)
    transaction_number = models.CharField(max_length=50, unique=True, verbose_name='Nomor Transaksi')
    item = models.ForeignKey(Items, on_delete=models.CASCADE, verbose_name='Barang')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, verbose_name='Supplier')
    quantity = models.IntegerField(verbose_name='Jumlah')
    transaction_date = models.DateField(verbose_name='Tanggal Transaksi')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received', verbose_name='Status')
    notes = models.TextField(blank=True, null=True, verbose_name='Catatan')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='incoming_transactions', verbose_name='Diterima Oleh')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Incoming Transaction'
        verbose_name_plural = 'Incoming Transactions'
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.transaction_number} - {self.item.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        if not self.transaction_number:
            from datetime import datetime
            today = datetime.now().strftime('%Y%m%d')
            last_transaction = IncomingTransaction.objects.filter(
                transaction_number__startswith=f'IN{today}'
            ).order_by('-transaction_number').first()
            
            if last_transaction:
                last_number = int(last_transaction.transaction_number[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.transaction_number = f'IN{today}{str(new_number).zfill(4)}'
        
        is_new = self.pk is None
        old_status = None
        old_quantity = 0
        
        if not is_new:
            old_transaction = IncomingTransaction.objects.get(pk=self.pk)
            old_status = old_transaction.status
            old_quantity = old_transaction.quantity
        
        super().save(*args, **kwargs)
        
        if self.status == 'received':
            if is_new:
                self.item.current_stock += self.quantity
                self.item.save()
            elif old_status != 'received':
                self.item.current_stock += self.quantity
                self.item.save()
            elif old_quantity != self.quantity:
                stock_difference = self.quantity - old_quantity
                self.item.current_stock += stock_difference
                self.item.save()
        elif old_status == 'received' and self.status != 'received':
            self.item.current_stock -= old_quantity
            self.item.save()

class OutgoingTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('released', 'Dikeluarkan'),
        ('cancelled', 'Dibatalkan'),
    ]

    outgoing_id = models.AutoField(primary_key=True)
    transaction_number = models.CharField(max_length=50, unique=True, verbose_name='Nomor Transaksi')
    request_item = models.OneToOneField(
        'RequestItems', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='outgoing_transaction',
        verbose_name='Permintaan Terkait'
    )
    item = models.ForeignKey(Items, on_delete=models.CASCADE, verbose_name='Barang')
    quantity = models.IntegerField(verbose_name='Jumlah')
    transaction_date = models.DateField(verbose_name='Tanggal Transaksi')
    purpose = models.CharField(max_length=200, verbose_name='Tujuan/Keperluan')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='released', verbose_name='Status')
    notes = models.TextField(blank=True, null=True, verbose_name='Catatan')
    released_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='outgoing_transactions', verbose_name='Dikeluarkan Oleh')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Outgoing Transaction'
        verbose_name_plural = 'Outgoing Transactions'
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.transaction_number} - {self.item.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        if not self.transaction_number:
            from datetime import datetime
            today = datetime.now().strftime('%Y%m%d')
            last_transaction = OutgoingTransaction.objects.filter(
                transaction_number__startswith=f'OUT{today}'
            ).order_by('-transaction_number').first()
            
            if last_transaction:
                last_number = int(last_transaction.transaction_number[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.transaction_number = f'OUT{today}{str(new_number).zfill(4)}'
        
        is_new = self.pk is None
        old_status = None
        old_quantity = 0
        
        if not is_new:
            old_transaction = OutgoingTransaction.objects.get(pk=self.pk)
            old_status = old_transaction.status
            old_quantity = old_transaction.quantity
        
        super().save(*args, **kwargs)
        
        if self.status == 'released':
            if is_new:
                self.item.current_stock -= self.quantity
                self.item.save()
            elif old_status != 'released':
                self.item.current_stock -= self.quantity
                self.item.save()
            elif old_quantity != self.quantity:
                stock_difference = old_quantity - self.quantity
                self.item.current_stock += stock_difference
                self.item.save()
        elif old_status == 'released' and self.status != 'released':
            self.item.current_stock += old_quantity
            self.item.save()

class RequestItems(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Disetujui'),
        ('rejected', 'Ditolak'),
        ('completed', 'Selesai'),
    ]

    request_id = models.AutoField(primary_key=True)
    request_number = models.CharField(max_length=50, unique=True, verbose_name='Nomor Permintaan')
    item = models.ForeignKey(Items, on_delete=models.CASCADE, verbose_name='Barang')
    quantity = models.IntegerField(verbose_name='Jumlah')
    request_date = models.DateField(verbose_name='Tanggal Permintaan')
    needed_date = models.DateField(verbose_name='Tanggal Dibutuhkan')
    purpose = models.CharField(max_length=200, verbose_name='Keperluan')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    notes = models.TextField(blank=True, null=True, verbose_name='Catatan')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_items', verbose_name='Diminta Oleh')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests', verbose_name='Disetujui Oleh')
    approved_date = models.DateTimeField(null=True, blank=True, verbose_name='Tanggal Disetujui')
    rejection_reason = models.TextField(blank=True, null=True, verbose_name='Alasan Penolakan')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Request Item'
        verbose_name_plural = 'Request Items'
        ordering = ['-request_date', '-created_at']

    def __str__(self):
        return f"{self.request_number} - {self.item.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        # Auto-generate request number if not exists
        if not self.request_number:
            from datetime import datetime
            today = datetime.now().strftime('%Y%m%d')
            last_request = RequestItems.objects.filter(
                request_number__startswith=f'REQ{today}'
            ).order_by('-request_number').first()
            
            if last_request:
                last_number = int(last_request.request_number[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.request_number = f'REQ{today}{str(new_number).zfill(4)}'
        
        super().save(*args, **kwargs)