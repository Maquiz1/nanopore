"""
Date issues: dates that are impossible within a form or that conflict with a date on
another form of the same participant.

Each check compares two dates ("A before B" or "A after B" is the problem), or looks
for dates in the future / before the study started. The page lists the records with
both dates and links to the forms that hold them.

Agreed rules (Oct 2026): Xpert decides eligibility, so the Xpert date and Clinic Lab
sample 1 must be on or before the screening date; everything else follows the order
the forms are filled in.
"""
import datetime
from dataclasses import dataclass, field

from django.apps import apps
from django.db import models
from django.db.models import CharField, F, Q
from django.db.models.functions import Cast
from django.utils import timezone

from utils import access
from utils.access import can_see_queries, scope_queryset

STUDY_START = datetime.date(2025, 1, 1)

# form -> (label, model, link from a Screening to the form's record)
FORMS = {
    access.SCREENING: ("Screening", "Screening", None),
    access.ENROLLMENT: ("Enrollment", "Enrollment", "enrollment"),
    access.CLINIC_LAB: ("Clinic Lab", "ClinicLaboratory", "clinic_laboratory"),
    access.ZONAL_LAB: ("Zonal Lab", "ZonalLaboratory", "zonal_laboratory"),
    access.EDCS_TBLIS: ("EDCS / TBLIS", "EdcsTblisZonal", "tblis_laboratory"),
    access.DIAGNOSIS: ("Diagnosis", "Diagnosis", "diagnosis"),
    access.REGIMEN: ("Regimen", "RegimenChanges", None),
}
# Lookup prefix from a form's record to another form's fields
TO_FORM = {
    access.SCREENING: "screening__",
    access.CLINIC_LAB: "screening__clinic_laboratory__",
    access.DIAGNOSIS: "screening__diagnosis__",
}


@dataclass(frozen=True)
class DateCheck:
    key: str
    form: str                  # the form the record belongs to
    label: str
    q: Q
    a: tuple = ()              # (lookup, label) of the date that is wrong
    b: tuple = ()              # (lookup, label) it is compared with
    b_form: str = ""           # form holding date B, when it is another form
    fields: tuple = field(default=())  # future / too-early checks: the date fields looked at

    @property
    def between_forms(self):
        return bool(self.b_form) and self.b_form != self.form


def _lower(label):
    """Lower-case the first letter unless it starts an abbreviation (LJ, MGIT, TB...)."""
    return label if label[1:2].isupper() else label[:1].lower() + label[1:]


def _before(key, form, a, a_label, b, b_label, b_form=""):
    """Problem: date A is before date B."""
    path = TO_FORM.get(b_form, "") + b if b_form else b
    return DateCheck(key, form, f"{a_label} before {_lower(b_label)}",
                     Q(**{f"{a}__lt": F(path)}), (a, a_label), (path, b_label), b_form)


def _after(key, form, a, a_label, b, b_label, b_form=""):
    """Problem: date A is after date B."""
    path = TO_FORM.get(b_form, "") + b if b_form else b
    return DateCheck(key, form, f"{a_label} after {_lower(b_label)}",
                     Q(**{f"{a}__gt": F(path)}), (a, a_label), (path, b_label), b_form)


def _date_fields(model_name, skip=()):
    model = apps.get_model("nanopore", model_name)
    return tuple(f.name for f in model._meta.concrete_fields if type(f) is models.DateField and f.name not in skip)


def _range_checks(form):
    """Dates in the future, and dates before the study started (date of birth excluded)."""
    label, model_name, _ = FORMS[form]
    fields = _date_fields(model_name)
    early = _date_fields(model_name, skip=("dob",))
    today = timezone.localdate()
    future_q, early_q = Q(), Q()
    for f in fields:
        future_q |= Q(**{f"{f}__gt": today})
    for f in early:
        early_q |= Q(**{f"{f}__lt": STUDY_START})
    return [
        DateCheck(f"{form}_future", form, "Date in the future", future_q, fields=fields),
        DateCheck(f"{form}_too_early", form, f"Date before the study started ({STUDY_START:%d %b %Y})", early_q, fields=early),
    ]


S, E, C, Z, T, D, R = (access.SCREENING, access.ENROLLMENT, access.CLINIC_LAB, access.ZONAL_LAB,
                       access.EDCS_TBLIS, access.DIAGNOSIS, access.REGIMEN)


def _lab_checks(form):
    """Zonal Lab and EDCS / TBLIS have the same date fields."""
    p = "zonal" if form == Z else "edcs"
    received = ("date_sputum_received", "Sputum received")
    return [
        _before(f"{p}_received_before_screening", form, *received, "screening_date", "Screening date", S),
        _before(f"{p}_received_before_collected", form, *received, "date_sample1_collected", "Clinic sample 1 collected", C),
        _before(f"{p}_microscopy_before_received", form, "microscopy_date", "Microscopy date", *received),
        _before(f"{p}_lj_inoculation_before_received", form, "lj_inoculation_date", "LJ inoculation", *received),
        _before(f"{p}_lj_results_before_inoculation", form, "lj_results_date", "LJ results", "lj_inoculation_date", "LJ inoculation"),
        _before(f"{p}_mgit_inoculation_before_received", form, "mgit_inoculation_date", "MGIT inoculation", *received),
        _before(f"{p}_mgit_results_before_inoculation", form, "mgit_results_date", "MGIT results", "mgit_inoculation_date", "MGIT inoculation"),
        _before(f"{p}_isolate_before_received", form, "isolate_date", "Isolate date", *received),
        _before(f"{p}_lpa1_before_received", form, "first_line_lpa_date", "First-line LPA", *received),
        _before(f"{p}_lpa2_before_received", form, "second_line_lpa_date", "Second-line LPA", *received),
        _before(f"{p}_xdr_before_received", form, "xpert_xdr_date_performed", "Xpert XDR", *received),
        _before(f"{p}_dst1_before_received", form, "first_line_dst_performed_date", "First-line DST performed", *received),
        _before(f"{p}_dst1_results_before_performed", form, "first_line_dst_results_date", "First-line DST results",
                "first_line_dst_performed_date", "First-line DST performed"),
        _before(f"{p}_dst2_before_received", form, "second_line_dst_performed_date", "Second-line DST performed", *received),
        _before(f"{p}_dst2_results_before_performed", form, "second_line_dst_results_date", "Second-line DST results",
                "second_line_dst_performed_date", "Second-line DST performed"),
    ] + _range_checks(form)


