# # nanopore/views/laboratory/edcs_tblis/task_status.py

# from django.http import JsonResponse
# from celery.result import AsyncResult


# def task_status(request, task_id):
#     res = AsyncResult(task_id)

#     if res.state == "SUCCESS":
#         return JsonResponse(res.result)

#     if res.state == "PROGRESS":
#         return JsonResponse(res.info)

#     return JsonResponse({"state": res.state})

