# reports/views/mentorships/screening_data_quality_report_view.py
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Q, Count, F

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


DAR_ES_SALAAM_ZONE_ID = 1  # Dar es Salaam zone ID


class ScreeningDataQualityReportView(View):
    template_name = "reports/data_quality/screenings/data_screening_quality_report.html"

    def get(self, request, *args, **kwargs):
        Screening = apps.get_model("nanopore", "Screening")

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

        screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")
        if zone_id:
            screenings = screenings.filter(site__district__region__zone_id=zone_id)
        if site_id:
            screenings = screenings.filter(site_id=site_id)

        total_screenings = screenings.count()

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

        # Missing fields queries
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

        missing_reasons_qs = screenings.filter(
            enrolled__name__iexact="no",
            reasons__isnull=True
        )

        # Conditional missing
        missing_consent_date_when_yes_qs = screenings.filter(
            consent__name__iexact="yes",
            consent_date__isnull=True
        )

        missing_reasons_other_qs = screenings.filter(
            reasons__value=96,                    # ← fixed: use __value from EnrolledReason
            reasons_other__isnull=True
        )

        # Zone-specific (using constant for Dar es Salaam)
        dar_es_salaam_missing_symptoms_qs = screenings.filter(
            site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID,
            present_symptoms__isnull=True
        )

        other_zones_missing_genexpert_qs = screenings.exclude(
            site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID
        ).filter(genexpert_confirmation__isnull=True)

        # PID issues
        duplicate_pids = screenings.values("pid").annotate(pid_count=Count("id")).filter(pid_count__gt=1)
        duplicate_pids_set = {d["pid"] for d in duplicate_pids}

        mismatched_pids_qs = screenings.filter(
            ~Q(pid1=F("pid2")),
            pid1__isnull=False,
            pid2__isnull=False
        )

        invalid_length_pids_qs = screenings.filter(
            pid__isnull=False,
            pid__regex=r"^(?!.{16}$).*$"
        )

        not_eligible_qs = screenings.filter(eligible=False)

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

            # Lists (limited to 100)
            "missing_screening_date": [serialize_screening(s) for s in missing_screening_date_qs[:100]],
            "missing_pid1": [serialize_screening(s) for s in missing_pid1_qs[:100]],
            "missing_pid2": [serialize_screening(s) for s in missing_pid2_qs[:100]],
            "missing_sex": [serialize_screening(s) for s in missing_sex_qs[:100]],
            "missing_age_dob": [serialize_screening(s) for s in missing_age_dob_qs[:100]],
            "missing_consent": [serialize_screening(s) for s in missing_consent_qs[:100]],
            "missing_age18years": [serialize_screening(s) for s in missing_age18years_qs[:100]],
            "missing_present_symptoms": [serialize_screening(s) for s in dar_es_salaam_missing_symptoms_qs[:100]],
            "missing_genexpert_confirmation": [serialize_screening(s) for s in other_zones_missing_genexpert_qs[:100]],
            "missing_produce_resp_sample": [serialize_screening(s) for s in missing_produce_resp_sample_qs[:100]],
            "missing_unable_understand": [serialize_screening(s) for s in missing_unable_qs[:100]],
            "missing_not_willing": [serialize_screening(s) for s in missing_not_willing_qs[:100]],
            "missing_enrolled": [serialize_screening(s) for s in missing_enrolled_qs[:100]],
            "missing_reasons": [serialize_screening(s) for s in missing_reasons_qs[:100]],
            "missing_consent_date_when_yes": [serialize_screening(s) for s in missing_consent_date_when_yes_qs[:100]],
            "missing_reasons_other": [serialize_screening(s) for s in missing_reasons_other_qs[:100]],

            "duplicate_pids": [serialize_screening(s) for s in screenings.filter(pid__in=duplicate_pids_set)[:100]],
            "mismatched_pids": [serialize_screening(s) for s in mismatched_pids_qs[:100]],
            "invalid_length_pids": [serialize_screening(s) for s in invalid_length_pids_qs[:100]],
            "not_eligible": [serialize_screening(s) for s in not_eligible_qs[:100]],

            # Counts
            "count_missing_screening_date": missing_screening_date_qs.count(),
            "count_missing_pid1": missing_pid1_qs.count(),
            "count_missing_pid2": missing_pid2_qs.count(),
            "count_missing_sex": missing_sex_qs.count(),
            "count_missing_age_dob": missing_age_dob_qs.count(),
            "count_missing_consent": missing_consent_qs.count(),
            "count_missing_age18years": missing_age18years_qs.count(),
            "count_missing_present_symptoms": dar_es_salaam_missing_symptoms_qs.count(),
            "count_missing_genexpert_confirmation": other_zones_missing_genexpert_qs.count(),
            "count_missing_produce_resp_sample": missing_produce_resp_sample_qs.count(),
            "count_missing_unable_understand": missing_unable_qs.count(),
            "count_missing_not_willing": missing_not_willing_qs.count(),
            "count_missing_enrolled": missing_enrolled_qs.count(),
            "count_missing_reasons": missing_reasons_qs.count(),
            "count_missing_consent_date_when_yes": missing_consent_date_when_yes_qs.count(),
            "count_missing_reasons_other": missing_reasons_other_qs.count(),
            "count_duplicate_pids": len(duplicate_pids_set),
            "count_mismatched_pids": mismatched_pids_qs.count(),
            "count_invalid_length_pids": invalid_length_pids_qs.count(),
            "count_not_eligible": not_eligible_qs.count(),
        }

        # Total issues – exact order from context processor
        context["total_issues"] = (
            context["count_duplicate_pids"] +
            context["count_invalid_length_pids"] +
            context["count_mismatched_pids"] +
            context["count_missing_pid1"] +
            context["count_missing_pid2"] +
            context["count_not_eligible"] +
            context["count_missing_screening_date"] +
            context["count_missing_sex"] +
            context["count_missing_age_dob"] +
            context["count_missing_consent"] +
            context["count_missing_consent_date_when_yes"] +
            context["count_missing_age18years"] +
            context["count_missing_present_symptoms"] +
            context["count_missing_genexpert_confirmation"] +
            context["count_missing_produce_resp_sample"] +
            context["count_missing_unable_understand"] +
            context["count_missing_not_willing"] +
            context["count_missing_enrolled"] +
            context["count_missing_reasons"] +
            context["count_missing_reasons_other"]
        )

        return render(request, self.template_name, context)