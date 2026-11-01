# reports/views/queries/laboratory/zonal/ctrl_dar_work_view.py
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View

from reports.services.zonal_dq.ctrl import get_dar_work
from utils import access
from utils.access_mixins import AnyFormAccessMixin

FORM_URLS = {"nanopore": "nanopore:ctrl-dar-nanopore", "lpa": "nanopore:ctrl-dar-lpa"}


class CtrlDarWorkView(AnyFormAccessMixin, View):
    """CTRL's to-do lists for Dar es Salaam: Nanopore and LPA checkboxes."""
    access_forms = (access.CTRL_ISOLATES,)
    template_name = "reports/data_quality/laboratory/zonal/ctrl_dar_work.html"
    paginate_by = 50

    def get(self, request):
        work = get_dar_work(request.user)
        search = request.GET.get("q", "").strip()
        tab = request.GET.get("tab") if request.GET.get("tab") in work else "nanopore"
        tabs = []
        for key, (label, qs) in work.items():
            if search:
                qs = qs.filter(screening__pid__icontains=search) | qs.filter(unique_lab_no__icontains=search)
                work[key] = (label, qs)
            tabs.append({"key": key, "label": label, "count": qs.count()})
        page = Paginator(work[tab][1], self.paginate_by).get_page(request.GET.get("page"))
        return render(request, self.template_name, {
            "tabs": tabs, "tab": tab, "page_obj": page, "search": search, "form_url": FORM_URLS[tab],
            "can_edit": access.can_edit(request.user, access.CTRL_ISOLATES),
        })
