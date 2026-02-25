# views.py
from django.http import JsonResponse
from nanopore.models import ClinicLaboratory

def audit_history_ajax(request, field):
    pid = request.GET.get('pid')  # optional: pass PID to filter
    history = []  # fetch history for this field
    for h in ClinicLaboratory.history.filter(field=field, object_id=pid):
        history.append({
            'changed_at': h.changed_at.strftime('%Y-%m-%d %H:%M'),
            'user': h.changed_by.username if h.changed_by else "System",
            'old': h.old,
            'new': h.new
        })
    return JsonResponse(history, safe=False)