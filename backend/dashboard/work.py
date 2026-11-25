"""
"Your work today": the dashboard panel that shows each person their own work first.

Tiles come from the same cached counts and access rules as the sidebar (so the two always
agree), and each tile shows only to the roles that work on it: a nurse sees her forms and
queries, a zonal lab her Zonal Lab work, CTRL its Dar es Salaam and isolate work, data
specialists and coordinators the queries of their zones, statisticians the exports.
A tile is a count that opens its list; a count of 0 shows as done.
"""
from dataclasses import dataclass

from django.urls import reverse
from django.utils import timezone

from utils import access
from utils.access import AccessFlags

STALE_UPLOAD_DAYS = 30  # a TB-LIS upload older than this is flagged
WAIT_DAYS = 30          # a missing form or isolate number waiting longer than this is pointed out
OUTCOME_DAYS = 182      # an outcome is due about 6 months after enrollment


@dataclass
class Tile:
    label: str
    url: str
    icon: str
    count: int = None      # None: an action, not a count
    note: str = ""
    tone: str = ""         # todo / done / info / action / warn
    snapshot: tuple = None  # (form, query or None for all) in the daily query snapshot
    waiting: int = None     # of count, how many have waited long (see waiting_note)
    waiting_note: str = ""
    change: int = None      # count now minus at the last visit

    def __post_init__(self):
        if not self.tone:
            self.tone = "action" if self.count is None else ("todo" if self.count else "done")


def _context(request):
    """The sidebar's counts (context processors, cached per user for a few minutes)."""
    from reports.context_processors.form_missing.forms_context import forms_report_total
    from reports.context_processors.form_queries.clinic_laboratory_context import clinic_report_total
    from reports.context_processors.form_queries.diagnosis_context import diagnosis_report_total
    from reports.context_processors.form_queries.edcs_tblis_laboratory_context_processor import edcs_tblis_report_total
    from reports.context_processors.form_queries.enrollment_context import enrollment_report_total
    from reports.context_processors.form_queries.regimen_context_processor import regimen_report_total
    from reports.context_processors.form_queries.screening_context import screening_report_total
    from reports.context_processors.form_queries.zonal_laboratory_context import zonal_report_total
    from reports.context_processors.tblis_follow_up_context import tblis_follow_up_total
    context = {}
    for processor in (forms_report_total, screening_report_total, enrollment_report_total, clinic_report_total,
                      diagnosis_report_total, regimen_report_total, zonal_report_total, edcs_tblis_report_total,
                      tblis_follow_up_total):
        context.update(processor(request))
    return context


