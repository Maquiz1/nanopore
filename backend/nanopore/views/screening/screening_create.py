from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from nanopore.models import Screening
from nanopore.forms.screening.screeningform import ScreeningForm
from locations.models import Site

class ScreeningCreateView(LoginRequiredMixin, CreateView):
    model = Screening
    form_class = ScreeningForm
    template_name = "nanopore/screening/screening_form.html"
    success_url = reverse_lazy("nanopore:screening-list")

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Assign site from user profile or fallback
        site = getattr(getattr(self.request.user, "profile", None), "site", None)
        if site:
            obj.site = site
        elif not obj.site:
            obj.site = Site.objects.first()
        if not obj.site:
            form.add_error(None, "No site found. Please create a site first.")
            return self.form_invalid(form)

        # Assign created_by/updated_by
        obj.created_by = self.request.user
        obj.updated_by = self.request.user
        obj.updated_at = timezone.now()

        # PID will be generated in model save()
        try:
            obj.save()
            form.save_m2m()
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        return redirect(self.success_url)
