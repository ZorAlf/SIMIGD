from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field, HTML, Row, Column
from crispy_forms.bootstrap import FormActions
from .models import User, Category, Supplier, Items, IncomingTransaction, OutgoingTransaction, RequestItems

class UserForm(forms.ModelForm):
    """Form for creating and updating user accounts"""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Minimal 8 karakter',
        min_length=8,
        required=True
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Konfirmasi Password',
        required=True
    )

    class Meta:
        model = User
        fields = ['name', 'username', 'password', 'role', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Field('name', css_class='mb-3'),
                Field('username', css_class='mb-3'),
                Field('password', css_class='mb-3'),
                Field('confirm_password', css_class='mb-3'),
                Field('role', css_class='mb-3'),
                Field('is_active', css_class='form-check-input'),
                css_class='card-body'
            ),
            FormActions(
                Submit('submit', 'Simpan', css_class='btn btn-primary'),
                HTML('<a href="{% url \'user_list\' %}" class="btn btn-secondary">Batal</a>'),
            )
        )
        
        # Make password optional when updating
        if self.instance and self.instance.pk:
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
            self.fields['password'].help_text = 'Kosongkan jika tidak ingin mengubah password'

    def clean_username(self):
        """Validate that username is unique"""
        username = self.cleaned_data.get('username')
        
        # Check if username already exists (excluding current instance when updating)
        if self.instance and self.instance.pk:
            if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
                raise forms.ValidationError('Username sudah digunakan. Pilih username lain.')
        else:
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError('Username sudah digunakan. Pilih username lain.')
        
        return username

    def clean(self):
        """Validate that passwords match"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Only validate if password is provided
        if password or confirm_password:
            if password != confirm_password:
                raise forms.ValidationError('Password dan konfirmasi password tidak sama.')
        
        # If updating and no password provided, remove password fields
        if self.instance and self.instance.pk and not password:
            cleaned_data.pop('password', None)
            cleaned_data.pop('confirm_password', None)

        return cleaned_data

    def save(self, commit=True):
        """Save the user with hashed password"""
        user = super().save(commit=False)
        
        # Only set password if it was provided
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating user information without password"""
    
    class Meta:
        model = User
        fields = ['name', 'username', 'role', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Field('name', css_class='mb-3'),
                Field('username', css_class='mb-3'),
                Field('role', css_class='mb-3'),
                Field('is_active', css_class='form-check-input'),
                css_class='card-body'
            ),
            FormActions(
                Submit('submit', 'Update', css_class='btn btn-primary'),
                HTML('<a href="{% url \'user_list\' %}" class="btn btn-secondary">Batal</a>'),
            )
        )

    def clean_username(self):
        """Validate that username is unique"""
        username = self.cleaned_data.get('username')
        
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise forms.ValidationError('Username sudah digunakan. Pilih username lain.')
        
        return username


class ResetPasswordForm(forms.Form):
    """Form for resetting user password by admin"""
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Password Baru',
        help_text='Minimal 8 karakter',
        min_length=8,
        required=True
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Konfirmasi Password Baru',
        required=True
    )
    
    require_reset = forms.BooleanField(
        required=False,
        initial=True,
        label='Wajib ganti password saat login pertama',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Field('new_password', css_class='mb-3'),
                Field('confirm_password', css_class='mb-3'),
                Field('require_reset', css_class='form-check-input mb-3'),
                css_class='card-body'
            ),
            FormActions(
                Submit('submit', 'Reset Password', css_class='btn btn-primary'),
                HTML('<a href="{% url \'user_list\' %}" class="btn btn-secondary">Batal</a>'),
            )
        )

    def clean(self):
        """Validate that passwords match"""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError('Password dan konfirmasi password tidak sama.')

        return cleaned_data
    
class CategoryForm(forms.ModelForm):
    """Form untuk kategori barang"""
    
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Kategori'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Deskripsi kategori (opsional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name', css_class='mb-3'),
            Field('description', css_class='mb-3'),
            FormActions(
                Submit('submit', 'Simpan', css_class='btn btn-primary'),
                HTML('<a href="{% url \'category_list\' %}" class="btn btn-secondary">Batal</a>'),
            )
        )

