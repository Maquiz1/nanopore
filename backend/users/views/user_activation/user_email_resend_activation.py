from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.views import View
from django.views.generic import FormView

from users.emails import send_activation_email
from users.forms import ResendActivationEmailForm
from utils.access_mixins import SuperuserRequiredMixin

User = get_user_model()


def _user_from_link(uidb64, token):
    try:
        user = User.objects.get(pk=urlsafe_base64_decode(uidb64).decode())
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
    return user if default_token_generator.check_token(user, token) else None


class ActivateAccountView(View):
    """The link from the activation email: choose a password, which activates the account."""
    template_name = "registration/activate_account.html"

    def dispatch(self, request, uidb64, token):
        self.account = _user_from_link(uidb64, token)
        if self.account is None:
            return render(request, self.template_name, {"invalid": True})
        return super().dispatch(request, uidb64, token)

    def get(self, request, uidb64, token):
        return render(request, self.template_name, {"form": SetPasswordForm(self.account), "account": self.account})

    def post(self, request, uidb64, token):
        form = SetPasswordForm(self.account, request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "account": self.account})
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        messages.success(request, f"Your account is active. Log in with your username ({user.username}) or email.")
        return redirect("users:login")


class ResendActivationEmailView(FormView):
    """Public page: email a new activation link to an account that is not active yet."""
    template_name = "registration/resend_activation_email.html"
    form_class = ResendActivationEmailForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = User.objects.filter(email__iexact=form.cleaned_data["email"], is_active=False).first()
        if user:
            send_activation_email(user)
        # Same answer whether or not the address exists, so the page can't be used to find accounts
        messages.info(self.request, "If that email belongs to an account that is not active yet, "
                                    "a new activation link has been sent to it.")
        return super().form_valid(form)


class StaffResendActivationView(SuperuserRequiredMixin, View):
    """Users list: send (again) the activation link to one account."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if not user.email:
            messages.error(request, f"{user.username} has no email address. Add one first.")
        elif send_activation_email(user):
            messages.success(request, f"Activation link sent to {user.email}.")
        else:
            messages.error(request, f"Could not send the email to {user.email}. See Email logs for the reason.")
        back = request.POST.get("next")
        safe = back and url_has_allowed_host_and_scheme(back, {request.get_host()}, request.is_secure())
        return redirect(back if safe else "users:staff_list")
