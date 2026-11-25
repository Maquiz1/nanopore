"""Accept / Undo an item of a check list (reports/services/accepted.py)."""
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from reports.services import accepted as acc
from reports.services.accepted_lists import find
from utils import access
from utils.access_mixins import FeatureAccessMixin


class AcceptCheckView(FeatureAccessMixin, View):
    access_feature = access.ACCEPT_CHECKS
    http_method_names = ["post"]

    def post(self, request):
        list_key, check_key, oid = request.POST.get("list", ""), request.POST.get("check", ""), request.POST.get("oid", "")
        action, reason = request.POST.get("action"), request.POST.get("reason", "").strip()
        if list_key not in acc.LISTS:
            messages.error(request, "Unknown list.")
        elif action == "undo":
            if acc.undo(request.user, list_key, check_key, oid):
                messages.success(request, "Put back on the list.")
        elif action == "accept":
            item = find(request.user, list_key, check_key, oid)
            if item is None:
                messages.error(request, "This item is not on the list any more.")
            elif not reason:
                messages.error(request, "Give the reason it is correct.")
            else:
                acc.accept(request.user, list_key, check_key, oid, item.values, reason[:500],
                           screening=item.screening, zonal_lab=item.zonal_lab)
                messages.success(request, "Accepted: it is on the Accepted tab now. "
                                          "It comes back to the list if its data changes.")
        back = request.POST.get("back", "")
        if not url_has_allowed_host_and_scheme(back, {request.get_host()}, request.is_secure()):
            back = "/"
        return HttpResponseRedirect(back)
