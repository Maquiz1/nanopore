from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag
def eligible_link(screening, field_name, user_group):
    """
    Returns N/A if not eligible.
    Otherwise, returns a link or status based on the field and user group.
    field_name can be: 'enrollment', 'clinic_laboratory', 'diagnosis', 'zonal_laboratory'
    user_group: string (first group of the user)
    """

    # If not eligible
    if not screening.eligible:
        return "N/A"

    # Enrollment
    if field_name == "enrollment":
        if screening.enrollment:
            if user_group != "REVIEWER":
                url = reverse("nanopore:enrollment-update", args=[screening.enrollment.pk])
                return f'<a href="{url}">✅ Enrolled</a><br>{screening.enrollment.enrollment_date.strftime("%Y-%m-%d")}'
            return f"✅ Enrolled<br>{screening.enrollment.enrollment_date.strftime('%Y-%m-%d')}"
        else:
            if user_group in ["NURSE", "CLINICIAN"]:
                url = reverse("nanopore:enrollment-create") + f"?screening={screening.pk}"
                return f'<a href="{url}">❌ Not Enrolled</a>'
            return "❌ Not Enrolled"

    # Clinic Lab
    elif field_name == "clinic_laboratory":
        if screening.clinic_laboratory:
            if user_group != "REVIEWER":
                url = reverse("nanopore:clinic-laboratory-update", args=[screening.clinic_laboratory.pk])
                return f'<a href="{url}">✅ DONE</a>'
            return "✅ DONE"
        else:
            if user_group in ["NURSE", "CLINICIAN"]:
                url = reverse("nanopore:clinic-laboratory-create") + f"?screening={screening.pk}"
                return f'<a href="{url}">❌ Add</a>'
            return "❌ Add"

    # Diagnosis
    elif field_name == "diagnosis":
        if screening.diagnosis:
            if user_group != "REVIEWER":
                url = reverse("nanopore:diagnosis-update", args=[screening.diagnosis.pk])
                return f'<a href="{url}">✅ DONE</a>'
            return "✅ DONE"
        else:
            if user_group in ["NURSE", "CLINICIAN"]:
                url = reverse("nanopore:diagnosis-create") + f"?screening={screening.pk}"
                return f'<a href="{url}">❌ Add</a>'
            return "❌ Add"

    # Zonal Laboratory
    elif field_name == "zonal_laboratory":
        if screening.substudy_case == "Substudy 2":
            if screening.zonal_laboratory:
                if user_group != "REVIEWER":
                    url = reverse("nanopore:zonal-laboratory-update", args=[screening.zonal_laboratory.pk])
                    return f'<a href="{url}">✅ DONE</a>'
                return "✅ DONE"
            else:
                if user_group == "LABORATORY_TECHNICIAN":
                    url = reverse("nanopore:zonal-laboratory-create") + f"?screening={screening.pk}"
                    return f'<a href="{url}">❌ Add</a>'
                return "❌ Add"
        elif screening.substudy_case in ["Substudy 4", "Uncategorized"]:
            text = "N/A"
            if screening.substudy_case == "Uncategorized":
                text += "<br><small>(ASK Site to fill Clinic Lab form first)</small>"
            return text
        else:
            return "-"

    return "-"
