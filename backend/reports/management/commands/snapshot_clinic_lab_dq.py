# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django.apps import apps
# from django.db.models import Count, Q

# from reports.models import DataQualitySnapshot, ClinicDQSnapshot


# class Command(BaseCommand):
#     help = "Create daily Clinic Laboratory Data Quality snapshot"

#     def handle(self, *args, **options):
#         Clinic = apps.get_model("nanopore", "ClinicLaboratory")

#         snapshot, _ = DataQualitySnapshot.objects.get_or_create(
#             snapshot_date=timezone.localdate()
#         )

#         qs = Clinic.objects.select_related(
#             "screening",
#             "screening__site",
#             "screening__site__district__region__zone",
#         )

#         # Q helpers (IDENTICAL to your view)
#         sample_received_is_2_q = Q(sample_received__value=2) | Q(sample_received__name__iexact="2")
#         sample_received_is_1_q = Q(sample_received__value=1) | Q(sample_received__name__iexact="1")
#         new_sample_is_1_q = Q(new_sample__value=1) | Q(new_sample__name__iexact="1")
#         new_sample_is_2_q = Q(new_sample__value=2) | Q(new_sample__name__iexact="2")
#         sample_reason_is_96_q = Q(sample_reason__value=96) | Q(sample_reason__name__iexact="96")

#         nr_is_2_q = Q(number_received__value=2) | Q(number_received__name__iexact="2")

#         afb_xpert_required_q = sample_received_is_1_q | (sample_received_is_2_q & new_sample_is_1_q)
#         afb_yes_q = Q(afb_microscopy_conducted__name__iexact="yes")
#         xpert_yes_q = Q(xpert_mtb_rif_conducted__name__iexact="yes")

#         xpert_in_2_6_q = Q(xpert_mtb__value__in=[2, 3, 4, 5, 6]) | Q(xpert_mtb__name__in=["2", "3", "4", "5", "6"])
#         xpert_is_8_q = Q(xpert_mtb__value=8) | Q(xpert_mtb__name__iexact="8")

#         grouped = qs.values(
#             "screening__site__district__region__zone_id",
#             "screening__site_id",
#         ).annotate(
#             total_clinics=Count("id"),

#             missing_sample_received=Count("id", filter=Q(sample_received__isnull=True)),
#             missing_number_received=Count("id", filter=(sample_received_is_1_q | sample_received_is_2_q | new_sample_is_1_q) & Q(number_received__isnull=True)),
#             missing_sample_reason_when_received_2=Count("id", filter=sample_received_is_2_q & Q(sample_reason__isnull=True)),
#             missing_new_reason_when_new_sample_2=Count("id", filter=new_sample_is_2_q & Q(new_reason__isnull=True)),
#             missing_other_reason_when_sample_reason_96=Count("id", filter=sample_reason_is_96_q & Q(other_reason__isnull=True)),

#             missing_date_sample1_collected=Count("id", filter=Q(number_received__isnull=False, date_sample1_collected__isnull=True)),
#             missing_date_sample1_received=Count("id", filter=Q(number_received__isnull=False, date_sample1_received__isnull=True)),
#             missing_appearance_sample1=Count("id", filter=Q(number_received__isnull=False, appearance_sample1__isnull=True)),
#             missing_sample1_volume=Count("id", filter=Q(number_received__isnull=False, sample1_volume__isnull=True)),

#             missing_date_sample2_collected=Count("id", filter=nr_is_2_q & Q(date_sample2_collected__isnull=True)),
#             missing_date_sample2_received=Count("id", filter=nr_is_2_q & Q(date_sample2_received__isnull=True)),
#             missing_appearance_sample2=Count("id", filter=nr_is_2_q & Q(appearance_sample2__isnull=True)),
#             missing_sample2_volume=Count("id", filter=nr_is_2_q & Q(sample2_volume__isnull=True)),

#             missing_afb_microscopy_conducted=Count("id", filter=afb_xpert_required_q & Q(afb_microscopy_conducted__isnull=True)),
#             missing_afb_a_date=Count("id", filter=afb_yes_q & Q(afb_a_date__isnull=True)),
#             missing_technique_a=Count("id", filter=afb_yes_q & Q(technique_a__isnull=True)),
#             missing_afb_a_results=Count("id", filter=afb_yes_q & Q(afb_a_results__isnull=True)),