def work_groups(request, compare_to=None):
    """([(title, [Tile])], since) for the user, groups with no tiles left out. compare_to: the last visit's date."""
    from nanopore.models.system_control import SystemControl
    from reports.services.missing_form_dq_counts import get_missing_forms_counts
    from reports.services.substudy_queries import QUERIES_BY_KEY, substudy_query_qs

    user = request.user
    flags = AccessFlags(user)
    context = _context(request)
    missing = context.get("context_forms_report_total", {})
    old_missing = get_missing_forms_counts(user, screened_before=_days_ago(WAIT_DAYS))
    groups = []
    # Read-only roles (coordinators, statisticians, reviewers) follow the work rather than do it
    does_the_work = any(flags.edit[form] for form in access.ALL_FORMS)
    # EDCS / TB-LIS queries are Dar es Salaam's: not for other zones' lab technicians
    other_zone_lab = (access.has_role(user, access.LABORATORY_TECHNICIAN) and not access.is_ctrl_lab(user)
                      and not flags.is_unscoped and set(flags.roles) == {access.LABORATORY_TECHNICIAN})

    # Start here: what the person does first
    start = []
    if flags.add.screening:
        start.append(Tile("New screening", reverse("nanopore:screening-create"), "fa-user-plus"))
    if flags.view.screening:
        start.append(Tile("Find a participant", reverse("nanopore:form-status-list"), "fa-magnifying-glass"))
    if flags.exports:
        start.append(Tile("Download data", reverse("reports:data-export"), "fa-file-arrow-down"))
        start.append(Tile("Data dictionary", reverse("reports:codebook"), "fa-book"))
    groups.append(("Start here", start))

    # Forms not filled in yet, for the forms the person works on
    forms = []
    for key, form, label, icon in (("enrollment", access.ENROLLMENT, "Enrollment", "fa-id-card"),
                                   ("clinic", access.CLINIC_LAB, "Clinic Lab", "fa-vial"),
                                   ("zonal", access.ZONAL_LAB, "Zonal Lab", "fa-microscope"),
                                   ("diagnosis", access.DIAGNOSIS, "Diagnosis", "fa-stethoscope"),
                                   ("regimen", access.REGIMEN, "Regimen changes", "fa-pills")):
        if flags.queries[form]:
            forms.append(Tile(f"{label} forms missing", reverse("reports:missing_form_details_queries", args=[key]), icon,
                              missing.get(f"context_missing_{key}_count", 0), snapshot=("missing_forms", form),
                              waiting=old_missing.get(f"missing_{key}_count", 0), waiting_note=f"screened over {WAIT_DAYS} days ago"))
    groups.append(("Forms to fill in" if does_the_work else "Forms not filled in yet", forms))

    # Queries to fix on the forms the person works on
    queries = []
    for form, label, key, url_name in (
            (access.SCREENING, "Screening", "context_screening_report_total", "reports:screening_quality_report"),
            (access.ENROLLMENT, "Enrollment", "context_enrollment_report_total", "reports:enrollment_quality_report"),
            (access.CLINIC_LAB, "Clinic Lab", "context_clinic_report_total", "reports:clinic_quality_report"),
            (access.ZONAL_LAB, "Zonal Lab", "context_zonal_report_total", "reports:zonal_quality_report"),
            (access.DIAGNOSIS, "Diagnosis", "context_diagnosis_report_total", "reports:diagnosis_quality_report"),
            (access.REGIMEN, "Regimen", "context_regimen_report_total", "reports:regimen_quality_report"),
            (access.EDCS_TBLIS, "EDCS / TB-LIS", "context_edcs_tblis_report_total", "reports:edcs_tblis_quality_report")):
        if flags.queries[form] and not (form == access.EDCS_TBLIS and other_zone_lab):
            queries.append(Tile(f"{label} queries", reverse(url_name), "fa-triangle-exclamation", context.get(key, 0),
                                snapshot=(form, None)))
    if flags.queries[access.CTRL_ISOLATES]:
        queries.append(Tile("CTRL isolates: numbers to enter", reverse("reports:ctrl_isolates"), "fa-flask",
                            context.get("context_ctrl_isolates_report_total", 0), note="Other zones' isolates",
                            snapshot=("ctrl_isolates", None), waiting=isolates_waiting(user),
                            waiting_note=f"isolate sent over {WAIT_DAYS} days ago, no number"))
        queries.append(Tile("CTRL work (Dar): Nanopore and LPA", reverse("reports:ctrl_dar_work"), "fa-dna",
                            context.get("context_ctrl_dar_work_total", 0), note="Dar es Salaam", snapshot=("ctrl_dar_work", None)))
    groups.append(("Queries to fix" if does_the_work else "Open queries", queries))

    # Follow-up: outcomes, TB-LIS, information lists
    follow = []
    if flags.queries[access.DIAGNOSIS]:
        due = substudy_query_qs(user, QUERIES_BY_KEY["ss2_no_outcome"])
        follow.append(Tile("Substudy 2 outcomes to record", reverse("reports:substudy_queries", args=["ss2_no_outcome"]),
                           "fa-flag-checkered", due.count(), note="Enrolled, no treatment outcome yet",
                           waiting=due.filter(enrollment__enrollment_date__lt=_days_ago(OUTCOME_DAYS)).count(),
                           waiting_note="enrolled over 6 months ago"))
    if flags.tblis_follow_up:
        follow.append(Tile("TB-LIS follow-up", reverse("nanopore:tblis-follow-up"), "fa-list-check",
                           context.get("context_tblis_follow_up_total", 0), note="Participants to follow up in TB-LIS"))
        follow.append(Tile("No DST (information)", reverse("reports:no_dst"), "fa-vial-circle-check",
                           context.get("context_no_dst_total", 0), tone="info", note="Positive cultures without DST"))
        follow.append(Tile("Nanopore failed (information)", reverse("reports:nanopore_failed"), "fa-dna",
                           context.get("context_nanopore_failed_total", 0), tone="info", note="Runs all failed so far: re-run owed"))
    if flags.tblis_upload or flags.tblis_follow_up:
        follow.append(last_upload_tile(can_upload=bool(flags.tblis_upload)))
    groups.append(("Follow-up", follow))

    groups = [(title, tiles) for title, tiles in groups if tiles]
    since = add_changes(user, [tile for _, tiles in groups for tile in tiles], compare_to)
    return groups, since


