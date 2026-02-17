from .forms.missing_form_details_queries_view import MissingFormDetailsQueriesView
from .forms.data_form_quality_pdf_document import DreamFundQueriesPDFView
from .screening.data_screening_quality_view import ScreeningDataQualityReportView
from .enrollment.data_enrollment_quality_view import EnrollmentDataQualityReportView
from .enrollment.data_quality_enrollment_view import EnrollmentDataQualityView
from .laboratory.clinic.data_clinic_quality_view import ClinicDataQualityReportView
from .laboratory.clinic.data_quality_clinic_view import ClinicDataQualityView
from .diagnosis.data_diagnosis_quality_view import DiagnosisDataQualityReportView
from .diagnosis.data_quality_diagnosis_view import DiagnosisDataQualityView
# from .regimen.data_regimen_quality_view import RegimenDataQualityReportView
from .regimen.data_quality_regimen_view import RegimenDataQualityView
from .laboratory.zonal.data_zonal_quality_view_Final_Working import ZonalDataQualityReportView
from .laboratory.zonal.data_zonal_quality_view import ZonalDataQualityView
from .laboratory.edcs_tblis.data_edcs_tblis_quality_view import EdcsTBLISDataQualityView
from .all_queries_overview_dashboard_view import AllOverviewQueriesDashboardView
from .forms.missing_form_queries_dashboard_view import MissingFormQueriesDashboardView
from .forms.specific_form_queries_dashboard_view import SpecificFormQueriesDashboardView

__all__ = [
    "AllOverviewQueriesDashboardView",
    "MissingFormQueriesDashboardView",
    "SpecificFormQueriesDashboardView",
    # "FormsDataQualityReportView",
    "MissingFormDetailsQueriesView",
    # "DataQualityReportPDFView",
    "DreamFundQueriesPDFView",
    "ScreeningDataQualityReportView",
    
    "EnrollmentDataQualityReportView",
    "EnrollmentDataQualityView",
    
    "ClinicDataQualityReportView",
    "ClinicDataQualityView",
    
    "DiagnosisDataQualityReportView",
    "DiagnosisDataQualityView",
    
    # "RegimenDataQualityReportView",
    "RegimenDataQualityView",
    
    "ZonalDataQualityReportView",
    "ZonalDataQualityView",
    "EdcsTBLISDataQualityView",
]
