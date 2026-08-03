from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Min, Max
from django.utils import timezone
from locations.models import Zone, Site
from nanopore.models import (
    EdcsTblisMergeSummary,
    EdcsTblisZonal,
    TblisRawData,
    TblisUploadBatch,
    ZonalLaboratory,
)
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
        total_edcs_records = ZonalLaboratory.objects.count()
        
        # CTRL laboratory records are the Dar es Salaam records that receive TBLIS transformations.
        from django.db.models import Q
        ctrl_prefixes = [
            "DF_TZ_SS2_14", "DF_TZ_SS2_15", "DF_TZ_SS2_16",
            "DF_TZ_SS2_17", "DF_TZ_SS2_18", "DF_TZ_SS2_19"
        ]
        prefix_query = Q()
        for prefix in ctrl_prefixes:
            prefix_query |= Q(screening__pid__startswith=prefix)
        ctrl_laboratories = ZonalLaboratory.objects.filter(prefix_query)
        zonal_lab_numbers = ZonalLaboratory.objects.values("unique_lab_no")
        latest_upload_batch = TblisUploadBatch.objects.first()
        merge_summary = (
            EdcsTblisMergeSummary.objects.filter(upload_batch=latest_upload_batch).first()
            if latest_upload_batch
            else EdcsTblisMergeSummary.objects.first()
        )
        latest_tblis_rows = (
            TblisRawData.objects.filter(upload_batch=latest_upload_batch)
            if latest_upload_batch
            else TblisRawData.objects.none()
        )
        tblis_lab_numbers = latest_tblis_rows.values("labno")

        total_zonal_edcs = ctrl_laboratories.count()
        total_ctrl_records = total_zonal_edcs
        total_raw_tblis_records = latest_tblis_rows.count()
        total_merged_records = latest_tblis_rows.filter(is_merged=True).count()
        total_edcs_not_in_tblis = ctrl_laboratories.exclude(
            unique_lab_no__in=tblis_lab_numbers
        ).count()
        total_tblis_not_in_edcs = latest_tblis_rows.exclude(
            labno__in=zonal_lab_numbers
        ).count()
        
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
            "total_ctrl_records": total_ctrl_records,
            "total_raw_tblis_records": total_raw_tblis_records,
            "total_merged_records": total_merged_records,
            "total_edcs_not_in_tblis": total_edcs_not_in_tblis,
            "total_tblis_not_in_edcs": total_tblis_not_in_edcs,
            "latest_upload_batch": latest_upload_batch,
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

        return context
