"""
Recycle bin: recoverable ("soft") deletes.

Deleting a record moves it, and every record that depends on it, into one
DeletedRecord entry and removes them from the forms. Restoring puts them all
back exactly as they were (same IDs, same values, same many-to-many choices).

What goes with what:
  * Screening        -> all its forms: Enrollment, Clinic Lab, Zonal Lab,
                        EDCS/TBLIS, Diagnosis and every Regimen Change
                        (whatever the database cascades from Screening).
  * Clinic Lab       -> its Zonal Lab and EDCS/TBLIS record. Whether a participant
                        needs a Zonal Lab at all depends on the clinic Xpert MTB/RIF result.
  * Zonal Lab        -> its EDCS/TBLIS record. That record is a copy of the Zonal
                        Lab (plus TBLIS results for CTRL sites) rebuilt by the TBLIS
                        upload and the daily sync, so it can't outlive its Zonal Lab.
  * Diagnosis        -> its Regimen Changes. They are entered from the Diagnosis
                        form when "Regimen changed = Yes".
  * Any other form   -> only that record.

These dependents hang off the Screening in the database, so the rules live in
DEPENDS_ON below and are followed down the chain (Clinic Lab -> Zonal Lab ->
EDCS/TBLIS). Restoring a dependent on its own (e.g. a Zonal Lab) is only allowed
once the form it depends on (the Clinic Lab) exists again.

Uploaded TBLIS rows (TblisRawData) are independent and never touched: they are
only used to update matching EDCS/TBLIS records.
"""
import json

from django.core import serializers
from django.db import DEFAULT_DB_ALIAS, IntegrityError, router, transaction
from django.db.models.deletion import Collector
from django.utils import timezone

from nanopore.models import (
    ClinicLaboratory, DeletedRecord, Diagnosis, EdcsTblisZonal, RegimenChanges, Screening, ZonalLaboratory,
)

# dependent form -> form it depends on (same participant)
DEPENDS_ON = {
    ZonalLaboratory: ClinicLaboratory,
    EdcsTblisZonal: ZonalLaboratory,
    RegimenChanges: Diagnosis,
}

FORM_LABELS = {
    ClinicLaboratory: "Clinic Lab",
    ZonalLaboratory: "Zonal Lab",
    EdcsTblisZonal: "EDCS/TBLIS record",
    Diagnosis: "Diagnosis",
    RegimenChanges: "Regimen Changes",
}


class RestoreError(Exception):
    pass


def _extra_dependents(obj):
    """
    Records that belong to obj by meaning although the database doesn't cascade
    them, following the chain (a Clinic Lab brings its Zonal Lab, which brings its
    EDCS/TBLIS record).
    """
    extras = []
    for dependent, parent in DEPENDS_ON.items():
        if isinstance(obj, parent):
            for record in dependent.objects.filter(screening_id=obj.screening_id):
                extras.append(record)
                extras.extend(_extra_dependents(record))
    return extras


def collect(obj):
    """Every record that is removed together with obj, in restore order (parents first)."""
    using = router.db_for_write(obj.__class__, instance=obj) or DEFAULT_DB_ALIAS
    collector = Collector(using=using)
    collector.collect([obj])
    for extra in _extra_dependents(obj):  # one model per collect() call
        collector.collect([extra])
    collector.sort()  # deletion order: dependents before the records they point to
    ordered = []
    for model, instances in collector.data.items():
        ordered.extend(sorted(instances, key=lambda instance: instance.pk))
    # Children Django deletes in bulk (no signals) are only listed as querysets.
    for queryset in collector.fast_deletes:
        ordered[:0] = [instance for instance in queryset if instance not in ordered]
    return list(reversed(ordered))


def summarize(objects):
    summary = {}
    for instance in objects:
        name = instance.__class__.__name__
        summary[name] = summary.get(name, 0) + 1
    return summary


def _pid_of(obj):
    if isinstance(obj, Screening):
        return obj.pid
    screening = getattr(obj, "screening", None)
    return getattr(screening, "pid", "") or getattr(obj, "pid", "") or ""


@transaction.atomic
def soft_delete(obj, user, reason=""):
    """Move obj and its dependents to the recycle bin. Returns the DeletedRecord."""
    objects = collect(obj)
    entry = DeletedRecord.objects.create(
        model_name=obj.__class__.__name__,
        object_id=str(obj.pk),
        pid=_pid_of(obj),
        summary=summarize(objects),
        payload=json.loads(serializers.serialize("json", objects)),
        reason=reason,
        deleted_by=user if getattr(user, "is_authenticated", False) else None,
    )
    for instance in _extra_dependents(obj):
        instance.delete()
    obj.delete()  # the database cascades the rest
    return entry


@transaction.atomic
def restore(entry, user):
    """Put every record of a recycle-bin entry back. Raises RestoreError if that's not possible."""
    if entry.is_restored:
        raise RestoreError("This record was already restored.")

    records = list(serializers.deserialize("python", entry.payload))
    for record in records:
        model = record.object.__class__
        if model.objects.filter(pk=record.object.pk).exists():
            raise RestoreError(f"{model.__name__} #{record.object.pk} already exists again.")
        screening_id = getattr(record.object, "screening_id", None)
        restoring_screening = any(isinstance(r.object, Screening) and r.object.pk == screening_id for r in records)
        if screening_id and not restoring_screening and not Screening.objects.filter(pk=screening_id).exists():
            raise RestoreError(
                f"Participant {entry.pid or screening_id} is itself in the recycle bin. Restore the Screening first."
            )
        parent = DEPENDS_ON.get(model)
        if parent and not restoring_screening:
            parent_in_entry = any(isinstance(r.object, parent) for r in records)
            if not parent_in_entry and not parent.objects.filter(screening_id=screening_id).exists():
                raise RestoreError(
                    f"{FORM_LABELS[model]} depends on the {FORM_LABELS[parent]} of participant "
                    f"{entry.pid or screening_id}, which is in the recycle bin. Restore the {FORM_LABELS[parent]} first."
                )

    try:
        with transaction.atomic():
            for record in records:
                record.save()  # raw save: same pk, values and many-to-many choices
    except IntegrityError as exc:
        raise RestoreError(
            "Cannot restore: a newer record now uses the same participant, lab number or form "
            f"(e.g. a new Enrollment was entered for this participant). Details: {exc}"
        ) from exc

    entry.restored_at = timezone.now()
    entry.restored_by = user
    entry.save(update_fields=["restored_at", "restored_by"])
    return entry
