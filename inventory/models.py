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