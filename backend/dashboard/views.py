from django.views.generic import ListView
from nanopore.models import Screening
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context
from django.db.models import Count

class DashboardHomeView(ListView):
    model = Screening
    template_name = 'dashboard/dashboard.html'
    context_object_name = 'object_list'
    paginate_by = 50

    def get_queryset(self):
        qs = Screening.objects.select_related('site', 'site__district__region__zone', 'sex', 'enrolled')
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

        # Role-based zones/sites (dictionary for dropdowns)
        role_context = get_role_context(self.request.user)
        context.update({
            'is_admin': role_context['is_admin'],
            'is_zonal_lab': role_context['is_zonal_lab'],
            'is_national_lab': role_context['is_national_lab'],
            'is_site_only': role_context['is_site_only'],
            # convert querysets to dicts for dropdown get_item filter
            'zones': {z.id: z.name for z in role_context['zones']},
            'sites': {s.id: s.name for s in role_context['sites']},
        })

        # Counts
        context['screened_count'] = qs.count()
        context['eligible_count'] = qs.filter(eligible=True).count()
        context['enrolled_count'] = qs.filter(enrollment__isnull=False).count()
        context['completed_count'] = qs.filter(enrollment__isnull=False, enrolled__name__iexact='yes').count()

        # --- Graph data by zone ---
        zone_aggregation = qs.values(
            'site__district__region__zone__id',
            'site__district__region__zone__name'
        ).annotate(count=Count('id')).order_by('site__district__region__zone__name')

        context['zone_labels_json'] = [z['site__district__region__zone__name'] for z in zone_aggregation]
        context['zone_values_json'] = [z['count'] for z in zone_aggregation]

        # --- Time series per zone ---
        # example: daily counts per zone (adjust period if needed)
        from django.db.models.functions import TruncDate
        import json

        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        qs_time = qs
        if start_date and end_date:
            qs_time = qs_time.filter(screening_date__range=[start_date, end_date])

        time_datasets = []
        zones_qs = role_context['zones']  # queryset
        for zone in zones_qs:
            zone_qs = qs_time.filter(site__district__region__zone=zone)
            counts_by_date = zone_qs.annotate(date=TruncDate('screening_date')).values('date').annotate(count=Count('id')).order_by('date')
            dates = [c['date'].isoformat() for c in counts_by_date]
            values = [c['count'] for c in counts_by_date]

            time_datasets.append({
                'label': zone.name,
                'data': values,
                'dates': dates
            })

        # unify all dates for chart labels
        all_dates = sorted(set(d for dataset in time_datasets for d in dataset['dates']))
        for dataset in time_datasets:
            dataset_data_dict = dict(zip(dataset['dates'], dataset['data']))
            dataset['data'] = [dataset_data_dict.get(d, 0) for d in all_dates]

        context['time_labels_json'] = json.dumps(all_dates)
        context['time_datasets_json'] = json.dumps(time_datasets)

        return context
