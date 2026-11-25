"""
Substudy 4 participants and the Zonal Lab.

The Zonal Lab follows Substudy 2 participants (clinic Xpert MTB detected). Zonal Lab
forms of Substudy 4 participants are set aside in the Recycle Bin with SET_ASIDE_REASON
(manage.py set_aside_substudy4_zonal): their EDCS/TBLIS record goes with them, they
leave every list, export, count and merge, and an admin can restore any of them from
the Recycle Bin if they are needed later. New ones are not started (only admins can).

Their lab numbers stay known here, so a TB-LIS upload lists those rows as set aside
instead of "TB-LIS rows not in EDCS".
"""
from nanopore.models import DeletedRecord, ZonalLaboratory
from nanopore.substudy import SUBSTUDY_4, clinic_lab_of, substudy_of, substudy_q

SET_ASIDE_REASON = "Substudy 4: not entered in Zonal Lab"


def substudy4_zonal_labs():
    """Zonal Lab forms of Substudy 4 participants (by their Clinic Lab Xpert MTB/RIF result)."""
    return ZonalLaboratory.objects.filter(substudy_q(SUBSTUDY_4, "screening__clinic_laboratory__"))


def is_substudy4(screening):
    return substudy_of(clinic_lab_of(screening)) == SUBSTUDY_4


def may_start_for(user, screening):
    """A new Zonal Lab form: not for Substudy 4, except by admins (to restore one by hand)."""
    from utils import access
    if not is_substudy4(screening):
        return True
    return getattr(user, "is_superuser", False) or access.has_role(user, access.ADMIN)


def set_aside_entries():
    return DeletedRecord.objects.filter(reason=SET_ASIDE_REASON, restored_at__isnull=True)


def set_aside_lab_numbers():
    """Lab numbers (and isolate numbers) of the Zonal Lab forms set aside and not restored."""
    numbers = set()
    for payload in set_aside_entries().values_list("payload", flat=True):
        for item in payload:
            if item.get("model") == "nanopore.zonallaboratory":
                for name in ("unique_lab_no", "isolate_unique_lab_no"):
                    value = (item.get("fields") or {}).get(name)
                    if value:
                        numbers.add(str(value).strip())
    return numbers
