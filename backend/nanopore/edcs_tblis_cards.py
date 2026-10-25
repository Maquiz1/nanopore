"""
The cards on the EDCS / TB-LIS page: what each one counts.

The number on a card, the list it opens and its Excel export all come from
card_queryset(), so the three always agree.

  Dar es Salaam (CTRL) records are the ones matched with TB-LIS uploads; they are
  recognised by their PID prefix. "Merged" / "not in TB-LIS" refer to the latest
  TB-LIS upload. Substudy comes from the Clinic Lab (nanopore/substudy.py).
"""
from dataclasses import dataclass

from django.apps import apps
from django.db.models import Q

from nanopore.substudy import SUBSTUDY_2, SUBSTUDY_4, UNCATEGORIZED, substudy_case

CTRL_PREFIXES = ["DF_TZ_SS2_14", "DF_TZ_SS2_15", "DF_TZ_SS2_16", "DF_TZ_SS2_17", "DF_TZ_SS2_18", "DF_TZ_SS2_19"]
TO_CLINIC_LAB = "screening__clinic_laboratory__"


def ctrl_q():
    q = Q()
    for prefix in CTRL_PREFIXES:
        q |= Q(screening__pid__startswith=prefix)
    return q


@dataclass(frozen=True)
class Card:
    key: str
    label: str
    source: str           # "zonal" (Zonal Lab), "edcs" (EDCS/TB-LIS records) or "tblis" (raw upload rows)
    tone: str = "info"    # info / good / warn / bad
    share_of: str = ""    # show the count as a % of this card


SECTIONS = (
    ("Overview", "All zonal lab records and the latest TB-LIS upload", (
        Card("total_edcs", "Zonal Lab records", "zonal"),
        Card("ctrl", "Dar es Salaam (CTRL)", "zonal", share_of="total_edcs"),
        Card("other_zones", "Other zones", "zonal", share_of="total_edcs"),
        Card("total_tblis", "TB-LIS rows in latest upload", "tblis"),
        Card("tblis_not_in_edcs", "TB-LIS rows not in EDCS", "tblis", tone="bad"),
        Card("missing_culture", "EDCS records missing culture performed", "edcs", tone="warn"),
    )),
    ("Dar es Salaam: merged with TB-LIS", "CTRL records found in the latest TB-LIS upload", (
        Card("merged", "Merged", "edcs", tone="good", share_of="ctrl"),
        Card("merged_substudy2", "Substudy 2", "edcs", share_of="merged"),
        Card("merged_substudy4", "Substudy 4", "edcs", share_of="merged"),
        Card("merged_uncategorized", "Uncategorized", "edcs", share_of="merged"),
        Card("merged_missing_culture", "Culture performed missing", "edcs", tone="warn"),
    )),
    ("Dar es Salaam: not in TB-LIS", "CTRL records the latest TB-LIS upload doesn't have yet", (
        Card("edcs_not_in_tblis", "Not in TB-LIS", "edcs", tone="warn", share_of="ctrl"),
        Card("edcs_not_in_tblis_substudy2", "Substudy 2", "edcs", share_of="edcs_not_in_tblis"),
        Card("edcs_not_in_tblis_substudy4", "Substudy 4", "edcs", share_of="edcs_not_in_tblis"),
        Card("edcs_not_in_tblis_uncategorized", "Uncategorized", "edcs", share_of="edcs_not_in_tblis"),
    )),
    ("Other zones", "Zonal Lab records outside Dar es Salaam (entered on the form, not from TB-LIS)", (
        Card("other_zones_substudy2", "Substudy 2", "zonal", share_of="other_zones"),
        Card("other_zones_substudy4", "Substudy 4", "zonal", share_of="other_zones"),
        Card("other_zones_uncategorized", "Uncategorized", "zonal", share_of="other_zones"),
        Card("other_zones_missing_culture", "Culture performed missing", "zonal", tone="warn"),
    )),
)
CARDS = {card.key: card for _, _, cards in SECTIONS for card in cards}
DEFAULT_CARD = "merged"

SUBSTUDY_SUFFIX = {"substudy2": SUBSTUDY_2, "substudy4": SUBSTUDY_4, "uncategorized": UNCATEGORIZED}


def latest_batch():
    return apps.get_model("nanopore", "TblisUploadBatch").objects.first()


def card_queryset(key, batch=None):
    """Records behind one card, before limiting to the user's sites. batch: the latest upload (looked up if None)."""
    card = CARDS.get(key) or CARDS[DEFAULT_CARD]
    key = card.key
    batch = batch if batch is not None else latest_batch()
    TblisRawData = apps.get_model("nanopore", "TblisRawData")
    batch_rows = TblisRawData.objects.filter(upload_batch=batch) if batch else TblisRawData.objects.none()

    if card.source == "tblis":
        qs = batch_rows
        if key == "tblis_not_in_edcs":
            ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")
            qs = qs.exclude(labno__in=ZonalLaboratory.objects.values("unique_lab_no"))
        return qs.order_by("labno")

    model = apps.get_model("nanopore", "ZonalLaboratory" if card.source == "zonal" else "EdcsTblisZonal")
    qs = model.objects.select_related(
        "screening__site__district__region__zone",
        "screening__clinic_laboratory__xpert_mtb_rif_conducted",
        "screening__clinic_laboratory__xpert_mtb",
        "culture_performed",
    ).annotate(substudy_group=substudy_case(TO_CLINIC_LAB))

    if key == "ctrl":
        qs = qs.filter(ctrl_q())
    elif key.startswith("other_zones"):
        qs = qs.exclude(ctrl_q())
    elif key.startswith("merged"):
        qs = qs.filter(ctrl_q(), unique_lab_no__in=batch_rows.filter(is_merged=True).values("labno"))
    elif key.startswith("edcs_not_in_tblis"):
        qs = qs.filter(ctrl_q()).exclude(unique_lab_no__in=batch_rows.values("labno"))

    suffix = key.rsplit("_", 1)[-1]
    if suffix in SUBSTUDY_SUFFIX:
        qs = qs.filter(substudy_group=SUBSTUDY_SUFFIX[suffix])
    if key.endswith("missing_culture"):
        qs = qs.filter(culture_performed__isnull=True)

    return qs.order_by("screening__site__district__region__zone__name", "screening__site__name", "screening__pid")
