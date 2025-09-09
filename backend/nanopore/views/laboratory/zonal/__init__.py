from .zonal_laboratory_list import ZonalLaboratoryListView
from .zonal_laboratory_detail import ZonalLaboratoryDetailView
from .zonal_laboratory_create import ZonalLaboratoryCreateView
from .zonal_laboratory_update import ZonalLaboratoryUpdateView
from .zonal_laboratory_delete import ZonalLaboratoryDeleteView
from .zonal_laboratory_form_view import ZonalLabFormView  # new form view
from .zonal_laboratory_upload_values import ZonalLabCsvUploadView


__all__ = [
    "ZonalLaboratoryListView",
    "ZonalLaboratoryDetailView",
    "ZonalLaboratoryCreateView",
    "ZonalLaboratoryUpdateView",
    "ZonalLaboratoryDeleteView",
    "ZonalLabFormView",  # new form view
    "ZonalLabCsvUploadView",
]
