from django.views import View
from django.http import JsonResponse
from nanopore.models import Screening, Site

class CheckPIDView(View):
    def get(self, request, *args, **kwargs):
        pid1 = request.GET.get('pid1', '').strip()
        site_id = request.GET.get('site_id')
        pid_prefix = ""
        if site_id:
            site = Site.objects.filter(id=site_id).first()
            pid_prefix = site.pid_prefix if site else ""
        final_pid = f"{pid_prefix}{pid1}"
        exists = Screening.objects.filter(pid=final_pid).exists()
        return JsonResponse({'exists': exists, 'pid': final_pid})
