"""
The Zonal Lab form's sections (nanopore/zonal_sections.py), each saved on its own.

A section requires only its gate questions ("Was culture performed?") and what is
done at the same moment; results that come weeks later (LJ results, DST) can be
added on a later visit and stay a query until then. A question that its gate hides
is cleared on save, so a No leaves nothing behind. RULES say which answer of which
question opens a question: the server clears and requires by them, and
static/custom_js/zonal_section.js shows and hides by the same rules.
"""
from django import forms

from common.labels.laboratory.zonal.zonal_labels import ZONAL_LABELS
from nanopore.forms.laboratory.zonal.ctrl_dar_forms import DarNanoporeForm
from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm
from nanopore.forms.reason_for_change import ReasonForChangeMixin
from nanopore.models import ZonalLaboratory
from nanopore.zonal_rules import ctrl_answers, is_lab_number_only
from nanopore.zonal_sections import BY_KEY, DAR_FIELDS, ISOLATE_CTRL_FIELDS, ISOLATE_ZONE_FIELDS, culture_positive

# Option ids, as the query rules (reports/services/zonal_dq/filters.py) and the old form's scripts use them
YES = 1
LJ, MGIT = 1, 2


def _meta(names):
    return type("Meta", (), {
        "model": ZonalLaboratory,
        "fields": names,
        "labels": {name: ZONAL_LABELS[name] for name in names if name in ZONAL_LABELS},
        "widgets": {name: ZonalLaboratoryForm.Meta.widgets[name] for name in names if name in ZonalLaboratoryForm.Meta.widgets},
    })


def _pks(value):
    if value is None:
        return set()
    if hasattr(value, "values_list"):
        return set(value.values_list("pk", flat=True))
    return {value.pk}


def _empty(value):
    return value in (None, "") if not hasattr(value, "exists") else not value.exists()


class SectionForm(ReasonForChangeMixin, forms.ModelForm):
    section_key = None
    required = ()            # always required
    rules = ()               # ((children), parent, {pks that open them}), parents before children
    required_when_shown = ()

    def __init__(self, *args, screening=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.section = BY_KEY[self.section_key]
        self.dar = is_lab_number_only(screening)
        for name, form_field in self.fields.items():
            queryset = getattr(form_field, "queryset", None)
            if queryset is not None and any(f.name == "value" for f in queryset.model._meta.fields):
                form_field.queryset = queryset.order_by("value")
            form_field.required = name in self.required

    @property
    def has_answers(self):
        return any(name != "reason_for_change" for name in self.fields)

    def shown_by(self):
        """{child: (parent, "1,2")} for the template's data-when attributes."""
        return {child: (parent, ",".join(str(pk) for pk in sorted(pks)))
                for children, parent, pks in self.rules for child in children if child in self.fields}

    def rows(self):
        shown_by = self.shown_by()
        return [(self[name], *shown_by.get(name, ("", ""))) for name in self.fields if name != "reason_for_change"]

    def clean(self):
        cleaned = super().clean()
        for children, parent, pks in self.rules:
            opened = bool(_pks(cleaned.get(parent)) & set(pks))
            for name in children:
                if name not in self.fields:
                    continue
                if not opened:
                    form_field = self.fields[name]
                    cleaned[name] = form_field.queryset.none() if isinstance(form_field, forms.ModelMultipleChoiceField) else None
                    self.errors.pop(name, None)
                elif name in self.required_when_shown and _empty(cleaned.get(name)) and name not in self.errors:
                    self.add_error(name, "Required.")
        return cleaned


class ReceptionForm(SectionForm):
    """1. Sample reception. Dar es Salaam takes only the lab number: TB-LIS gives the rest."""
    section_key = "reception"
    Meta = _meta(BY_KEY["reception"].fields)
    required = BY_KEY["reception"].fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.dar:
            for name in BY_KEY["reception"].fields:
                if name not in DAR_FIELDS["reception"]:
                    del self.fields[name]


class MicroscopyForm(SectionForm):
    """2. Microscopy: type, date and result are recorded together."""
    section_key = "microscopy"
    Meta = _meta(BY_KEY["microscopy"].fields)
    required = BY_KEY["microscopy"].fields


LJ_FIELDS = ("lj_inoculation_date", "lj_results_date", "lj_results")
MGIT_FIELDS = ("mgit_inoculation_date", "mgit_results_date", "mgit_results")


class CultureForm(SectionForm):
    """3. Culture. Results can be added later; the method is needed once culture is done."""
    section_key = "culture"
    Meta = _meta(BY_KEY["culture"].fields)
    required = ("culture_performed",)
    rules = (
        (("culture_method",), "culture_performed", {YES}),
        (LJ_FIELDS, "culture_method", {LJ}),
        (MGIT_FIELDS, "culture_method", {MGIT}),
    )
    required_when_shown = ("culture_method",)


class IsolateForm(SectionForm):
    """4. Isolate: the zone says whether it was sent and when. CTRL gives the number; DST comes from TB-LIS."""
    section_key = "isolate"
    Meta = _meta(ISOLATE_ZONE_FIELDS)
    required = ("culture_isolate",)
    rules = ((("isolate_date",), "culture_isolate", {YES}),)
    required_when_shown = ("isolate_date",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.applicable = culture_positive(self.instance)
        if not self.applicable:
            for name in ISOLATE_ZONE_FIELDS:
                del self.fields[name]
        self.ctrl_values = ctrl_answers(self.instance, ISOLATE_CTRL_FIELDS)


XPERT_RESULTS = tuple(name for name in BY_KEY["xpert"].fields if name not in ("xpert_xdr_performed",))


class XpertForm(SectionForm):
    """5. Xpert XDR. Results can be added after the date it was run."""
    section_key = "xpert"
    Meta = _meta(BY_KEY["xpert"].fields)
    required = ("xpert_xdr_performed",)
    rules = ((XPERT_RESULTS, "xpert_xdr_performed", {YES}),)
    required_when_shown = ("xpert_xdr_date_performed",)


LPA1 = ("first_line_lpa_date", "first_line_drugs", "lpa1_mtb", "lpa1_rif", "lpa1_inh")
LPA2 = ("second_line_lpa_date", "second_line_drugs", "lpa2_mtb", "lpa2_rfluoroquinolones", "lpa2_aminoglycosides", "lpa2_kanamycin")


class LpaForm(SectionForm):
    """6. Line probe assay: first- and second-line are asked when LPA was performed."""
    section_key = "lpa"
    Meta = _meta(BY_KEY["lpa"].fields)
    required = ("lpa",)
    rules = (
        (("first_line_lpa", "second_line_lpa"), "lpa", {YES}),
        (LPA1, "first_line_lpa", {YES}),
        (LPA2, "second_line_lpa", {YES}),
    )
    required_when_shown = ("first_line_lpa", "second_line_lpa")


class NanoporeForm(DarNanoporeForm):
    """7. Nanopore sequencing: the same questions and rules as CTRL's Dar es Salaam Nanopore form."""
    section_key = "nanopore"

    def __init__(self, *args, screening=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.section = BY_KEY["nanopore"]
        self.dar = is_lab_number_only(screening)


SECTION_FORMS = {form.section_key: form for form in (ReceptionForm, MicroscopyForm, CultureForm, IsolateForm, XpertForm, LpaForm, NanoporeForm)}
