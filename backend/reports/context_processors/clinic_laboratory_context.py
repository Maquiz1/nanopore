from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

def clinic_report_total(request):
    """
    Returns clinic data quality issues count for navbar:
    - Individual counts for missing 'sample_received' and 'number_received'
    - Total issues count for easy display
    """
    if not request.user.is_authenticated:
        return {
            "clinic_report_total": 0,
            "missing_sample_received": 0,
            "missing_number_received": 0,
        }

    Clinic = apps.get_model('nanopore', 'ClinicLaboratory')
    clinics = Clinic.objects.all()
    clinics = filter_queryset_by_user_role(request.user, clinics, site_field="screening__site")

    # --- Missing Fields Counts ---
    missing_sample_received = clinics.filter(
        Q(sample_received__isnull=True) | Q(sample_received='') | Q(sample_received=False)
    ).count()

    missing_number_received = clinics.filter(
        Q(number_received__isnull=True) | Q(number_received='') | Q(number_received=False)
    ).count()

    # --- Total Issues ---
    clinic_report_total = missing_sample_received + missing_number_received

    return {
        "clinic_report_total": clinic_report_total,
        "missing_sample_received": missing_sample_received,
        "missing_number_received": missing_number_received,
    }
