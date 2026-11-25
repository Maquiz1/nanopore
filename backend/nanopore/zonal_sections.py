"""
The Zonal Lab form in sections (the participant's section hub).

The record is still one ZonalLaboratory row: sections only split its questions by
when and by whom they are answered, so exports, the EDCS/TBLIS merge and the data
dictionary don't change. A section's status reuses the data-quality query rules
(reports/services/zonal_dq/filters.py), so the hub and the query pages always agree.

Dar es Salaam (CTRL) records take only the lab number here; the other sections come
from TB-LIS (see nanopore/zonal_rules.py) or CTRL's own Nanopore and LPA forms.
"""
from dataclasses import dataclass, field

from django.db.models import Count
from django.urls import reverse

from nanopore.models import ZonalLaboratory
from nanopore.zonal_rules import is_lab_number_only

NOT_STARTED, IN_PROGRESS, COMPLETE, FROM_TBLIS, NOT_APPLICABLE = "not_started", "in_progress", "complete", "from_tblis", "not_applicable"
WAITING_CTRL, WAITING_DST = "waiting_ctrl", "waiting_dst"
STATUS_LABELS = {
    NOT_STARTED: "Not started", IN_PROGRESS: "In progress", COMPLETE: "Complete", FROM_TBLIS: "From TB-LIS",
    NOT_APPLICABLE: "Not applicable",
    WAITING_CTRL: "Waiting for CTRL", WAITING_DST: "Waiting for DST",
}


@dataclass(frozen=True)
class Section:
    key: str
    number: int
    title: str
    fields: tuple
    entered_by: str
    read_only_fields: tuple = field(default=())  # shown to the zone, entered by CTRL or TB-LIS


ISOLATE_ZONE_FIELDS = ("culture_isolate", "isolate_date")
ISOLATE_CTRL_FIELDS = (
    "isolate_unique_lab_no",
    "phenotypic_performed", "phenotypic_date_performed", "phenotypic_date_results",
    "first_line_dst_performed", "first_line_dst_performed_date", "first_line_dst_results_date",
    "second_line_dst_performed", "second_line_dst_performed_date", "second_line_dst_results_date",
    "rifampicin", "isoniazid", "ethambutol",
    "levofloxacin", "bedaquiline", "linezolid", "clofazimine", "cycloserine", "delamanid", "pretomanid",
    "pyrazinamide", "imipenem", "cilastatin", "meropenem", "terizidone", "moxifloxacin",
    "amikacin", "streptomycin", "ethionamide", "prothionamide", "para_aminosalicylic_acid",
)

SECTIONS = (
    Section("reception", 1, "Sample reception",
            ("unique_lab_no", "date_sputum_received", "appearance", "sample_volume"), "Zone lab"),
    Section("microscopy", 2, "Microscopy", ("microscopy_type", "microscopy_date", "microscopy_results"), "Zone lab"),
    Section("culture", 3, "Culture (LJ and MGIT)",
            ("culture_performed", "culture_method", "lj_inoculation_date", "lj_results_date", "lj_results",
             "mgit_inoculation_date", "mgit_results_date", "mgit_results"), "Zone lab"),
    Section("isolate", 4, "Isolate and phenotypic DST", ISOLATE_ZONE_FIELDS + ISOLATE_CTRL_FIELDS,
            "Zone lab sends the isolate; CTRL gives its number; DST from TB-LIS", read_only_fields=ISOLATE_CTRL_FIELDS),
    Section("xpert", 5, "Xpert XDR",
            ("xpert_xdr_performed", "xpert_xdr_date_performed", "xpert_xdr_isoniazid", "xpert_xdr_fluoroquinolones",
             "xpert_xdr_amikacin", "xpert_xdr_kanamycin", "xpert_xdr_capreomycin", "xpert_xdr_ethionamide"), "Zone lab"),
    Section("lpa", 6, "Line probe assay (LPA)",
            ("lpa", "first_line_lpa", "first_line_lpa_date", "first_line_drugs", "lpa1_mtb", "lpa1_rif", "lpa1_inh",
             "second_line_lpa", "second_line_lpa_date", "second_line_drugs", "lpa2_mtb", "lpa2_rfluoroquinolones",
             "lpa2_aminoglycosides", "lpa2_kanamycin"), "Zone lab"),
    Section("nanopore", 7, "Nanopore sequencing",
            ("nanopore_done", "nanopore_sequencing_date", "epi_to_me", "epi_to_me_date", "epi_to_me_version",
             "sequencing_results", "nanopore_results", "sequencing_delayed", "sequencing_delayed_days",
             "sequencing_delayed_reasons", "sequencing_delayed_others", "nano_amikacin", "nano_bedaquiline",
             "nano_capreomycin", "nano_clofazimine", "nano_delamanid", "nano_ethambutol", "nano_ethionamide",
             "nano_isoniazid", "nano_kanamycin", "nano_levofloxacin", "nano_linezolid", "nano_moxifloxacin",
             "nano_pretomanid", "nano_pyrazinamide", "nano_rifampicin", "nano_streptomycin"), "Zone lab"),
)
BY_KEY = {section.key: section for section in SECTIONS}

