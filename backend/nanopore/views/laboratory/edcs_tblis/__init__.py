from .edcs_tblis_list_view import EdcsTBLISLaboratoryListView
# from .zonal_laboratory_detail import ZonalLaboratoryDetailView
# from .zonal_laboratory_create import ZonalLaboratoryCreateView
# from .zonal_laboratory_update import ZonalLaboratoryUpdateView
# from .zonal_laboratory_delete import ZonalLaboratoryDeleteView
from .edcs_tblis_laboratory_form_view import EdcsTblisFormView  # new form view
from .edcs_tblis_upload_view import EdcsTBLISCsvUploadView

__all__ = [
    "EdcsTBLISLaboratoryListView",
    # "ZonalLaboratoryDetailView",
    # "ZonalLaboratoryCreateView",
    # "ZonalLaboratoryUpdateView",
    # "ZonalLaboratoryDeleteView",
    "EdcsTblisFormView",  # new form view
    "EdcsTBLISCsvUploadView",
]
