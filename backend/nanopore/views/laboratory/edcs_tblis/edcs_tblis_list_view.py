from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Min, Max
from django.utils import timezone
from locations.models import Zone, Site
from nanopore.models import EdcsTblisZonal, ZonalLaboratory
from utils.permissions import filter_queryset_by_user_role


class EdcsTBLISLaboratoryListView(LoginRequiredMixin, ListView):
    model = EdcsTblisZonal
    template_name = "nanopore/laboratory/edcs_tblis/edcs_tblis_laboratory_list.html"
    context_object_name = "object_list"
    paginate_by = 30

    def get_queryset(self):
        qs = EdcsTblisZonal.objects.select_related("screening__site", "screening__sex")
        qs = filter_queryset_by_user_role(self.request.user, qs, site_field="screening__site")

        # Filters
        zone_id = self.request.GET.get("zone")
        site_id = self.request.GET.get("site")
        pid = self.request.GET.get("pid")
        unique_lab_no = self.request.GET.get("unique_lab_no")
        if zone_id:
            qs = qs.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(screening__site_id=site_id)
        if pid:
            qs = qs.filter(screening__pid__icontains=pid)
        if unique_lab_no:
            qs = qs.filter(unique_lab_no__icontains=unique_lab_no)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["zones"] = Zone.objects.all()
        context["sites"] = Site.objects.all()
        context["request"] = self.request

        # Upload stats
        total_tblis_records = EdcsTblisZonal.objects.count()
        total_edcs_records = ZonalLaboratory.objects.count()
        percentage_uploaded = (
            round((total_tblis_records / total_edcs_records) * 100, 2)
            if total_edcs_records else 0
        )
        last_upload = EdcsTblisZonal.objects.order_by("-updated_at").first()

        context.update({
            "total_edcs_records": total_edcs_records,
            "total_tblis_records": total_tblis_records,
            "percentage_uploaded": percentage_uploaded,
            "last_upload": last_upload.updated_at if last_upload else None,
            "last_upload_by": last_upload.updated_by if last_upload else None,
        })

        # TBLIS date range from DB
        date_agg = EdcsTblisZonal.objects.aggregate(
            date_from=Min("date_sputum_received"),
            date_to=Max("date_sputum_received"),
        )
        context["tblis_date_from"] = date_agg["date_from"]
        context["tblis_date_to"]   = date_agg["date_to"]

        return context