# Dar es Salaam: what each section is, since TB-LIS supplies most of it
DAR_FIELDS = {"reception": ("unique_lab_no",)}
DAR_CTRL_FORMS = {"nanopore": "nanopore:ctrl-dar-nanopore", "lpa": "nanopore:ctrl-dar-lpa"}


def _answered(record, name):
    model_field = ZonalLaboratory._meta.get_field(name)
    if model_field.many_to_many:
        return record.pk is not None and getattr(record, name).exists()
    value = getattr(record, model_field.attname)
    return value not in (None, "")


def _query_filters():
    """{query key: (Q, the section it belongs to)} for the Zonal Lab and CTRL isolate queries."""
    from reports.constants.zona_mapping import ZONAL_DQ_FIELD_MAPPING
    from reports.services.zonal_dq.filters import get_ctrl_isolate_filters, get_zonal_dq_filters

    owner = {name: section.key for section in SECTIONS for name in section.fields}
    filters = {**get_zonal_dq_filters(ZonalLaboratory), **get_ctrl_isolate_filters()}
    return {key: (q, owner.get(ZONAL_DQ_FIELD_MAPPING[key][0])) for key, q in filters.items()}


def open_queries(record):
    """{section key: [query labels]} of the record's open queries for the zone. What CTRL
    still has to answer (the isolate number, DST) isn't the zone's: it shows as waiting."""
    from reports.constants.zona_mapping import CTRL_QUERIES
    from reports.services.zonal_dq.problem_lists import query_label

    found = {}
    if record.pk is None:
        return found
    filters = {key: (q, section_key) for key, (q, section_key) in _query_filters().items()
               if section_key and key not in CTRL_QUERIES}
    # One database query for all of them
    hits = ZonalLaboratory.objects.filter(pk=record.pk).aggregate(
        **{key: Count("pk", filter=q, distinct=True) for key, (q, _) in filters.items()})
    for key, (_, section_key) in filters.items():
        if hits[key]:
            found.setdefault(section_key, []).append(query_label(key))
    return found


NO = 2
POSITIVE_LJ, POSITIVE_MGIT = (1, 2, 3, 4), (1,)


def culture_positive(record):
    """The isolate is asked for a positive LJ or MGIT culture (as the query rules say)."""
    return record.lj_results_id in POSITIVE_LJ or record.mgit_results_id in POSITIVE_MGIT


def _not_applicable(section_key, record):
    if section_key == "microscopy":
        return record.culture_performed_id == NO
    if section_key == "isolate":
        culture_known = record.lj_results_id is not None or record.mgit_results_id is not None
        return record.culture_performed_id == NO or (culture_known and not culture_positive(record))
    return False


def _isolate_waiting(record):
    """Other zones: where the isolate is between the zone, CTRL and TB-LIS."""
    sent = getattr(record.culture_isolate, "name", "") == "Yes"
    if sent and not record.isolate_unique_lab_no:
        return WAITING_CTRL
    if sent and record.phenotypic_performed_id is None:
        return WAITING_DST
    return None


# Dar es Salaam: where each section's answers are, on the merged EDCS/TBLIS record
DAR_SOURCES = {"microscopy": "From TB-LIS", "culture": "From TB-LIS", "isolate": "From TB-LIS",
               "xpert": "From TB-LIS", "lpa": "TB-LIS + CTRL", "nanopore": "CTRL"}
