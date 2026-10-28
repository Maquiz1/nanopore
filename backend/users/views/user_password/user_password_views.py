from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from notifications.mail import emails_enabled
from users.emails import random_password, send_activation_email, send_password_reset_email
from utils.access_mixins import SuperuserRequiredMixin

User = get_user_model()


class StaffResetPasswordView(SuperuserRequiredMixin, View):
    """Users list > Reset password: email a reset link, or make a temporary password shown once."""
    template_name = "users/staff/reset_password.html"

    def get(self, request, pk):
        return render(request, self.template_name, {"staff_member": get_object_or_404(User, pk=pk)})

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if request.POST.get("action") == "temporary":
            password = random_password()
            user.set_password(password)
            user.is_active = True
            user.save()
            # Shown on the page itself (never stored in a message or cookie)
            return render(request, "users/staff/temporary_password.html", {"staff_member": user, "password": password})

        if not emails_enabled():
            messages.error(request, "Emails are turned off on this server. Make a temporary password instead.")
            return redirect("users:staff_reset_password", pk=user.pk)
        if not user.email:
            messages.error(request, f"{user.username} has no email address. Make a temporary password instead.")
            return redirect("users:staff_reset_password", pk=user.pk)
        # A not-yet-activated account gets the activation link: choosing a password also activates it
        sent = send_activation_email(user) if not user.is_active else send_password_reset_email(user)
        if sent:
            kind = "Activation" if not user.is_active else "Password reset"
            messages.success(request, f"{kind} link sent to {user.email}.")
        else:
            messages.error(request, f"Could not send the email to {user.email}. See Email logs for the reason.")
        return redirect("users:staff_list")


class ChangeOwnPasswordView(LoginRequiredMixin, PasswordChangeView):
    """Profile > Change password. Keeps the person logged in."""
    template_name = "registration/password_change_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        return form

    def get_success_url(self):
        return reverse("users:profile", args=[self.request.user.pk])

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed.")
        return super().form_valid(form)
