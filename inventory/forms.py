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