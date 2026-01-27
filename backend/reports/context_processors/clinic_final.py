from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

def clinic_report_total(request):
    """
    Returns clinic data quality issues count for navbar:
    - Individual counts for missing critical fields
    - Total issues count for easy display
    """
    if not request.user.is_authenticated:
        return {
            "clinic_report_total": 0,
            "missing_sample_received": 0,
            "missing_number_received": 0,
            "missing_afb_microscopy_conducted": 0,
            "missing_xpert_mtb_rif_conducted": 0,
            "missing_date_sample1_collected": 0,
            "missing_date_sample1_received": 0,
            "missing_appearance_sample1": 0,
            "missing_sample1_volume": 0,
            "missing_appearance_sample2": 0,
            "missing_sample2_volume": 0,
        }

    Clinic = apps.get_model('nanopore', 'ClinicLaboratory')
    clinics = Clinic.objects.all()
    clinics = filter_queryset_by_user_role(request.user, clinics, site_field="screening__site")

    # --- Missing Fields Counts ---
    missing_sample_received = clinics.filter(sample_received__isnull=True).count()
    missing_number_received = clinics.filter(number_received__isnull=True).count()
    missing_afb_microscopy_conducted = clinics.filter(afb_microscopy_conducted__isnull=True).count()
    missing_xpert_mtb_rif_conducted = clinics.filter(xpert_mtb_rif_conducted__isnull=True).count()
    missing_date_sample1_collected = clinics.filter(date_sample1_collected__isnull=True).count()
    missing_date_sample1_received = clinics.filter(date_sample1_received__isnull=True).count()
    missing_appearance_sample1 = clinics.filter(appearance_sample1__isnull=True).count()
    missing_sample1_volume = clinics.filter(sample1_volume__isnull=True).count()
    missing_appearance_sample2 = clinics.filter(appearance_sample2__isnull=True).count()
    missing_sample2_volume = clinics.filter(sample2_volume__isnull=True).count()
    
    # --- Total Issues ---
    clinic_report_total = (
        missing_sample_received
        + missing_number_received
        + missing_afb_microscopy_conducted
        + missing_xpert_mtb_rif_conducted
        + missing_date_sample1_collected
        + missing_date_sample1_received
        + missing_appearance_sample1
        + missing_sample1_volume
        + missing_appearance_sample2
        + missing_sample2_volume
    )

    return {
        "clinic_report_total": clinic_report_total,
        "missing_sample_received": missing_sample_received,
        "missing_number_received": missing_number_received,
        "missing_afb_microscopy_conducted": missing_afb_microscopy_conducted,
        "missing_xpert_mtb_rif_conducted": missing_xpert_mtb_rif_conducted,
        "missing_date_sample1_collected": missing_date_sample1_collected,
        "missing_date_sample1_received": missing_date_sample1_received,
        "missing_appearance_sample1": missing_appearance_sample1,
        "missing_sample1_volume": missing_sample1_volume,
        "missing_appearance_sample2": missing_appearance_sample2,
        "missing_sample2_volume": missing_sample2_volume,
    }