def last_upload_tile(can_upload):
    from nanopore.models import TblisUploadBatch
    batch = TblisUploadBatch.objects.order_by("-created_at").first()
    url = reverse("nanopore:tblis-raw-upload" if can_upload else "nanopore:tblis-follow-up")
    if batch is None:
        return Tile("Last TB-LIS upload", url, "fa-cloud-arrow-up", tone="warn", note="No upload yet")
    days = (timezone.now() - batch.created_at).days
    note = "today" if days == 0 else f"{days} day{'s' if days != 1 else ''} ago"
    return Tile("Last TB-LIS upload", url, "fa-cloud-arrow-up", tone="warn" if days > STALE_UPLOAD_DAYS else "info",
                note=f"{timezone.localtime(batch.created_at):%d %b %Y} · {note}"
                     + (f" (older than {STALE_UPLOAD_DAYS} days)" if days > STALE_UPLOAD_DAYS else ""))


def _days_ago(days):
    return timezone.localdate() - timezone.timedelta(days=days)


def isolates_waiting(user):
    """Other zones' isolates sent to CTRL over WAIT_DAYS ago that still have no isolate number."""
    from reports.services.zonal_dq.ctrl import get_ctrl_isolates_queryset
    from reports.services.zonal_dq.filters import get_ctrl_isolate_filters
    missing_number = get_ctrl_isolate_filters()["missing_isolate_unique_lab_no"]
    return get_ctrl_isolates_queryset(user).filter(missing_number, isolate_date__lt=_days_ago(WAIT_DAYS)).count()


# --- Since your last visit ---------------------------------------------------------------

def remember_visit(user):
    """The date of the last visit before today (None the first time); today becomes the new one."""
    profile = getattr(user, "profile", None)
    if profile is None:
        return None
    today = timezone.localdate()
    if profile.dashboard_seen_on != today:
        profile.dashboard_compare_to = profile.dashboard_seen_on
        profile.dashboard_seen_on = today
        profile.save(update_fields=["dashboard_seen_on", "dashboard_compare_to"])
    return profile.dashboard_compare_to


def _snapshot_totals(user, on_date):
    """{(form, query): count} in the user's sites from the daily query snapshot taken on or before on_date."""
    from django.db.models import Sum
    from reports.models import QuerySnapshotRun
    from reports.services.query_snapshot import ADMIN_ONLY
    run = QuerySnapshotRun.objects.filter(snapshot_date__lte=on_date).order_by("-snapshot_date").first()
    if run is None:
        return None, None
    sites = access.get_accessible_sites(user)
    all_sites = run.counts.filter(site__isnull=True)
    mine = all_sites if sites is None else run.counts.filter(site_id__in=list(sites))
    totals = {}
    for source, scope in (("mine", mine), ("all", all_sites)):
        for row in scope.values("form", "query").annotate(n=Sum("count")):
            if (row["form"], row["query"]) in ADMIN_ONLY and not access.is_unscoped(user):
                continue
            totals[(source, row["form"], row["query"])] = row["n"]
    return totals, run.snapshot_date


def add_changes(user, tiles, compare_to):
    """Each counted tile's change since the last visit; returns {"date": ..., "change": total} or None."""
    if compare_to is None:
        return None
    totals, snapshot_date = _snapshot_totals(user, compare_to)
    if totals is None:
        return None
    # CTRL covers every zone for its own lists, whatever its site assignment
    every_zone = access.is_ctrl_lab(user)
    overall = 0
    for tile in tiles:
        if tile.snapshot is None or tile.count is None:
            continue
        form, query = tile.snapshot
        source = "all" if every_zone and form in ("ctrl_isolates", "ctrl_dar_work", "edcs_tblis") else "mine"
        if not any(f == form for (_, f, _q) in totals):
            continue  # not counted in that snapshot yet (a newer list): nothing to compare with
        before = sum(n for (src, f, q), n in totals.items() if src == source and f == form and (query is None or q == query))
        tile.change = tile.count - before
        overall += tile.change
    return {"date": snapshot_date, "change": overall}
