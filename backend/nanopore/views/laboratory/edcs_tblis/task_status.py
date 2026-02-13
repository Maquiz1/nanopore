# nanopore/views/laboratory/edcs_tblis/task_status.py

from django.http import JsonResponse
from celery.result import AsyncResult


def task_status(request, task_id):
    res = AsyncResult(task_id)
    return JsonResponse(res.info or {"state": res.state})