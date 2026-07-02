import csv
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models.discrepancies import TblisNotInEdcs, EdcsNotInTblis, EdcsTblisMismatch

class DiscrepancyDownloadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        discrepancy_type = kwargs.get('discrepancy_type')
        
        response = HttpResponse(content_type='text/csv')
        
        if discrepancy_type == 'edcs_not_in_tblis':
            response['Content-Disposition'] = 'attachment; filename="edcs_records_not_in_tblis.csv"'
            writer = csv.writer(response)
            writer.writerow(['Unique Lab No', 'PID', 'Created At'])
            for obj in EdcsNotInTblis.objects.all():
                writer.writerow([obj.unique_lab_no, obj.pid, obj.created_at])
                
        elif discrepancy_type == 'tblis_not_in_edcs':
            response['Content-Disposition'] = 'attachment; filename="tblis_records_not_in_edcs.csv"'
            writer = csv.writer(response)
            writer.writerow(['Lab No', 'Raw Data', 'Created At'])
            for obj in TblisNotInEdcs.objects.all():
                writer.writerow([obj.labno, str(obj.raw_data), obj.created_at])
                
        elif discrepancy_type == 'mismatches':
            response['Content-Disposition'] = 'attachment; filename="edcs_tblis_mismatches.csv"'
            writer = csv.writer(response)
            writer.writerow(['Lab No', 'PID', 'Field Name', 'EDCS Value', 'TBLIS Value', 'Created At'])
            for obj in EdcsTblisMismatch.objects.all():
                writer.writerow([obj.labno, obj.pid, obj.field_name, obj.edcs_value, obj.tblis_value, obj.created_at])
        
        else:
            return HttpResponse("Invalid discrepancy type", status=400)
            
        return response
