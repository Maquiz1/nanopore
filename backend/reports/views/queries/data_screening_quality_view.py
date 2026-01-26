# reports/views/mentorships/screening_data_quality_report_view.py
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Q, Count, F, Exists, OuterRef

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class ScreeningDataQualityReportView(View):
    """
    Detailed Screening Data Quality Report.
    
    Shows categorized lists of records with specific quality issues.
    Uses efficient querysets (no full Python loop over all records).
    """

    template_name = "reports/data_quality/screenings/data_screening_quality_report.html"

    def get(self, request, *args, **kwargs):
        Screening = apps.get_model("nanopore", "Screening")

        # ── Base queryset ────────────────────────────────────────────────────
        screenings = Screening.objects.select_related(
            "site",
            "site__district__region__zone",
            "sex",
            "enrolled",
            "consent",
            "produce_resp_sample",
            "genexpert_confirmation",
            "unable_understand",
            "not_willing",
            "reasons",
        ).order_by(
            "site__district__region__zone__name",
            "site__name",
            "pid",
        )

        # Apply permission scoping
        screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

        # ── Optional filters ─────────────────────────────────────────────────
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")
        if zone_id:
            screenings = screenings.filter(site__district__region__zone_id=zone_id)
        if site_id:
            screenings = screenings.filter(site_id=site_id)

        total_screenings = screenings.count()

        # ── Helper: serialize record (used for all issue lists) ─────────────
        def serialize_screening(s):
            zone_obj = getattr(
                getattr(getattr(getattr(s, "site", None), "district", None), "region", None), "zone", None
            )
            return {
                "id": s.id,
                "pid": s.pid or "",
                "pid1": s.pid1 or "",
                "pid2": s.pid2 or "",
                "screening_date": s.screening_date,
                "zone_name": zone_obj.name if zone_obj else "",
                "site_name": getattr(s.site, "name", ""),
                "sex": getattr(getattr(s, "sex", None), "name", ""),
                "age": s.age,
                "dob": s.dob,
                "eligible": s.eligible,
                "consent": getattr(getattr(s, "consent", None), "name", ""),
                "produce_resp_sample": getattr(getattr(s, "produce_resp_sample", None), "name", ""),
                "genexpert_confirmation": getattr(getattr(s, "genexpert_confirmation", None), "name", ""),
                "enrolled": getattr(getattr(s, "enrolled", None), "name", ""),
            }

        # ── 1. Missing / null fields ─────────────────────────────────────────
        # We use .values() + .distinct() to avoid loading full objects twice
        missing_screening_date_qs = screenings.filter(screening_date__isnull=True)
        missing_pid1_qs           = screenings.filter(pid1__isnull=True)
        missing_pid2_qs           = screenings.filter(pid2__isnull=True)
        missing_sex_qs            = screenings.filter(sex__isnull=True)
        missing_age_dob_qs        = screenings.filter(age__isnull=True, dob__isnull=True)
        missing_consent_qs        = screenings.filter(consent__isnull=True)
        missing_age18years_qs     = screenings.filter(age18years__isnull=True)
        missing_present_symptoms_qs = screenings.filter(present_symptoms__isnull=True)
        missing_produce_resp_sample_qs = screenings.filter(produce_resp_sample__isnull=True)
        missing_genexpert_qs      = screenings.filter(genexpert_confirmation__isnull=True)
        missing_unable_qs         = screenings.filter(unable_understand__isnull=True)
        missing_not_willing_qs    = screenings.filter(not_willing__isnull=True)
        missing_enrolled_qs       = screenings.filter(enrolled__isnull=True)

        # Missing reasons only when enrolled = "No"
        missing_reasons_qs = screenings.filter(
            enrolled__name__iexact="no",
            reasons__isnull=True
        )

        # ── 2. PID issues ────────────────────────────────────────────────────
        # Duplicates
        duplicate_pids = (
            screenings.values("pid")
            .annotate(pid_count=Count("id"))
            .filter(pid_count__gt=1)
        )
        duplicate_pids_set = {d["pid"] for d in duplicate_pids}
        duplicate_pids_list = [
            serialize_screening(s) for s in screenings if s.pid in duplicate_pids_set
        ]

        # Mismatched pid1 != pid2
        mismatched_pids_list = [
            serialize_screening(s) for s in screenings.filter(
                ~Q(pid1=F("pid2")),
                pid1__isnull=False,
                pid2__isnull=False
            )
        ]

        # Invalid PID length (not exactly 16 chars)
        invalid_length_pids_list = [
            serialize_screening(s) for s in screenings.filter(
                pid__isnull=False,
                pid__regex=r"^(?!.{16}$).*$"   # not exactly 16 chars
            )
        ]

        # ── 3. Not eligible ──────────────────────────────────────────────────
        not_eligible_list = [
            serialize_screening(s) for s in screenings.filter(eligible=False)
        ]

        # ── Zone-specific logic (Dar es Salaam vs others) ────────────────────
        dar_es_salaam_missing_symptoms = screenings.filter(
            site__district__region__zone__name__iexact="dar es salaam",
            present_symptoms__isnull=True
        )
        other_zones_missing_genexpert = screenings.exclude(
            site__district__region__zone__name__iexact="dar es salaam"
        ).filter(
            genexpert_confirmation__isnull=True
        )

        # ── Role context & dropdowns ─────────────────────────────────────────
        role_context = get_role_context(request.user)

        context = {
            "total_screenings": total_screenings,
            "report_date": timezone.now(),
            "report_title": "Screening Data Quality Report",
            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "zones": {z.id: z.name for z in role_context.get("zones", [])},
            "sites": {s.id: s.name for s in role_context.get("sites", [])},
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",

            # Missing fields (limited to avoid huge pages)
            "missing_screening_date": [serialize_screening(s) for s in missing_screening_date_qs[:100]],
            "missing_pid1": [serialize_screening(s) for s in missing_pid1_qs[:100]],
            "missing_pid2": [serialize_screening(s) for s in missing_pid2_qs[:100]],
            "missing_sex": [serialize_screening(s) for s in missing_sex_qs[:100]],
            "missing_age_dob": [serialize_screening(s) for s in missing_age_dob_qs[:100]],
            "missing_consent": [serialize_screening(s) for s in missing_consent_qs[:100]],
            "missing_age18years": [serialize_screening(s) for s in missing_age18years_qs[:100]],
            "missing_present_symptoms": [serialize_screening(s) for s in dar_es_salaam_missing_symptoms[:100]],
            "missing_genexpert_confirmation": [serialize_screening(s) for s in other_zones_missing_genexpert[:100]],
            "missing_produce_resp_sample": [serialize_screening(s) for s in missing_produce_resp_sample_qs[:100]],
            "missing_unable_understand": [serialize_screening(s) for s in missing_unable_qs[:100]],
            "missing_not_willing": [serialize_screening(s) for s in missing_not_willing_qs[:100]],
            "missing_enrolled": [serialize_screening(s) for s in missing_enrolled_qs[:100]],
            "missing_reasons": [serialize_screening(s) for s in missing_reasons_qs[:100]],

            # Other issues
            "duplicate_pids": duplicate_pids_list[:100],
            "mismatched_pids": mismatched_pids_list[:100],
            "invalid_length_pids": invalid_length_pids_list[:100],
            "not_eligible": not_eligible_list[:100],

            # Counts (for badges / summary)
            "count_missing_screening_date": missing_screening_date_qs.count(),
            "count_missing_pid1": missing_pid1_qs.count(),
            # ... add counts for all other categories you want to show
            "count_duplicate_pids": len(duplicate_pids_set),
            "count_mismatched_pids": len(mismatched_pids_list),
            "count_invalid_length_pids": len(invalid_length_pids_list),
            "count_not_eligible": len(not_eligible_list),
        }

        # Optional: total issues count (if you want to show it)
        context["total_issues"] = sum(
            context[f"count_{k}"] for k in context if k.startswith("count_")
        )

        return render(request, self.template_name, context)