from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError

from nanopore.models import Screening
from nanopore.forms.screening.screeningform import ScreeningForm
from locations.models import Site,Zone
from django.utils.http import url_has_allowed_host_and_scheme

class ScreeningFormView(LoginRequiredMixin, View):
    template_name = "nanopore/screening/screening_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")
    form_class = ScreeningForm
    model = Screening

    def get_object(self, pk=None):
        if pk:
            return get_object_or_404(Screening, pk=pk)
        return None


    # def get(self, request, pk=None):
    #     obj = self.get_object(pk)
    #     form = self.form_class(instance=obj, initial=self.get_initial(request, obj))
    #     context = self.get_context_data(form=form, object=obj)
    #     return render(request, self.template_name, context)
    
    def get(self, request, pk=None):
        obj = self.get_object(pk)

        next_url = request.GET.get("next") or request.META.get("HTTP_REFERER")

        form = self.form_class(instance=obj, initial=self.get_initial(request, obj))
        context = self.get_context_data(form=form, object=obj, next=next_url)

        return render(request, self.template_name, context)

    
    def get_context_data(self, **kwargs):
        """
        Returns context data for the template, including the user's zone
        and the Dar es Salaam zone reference.
        """
        context = kwargs
        user_site = getattr(getattr(self.request.user, "profile", None), "site", None)
        user_zone = None

        if user_site and user_site.district and user_site.district.region:
            user_zone = user_site.district.region.zone

        context["user_zone"] = user_zone
        context["dar_es_salaam_zone"] = Zone.objects.filter(name__iexact="Dar es Salaam").first()
        context["zone_group_1"] = [1]  # ← add this line
        context["zone_group_2_5"] = [2, 3, 4, 5]  # ← add this line
        
        # Calculate current age if dob exists
        form = context.get("form")
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
        form = self.form_class(request.POST, instance=obj, initial=self.get_initial(request, obj))
        context = self.get_context_data(form=form, object=obj)
        
        if form.is_valid():
            obj = form.save(commit=False)

            # Assign site from user profile if not already set
            site = getattr(getattr(request.user, "profile", None), "site", None)
            if site:
                obj.site = site
            elif not obj.site:
                obj.site = Site.objects.first()

            if not obj.site:
                form.add_error(None, "No site found. Please create a site first.")
                return render(request, self.template_name, {"form": form, "object": obj})

            # Assign audit fields
            if not obj.pk:
                obj.created_by = request.user
            obj.updated_by = request.user
            obj.updated_at = timezone.now()

            # Eligibility recalculation
            obj.eligible = self.calculate_eligibility(obj)

            try:
                obj.save()
                form.save_m2m()
            except ValidationError as e:
                form.add_error(None, e)
                return render(request, self.template_name, {"form": form, "object": obj})
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, self.template_name, {"form": form, "object": obj})

            # return redirect(self.success_url)
            next_url = request.POST.get("next")

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
            ):
                return redirect(next_url)


            return redirect(self.success_url)


        # return render(request, self.template_name, {"form": form, "object": obj})
    
        return render(request, self.template_name, context)


    def get_initial(self, request, obj=None):
        """
        Pre-fill the site in the form if user has a profile with a site.
        """
        initial = {}
        site = getattr(getattr(request.user, "profile", None), "site", None)
        if site:
            initial["site"] = site
        elif obj and obj.site:
            initial["site"] = obj.site
        return initial

    def calculate_eligibility(self, obj):
        """
        Recalculate eligibility based on zone, consent, understanding, willingness,
        age, inclusion/exclusion criteria.
        """
        eligible = True

        # Basic checks
        if not (obj.consent and obj.unable_understand and obj.not_willing):
            eligible = False
        elif not (obj.consent.name == "Yes" and obj.unable_understand.name == "No" and obj.not_willing.name == "No"):
            eligible = False

        # Age ≥ 18 at screening
        if obj.age < 18 or not (obj.age18years and obj.age18years.name == "Yes"):
            eligible = False

        # Zone-dependent inclusion
        zone = getattr(getattr(obj.site, "district", None), "region", None)
        zone = getattr(zone, "zone", None) if zone else None

        if zone and zone.name.lower() == "dar es salaam":
            if not (obj.present_symptoms and obj.present_symptoms.name == "Yes"):
                eligible = False
        elif zone:
            if not (obj.genexpert_confirmation and obj.genexpert_confirmation.name == "Yes"):
                eligible = False

        # Must be able to produce sample
        if not (obj.produce_resp_sample and obj.produce_resp_sample.name == "Yes"):
            eligible = False

        return eligible
