"""LPA questions shared by the Zonal Lab and EDCS/TBLIS forms."""


def relax_lpa_lines(form):
    """
    First-/second-line LPA questions are only shown when "LPA performed" is Yes
    (static/custom_js/lpa_fields.js), so they can't be required on every save.
    """
    for name in ("first_line_lpa", "second_line_lpa"):
        if name in form.fields:
            form.fields[name].required = False


def require_lpa_lines_when_done(form, cleaned_data):
    """Require the first-/second-line LPA answers only when LPA performed = Yes."""
    lpa = cleaned_data.get("lpa")
    if lpa is None or str(getattr(lpa, "name", "")).strip().lower() != "yes":
        return
    for name in ("first_line_lpa", "second_line_lpa"):
        if name in form.fields and not cleaned_data.get(name):
            form.add_error(name, "Required when LPA was performed.")
