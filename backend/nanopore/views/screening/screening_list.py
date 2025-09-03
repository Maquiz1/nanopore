# views.py
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import Screening
from locations.models import Zone, Site
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

class ScreeningListView(ListView):
    model = Screening
    template_name = 'nanopore/screening/screening_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self):
        qs = Screening.objects.select_related('site', 'sex', 'enrolled')
        qs = filter_queryset_by_user_role(self.request.user, qs)

        # Additional filters
        zone_id = self.request.GET.get('zone')
        site_id = self.request.GET.get('site')
        pid = self.request.GET.get('pid')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        order_by = self.request.GET.get('order_by', '-screening_date')

        if zone_id:
            qs = qs.filter(site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(site_id=site_id)
        if pid:
            qs = qs.filter(pid__icontains=pid)
        if start_date and end_date:
            qs = qs.filter(screening_date__range=[start_date, end_date])
        if order_by:
            qs = qs.order_by(order_by)
        return qs
