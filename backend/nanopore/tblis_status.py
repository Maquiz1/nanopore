"""
What TB-LIS currently says about a lab number, over every upload.

An export doesn't always hold every earlier lab number, so a new file only decides
about the lab numbers in it:
  * in the file and accepted  -> its values are used
  * in the file and rejected  -> the TB-LIS values go (the form's own values stay)
                                 and the record is listed for CTRL
  * not in the file           -> the last decision stands; an accepted result is
                                 marked "Not in latest file"

TblisRawData holds the accepted rows (uploads before October 2026 stored every row)
and TblisLeftOut the lab numbers each upload rejected. The upload, the nightly sync,
the exports and the follow-up lists all ask here, so they agree.
"""
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from nanopore.models import TblisLeftOut, TblisRawData, TblisUploadBatch
from nanopore.tblis_file import FILTER_REASONS, filter_reason, is_isolate

CURRENT, NOT_IN_LATEST, REJECTED = "current", "not_in_latest", "rejected"
LABELS = {CURRENT: "In latest file", NOT_IN_LATEST: "Not in latest file", REJECTED: "Rejected in TB-LIS"}
USED = (CURRENT, NOT_IN_LATEST)
REASONS = {**FILTER_REASONS, "not_isolate": "No longer recorded as an isolate"}


@dataclass(frozen=True)
class Status:
    state: str = ""  # empty: TB-LIS never had this lab number
    raw_id: Optional[int] = None  # the row to use
    reason: str = ""

    @property
    def label(self):
        return LABELS.get(self.state, "")

    @property
    def reason_label(self):
        return REASONS.get(self.reason, "")

    @property
    def used(self):
        return self.state in USED


NEVER_SEEN = Status()


def statuses(labnos=None, isolate=False):
    """
    {lab number: Status}. labnos: a list or subquery (None: every lab number).
    isolate: the number is another zone's isolate number, so only an Isolate row is accepted.
    Otherwise it is a sputum lab number, and Isolate rows don't count as seeing it.
    """
    raw = TblisRawData.objects.all()
    left_out = TblisLeftOut.objects.all()
    if labnos is not None:
        raw, left_out = raw.filter(labno__in=labnos), left_out.filter(labno__in=labnos)

    # (when, order, upload, accepted row, why not)
    seen = defaultdict(list)
    for pk, labno, batch, when, spectype, genexpert in raw.values_list(
        "pk", "labno", "upload_batch_id", "uploaded_at", "raw_data__spectype", "raw_data__peripheralres_genexpert",
    ):
        row = {"spectype": str(spectype or ""), "peripheralres_genexpert": str(genexpert or "")}
        if isolate:
            reason = "" if is_isolate(row) else "not_isolate"
        elif is_isolate(row):
            continue
        else:
            reason = filter_reason(row) or ""
        seen[labno].append((when, pk, batch, None if reason else pk, reason))
    for pk, labno, batch, when, reason in left_out.values_list("pk", "labno", "upload_batch_id", "seen_at", "reason"):
        seen[labno].append((when, pk, batch, None, "not_isolate" if isolate else reason))

    latest = TblisUploadBatch.objects.values_list("pk", flat=True).first()
    found = {}
    for labno, sightings in seen.items():
        last = max(sightings, key=lambda sighting: sighting[:2])
        # An accepted row wins over a rejected one in the same file. Rows from before
        # uploads were recorded have no file, so each stands alone.
        same_file = [last] if last[2] is None else [s for s in sightings if s[2] == last[2]]
        accepted = [sighting for sighting in same_file if sighting[3]]
        if not accepted:
            found[labno] = Status(REJECTED, reason=last[4])
        else:
            state = CURRENT if last[2] == latest else NOT_IN_LATEST
            found[labno] = Status(state, raw_id=max(accepted, key=lambda sighting: sighting[:2])[3])
    return found


def status(labno, isolate=False):
    return statuses([labno], isolate).get(labno, NEVER_SEEN) if labno else NEVER_SEEN


def record_statuses(records):
    """{screening id: Status} for Zonal Lab or EDCS/TBLIS records: Dar by lab number, others by isolate number."""
    from nanopore.edcs_tblis_cards import ctrl_q

    found = {}
    for qs, number, isolate in ((records.filter(ctrl_q()), "unique_lab_no", False),
                                (records.exclude(ctrl_q()), "isolate_unique_lab_no", True)):
        numbered = qs.filter(**{f"{number}__isnull": False})
        by_number = statuses(numbered.values(number), isolate)
        for screening_id, value in numbered.values_list("screening_id", number):
            if value in by_number:
                found[screening_id] = by_number[value]
    return found


def used_labnos(records):
    """The lab numbers of these Dar records with a TB-LIS result in use."""
    return [labno for labno, found in statuses(records.values("unique_lab_no")).items() if found.used]