class SupplierForm(forms.ModelForm):
    """Form untuk data supplier"""
    class Meta:
        model = Supplier
        fields = ['code', 'name', 'contact_person', 'phone', 'email', 'address', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Supplier'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Contact Person'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08123456789'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@supplier.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Alamat lengkap supplier'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column(Field('code', css_class='mb-3'), css_class='col-md-6'),
                Column(Field('name', css_class='mb-3'), css_class='col-md-6'),
            ),
            Row(
                Column(Field('contact_person', css_class='mb-3'), css_class='col-md-6'),
                Column(Field('phone', css_class='mb-3'), css_class='col-md-6'),
            ),
            Field('email', css_class='mb-3'),
            Field('address', css_class='mb-3'),
            Field('is_active', css_class='form-check-input mb-3'),
            FormActions(
                Submit('submit', 'Simpan', css_class='btn btn-primary'),
                HTML('<a href="/suppliers/" class="btn btn-secondary">Batal</a>'),
            )
        )
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        if name and not self.instance.pk:
            from .models import Supplier
            import re
            # Generate code: ambil 3 huruf pertama tiap kata, uppercase, join pakai '-', tambah angka jika sudah ada
            words = re.findall(r'\w+', name)
            base_code = '-'.join([w[:3].upper() for w in words if w])
            code = base_code
            counter = 1
            while Supplier.objects.filter(code=code).exists():
                code = f"{base_code}-{counter}"
                counter += 1
            cleaned_data['code'] = code
            self.data = self.data.copy()
            self.data['code'] = code
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column(Field('code', css_class='mb-3'), css_class='col-md-6'),
                Column(Field('name', css_class='mb-3'), css_class='col-md-6'),
            ),
            Row(
                Column(Field('contact_person', css_class='mb-3'), css_class='col-md-6'),
                Column(Field('phone', css_class='mb-3'), css_class='col-md-6'),
            ),
            Field('email', css_class='mb-3'),
            Field('address', css_class='mb-3'),
            Field('is_active', css_class='form-check-input mb-3'),
            FormActions(
                Submit('submit', 'Simpan', css_class='btn btn-primary'),
                HTML('<a href="{% url \'supplier_list\' %}" class="btn btn-secondary">Batal</a>'),
            )
        )

class ItemForm(forms.ModelForm):
    """Form untuk master barang"""
    class Meta:
        model = Items
        fields = ['code', 'name', 'category', 'unit', 'minimum_stock', 'description', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BRG001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Barang'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '10', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Deskripsi barang (opsional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column(Field('code', css_class='mb-3'), css_class='col-md-6'),
                Column(Field('name', css_class='mb-3'), css_class='col-md-6'),
            ),
            Row(
                Column(Field('category', css_class='mb-3'), css_class='col-md-4'),
                Column(Field('unit', css_class='mb-3'), css_class='col-md-4'),
                Column(Field('minimum_stock', css_class='mb-3'), css_class='col-md-4'),
            ),
            Field('description', css_class='mb-3'),
            Field('is_active', css_class='form-check-input mb-3'),
            FormActions(
                Submit('submit', 'Simpan', css_class='btn btn-primary'),
                HTML('<a href="{% url \'item_list\' %}" class="btn btn-secondary">Batal</a>'),
            )
        )

class IncomingTransactionForm(forms.ModelForm):
    """Form untuk transaksi barang masuk"""
    
    transaction_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Tanggal Transaksi'
    )
    
    class Meta:
        model = IncomingTransaction
        fields = ['item', 'supplier', 'quantity', 'transaction_date', 'status', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Jumlah', 'min': '1'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Catatan (opsional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column(Field('item', css_class='mb-3'), css_class='col-md-6'),
                Column(Field('supplier', css_class='mb-3'), css_class='col-md-6'),
            ),
            Row(
                Column(Field('quantity', css_class='mb-3'), css_class='col-md-4'),
                Column(Field('transaction_date', css_class='mb-3'), css_class='col-md-4'),
                Column(Field('status', css_class='mb-3'), css_class='col-md-4'),
            ),
            Field('notes', css_class='mb-3'),
            FormActions(
                Submit('submit', 'Simpan', css_class='btn btn-primary'),
                HTML('<a href="{% url \'incoming_list\' %}" class="btn btn-secondary">Batal</a>'),
            )
        )

class OutgoingTransactionForm(forms.ModelForm):
    """Form untuk transaksi barang keluar"""
    
    transaction_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Tanggal Transaksi'
    )
    class Meta:
        model = OutgoingTransaction
        fields = ['item', 'quantity', 'transaction_date', 'purpose', 'status', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Jumlah', 'min': '1'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tujuan/Keperluan'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Catatan (opsional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('item', css_class='mb-3'),
            Row(
                Column(Field('quantity', css_class='mb-3'), css_class='col-md-4'),
                Column(Field('transaction_date', css_class='mb-3'), css_class='col-md-4'),
                Column(Field('status', css_class='mb-3'), css_class='col-md-4'),
            ),
            Field('purpose', css_class='mb-3'),
            Field('notes', css_class='mb-3'),
            FormActions(
                Submit('submit', 'Simpan', css_class='btn btn-primary'),
                HTML('<a href="{% url \'outgoing_list\' %}" class="btn btn-secondary">Batal</a>'),
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        quantity = cleaned_data.get('quantity')
        status = cleaned_data.get('status')
        
        # Validate stock if status is released
        if item and quantity and status == 'released':
            if item.current_stock < quantity:
                raise forms.ValidationError(
                    f'Stok tidak mencukupi! Stok saat ini: {item.current_stock} {item.unit}'
                )
        
        return cleaned_data

