from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView,CreateView
from .models import Household
from .forms import HouseholdForm


class HouseholdListView(LoginRequiredMixin, ListView):
    model = Household
    template_name = 'household/list.html'
    context_object_name = 'households'

    def get_queryset(self):
        # Show only households linked to logged-in user (veo)
        return Household.objects.filter(veo=self.request.user)
    
    
class HouseholdCreateView(LoginRequiredMixin, CreateView):
    model = Household
    form_class = HouseholdForm
    template_name = 'household/create.html'
    success_url = reverse_lazy('household_list')  # Change to your success URL or name

    def form_valid(self, form):
        form.instance.veo = self.request.user  # assign logged-in user here
        return super().form_valid(form)
