from django.db import models
from .general_base_snapshot_model import DataQualitySnapshot


class ZonalLaboratoryDQSnapshot(models.Model):
    snapshot = models.ForeignKey(
        DataQualitySnapshot,
        on_delete=models.CASCADE,
        related_name="zonal_lab_details"
    )

    zone = models.ForeignKey(
        "locations.Zone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    site = models.ForeignKey(
        "locations.Site",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    total_records = models.IntegerField(default=0)
    total_issues = models.IntegerField(default=0)

    # ── Basic fields
    missing_date_sputum_received = models.IntegerField(default=0)
    missing_unique_lab_no = models.IntegerField(default=0)
    duplicate_unique_lab_no = models.IntegerField(default=0)
    missing_sample_volume = models.IntegerField(default=0)
    missing_appearance = models.IntegerField(default=0)

    # ── Culture
    missing_culture_performed = models.IntegerField(default=0)
    missing_culture_method = models.IntegerField(default=0)
    missing_microscopy_type = models.IntegerField(default=0)
    missing_microscopy_date = models.IntegerField(default=0)
    missing_microscopy_results = models.IntegerField(default=0)

    missing_lj_inoculation_date = models.IntegerField(default=0)
    missing_lj_results_date = models.IntegerField(default=0)
    missing_lj_results = models.IntegerField(default=0)

    missing_mgit_inoculation_date = models.IntegerField(default=0)
    missing_mgit_results_date = models.IntegerField(default=0)
    missing_mgit_results = models.IntegerField(default=0)

    missing_culture_isolate = models.IntegerField(default=0)
    missing_isolate_date = models.IntegerField(default=0)
    missing_isolate_unique_lab_no = models.IntegerField(default=0)

    # ── Phenotypic DST
    missing_phenotypic_performed = models.IntegerField(default=0)
    missing_phenotypic_date_performed = models.IntegerField(default=0)
    missing_phenotypic_date_results = models.IntegerField(default=0)
    missing_phenotypic_dst_results = models.IntegerField(default=0)

    # ── Xpert XDR
    missing_xpert_xdr_performed = models.IntegerField(default=0)
    missing_xpert_xdr_date_performed = models.IntegerField(default=0)
    missing_xpert_xdr_results = models.IntegerField(default=0)

    # ── LPA
    missing_lpa = models.IntegerField(default=0)
    # ── First and Second line LPA
    missing_first_line_lpa_date = models.IntegerField(default=0)
    missing_first_line_drugs = models.IntegerField(default=0)
    missing_lpa1_mtb = models.IntegerField(default=0)
    missing_lpa1_rif = models.IntegerField(default=0)
    missing_lpa1_inh = models.IntegerField(default=0)

    missing_second_line_lpa_date = models.IntegerField(default=0)
    missing_second_line_drugs = models.IntegerField(default=0)
    missing_lpa2_mtb = models.IntegerField(default=0)
    missing_lpa2_rfluoroquinolones = models.IntegerField(default=0)
    missing_lpa2_aminoglycosides = models.IntegerField(default=0)
    missing_lpa2_kanamycin = models.IntegerField(default=0)

    # ── Nanopore
    missing_nanopore_done = models.IntegerField(default=0)            
    missing_nanopore_sequencing_date = models.IntegerField(default=0)
    missing_nanopore_results = models.IntegerField(default=0)
    
    # ── EPI to ME
    missing_epi_to_me = models.IntegerField(default=0)
    missing_epi_to_me_date = models.IntegerField(default=0)
    missing_epi_to_me_version = models.IntegerField(default=0)
    missing_sequencing_results = models.IntegerField(default=0)
    
    # ── Delays
    missing_sequencing_delayed = models.IntegerField(default=0)
    missing_sequencing_delayed_days = models.IntegerField(default=0)
    missing_sequencing_delayed_reasons = models.IntegerField(default=0)
    missing_sequencing_delayed_others = models.IntegerField(default=0)
    
    # ── Nanopore drug results
    missing_nanopore_drug_results = models.IntegerField(default=0)

    class Meta:
        unique_together = ("snapshot", "zone", "site")
        indexes = [
            models.Index(fields=["snapshot", "zone"]),
            models.Index(fields=["snapshot", "site"]),
        ]
