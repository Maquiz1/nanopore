from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django import forms

from nanopore.models import Screening
from nanopore.forms.screening.screeningform import ScreeningForm
from locations.models import Site


class ScreeningCreateView(LoginRequiredMixin, CreateView):
    model = Screening
    form_class = ScreeningForm
    template_name = "nanopore/screening/screening_form.html"
    success_url = reverse_lazy("nanopore:screening-list")

    def form_valid(self, form):
        # Save form without committing to assign extra fields
        obj = form.save(commit=False)

        # Assign site safely from user's profile
        site = getattr(getattr(self.request.user, "profile", None), "site", None)
        if site:
            obj.site = site
        else:
            obj.site = Site.objects.first()
            if not obj.site:
                form.add_error(None, "No site found. Please create a site first.")
                return self.form_invalid(form)

        # Assign created/updated info
        obj.created_by = self.request.user
        obj.updated_by = self.request.user
        now = timezone.now()
        obj.created_at = now
        obj.updated_at = now

        # Determine eligibility
        consent = form.cleaned_data.get("consent")
        unable_understand = form.cleaned_data.get("unable_understand")
        not_willing = form.cleaned_data.get("not_willing")

        obj.eligible = (
            consent.name == "Yes" and
            unable_understand.name == "No" and
            not_willing.name == "No"
        ) if consent and unable_understand and not_willing else False

        # Save object and m2m fields
        obj.save()
        try:
            form.save_m2m()
        except AttributeError:
            pass  # ignore if no m2m fields

        return redirect(self.success_url)

    def form_invalid(self, form):
        # Optionally print form errors to console for debugging
        print("Form errors:", form.errors)
        return super().form_invalid(form)
