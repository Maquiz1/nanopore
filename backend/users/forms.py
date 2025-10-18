from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy, reverse
from django.utils.html import format_html
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm
from phonenumber_field.formfields import PhoneNumberField
from users.models import Profile, Prefix, Position, Site

User = get_user_model()

# users/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import Profile, Prefix, Position

User = get_user_model()

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['site', 'phone_number', 'prefix', 'position']
        widgets = {
            'site': forms.Select(attrs={'class': 'form-select'}),
            'prefix': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            UserModel = get_user_model()
            try:
                user = UserModel.objects.get(username=username)

                if not user.is_active:
                    resend_url = reverse_lazy('users:resend_activation')
                    raise forms.ValidationError(
                        format_html(
                            'Your account is inactive. <a href="{}">Resend activation email</a>',
                            resend_url
                        ),
                        code='inactive'
                    )

                # Only authenticate if user is active
                user = authenticate(self.request, username=username, password=password)
                if user is None:
                    raise forms.ValidationError(
                        "Invalid username or password.",
                        code='invalid_login'
                    )

                # ✅ Required: Store the user in self.user_cache (what AuthenticationForm expects)
                self.user_cache = user

            except UserModel.DoesNotExist:
                raise forms.ValidationError(
                    "Invalid username or password.",
                    code='invalid_login'
                )

        return self.cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)
    
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        

class PhoneVerificationForm(forms.Form):
    phone_number = PhoneNumberField(region="TZ")  # or your default region code
    
    
    
class StaffForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=False)  # required on creation
    first_name = forms.CharField(max_length=50, required=False)
    middle_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=False)
    prefix = forms.ModelChoiceField(queryset=Prefix.objects.all(), required=False, empty_label="-- Select Prefix --")
    position = forms.ModelChoiceField(queryset=Position.objects.all(), required=False, empty_label="-- Select Position --")
    site = forms.ModelChoiceField(queryset=Site.objects.all(), required=False, empty_label="-- Select Site --")
    phone_number = forms.CharField(max_length=20, required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={"rows":2}), required=False)
    is_staff = forms.BooleanField(initial=True, required=False)
