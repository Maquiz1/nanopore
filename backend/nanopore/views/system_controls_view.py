from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from nanopore.models.system_control import SystemControl

class SystemControlsView(UserPassesTestMixin, View):
    template_name = "nanopore/system_controls.html"

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        # Allow superusers and ADMIN group
        if user.is_superuser:
            return True
        if user.groups.filter(name__iexact="ADMIN").exists():
            return True
        return False

    def get(self, request, *args, **kwargs):
        control = SystemControl.objects.first()
        if not control:
            control = SystemControl.objects.create()
        return render(request, self.template_name, {"control": control})

    def post(self, request, *args, **kwargs):
        control = SystemControl.objects.first()
        if not control:
            control = SystemControl.objects.create()

        # Checkboxes only send a value if they are checked.
        # If not present in request.POST, they are False.
        control.enable_form_submissions = request.POST.get("enable_form_submissions") == "on"
        control.enable_new_screening = request.POST.get("enable_new_screening") == "on"
        control.save()

        messages.success(request, "System Controls updated successfully.")
        return redirect("nanopore:system-controls")