#             missing_xpert_mtb_rif_conducted=Count("id", filter=afb_xpert_required_q & Q(xpert_mtb_rif_conducted__isnull=True)),
#             missing_xpert_date=Count("id", filter=xpert_yes_q & Q(xpert_date__isnull=True)),
#             missing_xpert_mtb=Count("id", filter=xpert_yes_q & Q(xpert_mtb__isnull=True)),
#             missing_error_code=Count("id", filter=xpert_is_8_q & Q(error_code__isnull=True)),
#             missing_xpert_rif=Count("id", filter=xpert_in_2_6_q & Q(xpert_rif__isnull=True)),
#             missing_ct_value=Count(
#                 "id",
#                 filter=xpert_in_2_6_q
#                 & ~(
#                     Q(ct_value__isnull=False, ct_na=False)
#                     | Q(ct_value__isnull=True, ct_na=True)
#                     | Q(ct_value__in=[99, 99.0])
#                 )
#             ),
#         )

#         rows = []
#         for g in grouped:
#             total_issues = sum(v for k, v in g.items() if k.startswith("missing_"))

#             rows.append(
#                 ClinicDQSnapshot(
#                     snapshot=snapshot,
#                     zone_id=g["screening__site__district__region__zone_id"],
#                     site_id=g["screening__site_id"],
#                     total_clinics=g["total_clinics"],
#                     total_issues=total_issues,
#                     **{k: g[k] for k in g if k.startswith("missing_")}
#                 )
#             )

#         ClinicDQSnapshot.objects.bulk_create(rows, ignore_conflicts=True)

#         self.stdout.write(self.style.SUCCESS("Clinic DQ snapshot created"))

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.db.models import Count, Q

from reports.models import DataQualitySnapshot, ClinicDQSnapshot


