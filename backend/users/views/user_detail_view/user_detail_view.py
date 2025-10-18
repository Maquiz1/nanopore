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


class StaffDetailView(DetailView):
    model = User
    template_name = 'users/staff/staff_detail.html'
    context_object_name = 'staff_member'

    def get_queryset(self):
        return (
            User.objects.select_related(
                'profile',
                'profile__position',
                'profile__site__district__region__zone'
            )
            .prefetch_related('groups')
        )

