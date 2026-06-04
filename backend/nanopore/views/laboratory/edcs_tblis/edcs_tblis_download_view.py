import csv
from django.http import StreamingHttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from nanopore.models import EdcsTblisZonal


class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        return value


class EdcsTblisDownloadCsvView(LoginRequiredMixin, View):
    """
    Streams EdcsTblisZonal data as CSV using StreamingHttpResponse
    to avoid memory/timeout issues in production with large datasets.
    """

    def get(self, request, *args, **kwargs):
        qs = EdcsTblisZonal.objects.select_related(
            "screening",
            "appearance",
            "culture_performed",
            "microscopy_type",
            "microscopy_results",
            "lj_results",
            "mgit_results",
            "culture_isolate",
            "phenotypic_performed",
            "rifampicin",
            "isoniazid",
            "ethambutol",
            "levofloxacin",
            "moxifloxacin",
            "bedaquiline",
            "linezolid",
            "clofazimine",
            "delamanid",
            "ethionamide",
            "prothionamide",
            "para_aminosalicylic_acid",
            "cycloserine",
            "terizidone",
            "pyrazinamide",
            "amikacin",
            "streptomycin",
            "imipenem",
            "cilastatin",
            "meropenem",
            "xpert_xdr_performed",
            "xpert_xdr_isoniazid",
            "xpert_xdr_fluoroquinolones",
            "xpert_xdr_amikacin",
            "xpert_xdr_kanamycin",
            "xpert_xdr_capreomycin",
            "xpert_xdr_ethionamide",
            "lpa",
            "first_line_lpa",
            "lpa1_mtb",
            "lpa1_rif",
            "second_line_lpa",
            "lpa2_mtb",
            "lpa2_rfluoroquinolones",
            "lpa2_aminoglycosides",
            "lpa2_kanamycin",
            "nanopore_done",
            "nanopore_results",
            "epi_to_me",
            "sequencing_results",
            "sequencing_delayed",
        ).only(
            "screening__pid",
            "unique_lab_no",
            "date_sputum_received",
            "sample_volume",
            "microscopy_date",
            "microscopy_results__id",
            "lj_inoculation_date",
            "lj_results_date",
            "mgit_inoculation_date",
            "mgit_results_date",
            "isolate_date",
            "phenotypic_date_performed",
            "phenotypic_date_results",
            "xpert_xdr_date_performed",
            "first_line_lpa_date",
            "second_line_lpa_date",
            "nanopore_sequencing_date",
            "epi_to_me_version",
            "epi_to_me_date",
            "sequencing_delayed_days",
            "sequencing_delayed_others",
        ).iterator(chunk_size=500)

        def fk_val(obj):
            return obj.id if obj else ""

        def row_gen(queryset):
            header = [
                "pid", "unique_lab_no", "date_sputum_received", "appearance", "sample_volume",
                "culture_performed", "culture_method",
                "microscopy_type", "microscopy_date", "microscopy_results",
                "lj_inoculation_date", "lj_results_date", "lj_results",
                "mgit_inoculation_date", "mgit_results_date", "mgit_results",
                "culture_isolate", "isolate_date",
                "phenotypic_performed", "phenotypic_date_performed", "phenotypic_date_results",
                "rifampicin", "isoniazid", "ethambutol", "levofloxacin", "moxifloxacin",
                "bedaquiline", "linezolid", "clofazimine", "delamanid", "ethionamide",
                "prothionamide", "para_aminosalicylic_acid", "cycloserine", "terizidone",
                "pyrazinamide", "amikacin", "streptomycin", "imipenem", "cilastatin",
                "meropenem",
                "xpert_xdr_performed", "xpert_xdr_date_performed", "xpert_xdr_isoniazid",
                "xpert_xdr_fluoroquinolones", "xpert_xdr_amikacin", "xpert_xdr_kanamycin",
                "xpert_xdr_capreomycin", "xpert_xdr_ethionamide",
                "lpa", "first_line_lpa", "first_line_lpa_date", "first_line_drugs",
                "lpa1_mtb", "lpa1_rif", "lpa1_inh",
                "second_line_lpa", "second_line_lpa_date", "second_line_drugs",
                "lpa2_mtb", "lpa2_rfluoroquinolones", "lpa2_aminoglycosides", "lpa2_kanamycin",
                "nanopore_done", "nanopore_sequencing_date", "nanopore_results",
                "epi_to_me", "epi_to_me_version", "epi_to_me_date",
                "sequencing_results", "sequencing_delayed", "sequencing_delayed_days",
                "sequencing_delayed_others",
            ]
            yield header

            for obj in queryset:
                # M2M fields need separate queries — batch resolved
                try:
                    culture_methods = "|".join(str(m.id) for m in obj.culture_method.all())
                    first_line_drugs = "|".join(str(d.id) for d in obj.first_line_drugs.all())
                    second_line_drugs = "|".join(str(d.id) for d in obj.second_line_drugs.all())
                    lpa1_inh = "|".join(str(d.id) for d in obj.lpa1_inh.all())
                except Exception:
                    culture_methods = first_line_drugs = second_line_drugs = lpa1_inh = ""

                yield [
                    getattr(obj.screening, "pid", ""),
                    obj.unique_lab_no or "",
                    obj.date_sputum_received or "",
                    fk_val(obj.appearance),
                    obj.sample_volume or "",
                    fk_val(obj.culture_performed),
                    culture_methods,
                    fk_val(obj.microscopy_type),
                    obj.microscopy_date or "",
                    fk_val(obj.microscopy_results),
                    obj.lj_inoculation_date or "",
                    obj.lj_results_date or "",
                    fk_val(obj.lj_results),
                    obj.mgit_inoculation_date or "",
                    obj.mgit_results_date or "",
                    fk_val(obj.mgit_results),
                    fk_val(obj.culture_isolate),
                    obj.isolate_date or "",
                    fk_val(obj.phenotypic_performed),
                    obj.phenotypic_date_performed or "",
                    obj.phenotypic_date_results or "",
                    fk_val(obj.rifampicin),
                    fk_val(obj.isoniazid),
                    fk_val(obj.ethambutol),
                    fk_val(obj.levofloxacin),
                    fk_val(obj.moxifloxacin),
                    fk_val(obj.bedaquiline),
                    fk_val(obj.linezolid),
                    fk_val(obj.clofazimine),
                    fk_val(obj.delamanid),
                    fk_val(obj.ethionamide),
                    fk_val(obj.prothionamide),
                    fk_val(obj.para_aminosalicylic_acid),
                    fk_val(obj.cycloserine),
                    fk_val(obj.terizidone),
                    fk_val(obj.pyrazinamide),
                    fk_val(obj.amikacin),
                    fk_val(obj.streptomycin),
                    fk_val(obj.imipenem),
                    fk_val(obj.cilastatin),
                    fk_val(obj.meropenem),
                    fk_val(obj.xpert_xdr_performed),
                    obj.xpert_xdr_date_performed or "",
                    fk_val(obj.xpert_xdr_isoniazid),
                    fk_val(obj.xpert_xdr_fluoroquinolones),
                    fk_val(obj.xpert_xdr_amikacin),
                    fk_val(obj.xpert_xdr_kanamycin),
                    fk_val(obj.xpert_xdr_capreomycin),
                    fk_val(obj.xpert_xdr_ethionamide),
                    fk_val(obj.lpa),
                    fk_val(obj.first_line_lpa),
                    obj.first_line_lpa_date or "",
                    first_line_drugs,
                    fk_val(obj.lpa1_mtb),
                    fk_val(obj.lpa1_rif),
                    lpa1_inh,
                    fk_val(obj.second_line_lpa),
                    obj.second_line_lpa_date or "",
                    second_line_drugs,
                    fk_val(obj.lpa2_mtb),
                    fk_val(obj.lpa2_rfluoroquinolones),
                    fk_val(obj.lpa2_aminoglycosides),
                    fk_val(obj.lpa2_kanamycin),
                    fk_val(obj.nanopore_done),
                    obj.nanopore_sequencing_date or "",
                    fk_val(obj.nanopore_results),
                    fk_val(obj.epi_to_me),
                    obj.epi_to_me_version or "",
                    obj.epi_to_me_date or "",
                    fk_val(obj.sequencing_results),
                    fk_val(obj.sequencing_delayed),
                    obj.sequencing_delayed_days or "",
                    obj.sequencing_delayed_others or "",
                ]

        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)

        response = StreamingHttpResponse(
            (writer.writerow(row) for row in row_gen(qs)),
            content_type="text/csv",
        )
        response["Content-Disposition"] = 'attachment; filename="edcs_tblis_zonal_data.csv"'
        return response
