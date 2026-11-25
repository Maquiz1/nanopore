"""
Record verification (nanopore/study_lock.py has the lock itself).

A data specialist / data manager (utils.access.VERIFY_RECORDS) marks a form record
Verified from its View page. It can't be verified while it has open queries. Verified, it
is read only for everyone; a verifier unlocks it with a reason, it is corrected, and then
verified again. Every verify and unlock is kept (VerificationEvent).
"""
from django.apps import apps
from django.db import transaction

from nanopore import study_lock
from utils import access

MODELS = {
    access.SCREENING: ("Screening", "Screening", "nanopore:screening-detail"),
    access.ENROLLMENT: ("Enrollment", "Enrollment", "nanopore:enrollment-detail"),
    access.CLINIC_LAB: ("ClinicLaboratory", "Clinic Lab", "nanopore:clinic-laboratory-detail"),
    access.ZONAL_LAB: ("ZonalLaboratory", "Zonal Lab", "nanopore:zonal-laboratory-detail"),
    access.DIAGNOSIS: ("Diagnosis", "Diagnosis", "nanopore:diagnosis-detail"),
}


def model_of(form):
    return apps.get_model("nanopore", MODELS[form][0])


def _count(totals):
    return sum(v for k, v in totals.items() if isinstance(v, int) and not k.endswith("_total"))


def open_queries(user, form, obj):
    """How many open queries this record has (form queries, date issues, DS / DR checks)."""
    one = type(obj)._default_manager.filter(pk=obj.pk)
    total = 0
    if form == access.SCREENING:
        from reports.services.screening_dq.screening_dq import get_screening_dq
        total += _count(get_screening_dq(one)[1])
    elif form == access.ENROLLMENT:
        from reports.services.enrollment_dq.enrollment_dq import get_enrollment_dq
        total += _count(get_enrollment_dq(one)[1])
    elif form == access.CLINIC_LAB:
        from reports.services.clinic_dq.clinic_dq import get_clinic_dq
        total += _count(get_clinic_dq(one)[1])
    elif form == access.DIAGNOSIS:
        from reports.services.diagnosis_dq.diagnosis_dq import get_diagnosis_dq
        total += _count(get_diagnosis_dq(one)[1])
    elif form == access.ZONAL_LAB:
        from reports.services.zonal_dq.stats import get_zonal_stats
        total += get_zonal_stats(one)[1]
    from reports.services import dsdr_checks
    from reports.services.accepted import split
    from reports.services.date_issues import _failing, build_checks, check_values
    for check in [*build_checks(), *dsdr_checks.build_checks()]:
        if check.form != form:
            continue
        failing = _failing(user, check).filter(pk=obj.pk)
        total += split(failing, check.list_key, check.key, lambda o, c=check: check_values(c, o))[0].count()
    return total


def verify(user, form, obj):
    """Returns an error message, or None when verified."""
    from nanopore.models import RecordVerification, VerificationEvent
    if study_lock.is_locked():
        return "The study is locked."
    if study_lock.is_verified(form, obj.pk):
        return "Already verified."
    found = open_queries(user, form, obj)
    if found:
        return f"This record has {found} open quer{'y' if found == 1 else 'ies'}: fix or accept them before verifying."
    screening_id = obj.pk if form == access.SCREENING else obj.screening_id
    with transaction.atomic():
        RecordVerification.objects.create(form=form, object_id=obj.pk, screening_id=screening_id, verified_by=user)
        VerificationEvent.objects.create(form=form, object_id=obj.pk, screening_id=screening_id,
                                         action=VerificationEvent.VERIFY, by=user)
    return None


def unlock(user, form, obj, reason):
    from nanopore.models import RecordVerification, VerificationEvent
    if study_lock.is_locked():
        return "The study is locked."
    if not reason:
        return "Give the reason for unlocking."
    screening_id = obj.pk if form == access.SCREENING else obj.screening_id
    with transaction.atomic():
        if not RecordVerification.objects.filter(form=form, object_id=obj.pk).delete()[0]:
            return "This record is not verified."
        VerificationEvent.objects.create(form=form, object_id=obj.pk, screening_id=screening_id,
                                         action=VerificationEvent.UNLOCK, reason=reason, by=user)
    return None


def progress(user):
    """Per form: records, verified, percent (the user's sites)."""
    from nanopore.models import RecordVerification
    rows = []
    for form, (model_name, label, _) in MODELS.items():
        site = "site" if form == access.SCREENING else "screening__site"
        records = access.scope_queryset(user, model_of(form).objects.all(), site)
        total = records.count()
        done = RecordVerification.objects.filter(form=form, object_id__in=records.values("pk")).count()
        rows.append({"form": form, "label": label, "total": total, "verified": done,
                     "percent": round(100 * done / total) if total else 0})
    return rows


def participant_forms(screening):
    """[(form, record)] of the participant's forms that exist: Screening, Enrollment, Clinic Lab, Zonal Lab, Diagnosis."""
    found = [(access.SCREENING, screening)]
    for form, accessor in ((access.ENROLLMENT, "enrollment"), (access.CLINIC_LAB, "clinic_laboratory"),
                           (access.ZONAL_LAB, "zonal_laboratory"), (access.DIAGNOSIS, "diagnosis")):
        try:
            record = getattr(screening, accessor)
        except Exception:  # no such form yet
            record = None
        if record is not None:
            found.append((form, record))
    return found


def verify_all(user, screening):
    """Verify every form of a participant, all or nothing. Returns (number verified now, problems)."""
    from nanopore.models import RecordVerification, VerificationEvent
    if study_lock.is_locked():
        return 0, ["The study is locked."]
    forms = [(form, record) for form, record in participant_forms(screening) if not study_lock.is_verified(form, record.pk)]
    problems = []
    for form, record in forms:
        found = open_queries(user, form, record)
        if found:
            problems.append(f"{MODELS[form][1]} has {found} open quer{'y' if found == 1 else 'ies'}")
    if problems:
        return 0, problems
    with transaction.atomic():
        for form, record in forms:
            RecordVerification.objects.create(form=form, object_id=record.pk, screening_id=screening.pk, verified_by=user)
            VerificationEvent.objects.create(form=form, object_id=record.pk, screening_id=screening.pk,
                                             action=VerificationEvent.VERIFY, reason="Verify all forms", by=user)
    return len(forms), []


def participant_status(screenings):
    """{screening pk: (verified, forms)} for a page of participants."""
    from nanopore.models import RecordVerification
    screenings = list(screenings)
    verified = {}
    for form, pk, screening_id in RecordVerification.objects.filter(
            screening_id__in=[s.pk for s in screenings]).values_list("form", "object_id", "screening_id"):
        verified.setdefault(screening_id, set()).add((form, pk))
    status = {}
    for s in screenings:
        forms = participant_forms(s)
        done = sum((form, record.pk) in verified.get(s.pk, set()) for form, record in forms)
        status[s.pk] = (done, len(forms))
    return status
