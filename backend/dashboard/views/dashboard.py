from django.views.generic import ListView
from django.db.models import Count, Q, F, IntegerField, ExpressionWrapper, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
import json
from datetime import timedelta

from nanopore.models import Screening, Enrollment, ClinicLaboratory, ZonalLaboratory,Diagnosis
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context
from locations.models import Site


class DashboardHomeView(ListView):
    model = Screening
    template_name = "dashboard/dashboard.html"
    context_object_name = "object_list"
    paginate_by = 50

    # ==================================================
    # Base queryset (role + filters)
    # ==================================================
    def get_queryset(self):
        qs = Screening.objects.select_related(
            "site", "site__district__region__zone", "sex", "enrolled"
        )

        # Apply role-based filtering
        qs = filter_queryset_by_user_role(self.request.user, qs, site_field="site")

        # Apply GET filters
        zone_id = self.request.GET.get("zone")
        site_id = self.request.GET.get("site")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        order_by = self.request.GET.get("order_by", "-screening_date")

        if zone_id:
            qs = qs.filter(site__district__region__zone_id=zone_id)

        if site_id:
            qs = qs.filter(site_id=site_id)

        if start_date and end_date:
            qs = qs.filter(screening_date__range=[start_date, end_date])

        return qs.order_by(order_by)

    # ==================================================
    # Context
    # ==================================================
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()

        # Role context
        role_context = get_role_context(self.request.user)
        context.update({
            "is_admin": role_context["is_admin"],
            "is_zonal_lab": role_context["is_zonal_lab"],
            "is_national_lab": role_context["is_national_lab"],
            "is_site_only": role_context["is_site_only"],
            "zones": {z.id: z.name for z in role_context["zones"]},
            "sites": {s.id: s.name for s in role_context["sites"]},
        })

        # ==================================================
        # GLOBAL COUNTS
        # ==================================================
        screened_count = qs.count()
        eligible_count = qs.filter(eligible=True).count()

        enrolled_qs = Enrollment.objects.filter(screening__in=qs)
        enrolled_count = enrolled_qs.count()
        
        # ==================================================
        # MODEL-BASED TARGETS (SITE SUM)
        # ==================================================
        site_ids = qs.values_list("site_id", flat=True).distinct()
        targets = Site.objects.filter(id__in=site_ids).aggregate(
            total_target=Sum("target"),
            substudy2_target=Sum("substudy2Target"),
            substudy4_target=Sum("substudy4Target"),
        )

        enrolled_required_count = targets["total_target"] or 0
        substudy2_required_count = targets["substudy2_target"] or 0
        substudy4_required_count = targets["substudy4_target"] or 0

        # Progress calculations
        enrolled_progress = round(
            enrolled_count / enrolled_required_count * 100, 1
        ) if enrolled_required_count else 0

        # ==================================================
        # SUBSTUDY 2 + 4 (ENROLLED ONLY)
        # ==================================================
        substudy2_enrolled_qs = enrolled_qs.filter(
            screening__clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6]
        )
        substudy4_enrolled_qs = enrolled_qs.filter(
            screening__clinic_laboratory__xpert_mtb__in=[1, 7, 8, 9]
        )

        substudy2_enrolled_count = substudy2_enrolled_qs.count()
        substudy4_enrolled_count = substudy4_enrolled_qs.count()

        substudy2_enrolled_progress = round(
            substudy2_enrolled_count / substudy2_required_count * 100, 1
        ) if substudy2_required_count else 0

        substudy4_enrolled_progress = round(
            substudy4_enrolled_count / substudy4_required_count * 100, 1
        ) if substudy4_required_count else 0


        # Diagnosis
        diagnosis_qs = Diagnosis.objects.filter(screening__in=qs)
        # diagnosis_count = diagnosis_qs.count()
        
        diagnosis_outcome_qs = diagnosis_qs.filter(
            screening__diagnosis__tb_outcome2__in=[1,2, 3, 4, 5]
        )

        diagnosis_outcome_count = diagnosis_outcome_qs.count()

        diagnosis_outcome_progress = round(
            diagnosis_outcome_count / substudy2_enrolled_count * 100, 1
        ) if substudy2_enrolled_count else 0
        
        
        # # ==================================================
        # SITE TARGETS (ROLE + FILTER AWARE)
        # ==================================================
        site_targets = (
            qs.values("site__id", "site__name", "site__target")
            .annotate(
                enrolled=Count("enrollment", distinct=True),
                remaining=ExpressionWrapper(
                    F("site__target") - Count("enrollment", distinct=True),
                    output_field=IntegerField(),
                ),
            )
            .order_by("site__name")
        )
        context["site_targets"] = site_targets

        # ==================================================
        # ZONAL LAB PROGRESS (ALL SUBSTUDIES)
        # ==================================================
        zonal_qs = ZonalLaboratory.objects.filter(screening__in=qs)
        total_substudy_counts = substudy2_enrolled_count
        zonal_completed_count = zonal_qs.count()
        zonal_progress = round(
            zonal_completed_count / total_substudy_counts * 100, 1
        ) if total_substudy_counts else 0

        # Individual test counts
        culture_completed_count = zonal_qs.filter(culture_performed=1).count()
        culture_progress = round(
            culture_completed_count / zonal_completed_count * 100, 1
        ) if zonal_completed_count else 0
        
        isolate_completed_count = zonal_qs.filter(culture_isolate=1).count()
        isolate_progress = round(
            isolate_completed_count / culture_completed_count * 100, 1
        ) if culture_completed_count else 0
        
        dst_completed_count = zonal_qs.filter(phenotypic_performed=1).count()
        dst_progress = round(
            dst_completed_count / isolate_completed_count * 100, 1
        ) if isolate_completed_count else 0
        
        xpert_xdr_completed_count = zonal_qs.filter(xpert_xdr_performed=1).count()
        xpert_xdr_progress = round(
            xpert_xdr_completed_count / total_substudy_counts * 100, 1
        ) if total_substudy_counts else 0
        
        lpa_completed_count = zonal_qs.filter(
            Q(first_line_lpa=1) | Q(second_line_lpa=1)
        ).distinct().count()
        lpa_progress = round(
            lpa_completed_count / total_substudy_counts * 100, 1
        ) if total_substudy_counts else 0
        
        nanopore_completed_count = zonal_qs.filter(nanopore_done=1).count()
        nanopore_progress = round(
            nanopore_completed_count / total_substudy_counts * 100, 1
        ) if total_substudy_counts else 0

        # ==================================================
        # CONTEXT PUSH
        # ==================================================
        context.update({
            # GLOBAL
            "screened_count": screened_count,
            "eligible_count": eligible_count,
            "enrolled_count": enrolled_count,
            "enrolled_required_count": enrolled_required_count,
            "enrolled_progress": enrolled_progress,
            "total_substudy_counts": total_substudy_counts,

            # SUBSTUDY 2
            "substudy2_enrolled_count": substudy2_enrolled_count,
            "substudy2_required_count": substudy2_required_count,
            "substudy2_enrolled_progress": substudy2_enrolled_progress,

            # SUBSTUDY 4
            "substudy4_enrolled_count": substudy4_enrolled_count,
            "substudy4_required_count": substudy4_required_count,
            "substudy4_enrolled_progress": substudy4_enrolled_progress,
            
            # DIAGNOSIS OUTCOME
            "diagnosis_outcome_count": diagnosis_outcome_count,
            "diagnosis_outcome_progress": diagnosis_outcome_progress,

            # ZONAL LAB
            "zonal_completed_count": zonal_completed_count,
            "zonal_progress": zonal_progress,
            "isolate_completed_count": isolate_completed_count,
            "isolate_progress": isolate_progress,
            "culture_completed_count": culture_completed_count,
            "culture_progress": culture_progress,
            "dst_completed_count": dst_completed_count,
            "dst_progress": dst_progress,
            "xpert_xdr_completed_count": xpert_xdr_completed_count,
            "xpert_xdr_progress": xpert_xdr_progress,
            "lpa_completed_count": lpa_completed_count,
            "lpa_progress": lpa_progress,
            "nanopore_completed_count": nanopore_completed_count,
            "nanopore_progress": nanopore_progress,
        })

        return context
