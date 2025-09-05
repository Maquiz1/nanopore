# nanopore/views/status.py
from django.views.generic import ListView
from nanopore.models import Screening
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

class FormStatusListView(ListView):
    model = Screening
    template_name = "nanopore/form_status/form_status_list.html"
    context_object_name = "screenings"
    paginate_by = 10  # optional for large datasets

    def get_queryset(self):
        qs = Screening.objects.select_related(
            "enrollment",
            "clinic_laboratory",
            "zonal_laboratory",
            "diagnosis",
            "site",
            "site__district",
            "site__district__region",
            "site__district__region__zone",
        )

        # Role-based filtering
        qs = filter_queryset_by_user_role(self.request.user, qs)

        # GET filters
        zone_id = self.request.GET.get("zone")
        site_id = self.request.GET.get("site")
        pid = self.request.GET.get("pid")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        status = self.request.GET.get("status")  # 🔹 Status filter

        if zone_id:
            qs = qs.filter(site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(site_id=site_id)
        if pid:
            qs = qs.filter(pid__icontains=pid)
        if start_date and end_date:
            qs = qs.filter(screening_date__range=[start_date, end_date])
        
        # 🔹 Filter by eligibility status using correct field
        if status == "eligible":
            qs = qs.filter(eligible=True)
        elif status == "not_eligible":
            qs = qs.filter(eligible=False)

        return qs.order_by("-screening_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add zones and sites for filter dropdowns
        role_context = get_role_context(self.request.user)
        context.update(role_context)

        # Keep GET params for form persistence
        context['selected_zone'] = self.request.GET.get("zone", "")
        context['selected_site'] = self.request.GET.get("site", "")
        context['selected_pid'] = self.request.GET.get("pid", "")
        context['selected_start_date'] = self.request.GET.get("start_date", "")
        context['selected_end_date'] = self.request.GET.get("end_date", "")
        context['selected_status'] = self.request.GET.get("status", "")  # 🔹 Pass status to template

        return context
