"""
Substudy queries: participants whose forms don't fit their substudy (nanopore/substudy.py).

  ss2_no_zonal                Substudy 2 without a Zonal Lab form (every Substudy 2 needs one)
  ss4_with_zonal              Substudy 4 with a Zonal Lab form (Substudy 4 never goes to the zonal lab)
  ss2_no_outcome              Substudy 2 enrolled without a treatment outcome
  ss4_with_outcome            Substudy 4 with a treatment outcome (only Substudy 2 is followed up)
  uncategorized_with_outcome  No Xpert result yet, but a treatment outcome is recorded

Usually either the Clinic Lab Xpert result is wrong (it decides the substudy), or the
Zonal Lab / Diagnosis form doesn't belong. The list page links to each form to fix it.
"""
from dataclasses import dataclass

from django.apps import apps
from django.db.models import Q

from nanopore.substudy import OUTCOMES, SUBSTUDY_2, SUBSTUDY_4, UNCATEGORIZED, substudy_q
from utils import access
from utils.access import can_see_queries, scope_queryset

HAS_OUTCOME = Q(diagnosis__tb_outcome2__in=OUTCOMES)


@dataclass(frozen=True)
class SubstudyQuery:
    key: str
    title: str
    help: str
    forms: tuple              # shown to users who work on queries of any of these forms
    q: Q


QUERIES = (
    SubstudyQuery(
        "ss2_no_zonal", "Substudy 2 without Zonal Lab",
        "Every Substudy 2 participant must have a Zonal Lab form. Add it, or correct the Clinic Lab "
        "Xpert result if the participant is not Substudy 2.",
        (access.ZONAL_LAB, access.CLINIC_LAB),
        substudy_q(SUBSTUDY_2) & Q(zonal_laboratory__isnull=True),
    ),
    SubstudyQuery(
        "ss4_with_zonal", "Substudy 4 with Zonal Lab",
        "Substudy 4 participants are not sent to the zonal lab. Correct the Clinic Lab Xpert result, "
        "or delete the Zonal Lab form if it should not be there.",
        (access.ZONAL_LAB, access.CLINIC_LAB),
        substudy_q(SUBSTUDY_4) & Q(zonal_laboratory__isnull=False),
    ),
    SubstudyQuery(
        "ss2_no_outcome", "Substudy 2 without outcome",
        "Enrolled Substudy 2 participants with no treatment outcome yet. Record the outcome on the "
        "Diagnosis form once it is known.",
        (access.DIAGNOSIS,),
        substudy_q(SUBSTUDY_2) & Q(enrollment__isnull=False) & ~HAS_OUTCOME,
    ),
    SubstudyQuery(
        "ss4_with_outcome", "Substudy 4 with outcome",
        "Only Substudy 2 participants are followed to a treatment outcome. Correct the Clinic Lab "
        "Xpert result, or remove the outcome from the Diagnosis form.",
        (access.DIAGNOSIS, access.CLINIC_LAB),
        substudy_q(SUBSTUDY_4) & HAS_OUTCOME,
    ),
    SubstudyQuery(
        "uncategorized_with_outcome", "Uncategorized with outcome",
        "These participants have no Xpert result yet (no Clinic Lab form, or no result on it), so "
        "their substudy is unknown, but a treatment outcome is recorded. Complete the Clinic Lab form.",
        (access.DIAGNOSIS, access.CLINIC_LAB),
        substudy_q(UNCATEGORIZED) & HAS_OUTCOME,
    ),
)
QUERIES_BY_KEY = {query.key: query for query in QUERIES}


def visible_queries(user):
    return [query for query in QUERIES if any(can_see_queries(user, form) for form in query.forms)]


def substudy_query_qs(user, query, zone_id=None, site_id=None):
    """Eligible screenings matching one substudy query, limited to the user's sites."""
    Screening = apps.get_model("nanopore", "Screening")
    qs = scope_queryset(user, Screening.objects.filter(eligible=True), "site").filter(query.q)
    if zone_id:
        qs = qs.filter(site__district__region__zone_id=zone_id)
    if site_id:
        qs = qs.filter(site_id=site_id)
    return qs


def substudy_query_counts(user, zone_id=None, site_id=None):
    """{key: count} for the queries the user can see."""
    return {
        query.key: substudy_query_qs(user, query, zone_id, site_id).count()
        for query in visible_queries(user)
    }

