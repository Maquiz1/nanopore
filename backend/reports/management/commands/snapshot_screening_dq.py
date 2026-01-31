from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.db.models import Count, Q, F

from reports.models import DataQualitySnapshot, ScreeningDQSnapshot


DAR_ES_SALAAM_ZONE_ID = 1


class Command(BaseCommand):
    help = "Create daily Screening Data Quality snapshot"

    def handle(self, *args, **options):
        Screening = apps.get_model("nanopore", "Screening")

        snapshot, _ = DataQualitySnapshot.objects.get_or_create(
            snapshot_date=timezone.localdate()
        )

        qs = Screening.objects.select_related(
            "site",
            "site__district__region__zone"
        )

        grouped = qs.values(
            "site__district__region__zone_id",
            "site_id",
        ).annotate(
            total_screenings=Count("id"),

            missing_screening_date=Count("id", filter=Q(screening_date__isnull=True)),
            missing_pid1=Count("id", filter=Q(pid1__isnull=True)),
            missing_pid2=Count("id", filter=Q(pid2__isnull=True)),
            missing_sex=Count("id", filter=Q(sex__isnull=True)),
            missing_age_dob=Count(
                "id",
                filter=Q(age__isnull=True, dob__isnull=True)
            ),
            missing_consent=Count("id", filter=Q(consent__isnull=True)),
            missing_consent_date_when_yes=Count(
                "id",
                filter=Q(consent__name__iexact="yes", consent_date__isnull=True)
            ),
            missing_age18years=Count("id", filter=Q(age18years__isnull=True)),

            # Zone-specific logic
            missing_present_symptoms=Count(
                "id",
                filter=Q(
                    site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID,
                    present_symptoms__isnull=True
                )
            ),
            missing_genexpert_confirmation=Count(
                "id",
                filter=~Q(site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID)
                & Q(genexpert_confirmation__isnull=True)
            ),

            missing_produce_resp_sample=Count(
                "id", filter=Q(produce_resp_sample__isnull=True)
            ),
            missing_unable_understand=Count(
                "id", filter=Q(unable_understand__isnull=True)
            ),
            missing_not_willing=Count(
                "id", filter=Q(not_willing__isnull=True)
            ),
            missing_enrolled=Count(
                "id", filter=Q(enrolled__isnull=True)
            ),
            missing_reasons=Count(
                "id",
                filter=Q(enrolled__name__iexact="no", reasons__isnull=True)
            ),
            missing_reasons_other=Count(
                "id",
                filter=Q(reasons__value=96, reasons_other__isnull=True)
            ),

            # PID quality checks
            duplicate_pids=Count(
                "id",
                filter=Q(pid1__isnull=False)
                & Q(pid1__in=qs.values("pid1")
                    .annotate(c=Count("id"))
                    .filter(c__gt=1)
                    .values("pid1"))
            ),
            mismatched_pids=Count(
                "id",
                filter=Q(pid1__isnull=False, pid2__isnull=False)
                & ~Q(pid1=F("pid2"))
            ),
            invalid_length_pids=Count(
                "id",
                filter=~Q(pid1__regex=r"^.{16}$")
            ),
        )

        rows = []
        for g in grouped:
            total_issues = sum([
                g["missing_screening_date"],
                g["missing_pid1"],
                g["missing_pid2"],
                g["missing_sex"],
                g["missing_age_dob"],
                g["missing_consent"],
                g["missing_consent_date_when_yes"],
                g["missing_age18years"],
                g["missing_present_symptoms"],
                g["missing_genexpert_confirmation"],
                g["missing_produce_resp_sample"],
                g["missing_unable_understand"],
                g["missing_not_willing"],
                g["missing_enrolled"],
                g["missing_reasons"],
                g["missing_reasons_other"],
                g["duplicate_pids"],
                g["mismatched_pids"],
                g["invalid_length_pids"],
            ])

            rows.append(
                ScreeningDQSnapshot(
                    snapshot=snapshot,
                    zone_id=g["site__district__region__zone_id"],
                    site_id=g["site_id"],
                    total_screenings=g["total_screenings"],
                    total_issues=total_issues,

                    missing_screening_date=g["missing_screening_date"],
                    missing_pid1=g["missing_pid1"],
                    missing_pid2=g["missing_pid2"],
                    missing_sex=g["missing_sex"],
                    missing_age_dob=g["missing_age_dob"],
                    missing_consent=g["missing_consent"],
                    missing_consent_date_when_yes=g["missing_consent_date_when_yes"],
                    missing_age18years=g["missing_age18years"],
                    missing_present_symptoms=g["missing_present_symptoms"],
                    missing_genexpert_confirmation=g["missing_genexpert_confirmation"],
                    missing_produce_resp_sample=g["missing_produce_resp_sample"],
                    missing_unable_understand=g["missing_unable_understand"],
                    missing_not_willing=g["missing_not_willing"],
                    missing_enrolled=g["missing_enrolled"],
                    missing_reasons=g["missing_reasons"],
                    missing_reasons_other=g["missing_reasons_other"],
                    duplicate_pids=g["duplicate_pids"],
                    mismatched_pids=g["mismatched_pids"],
                    invalid_length_pids=g["invalid_length_pids"],
                )
            )

        ScreeningDQSnapshot.objects.bulk_create(
            rows,
            ignore_conflicts=True
        )

        self.stdout.write(
            self.style.SUCCESS("Screening data quality snapshot created")
        )
