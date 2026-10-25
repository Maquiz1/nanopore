"""
Celery task: export EDCS/TBLIS data to an Excel (.xlsx) file in the background,
reporting progress so the UI can show a progress bar.

Card-type → column mapping:
  - TBLIS cards (total_tblis, tblis_not_in_edcs):
      From TblisRawData.raw_data JSON:
      labno, studycode, tbno, name, gender, age,
      hfacilitycode, hfacility, hfacilitydistrict, tbregion, patcategory

  - All other EDCS cards (uses ZonalLaboratory joined to Screening / ClinicLaboratory):
      pid, xpert_mtb_rif_conducted, xpert_mtb,
      culture_performed, site, zone
"""
import os
from celery import shared_task
from django.conf import settings

from nanopore.edcs_tblis_cards import CARDS, card_queryset
from nanopore.substudy import SUBSTUDIES


# ─── helpers ──────────────────────────────────────────────────────────────────

TBLIS_CARD_TYPES = {key for key, card in CARDS.items() if card.source == "tblis"}

TBLIS_COLUMNS = [
    "labno", "studycode", "tbno", "name", "gender", "age",
    "hfacilitycode", "hfacility", "hfacilitydistrict", "tbregion", "patcategory",
]

EDCS_COLUMNS = [
    "pid",
    "date_sputum_received",
    "appearance",
    "unique_lab_no",
    "xpert_mtb_rif_conducted",
    "xpert_mtb",
    "culture_performed",
    "site",
    "zone",
]

def _build_edcs_qs(filters):
    """Records behind the card (nanopore/edcs_tblis_cards.py), narrowed by the list filters."""
    filters = filters or {}
    qs = card_queryset(filters.get("card_type", ""))
    if filters.get("zone"):
        qs = qs.filter(screening__site__district__region__zone_id=filters["zone"])
    if filters.get("site"):
        qs = qs.filter(screening__site_id=filters["site"])
    if filters.get("pid"):
        qs = qs.filter(screening__pid__icontains=filters["pid"])
    if filters.get("unique_lab_no"):
        qs = qs.filter(unique_lab_no__icontains=filters["unique_lab_no"])
    if filters.get("substudy") in SUBSTUDIES:
        qs = qs.filter(substudy_group=filters["substudy"])
    if filters.get("start_date"):
        qs = qs.filter(date_sputum_received__gte=filters["start_date"])
    if filters.get("end_date"):
        qs = qs.filter(date_sputum_received__lte=filters["end_date"])
    return qs


def _build_tblis_qs(filters):
    """Raw TB-LIS rows behind the card."""
    filters = filters or {}
    qs = card_queryset(filters.get("card_type", ""))
    if filters.get("unique_lab_no"):
        qs = qs.filter(labno__icontains=filters["unique_lab_no"])
    return qs


def _scope_for_user(qs, user_id, is_tblis):
    """Limit the export to what the requesting user may see (see utils/access.py)."""
    from django.contrib.auth import get_user_model
    from utils.access import is_unscoped, scope_queryset

    user = get_user_model().objects.filter(pk=user_id).first() if user_id else None
    if user is None:
        return qs.none()
    if is_tblis:
        # Raw TBLIS rows carry no site: only unscoped users may export them.
        return qs if is_unscoped(user) else qs.none()
    return scope_queryset(user, qs, "screening__site")


# ─── main task ────────────────────────────────────────────────────────────────

