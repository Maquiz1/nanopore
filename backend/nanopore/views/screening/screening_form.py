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
from locations.models import Site,Zone
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


    # def get(self, request, pk=None):
    #     obj = self.get_object(pk)
    #     form = self.form_class(instance=obj, initial=self.get_initial(request, obj))
    #     context = self.get_context_data(form=form, object=obj)
    #     return render(request, self.template_name, context)
    
    def get(self, request, pk=None):
        obj = self.get_object(pk)

        next_url = request.GET.get("next") or request.META.get("HTTP_REFERER")

        form = self.limit_choices(self.form_class(instance=obj, initial=self.get_initial(request, obj)))
        context = self.get_context_data(form=form, object=obj, next=next_url)

        return render(request, self.template_name, context)

    
    def get_context_data(self, **kwargs):
        """
        Returns context data for the template, including the user's zone
        and the Dar es Salaam zone reference.
        """
        context = kwargs
        # Determine the relevant site for this form
        obj = context.get('object')
        relevant_site = None
        if obj and obj.site:
            relevant_site = obj.site
        elif hasattr(self.request.user, "profile") and self.request.user.profile.sites.exists():
            relevant_site = self.request.user.profile.sites.first()
        elif hasattr(self.request.user, "profile") and self.request.user.profile.zones.exists():
            relevant_site = Site.objects.filter(district__region__zone=self.request.user.profile.zones.first()).first()

        user_zone = None
        if relevant_site and relevant_site.district and relevant_site.district.region:
            user_zone = relevant_site.district.region.zone

        context["user_zone"] = user_zone
        context["site"] = relevant_site
        # Question 4 (Dar es Salaam) or 4(a) (other zones); None = zone unknown, show both
        context["is_dar"] = user_zone.name.strip().lower() == "dar es salaam" if user_zone else None
        context["eligibility_problems"] = obj.eligibility_problems() if obj else []
        
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
        original_site = obj.site if obj else None
        
        form = self.form_class(request.POST, instance=obj, initial=self.get_initial(request, obj))
        context = self.get_context_data(form=form, object=obj, next=request.POST.get("next"))

        self.limit_choices(form)
        
        if form.is_valid():
            obj = form.save(commit=False)
            
            # If updating an existing record, STRICTLY preserve its original site
            if pk and original_site:
                obj.site = original_site

            # Ensure site is set for NEW records: default to user's first assigned site
            if not obj.site:
                if hasattr(request.user, "profile") and request.user.profile.sites.exists():
                    obj.site = request.user.profile.sites.first()
                elif hasattr(request.user, "profile") and request.user.profile.zones.exists():
                    obj.site = Site.objects.filter(district__region__zone=request.user.profile.zones.first()).first()

            if not obj.site:
                form.add_error(None, "No site found. Please create a site first.")
                return render(request, self.template_name, context)

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
                return render(request, self.template_name, context)
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, self.template_name, context)
            
            messages.success(request, "Screening saved successfully.")

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
        if obj and obj.site:
            initial["site"] = obj.site
        elif hasattr(request.user, "profile") and request.user.profile.sites.exists():
            initial["site"] = request.user.profile.sites.first()
        elif hasattr(request.user, "profile") and request.user.profile.zones.exists():
            initial["site"] = Site.objects.filter(district__region__zone=request.user.profile.zones.first()).first()
        return initial
