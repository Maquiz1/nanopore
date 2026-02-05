from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Q, Count, Case, When, IntegerField

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class ZonalDataQualityReportView(View):
    """
    Full Zonal Laboratory Data Quality Report — includes all field-level problem lists
    and enforces conditional rules for culture_isolate and phenotypic_performed.
    """
    template_name = "reports/data_quality/laboratory/zonal/data_zonal_quality_report.html"

    def get(self, request, *args, **kwargs):
        Zonal = apps.get_model("nanopore", "ZonalLaboratory")

        # Base queryset + role filtering
        qs = Zonal.objects.select_related(
            "screening",
            "screening__site",
            "screening__site__district__region__zone"
        ).order_by(
            "screening__site__district__region__zone__name",
            "screening__site__name",
            "screening__pid"
        )
        
        role_context = get_role_context(request.user)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_admin     = role_context.get("is_admin", False)
        is_reviewer  = role_context.get("is_reviewer", False)
        is_superuser = request.user.is_superuser
        is_full_access = is_admin or is_superuser
        is_privileged = is_admin or is_reviewer

        qs = filter_queryset_by_user_role(request.user, qs, site_field="screening__site")

        # Prepare zone and site mappings for template
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        # After getting zone_id and site_id from GET
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        # Convert to int if possible
        zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id_int = int(site_id) if site_id and site_id.isdigit() else None

        # Resolve names for template
        selected_zone_name = zones.get(zone_id_int, "") if zone_id_int else ""
        selected_site_name = sites.get(site_id_int, "") if site_id_int else ""

        # Apply filters
        if zone_id_int and zone_id_int in zones:
            qs = qs.filter(screening__site__district__region__zone_id=zone_id_int)

        if site_id_int and site_id_int in sites:
            qs = qs.filter(screening__site_id=site_id_int)


        total_records = qs.count()

        # =====================================================
        # DUPLICATE UNIQUE LAB NUMBER DETECTION
        # =====================================================

        duplicate_lab_numbers = (
            qs.exclude(unique_lab_no__isnull=True)
            .exclude(unique_lab_no__exact="")
            .values("unique_lab_no")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .values_list("unique_lab_no", flat=True)
        )
        
        # ── Aggregated counts with conditional rules ────────
        stats = qs.aggregate(
            missing_date_sputum_received=Count(Case(When(date_sputum_received__isnull=True, then=1), output_field=IntegerField())),
            missing_unique_lab_no=Count(
                Case(
                    When(
                        Q(unique_lab_no__isnull=True) |
                        Q(unique_lab_no__exact=""),
                        then=1
                    ),
                    output_field=IntegerField()
                )
            ),

            duplicate_unique_lab_no=Count(
                Case(
                    When(unique_lab_no__in=duplicate_lab_numbers, then=1),
                    output_field=IntegerField()
                )
            ),
            
            missing_sample_volume=Count(Case(When(sample_volume__isnull=True, then=1), output_field=IntegerField())),
            missing_appearance=Count(Case(When(appearance__isnull=True, then=1), output_field=IntegerField())),

            # Culture
            # CULTURE PERFORMED
            missing_culture_performed=Count(
                Case(When(culture_performed__isnull=True, then=1), output_field=IntegerField())
            ),
            # missing_culture_method
            missing_culture_method = Count(
                Case(
                    When(
                        culture_performed=1,
                        culture_method__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),

            missing_microscopy_type=Count(Case(When(culture_performed=1, microscopy_type__isnull=True, then=1), output_field=IntegerField())),
            missing_microscopy_date=Count(Case(When(culture_performed=1, microscopy_date__isnull=True, then=1), output_field=IntegerField())),
            missing_microscopy_results=Count(Case(When(culture_performed=1, microscopy_results__isnull=True, then=1), output_field=IntegerField())),

            # LJ culture
            missing_lj_inoculation_date = Count(
                Case(
                    When(
                        culture_performed=1,
                        culture_method=1,
                        lj_inoculation_date__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),

            missing_lj_results_date = Count(
                Case(
                    When(
                        culture_performed=1,
                        culture_method=1,
                        lj_results_date__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),

            missing_lj_results = Count(
                Case(
                    When(
                        culture_performed=1,
                        culture_method=1,
                        lj_results__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),

            # MGIT culture
            missing_mgit_inoculation_date = Count(
                Case(
                    When(
                        culture_performed=1,
                        culture_method=2,
                        mgit_inoculation_date__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),

            missing_mgit_results_date = Count(
                Case(
                    When(
                        culture_performed=1,
                        culture_method=2,
                        mgit_results_date__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),

            missing_mgit_results = Count(
                Case(
                    When(
                        culture_performed=1,
                        culture_method=2,
                        mgit_results__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),

            # Culture isolate — conditional: only count if lj_results not in [1,2,3,4] AND mgit_results != 1
            # missing_culture_isolate = Count(
            #     Case(
            #         When(
            #             Q(culture_isolate__isnull=True) &
            #             (Q(lj_results__in=[1, 2, 3, 4]) | Q(mgit_results=1)),
            #             then=1
            #         ),
            #         output_field=IntegerField()
            #     )
            # ),
            
            missing_culture_isolate = Count(
                Case(
                    When(culture_isolate__isnull=True, lj_results__in=[1,2,3,4], then=1),
                    When(culture_isolate__isnull=True, mgit_results=1, then=1),
                    output_field=IntegerField()
                )
            ),

            
            # ── ISOLATE DATE ──
            missing_isolate_date = Count(
                Case(
                    When(
                        Q(isolate_date__isnull=True) & Q(culture_isolate=1),
                        then=1
                    ),
                    output_field=IntegerField()
                )
            ),

            # Phenotypic DST — conditional: only if culture_isolate = 1
            missing_phenotypic_performed = Count(
                Case(
                    When(
                        Q(culture_isolate__isnull=False) & Q(culture_isolate=1) & Q(phenotypic_performed__isnull=True),
                        then=1
                    ),
                    output_field=IntegerField()
                )
            ),

            # Phenotypic Date Performed — only if phenotypic_performed = 1
            missing_phenotypic_date_performed = Count(
                Case(
                    When(
                        Q(phenotypic_date_performed__isnull=True) & Q(phenotypic_performed=1),
                        then=1
                    ),
                    output_field=IntegerField()
                )
            ),

            # Phenotypic Date Results — only if phenotypic_performed = 1
            missing_phenotypic_date_results = Count(
                Case(
                    When(
                        Q(phenotypic_date_results__isnull=True) & Q(phenotypic_performed=1),
                        then=1
                    ),
                    output_field=IntegerField()
                )
            ),
            missing_phenotypic_dst_results=Count(Case(
                When(
                    phenotypic_performed=1,
                    then=Case(
                        When(
                            Q(rifampicin__isnull=True) |
                            Q(isoniazid__isnull=True) |
                            Q(levofloxacin__isnull=True) |
                            Q(moxifloxacin__isnull=True) |
                            Q(bedaquiline__isnull=True) |
                            Q(linezolid__isnull=True) |
                            Q(clofazimine__isnull=True) |
                            Q(cycloserine__isnull=True) |
                            Q(terizidone__isnull=True) |
                            Q(ethambutol__isnull=True) |
                            Q(delamanid__isnull=True) |
                            Q(pyrazinamide__isnull=True) |
                            Q(imipenem__isnull=True) |
                            Q(cilastatin__isnull=True) |
                            Q(meropenem__isnull=True) |
                            Q(amikacin__isnull=True) |
                            Q(streptomycin__isnull=True) |
                            Q(ethionamide__isnull=True) |
                            Q(prothionamide__isnull=True) |
                            Q(para_aminosalicylic_acid__isnull=True),
                            then=1
                        ),
                        default=None,
                        output_field=IntegerField()
                    )
                )
            )),

            # Xpert XDR
            missing_xpert_xdr_performed=Count(
                Case(When(xpert_xdr_performed__isnull=True, then=1), output_field=IntegerField())
            ),
            missing_xpert_xdr_date_performed=Count(Case(When(xpert_xdr_performed=1, xpert_xdr_date_performed__isnull=True, then=1), output_field=IntegerField())),
            missing_xpert_xdr_results=Count(Case(
                When(xpert_xdr_performed=1, then=Case(
                    When(
                        Q(xpert_xdr_isoniazid__isnull=True) |
                        Q(xpert_xdr_fluoroquinolones__isnull=True) |
                        Q(xpert_xdr_amikacin__isnull=True) |
                        Q(xpert_xdr_kanamycin__isnull=True) |
                        Q(xpert_xdr_capreomycin__isnull=True) |
                        Q(xpert_xdr_ethionamide__isnull=True),
                        then=1
                    ),
                    default=None,
                    output_field=IntegerField()
                ))
            )),
            # LPA
            missing_lpa=Count(
                Case(When(lpa__isnull=True, then=1), output_field=IntegerField())
            ),
            missing_lpa1=Count(
                Case(When(lpa=1, first_line_lpa__isnull=True, then=1), output_field=IntegerField())
            ),
            missing_lpa2=Count(
                Case(When(lpa=1, second_line_lpa__isnull=True, then=1), output_field=IntegerField())
            ),
            # FIRST LINE LPA
            missing_first_line_lpa=Count(
                Case(When(first_line_lpa__isnull=True, then=1), output_field=IntegerField())
            ),
            missing_first_line_lpa_date=Count(Case(When(first_line_lpa=1, first_line_lpa_date__isnull=True, then=1), output_field=IntegerField())),
            # First line LPA drugs (M2M)
            missing_first_line_drugs = Count(
                Case(
                    When(
                        first_line_lpa=1,
                        first_line_drugs__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),
            missing_lpa1_mtb=Count(Case(When(first_line_lpa=1, lpa1_mtb__isnull=True, then=1), output_field=IntegerField())),
            missing_lpa1_rif=Count(Case(When(first_line_lpa=1, lpa1_rif__isnull=True, then=1), output_field=IntegerField())),
            # LPA1 INH
            missing_lpa1_inh = Count(
                Case(
                    When(
                        first_line_lpa=1,
                        lpa1_inh__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),
            
            # Second line LPA
            missing_second_line_lpa=Count(
                Case(When(second_line_lpa__isnull=True, then=1), output_field=IntegerField())
            ),
            missing_second_line_lpa_date=Count(Case(When(second_line_lpa=1, second_line_lpa_date__isnull=True, then=1), output_field=IntegerField())),
            # Second line LPA drugs (M2M)
            missing_second_line_drugs = Count(
                Case(
                    When(
                        second_line_lpa=1,
                        second_line_drugs__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),
            missing_lpa2_mtb=Count(Case(When(second_line_lpa=1, lpa2_mtb__isnull=True, then=1), output_field=IntegerField())),
            missing_lpa2_rfluoroquinolones=Count(Case(When(second_line_lpa=1, lpa2_rfluoroquinolones__isnull=True, then=1), output_field=IntegerField())),
            missing_lpa2_aminoglycosides=Count(Case(When(second_line_lpa=1, lpa2_aminoglycosides__isnull=True, then=1), output_field=IntegerField())),
            missing_lpa2_kanamycin=Count(Case(When(second_line_lpa=1, lpa2_kanamycin__isnull=True, then=1), output_field=IntegerField())),

            # Nanopore
            missing_nanopore_done=Count(
                Case(When(nanopore_done__isnull=True, then=1), output_field=IntegerField())
            ),
            missing_nanopore_sequencing_date=Count(Case(When(nanopore_done=1, nanopore_sequencing_date__isnull=True, then=1), output_field=IntegerField())),
            missing_nanopore_results=Count(Case(When(nanopore_done=1, nanopore_results__isnull=True, then=1), output_field=IntegerField())),
            missing_epi_to_me=Count(Case(When(nanopore_done=1, epi_to_me__isnull=True, then=1), output_field=IntegerField())),
            missing_sequencing_delayed = Count(
                Case(
                    When(
                        nanopore_done=1,
                        nanopore_results=1,
                        sequencing_delayed__isnull=True,
                        then=1
                    ),
                    output_field=IntegerField(),
                )
            ),

            missing_sequencing_delayed_days = Count(
                Case(
                    When(
                        nanopore_done=1,
                        nanopore_results=1,
                        sequencing_delayed=1,
                        sequencing_delayed_days__isnull=True,
                        then=1
                    ),
                    output_field=IntegerField(),
                )
            ),

            missing_sequencing_delayed_reasons = Count(
                Case(
                    When(
                        nanopore_done=1,
                        nanopore_results=1,
                        sequencing_delayed=1,
                        sequencing_delayed_reasons__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),

            missing_sequencing_delayed_others = Count(
                Case(
                    When(
                        nanopore_done=1,
                        nanopore_results=1,
                        sequencing_delayed=1,
                        sequencing_delayed_reasons__value=96,
                        sequencing_delayed_others__isnull=True,
                        then="pk"
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True
            ),

            missing_epi_to_me_date = Count(
                Case(
                    When(
                        epi_to_me=1,
                        epi_to_me_date__isnull=True,
                        then=1
                    ),
                    output_field=IntegerField(),
                )
            ),

            missing_epi_to_me_version = Count(
                Case(
                    When(
                        epi_to_me=1,
                        epi_to_me_version__isnull=True,
                        then=1
                    ),
                    output_field=IntegerField(),
                )
            ),

            missing_nanopore_drug_results = Count(
                Case(
                    When(
                        nanopore_results=1,
                        then=Case(
                            When(
                                Q(nano_amikacin__isnull=True) |
                                Q(nano_bedaquiline__isnull=True) |
                                Q(nano_capreomycin__isnull=True) |
                                Q(nano_clofazimine__isnull=True) |
                                Q(nano_delamanid__isnull=True) |
                                Q(nano_ethambutol__isnull=True) |
                                Q(nano_ethionamide__isnull=True) |
                                Q(nano_isoniazid__isnull=True) |
                                Q(nano_kanamycin__isnull=True) |
                                Q(nano_levofloxacin__isnull=True) |
                                Q(nano_linezolid__isnull=True) |
                                Q(nano_moxifloxacin__isnull=True) |
                                Q(nano_pretomanid__isnull=True) |
                                Q(nano_pyrazinamide__isnull=True) |
                                Q(nano_rifampicin__isnull=True) |
                                Q(nano_streptomycin__isnull=True),
                                then=1
                            ),
                            default=None,
                            output_field=IntegerField(),
                        )
                    ),
                    output_field=IntegerField(),
                )
            ),

        )

        total_issues = sum(stats.values())
        
        # ── Serialization helper ─────────────────────────────
        def serialize_record(z, fields):
            screening = getattr(z, "screening", None)
            site = getattr(screening, "site", None) if screening else None
            zone_obj = getattr(getattr(getattr(site, "district", None), "region", None), "zone", None)
            record = {
                "id": z.id,
                "pid": getattr(screening, "pid", "") if screening else "",
                "screening_date": getattr(screening, "screening_date", None) if screening else None,
                "zone_name": zone_obj.name if zone_obj else "",
                "site_name": getattr(site, "name", "") if site else "",
            }
            for f in fields:
                record[f] = getattr(z, f, None)
            return record

        # ── All fields mapping for problem lists ─────────────
        all_fields_mapping = {
            # Basic fields
            "missing_date_sputum_received": ["date_sputum_received"],
            "missing_unique_lab_no": ["unique_lab_no"],
            "duplicate_unique_lab_no": ["unique_lab_no"],
            "missing_sample_volume": ["sample_volume"],
            "missing_appearance": ["appearance"],

            # Culture
            "missing_culture_performed": ["culture_performed"],
            "missing_culture_method": ["culture_method"],
            "missing_microscopy_type": ["microscopy_type"],
            "missing_microscopy_date": ["microscopy_date"],
            "missing_microscopy_results": ["microscopy_results"],

            # LJ culture
            "missing_lj_inoculation_date": ["lj_inoculation_date"],
            "missing_lj_results_date": ["lj_results_date"],
            "missing_lj_results": ["lj_results"],

            # MGIT culture
            "missing_mgit_inoculation_date": ["mgit_inoculation_date"],
            "missing_mgit_results_date": ["mgit_results_date"],
            "missing_mgit_results": ["mgit_results"],

            # Culture isolate
            "missing_culture_isolate":["culture_isolate"],
            "missing_isolate_date": ["isolate_date"],

            # Phenotypic DST
            "missing_phenotypic_performed": ["phenotypic_performed"],
            "missing_phenotypic_date_performed": ["phenotypic_date_performed"],
            "missing_phenotypic_date_results": ["phenotypic_date_results"],
            "missing_phenotypic_dst_results": [
                "rifampicin","isoniazid","levofloxacin","moxifloxacin","bedaquiline",
                "linezolid","clofazimine","cycloserine","terizidone","ethambutol",
                "delamanid","pyrazinamide","imipenem","cilastatin","meropenem",
                "amikacin","streptomycin","ethionamide","prothionamide","para_aminosalicylic_acid"
            ],

            # Xpert XDR
            "missing_xpert_xdr_performed": ["xpert_xdr_performed"],
            "missing_xpert_xdr_date_performed": ["xpert_xdr_date_performed"],
            "missing_xpert_xdr_results": [
                "xpert_xdr_isoniazid",
                "xpert_xdr_fluoroquinolones",
                "xpert_xdr_amikacin",
                "xpert_xdr_kanamycin",
                "xpert_xdr_capreomycin",
                "xpert_xdr_ethionamide"
            ],
            # LPA
            "missing_lpa": ["lpa"],
            "missing_lpa1": ["first_line_lpa"],
            "missing_lpa2": ["second_line_lpa"],
            # First line LPA
            "missing_first_line_lpa": ["first_line_lpa"],
            "missing_first_line_lpa_date": ["first_line_lpa_date"],
            "missing_first_line_drugs": ["first_line_drugs"],
            "missing_lpa1_mtb": ["lpa1_mtb"],
            "missing_lpa1_rif": ["lpa1_rif"],
            "missing_lpa1_inh": ["lpa1_inh"],

            # Second line LPA
            "missing_second_line_lpa": ["second_line_lpa"],
            "missing_second_line_lpa_date": ["second_line_lpa_date"],
            "missing_second_line_drugs": ["second_line_drugs"],
            "missing_lpa2_mtb": ["lpa2_mtb"],
            "missing_lpa2_rfluoroquinolones": ["lpa2_rfluoroquinolones"],
            "missing_lpa2_aminoglycosides": ["lpa2_aminoglycosides"],
            "missing_lpa2_kanamycin": ["lpa2_kanamycin"],

            # Nanopore
            "missing_nanopore_done": ["nanopore_done"],
            "missing_nanopore_sequencing_date": ["nanopore_sequencing_date"],
            "missing_nanopore_results": ["nanopore_results"],
            "missing_epi_to_me": ["epi_to_me"],
            "missing_sequencing_delayed": ["sequencing_delayed"],
            "missing_sequencing_delayed_days": ["sequencing_delayed_days"],
            "missing_sequencing_delayed_reasons": ["sequencing_delayed_reasons"],
            "missing_sequencing_delayed_others": ["sequencing_delayed_others"],
            "missing_epi_to_me_date": ["epi_to_me_date"],
            "missing_epi_to_me_version": ["epi_to_me_version"],
            "missing_nanopore_drug_results": [
                "nano_amikacin","nano_bedaquiline","nano_capreomycin","nano_clofazimine",
                "nano_delamanid","nano_ethambutol","nano_ethionamide","nano_isoniazid",
                "nano_kanamycin","nano_levofloxacin","nano_linezolid","nano_moxifloxacin",
                "nano_pretomanid","nano_pyrazinamide","nano_rifampicin","nano_streptomycin"
            ],
        }

        # ── Generate problem lists ─────────────
        problem_lists = {}

        # for key, fields in all_fields_mapping.items():

        #     # ----------------------------
        #     # DUPLICATE LAB NUMBER LIST
        #     # ----------------------------
        #     if key == "duplicate_unique_lab_no":
        #         problem_lists[key] = [
        #             serialize_record(z, fields)
        #             for z in qs.filter(unique_lab_no__in=duplicate_lab_numbers)[:100]
        #         ]
        #         continue

        #     # ----------------------------
        #     # NORMAL MISSING FIELD LOGIC
        #     # ----------------------------
        #     q = Q()
        #     for f in fields:
        #         q |= Q(**{f + "__isnull": True})

        #     problem_lists[key] = [
        #         serialize_record(z, fields)
        #         for z in qs.filter(q)[:100]
        #     ]
        
        for key, fields in all_fields_mapping.items():

            if key == "duplicate_unique_lab_no":
                problem_lists[key] = [
                    serialize_record(z, fields)
                    for z in qs.filter(unique_lab_no__in=duplicate_lab_numbers)[:100]
                ]
                continue

            q = Q()

            for f in fields:
                q |= Q(**{f + "__isnull": True})

            # Conditional guards
            if key.startswith("missing_culture_method_"):
                q &= Q(culture_performed=1)
                
            if key.startswith("missing_lj_"):
                q &= Q(culture_performed=1, culture_method=1)

            if key.startswith("missing_mgit_"):
                q &= Q(culture_performed=1, culture_method=2)
                
            if key.startswith("missing_isolate_date_"):
                q &= Q(culture_isolate=1)

            if key.startswith("missing_first_line_"):
                q &= Q(first_line_lpa=1)

            if key.startswith("missing_second_line_"):
                q &= Q(second_line_lpa=1)

            if key.startswith("missing_nanopore_"):
                q &= Q(nanopore_done=1)

            problem_lists[key] = [
                serialize_record(z, fields)
                for z in qs.filter(q)[:100]
            ]

        context = {
            "total_records": total_records,
            "report_date": timezone.now(),
            "report_title": "Zonal Laboratory Data Quality Report",
            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "is_national_lab": role_context.get("is_national_lab", False),
            "zones": zones,
            "sites": sites,
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",
            "selected_zone_name": selected_zone_name,
            "selected_site_name": selected_site_name,
            **{f"count_{k}": v for k, v in stats.items()},
            "total_issues": total_issues,
            **problem_lists,  # <-- include serialized lists here
        }

        return render(request, self.template_name, context)





