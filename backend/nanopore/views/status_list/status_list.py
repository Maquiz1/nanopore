# nanopore/views/status.py
from django.views.generic import ListView
from nanopore.models import Screening
from utils.permissions import filter_queryset_by_user_role

class StatusListView(ListView):
    model = Screening
    template_name = "nanopore/form_status/status_list.html"
    context_object_name = "screenings"

    def get_queryset(self):
        qs = Screening.objects.all().select_related(
            "enrollment",
            "clinic_laboratory",
            "zonal_laboratory",
            "diagnosis",
            "site",
            "site__district",
            "site__district__region",
            "site__district__region__zone"
        )
        # Filter based on user role & site
        qs = filter_queryset_by_user_role(self.request.user, qs)
        return qs
