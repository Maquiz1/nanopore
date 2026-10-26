from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy, reverse
from django.utils.html import format_html
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm
from phonenumber_field.formfields import PhoneNumberField
from users.models import Profile, Prefix, Position, Site, Zone
from django.contrib.auth.models import Group
from phonenumbers import parse, is_valid_number, NumberParseException
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import re

User = get_user_model()

# users/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import Profile, Prefix, Position

User = get_user_model()

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['sites', 'phone_number', 'prefix', 'position']
        widgets = {
            'sites': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'prefix': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CustomLoginForm(AuthenticationForm):
    """Log in with username or email (users/backends.py)."""
    username = forms.CharField(
        label="Username or email",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or email',
            'autocomplete': 'username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        })
    )
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': "Wrong username/email or password.",
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                # Tell the person their account is not active only once the password is right
                inactive = self._inactive_account(username)
                if inactive is not None and inactive.check_password(password):
                    raise forms.ValidationError(
                        format_html('Your account is not activated yet. Use the link in your activation email, '
                                    'or <a href="{}">send a new one</a>.', reverse('users:resend_activation')),
                        code='inactive',
                    )
                raise self.get_invalid_login_error()
        return self.cleaned_data

    @staticmethod
    def _inactive_account(username):
        username = username.strip()
        user = User.objects.filter(username=username, is_active=False).first()
        if user is None and "@" in username:
            matches = list(User.objects.filter(email__iexact=username)[:2])
            user = matches[0] if len(matches) == 1 and not matches[0].is_active else None
        return user

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

class ResendActivationEmailForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
    
class CustomPasswordResetForm(PasswordResetForm):
    """Forgot password: the link uses the Site URL from Administration, and the email is logged."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'you@example.com', 'autocomplete': 'email', 'autofocus': True,
        })

    def save(self, domain_override=None, use_https=False, **kwargs):
        from urllib.parse import urlsplit
        from notifications.mail import site_url
        url = urlsplit(site_url())
        return super().save(domain_override=url.netloc, use_https=url.scheme == "https", **kwargs)

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email,
                  html_email_template_name=None):
        from django.template.loader import render_to_string
        from notifications.mail import send_email
        # send_email renders <template>.txt and .html; context carries protocol/domain/uid/token
        subject = "".join(render_to_string(subject_template_name, context).splitlines())
        send_email(to_email, subject, "registration/password_reset_email", context, "password_reset")
        

class PhoneVerificationForm(forms.Form):
    phone_number = PhoneNumberField(region="TZ")  # or your default region code
    
    
    
class StaffForm(forms.Form):
    # User fields
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Username",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(
        required=False,
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label="First Name",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    middle_name = forms.CharField(
        max_length=150,
        required=False,
        label="Middle Name",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Last Name",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    
    is_active = forms.BooleanField(
        required=False,
        label="Is Active",
        initial=True,
        widget=forms.CheckboxInput()
    )
        
    is_staff = forms.BooleanField(
        required=False,
        label="Is Staff",
        initial=False,
        widget=forms.CheckboxInput()
    )
    
    

    # Profile fields
    prefix = forms.ModelChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        label="Prefix",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        required=False,
        label="Position",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    sites = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label="Sites",
        widget=forms.CheckboxSelectMultiple()
    )
    zones = forms.ModelMultipleChoiceField(
        queryset=Zone.objects.all(),
        required=False,
        label="Zones",
        widget=forms.CheckboxSelectMultiple()
    )
    phone_number = forms.CharField(
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    description = forms.CharField(
        required=False,
        label="Description",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )
    
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if " " in username:
            raise forms.ValidationError("Username cannot contain spaces.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            qs = User.objects.filter(email__iexact=email)
            # Exclude current user if updating
            if getattr(self, "instance", None):
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("This email address is already registered.")
        return email
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number")
        if phone:
            try:
                number = parse(phone, "TZ")  # Tanzania region, change as needed
                if not is_valid_number(number):
                    raise forms.ValidationError("Enter a valid Tanzanian phone number.")
            except NumberParseException:
                raise forms.ValidationError("Enter a valid phone number.")
        return phone
    
    # def clean_phone_number(self):
    #     phone = self.cleaned_data.get('phone_number')

    #     # Validate format (Tanzanian format example)
    #     if phone:
    #         if not re.match(r'^(?:\+255|0)[67]\d{8}$', phone):
    #             raise ValidationError("Enter a valid Tanzanian phone number (e.g., 0652821433 or +255652821433).")

    #         # Check uniqueness
    #         if User.objects.filter(phone_number=phone).exclude(pk=self.instance.pk).exists():
    #             raise ValidationError("This phone number is already registered.")

    #     return phone