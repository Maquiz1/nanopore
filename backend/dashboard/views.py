from django.views.generic import ListView
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
import json
from datetime import timedelta

from nanopore.models import Screening, Enrollment, Diagnosis, ClinicLaboratory
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class DashboardHomeView(ListView):
    model = Screening
    template_name = "dashboard/dashboard.html"
    context_object_name = "object_list"
    paginate_by = 50

    def get_queryset(self):
        qs = Screening.objects.select_related(
            "site", "site__district__region__zone", "sex", "enrolled"
        )
        qs = filter_queryset_by_user_role(self.request.user, qs, site_field="site")

        # Filters
        zone_id = self.request.GET.get("zone")
        site_id = self.request.GET.get("site")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        order_by = self.request.GET.get("order_by", "-screening_date")

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

        # Role context
        role_context = get_role_context(self.request.user)
        context.update(
            {
                "is_admin": role_context["is_admin"],
                "is_zonal_lab": role_context["is_zonal_lab"],
                "is_national_lab": role_context["is_national_lab"],
                "is_site_only": role_context["is_site_only"],
                "zones": {z.id: z.name for z in role_context["zones"]},
                "sites": {s.id: s.name for s in role_context["sites"]},
            }
        )

        # --- Counts ---
        screened_count = qs.count()
        eligible_count = qs.filter(eligible=True).count()
        enrolled_count = Enrollment.objects.filter(screening__in=qs).count()
        enrolled_required_count = 2600  # Example required count

        if enrolled_required_count > 0:
            enrolled_progress = round(
                (enrolled_count / enrolled_required_count) * 100, 1
            )
        else:
            enrolled_progress = 0
        
        # ---- Substudy 2 ----
        completed_count = qs.filter(
            diagnosis__tb_outcome2__in=[1, 2, 3, 4, 5, 6]
        ).count()
        
        substudy2_count = qs.filter(
            clinic_laboratory__xpert_mtb__in=[2,3,4,5,6]
        ).count()
        
        if substudy2_count > 0:
            substudy2_progress = round(completed_count / substudy2_count * 100, 1)
        else:
            substudy2_progress = 0
            
            
        # =========================
        # Substudy 2 (ENROLLED ONLY)
        # =========================
        substudy2_enrolled_qs = Enrollment.objects.filter(
            screening__in=qs,
            screening__clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6]
        )

        substudy2_enrolled_count = substudy2_enrolled_qs.count()
        substudy2_required_count = 1600  # Example required count

        if substudy2_required_count > 0:
            substudy2_enrolled_progress = round(
                (substudy2_enrolled_count / substudy2_required_count) * 100, 1
            )
        else:
            substudy2_enrolled_progress = 0
            
            
        # =========================
        # Substudy 4 (ENROLLED ONLY)
        # =========================
        substudy4_enrolled_qs = Enrollment.objects.filter(
            screening__in=qs,
            screening__clinic_laboratory__xpert_mtb__in=[1, 7, 8, 9]
        )

        substudy4_enrolled_count = substudy4_enrolled_qs.count()
        substudy4_required_count = 1000  # Example required count

        if substudy4_required_count > 0:
            substudy4_enrolled_progress = round(
                (substudy4_enrolled_count / substudy4_required_count) * 100, 1
            )
        else:
            substudy4_enrolled_progress = 0

        context.update(
            {
                "screened_count": screened_count,
                "eligible_count": eligible_count,
                "enrolled_count": enrolled_count,
                "completed_count": completed_count,
                "substudy2_count": substudy2_count,
                "substudy2_progress": substudy2_progress,
                
                # Enrollment
                "enrolled_progress": enrolled_progress,
                "enrolled_required_count": enrolled_required_count,
                
                # Substudy 2 (Enrolled Only)
                "substudy2_enrolled_count": substudy2_enrolled_count,
                "substudy2_required_count": substudy2_required_count,
                "substudy2_enrolled_progress": substudy2_enrolled_progress,
                
                # Substudy 4 (ENROLLED ONLY)
                "substudy4_enrolled_count": substudy4_enrolled_count,
                "substudy4_required_count": substudy4_required_count,
                "substudy4_enrolled_progress": substudy4_enrolled_progress,
            }
        )

        # --- Zone or Site Aggregation ---
        zone_id = self.request.GET.get("zone")
        if screened_count == 0:
            context["zone_labels_json"] = json.dumps([])
            context["zone_values_json"] = json.dumps([])
        else:
            if zone_id:
                site_agg = (
                    qs.values("site__id", "site__name")
                    .annotate(count=Count("id"))
                    .order_by("site__name")
                )
                context["zone_labels_json"] = json.dumps(
                    [s["site__name"] for s in site_agg]
                )
                context["zone_values_json"] = json.dumps(
                    [int(s["count"]) for s in site_agg]
                )
            else:
                zone_agg = (
                    qs.values(
                        "site__district__region__zone__id",
                        "site__district__region__zone__name",
                    )
                    .annotate(count=Count("id"))
                    .order_by("site__district__region__zone__name")
                )
                context["zone_labels_json"] = json.dumps(
                    [z["site__district__region__zone__name"] for z in zone_agg]
                )
                context["zone_values_json"] = json.dumps(
                    [int(z["count"]) for z in zone_agg]
                )

        # --- Monthly Trends (existing) ---
        qs_time = qs
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        if start_date and end_date:
            qs_time = qs_time.filter(screening_date__range=[start_date, end_date])

        time_datasets = []
        if zone_id:
            sites = qs_time.values("site__id", "site__name").distinct()
            for site in sites:
                site_qs = qs_time.filter(site_id=site["site__id"])
                counts = (
                    site_qs.annotate(month=TruncMonth("screening_date"))
                    .values("month")
                    .annotate(count=Count("id"))
                    .order_by("month")
                )
                months = [c["month"].strftime("%Y-%m") for c in counts]
                values = [int(c["count"]) for c in counts]
                time_datasets.append(
                    {"label": site["site__name"], "data": values, "dates": months}
                )
        else:
            for zone in role_context["zones"]:
                zone_qs = qs_time.filter(site__district__region__zone=zone)
                counts = (
                    zone_qs.annotate(month=TruncMonth("screening_date"))
                    .values("month")
                    .annotate(count=Count("id"))
                    .order_by("month")
                )
                months = [c["month"].strftime("%Y-%m") for c in counts]
                values = [int(c["count"]) for c in counts]
                time_datasets.append(
                    {"label": zone.name, "data": values, "dates": months}
                )

        all_months = sorted(
            set(m for dataset in time_datasets for m in dataset["dates"])
        )
        for dataset in time_datasets:
            data_dict = dict(zip(dataset["dates"], dataset["data"]))
            dataset["data"] = [int(data_dict.get(m, 0)) for m in all_months]

        context["time_labels_json"] = json.dumps(all_months)
        context["time_datasets_json"] = json.dumps(time_datasets)

        # --- Substudy Counts ---
        sub_labels, sub2_values, sub4_values = [], [], []
        if zone_id:
            sites = qs_time.values("site__id", "site__name").distinct()
            for site in sites:
                lab_qs = ClinicLaboratory.objects.filter(
                    screening__site_id=site["site__id"]
                )
                if start_date and end_date:
                    lab_qs = lab_qs.filter(
                        screening__screening_date__range=[start_date, end_date]
                    )
                sub2_values.append(
                    int(lab_qs.filter(xpert_mtb__in=[2, 3, 4, 5, 6]).count())
                )
                sub4_values.append(
                    int(lab_qs.filter(xpert_mtb__in=[1, 7, 8, 9]).count())
                )
                sub_labels.append(site["site__name"])
        else:
            for zone in role_context["zones"]:
                lab_qs = ClinicLaboratory.objects.filter(
                    screening__site__district__region__zone=zone
                )
                if start_date and end_date:
                    lab_qs = lab_qs.filter(
                        screening__screening_date__range=[start_date, end_date]
                    )
                sub2_values.append(
                    int(lab_qs.filter(xpert_mtb__in=[2, 3, 4, 5, 6]).count())
                )
                sub4_values.append(
                    int(lab_qs.filter(xpert_mtb__in=[1, 7, 8, 9]).count())
                )
                sub_labels.append(zone.name)

        context["substudy_labels_json"] = json.dumps(sub_labels)
        context["sub2_values_json"] = json.dumps(sub2_values)
        context["sub4_values_json"] = json.dumps(sub4_values)

        # --- Last 7 Days Trend (integer safe) ---
        today = timezone.now().date()
        last7days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        last7days_labels = [d.strftime("%b %d") for d in last7days]
        last7days_values = [int(qs.filter(screening_date=d).count()) for d in last7days]

        context["last7days_labels_json"] = json.dumps(last7days_labels)
        context["last7days_values_json"] = json.dumps(last7days_values)

        # --- This Month Trend (By Zone) ---
        first_day = today.replace(day=1)
        this_month_qs = qs.filter(screening_date__gte=first_day)

        # Group by zone
        month_zone_agg = (
            this_month_qs.values("site__district__region__zone__name")
            .annotate(count=Count("id"))
            .order_by("site__district__region__zone__name")
        )

        if month_zone_agg.exists():
            this_month_labels = [
                z["site__district__region__zone__name"] or "Unknown"
                for z in month_zone_agg
            ]
            this_month_values = [int(z["count"]) for z in month_zone_agg]
        else:
            this_month_labels = []
            this_month_values = []

        context["this_month_labels_json"] = json.dumps(this_month_labels)
        context["this_month_values_json"] = json.dumps(this_month_values)

        # --- Fallback if no screenings ---
        if screened_count == 0:
            context["message"] = "No screening data available."

        return context
