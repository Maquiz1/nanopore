from .clinic import ClinicLaboratoryListView
from .clinic import ClinicLaboratoryDetailView
from .clinic import ClinicLaboratoryCreateView
from .clinic import ClinicLaboratoryUpdateView
from .clinic import ClinicLaboratoryDeleteView
from .clinic import ClinicLaboratoryFormView
from .clinic import ClinicLabCsvUploadView

from .zonal import ZonalLaboratoryListView
from .zonal import ZonalLaboratoryDetailView
from .zonal import ZonalLaboratoryCreateView    
from .zonal import ZonalLaboratoryUpdateView
from .zonal import ZonalLaboratoryDeleteView
from .zonal import ZonalLabFormView
from .zonal import ZonalLabCsvUploadView

from .edcs_tblis import EdcsTBLISLaboratoryListView
from .edcs_tblis import EdcsTBLISCsvUploadView
from .edcs_tblis import EdcsTblisFormView


__all__ = [
    "ClinicLaboratoryListView",
    "ClinicLaboratoryDetailView",
    "ZonalLaboratoryListView",
    "ZonalLaboratoryDetailView",
    "ClinicLaboratoryCreateView",
    "ClinicLaboratoryUpdateView",
    "ClinicLaboratoryDeleteView",
    "ZonalLaboratoryCreateView",
    "ZonalLaboratoryUpdateView",
    "ZonalLaboratoryDeleteView",
    "ClinicLaboratoryFormView",
    "ZonalLabFormView",  # new form view
    "ClinicLabCsvUploadView",
    "ZonalLabCsvUploadView",
    
    #EDCS-TBLIS
    "EdcsTBLISLaboratoryListView",
    "EdcsTBLISCsvUploadView",
    "EdcsTblisFormView",  # new form view
]
