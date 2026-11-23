from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404, HttpResponse
from django.views import View
from django.views.generic import TemplateView

from django.apps import apps

from utils import access
from utils.access import export_queryset, exports_all_sites
from utils.access_mixins import FeatureAccessMixin
from reports import data_dictionary
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
    """Codebook downloads for every logged-in user (no participant data)."""
    template_name = "reports/codebook/codebook.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = "codebook"
        context["forms"] = [(key, title) for key, (title, _) in CODEBOOK_FORMS.items()]
        context["version"] = codebook_version()
        issued = data_dictionary.versions()
        context["dictionary"] = issued[0] if issued else None
        context["dictionary_earlier"] = issued[1:]
        context["dictionary_log"] = dict((version, (date, text)) for version, date, text in data_dictionary.CHANGE_LOG)
        return context


class DataDictionaryDownloadView(LoginRequiredMixin, View):
    """An issued data dictionary version, exactly as on the server (variables, codes and mapping rules; no participant data)."""

    def get(self, request, version):
        path = dict(data_dictionary.versions()).get(version)
        if path is None:
            raise Http404("No such data dictionary version on this server.")
        return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)


class DataExportView(FeatureAccessMixin, TemplateView):
    """Data export: data specialists, data managers, statisticians and admins."""
    access_feature = access.EXPORTS
    template_name = "reports/codebook/codebook.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["page"] = "export"
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
