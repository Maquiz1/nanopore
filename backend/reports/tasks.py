from celery import shared_task
from django.core.management import call_command

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
def create_clinic_dq_snapshot(self):
    call_command("snapshot_clinic_dq")
