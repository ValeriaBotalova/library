from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from core.models import Reader
from django.utils import timezone
import re

class ReaderRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Reader
        fields = ['full_name', 'birth_date', 'address', 'phone', 'email', 'password']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Reader.objects.filter(email=email).exists():
            raise ValidationError("Этот email уже зарегистрирован")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if not re.match(r'^\+?[0-9]{10,15}$', phone):
                raise ValidationError("Введите корректный номер телефона")
            if Reader.objects.filter(phone=phone).exists():
                raise ValidationError("Этот телефон уже зарегистрирован")
        return phone

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            age = (timezone.now().date() - birth_date).days // 365
            if age < 12:
                raise ValidationError("Регистрация возможна только с 12 лет")
        return birth_date

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Пароли не совпадают")
        return cleaned_data

    def save(self, commit=True):
        reader = super().save(commit=False)
        password = self.cleaned_data.get('password')
        reader.set_password(password)  # хеширование пароля
        if commit:
            reader.save()
        return reader
    
class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={
        'autofocus': True,
        'class': 'form-control',
        'placeholder': 'Введите ваш email'
    }))
    
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Введите ваш пароль'
    }))
    
    error_messages = {
        'invalid_login': "Неверный email или пароль",
        'inactive': "Этот аккаунт неактивен",
    }
    
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )
        

