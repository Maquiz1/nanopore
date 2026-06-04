from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag
def eligible_link(screening, field_name, user):
    """
    Returns N/A if not eligible.
    Otherwise, returns a link or status based on the field and user.
    field_name can be: 'enrollment', 'clinic_laboratory', 'diagnosis', 'zonal_laboratory'
    """

    # If not eligible
    if not screening.eligible:
        return "N/A"

    # Identify user roles
    user_groups = [g.name.upper() for g in user.groups.all()]
    is_data_specialist = hasattr(user, "profile") and user.profile.position and user.profile.position.name.lower() == "data specialist"
    
    is_admin = user.is_superuser or "ADMIN" in user_groups or is_data_specialist
    is_reviewer = "REVIEWER" in user_groups
    
    # If they have other roles or are admin, they aren't "just" a reviewer
    is_reviewer_only = is_reviewer and not (is_admin or "NURSE" in user_groups or "CLINICIAN" in user_groups or "LABORATORY_TECHNICIAN" in user_groups)

    can_create_clinic = "NURSE" in user_groups or "CLINICIAN" in user_groups or is_admin
    can_create_zonal = "LABORATORY_TECHNICIAN" in user_groups or is_admin
    can_edit = not is_reviewer_only

    # Enrollment
    if field_name == "enrollment":
        if screening.enrollment:
            if can_edit:
                url = reverse("nanopore:enrollment-update", args=[screening.enrollment.pk])
                return f'<a href="{url}">✅ Enrolled</a><br>{screening.enrollment.enrollment_date.strftime("%Y-%m-%d")}'
            return f"✅ Enrolled<br>{screening.enrollment.enrollment_date.strftime('%Y-%m-%d')}"
        else:
            if can_create_clinic:
                url = reverse("nanopore:enrollment-create") + f"?screening={screening.pk}"
                return f'<a href="{url}">❌ Not Enrolled</a>'
            return "❌ Not Enrolled"

    # Clinic Lab
    elif field_name == "clinic_laboratory":
        if screening.clinic_laboratory:
            if can_edit:
                url = reverse("nanopore:clinic-laboratory-update", args=[screening.clinic_laboratory.pk])
                return f'<a href="{url}">✅ DONE</a>'
            return "✅ DONE"
        else:
            if can_create_clinic:
                url = reverse("nanopore:clinic-laboratory-create") + f"?screening={screening.pk}"
                return f'<a href="{url}">❌ Add</a>'
            return "❌ Add"

    # Diagnosis
    elif field_name == "diagnosis":
        if screening.diagnosis:
            if can_edit:
                url = reverse("nanopore:diagnosis-update", args=[screening.diagnosis.pk])
                return f'<a href="{url}">✅ DONE</a>'
            return "✅ DONE"
        else:
            if can_create_clinic:
                url = reverse("nanopore:diagnosis-create") + f"?screening={screening.pk}"
                return f'<a href="{url}">❌ Add</a>'
            return "❌ Add"

    # Zonal Laboratory
    elif field_name == "zonal_laboratory":
        if screening.substudy_case == "Substudy 2":
            if screening.zonal_laboratory:
                if can_edit:
                    url = reverse("nanopore:zonal-laboratory-update", args=[screening.zonal_laboratory.pk])
                    return f'<a href="{url}">✅ DONE</a>'
                return "✅ DONE"
            else:
                if can_create_zonal:
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
