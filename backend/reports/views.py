from django.shortcuts import render
import json

def dashboard_report(request):
    # Example dynamic data
    visits_per_site = {'Site A': 12, 'Site B': 19, 'Site C': 3, 'Site D': 5}
    mentorship_progress = [3, 7, 4, 6, 8, 10]
    competence_status = {'Completed': 10, 'Pending': 5, 'In Progress': 3}

    context = {
        'visits_labels': json.dumps(list(visits_per_site.keys())),
        'visits_data': json.dumps(list(visits_per_site.values())),
        'progress_labels': json.dumps(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']),
        'progress_data': json.dumps(mentorship_progress),
        'status_labels': json.dumps(list(competence_status.keys())),
        'status_data': json.dumps(list(competence_status.values())),
    }

    return render(request, 'reports/index.html', context)
