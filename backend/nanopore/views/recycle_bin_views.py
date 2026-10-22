from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView

from nanopore.models import DeletedRecord, RegimenChanges
from nanopore.recycle_bin import RestoreError, restore
from utils import access
from utils.access_mixins import FeatureAccessMixin, FormAccessMixin, SoftDeleteMixin
from utils.roles import get_role_context

__all__ = [
    "RecycleBinListView", "RecycleBinDetailView", "RecycleBinRestoreView",
    "RegimenChangesRecordDeleteView", "RegimenChangesListView",
]

MODEL_LABELS = {
    "Screening": "Screening",
    "Enrollment": "Enrollment",
    "ClinicLaboratory": "Clinic Laboratory",
    "ZonalLaboratory": "Zonal Laboratory",
    "EdcsTblisZonal": "EDCS / TBLIS",
    "Diagnosis": "Diagnosis",
    "RegimenChanges": "Regimen Change",
}


class RecycleBinListView(FeatureAccessMixin, ListView):
    access_feature = access.DELETE_RECORDS
    model = DeletedRecord
    template_name = "nanopore/recycle_bin/recycle_bin_list.html"
    context_object_name = "entries"
    paginate_by = 25

    def get_queryset(self):
        qs = DeletedRecord.objects.select_related("deleted_by", "restored_by").defer("payload")
        model = self.request.GET.get("model")
        pid = self.request.GET.get("pid", "").strip()
        status = self.request.GET.get("status", "deleted")
        if model:
            qs = qs.filter(model_name=model)
        if pid:
            qs = qs.filter(pid__icontains=pid)
        if status == "deleted":
            qs = qs.filter(restored_at__isnull=True)
        elif status == "restored":
            qs = qs.filter(restored_at__isnull=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_labels"] = MODEL_LABELS
        context["selected_model"] = self.request.GET.get("model", "")
        context["selected_pid"] = self.request.GET.get("pid", "")
        context["selected_status"] = self.request.GET.get("status", "deleted")
        query = self.request.GET.copy()
        query.pop("page", None)
        context["query_params"] = query.urlencode()
        return context


class RecycleBinDetailView(FeatureAccessMixin, DetailView):
    access_feature = access.DELETE_RECORDS
    model = DeletedRecord
    template_name = "nanopore/recycle_bin/recycle_bin_detail.html"
    context_object_name = "entry"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["records"] = [
            {
                "model": item["model"].split(".")[-1],
                "pk": item["pk"],
                "fields": sorted(item["fields"].items()),
            }
            for item in self.object.payload
        ]
        return context


class RecycleBinRestoreView(FeatureAccessMixin, View):
    access_feature = access.DELETE_RECORDS

    def post(self, request, pk):
        entry = get_object_or_404(DeletedRecord, pk=pk)
        try:
            restore(entry, request.user)
        except RestoreError as exc:
            messages.error(request, str(exc))
            return redirect("nanopore:recycle-bin-detail", pk=entry.pk)
        messages.success(request, f"Restored {entry.model_name} {entry.pid} ({entry.total_records} record(s)).")
        return redirect("nanopore:recycle-bin")


class RegimenChangesRecordDeleteView(SoftDeleteMixin, DeleteView):
    access_form = access.REGIMEN
    model = RegimenChanges
    success_url = reverse_lazy("nanopore:regimen-list")


class RegimenChangesListView(FormAccessMixin, ListView):
    access_form = access.REGIMEN
    model = RegimenChanges
    template_name = "nanopore/regimen/regimen_list_page.html"
    context_object_name = "object_list"
    paginate_by = 25

    def get_queryset(self):
        qs = self.scope(
            RegimenChanges.objects.select_related(
                "screening__site__district__region__zone", "screening__diagnosis", "changes", "reason",
            )
        )
        zone_id = self.request.GET.get("zone")
        site_id = self.request.GET.get("site")
        pid = self.request.GET.get("pid")
        if zone_id:
            qs = qs.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(screening__site_id=site_id)
        if pid:
            qs = qs.filter(screening__pid__icontains=pid)
        return qs.order_by("screening__pid", "date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_role_context(self.request.user))
        return context
