# views.py
from django.http import JsonResponse

def raise_query(request):
    if request.method == "POST":
        field = request.POST.get('field')
        query = request.POST.get('query')
        # Save query to DB linked to PID + field
        return JsonResponse({"status": "ok"})