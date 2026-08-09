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

    def _get_latest_batch(self):
        """Cache latest batch on the instance to avoid repeated DB hits."""
        if not hasattr(self, "_latest_batch"):
            self._latest_batch = TblisUploadBatch.objects.first()
        return self._latest_batch

    def get_queryset(self):
        card_type = self.request.GET.get("card_type") or self.request.GET.get("view_type")

        # 1. Cards based on TblisRawData
        if card_type in {"total_tblis", "tblis_not_in_edcs"}:
            latest_batch = self._get_latest_batch()
            if not latest_batch:
                return TblisRawData.objects.none()
            
            qs = TblisRawData.objects.filter(upload_batch=latest_batch).order_by("labno")
            if card_type == "tblis_not_in_edcs":
                zonal_lab_numbers = ZonalLaboratory.objects.values("unique_lab_no")
                qs = qs.exclude(labno__in=zonal_lab_numbers)
            
            labno = self.request.GET.get("unique_lab_no") or self.request.GET.get("labno")
            if labno:
                qs = qs.filter(labno__icontains=labno)
            return qs.order_by("labno")

        # 2. Cards based on ZonalLaboratory
        ctrl_prefixes = [
            "DF_TZ_SS2_14", "DF_TZ_SS2_15", "DF_TZ_SS2_16",
            "DF_TZ_SS2_17", "DF_TZ_SS2_18", "DF_TZ_SS2_19"
        ]
        from django.db.models import Q
        prefix_q = Q()
        for p in ctrl_prefixes:
            prefix_q |= Q(screening__pid__startswith=p)

        if card_type in {"total_edcs", "ctrl"} or (card_type and card_type.startswith("other_zones")):
            qs = ZonalLaboratory.objects.select_related(
                "screening__site",
                "screening__sex",
                "screening__clinic_laboratory__xpert_mtb_rif_conducted",
                "screening__clinic_laboratory__xpert_mtb",
                "culture_performed",
            )
            qs = filter_queryset_by_user_role(self.request.user, qs, site_field="screening__site")
            if card_type == "ctrl":
                qs = qs.filter(prefix_q)
            elif card_type.startswith("other_zones"):
                qs = qs.exclude(prefix_q)
                if card_type == "other_zones_substudy2":
                    qs = qs.filter(screening__clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6])
                elif card_type == "other_zones_substudy4":
                    qs = qs.filter(screening__clinic_laboratory__xpert_mtb__in=[1, 7, 8, 9])
                elif card_type == "other_zones_missing_culture":
                    qs = qs.filter(culture_performed__isnull=True)
                elif card_type == "other_zones_uncategorized":
                    qs = qs.exclude(screening__clinic_laboratory__xpert_mtb__in=[1, 2, 3, 4, 5, 6, 7, 8, 9])
            return qs.order_by(
                "screening__site__district__region__zone__name",
                "screening__site__name",
                "screening__pid",
            )

        # 3. All other cards (or default reset view) based on EdcsTblisZonal
        qs = EdcsTblisZonal.objects.select_related(
            "screening__site",
            "screening__sex",
            "screening__clinic_laboratory__xpert_mtb_rif_conducted",
            "screening__clinic_laboratory__xpert_mtb",
            "culture_performed",
        )
        qs = filter_queryset_by_user_role(self.request.user, qs, site_field="screening__site")

        # Latest upload batch labnos for merged / not in TBLIS logic
        latest_batch = self._get_latest_batch()
        latest_tblis_rows = (
            TblisRawData.objects.filter(upload_batch=latest_batch)
            if latest_batch
            else TblisRawData.objects.none()
        )
        tblis_lab_numbers = latest_tblis_rows.values("labno")
        merged_lab_numbers = latest_tblis_rows.filter(is_merged=True).values("labno")

        if not card_type:
            # Default view: show only records merged from the latest upload batch
            qs = qs.filter(unique_lab_no__in=merged_lab_numbers)

        ss2_xpert = [2, 3, 4, 5, 6]
        ss4_xpert = [1, 7, 8, 9]

        if card_type == "missing_culture":
            qs = qs.filter(culture_performed__isnull=True)
        elif card_type == "merged_uncategorized":
            qs = qs.filter(prefix_q, unique_lab_no__in=merged_lab_numbers).exclude(
                screening__clinic_laboratory__xpert_mtb__in=ss2_xpert + ss4_xpert
            )
        elif card_type == "merged":
            qs = qs.filter(prefix_q, unique_lab_no__in=merged_lab_numbers)
        elif card_type == "merged_substudy2":
            qs = qs.filter(
                prefix_q,
                unique_lab_no__in=merged_lab_numbers,
                screening__clinic_laboratory__xpert_mtb__in=ss2_xpert
            )
        elif card_type == "merged_missing_culture_substudy2":
            qs = qs.filter(
                prefix_q,
                unique_lab_no__in=merged_lab_numbers,
                screening__clinic_laboratory__xpert_mtb__in=ss2_xpert,
                culture_performed__isnull=True
            )
        elif card_type == "merged_substudy4":
            qs = qs.filter(
                prefix_q,
                unique_lab_no__in=merged_lab_numbers,
                screening__clinic_laboratory__xpert_mtb__in=ss4_xpert
            )
        elif card_type == "merged_missing_culture_substudy4":
            qs = qs.filter(
                prefix_q,
                unique_lab_no__in=merged_lab_numbers,
                screening__clinic_laboratory__xpert_mtb__in=ss4_xpert,
                culture_performed__isnull=True
            )
        elif card_type == "merged_missing_culture_uncategorized":
            qs = qs.filter(
                prefix_q,
                unique_lab_no__in=merged_lab_numbers,
                culture_performed__isnull=True
            ).exclude(
                screening__clinic_laboratory__xpert_mtb__in=ss2_xpert + ss4_xpert
            )
        elif card_type == "edcs_not_in_tblis":
            qs = qs.filter(prefix_q).exclude(unique_lab_no__in=tblis_lab_numbers)
        elif card_type == "edcs_not_in_tblis_substudy2":
            qs = qs.filter(prefix_q, screening__clinic_laboratory__xpert_mtb__in=ss2_xpert).exclude(
                unique_lab_no__in=tblis_lab_numbers
            )
        elif card_type == "missing_culture_substudy2":
            qs = qs.filter(
                screening__clinic_laboratory__xpert_mtb__in=ss2_xpert,
                culture_performed__isnull=True
            )
        elif card_type == "edcs_not_in_tblis_substudy4":
            qs = qs.filter(prefix_q, screening__clinic_laboratory__xpert_mtb__in=ss4_xpert).exclude(
                unique_lab_no__in=tblis_lab_numbers
            )
        elif card_type == "missing_culture_substudy4":
            qs = qs.filter(
                screening__clinic_laboratory__xpert_mtb__in=ss4_xpert,
                culture_performed__isnull=True
            )
        elif card_type == "edcs_not_in_tblis_uncategorized":
            qs = qs.filter(prefix_q).exclude(unique_lab_no__in=tblis_lab_numbers).exclude(
                screening__clinic_laboratory__xpert_mtb__in=ss2_xpert + ss4_xpert
            )

        # Filters from form / params
        zone_id = self.request.GET.get("zone")
        site_id = self.request.GET.get("site")
        pid = self.request.GET.get("pid")
        unique_lab_no = self.request.GET.get("unique_lab_no")
        substudy = self.request.GET.get("substudy")
        if zone_id:
            qs = qs.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(screening__site_id=site_id)
        if pid:
            qs = qs.filter(screening__pid__icontains=pid)
        if unique_lab_no:
            qs = qs.filter(unique_lab_no__icontains=unique_lab_no)
        if substudy:
            if substudy == 'Substudy 2':
                qs = qs.filter(screening__clinic_laboratory__xpert_mtb__in=ss2_xpert)
            elif substudy == 'Substudy 4':
                qs = qs.filter(screening__clinic_laboratory__xpert_mtb__in=ss4_xpert)
        # Sort: zone → site → pid
        qs = qs.order_by(
            "screening__site__district__region__zone__name",
            "screening__site__name",
            "screening__pid",
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_card = self.request.GET.get("card_type") or self.request.GET.get("view_type", "")
        context["view_type"] = active_card
        context["active_card_type"] = active_card
        context["zones"] = Zone.objects.all()
        context["sites"] = Site.objects.all()
        context["request"] = self.request

        # Upload stats
        total_edcs_records = ZonalLaboratory.objects.count()
        
        # Other zonal (non-CTRL) records
        from django.db.models import Q as _Q
        _ctrl_prefixes = [
            "DF_TZ_SS2_14", "DF_TZ_SS2_15", "DF_TZ_SS2_16",
            "DF_TZ_SS2_17", "DF_TZ_SS2_18", "DF_TZ_SS2_19"
        ]
        _other_q = _Q()
        for _p in _ctrl_prefixes:
            _other_q |= _Q(screening__pid__startswith=_p)
        other_qs = ZonalLaboratory.objects.exclude(_other_q)
        total_other_zonal_records = other_qs.count()
        other_zonal_substudy2 = other_qs.filter(screening__clinic_laboratory__xpert_mtb__in=[2,3,4,5,6]).count()
        other_zonal_substudy4 = other_qs.filter(screening__clinic_laboratory__xpert_mtb__in=[1,7,8,9]).count()
        other_zonal_uncategorized = other_qs.exclude(screening__clinic_laboratory__xpert_mtb__in=[1,2,3,4,5,6,7,8,9]).count()
        other_zonal_missing_culture = other_qs.filter(culture_performed__isnull=True).count()

        other_zonal_percentages = {
            'substudy2': round((other_zonal_substudy2 / total_other_zonal_records) * 100, 2) if total_other_zonal_records else 0,
            'substudy4': round((other_zonal_substudy4 / total_other_zonal_records) * 100, 2) if total_other_zonal_records else 0,
            'uncategorized': round((other_zonal_uncategorized / total_other_zonal_records) * 100, 2) if total_other_zonal_records else 0,
        }

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
        latest_upload_batch = self._get_latest_batch()
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

        total_zonal_edcs = ZonalLaboratory.objects.count()
        total_ctrl_records = ctrl_laboratories.count()
        total_raw_tblis_records = latest_tblis_rows.count()
        total_merged_records = latest_tblis_rows.filter(is_merged=True).count()
        total_edcs_not_in_tblis_qs = ctrl_laboratories.exclude(
            unique_lab_no__in=tblis_lab_numbers
        )
        total_edcs_not_in_tblis = total_edcs_not_in_tblis_qs.count()

        # Breakdown by substudy for EDCS Not in TBLIS
        from django.db.models import Case, When, CharField, Count, Value
        substudy_breakdown_qs = total_edcs_not_in_tblis_qs.annotate(
            substudy=Case(
                When(screening__clinic_laboratory__xpert_mtb__in=[2,3,4,5,6], then=Value('Substudy 2')),
                When(screening__clinic_laboratory__xpert_mtb__in=[1,7,8,9], then=Value('Substudy 4')),
                default=Value('Uncategorized'),
                output_field=CharField(),
            )
        ).values('substudy').annotate(cnt=Count('id'))

        # Breakdown by substudy for Total EDCS CTRL Merged Records
        merged_qs = ctrl_laboratories.filter(unique_lab_no__in=latest_tblis_rows.filter(is_merged=True).values("labno"))
        merged_substudy_breakdown_qs = merged_qs.annotate(
            substudy=Case(
                When(screening__clinic_laboratory__xpert_mtb__in=[2,3,4,5,6], then=Value('Substudy 2')),
                When(screening__clinic_laboratory__xpert_mtb__in=[1,7,8,9], then=Value('Substudy 4')),
                default=Value('Uncategorized'),
                output_field=CharField(),
            )
        ).values('substudy').annotate(cnt=Count('id'))

        # Convert to dict with space‑free keys for template access
        key_map = {
            'Substudy 2': 'substudy2',
            'Substudy 4': 'substudy4',
            'Uncategorized': 'uncategorized',
        }
        edcs_not_in_tblis_breakdown = {v: 0 for v in key_map.values()}
        for item in substudy_breakdown_qs:
            mapped_key = key_map.get(item['substudy'])
            if mapped_key:
                edcs_not_in_tblis_breakdown[mapped_key] = item['cnt']
        total_tblis_not_in_edcs = latest_tblis_rows.exclude(
            labno__in=zonal_lab_numbers
        ).count()
        
        total_tblis_records = merge_summary.matched_records if merge_summary else 0
        percentage_uploaded = (
            round((total_tblis_records / total_ctrl_records) * 100, 2)
            if total_ctrl_records else 0
        )

        edcs_not_in_tblis_percentages = {}
        for key, cnt in edcs_not_in_tblis_breakdown.items():
            edcs_not_in_tblis_percentages[key] = (
                round((cnt / total_edcs_not_in_tblis) * 100, 2) if total_edcs_not_in_tblis else 0
            )

        merged_breakdown = {v: 0 for v in key_map.values()}
        for item in merged_substudy_breakdown_qs:
            mapped_key = key_map.get(item['substudy'])
            if mapped_key:
                merged_breakdown[mapped_key] = item['cnt']

        merged_percentages = {}
        for key, cnt in merged_breakdown.items():
            merged_percentages[key] = (
                round((cnt / total_merged_records) * 100, 2) if total_merged_records else 0
            )

        merged_missing_culture_substudy2 = EdcsTblisZonal.objects.filter(
            screening__clinic_laboratory__xpert_mtb__in=[2,3,4,5,6],
            culture_performed__isnull=True
        ).count()
        merged_missing_culture_substudy4 = EdcsTblisZonal.objects.filter(
            screening__clinic_laboratory__xpert_mtb__in=[1,7,8,9],
            culture_performed__isnull=True
        ).count()
        merged_missing_culture_uncategorized = EdcsTblisZonal.objects.filter(
            culture_performed__isnull=True
        ).exclude(
            screening__clinic_laboratory__xpert_mtb__in=[1,2,3,4,5,6,7,8,9]
        ).count()

        missing_culture_substudy2 = EdcsTblisZonal.objects.filter(
            screening__clinic_laboratory__xpert_mtb__in=[2,3,4,5,6],
            culture_performed__isnull=True
        ).count()
        missing_culture_substudy4 = EdcsTblisZonal.objects.filter(
            screening__clinic_laboratory__xpert_mtb__in=[1,7,8,9],
            culture_performed__isnull=True
        ).count()
        missing_culture_uncategorized = EdcsTblisZonal.objects.filter(
            culture_performed__isnull=True
        ).exclude(
            screening__clinic_laboratory__xpert_mtb__in=[1,2,3,4,5,6,7,8,9]
        ).count()
        total_missing_culture_performed = EdcsTblisZonal.objects.filter(
            culture_performed__isnull=True
        ).count()

        missing_culture_breakdown = {
            'substudy2': missing_culture_substudy2,
            'substudy4': missing_culture_substudy4,
            'uncategorized': missing_culture_uncategorized,
        }

        last_upload = EdcsTblisZonal.objects.order_by("-updated_at").first()

        context.update({
            "total_edcs_records": total_edcs_records,
            "total_other_zonal_records": total_other_zonal_records,
            "other_zonal_substudy2": other_zonal_substudy2,
            "other_zonal_substudy4": other_zonal_substudy4,
            "other_zonal_uncategorized": other_zonal_uncategorized,
            "other_zonal_percentages": other_zonal_percentages,
            "other_zonal_missing_culture": other_zonal_missing_culture,
            "total_zonal_edcs": total_zonal_edcs,
            "total_tblis_records": total_tblis_records,
            "total_ctrl_records": total_ctrl_records,
            "total_raw_tblis_records": total_raw_tblis_records,
            "total_merged_records": total_merged_records,
            "total_edcs_not_in_tblis": total_edcs_not_in_tblis,
            "total_tblis_not_in_edcs": total_tblis_not_in_edcs,
            "edcs_not_in_tblis_breakdown": edcs_not_in_tblis_breakdown,
            "edcs_not_in_tblis_percentages": edcs_not_in_tblis_percentages,
            "merged_breakdown": merged_breakdown,
            "merged_percentages": merged_percentages,
            "merged_missing_culture_substudy2": merged_missing_culture_substudy2,
            "merged_missing_culture_substudy4": merged_missing_culture_substudy4,
            "merged_missing_culture_uncategorized": merged_missing_culture_uncategorized,
            "missing_culture_substudy2": missing_culture_substudy2,
            "missing_culture_substudy4": missing_culture_substudy4,
            "missing_culture_uncategorized": missing_culture_uncategorized,
            "missing_culture_breakdown": missing_culture_breakdown,
            "total_missing_culture_performed": total_missing_culture_performed,
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
