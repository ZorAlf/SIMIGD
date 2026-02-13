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
        # Hash password if it's not already hashed
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
