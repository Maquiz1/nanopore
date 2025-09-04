# dashboard/views.py
from django.views.generic import ListView
from nanopore.models import Screening
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class DashboardHomeView(ListView):
    model = Screening
    template_name = 'dashboard/dashboard.html'
    context_object_name = 'object_list'
    paginate_by = 50

    def get_queryset(self):
        qs = Screening.objects.select_related('site', 'sex', 'enrolled')
        qs = filter_queryset_by_user_role(self.request.user, qs, site_field="site")

        # Filters
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

        # Role-based zones/sites
        context.update(get_role_context(self.request.user))

        # Counts
        context['screened_count'] = qs.count()
        context['eligible_count'] = qs.filter(eligible=True).count()
        context['enrolled_count'] = qs.filter(enrollment__isnull=False).count()

        return context
