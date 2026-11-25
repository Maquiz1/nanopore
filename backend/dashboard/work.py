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


@dataclass
class Tile:
    label: str
    url: str
    icon: str
    count: int = None      # None: an action, not a count
    note: str = ""
    tone: str = ""         # todo / done / info / action / warn

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


def work_groups(request):
    """[(title, [Tile])] for the user, groups with no tiles left out."""
    from nanopore.models.system_control import SystemControl
    from reports.services.substudy_queries import QUERIES_BY_KEY, substudy_query_qs

    user = request.user
    flags = AccessFlags(user)
    context = _context(request)
    missing = context.get("context_forms_report_total", {})
    groups = []
    # Read-only roles (coordinators, statisticians, reviewers) follow the work rather than do it
    does_the_work = any(flags.edit[form] for form in access.ALL_FORMS)
    # EDCS / TB-LIS queries are Dar es Salaam's: not for other zones' lab technicians
    other_zone_lab = (access.has_role(user, access.LABORATORY_TECHNICIAN) and not access.is_ctrl_lab(user)
                      and not flags.is_unscoped and set(flags.roles) == {access.LABORATORY_TECHNICIAN})

    # Start here: what the person does first
    start = []
    control = SystemControl.objects.first()
    if flags.edit.screening and (control is None or control.enable_new_screening):
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
                              missing.get(f"context_missing_{key}_count", 0)))
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
            queries.append(Tile(f"{label} queries", reverse(url_name), "fa-triangle-exclamation", context.get(key, 0)))
    if flags.queries[access.CTRL_ISOLATES]:
        queries.append(Tile("CTRL isolates: numbers to enter", reverse("reports:ctrl_isolates"), "fa-flask",
                            context.get("context_ctrl_isolates_report_total", 0), note="Other zones' isolates"))
        queries.append(Tile("CTRL work (Dar): Nanopore and LPA", reverse("reports:ctrl_dar_work"), "fa-dna",
                            context.get("context_ctrl_dar_work_total", 0), note="Dar es Salaam"))
    groups.append(("Queries to fix" if does_the_work else "Open queries", queries))

    # Follow-up: outcomes, TB-LIS, information lists
    follow = []
    if flags.queries[access.DIAGNOSIS]:
        due = substudy_query_qs(user, QUERIES_BY_KEY["ss2_no_outcome"]).count()
        follow.append(Tile("Substudy 2 outcomes to record", reverse("reports:substudy_queries", args=["ss2_no_outcome"]),
                           "fa-flag-checkered", due, note="Enrolled, no treatment outcome yet"))
    if flags.tblis_follow_up:
        follow.append(Tile("TB-LIS follow-up", reverse("nanopore:tblis-follow-up"), "fa-list-check",
                           context.get("context_tblis_follow_up_total", 0), note="Participants to follow up in TB-LIS"))
        follow.append(Tile("No DST (information)", reverse("reports:no_dst"), "fa-vial-circle-check",
                           context.get("context_no_dst_total", 0), tone="info", note="Positive cultures without DST"))
    if flags.tblis_upload or flags.tblis_follow_up:
        follow.append(last_upload_tile(can_upload=bool(flags.tblis_upload)))
    groups.append(("Follow-up", follow))

    return [(title, tiles) for title, tiles in groups if tiles]


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
