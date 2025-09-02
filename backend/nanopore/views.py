from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Screening

# List all screenings
class ScreeningListView(ListView):
    model = Screening
    template_name = "nanopore/screening/screening_list.html"
    context_object_name = "screenings"
    ordering = ["zone", "facility_id", "pid"]

# View details of a single screening
class ScreeningDetailView(DetailView):
    model = Screening
    template_name = "nanopore/screening/screening_detail.html"
    context_object_name = "screening"

# Create new screening
class ScreeningCreateView(CreateView):
    model = Screening
    fields = "__all__"   # or pick specific fields like ['pid','zone','facility_id','screening_date','status']
    template_name = "nanopore/screening/screening_form.html"
    success_url = reverse_lazy("screening-list")

# Update existing screening
class ScreeningUpdateView(UpdateView):
    model = Screening
    fields = "__all__"
    template_name = "nanopore/screening/screening_form.html"
    success_url = reverse_lazy("screening-list")

# Delete screening
class ScreeningDeleteView(DeleteView):
    model = Screening
    template_name = "nanopore/screening/screening_confirm_delete.html"
    success_url = reverse_lazy("screening-list")
