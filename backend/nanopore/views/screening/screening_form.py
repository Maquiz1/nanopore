from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import ModelFormMixin
from django.views import View
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy

from nanopore.models import Screening
from nanopore.forms.screening.screeningform import ScreeningForm
from locations.models import Site

class ScreeningFormView(LoginRequiredMixin, View):
    template_name = "nanopore/screening/screening_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")
    form_class = ScreeningForm
    model = Screening

    def get_object(self, pk=None):
        if pk:
            return get_object_or_404(Screening, pk=pk)
        return None

    def get(self, request, pk=None):
        obj = self.get_object(pk)
        form = self.form_class(instance=obj)
        return render(request, self.template_name, {"form": form, "object": obj})

    def post(self, request, pk=None):
        obj = self.get_object(pk)
        form = self.form_class(request.POST, instance=obj)

        if form.is_valid():
            obj = form.save(commit=False)

            # Assign site
            site = getattr(getattr(request.user, "profile", None), "site", None)
            if site:
                obj.site = site
            elif not obj.site:
                obj.site = Site.objects.first()
            if not obj.site:
                form.add_error(None, "No site found. Please create a site first.")
                return render(request, self.template_name, {"form": form, "object": obj})

            # Assign audit fields
            if not obj.pk:  # new object
                obj.created_by = request.user
            obj.updated_by = request.user
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

            try:
                obj.save()
                form.save_m2m()
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, self.template_name, {"form": form, "object": obj})

            return redirect(self.success_url)

        return render(request, self.template_name, {"form": form, "object": obj})
