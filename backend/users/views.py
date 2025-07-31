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
from .forms import CustomLoginForm,CustomUserCreationForm,ResendActivationEmailForm
from django.contrib.auth.views import LoginView
from django.utils.html import format_html
from django.contrib.auth import authenticate
import binascii

User = get_user_model()


class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    
class SignUpView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'registration/sign_up.html'
    success_url = reverse_lazy('users:email_confirmation_sent')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False  # Deactivate account until confirmed
        user.save()

        self.send_confirmation_email(user)
        return super().form_valid(form)

    def send_confirmation_email(self, user):
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth.tokens import default_token_generator
        from django.urls import reverse

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        activation_url = self.request.build_absolute_uri(
            reverse('users:activate_account', kwargs={'uidb64': uid, 'token': token})
        )

        subject = 'Confirm your Email Address'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email

        context = {
            'username': user.username,
            'activation_url': activation_url,
        }

        # Render text and HTML versions of the email
        text_content = render_to_string('emails/activation_email.txt', context)
        html_content = render_to_string('emails/activation_email.html', context)

        email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        email.attach_alternative(html_content, "text/html")
        email.send()


class ActivateAccount(View):
    def get(self, request, uidb64, token):
        try:
            uid_bytes = urlsafe_base64_decode(uidb64)
            uid = uid_bytes.decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist, binascii.Error, UnicodeDecodeError):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Your account has been activated successfully. You can now log in.")
            return redirect('users:login')
        else:
            return HttpResponse('Invalid or expired activation link.', status=400)
        
        
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