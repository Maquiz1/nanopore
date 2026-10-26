"""
Sunday-night emails (scheduled in src/settings.py, sent by notifications/tasks.py).

1. Open queries: per site, the queries on each form and the forms not filled yet,
   from a snapshot taken just before sending (the same counts as the Query trends
   page). Each person gets the sites they are assigned to (zones -> all their sites;
   reviewers every site) and the forms they work on. Nobody gets an empty email.

2. Treatment without outcome: Substudy 2 participants who started treatment but
   have no outcome yet, sent to the same staff, each for the zones/sites they cover.

People listed under Administration > Email recipients get the all-sites copy of both.
"""
from collections import defaultdict

from django.apps import apps
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from nanopore.substudy import OUTCOMES, SUBSTUDY_2, substudy_q
from notifications.mail import absolute_url, already_sent, report_copies, send_email
from reports.services.query_snapshot import ADMIN_ONLY, FORM_LABELS, take_snapshot
from utils import access

QUERIES_TASK = "weekly_queries"
OUTCOMES_TASK = "weekly_treatment_outcomes"

# Who receives the weekly emails (each for the zones/sites assigned to them)
QUERY_ROLES = {access.NURSE, access.CLINICIAN, access.LABORATORY_TECHNICIAN, access.COORDINATOR,
               access.DATA_SPECIALIST, access.DATA_MANAGER, access.STATISTICIAN, access.REVIEWER}
# Roles that follow every form's queries in their zones/sites without editing them
ALL_FORMS_ROLES = {access.COORDINATOR, access.STATISTICIAN, access.REVIEWER}

# Forms in table order (missing forms are a separate column)
FORMS = [form for form in FORM_LABELS if form != "missing_forms"]
OUTCOME_DUE_DAYS = 182  # about 6 months of treatment


def _copies(subject, task_type):
    """Extra recipients (to, bcc) who have not received this email yet."""
    to, bcc = report_copies()
    return ([e for e in to if not already_sent(e, subject, task_type)],
            [e for e in bcc if not already_sent(e, subject, task_type)])


def _recipients(roles):
    """Active users with an email holding one of `roles`."""
    users = (get_user_model().objects.filter(is_active=True).exclude(email__isnull=True).exclude(email="")
             .select_related("profile__position").prefetch_related("groups"))
    return [u for u in users if access.get_user_roles(u) & roles]


def _site_ids(user):
    """Site ids the user covers, or None for every site."""
    sites = access.get_accessible_sites(user)
    return None if sites is None else set(sites.values_list("id", flat=True))


def _forms_of(user):
    if access.has_role(user, *ALL_FORMS_ROLES):
        return list(FORMS)
    return [form for form in FORMS if access.can_see_queries(user, form)]


# ── 1. Open queries ─────────────────────────────────────────────────────────

def query_table(per_site, sites, forms, site_ids=None, admin=False):
    """Rows (site, zone, counts per form, missing forms, total) with something open, and a total row."""
    rows = []
    for site in sites:
        if site_ids is not None and site.id not in site_ids:
            continue
        counts = per_site.get(site.id, {})
        by_form = [sum(n for (f, q), n in counts.items() if f == form and (admin or (f, q) not in ADMIN_ONLY))
                   for form in forms]
        missing = sum(n for (f, q), n in counts.items() if f == "missing_forms" and q in forms)
        total = sum(by_form) + missing
        if total:
            rows.append({"site": site.name, "zone": site.district.region.zone.name if site.district and site.district.region else "",
                         "forms": by_form, "named": [(FORM_LABELS[f], n) for f, n in zip(forms, by_form) if n],
                         "missing": missing, "total": total})
    totals = {
        "forms": [sum(r["forms"][i] for r in rows) for i in range(len(forms))],
        "missing": sum(r["missing"] for r in rows),
        "total": sum(r["total"] for r in rows),
    }
    return rows, totals


