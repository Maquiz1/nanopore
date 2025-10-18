from django.views.generic import FormView, ListView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from users.models import Profile, Prefix, Position
from users.forms import StaffForm
from locations.models import Site

User = get_user_model()


def force_logout(request):
    """Forcefully log out the current user and redirect to login page."""
    logout(request)
    return redirect('users:login')


class StaffListView(ListView):
    model = User
    template_name = 'users/staff/staff_list.html'
    context_object_name = 'staff_list'

    def get_queryset(self):
        return (
            # User.objects.filter(is_active=True, is_staff=True)
            User.objects.filter(is_active=True)
            .select_related(
                'profile',
                'profile__position',
                'profile__site__district__region__zone'
            )
            .prefetch_related('groups')
            .order_by('username')
        )

