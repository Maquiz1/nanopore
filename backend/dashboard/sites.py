"""
"Sites at a glance": the dashboard's site-by-site comparison, for people who follow several
sites (coordinators, data specialists and managers, statisticians, reviewers, admins).

Per site: Substudy 2 enrollment against the site's target, Zonal Lab forms and treatment
outcomes of those participants, and the open queries and missing forms from the latest
daily query snapshot. A site is flagged when it is well behind the others, so attention
goes where it is needed:
  * enrollment: its Substudy 2 target reached BEHIND_POINTS percentage points less than overall
  * queries: more open queries per enrolled participant than QUERY_RATIO times the overall rate
"""
from dataclasses import dataclass, field

from django.db.models import Count, Q, Sum

from nanopore.substudy import OUTCOMES, SUBSTUDY_2, substudy_q
from utils import access

BEHIND_POINTS = 20
QUERY_RATIO = 2


@dataclass
class SiteRow:
    site_id: int
    name: str
    zone: str
    target: int
    enrolled: int = 0
    zonal: int = 0
    outcomes: int = 0
    queries: int = 0
    missing: int = 0
    flags: list = field(default_factory=list)

    @staticmethod
    def _pct(part, whole):
        return round(part / whole * 100) if whole else None

    @property
    def enrolled_pct(self):
        return self._pct(self.enrolled, self.target)

    @property
    def zonal_pct(self):
        return self._pct(self.zonal, self.enrolled)

    @property
    def outcomes_pct(self):
        return self._pct(self.outcomes, self.enrolled)


def shows_sites(user):
    """For those who follow several sites."""
    sites = access.get_accessible_sites(user)
    return access.has_feature(user, access.REPORTS) and (sites is None or len(list(sites)) > 1)


def sites_at_a_glance(user):
    """(rows ordered by need, the snapshot date the queries come from) for the user's sites."""
    from locations.models import Site
    from nanopore.models import Enrollment
    from reports.models import QuerySnapshotRun
    from reports.services.query_snapshot import ADMIN_ONLY
    from utils.access import can_see_queries
    from utils.permissions import filter_queryset_by_user_role

    sites = filter_queryset_by_user_role(user, Site.objects.filter(is_active=True), site_field="id").filter(
        screening__isnull=False).distinct().select_related("district__region__zone")
    rows = {s.pk: SiteRow(s.pk, s.name, s.district.region.zone.name if s.district and s.district.region else "",
                          s.substudy2Target or 0) for s in sites}
    if not rows:
        return [], None

    # Substudy 2 enrolled participants, their Zonal Lab forms and treatment outcomes
    enrolled = Enrollment.objects.filter(substudy_q(SUBSTUDY_2, "screening__clinic_laboratory__"),
                                         screening__site_id__in=rows)
    for row in enrolled.values("screening__site_id").annotate(
            n=Count("pk"),
            zonal=Count("pk", filter=Q(screening__zonal_laboratory__isnull=False)),
            outcomes=Count("pk", filter=Q(screening__diagnosis__tb_outcome2__in=OUTCOMES))):
        site = rows[row["screening__site_id"]]
        site.enrolled, site.zonal, site.outcomes = row["n"], row["zonal"], row["outcomes"]

    # Open queries and missing forms: the latest daily snapshot, for the forms the user follows
    run = QuerySnapshotRun.objects.order_by("-snapshot_date").first()
    if run is not None:
        counts = run.counts.filter(site_id__in=rows).values("site_id", "form", "query").annotate(n=Sum("count"))
        for row in counts:
            form, query = row["form"], row["query"]
            if (form, query) in ADMIN_ONLY and not access.is_unscoped(user):
                continue
            if form == "missing_forms":
                if can_see_queries(user, query):
                    rows[row["site_id"]].missing += row["n"]
            elif can_see_queries(user, access.CTRL_ISOLATES if form == "ctrl_dar_work" else form):
                rows[row["site_id"]].queries += row["n"]

    # Flags: well behind the overall figures
    all_rows = list(rows.values())
    target = sum(r.target for r in all_rows)
    overall_pct = round(sum(r.enrolled for r in all_rows) / target * 100) if target else None
    enrolled_total = sum(r.enrolled for r in all_rows)
    query_rate = sum(r.queries for r in all_rows) / enrolled_total if enrolled_total else 0
    for r in all_rows:
        if overall_pct is not None and r.enrolled_pct is not None and r.enrolled_pct < overall_pct - BEHIND_POINTS:
            r.flags.append(("Enrollment behind", f"{r.enrolled_pct}% of target, overall {overall_pct}%"))
        if query_rate and r.enrolled and r.queries / r.enrolled > QUERY_RATIO * query_rate:
            r.flags.append(("Many queries", f"{r.queries / r.enrolled:.1f} per enrolled participant, overall {query_rate:.1f}"))

    ordered = sorted(all_rows, key=lambda r: (-len(r.flags), -(r.queries + r.missing), r.zone, r.name))
    return ordered, (run.snapshot_date if run else None)
