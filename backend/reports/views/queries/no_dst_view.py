"""Positive culture, no DST (reports/services/no_dst.py): information for the study team, not queries."""
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.views import View

from reports.services.no_dst import GROUPS, no_dst_counts, no_dst_records
from utils import access
from utils.access_mixins import FeatureAccessMixin


class NoDstView(FeatureAccessMixin, View):
    access_feature = access.TBLIS_FOLLOW_UP  # the same people as TB-LIS follow-up
    template_name = "reports/data_quality/no_dst.html"
    paginate_by = 50

    def get(self, request):
        group = request.GET.get("group") if request.GET.get("group") in dict(GROUPS) else "dar"
        search = request.GET.get("q", "").strip()
        records = no_dst_records(request.user, group).select_related(
            "screening__site__district__region__zone", "lj_results", "mgit_results")
        if search:
            records = records.filter(Q(screening__pid__icontains=search) | Q(unique_lab_no__icontains=search))
        counts = no_dst_counts(request.user)
        page = Paginator(records, self.paginate_by).get_page(request.GET.get("page"))
        return render(request, self.template_name, {
            "groups": [{"key": key, "label": label, "count": counts[key]} for key, label in GROUPS],
            "group": group, "page_obj": page, "search": search,
        })
