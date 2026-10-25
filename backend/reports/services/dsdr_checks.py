"""
DS / DR checks: drug-susceptible vs drug-resistant answers that contradict each other.

Enrollment (previous episode): Q10d "Was it DR or DS TB" against the previous regimen.
Diagnosis (current episode, treatment started): the prescribed regimen against the
rifampicin result from Clinic Lab Xpert and Zonal Lab LPA, and against a previous DR
episode on Enrollment.
"""
from django.db.models import Q

from reports.services.date_issues import TO_FORM, DateCheck
from utils import access

E, C, Z, D = access.ENROLLMENT, access.CLINIC_LAB, access.ZONAL_LAB, access.DIAGNOSIS

TO_FORM = {**TO_FORM, E: "screening__enrollment__", Z: "screening__zonal_laboratory__"}

# DrDsTB: 1 DR, 2 DS. Regimen (Enrollment TreatmentRegimen and Diagnosis RegimenPrescribed share values):
# 1-2 DS regimens; 3 DR long, 4 DR short, 5 BPaL, 6 BPaLM, 7 individualized
DR, DS = 1, 2
DS_REGIMENS = [1, 2]
DR_REGIMENS = [3, 4, 5, 6, 7]
XPERT_RIF_NOT_DETECTED, XPERT_RIF_DETECTED = 1, 2
LPA_RESISTANT = [1, 4]  # Resistant, Resistance inferred
LPA_SUSCEPTIBLE = 2


def _conflict(key, form, label, q, a, b, b_form=""):
    """a and b are (lookup, label); b's lookup is on b_form when given."""
    path = TO_FORM[b_form] + b[0] if b_form else b[0]
    return DateCheck(key, form, label, q, a, (path, b[1]), b_form)


def build_checks():
    enr_regimen = ("tb_regimen", "Previous regimen")
    dx_regimen = ("tb_regimen", "Regimen prescribed")
    started = Q(tb_treatment=1)
    xpert = ("xpert_rif", "Xpert RIF")
    lpa = ("lpa1_rif", "LPA RIF")
    return [
        _conflict("enrollment_dr_on_ds_regimen", E, "Previous TB DR but DS regimen",
                  Q(dr_ds=DR, tb_regimen__in=DS_REGIMENS), ("dr_ds", "DR or DS"), enr_regimen),
        _conflict("enrollment_ds_on_dr_regimen", E, "Previous TB DS but DR regimen",
                  Q(dr_ds=DS, tb_regimen__in=DR_REGIMENS), ("dr_ds", "DR or DS"), enr_regimen),

        _conflict("diagnosis_xpert_rif_detected_ds_regimen", D, "Xpert RIF detected but DS regimen",
                  started & Q(tb_regimen__in=DS_REGIMENS, screening__clinic_laboratory__xpert_rif=XPERT_RIF_DETECTED),
                  dx_regimen, xpert, C),
        _conflict("diagnosis_xpert_rif_not_detected_dr_regimen", D, "Xpert RIF not detected but DR regimen",
                  started & Q(tb_regimen__in=DR_REGIMENS, screening__clinic_laboratory__xpert_rif=XPERT_RIF_NOT_DETECTED),
                  dx_regimen, xpert, C),
        _conflict("diagnosis_lpa_rif_resistant_ds_regimen", D, "LPA RIF resistant but DS regimen",
                  started & Q(tb_regimen__in=DS_REGIMENS, screening__zonal_laboratory__lpa1_rif__in=LPA_RESISTANT),
                  dx_regimen, lpa, Z),
        _conflict("diagnosis_lpa_rif_susceptible_dr_regimen", D, "LPA RIF susceptible but DR regimen",
                  started & Q(tb_regimen__in=DR_REGIMENS, screening__zonal_laboratory__lpa1_rif=LPA_SUSCEPTIBLE),
                  dx_regimen, lpa, Z),
        _conflict("diagnosis_previous_dr_ds_regimen", D, "Previously DR, now DS regimen",
                  started & Q(tb_regimen__in=DS_REGIMENS, screening__enrollment__dr_ds=DR),
                  dx_regimen, ("dr_ds", "Previous TB (Enrollment)"), E),
    ]
