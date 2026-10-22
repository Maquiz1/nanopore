from utils import access
from utils.access_mixins import FeatureAccessMixin
from django.views import View
from django.http import JsonResponse
from celery.result import AsyncResult
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class TaskStatusView(FeatureAccessMixin, View):
    # Polled by TBLIS uploads and by the model export page.
    access_feature = (access.TBLIS_UPLOAD, access.EXPORTS)

    def get(self, request, task_id):
        task = AsyncResult(task_id)

        response = {
            "state": task.state,
        }

        if task.state == "PROGRESS":
            response.update(task.info)

        elif task.state == "SUCCESS":
            response.update(task.result)

        elif task.state == "FAILURE":
            response["error"] = str(task.info)

        return JsonResponse(response)


@method_decorator(csrf_exempt, name="dispatch")
class RevokeEdcsTblisTaskView(FeatureAccessMixin, View):
    access_feature = access.TBLIS_UPLOAD

    def post(self, request, task_id):
        task = AsyncResult(task_id)
        task.revoke(terminate=True)
        return JsonResponse({"status": "revoked"})