@shared_task(bind=True)
def export_edcs_tblis_csv(self, filename="edcs_tblis_export.xlsx", filters=None, user_id=None):
    """
    Export EDCS/TBLIS data to Excel based on card_type in filters.

    Always writes to PRIVATE_EXPORTS_DIR/<filename> (outside the public media folder).
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return {"state": "FAILURE", "error": "openpyxl not installed"}

    filters = filters or {}
    card_type = filters.get("card_type", "")
    is_tblis = card_type in TBLIS_CARD_TYPES

    export_dir = str(settings.PRIVATE_EXPORTS_DIR)
    os.makedirs(export_dir, exist_ok=True)
    filepath = os.path.join(export_dir, filename)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Export"

    # ── Header style ──────────────────────────────────────────────────────────
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1E3A5F")
    center = Alignment(horizontal="center", vertical="center")

    if is_tblis:
        columns = TBLIS_COLUMNS
        qs = _build_tblis_qs(filters)
    else:
        columns = EDCS_COLUMNS
        qs = _build_edcs_qs(filters)

    qs = _scope_for_user(qs, user_id, is_tblis)

    total = qs.count()

    # Write header row
    for col_idx, col_name in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name.upper().replace("_", " "))
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center

    if total == 0:
        wb.save(filepath)
        return {"state": "SUCCESS", "file": filename, "total": 0}

    # ── Write rows ────────────────────────────────────────────────────────────
    if is_tblis:
        for row_idx, obj in enumerate(qs.iterator(chunk_size=500), start=2):
            rd = obj.raw_data or {}
            row_data = [
                obj.labno,
                rd.get("studycode", "") or rd.get("StudyCode", "") or rd.get("STUDYCODE", ""),
                rd.get("tbno", "") or rd.get("TBNo", "") or rd.get("TBNO", ""),
                rd.get("name", "") or rd.get("Name", "") or rd.get("NAME", ""),
                rd.get("gender", "") or rd.get("Gender", "") or rd.get("GENDER", ""),
                rd.get("age", "") or rd.get("Age", "") or rd.get("AGE", ""),
                rd.get("hfacilitycode", "") or rd.get("HFacilityCode", "") or rd.get("HFACILITYCODE", ""),
                rd.get("hfacility", "") or rd.get("HFacility", "") or rd.get("HFACILITY", ""),
                rd.get("hfacilitydistrict", "") or rd.get("HFacilityDistrict", "") or rd.get("HFACILITYDISTRICT", ""),
                rd.get("tbregion", "") or rd.get("TBRegion", "") or rd.get("TBREGION", ""),
                rd.get("patcategory", "") or rd.get("PatCategory", "") or rd.get("PATCATEGORY", ""),
            ]
            for col_idx, val in enumerate(row_data, start=1):
                ws.cell(row=row_idx, column=col_idx, value=val if val != "" else None)

            i = row_idx - 1
            if i % 100 == 0 or i == total:
                self.update_state(state="PROGRESS", meta={"current": i, "total": total})

    else:
        for row_idx, obj in enumerate(qs.iterator(chunk_size=500), start=2):
            try:
                pid = getattr(obj.screening, "pid", "") or ""
            except Exception:
                pid = ""

            try:
                cl = obj.screening.clinic_laboratory
                xpert_mtb_rif = cl.xpert_mtb_rif_conducted.name if cl and cl.xpert_mtb_rif_conducted else ""
                xpert_mtb = cl.xpert_mtb.name if cl and cl.xpert_mtb else ""
            except Exception:
                xpert_mtb_rif = ""
                xpert_mtb = ""

            try:
                date_sputum_received = obj.date_sputum_received.strftime("%Y-%m-%d") if getattr(obj, "date_sputum_received", None) else ""
            except Exception:
                date_sputum_received = ""

            try:
                appearance = obj.appearance.name if getattr(obj, "appearance", None) else ""
            except Exception:
                appearance = ""

            try:
                unique_lab_no = getattr(obj, "unique_lab_no", "") or ""
            except Exception:
                unique_lab_no = ""

            try:
                culture = obj.culture_performed.name if obj.culture_performed else ""
            except Exception:
                culture = ""

            try:
                site = obj.screening.site.name if obj.screening and obj.screening.site else ""
            except Exception:
                site = ""

            try:
                zone = (
                    obj.screening.site.district.region.zone.name
                    if obj.screening and obj.screening.site
                    and obj.screening.site.district
                    and obj.screening.site.district.region
                    and obj.screening.site.district.region.zone
                    else ""
                )
            except Exception:
                zone = ""

            row_data = [
                pid,
                date_sputum_received,
                appearance,
                unique_lab_no,
                xpert_mtb_rif,
                xpert_mtb,
                culture,
                site,
                zone,
            ]
            for col_idx, val in enumerate(row_data, start=1):
                ws.cell(row=row_idx, column=col_idx, value=val if val != "" else None)

            i = row_idx - 1
            if i % 100 == 0 or i == total:
                self.update_state(state="PROGRESS", meta={"current": i, "total": total})

    # Auto-fit column widths (approximate)
    for col in ws.columns:
        max_len = max((len(str(cell.value)) if cell.value else 0) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 4, 12), 60)

    wb.save(filepath)
    return {"state": "SUCCESS", "file": filename, "total": total}
