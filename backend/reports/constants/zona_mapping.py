# reports/constants.py
ZONAL_DQ_FIELD_MAPPING = {
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