class Command(BaseCommand):
    help = "Create or update daily Clinic Laboratory Data Quality snapshot"

    def handle(self, *args, **options):
        Clinic = apps.get_model("nanopore", "ClinicLaboratory")

        today = timezone.localdate()
        snapshot, _ = DataQualitySnapshot.objects.get_or_create(
            snapshot_date=today
        )

        qs = Clinic.objects.select_related(
            "screening",
            "screening__site",
            "screening__site__district__region__zone",
        )

        # ─────────────────────────────────────────────
        # Q helpers (IDENTICAL to view logic)
        # ─────────────────────────────────────────────
        sample_received_is_2_q = Q(sample_received__value=2) | Q(sample_received__name__iexact="2")
        sample_received_is_1_q = Q(sample_received__value=1) | Q(sample_received__name__iexact="1")
        new_sample_is_1_q = Q(new_sample__value=1) | Q(new_sample__name__iexact="1")
        new_sample_is_2_q = Q(new_sample__value=2) | Q(new_sample__name__iexact="2")
        sample_reason_is_96_q = Q(sample_reason__value=96) | Q(sample_reason__name__iexact="96")

        nr_is_2_q = Q(number_received__value=2) | Q(number_received__name__iexact="2")

        afb_xpert_required_q = sample_received_is_1_q | (
            sample_received_is_2_q & new_sample_is_1_q
        )

        afb_yes_q = Q(afb_microscopy_conducted__name__iexact="yes")
        xpert_yes_q = Q(xpert_mtb_rif_conducted__name__iexact="yes")

        xpert_in_2_6_q = (
            Q(xpert_mtb__value__in=[2, 3, 4, 5, 6]) |
            Q(xpert_mtb__name__in=["2", "3", "4", "5", "6"])
        )

        xpert_is_8_q = Q(xpert_mtb__value=8) | Q(xpert_mtb__name__iexact="8")

        grouped = qs.values(
            "screening__site__district__region__zone_id",
            "screening__site_id",
        ).annotate(

            # =========================
            # TOTAL
            # =========================
            total_clinics=Count("id"),

            # =========================
            # SAMPLE RECEIPT
            # =========================
            missing_sample_received=Count("id", filter=Q(sample_received__isnull=True)),
            missing_number_received=Count(
                "id",
                filter=(sample_received_is_1_q | sample_received_is_2_q | new_sample_is_1_q)
                       & Q(number_received__isnull=True)
            ),
            missing_sample_reason_when_received_2=Count(
                "id",
                filter=sample_received_is_2_q & Q(sample_reason__isnull=True)
            ),
            missing_new_reason_when_new_sample_2=Count(
                "id",
                filter=new_sample_is_2_q & Q(new_reason__isnull=True)
            ),
            missing_other_reason_when_sample_reason_96=Count(
                "id",
                filter=sample_reason_is_96_q & Q(other_reason__isnull=True)
            ),

            # =========================
            # SAMPLE 1
            # =========================
            missing_date_sample1_collected=Count(
                "id",
                filter=Q(number_received__isnull=False, date_sample1_collected__isnull=True)
            ),
            missing_date_sample1_received=Count(
                "id",
                filter=Q(number_received__isnull=False, date_sample1_received__isnull=True)
            ),
            missing_appearance_sample1=Count(
                "id",
                filter=Q(number_received__isnull=False, appearance_sample1__isnull=True)
            ),
            missing_sample1_volume=Count(
                "id",
                filter=Q(number_received__isnull=False, sample1_volume__isnull=True)
            ),

            # =========================
            # SAMPLE 2
            # =========================
            missing_date_sample2_collected=Count(
                "id",
                filter=nr_is_2_q & Q(date_sample2_collected__isnull=True)
            ),
            missing_date_sample2_received=Count(
                "id",
                filter=nr_is_2_q & Q(date_sample2_received__isnull=True)
            ),
            missing_appearance_sample2=Count(
                "id",
                filter=nr_is_2_q & Q(appearance_sample2__isnull=True)
            ),
            missing_sample2_volume=Count(
                "id",
                filter=nr_is_2_q & Q(sample2_volume__isnull=True)
            ),

            # =========================
            # AFB
            # =========================
            missing_afb_microscopy_conducted=Count(
                "id",
                filter=afb_xpert_required_q & Q(afb_microscopy_conducted__isnull=True)
            ),
            missing_afb_a_date=Count(
                "id",
                filter=afb_yes_q & Q(afb_a_date__isnull=True)
            ),
            missing_technique_a=Count(
                "id",
                filter=afb_yes_q & Q(technique_a__isnull=True)
            ),
            missing_afb_a_results=Count(
                "id",
                filter=afb_yes_q & Q(afb_a_results__isnull=True)
            ),

            # =========================
            # XPERT
            # =========================
            missing_xpert_mtb_rif_conducted=Count(
                "id",
                filter=afb_xpert_required_q & Q(xpert_mtb_rif_conducted__isnull=True)
            ),
            missing_xpert_date=Count(
                "id",
                filter=xpert_yes_q & Q(xpert_date__isnull=True)
            ),
            missing_xpert_mtb=Count(
                "id",
                filter=xpert_yes_q & Q(xpert_mtb__isnull=True)
            ),
            missing_error_code=Count(
                "id",
                filter=xpert_is_8_q & Q(error_code__isnull=True)
            ),
            missing_xpert_rif=Count(
                "id",
                filter=xpert_in_2_6_q & Q(xpert_rif__isnull=True)
            ),
            missing_ct_value=Count(
                "id",
                filter=xpert_in_2_6_q & ~(
                    Q(ct_value__isnull=False, ct_na=False)
                    | Q(ct_value__isnull=True, ct_na=True)
                    | Q(ct_value__in=[99, 99.0])
                )
            ),
        )

        for g in grouped:
            total_issues = sum(
                g[k] for k in g if k.startswith("missing_")
            )

            ClinicDQSnapshot.objects.update_or_create(
                snapshot=snapshot,
                zone_id=g["screening__site__district__region__zone_id"],
                site_id=g["screening__site_id"],
                defaults={
                    "total_clinics": g["total_clinics"],
                    "total_issues": total_issues,
                    **{k: g[k] for k in g if k.startswith("missing_")},
                }
            )

        self.stdout.write(
            self.style.SUCCESS(f"Clinic DQ snapshot created/updated for {today}")
        )
