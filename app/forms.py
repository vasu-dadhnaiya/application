import re
from django import forms
from django.contrib.auth.models import User
from django.core.validators import EmailValidator, validate_email
from django.core.exceptions import ValidationError
from .models import UserProfile

class UserRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Username'})
    )
    full_name = forms.CharField(
        max_length=150,
        required=True,
        label="User Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Full User Name'})
    )
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    contact_number = forms.CharField(
        max_length=15,
        required=True,
        label="Contact Number",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 9876543210'})
    )
    age = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=120,
        label="Age",
        error_messages={
            'min_value': 'Age must be between 1 and 120.',
            'max_value': 'Age must be between 1 and 120.',
        },
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Age'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'})
    )
    confirm_password = forms.CharField(
        required=True,
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError("Username is required.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise ValidationError("Email address is required.")
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Please enter a valid email address.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email address already exists.")
        return email

    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number', '').strip()
        if not contact_number:
            raise ValidationError("Contact number is required.")
        # Allow numbers, spaces, leading +, hyphens (between 7 to 15 digits)
        digits = re.sub(r'\D', '', contact_number)
        if len(digits) < 7 or len(digits) > 15:
            raise ValidationError("Contact number must contain between 7 and 15 digits.")
        if UserProfile.objects.filter(contact_number=contact_number).exists():
            raise ValidationError("This contact number is already registered.")
        return contact_number

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is None:
            raise ValidationError("Age is required.")
        if age < 1 or age > 120:
            raise ValidationError("Age must be between 1 and 120.")
        return age

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        full_name = self.cleaned_data['full_name']
        contact_number = self.cleaned_data['contact_number']
        age = self.cleaned_data['age']

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name
        )
        profile = UserProfile.objects.create(
            user=user,
            full_name=full_name,
            contact_number=contact_number,
            age=age
        )
        return user, profile


class UserLoginForm(forms.Form):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Username'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'})
    )


class UserProfileEditForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        label="User Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
    )
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    contact_number = forms.CharField(
        max_length=15,
        required=True,
        label="Contact Number",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Number'})
    )
    age = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=120,
        label="Age",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise ValidationError("Email address is required.")
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Please enter a valid email address.")
        
        existing_users = User.objects.filter(email__iexact=email)
        if self.user:
            existing_users = existing_users.exclude(pk=self.user.pk)
        if existing_users.exists():
            raise ValidationError("This email is already in use by another account.")
        return email

    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number', '').strip()
        if not contact_number:
            raise ValidationError("Contact number is required.")
        digits = re.sub(r'\D', '', contact_number)
        if len(digits) < 7 or len(digits) > 15:
            raise ValidationError("Contact number must contain between 7 and 15 digits.")
        
        existing_profiles = UserProfile.objects.filter(contact_number=contact_number)
        if self.user and hasattr(self.user, 'profile'):
            existing_profiles = existing_profiles.exclude(pk=self.user.profile.pk)
        if existing_profiles.exists():
            raise ValidationError("This contact number is already registered to another user.")
        return contact_number

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is None:
            raise ValidationError("Age is required.")
        if age < 1 or age > 120:
            raise ValidationError("Age must be between 1 and 120.")
        return age

    def save(self, user):
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['full_name']
        user.save()

        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.full_name = self.cleaned_data['full_name']
        profile.contact_number = self.cleaned_data['contact_number']
        profile.age = self.cleaned_data['age']
        profile.save()
        return profile
