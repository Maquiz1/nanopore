from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from locations.models import Zone, Site
from nanopore.models import Enrollment, ClinicLaboratory, Diagnosis, ZonalLaboratory
from utils.permissions import filter_queryset_by_user_role


class ZonalLaboratoryListView(LoginRequiredMixin, ListView):
    model = ZonalLaboratory
    template_name = "nanopore/laboratory/zonal/zonal_laboratory_list.html"
    context_object_name = "object_list"
    paginate_by = 10

    def get_queryset(self):
        qs = ZonalLaboratory.objects.select_related("screening__site", "screening__sex")
        qs = filter_queryset_by_user_role(self.request.user, qs, site_field="screening__site")
        # Filters
        zone_id = self.request.GET.get("zone")
        site_id = self.request.GET.get("site")
        pid = self.request.GET.get("pid")
        if zone_id:
            qs = qs.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(screening__site_id=site_id)
        if pid:
            qs = qs.filter(screening__pid__icontains=pid)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["zones"] = Zone.objects.all()
        context["sites"] = Site.objects.all()
        context["request"] = self.request
        return context
