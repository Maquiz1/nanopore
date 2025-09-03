# views.py
from django.views.generic import ListView
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from nanopore.models import Screening
from locations.models import Zone, Site
from clinical.models import YesNo
import json
from utils.permissions import filter_queryset_by_user_role

class DashboardHomeView(ListView):
    model = Screening
    template_name = 'dashboard/dashboard.html'
    context_object_name = 'object_list'
    paginate_by = 50

    def get_queryset(self):
        qs = Screening.objects.select_related('site', 'sex', 'enrolled')
        qs = filter_queryset_by_user_role(self.request.user, qs)

        # Filters from GET params
        zone_id = self.request.GET.get('zone')
        site_id = self.request.GET.get('site')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        order_by = self.request.GET.get('order_by', '-screening_date')

        if zone_id:
            qs = qs.filter(site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(site_id=site_id)
        if start_date and end_date:
            qs = qs.filter(screening_date__range=[start_date, end_date])
        if order_by:
            qs = qs.order_by(order_by)
        return qs