def _outcome_before_treatment():
    # tb_outcome2_date is stored as text (YYYY-MM-DD): compared as text, which orders like a date
    q = Q(tb_treatment=1, tb_outcome2_date__regex=r"^\d{4}-\d{2}-\d{2}$",
          tb_outcome2_date__lt=Cast("tb_treatment_date", CharField()))
    return DateCheck("diagnosis_outcome_before_treatment", D, "Outcome date before treatment started", q,
                     ("tb_outcome2_date", "Outcome date"), ("tb_treatment_date", "Treatment started"))


def build_checks():
    return [
        _before("screening_consent_before_screening", S, "consent_date", "Consent date", "screening_date", "Screening date"),
        _after("screening_dob_after_screening", S, "dob", "Date of birth", "screening_date", "Screening date"),
        *_range_checks(S),

        _before("enrollment_before_screening", E, "enrollment_date", "Enrollment date", "screening_date", "Screening date", S),
        _before("enrollment_before_consent", E, "enrollment_date", "Enrollment date", "consent_date", "Consent date", S),
        _before("enrollment_info_before_screening", E, "date_information_collected", "Information collected", "screening_date", "Screening date", S),
        _before("enrollment_sputum_before_screening", E, "sputum_date", "Sputum date", "screening_date", "Screening date", S),
        *_range_checks(E),

        _after("clinic_sample1_after_screening", C, "date_sample1_collected", "Sample 1 collected", "screening_date", "Screening date", S),
        _before("clinic_sample1_received_before_collected", C, "date_sample1_received", "Sample 1 received", "date_sample1_collected", "Sample 1 collected"),
        _before("clinic_sample2_received_before_collected", C, "date_sample2_received", "Sample 2 received", "date_sample2_collected", "Sample 2 collected"),
        _after("clinic_xpert_after_screening", C, "xpert_date", "Xpert date", "screening_date", "Screening date", S),
        _before("clinic_xpert_before_sample1_received", C, "xpert_date", "Xpert date", "date_sample1_received", "Sample 1 received"),
        _before("clinic_afb_a_before_sample1_received", C, "afb_a_date", "AFB A date", "date_sample1_received", "Sample 1 received"),
        _before("clinic_afb_b_before_sample2_received", C, "afb_b_date", "AFB B date", "date_sample2_received", "Sample 2 received"),
        *_range_checks(C),

        *_lab_checks(Z),
        *_lab_checks(T),

        _before("diagnosis_before_screening", D, "tb_diagnosis_date", "TB diagnosis date", "screening_date", "Screening date", S),
        _before("diagnosis_treatment_before_screening", D, "tb_treatment_date", "Treatment started", "screening_date", "Screening date", S),
        _before("diagnosis_treatment_before_diagnosis", D, "tb_treatment_date", "Treatment started", "tb_diagnosis_date", "TB diagnosis date"),
        _before("diagnosis_clinician_before_xpert", D, "clinician_received_date", "Clinician received results", "xpert_date", "Xpert date", C),
        _outcome_before_treatment(),
        *_range_checks(D),

        _before("regimen_before_treatment", R, "date", "Regimen change date", "tb_treatment_date", "Treatment started", D),
        *_range_checks(R),
    ]


def visible_checks(user, builder=None):
    """Checks of the forms the user works on; builder gives another list of checks (DS / DR)."""
    return [check for check in (builder or build_checks)() if can_see_queries(user, check.form)]


def check_queryset(user, check, zone_id=None, site_id=None):
    """Records failing one check, limited to the user's sites."""
    model_name = FORMS[check.form][1]
    model = apps.get_model("nanopore", model_name)
    site = "site" if model_name == "Screening" else "screening__site"
    qs = scope_queryset(user, model.objects.all(), site).filter(check.q)
    if zone_id:
        qs = qs.filter(**{f"{site}__district__region__zone_id": zone_id})
    if site_id:
        qs = qs.filter(**{f"{site}_id": site_id})
    related = [] if model_name == "Screening" else ["screening"]
    return qs.select_related(*related).order_by("pk")


def date_issue_counts(user, zone_id=None, site_id=None, builder=None):
    return {check.key: check_queryset(user, check, zone_id, site_id).count() for check in visible_checks(user, builder)}


# ── Row helpers for the list page ───────────────────────────────────────────

def resolve(obj, lookup):
    """Follow a lookup like screening__clinic_laboratory__xpert_date on an object (None if missing)."""
    for part in lookup.split("__"):
        try:
            obj = getattr(obj, part)
        except Exception:  # missing related form
            return None
        if obj is None:
            return None
    return obj


def screening_of(obj):
    return obj if obj.__class__.__name__ == "Screening" else obj.screening


def form_record(obj, form):
    """The record of `form` for the participant of obj (obj itself for its own form)."""
    if FORMS[form][1] == obj.__class__.__name__:
        return obj
    accessor = FORMS[form][2]
    if form == access.SCREENING:
        return screening_of(obj)
    return resolve(screening_of(obj), accessor) if accessor else None
