"""Nanopore questions shared by the Zonal Lab and CTRL forms: what each answer opens (static/custom_js/nanopore_section.js)."""
from django import forms

YES = 1
OTHER_REASON = 96
DRUG_FIELDS = (
    "nano_amikacin", "nano_bedaquiline", "nano_capreomycin", "nano_clofazimine", "nano_delamanid", "nano_ethambutol",
    "nano_ethionamide", "nano_isoniazid", "nano_kanamycin", "nano_levofloxacin", "nano_linezolid", "nano_moxifloxacin",
    "nano_pretomanid", "nano_pyrazinamide", "nano_rifampicin", "nano_streptomycin",
)
OPENED_BY = {
    "nanopore_done": ("nanopore_sequencing_date", "epi_to_me", "nanopore_results", "sequencing_delayed"),
    "epi_to_me": ("epi_to_me_date", "epi_to_me_version", "sequencing_results"),
    "nanopore_results": DRUG_FIELDS,
    "sequencing_delayed": ("sequencing_delayed_days", "sequencing_delayed_reasons"),
}


def _answered_yes(cleaned, name):
    answer = cleaned.get(name)
    return bool(answer and answer.pk == YES)


def _clear(form, cleaned, name):
    field = form.fields[name]
    cleaned[name] = field.queryset.none() if isinstance(field, forms.ModelMultipleChoiceField) else None


def _is_empty(cleaned, name):
    value = cleaned.get(name)
    return value in (None, "") or (hasattr(value, "exists") and not value.exists())


def settle_nanopore(form, cleaned, require=False):
    """
    Hidden answers are cleared, so a No leaves nothing behind. With require=True the
    questions a Yes opens must be answered (the CTRL form).
    """
    if "nanopore_done" not in form.fields:
        return
    for parent, children in OPENED_BY.items():  # parents first: a cleared parent clears its own children
        for name in children:
            if not _answered_yes(cleaned, parent):
                _clear(form, cleaned, name)
            elif require and _is_empty(cleaned, name) and name not in form.errors:
                form.add_error(name, "Required.")
    reasons = cleaned.get("sequencing_delayed_reasons")
    other = reasons is not None and reasons.filter(value=OTHER_REASON).exists()
    if not other:
        cleaned["sequencing_delayed_others"] = None
    elif require and not cleaned.get("sequencing_delayed_others"):
        form.add_error("sequencing_delayed_others", "Required when the reason is Other.")
