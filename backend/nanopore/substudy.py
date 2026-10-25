"""
The one definition of a participant's substudy, from the Clinic Lab form.

  Substudy 2     Xpert MTB/RIF conducted = Yes and MTB detected (trace, very low,
                 low, medium or high).
  Substudy 4     Xpert conducted = Yes and MTB not detected / invalid / error /
                 no result, OR Xpert not conducted.
  Uncategorized  no Xpert answer yet: no Clinic Lab form, or Xpert conducted =
                 Yes without a result.

The three groups never overlap and together cover every participant. Use the
helpers below everywhere; don't re-type the option ids.

`prefix` is the lookup path from the queried model to the Clinic Lab:
  Screening                                -> "clinic_laboratory__" (default)
  Enrollment, Diagnosis, Zonal Lab, EDCS   -> "screening__clinic_laboratory__"
  ClinicLaboratory itself                  -> ""
"""
from django.db.models import Case, CharField, Q, Value, When

# Option ids (options.XpertMTB / options.YesNo primary keys).
YES, NO = 1, 2
XPERT_DETECTED = [2, 3, 4, 5, 6]        # Detected: trace, very low, low, medium, high
XPERT_NOT_DETECTED = [1, 7, 8, 9]       # Not detected, Invalid, Error (code), No result
XPERT_ERROR = 8                         # "error,code": an error code must be recorded

# Treatment outcomes (options.TBTreatmentOutcome, Diagnosis.tb_outcome2): Cured, Treatment
# completed, Treatment failed, Died, Lost to follow-up, Not evaluated. A participant has
# completed the study once one is recorded; only Substudy 2 is followed to an outcome.
OUTCOMES = [1, 2, 3, 4, 5, 6]

SUBSTUDY_2 = "Substudy 2"
SUBSTUDY_4 = "Substudy 4"
UNCATEGORIZED = "Uncategorized"
SUBSTUDIES = (SUBSTUDY_2, SUBSTUDY_4, UNCATEGORIZED)

# URL/filter keys used by the list pages (?substudy=substudy2 ...).
SUBSTUDY_KEYS = {"substudy2": SUBSTUDY_2, "substudy4": SUBSTUDY_4, "uncategorized": UNCATEGORIZED}

DEFAULT_PREFIX = "clinic_laboratory__"


def substudy_q(substudy, prefix=DEFAULT_PREFIX):
    """Q selecting the participants of one substudy."""
    conducted = f"{prefix}xpert_mtb_rif_conducted"
    result = f"{prefix}xpert_mtb"
    if substudy == SUBSTUDY_2:
        return Q(**{conducted: YES, f"{result}__in": XPERT_DETECTED})
    if substudy == SUBSTUDY_4:
        return Q(**{conducted: YES, f"{result}__in": XPERT_NOT_DETECTED}) | Q(**{conducted: NO})
    if substudy == UNCATEGORIZED:
        return Q(**{conducted: YES, f"{result}__isnull": True}) | Q(**{f"{conducted}__isnull": True})
    raise ValueError(f"Unknown substudy: {substudy!r}")


def substudy_case(prefix=DEFAULT_PREFIX):
    """Annotation giving each row its substudy name ("Substudy 2", "Substudy 4", "Uncategorized")."""
    return Case(
        When(substudy_q(SUBSTUDY_2, prefix), then=Value(SUBSTUDY_2)),
        When(substudy_q(SUBSTUDY_4, prefix), then=Value(SUBSTUDY_4)),
        default=Value(UNCATEGORIZED),
        output_field=CharField(),
    )


def substudy_of(clinic_lab):
    """Substudy of one participant from their ClinicLaboratory (or None when there is none)."""
    if clinic_lab is None:
        return UNCATEGORIZED
    conducted = clinic_lab.xpert_mtb_rif_conducted_id
    result = clinic_lab.xpert_mtb_id
    if conducted == YES and result in XPERT_DETECTED:
        return SUBSTUDY_2
    if (conducted == YES and result in XPERT_NOT_DETECTED) or conducted == NO:
        return SUBSTUDY_4
    return UNCATEGORIZED


def clinic_lab_of(obj):
    """The ClinicLaboratory linked to a Screening (or to a record pointing at a Screening)."""
    screening = getattr(obj, "screening", obj)
    try:
        return screening.clinic_laboratory
    except Exception:  # RelatedObjectDoesNotExist
        return None
