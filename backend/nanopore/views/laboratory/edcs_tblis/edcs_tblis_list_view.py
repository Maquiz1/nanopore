from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Min, Max
from django.utils import timezone
from locations.models import Zone, Site
from nanopore.models import EdcsTblisZonal, ZonalLaboratory, EdcsTblisMergeSummary
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
        merge_summary = EdcsTblisMergeSummary.objects.order_by("-created_at").first()
        
        total_edcs_records = ZonalLaboratory.objects.count()
        
        # Calculate coverage based on ONLY the Zonal records (since Non-Zonal aren't merged)
        from django.db.models import Q
        allowed_prefixes = [
            "DF_TZ_SS2_14", "DF_TZ_SS2_15", "DF_TZ_SS2_16",
            "DF_TZ_SS2_17", "DF_TZ_SS2_18", "DF_TZ_SS2_19"
        ]
        prefix_query = Q()
        for prefix in allowed_prefixes:
            prefix_query |= Q(screening__pid__startswith=prefix)
        total_zonal_edcs = ZonalLaboratory.objects.filter(prefix_query).count()
        
        total_tblis_records = merge_summary.matched_records if merge_summary else 0
        percentage_uploaded = (
            round((total_tblis_records / total_zonal_edcs) * 100, 2)
            if total_zonal_edcs else 0
        )
        
        last_upload = EdcsTblisZonal.objects.order_by("-updated_at").first()

        context.update({
            "total_edcs_records": total_edcs_records,
            "total_zonal_edcs": total_zonal_edcs,
            "total_tblis_records": total_tblis_records,
            "percentage_uploaded": percentage_uploaded,
            "last_upload": merge_summary.created_at if merge_summary else (last_upload.updated_at if last_upload else None),
            "last_upload_by": merge_summary.uploaded_by if merge_summary else None,
            "merge_summary": merge_summary,
        })

        # TBLIS date range from DB
        date_agg = EdcsTblisZonal.objects.aggregate(
            date_from=Min("date_sputum_received"),
            date_to=Max("date_sputum_received"),
        )
        context["tblis_date_from"] = date_agg["date_from"]
        context["tblis_date_to"]   = date_agg["date_to"]

        # Latest merge summary from management command
        context["merge_summary"] = EdcsTblisMergeSummary.objects.first()

        return context