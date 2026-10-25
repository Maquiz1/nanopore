# nanopore/views/status.py
from nanopore.substudy import OUTCOMES, SUBSTUDY_2, SUBSTUDY_KEYS, substudy_case, substudy_q
from django.views.generic import ListView
from nanopore.models import Screening,Enrollment,Diagnosis,ClinicLaboratory,ZonalLaboratory,RegimenChanges
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context
from utils import access
from utils.access import assigned_locations, legacy_role_flags
from utils.access_mixins import AnyFormAccessMixin
from django.db.models import Case, When, Value, CharField, Q
from django.utils.http import urlencode


class FormStatusListView(AnyFormAccessMixin, ListView):
    access_forms = access.ALL_FORMS
    model = Screening
    template_name = "nanopore/form_status/form_status_list.html"
    context_object_name = "screenings"
    paginate_by = 10  # optional for large datasets

    def get_queryset(self):
        qs = Screening.objects.select_related(
            "enrollment",
            "clinic_laboratory",
            "zonal_laboratory",
            "diagnosis",
            "site",
            "site__district",
            "site__district__region",
            "site__district__region__zone",
        )

        # Role-based filtering
        qs = filter_queryset_by_user_role(self.request.user, qs)

        # GET filters
        zone_id = self.request.GET.get("zone")
        site_id = self.request.GET.get("site")
        pid = self.request.GET.get("pid")
        unique_lab_no = self.request.GET.get("unique_lab_no")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        status = self.request.GET.get("status")  # 🔹 Status filter
        list_type = self.request.GET.get("list_type", "screened")  # default to all screenings
        substudy = self.request.GET.get("substudy")  # 🔹 New filter


        if zone_id:
            qs = qs.filter(site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(site_id=site_id)
        if pid:
            qs = qs.filter(pid__icontains=pid)
        if start_date and end_date:
            qs = qs.filter(screening_date__range=[start_date, end_date])
        if unique_lab_no:
            # qs = qs.filter(Q(clinic_laboratory__unique_lab_no__icontains=unique_lab_no) | Q(zonal_laboratory__unique_lab_no__icontains=unique_lab_no) )
            qs = qs.filter(Q(zonal_laboratory__unique_lab_no__icontains=unique_lab_no))

        # 🔹 Filter by eligibility status using correct field
        if status == "eligible":
            qs = qs.filter(eligible=True)
        elif status == "not_eligible":
            qs = qs.filter(eligible=False)
            
            
        # 🔹 Dynamic list type filter
        if list_type == "eligible":
            qs = qs.filter(eligible=True)
        elif list_type == "enrolled":
            enrolled_screenings = Enrollment.objects.values_list("screening_id", flat=True)
            qs = qs.filter(id__in=enrolled_screenings)
        elif list_type == "completed":
            # Completed = Substudy 2 enrolled with a treatment outcome (nanopore/substudy.py)
            qs = qs.filter(substudy_q(SUBSTUDY_2), enrollment__isnull=False, diagnosis__tb_outcome2__in=OUTCOMES)
        
            
            
        # 🔹 Annotate substudy (one definition: nanopore/substudy.py)
        qs = qs.annotate(substudy_case=substudy_case())

        # 🔹 Substudy filter
        if substudy in SUBSTUDY_KEYS:
            qs = qs.filter(substudy_q(SUBSTUDY_KEYS[substudy]))


        # # Substudy filter using property logic
        # if substudy:
        #     filtered_ids = []
        #     for screening in qs:
        #         if screening.substudy.lower().replace(" ", "") == substudy.lower():
        #             filtered_ids.append(screening.id)
        #     qs = qs.filter(id__in=filtered_ids)

        return qs.order_by("-screening_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # # Include your filter values as before
        # filters = {}
        # for key in ['zone', 'site', 'pid', 'start_date', 'end_date', 'status', 'list_type', 'substudy']:
        #     value = self.request.GET.get(key)
        #     if value:
        #         filters[key] = value

        # context['query_params'] = urlencode(filters)
    
        # Add zones and sites for filter dropdowns
        role_context = get_role_context(self.request.user)
        context.update(role_context)
        
        # Explicit Profile Assignments for Header Display
        assigned_zones, assigned_sites = assigned_locations(self.request.user)
        context.update({
            "assigned_zones": assigned_zones,
            "assigned_sites": assigned_sites,
        })

        # Role flags (union of all the user's roles)
        context.update(legacy_role_flags(self.request.user))

        # Keep GET params for form persistence
        context['selected_zone'] = self.request.GET.get("zone", "")
        context['selected_site'] = self.request.GET.get("site", "")
        context['selected_pid'] = self.request.GET.get("pid", "")
        context['selected_unique_lab_no'] = self.request.GET.get("unique_lab_no", "")
        context['selected_start_date'] = self.request.GET.get("start_date", "")
        context['selected_end_date'] = self.request.GET.get("end_date", "")
        context['selected_status'] = self.request.GET.get("status", "")  # 🔹 Pass status to template
        context['list_type'] = self.request.GET.get("list_type", "screened")
        context['selected_substudy'] = self.request.GET.get("substudy", "")

        # 🔹 Build query_params string for pagination
        query_dict = {}
        if context['selected_zone']:
            query_dict['zone'] = context['selected_zone']
        if context['selected_site']:
            query_dict['site'] = context['selected_site']
        if context['selected_pid']:
            query_dict['pid'] = context['selected_pid']
        if context['selected_start_date']:
            query_dict['start_date'] = context['selected_start_date']
        if context['selected_end_date']:
            query_dict['end_date'] = context['selected_end_date']
        if context['selected_unique_lab_no']:
            query_dict['unique_lab_no'] = context['selected_unique_lab_no']
        if context['selected_status']:
            query_dict['status'] = context['selected_status']
        if context['list_type']:
            query_dict['list_type'] = context['list_type']
        if context['selected_substudy']:
            query_dict['substudy'] = context['selected_substudy']

        context['query_params'] = urlencode(query_dict)

        return context
