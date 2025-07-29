from django.views.generic import ListView, DetailView
from .models import Country, Region, District, Site

class CountryListView(ListView):
    model = Country
    template_name = 'locations/country_list.html'

class CountryDetailView(DetailView):
    model = Country
    template_name = 'locations/country_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['regions'] = Region.objects.filter(country=self.object)
        return context

class RegionDetailView(DetailView):
    model = Region
    template_name = 'locations/region_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['districts'] = District.objects.filter(region=self.object)
        return context

class DistrictDetailView(DetailView):
    model = District
    template_name = 'locations/district_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sites'] = Site.objects.filter(district=self.object)
        return context

class SiteDetailView(DetailView):
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
