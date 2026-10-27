"""
Numbers for the Queries overview page (/reports/data-quality/all-issues/).

Per form: the queries on filled forms and the forms not filled yet, only for the
forms the user works on (utils/access.can_see_queries), so the total equals the
Queries badge in the sidebar.

Without a zone/site filter the numbers come from the sidebar's own cached counts
(instant, identical by construction). With a filter they are counted with the same
functions the daily snapshot uses, and cached for 5 minutes per user and filter.
"""
from django.core.cache import cache

from reports.context_processors.form_missing.forms_context import forms_report_total
from reports.context_processors.form_queries.clinic_laboratory_context import clinic_report_total
from reports.context_processors.form_queries.diagnosis_context import diagnosis_report_total
from reports.context_processors.form_queries.edcs_tblis_laboratory_context_processor import edcs_tblis_report_total
from reports.context_processors.form_queries.enrollment_context import enrollment_report_total
from reports.context_processors.form_queries.regimen_context_processor import regimen_report_total
from reports.context_processors.form_queries.screening_context import screening_report_total
from reports.context_processors.form_queries.zonal_laboratory_context import zonal_report_total
from reports.services.missing_form_dq_counts import get_missing_forms_counts
from reports.services.query_snapshot import SOURCES
from utils import access
from utils.access import can_see_queries

# form -> (label, short description, quality report URL name, missing-forms key or None)
FORMS = {
    access.SCREENING: ("Screening", "Missing fields, consent, PID issues", "reports:screening_quality_report", None),
    access.ENROLLMENT: ("Enrollment", "Missing or invalid answers", "reports:enrollment_quality_report", "enrollment"),
    access.CLINIC_LAB: ("Clinic Lab", "Samples, AFB and Xpert results", "reports:clinic_quality_report", "clinic"),
    access.ZONAL_LAB: ("Zonal Lab", "Receipt, culture, LPA, DST, sequencing", "reports:zonal_quality_report", "zonal"),
    access.EDCS_TBLIS: ("EDCS / TB-LIS", "Results imported from TB-LIS", "reports:edcs_tblis_quality_report", None),
    access.DIAGNOSIS: ("Diagnosis", "Diagnosis, treatment and outcome", "reports:diagnosis_quality_report", "diagnosis"),
    access.REGIMEN: ("Regimen", "Regimen changes: date, drug, reason", "reports:regimen_quality_report", "regimen"),
}
# Sidebar processors and the key holding each form's total
PROCESSORS = {
    access.SCREENING: (screening_report_total, "context_screening_report_total"),
    access.ENROLLMENT: (enrollment_report_total, "context_enrollment_report_total"),
    access.CLINIC_LAB: (clinic_report_total, "context_clinic_report_total"),
    access.ZONAL_LAB: (zonal_report_total, "context_zonal_report_total"),
    access.EDCS_TBLIS: (edcs_tblis_report_total, "context_edcs_tblis_report_total"),
    access.DIAGNOSIS: (diagnosis_report_total, "context_diagnosis_report_total"),
    access.REGIMEN: (regimen_report_total, "context_regimen_report_total"),
}
COUNTERS = {form: counter for form, _, counter in SOURCES}


def _unfiltered(request):
    queries = {form: proc(request).get(key, 0) for form, (proc, key) in PROCESSORS.items()}
    m = forms_report_total(request)["context_forms_report_total"]
    missing = {key: m.get(f"context_missing_{key}_count", 0) for key in access.MISSING_FORM_TYPES}
    return queries, missing


def _filtered(user, zone_id, site_id):
    key = f"queries_overview:{user.pk}:{zone_id}:{site_id}"
    cached = cache.get(key)
    if cached is None:
        queries = {form: sum(COUNTERS[form](user, site_id, zone_id).values())
                   for form in FORMS if can_see_queries(user, form)}
        counts = get_missing_forms_counts(user, zone_id=zone_id, site_id=site_id)
        missing = {k: counts.get(f"missing_{k}_count", 0) for k in access.MISSING_FORM_TYPES}
        cached = (queries, missing)
        cache.set(key, cached, 300)
    return cached


def queries_overview(request, zone_id=None, site_id=None):
    user = request.user
    queries, missing = _filtered(user, zone_id, site_id) if (zone_id or site_id) else _unfiltered(request)
    forms = []
    for form, (label, description, report_url, missing_key) in FORMS.items():
        if not can_see_queries(user, form):
            continue
        forms.append({
            "key": form, "label": label, "description": description, "report_url": report_url,
            "queries": queries.get(form, 0),
            "missing_key": missing_key, "missing": missing.get(missing_key, 0) if missing_key else 0,
        })
    total_queries = sum(f["queries"] for f in forms)
    total_missing = sum(f["missing"] for f in forms)
    return {
        "forms": forms,
        "missing_forms": [f for f in forms if f["missing_key"]],
        "total_queries": total_queries,
        "total_missing": total_missing,
        "grand_total": total_queries + total_missing,
    }
