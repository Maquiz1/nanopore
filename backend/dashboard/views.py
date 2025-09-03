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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()

        # Add counts
        context['screened_count'] = qs.count()  # Total screened
        context['eligible_count'] = qs.filter(eligible=True).count()
        context['enrolled_count'] = qs.filter(enrollment__isnull=False).count()  # Enrolled patients
        # context['completed_count'] = qs.filter(completed__isnull=False).count()  # Completed patients

        # context['enrolled_count'] = qs.filter(enrolled__name="Yes").count()  # Enrolled patients
        # context['completed_count'] = qs.filter(enrolled__name="Yes", screening_completed=True).count()  # Example if you have completed flag

        # You can add more counts, e.g., completed, eligible, etc.
        context['zones'] = Zone.objects.all()
        context['sites'] = Site.objects.all()
        return context
