"""
Zonal Lab data entry rules.

Dar es Salaam (CTRL) zonal labs report their results through TBLIS: the TBLIS
upload merges them into the EDCS/TBLIS record by lab number. So for Dar es Salaam
participants the Zonal Lab form only takes the Unique Lab Number and Remarks. What
TBLIS can't supply has its own CTRL form (nanopore/forms/laboratory/zonal/ctrl_dar_forms.py):
the isolate number, Nanopore and the LPA band checkboxes. Every other zone enters the
full form, except CTRL_FIELDS: an isolate sent to CTRL gets its number there
(the CTRL isolate form), and the phenotypic DST comes from the TBLIS upload by
that number, because other zones' lab numbers are not in TBLIS.
"""
from django.apps import apps
from django.db.models import Q

from common.labels.laboratory.zonal.zonal_labels import ZONAL_LABELS
from utils.access import is_ctrl_lab, scope_queryset, writable_queryset

LAB_NUMBER_ONLY_ZONE = "dar es salaam"

# Zonal Lab records of lab-number-only participants.
LAB_NUMBER_ONLY_Q = Q(screening__site__district__region__zone__name__iexact=LAB_NUMBER_ONLY_ZONE)

# Fields of the Dar es Salaam Zonal Lab form
LAB_NUMBER_ONLY_FIELDS = ("screening", "unique_lab_no", "remarks")
NANOPORE_PREFIXES = ("nano", "epi_to_me", "sequencing_")

CTRL_FIELDS = (
    "isolate_unique_lab_no",
    "phenotypic_performed",
    "first_line_dst_performed", "first_line_dst_performed_date", "first_line_dst_results_date",
    "rifampicin", "isoniazid", "ethambutol",
    "second_line_dst_performed", "second_line_dst_performed_date", "second_line_dst_results_date",
    "levofloxacin", "bedaquiline", "linezolid", "clofazimine", "cycloserine", "delamanid", "pretomanid",
)


def ctrl_answers(record, names=CTRL_FIELDS):
    """(label, value) of the filled CTRL fields, for showing them read only."""
    return [(ZONAL_LABELS.get(name, name), getattr(record, name)) for name in names
            if getattr(record, name) not in (None, "")]


def _limit_ctrl(user, qs, write):
    """Superusers first: the query snapshot's system user is unsaved, so it has no groups to look up."""
    if getattr(user, "is_superuser", False) or is_ctrl_lab(user):
        return qs
    return (writable_queryset if write else scope_queryset)(user, qs, "screening__site")


def ctrl_records(user, write=False):
    """Other zones' Zonal Lab forms: CTRL covers every zone, anyone else their assigned sites."""
    ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")
    qs = ZonalLaboratory.objects.exclude(LAB_NUMBER_ONLY_Q).select_related("screening__site__district__region__zone")
    return _limit_ctrl(user, qs, write)


def ctrl_dar_records(user, write=False):
    """Dar es Salaam Zonal Lab forms CTRL's own forms can open."""
    ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")
    qs = ZonalLaboratory.objects.filter(LAB_NUMBER_ONLY_Q).select_related("screening__site__district__region__zone")
    return _limit_ctrl(user, qs, write)


def lpa_lines_done(screening):
    """(first-line, second-line) LPA done, as the TBLIS upload put them on the EDCS/TBLIS record."""
    EdcsTblisZonal = apps.get_model("nanopore", "EdcsTblisZonal")
    record = EdcsTblisZonal.objects.filter(screening=screening).first() if screening else None
    return (bool(record and record.first_line_lpa_id == 1), bool(record and record.second_line_lpa_id == 1))


def is_lab_number_only(screening):
    """True when this participant's Zonal Lab form only takes the Unique Lab Number."""
    site = getattr(screening, "site", None)
    region = getattr(getattr(site, "district", None), "region", None)
    zone = getattr(region, "zone", None)
    return bool(zone and zone.name.strip().lower() == LAB_NUMBER_ONLY_ZONE)


def viewable_edcs_records(user):
    """EDCS/TBLIS records the user may open read only: CTRL covers every zone, others their assigned sites."""
    from utils.access import EDCS_TBLIS, can_view, scope_queryset
    EdcsTblisZonal = apps.get_model("nanopore", "EdcsTblisZonal")
    qs = EdcsTblisZonal.objects.all()
    if getattr(user, "is_superuser", False) or is_ctrl_lab(user):
        return qs
    if not can_view(user, EDCS_TBLIS):
        return qs.none()
    return scope_queryset(user, qs, "screening__site")

