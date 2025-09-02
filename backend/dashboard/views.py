from django.views.generic import ListView
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from nanopore.models import Screening
from locations.models import Zone, Site
from clinical.models import YesNo
import json

class DashboardHomeView(ListView):
    model = Screening
    template_name = 'dashboard/dashboard.html'
    context_object_name = 'object_list'
    paginate_by = 50

    def get_queryset(self):
        qs = Screening.objects.select_related('site', 'sex', 'enrolled')

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
        yes_instance = YesNo.objects.filter(name="Yes").first()

        # Summary counts
        context['screened_count'] = qs.count()
        context['eligible_count'] = qs.filter(eligible=True).count()
        context['enrolled_count'] = qs.filter(enrolled=yes_instance).count() if yes_instance else 0
        context['completed_count'] = qs.filter(genexpert_confirmation=yes_instance).count() if yes_instance else 0

        # Filters
        context['zones'] = Zone.objects.all()
        context['sites'] = Site.objects.all()
        context['request'] = self.request

        # 🔹 Chart 1: Bar chart per zone
        zone_data = (
            qs.values("site__district__region__zone__name")
              .annotate(count=Count("id"))
              .order_by("site__district__region__zone__name")
        )
        context['zone_labels_json'] = json.dumps([z['site__district__region__zone__name'] or "Unassigned" for z in zone_data])
        context['zone_values_json'] = json.dumps([z['count'] for z in zone_data])

        # 🔹 Chart 2: Time series (daily / weekly / monthly)
        grouping = self.request.GET.get('grouping', 'weekly')  # default weekly
        context['current_grouping'] = grouping

        if grouping == "daily":
            qs_grouped = qs.annotate(period=TruncDay("screening_date"))
        elif grouping == "monthly":
            qs_grouped = qs.annotate(period=TruncMonth("screening_date"))
        else:  # weekly default
            qs_grouped = qs.annotate(period=TruncWeek("screening_date"))

        time_data = (
            qs_grouped.values("period", "site__district__region__zone__name")
                      .annotate(count=Count("id"))
                      .order_by("period")
        )

        zones_list = list({item["site__district__region__zone__name"] or "Unassigned" for item in time_data})
        periods = sorted({item["period"].strftime("%Y-%m-%d") for item in time_data})

        datasets = []
        for zone in zones_list:
            zone_counts = []
            for period in periods:
                entry = next(
                    (item for item in time_data
                     if (item["site__district__region__zone__name"] or "Unassigned") == zone and
                        item["period"].strftime("%Y-%m-%d") == period),
                    None
                )
                zone_counts.append(entry["count"] if entry else 0)
            datasets.append({"label": zone, "data": zone_counts})

        context['time_labels_json'] = json.dumps(periods)
        context['time_datasets_json'] = json.dumps(datasets)

        return context
