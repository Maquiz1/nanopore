from celery import shared_task
from django.core.management import call_command
from .tasks_export_models import export_model_raw_data_task


@shared_task
def create_screening_dq_snapshot():
    """
    Run the Screening Data Quality snapshot command
    """
    call_command("snapshot_screening_dq")
    return "Screening DQ snapshot created"


@shared_task
def create_enrollment_dq_snapshot():
    """
    Run the Enrollment Data Quality snapshot command
    """
    call_command("snapshot_enrollment_dq")
    return "Enrollment DQ snapshot created"


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60)
def create_clinic_lab_dq_snapshot(self):
    """
    Run the Clinic Data Quality snapshot command
    """
    call_command("snapshot_clinic_lab_dq")
    return "Clinic DQ snapshot created"


@shared_task
def create_diagnosis_dq_snapshot():
    """
    Run the Diagnosis Data Quality snapshot command
    """
    call_command("snapshot_diagnosis_dq")
    return "Diagnosis DQ snapshot created"


@shared_task
def create_regimen_dq_snapshot():
    """
    Run the Regimen Data Quality snapshot command
    """
    call_command("snapshot_regimen_dq")
    return "Regimen DQ snapshot created"


@shared_task
def create_zonal_lab_dq_snapshot():
    """
    Run the Zonal Laboratory Data Quality snapshot command
    """
    call_command("snapshot_zonal_lab_dq")
    return "Zonal Laboratory DQ snapshot created"

@shared_task
def create_missing_forms_dq_snapshot():
    """
    Run the Missing Forms Data Quality snapshot command
    """
    call_command("snapshot_missing_forms_dq")
    return "Missing Forms DQ snapshot created"