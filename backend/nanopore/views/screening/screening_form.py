from utils import access
from utils.access_mixins import FormAccessMixin
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError

from nanopore.models import Screening
from nanopore.forms.screening.screeningform import ScreeningForm
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages

class ScreeningFormView(FormAccessMixin, View):
    access_form = access.SCREENING
    access_site_field = "site"
    access_is_form = True
    template_name = "nanopore/screening/screening_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")
    form_class = ScreeningForm
    model = Screening

    def get_object(self, pk=None):
        if pk:
            return get_object_or_404(self.scope(Screening.objects.all()), pk=pk)
        return None


    def build_form(self, obj, data=None):
        """
        The site decides the zone, the PID prefix and question 4 / 4(a).
        New screening: chosen from screening_site_choices (admins, data managers and
        data specialists see every zone they may access; nurses and clinicians only
        their assigned sites). Saved screening: the site is fixed.
        """
        form = self.form_class(data, instance=obj)
        self.limit_choices(form)
        field = form.fields["site"]
        if obj:
            field.disabled = True
            field.required = False
        else:
            field.queryset = access.screening_site_choices(self.request.user)
            field.required = True
            field.empty_label = "Select site"
            field.widget.attrs["class"] = "form-select"
            sites = list(field.queryset)
            if len(sites) == 1:
                field.initial = sites[0].pk
        return form

    def get(self, request, pk=None):
        obj = self.get_object(pk)

        next_url = request.GET.get("next") or request.META.get("HTTP_REFERER")

        form = self.build_form(obj)
        context = self.get_context_data(form=form, object=obj, next=next_url)

        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """
        Returns context data for the template, including the user's zone
        and the Dar es Salaam zone reference.
        """
        context = kwargs
        obj = context.get("object")
        form = context["form"]

        if obj:
            site = obj.site
        else:
            # Site picked on this (failed) post, or the only one the user can pick
            choices = list(form.fields["site"].queryset)
            site = form.cleaned_data.get("site") if form.is_bound and hasattr(form, "cleaned_data") else None
            if site is None and len(choices) == 1:
                site = choices[0]
            context["site_choices"] = choices
            context["chooses_location"] = access.chooses_screening_site(self.request.user)
            context["zone_choices"] = sorted(
                {s.district.region.zone for s in choices if s.district.region.zone}, key=lambda z: z.name)

        user_zone = site.district.region.zone if site and site.district and site.district.region else None
        context["user_zone"] = user_zone
        context["site"] = site
        # Question 4 (Dar es Salaam) or 4(a) (other zones); None = not chosen yet
        context["is_dar"] = user_zone.name.strip().lower() == "dar es salaam" if user_zone else None
        context["eligibility_problems"] = obj.eligibility_problems() if obj else []

        # Calculate current age if dob exists
        current_age = None
        if form and form.instance.dob:
            today = timezone.now().date()
            dob = form.instance.dob
            current_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        context["current_age"] = current_age
    
        return context


    def post(self, request, pk=None):
        # obj = self.get_object(pk)
        # form = self.form_class(request.POST, instance=obj, initial=self.get_initial(request, obj))

        obj = self.get_object(pk)
        original_site = obj.site if obj else None

        form = self.build_form(obj, request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            # A saved screening keeps its site
            if original_site:
                obj.site = original_site

            # Assign audit fields
            if not obj.pk:
                obj.created_by = request.user
            obj.updated_by = request.user
            obj.updated_at = timezone.now()

            # Eligibility is worked out in Screening.save()
            try:
                obj.save()
                form.save_m2m()
            except ValidationError as e:
                form.add_error(None, e)
                return render(request, self.template_name, self.get_context_data(form=form, object=self.get_object(pk), next=request.POST.get("next")))
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, self.template_name, self.get_context_data(form=form, object=self.get_object(pk), next=request.POST.get("next")))
            
            messages.success(request, "Screening saved successfully.")

            # return redirect(self.success_url)
            next_url = request.POST.get("next")

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
            ):
                return redirect(next_url)


            return redirect(self.success_url)


        return render(request, self.template_name, self.get_context_data(form=form, object=self.get_object(pk), next=request.POST.get("next")))
