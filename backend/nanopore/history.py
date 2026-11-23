"""
Change history of every form (django-simple-history).

Each entry keeps who changed the record, when, the full record, where the change came
from (history_source: a form, CTRL's forms, a TB-LIS upload, the nightly sync, the
Recycle Bin) and, for corrections, the reason the user gave.

Only real changes are kept: a save that changes nothing records nothing, and a save
followed by its checkbox questions (many-to-many) is one entry. The page that shows a
record's history is nanopore/views/history_view.py.
"""
import contextvars
from contextlib import contextmanager

from django.db import models

STARTING_POINT = "Starting point"
FORM, SYSTEM = "Form", "System"
# Bookkeeping that changes on every save; not a change of an answer
IGNORED = {"updated_at", "updated_by", "updated_by_id", "created_at", "created_by", "created_by_id"}

REGISTRY = []  # the HistoricalRecords of every tracked model
_source = contextvars.ContextVar("history_source", default="")


class HistorySource(models.Model):
    """Extra column of every history table: where the change came from."""
    history_source = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        abstract = True


def tracked(m2m_fields=()):
    """HistoricalRecords for a model, with its checkbox questions and the source column."""
    from simple_history.models import HistoricalRecords
    records = HistoricalRecords(bases=[HistorySource], m2m_fields=list(m2m_fields))
    REGISTRY.append(records)
    return records


@contextmanager
def source(label):
    """Every change saved inside this block is recorded as coming from label (e.g. a TB-LIS upload)."""
    token = _source.set(label)
    try:
        yield
    finally:
        _source.reset(token)


def records_for(model):
    return next((records for records in REGISTRY if getattr(records, "cls", None) is model), None)


def _plain_answer(value):
    """Blank text and no answer are the same answer."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return value


def _stored(field, value):
    """An answer as the database keeps it: TB-LIS gives some as text ("2" for a volume of 2.00)."""
    value = _plain_answer(value)
    if value is not None and not field.is_relation:
        try:
            value = field.to_python(value)
        except Exception:
            pass
    return value


def _answers(instance):
    return {field.attname: _stored(field, getattr(instance, field.attname)) for field in instance._meta.concrete_fields
            if field.attname not in IGNORED}


def _checkboxes(entry):
    found = {}
    for field in entry._history_m2m_fields:
        target = field.m2m_reverse_field_name()
        found[field.name] = {getattr(row, f"{target}_id") for row in getattr(entry, field.name).all()}
    return found


def _same(entry, previous):
    tracked = [field for field in entry.instance_type._meta.concrete_fields if field.attname not in IGNORED]
    if any(_stored(field, getattr(entry, field.attname, None)) != _stored(field, getattr(previous, field.attname, None))
           for field in tracked):
        return False
    return _checkboxes(entry) == _checkboxes(previous)


# ── signals ────────────────────────────────────────────────────────────────

def skip_unchanged(sender, instance, raw=False, **kwargs):
    """Before a save: a new save starts; nothing changed (only bookkeeping) -> no history entry for it."""
    if records_for(sender) is None:
        return
    if not getattr(instance, "_history_one_change", False):
        instance._history_ids = []  # the entries this save makes; its checkbox questions join them
    if raw or instance._state.adding or instance.pk is None:
        return
    current = sender._default_manager.filter(pk=instance.pk).first()
    if current is not None and _answers(current) == _answers(instance):
        instance.skip_history_when_saving = True
        instance._history_skip_set = True


def stop_skipping(sender, instance, **kwargs):
    if getattr(instance, "_history_skip_set", False):
        del instance.skip_history_when_saving
        del instance._history_skip_set


def fill_source(sender, instance, history_instance, history_user=None, **kwargs):
    history_instance.history_source = (
        getattr(instance, "_history_source", "") or _source.get() or (FORM if history_user else SYSTEM)
    )[:200]


def keep_one_entry_per_save(sender, instance, history_instance, **kwargs):
    """
    Drop an entry identical to the one before, and fold the entries one save makes
    (the record, then each checkbox question) into the last one.
    """
    if getattr(instance, "_history_starting_point", False):
        return
    previous = history_instance.prev_record
    made_now = getattr(instance, "_history_ids", [])
    if previous is not None and previous.history_id in made_now:
        if previous.history_type == "+":
            history_instance.history_type = "+"
        history_instance.history_change_reason = history_instance.history_change_reason or previous.history_change_reason
        history_instance.save(update_fields=["history_type", "history_change_reason"])
        previous.delete()
        previous = history_instance.prev_record
    if previous is not None and history_instance.history_type == "~" and _same(history_instance, previous):
        history_instance.delete()
        return
    instance._history_ids = made_now + [history_instance.history_id]


def connect():
    from django.db.models.signals import post_save, pre_save
    from simple_history.signals import post_create_historical_record, pre_create_historical_record

    for records in REGISTRY:
        pre_save.connect(skip_unchanged, sender=records.cls, dispatch_uid=f"history_skip_{records.cls.__name__}")
        post_save.connect(stop_skipping, sender=records.cls, dispatch_uid=f"history_stop_{records.cls.__name__}")
    pre_create_historical_record.connect(fill_source, dispatch_uid="history_source")
    post_create_historical_record.connect(keep_one_entry_per_save, dispatch_uid="history_one_per_save")


@contextmanager
def one_change(instance):
    """Several saves of one record that make one change (e.g. rebuilding EDCS/TBLIS): one history entry."""
    instance._history_one_change, instance._history_ids = True, []
    try:
        yield instance
    finally:
        del instance._history_one_change


def record_starting_points():
    """One entry for every record without history yet, so the first change after it shows the old value."""
    created = 0
    for records in REGISTRY:
        model = records.cls
        with_history = model.history.values("id")
        for instance in model._default_manager.exclude(pk__in=with_history).iterator(chunk_size=500):
            instance._history_source = STARTING_POINT
            instance._history_starting_point = True
            records.create_historical_record(instance, "+")
            created += 1
    return created


def record_restored(instance):
    """The Recycle Bin puts records back without the usual save signals: note it in their history."""
    records = records_for(type(instance))
    if records is not None:
        instance._history_source = "Recycle Bin: restored"
        instance._history_starting_point = True
        records.create_historical_record(instance, "+")
