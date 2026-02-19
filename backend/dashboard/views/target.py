from django.views.generic import ListView
from django.db.models import Sum, F
from locations.models import Site
from nanopore.models import Enrollment

from django.views.generic import ListView
from django.db.models import Sum
from locations.models import Site, Zone
from nanopore.models import Enrollment
from utils.permissions import filter_queryset_by_user_role

class SiteTargetsView(ListView):
    model = Site
    template_name = "dashboard/target/site_targets.html"
    context_object_name = "sites"

    def get_queryset(self):
        """
        Annotate each site with actual enrolled counts for total, substudy2, and substudy4.
        Apply role-based filtering and optional GET filters: zone, site, start_date, end_date.
        """
        qs = Site.objects.all().order_by("name")

        # Role-based filtering
        qs = filter_queryset_by_user_role(self.request.user, qs, site_field="id")

        # GET filters
        zone_id = self.request.GET.get("zone")
        site_id = self.request.GET.get("site")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if zone_id:
            qs = qs.filter(district__region__zone_id=zone_id)

        if site_id:
            qs = qs.filter(id=site_id)

        # Annotate each site with actual enrolled counts
        for site in qs:
            enrollments = Enrollment.objects.filter(screening__site=site)
            if start_date and end_date:
                enrollments = enrollments.filter(screening__screening_date__range=[start_date, end_date])
            site.actual_total = enrollments.count()
            site.actual_substudy2 = enrollments.filter(
                screening__clinic_laboratory__xpert_mtb__in=[2,3,4,5,6]
            ).count()
            site.actual_substudy4 = enrollments.filter(
                screening__clinic_laboratory__xpert_mtb__in=[1,7,8,9]
            ).count()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sites = context["sites"]

        # Grand totals
        total_target = sum([s.target or 0 for s in sites])
        total_substudy2_target = sum([s.substudy2Target or 0 for s in sites])
        total_substudy4_target = sum([s.substudy4Target or 0 for s in sites])
        actual_total = sum([getattr(s, "actual_total", 0) for s in sites])
        actual_substudy2 = sum([getattr(s, "actual_substudy2", 0) for s in sites])
        actual_substudy4 = sum([getattr(s, "actual_substudy4", 0) for s in sites])

        # Zones for filter dropdown
        zones = Zone.objects.all().order_by("name")

        context.update({
            "total_target": total_target,
            "total_substudy2_target": total_substudy2_target,
            "total_substudy4_target": total_substudy4_target,
            "actual_total": actual_total,
            "actual_substudy2": actual_substudy2,
            "actual_substudy4": actual_substudy4,
            "zones": zones,
            # Pass GET params for template form
            "filter_zone": self.request.GET.get("zone", ""),
            "filter_site": self.request.GET.get("site", ""),
            "filter_start_date": self.request.GET.get("start_date", ""),
            "filter_end_date": self.request.GET.get("end_date", ""),
        })
        return context
