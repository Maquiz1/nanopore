# nanopore/tasks.py
from celery import shared_task
import csv
from django.apps import apps
from django.core.exceptions import ValidationError

from nanopore.views.laboratory.edcs_tblis.edcs_tblis_upload_view import (
    safe_int, safe_decimal, parse_date_field,
    get_foreign, split_m2m
)

from options.models import (
    SampleAppearance, YesNo, CultureMethod, MicroscopyType, CultureMicroscopyResults,
    LJCultureResult, MGITCultureResult, YesNoNA, PhenotypicDSTResults,
    XpertXDRResults, XpertXDRResultsTwo, XpertXDRResultsThree,
    FirstLineDrugs, SecondLineDrugs,
    MTBResultsLPA, RIFResultLPA, INHResultLPA, NanoporeResults,
    NanoporeSequencingResults, NanoporeSequencingDelayedReasons
)


@shared_task(bind=True)
def import_edcs_tblis(self, filepath):

    Screening = apps.get_model("nanopore", "Screening")
    EdcsTblisZonal = apps.get_model("nanopore", "EdcsTblisZonal")

    total = sum(1 for _ in open(filepath)) - 1
    processed = 0

    row_errors = []
    created = 0
    updated = 0

    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=2):

            pid = row.get("pid")

            try:
                screening = Screening.objects.filter(pid=pid).first()
                if not screening:
                    raise ValidationError(f"No Screening found pid={pid}")

                defaults = {
                    "date_sputum_received": parse_date_field(row.get("date_sputum_received")),
                    "appearance": get_foreign(SampleAppearance, row.get("appearance")),
                    "sample_volume": safe_decimal(row.get("sample_volume")),
                    "unique_lab_no": row.get("unique_lab_no") or None,

                    "culture_performed": get_foreign(YesNo, row.get("culture_performed")),
                    "microscopy_type": get_foreign(MicroscopyType, row.get("microscopy_type")),
                    "microscopy_date": parse_date_field(row.get("microscopy_date")),
                    "microscopy_results": get_foreign(CultureMicroscopyResults, row.get("microscopy_results")),

                    "lj_results": get_foreign(LJCultureResult, row.get("lj_results")),
                    "mgit_results": get_foreign(MGITCultureResult, row.get("mgit_results")),

                    "rifampicin": get_foreign(PhenotypicDSTResults, row.get("rifampicin")),
                    "isoniazid": get_foreign(PhenotypicDSTResults, row.get("isoniazid")),

                    "nanopore_done": get_foreign(YesNo, row.get("nanopore_done")),
                    "nanopore_results": get_foreign(NanoporeSequencingResults, row.get("nanopore_results")),

                    "sequencing_delayed_days": safe_int(row.get("sequencing_delayed_days")),
                    "remarks": row.get("remarks") or None,
                }

                lab, was_created = EdcsTblisZonal.objects.update_or_create(
                    screening=screening,
                    defaults=defaults
                )

                lab.culture_method.set(split_m2m(CultureMethod, row.get("culture_method")))
                lab.first_line_drugs.set(split_m2m(FirstLineDrugs, row.get("first_line_drugs")))
                lab.second_line_drugs.set(split_m2m(SecondLineDrugs, row.get("second_line_drugs")))
                lab.lpa1_inh.set(split_m2m(INHResultLPA, row.get("lpa1_inh")))
                lab.sequencing_delayed_reasons.set(
                    split_m2m(NanoporeSequencingDelayedReasons, row.get("sequencing_delayed_reasons"))
                )

                created += int(was_created)
                updated += int(not was_created)

            except Exception as e:
                row_errors.append(f"Row {idx} (pid={pid}): {e}")

            processed += 1

            self.update_state(
                state="PROGRESS",
                meta={"current": processed, "total": total}
            )

    return {
        "current": processed,
        "total": total,
        "created": created,
        "updated": updated,
        "errors": row_errors,
    }
