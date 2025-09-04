# nanopore/views.py
from django.views.generic import ListView
from nanopore.models import Screening

class StatusListView(ListView):
    model = Screening
    template_name = "nanopore/form_status/status_list.html"
    context_object_name = "screenings"

    def get_queryset(self):
        # Load related enrollment in one query
        return Screening.objects.all().select_related("enrollment")
