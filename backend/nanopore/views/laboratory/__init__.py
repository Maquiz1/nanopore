from .clinic import ClinicLaboratoryListView
from .clinic import ClinicLaboratoryDetailView
from .clinic import ClinicLaboratoryCreateView
from .clinic import ClinicLaboratoryUpdateView
from .clinic import ClinicLaboratoryDeleteView


from .zonal import ZonalLaboratoryListView
from .zonal import ZonalLaboratoryDetailView
from .zonal import ZonalLaboratoryCreateView    
from .zonal import ZonalLaboratoryUpdateView
from .zonal import ZonalLaboratoryDeleteView

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
]
