from django.views.generic import ListView
from django.contrib.auth import get_user_model
from users.models import Prefix, Position
from locations.models import Site, Zone
from django.contrib.auth.models import Group
from django.db.models import Q

User = get_user_model()

class StaffListView(ListView):
    model = User
    template_name = 'users/staff/staff_list.html'
    context_object_name = 'staff_list'
    paginate_by = 2  # Adjust per page

    def get_queryset(self):
        qs = User.objects.filter(is_active=True).select_related(
            'profile',
            'profile__position',
            'profile__site__district__region__zone'
        ).prefetch_related('groups').order_by('username')

        # FILTERS
        username = self.request.GET.get('username')
        full_name = self.request.GET.get('full_name')
        email = self.request.GET.get('email')
        prefix = self.request.GET.get('prefix')
        position = self.request.GET.get('position')
        site = self.request.GET.get('site')
        zone = self.request.GET.get('zone')
        group = self.request.GET.get('group')

        if username:
            qs = qs.filter(username__icontains=username)
        if full_name:
            qs = qs.filter(Q(first_name__icontains=full_name) | Q(last_name__icontains=full_name))
        if email:
            qs = qs.filter(email__icontains=email)
        if prefix:
            qs = qs.filter(profile__prefix_id=prefix)
        if position:
            qs = qs.filter(profile__position_id=position)
        if site:
            qs = qs.filter(profile__site_id=site)
        if zone:
            qs = qs.filter(profile__site__district__region__zone_id=zone)
        if group:
            qs = qs.filter(groups__id=group)

        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['prefixes'] = Prefix.objects.all()
        context['positions'] = Position.objects.all()
        context['sites'] = Site.objects.all()
        context['zones'] = Zone.objects.all()
        context['groups'] = Group.objects.all()
        return context
