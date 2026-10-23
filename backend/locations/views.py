from django.contrib.auth.mixins import LoginRequiredMixin
from utils import access
from utils.access_mixins import FeatureAccessMixin
from django.views.generic import ListView, DetailView
from .models import Country, Region, District, Site

class CountryListView(LoginRequiredMixin, ListView):
    model = Country
    template_name = 'locations/country_list.html'

class CountryDetailView(LoginRequiredMixin, DetailView):
    model = Country
    template_name = 'locations/country_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['regions'] = Region.objects.filter(country=self.object)
        return context

class RegionDetailView(LoginRequiredMixin, DetailView):
    model = Region
    template_name = 'locations/region_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['districts'] = District.objects.filter(region=self.object)
        return context

class DistrictDetailView(LoginRequiredMixin, DetailView):
    model = District
    template_name = 'locations/district_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sites'] = Site.objects.filter(district=self.object)
        return context

class SiteDetailView(LoginRequiredMixin, DetailView):
    model = Site
    template_name = 'locations/site_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        district = self.object.district
        region = district.region
        country = region.country
        context.update({
            'district': district,
            'region': region,
            'country': country
        })
        return context
    
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Site
from .forms import SiteForm  # We'll create this form next

# ---------------------------
# List all sites
# ---------------------------
class AllSitesListView(LoginRequiredMixin, ListView):
    model = Site
    template_name = 'locations/all_sites.html'
    context_object_name = 'sites'
    
    def get_queryset(self):
        return Site.objects.all().order_by('pid_prefix')  # or '-created_at' for newest first


# ---------------------------
# Add new site
# ---------------------------
class SiteCreateView(FeatureAccessMixin, CreateView):
    access_feature = access.SYSTEM_ADMIN
    model = Site
    form_class = SiteForm
    template_name = 'locations/site_form.html'

    def get_success_url(self):
        return reverse_lazy('locations:all-sites')


# ---------------------------
# Edit existing site
# ---------------------------
class SiteUpdateView(FeatureAccessMixin, UpdateView):
    access_feature = access.SYSTEM_ADMIN
    model = Site
    form_class = SiteForm
    template_name = 'locations/site_form.html'

    def get_success_url(self):
        return reverse_lazy('locations:all-sites')
