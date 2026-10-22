from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.views import View
from django.views.generic import TemplateView

from reports.codebook import CODEBOOK_FORMS, build_codebook, codebook_version, to_excel, to_pdf

CONTENT_TYPES = {
    "excel": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
    "pdf": ("application/pdf", "pdf"),
}


class CodebookView(LoginRequiredMixin, TemplateView):
    """Lists the forms with Excel / PDF codebook downloads. A codebook holds no participant data."""
    template_name = "reports/codebook/codebook.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["forms"] = [(key, title) for key, (title, _) in CODEBOOK_FORMS.items()]
        context["version"] = codebook_version()
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
