from django.contrib.auth import get_user_model
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy, reverse
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.views import View
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_decode
from django.http import HttpResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.views.generic import FormView
from django.contrib import messages
from users.forms import CustomLoginForm,CustomUserCreationForm,ResendActivationEmailForm,PhoneVerificationForm
from django.contrib.auth.views import LoginView
from django.utils.html import format_html
from django.contrib.auth import authenticate
import binascii
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView,DetailView
from django.views.generic.edit import UpdateView
from users.models import Profile
from users.forms import ProfileForm
from django.contrib.auth import logout
from users.sms_utils import send_verification_sms

User = get_user_model()

def force_logout(request):
    """Forcefully log out the current user and redirect to login page."""
    logout(request)
    return redirect('users:login')



class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True