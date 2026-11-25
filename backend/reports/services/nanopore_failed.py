"""
Nanopore failed (information): participants whose sequencing so far has only failed runs,
so a re-run may still be owed. Not queries: the record is complete (21(e) = Failed).

Tabs:
  since    recorded with runs (from 25 Nov 2026): every run failed so far
  before   entered before runs existed, saved as "Failed"
  closed   the team decided no re-run is planned (with the reason); they leave the other tabs
The badge counts since + before. Longest wait first.
"""
from django.db.models import Count, F, Max
from django.db.models.functions import Coalesce

from nanopore.models import ZonalLaboratory
from nanopore.nanopore_runs import FAILED_RESULT_VALUE
from nanopore.zonal_rules import LAB_NUMBER_ONLY_Q, ctrl_dar_records
from utils import access

YES = 1
TABS = (("since", "Since runs (from 25 Nov 2026)"), ("before", "Entered before runs"), ("closed", "No re-run planned"))


def _failed(user):
    labs = ZonalLaboratory.objects.filter(nanopore_done=YES, nanopore_results__value=FAILED_RESULT_VALUE)
    if not (getattr(user, "is_superuser", False) or access.is_unscoped(user) or access.is_ctrl_lab(user)):
        labs = access.scope_queryset(user, labs, "screening__site")
    return labs.select_related("screening__site__district__region__zone").annotate(
        runs=Count("nanopore_runs"), last_run=Coalesce(Max("nanopore_runs__run_date"), F("nanopore_sequencing_date")))


def nanopore_failed_records(user, tab=None, zone_id=None, site_id=None):
    """The tab's records (all open ones, since + before, when tab is None)."""
    labs = _failed(user)
    if zone_id:
        labs = labs.filter(screening__site__district__region__zone_id=zone_id)
    if site_id:
        labs = labs.filter(screening__site_id=site_id)
    if tab == "closed":
        labs = labs.filter(nanopore_rerun_not_planned=True)
    else:
        labs = labs.filter(nanopore_rerun_not_planned=False)
        if tab == "since":
            labs = labs.filter(runs__gt=0)
        elif tab == "before":
            labs = labs.filter(runs=0)
    return labs.order_by(F("last_run").asc(nulls_first=True), "screening__pid")


def nanopore_failed_counts(user, zone_id=None, site_id=None):
    return {key: nanopore_failed_records(user, key, zone_id, site_id).count() for key, _ in TABS}


def zones_and_sites(user):
    """The zones and sites of the user's failed records, for the filters."""
    labs = _failed(user)
    zones = dict(labs.order_by("screening__site__district__region__zone__name").values_list(
        "screening__site__district__region__zone_id", "screening__site__district__region__zone__name").distinct())
    sites = dict(labs.order_by("screening__site__name").values_list("screening__site_id", "screening__site__name").distinct())
    return zones, sites


def may_close(user, lab):
    """Who may decide that no re-run is planned: whoever may change that record's Nanopore answers."""
    if lab.screening_id and ZonalLaboratory.objects.filter(pk=lab.pk).filter(LAB_NUMBER_ONLY_Q).exists():
        return ctrl_dar_records(user, write=True).filter(pk=lab.pk).exists()  # Dar es Salaam: CTRL's Nanopore form
    if not access.can_edit(user, access.ZONAL_LAB):
        return False
    return access.writable_queryset(user, ZonalLaboratory.objects.filter(pk=lab.pk), "screening__site").exists()
