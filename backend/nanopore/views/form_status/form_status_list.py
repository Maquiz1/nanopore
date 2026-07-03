# nanopore/views/status.py
from lib2to3.fixes.fix_input import context
from django.views.generic import ListView
from nanopore.models import Screening,Enrollment,Diagnosis,ClinicLaboratory,ZonalLaboratory,RegimenChanges
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context
from django.db.models import Case, When, Value, CharField, Q
from django.utils.http import urlencode


class FormStatusListView(ListView):
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
            qs = qs.filter(diagnosis__tb_outcome2__in=[1, 2, 3, 4, 5, 6])
        
            
            
        # 🔹 Annotate substudy
        qs = qs.annotate(
            substudy_case=Case(
                When(
                    clinic_laboratory__xpert_mtb_rif_conducted=1,
                    clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
                    then=Value("Substudy 2")
                ),
                When(
                    Q(clinic_laboratory__xpert_mtb_rif_conducted=1, clinic_laboratory__xpert_mtb__in=[1, 7, 8, 9]) |
                    Q(clinic_laboratory__xpert_mtb_rif_conducted=2),
                    then=Value("Substudy 4")
                ),
                When(
                    Q(clinic_laboratory__xpert_mtb_rif_conducted=1, clinic_laboratory__xpert_mtb__isnull=True) |
                    Q(clinic_laboratory__xpert_mtb_rif_conducted__isnull=True),
                    then=Value("Uncategorized")
                ),
                default=Value("Uncategorized"),
                output_field=CharField(),
            )
        )
        
        # 🔹 Substudy filter
        if substudy:
            if substudy == "substudy2":
                qs = qs.filter(
                    clinic_laboratory__xpert_mtb_rif_conducted=1,
                    clinic_laboratory__xpert_mtb__in=[2,3,4,5,6]
                )
            elif substudy == "substudy4":
                qs = qs.filter(
                    Q(clinic_laboratory__xpert_mtb_rif_conducted=1, clinic_laboratory__xpert_mtb__in=[1,7,8,9]) |
                    Q(clinic_laboratory__xpert_mtb_rif_conducted=2)
                )
            elif substudy == "uncategorized":
                qs = qs.filter(
                    Q(clinic_laboratory__xpert_mtb_rif_conducted=1, clinic_laboratory__xpert_mtb__isnull=True) |
                    Q(clinic_laboratory__xpert_mtb_rif_conducted__isnull=True)
                )
        
        
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
        assigned_zones = []
        assigned_sites = []
        if hasattr(self.request.user, "profile"):
            assigned_zones = list(self.request.user.profile.zones.all())
            explicit_sites = set(self.request.user.profile.sites.all())
            
            # Add sites derived from explicitly assigned zones
            from locations.models import Site
            derived_sites = set(Site.objects.filter(district__region__zone__in=assigned_zones))
            assigned_sites = sorted(list(explicit_sites.union(derived_sites)), key=lambda s: s.name)

        context.update({
            "assigned_zones": assigned_zones,
            "assigned_sites": assigned_sites,
        })
        
        # Explicit group flags to fix template multi-role visibility
        user_groups = [g.upper() for g in self.request.user.groups.values_list('name', flat=True)]
        is_data_specialist = hasattr(self.request.user, "profile") and self.request.user.profile.position and self.request.user.profile.position.name.lower() == "data specialist"
        
        context['is_admin_or_reviewer'] = self.request.user.is_superuser or "ADMIN" in user_groups or "REVIEWER" in user_groups or is_data_specialist
        context['is_admin_only'] = self.request.user.is_superuser or "ADMIN" in user_groups or is_data_specialist
        context['is_reviewer_only'] = "REVIEWER" in user_groups and not context['is_admin_only']
        context['is_lab_tech'] = "LABORATORY_TECHNICIAN" in user_groups
        context['is_nurse_clinician'] = "NURSE" in user_groups or "CLINICIAN" in user_groups

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
