from nanopore.models import ClinicLaboratory
from django.views.generic import ListView
from nanopore.models import Screening,Enrollment,Diagnosis
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context
from django.db.models import Count
# from enrollment.models import Enrollment  # adjust import path if needed
# from diagnosis.models import Diagnosis   # for completed_count

class DashboardHomeView(ListView):
    model = Screening
    template_name = 'dashboard/dashboard.html'
    context_object_name = 'object_list'
    paginate_by = 50

    def get_queryset(self):
        qs = Screening.objects.select_related('site', 'site__district__region__zone', 'sex', 'enrolled')
        qs = filter_queryset_by_user_role(self.request.user, qs, site_field="site")

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

        role_context = get_role_context(self.request.user)
        context.update({
            'is_admin': role_context['is_admin'],
            'is_zonal_lab': role_context['is_zonal_lab'],
            'is_national_lab': role_context['is_national_lab'],
            'is_site_only': role_context['is_site_only'],
            'zones': {z.id: z.name for z in role_context['zones']},
            'sites': {s.id: s.name for s in role_context['sites']},
        })

        # Counts
        context['screened_count'] = qs.count()
        context['eligible_count'] = qs.filter(eligible=True).count()
        context['enrolled_count'] = Enrollment.objects.filter(screening__in=qs).count()
        context['completed_count'] = qs.filter(diagnosis__tb_outcome2__in=[1,2,3,4,5,6]).count()

        # Graph by zone
        from django.db.models import Count
        zone_aggregation = qs.values('site__district__region__zone__id','site__district__region__zone__name')\
                             .annotate(count=Count('id')).order_by('site__district__region__zone__name')
        context['zone_labels_json'] = [z['site__district__region__zone__name'] for z in zone_aggregation]
        context['zone_values_json'] = [z['count'] for z in zone_aggregation]

        # Time series per zone (existing)
        from django.db.models.functions import TruncDate
        import json
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        qs_time = qs
        if start_date and end_date:
            qs_time = qs_time.filter(screening_date__range=[start_date, end_date])
        time_datasets = []
        for zone in role_context['zones']:
            zone_qs = qs_time.filter(site__district__region__zone=zone)
            counts_by_date = zone_qs.annotate(date=TruncDate('screening_date'))\
                                    .values('date').annotate(count=Count('id')).order_by('date')
            dates = [c['date'].isoformat() for c in counts_by_date]
            values = [c['count'] for c in counts_by_date]
            time_datasets.append({'label': zone.name, 'data': values, 'dates': dates})
        all_dates = sorted(set(d for dataset in time_datasets for d in dataset['dates']))
        for dataset in time_datasets:
            data_dict = dict(zip(dataset['dates'], dataset['data']))
            dataset['data'] = [data_dict.get(d,0) for d in all_dates]
        context['time_labels_json'] = json.dumps(all_dates)
        context['time_datasets_json'] = json.dumps(time_datasets)

        # --- Substudy counts per zone ---
        sub2_values, sub4_values = [], []
        for zone in role_context['zones']:
            lab_qs = ClinicLaboratory.objects.filter(
                screening__site__district__region__zone=zone
            )
            if start_date and end_date:
                lab_qs = lab_qs.filter(screening__screening_date__range=[start_date, end_date])

            sub2_count = lab_qs.filter(xpert_mtb__in=[2,3,4,5,6]).count()
            sub4_count = lab_qs.filter(xpert_mtb__in=[1,7,8,9]).count()
            sub2_values.append(sub2_count)
            sub4_values.append(sub4_count)

        context['substudy_labels_json'] = [z.name for z in role_context['zones']]
        context['sub2_values_json'] = sub2_values
        context['sub4_values_json'] = sub4_values

        return context
