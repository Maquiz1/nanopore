from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.views import View
from django.views.generic import TemplateView

from django.apps import apps

from utils import access
from utils.access import export_queryset, exports_all_sites, has_feature
from reports.codebook import CODEBOOK_FORMS, build_codebook, codebook_version, to_excel, to_pdf

CONTENT_TYPES = {
    "excel": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
    "pdf": ("application/pdf", "pdf"),
}


# Forms offered in the data export: (model name, title).
EXPORT_FORMS = [
    ("Screening", "Screening (with Regimen Changes)"),
    ("Enrollment", "Enrollment"),
    ("ClinicLaboratory", "Clinic Laboratory"),
    ("ZonalLaboratory", "Zonal Laboratory"),
    ("EdcsTblisZonal", "EDCS / TBLIS"),
    ("Diagnosis", "Diagnosis"),
    ("RegimenChanges", "Regimen Changes"),
]


class CodebookView(LoginRequiredMixin, TemplateView):
    """
    Codebook (everyone; no participant data) and data export (data specialists,
    data managers, statisticians, admins) on one page.
    """
    template_name = "reports/codebook/codebook.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["forms"] = [(key, title) for key, (title, _) in CODEBOOK_FORMS.items()]
        context["version"] = codebook_version()
        context["can_export"] = has_feature(user, access.EXPORTS)
        if context["can_export"]:
            context["exports_all_sites"] = exports_all_sites(user)
            context["export_forms"] = []
            for model_name, title in EXPORT_FORMS:
                model = apps.get_model("nanopore", model_name)
                site_field = "site" if model_name == "Screening" else "screening__site"
                count = export_queryset(user, model.objects.all(), site_field).count()
                context["export_forms"].append((model_name, title, count))
        return context


class CodebookDownloadView(LoginRequiredMixin, View):
    def get(self, request, form_key, fmt):
        if fmt not in CONTENT_TYPES or (form_key != "all" and form_key not in CODEBOOK_FORMS):
            raise Http404("Unknown codebook")
        keys = list(CODEBOOK_FORMS) if form_key == "all" else [form_key]
        codebook = build_codebook(keys)
        content = to_excel(codebook) if fmt == "excel" else to_pdf(codebook)
        content_type, extension = CONTENT_TYPES[fmt]
        name = "all_forms" if form_key == "all" else form_key
        response = HttpResponse(content, content_type=content_type)
        stamp = codebook["version"]["generated"][:10]
        response["Content-Disposition"] = f'attachment; filename="codebook_{name}_{stamp}.{extension}"'
        return response
