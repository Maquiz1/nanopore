from celery import shared_task
from django.core.management import call_command

@shared_task
def create_screening_dq_snapshot():
    """
    Run the snapshot command via Celery
    """
    call_command("snapshot_screening_dq")