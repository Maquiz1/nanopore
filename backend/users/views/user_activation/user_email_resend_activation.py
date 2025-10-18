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

        
class ResendActivationEmailView(FormView):
    template_name = 'registration/resend_activation_email.html'
    form_class = ResendActivationEmailForm
    success_url = reverse_lazy('users:login')  # or your own URL

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                self.send_confirmation_email(user)
                messages.success(self.request, 'A new activation email has been sent.')
            else:
                messages.info(self.request, 'This account is already active.')
        except User.DoesNotExist:
            messages.error(self.request, 'No account found with that email.')

        return super().form_valid(form)

    def send_confirmation_email(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_url = self.request.build_absolute_uri(
            reverse('users:activate_account', kwargs={'uidb64': uid, 'token': token})
        )

        # ✅ Print the activation URL to your console
        print("Activation URL:", activation_url)
    
        context = {
            'username': user.username,
            'activation_url': activation_url,
        }

        subject = 'Confirm your Email Address'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email

        text_content = render_to_string('emails/activation_email.txt', context)
        html_content = render_to_string('emails/activation_email.html', context)

        email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        email.attach_alternative(html_content, "text/html")
        email.send()
      