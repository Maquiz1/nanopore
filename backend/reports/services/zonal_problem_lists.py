# reports/services/zonal_problem_lists.py
from django.db.models import Q
from reports.constants.zona_mapping import ZONAL_DQ_FIELD_MAPPING

def serialize_record(z, fields):
    """
    Serialize a single record with dynamic fields for problem lists.
    """
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


def get_zonal_problem_lists(qs, duplicate_lab_numbers, all_fields_mapping=ZONAL_DQ_FIELD_MAPPING):
    """
    Build problem lists for each field, using the same conditional logic as the aggregates.
    Fully mirrors zonal_dq_counts.py logic.
    """
    problem_lists = {}

    for key, fields in all_fields_mapping.items():
        # Handle duplicate lab numbers separately
        if key == "duplicate_unique_lab_no":
            problem_lists[key] = [
                serialize_record(z, fields)
                for z in qs.filter(unique_lab_no__in=duplicate_lab_numbers)[:100]
            ]
            continue

        q = Q()
        model = qs.model

        for f in fields:
            if f == "unique_lab_no":
                continue

            field_obj = model._meta.get_field(f)
            field_type = field_obj.get_internal_type()

            # Only strings can be empty ""
            if field_type in ("CharField", "TextField"):
                q |= Q(**{f + "__isnull": True}) | Q(**{f + "__exact": ""})

            # ALL other field types
            else:
                q |= Q(**{f + "__isnull": True})

        # Apply conditional guards to match aggregate filters
        # CULTURE
        if key in ["missing_culture_method", "missing_microscopy_type", "missing_microscopy_date", "missing_microscopy_results"]:
            q &= Q(culture_performed=1)

        # LJ
        if key in ["missing_lj_inoculation_date", "missing_lj_results_date", "missing_lj_results"]:
            q &= Q(culture_method=1)

        # MGIT
        if key in ["missing_mgit_inoculation_date", "missing_mgit_results_date", "missing_mgit_results"]:
            q &= Q(culture_method=2)

        # ISOLATE
        if key == "missing_culture_isolate":
            q &= (Q(lj_results__in=[1,2,3,4]) | Q(mgit_results=1)) & Q(culture_isolate__isnull=True)
            
        if key == "missing_isolate_date":
            q &= Q(culture_isolate=1)
            

        # PHENOTYPIC DST            
        if key == "missing_phenotypic_performed":
            q &= Q(culture_isolate=1, phenotypic_performed__isnull=True)

        if key in ["missing_phenotypic_date_performed", "missing_phenotypic_date_results"]:
            q &= Q(phenotypic_performed=1)

        if key == "missing_phenotypic_dst_results":
            q &= Q(phenotypic_performed=1) & (
                Q(rifampicin__isnull=True) | Q(isoniazid__isnull=True) |
                Q(levofloxacin__isnull=True) | Q(moxifloxacin__isnull=True) |
                Q(bedaquiline__isnull=True) | Q(linezolid__isnull=True) |
                Q(clofazimine__isnull=True) | Q(cycloserine__isnull=True) |
                Q(terizidone__isnull=True) | Q(ethambutol__isnull=True) |
                Q(delamanid__isnull=True) | Q(pyrazinamide__isnull=True) |
                Q(imipenem__isnull=True) | Q(cilastatin__isnull=True) |
                Q(meropenem__isnull=True) | Q(amikacin__isnull=True) |
                Q(streptomycin__isnull=True) | Q(ethionamide__isnull=True) |
                Q(prothionamide__isnull=True) | Q(para_aminosalicylic_acid__isnull=True)
            )

        # XPERT XDR
        if key in ["missing_xpert_xdr_date_performed", "missing_xpert_xdr_results"]:
            q &= Q(xpert_xdr_performed=1)

        # LPA
        # FIRST LINE LPA
        if key.startswith("missing_first_line_lpa"):
            q &= Q(lpa=1)
            
        # Handle LPA first-line missing drugs individually
        if key in [
            "missing_first_line_lpa_date","missing_first_line_drugs",
            "missing_lpa1_mtb", "missing_lpa1_rif", "missing_lpa1_inh"
        ]:
            q &= Q(first_line_lpa=1)

        # SECOND LINE LPA
        if key.startswith("missing_second_line_lpa"):
            q &= Q(second_line_lpa=1)
            
        # Handle LPA second-line missing drugs individually
        if key in [
            "missing_second_line_lpa_date","missing_second_line_drugs",
            "missing_lpa2_mtb", "missing_lpa2_rfluoroquinolones",
            "missing_lpa2_aminoglycosides","missing_lpa2_kanamycin"
        ]:
            q &= Q(second_line_lpa=1)

        # NANOPORE
        if key in [
            "missing_nanopore_sequencing_date","missing_epi_to_me","missing_nanopore_results",
            "missing_sequencing_delayed"
        ]:
            q &= Q(nanopore_done=1)
            
        # EPI to ME
        if key in ["missing_epi_to_me_date", "missing_epi_to_me_version","missing_sequencing_results"]:
            q &= Q(epi_to_me=1)

        # Delayed Sequenceng
        if key in [
            "missing_sequencing_delayed","missing_sequencing_delayed_days","missing_sequencing_delayed_reasons"
        ]:
            q &= Q(sequencing_delayed=1)    

        # Complex Nanopore drug results
        if key == "missing_nanopore_drug_results":
            q &= (
                Q(nanopore_results=1) & (
                    Q(nano_amikacin__isnull=True) | Q(nano_bedaquiline__isnull=True) | 
                    Q(nano_capreomycin__isnull=True) | Q(nano_clofazimine__isnull=True) |
                    Q(nano_delamanid__isnull=True) | Q(nano_ethambutol__isnull=True) |
                    Q(nano_ethionamide__isnull=True) | Q(nano_isoniazid__isnull=True) |
                    Q(nano_kanamycin__isnull=True) | Q(nano_levofloxacin__isnull=True) |
                    Q(nano_linezolid__isnull=True) | Q(nano_moxifloxacin__isnull=True) |
                    Q(nano_pretomanid__isnull=True) | Q(nano_pyrazinamide__isnull=True) |
                    Q(nano_rifampicin__isnull=True) | Q(nano_streptomycin__isnull=True)
                )
            )

        # Fetch top 100 records matching the filters
        problem_lists[key] = [
            serialize_record(z, fields)
            for z in qs.filter(q)[:600]
        ]

    return problem_lists
