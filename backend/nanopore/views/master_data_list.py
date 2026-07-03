from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import Screening
from dashboard.views.dashboard import get_role_context

class MasterDataListView(LoginRequiredMixin, ListView):
    model = Screening
    template_name = "nanopore/master_data_list.html"
    context_object_name = "screenings"
    paginate_by = 10

    def get_queryset(self):
        # Base QuerySet with optimizations
        from django.db.models import Case, When, Value, Q, CharField, Exists, OuterRef
        from nanopore.models import TblisRawData
        qs = Screening.objects.select_related(
            "site", 
            "site__district", 
            "site__district__region", 
            "site__district__region__zone",
            "enrollment",
            "clinic_laboratory",
            "zonal_laboratory",
            "diagnosis",
            "tblis_laboratory"
        ).prefetch_related("regimen_changes")

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
            ),
            has_tblis_raw=Exists(
                TblisRawData.objects.filter(labno=OuterRef('zonal_laboratory__unique_lab_no'))
            )
        )

        # Apply role-based filtering (same as dashboard/form_status)
        role_context = get_role_context(self.request.user)
        assigned_sites = role_context.get("sites", [])

        if not self.request.user.is_superuser:
            qs = qs.filter(site__in=assigned_sites)

        # Handle basic GET filters
        pid_query = self.request.GET.get("pid_labno", "").strip()
        if pid_query:
            qs = qs.filter(
                Q(pid__icontains=pid_query) | 
                Q(zonal_laboratory__unique_lab_no__icontains=pid_query)
            )
            
        zone_query = self.request.GET.get("zone", "").strip()
        if zone_query:
            qs = qs.filter(site__district__region__zone__id=zone_query)
            
        site_query = self.request.GET.get("site", "").strip()
        if site_query:
            qs = qs.filter(site__id=site_query)
            
        substudy_query = self.request.GET.get("substudy", "").strip()
        if substudy_query:
            qs = qs.filter(substudy_case=substudy_query)
            
        eligibility_query = self.request.GET.get("eligibility", "").strip()
        if eligibility_query == "Yes":
            qs = qs.filter(eligible=True)
        elif eligibility_query == "No":
            qs = qs.filter(eligible=False)
            
        # Handle complex Form + Hint filtering
        form_query = self.request.GET.get("form", "").strip()
        hint_query = self.request.GET.get("hint", "").strip()
        
        if form_query and hint_query:
            if form_query in ["enrollment", "clinic", "diagnosis"]:
                rel = {
                    "enrollment": "enrollment",
                    "clinic": "clinic_laboratory",
                    "diagnosis": "diagnosis"
                }[form_query]
                
                if hint_query == "Yes":
                    qs = qs.filter(eligible=True, **{f"{rel}__isnull": False})
                elif hint_query == "No":
                    qs = qs.filter(eligible=True, **{f"{rel}__isnull": True})
                elif hint_query == "N/A":
                    qs = qs.filter(eligible=False, **{f"{rel}__isnull": True})
                elif hint_query == "N/R":
                    qs = qs.filter(eligible=False, **{f"{rel}__isnull": False})
                    
            elif form_query in ["zonal", "edcs_tblis"]:
                rel = "zonal_laboratory" if form_query == "zonal" else "tblis_laboratory"
                if hint_query == "Yes":
                    qs = qs.filter(eligible=True).exclude(substudy_case="Substudy 4").filter(**{f"{rel}__isnull": False})
                elif hint_query == "No":
                    qs = qs.filter(eligible=True).exclude(substudy_case="Substudy 4").filter(**{f"{rel}__isnull": True})
                elif hint_query == "N/A":
                    qs = qs.filter(
                        Q(eligible=False, **{f"{rel}__isnull": True}) | 
                        Q(eligible=True, substudy_case="Substudy 4", **{f"{rel}__isnull": True})
                    )
                elif hint_query == "N/R":
                    qs = qs.filter(
                        Q(eligible=False, **{f"{rel}__isnull": False}) | 
                        Q(eligible=True, substudy_case="Substudy 4", **{f"{rel}__isnull": False})
                    )
                    
            elif form_query == "regimen":
                if hint_query == "Yes":
                    qs = qs.filter(eligible=True, diagnosis__regimen_changed__name__iexact="yes", regimen_changes__isnull=False).distinct()
                elif hint_query == "No":
                    qs = qs.filter(eligible=True, diagnosis__regimen_changed__name__iexact="yes", regimen_changes__isnull=True).distinct()
                elif hint_query == "N/A":
                    qs = qs.filter(
                        Q(eligible=False, regimen_changes__isnull=True) |
                        Q(eligible=True, diagnosis__isnull=True, regimen_changes__isnull=True) |
                        Q(eligible=True, diagnosis__isnull=False, regimen_changes__isnull=True)
                    ).exclude(eligible=True, diagnosis__regimen_changed__name__iexact="yes", regimen_changes__isnull=True)
                elif hint_query == "N/R":
                    qs = qs.filter(
                        Q(eligible=False, regimen_changes__isnull=False) |
                        Q(eligible=True, diagnosis__isnull=True, regimen_changes__isnull=False) |
                        Q(eligible=True, diagnosis__isnull=False, regimen_changes__isnull=False)
                    ).exclude(eligible=True, diagnosis__regimen_changed__name__iexact="yes", regimen_changes__isnull=False).distinct()
                    
            elif form_query == "tblis_raw":
                if hint_query == "Yes":
                    qs = qs.filter(zonal_laboratory__isnull=False, has_tblis_raw=True)
                elif hint_query == "No":
                    qs = qs.filter(zonal_laboratory__isnull=False, has_tblis_raw=False)
                elif hint_query == "N/F":
                    qs = qs.filter(zonal_laboratory__isnull=True)

        return qs.order_by("-screening_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add zones and sites for filter dropdowns
        role_context = get_role_context(self.request.user)
        context.update(role_context)
        
        # Explicit Profile Assignments for Header Display
        assigned_zones = []
        assigned_sites = []
        if hasattr(self.request.user, "profile"):
            assigned_zones = list(self.request.user.profile.zones.all())
            explicit_sites = set(self.request.user.profile.sites.all())
            
            from locations.models import Site
            derived_sites = set(Site.objects.filter(district__region__zone__in=assigned_zones))
            assigned_sites = sorted(list(explicit_sites.union(derived_sites)), key=lambda s: s.name)

        context.update({
            "assigned_zones": assigned_zones,
            "assigned_sites": assigned_sites,
        })
        
        # User permissions flags for UI rendering
        user_groups = [g.upper() for g in self.request.user.groups.values_list('name', flat=True)]
        is_data_specialist = hasattr(self.request.user, "profile") and self.request.user.profile.position and self.request.user.profile.position.name.lower() == "data specialist"
        
        context['is_admin_or_reviewer'] = self.request.user.is_superuser or "ADMIN" in user_groups or "REVIEWER" in user_groups or is_data_specialist
        context['is_admin_only'] = self.request.user.is_superuser or "ADMIN" in user_groups or is_data_specialist
        
        return context