EDCS_ANCHORS = {"microscopy": "section-culture", "culture": "section-culture", "isolate": "section-isolate",
                "xpert": "section-xpert", "lpa": "section-lpa"}


def _dar_ctrl_status(section, edcs):
    """Dar es Salaam Nanopore and LPA: CTRL's answers on the EDCS/TBLIS record and their open queries."""
    from reports.constants.zona_mapping import ZONAL_DQ_FIELD_MAPPING
    from reports.services.zonal_dq.filters import get_ctrl_dar_filters
    from reports.services.zonal_dq.problem_lists import query_label

    if edcs is None or not any(_answered(edcs, name) for name in section.fields):
        return NOT_STARTED, []
    filters = {key: q for key, q in get_ctrl_dar_filters().items() if ZONAL_DQ_FIELD_MAPPING[key][0] in section.fields}
    one = type(edcs).objects.filter(pk=edcs.pk)
    hits = one.aggregate(**{key: Count("pk", filter=q, distinct=True) for key, q in filters.items()}) if filters else {}
    open_ones = [query_label(key) for key in filters if hits.get(key)]
    return (IN_PROGRESS if open_ones else COMPLETE), open_ones


def section_cards(record, screening):
    """The hub's cards: each section with its status, open queries and what to show."""
    from nanopore.models import EdcsTblisZonal

    dar = is_lab_number_only(screening)
    queries = open_queries(record)
    edcs = EdcsTblisZonal.objects.filter(screening=screening).first() if dar else None
    cards = []
    for section in SECTIONS:
        fields = DAR_FIELDS.get(section.key, ()) if dar else section.fields
        card_queries = []
        if dar and section.key in DAR_CTRL_FORMS:
            status, card_queries = _dar_ctrl_status(section, edcs)
        elif dar and not fields:
            status = FROM_TBLIS
        elif not dar and _not_applicable(section.key, record):
            status = NOT_APPLICABLE
        elif not any(_answered(record, name) for name in fields):
            status = NOT_STARTED
        elif queries.get(section.key):
            status, card_queries = IN_PROGRESS, queries[section.key]
        else:
            status = (section.key == "isolate" and _isolate_waiting(record)) or COMPLETE
        ctrl_url = reverse(DAR_CTRL_FORMS[section.key], args=[record.pk]) if dar and section.key in DAR_CTRL_FORMS and record.pk else None
        # Dar es Salaam: TB-LIS sections are seen on the EDCS/TBLIS record, at that section
        edcs_url = None
        if dar and edcs is not None and section.key in EDCS_ANCHORS:
            edcs_url = reverse("nanopore:edcs-tblis-laboratory-view", args=[edcs.pk]) + "#" + EDCS_ANCHORS[section.key]
        cards.append({
            "section": section, "status": status, "status_label": STATUS_LABELS[status],
            "queries": card_queries if status == IN_PROGRESS else [],
            "dar": dar, "ctrl_url": ctrl_url, "edcs_url": edcs_url,
            "source": DAR_SOURCES.get(section.key, "CTRL") if dar else section.entered_by,
        })
    return cards


# --- Where Zonal Lab links go (System Controls: "Zonal Lab by section") ---

def by_section():
    """The admin switch; on unless an admin turned it off."""
    from nanopore.models.system_control import SystemControl
    control = SystemControl.objects.only("zonal_lab_by_section").first()
    return True if control is None else control.zonal_lab_by_section


def query_section(key):
    """The section whose form answers a query (None: not a Zonal Lab question)."""
    from reports.constants.zona_mapping import ZONAL_DQ_FIELD_MAPPING
    names = ZONAL_DQ_FIELD_MAPPING.get(key)
    if not names:
        return None
    return next((section.key for section in SECTIONS if names[0] in section.fields), None)


def zonal_edit_url(pk, key=None, switch=None):
    """Edit a Zonal Lab: its section for a query, else the hub; the full form when the switch is off."""
    if not (by_section() if switch is None else switch):
        return reverse("nanopore:zonal-laboratory-update", args=[pk])
    section = query_section(key) if key else None
    if section:
        return reverse("nanopore:zonal-lab-section", args=[pk, section])
    return reverse("nanopore:zonal-lab-hub", args=[pk])
