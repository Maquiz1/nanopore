from utils import access
from utils.access import export_queryset
from utils.access_mixins import FeatureAccessMixin
import pandas as pd
from django.http import HttpResponse
from django.views import View
from django.db.models import Q
from nanopore.models import Screening
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.substudy import SUBSTUDY_2, SUBSTUDY_4, substudy_q

class SubstudyDownloadView(FeatureAccessMixin, View):
    access_feature = access.REPORTS
    def get(self, request, *args, **kwargs):
        query_type = kwargs.get('query_type')
        
        base_qs = export_queryset(request.user, Screening.objects.all(), "site").filter(
            eligible=True,
            clinic_laboratory__isnull=False,
            tblis_laboratory__isnull=False
        ).filter(
            Q(tblis_laboratory__culture_performed__isnull=True) | 
            Q(tblis_laboratory__culture_performed__name__icontains='No') |
            Q(tblis_laboratory__culture_performed__name__exact='')
        )

        if query_type == 'substudy2':
            qs = base_qs.filter(substudy_q(SUBSTUDY_2))
            filename = "substudy2_not_having_culture_results.xlsx"
        elif query_type == 'substudy4':
            qs = base_qs.filter(substudy_q(SUBSTUDY_4))
            filename = "substudy4_not_having_culture_results.xlsx"
        else:
            return HttpResponse("Invalid query type", status=400)

        data = []
        for s in qs:
            site_name = ""
            if hasattr(s, 'facility') and s.facility:
                site_name = str(s.facility)
            elif hasattr(s, 'facility_id'):
                site_name = str(s.facility_id)
            elif hasattr(s, 'site'):
                site_name = str(s.site)
            
            data.append({
                'pid': s.pid,
                'site': site_name
            })
        
        df = pd.DataFrame(data)
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        if not df.empty:
            df.to_excel(response, index=False)
        else:
            # Create an empty excel
            df.to_excel(response, index=False)

        return response
