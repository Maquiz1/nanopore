from django.views import View
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.apps import apps
from utils.permissions import filter_queryset_by_user_role
from django.db.models import Count
from utils.roles import get_role_context
from django.db.models import Q

class DiagnosisDataQualityReportView(View):
    template_name = "reports/data_quality/diagnosis/data_diagnosis_quality_report.html"

    def get(self, request, *args, **kwargs):
        Diagnosis = apps.get_model("nanopore", "Diagnosis")

        # Base queryset with related fields
        diagnoses = Diagnosis.objects.select_related(
            "screening",
            "screening__site",
            "screening__site__district__region__zone",
        ).order_by(
            "screening__site__district__region__zone__name",
            "screening__site__name",
            "screening__pid",
        )

        role_context = get_role_context(request.user)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_admin     = role_context.get("is_admin", False)
        is_reviewer  = role_context.get("is_reviewer", False)
        is_superuser = request.user.is_superuser
        is_full_access = is_admin or is_superuser
        is_privileged = is_admin or is_reviewer
        # ─────────────────────────────────────────────
        # Zones and Sites for filters
        # ─────────────────────────────────────────────
        
        
        # Filter by user role
        diagnoses = filter_queryset_by_user_role(
            request.user, diagnoses, site_field="screening__site"
        )


        # Prepare zone and site mappings for template
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        # After getting zone_id and site_id from GET
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        # Convert to int if possible
        zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id_int = int(site_id) if site_id and site_id.isdigit() else None

        # Resolve names for template
        selected_zone_name = zones.get(zone_id_int, "") if zone_id_int else ""
        selected_site_name = sites.get(site_id_int, "") if site_id_int else ""

        if zone_id_int:
            diagnoses = diagnoses.filter(
                screening__site__district__region__zone_id=zone_id_int
            )

        if site_id_int:
            diagnoses = diagnoses.filter(
                screening__site_id=site_id_int
            )
            
        # ─────────────────────────────────────────────
        # DUPLICATE TB REGISTER NUMBER
        # ─────────────────────────────────────────────

        duplicate_tb_register_numbers = (
            diagnoses
            .filter(tb_diagnosis=1, tb_treatment=1)
            .exclude(tb_register_number__isnull=True)
            .exclude(tb_register_number__exact="")
            .values("tb_register_number")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .values_list("tb_register_number", flat=True)
        )

        duplicate_tb_register_number = diagnoses.filter(
            tb_diagnosis=1,
            tb_treatment=1,
            tb_register_number__in=duplicate_tb_register_numbers
        )
        
        # ─────────────────────────────────────────────
        # TB DIAGNOSIS & TREATMENT
        # ─────────────────────────────────────────────
        six_months_ago = timezone.now().date() - timedelta(days=180)
        today = timezone.now().date()

        # Long treatment patients (≥6 months)
        long_treatment = diagnoses.filter(tb_treatment=1, tb_treatment_date__lte=six_months_ago)

        # Annotate months_on_treatment
        for diag in long_treatment:
            if diag.tb_treatment_date:
                diag.months_on_treatment = (today - diag.tb_treatment_date).days // 30
            else:
                diag.months_on_treatment = None

        # ─────────────────────────────────────────────
        # Pending TB outcomes
        # ─────────────────────────────────────────────
        pending_tb_outcome = long_treatment.filter(tb_outcome2__isnull=True)
        pending_tb_outcome_date = long_treatment.filter(tb_outcome2__in=[1,2,3,4,5], tb_outcome2_date__isnull=True)

        # Annotate months for template
        for diag in pending_tb_outcome:
            diag.months_on_treatment = (today - diag.tb_treatment_date).days // 30 if diag.tb_treatment_date else None
        for diag in pending_tb_outcome_date:
            diag.months_on_treatment = (today - diag.tb_treatment_date).days // 30 if diag.tb_treatment_date else None


        missing_tb_diagnosed_clinically = (
            diagnoses
            .filter(tb_diagnosis=1, tb_diagnosis_made=1)
            .annotate(clinical_count=Count("tb_diagnosed_clinically"))
            .filter(clinical_count=0)
        )
        
        missing_tb_clinically_other = diagnoses.filter(
            tb_diagnosis=1,
            tb_diagnosis_made=1,
            tb_diagnosed_clinically__value=96,
            tb_clinically_other__isnull=True
        ).distinct()
        
        
        missing_tb_diagnosis_made2 = diagnoses.filter(
            tb_diagnosis=2,
            tb_diagnosis_made2__isnull=True
        )
        
        # =====================================================
        # tb_diagnosis = 2 → all TB diagnosis fields must be EMPTY
        # =====================================================

        tb_diag_fields = [
            "tb_diagnosis_date",
            "tb_diagnosis_made",
            "diagnosis_made_other",
            "bacteriological_diagnosis",
            "tb_clinically_other",
            "clinician_received_date",
            "tb_treatment",
            "tb_treatment_date",
            "tb_facility",
            "tb_reason",
            "tb_register_number",
            "tb_regimen",
            "tb_regimen_other",
            "regimen_changed",
            "tb_outcome2",
            "tb_outcome2_date",
        ]

        tb_diag_filled_q = Q()
        for field in tb_diag_fields:
            tb_diag_filled_q |= ~Q(**{f"{field}__isnull": True})

        missing_tb_diagnosis_2_should_be_empty = diagnoses.filter(
            tb_diagnosis=2
        ).filter(
            tb_diag_filled_q | Q(tb_diagnosed_clinically__isnull=False)
        ).distinct()

        count_missing_tb_diagnosis_2_should_be_empty = missing_tb_diagnosis_2_should_be_empty.count()

        # ─────────────────────────────────────────────
        # Prepare context
        # ─────────────────────────────────────────────
        context = {
            "zones": zones,
            "sites": sites,
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",
            "selected_zone_name": selected_zone_name,
            "selected_site_name": selected_site_name,
            
            "report_date": timezone.now(),
            "total_diagnosis_records": diagnoses.count(),

            # TB Diagnosis
            "missing_tb_diagnosis": diagnoses.filter(tb_diagnosis__isnull=True),
            "count_missing_tb_diagnosis": diagnoses.filter(tb_diagnosis__isnull=True).count(),

            "missing_tb_diagnosis_date": diagnoses.filter(tb_diagnosis=1, tb_diagnosis_date__isnull=True),
            "count_missing_tb_diagnosis_date": diagnoses.filter(tb_diagnosis=1, tb_diagnosis_date__isnull=True).count(),

            "missing_tb_diagnosis_made": diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made__isnull=True),
            "count_missing_tb_diagnosis_made": diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made__isnull=True).count(),

            "missing_diagnosis_made_other": diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made__value=96, diagnosis_made_other__isnull=True),
            "count_missing_diagnosis_made_other": diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made__value=96, diagnosis_made_other__isnull=True).count(),
            
            # Bacteriological Diagnosis
            "missing_bacteriological_diagnosis": diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=2, bacteriological_diagnosis__isnull=True),
            "count_missing_bacteriological_diagnosis": diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=2, bacteriological_diagnosis__isnull=True).count(),

            "missing_clinician_received_date": diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=2, clinician_received_date__isnull=True),
            "count_missing_clinician_received_date": diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=2, clinician_received_date__isnull=True).count(),

            #  Clinical Diagnosis

            "missing_tb_diagnosed_clinically": missing_tb_diagnosed_clinically,
            "count_missing_tb_diagnosed_clinically": missing_tb_diagnosed_clinically.count(),

            "missing_tb_clinically_other": missing_tb_clinically_other,
            "count_missing_tb_clinically_other": missing_tb_clinically_other.count(),

            # ─────────────────────────────────────────────
            # DUPLICATE TB REGISTER NUMBER
            # ─────────────────────────────────────────────
            "duplicate_tb_register_number": duplicate_tb_register_number,
            "count_duplicate_tb_register_number": duplicate_tb_register_number.count(),
            # ─────────────────────────────────────────────

            # TB REGIMEN & REASON / TB Treatment
            
            "missing_tb_treatment": diagnoses.filter(tb_diagnosis=1, tb_treatment__isnull=True),
            "count_missing_tb_treatment": diagnoses.filter(tb_diagnosis=1, tb_treatment__isnull=True).count(),

            "missing_tb_treatment_date": diagnoses.filter(tb_treatment=1, tb_treatment_date__isnull=True),
            "count_missing_tb_treatment_date": diagnoses.filter(tb_treatment=1, tb_treatment_date__isnull=True).count(),

            "missing_tb_facility": diagnoses.filter(tb_treatment=2, tb_facility__isnull=True),
            "count_missing_tb_facility": diagnoses.filter(tb_treatment=2, tb_facility__isnull=True).count(),

            "missing_tb_reason": diagnoses.filter(tb_treatment=96, tb_reason__isnull=True),
            "count_missing_tb_reason": diagnoses.filter(tb_treatment=96, tb_reason__isnull=True).count(),
            
            "missing_tb_register_number": diagnoses.filter(tb_treatment=1, tb_register_number__isnull=True),
            "count_missing_tb_register_number": diagnoses.filter(tb_treatment=1, tb_register_number__isnull=True).count(),

            "missing_tb_regimen": diagnoses.filter(tb_treatment=1, tb_regimen__isnull=True),
            "count_missing_tb_regimen": diagnoses.filter(tb_treatment=1, tb_regimen__isnull=True).count(),

            "missing_regimen_changed": diagnoses.filter(tb_treatment=1, regimen_changed__isnull=True),
            "count_missing_regimen_changed": diagnoses.filter(tb_treatment=1, regimen_changed__isnull=True).count(),

            # TB OUTCOME (≥6 MONTHS TREATMENT)
            "pending_tb_outcome": pending_tb_outcome,
            "count_pending_tb_outcome": pending_tb_outcome.count(),

            "pending_tb_outcome_date": pending_tb_outcome_date,
            "count_pending_tb_outcome_date": pending_tb_outcome_date.count(),
            
            
            # Diagnosis other than TB

            "missing_tb_other_diagnosis": diagnoses.filter(tb_diagnosis=2, tb_other_diagnosis__isnull=True),
            "count_missing_tb_other_diagnosis": diagnoses.filter(tb_diagnosis=2, tb_other_diagnosis__isnull=True).count(),

            "missing_tb_other_specify": diagnoses.filter(tb_diagnosis=2, tb_other_diagnosis__value=96, tb_other_specify__isnull=True),
            "count_missing_tb_other_specify": diagnoses.filter(tb_diagnosis=2, tb_other_diagnosis__value=96, tb_other_specify__isnull=True).count(),

            # "missing_tb_diagnosis_made2": diagnoses.filter(tb_diagnosis=2, tb_diagnosis_made2__isnull=True),
            # "count_missing_tb_diagnosis_made2": diagnoses.filter(tb_diagnosis=2, tb_diagnosis_made2__isnull=True).count(),
            
            "missing_tb_diagnosis_made2" : missing_tb_diagnosis_made2,
            "count_missing_tb_diagnosis_made2" : missing_tb_diagnosis_made2.count(),
            
            "missing_tb_diagnosis_2_should_be_empty":missing_tb_diagnosis_2_should_be_empty,
            "count_missing_tb_diagnosis_2_should_be_empty":count_missing_tb_diagnosis_2_should_be_empty,

        }

        # Total issues
        context["total_diagnosis_issues"] = sum([
            
            # TB Diagnosis
            context["count_missing_tb_diagnosis"],
            context["count_missing_tb_diagnosis_date"],
            context["count_missing_tb_diagnosis_made"],
            context["count_missing_diagnosis_made_other"],
            
            # Bacteriological Diagnosis
            context["count_missing_bacteriological_diagnosis"],
            context["count_missing_clinician_received_date"],
            
            #  Clinical Diagnosis
            context["count_missing_tb_diagnosed_clinically"],
            context["count_missing_tb_clinically_other"],
            
            
            # DUPLICATE TB REGISTER NUMBER
            context["count_duplicate_tb_register_number"],
            
            # TB REGIMEN & REASON / TB Treatment
            context["count_missing_tb_treatment"],
            context["count_missing_tb_treatment_date"],
            context["count_missing_tb_register_number"],
            context["count_missing_tb_regimen"],
            context["count_missing_regimen_changed"],
            context["count_missing_tb_facility"],   
            context["count_missing_tb_reason"],
            
            # TB OUTCOME (≥6 MONTHS TREATMENT)
            context["count_pending_tb_outcome"],
            context["count_pending_tb_outcome_date"],
            
            # Diagnosis other than TB
            context["count_missing_tb_other_diagnosis"],
            context["count_missing_tb_other_specify"],
            context["count_missing_tb_diagnosis_made2"],
            
            
            context["count_missing_tb_diagnosis_2_should_be_empty"],            
            
        ])

        return render(request, self.template_name, context)
