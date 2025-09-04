from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404

from nanopore.models import Screening
from nanopore.forms.screening.screeningform import ScreeningForm
from locations.models import Site

class ScreeningUpdateView(LoginRequiredMixin, UpdateView):
    model = Screening
    form_class = ScreeningForm
    template_name = "nanopore/screening/screening_form.html"
    success_url = reverse_lazy("nanopore:form-screening-list")

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Assign user's site if not set (only if you want to override)
        if not obj.site:
            if hasattr(self.request.user, "profile") and self.request.user.profile.site:
                obj.site = self.request.user.profile.site
            elif hasattr(self.request.user, "site") and self.request.user.site:
                obj.site = self.request.user.site
            else:
                obj.site = get_object_or_404(Site, id=1)  # fallback

        # Update audit fields
        obj.updated_by = self.request.user
        obj.updated_at = timezone.now()

        # Recalculate eligible
        if obj.consent and obj.unable_understand and obj.not_willing:
            obj.eligible = (
                obj.consent.name == "Yes" and
                obj.unable_understand.name == "No" and
                obj.not_willing.name == "No"
            )
        else:
            obj.eligible = False

        obj.save()
        return super().form_valid(form)