def send_weekly_query_emails(today=None):
    today = today or timezone.localdate()
    run, _ = take_snapshot(today)
    per_site = defaultdict(dict)
    for site_id, form, query, n in run.counts.filter(site__isnull=False).values_list("site_id", "form", "query", "count"):
        per_site[site_id][(form, query)] = n
    Site = apps.get_model("locations", "Site")
    sites = list(Site.objects.filter(id__in=per_site).select_related("district__region__zone")
                 .order_by("district__region__zone__name", "name"))

    subject = f"Open queries this week - {today:%d %b %Y}"
    link = absolute_url(reverse("dashboard:dashboard"))
    sent = 0

    def context(name, forms, rows, totals):
        return {"name": name, "date": today, "forms": [FORM_LABELS[f] for f in forms], "rows": rows,
                "totals": totals, "link": link, "missing_label": "Missing forms"}

    for user in _recipients(QUERY_ROLES):
        forms = _forms_of(user)
        site_ids = _site_ids(user)
        if not forms or site_ids == set() or already_sent(user.email, subject, QUERIES_TASK):
            continue
        rows, totals = query_table(per_site, sites, forms, site_ids, access.AccessFlags(user).is_admin)
        if totals["total"]:
            sent += send_email(user.email, subject, "emails/weekly_queries",
                               context(user.get_full_name() or user.username, forms, rows, totals), QUERIES_TASK)

    to, bcc = _copies(subject, QUERIES_TASK)
    if to or bcc:
        rows, totals = query_table(per_site, sites, FORMS)
        if totals["total"]:
            sent += send_email(to, subject, "emails/weekly_queries", context("team", FORMS, rows, totals),
                               QUERIES_TASK, bcc=bcc)
    return sent


# ── 2. Substudy 2 on treatment without an outcome ───────────────────────────

def treatment_without_outcome():
    Diagnosis = apps.get_model("nanopore", "Diagnosis")
    return (
        Diagnosis.objects.filter(substudy_q(SUBSTUDY_2, "screening__clinic_laboratory__"),
                                 screening__enrollment__isnull=False, tb_treatment=1)
        .exclude(tb_outcome2__in=OUTCOMES)
        .select_related("screening__site__district__region__zone")
        .order_by("screening__site__name", "tb_treatment_date", "screening__pid")
    )


def outcome_rows(diagnoses, today):
    rows = []
    for d in diagnoses:
        days = (today - d.tb_treatment_date).days if d.tb_treatment_date else None
        rows.append({"pid": d.screening.pid, "site": d.screening.site.name, "site_id": d.screening.site_id,
                     "started": d.tb_treatment_date, "months": round(days / 30.4, 1) if days is not None else None,
                     "due": days is not None and days >= OUTCOME_DUE_DAYS})
    return rows


def _by_site(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["site"]].append(row)
    return [{"site": site, "rows": items, "due": sum(r["due"] for r in items)} for site, items in groups.items()]


def send_weekly_outcome_emails(today=None):
    today = today or timezone.localdate()
    rows = outcome_rows(treatment_without_outcome(), today)
    subject = f"Substudy 2 on treatment without an outcome - {today:%d %b %Y}"
    link = absolute_url(reverse("dashboard:dashboard"))
    sent = 0

    def context(name, items):
        return {"name": name, "date": today, "sites": _by_site(items), "total": len(items),
                "due": sum(r["due"] for r in items), "due_months": round(OUTCOME_DUE_DAYS / 30.4), "link": link}

    for user in _recipients(QUERY_ROLES):
        site_ids = _site_ids(user)
        mine = [r for r in rows if site_ids is None or r["site_id"] in site_ids]
        if mine and not already_sent(user.email, subject, OUTCOMES_TASK):
            sent += send_email(user.email, subject, "emails/weekly_outcomes",
                               context(user.get_full_name() or user.username, mine), OUTCOMES_TASK)

    to, bcc = _copies(subject, OUTCOMES_TASK)
    if (to or bcc) and rows:
        sent += send_email(to, subject, "emails/weekly_outcomes", context("team", rows), OUTCOMES_TASK, bcc=bcc)
    return sent
