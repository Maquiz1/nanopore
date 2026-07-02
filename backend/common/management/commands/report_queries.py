import os
import pandas as pd
from django.core.management.base import BaseCommand
from nanopore.models import Screening

from django.db.models import Q

class Command(BaseCommand):
    help = "Generate Excel reports for substudy2 and substudy4 without culture results"

    def handle(self, *args, **options):
        # Base queryset: eligible=True, has clinic lab, has tblis lab, and culture_performed is empty or 'No'
        base_qs = Screening.objects.filter(
            eligible=True,
            clinic_laboratory__isnull=False,
            tblis_laboratory__isnull=False
        ).filter(
            Q(tblis_laboratory__culture_performed__isnull=True) | 
            Q(tblis_laboratory__culture_performed__name__icontains='No') |
            Q(tblis_laboratory__culture_performed__name__exact='')
        )
        
        # Substudy 2: xpert_mtb in [2, 3, 4, 5, 6]
        # XpertMTB is a ForeignKey, checking IDs
        substudy2_qs = base_qs.filter(
            clinic_laboratory__xpert_mtb_id__in=[2, 3, 4, 5, 6]
        )
        
        # Substudy 4: xpert_mtb NOT in [2, 3, 4, 5, 6]
        substudy4_qs = base_qs.exclude(
            clinic_laboratory__xpert_mtb_id__in=[2, 3, 4, 5, 6]
        )
        
        # Helper to export qs to excel
        def export_to_excel(qs, filename):
            data = []
            for s in qs:
                # Retrieve site name or ID
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
            if not df.empty:
                df.to_excel(filename, index=False)
                self.stdout.write(self.style.SUCCESS(f"Successfully generated {filename} with {len(df)} records."))
            else:
                self.stdout.write(self.style.WARNING(f"No records found for {filename}."))

        output_dir = os.path.expanduser("~/Documents/WORKS/NIMR/DREAM/ZONAL_EDCS_TBLIS/_2026/_2026_06_05/")
        os.makedirs(output_dir, exist_ok=True)

        file2 = os.path.join(output_dir, 'substudy2_not_having_culture_results.xlsx')
        self.stdout.write(f"Generating {file2}...")
        export_to_excel(substudy2_qs, file2)
        
        file4 = os.path.join(output_dir, 'substudy4_not_having_culture_results.xlsx')
        self.stdout.write(f"Generating {file4}...")
        export_to_excel(substudy4_qs, file4)

