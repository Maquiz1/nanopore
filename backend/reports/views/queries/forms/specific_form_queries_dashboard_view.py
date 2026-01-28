from django.views.generic import TemplateView
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

class SpecificFormQueriesDashboardView(TemplateView):
    template_name = "reports/data_quality/query_dashboard/specific_form_queries_dashboard.html"
    
    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            # ── Your role logic (you probably already have this somewhere) ──
            role_context = get_role_context(self.request.user)
            
            is_zonal_lab = role_context.get("is_zonal_lab", False)
            is_admin     = role_context.get("is_admin", False)
            is_reviewer  = role_context.get("is_reviewer", False)
            is_privileged = is_admin or is_reviewer

            # ── This is where you add the flags to the template context ──
            context.update({
                'is_admin': is_admin,
                'is_reviewer': is_reviewer,
                'is_zonal_lab': is_zonal_lab,
                'is_privileged': is_privileged,
            })

            # Probably already adding forms_report_total via context processor
            # If not — add it here too:
            # context['forms_report_total'] = forms_report_total(self.request)['forms_report_total']

            return context