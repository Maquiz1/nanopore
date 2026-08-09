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
from django.apps import apps
from django.db.models import Q


# ─── helpers ──────────────────────────────────────────────────────────────────

TBLIS_CARD_TYPES = {"total_tblis", "tblis_not_in_edcs"}

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

CTRL_PREFIXES = [
    "DF_TZ_SS2_14", "DF_TZ_SS2_15", "DF_TZ_SS2_16",
    "DF_TZ_SS2_17", "DF_TZ_SS2_18", "DF_TZ_SS2_19",
]

SS2_XPERT = [2, 3, 4, 5, 6]
SS4_XPERT = [1, 7, 8, 9]


def _ctrl_prefix_q():
    q = Q()
    for p in CTRL_PREFIXES:
        q |= Q(screening__pid__startswith=p)
    return q


def _build_edcs_qs(filters):
    """Return an EdcsTblisZonal or ZonalLaboratory queryset filtered by filters dict."""
    card_type = (filters or {}).get("card_type", "")

    # Cards that target ZonalLaboratory directly
    if card_type in {"total_edcs", "ctrl"} or card_type.startswith("other_zones"):
        ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")
        qs = ZonalLaboratory.objects.select_related(
            "screening",
            "screening__site",
            "screening__site__district__region__zone",
            "screening__clinic_laboratory",
            "culture_performed",
        )
    else:
        # All other EDCS cards source from EdcsTblisZonal
        EdcsTblisZonal = apps.get_model("nanopore", "EdcsTblisZonal")
        qs = EdcsTblisZonal.objects.select_related(
            "screening",
            "screening__site",
            "screening__site__district__region__zone",
            "screening__clinic_laboratory",
            "culture_performed",
        )

    # Card-type-specific base filtering
    if card_type == "total_edcs":
        pass  # All ZonalLaboratory records without prefix filtering

    elif card_type == "ctrl":
        qs = qs.filter(_ctrl_prefix_q())

    elif card_type == "other_zones":
        qs = qs.exclude(_ctrl_prefix_q())

    elif card_type == "other_zones_substudy2":
        qs = qs.exclude(_ctrl_prefix_q()).filter(screening__clinic_laboratory__xpert_mtb__in=SS2_XPERT)

    elif card_type == "other_zones_substudy4":
        qs = qs.exclude(_ctrl_prefix_q()).filter(screening__clinic_laboratory__xpert_mtb__in=SS4_XPERT)

    elif card_type == "other_zones_uncategorized":
        qs = qs.exclude(_ctrl_prefix_q()).exclude(screening__clinic_laboratory__xpert_mtb__in=SS2_XPERT + SS4_XPERT)

    elif card_type == "other_zones_missing_culture":
        qs = qs.exclude(_ctrl_prefix_q()).filter(culture_performed__isnull=True)

    elif card_type == "edcs_not_in_tblis":
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        tblis_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(_ctrl_prefix_q()).exclude(unique_lab_no__in=tblis_labnos)


    elif card_type == "merged":
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        merged_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch, is_merged=True
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(_ctrl_prefix_q(), unique_lab_no__in=merged_labnos)

    elif card_type == "merged_substudy2":
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        merged_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch, is_merged=True
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(
            _ctrl_prefix_q(),
            unique_lab_no__in=merged_labnos,
            screening__clinic_laboratory__xpert_mtb__in=SS2_XPERT,
        )

    elif card_type == "merged_substudy4":
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        merged_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch, is_merged=True
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(
            _ctrl_prefix_q(),
            unique_lab_no__in=merged_labnos,
            screening__clinic_laboratory__xpert_mtb__in=SS4_XPERT,
        )

    elif card_type == "merged_uncategorized":
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        merged_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch, is_merged=True
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(
            _ctrl_prefix_q(),
            unique_lab_no__in=merged_labnos,
        ).exclude(
            screening__clinic_laboratory__xpert_mtb__in=SS2_XPERT + SS4_XPERT
        )

    elif card_type == "merged_missing_culture_substudy2":
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        merged_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch, is_merged=True
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(
            _ctrl_prefix_q(),
            unique_lab_no__in=merged_labnos,
            screening__clinic_laboratory__xpert_mtb__in=SS2_XPERT,
            culture_performed__isnull=True,
        )

    elif card_type == "merged_missing_culture_substudy4":
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        merged_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch, is_merged=True
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(
            _ctrl_prefix_q(),
            unique_lab_no__in=merged_labnos,
            screening__clinic_laboratory__xpert_mtb__in=SS4_XPERT,
            culture_performed__isnull=True,
        )

    elif card_type == "merged_missing_culture_uncategorized":
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        merged_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch, is_merged=True
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(
            _ctrl_prefix_q(),
            unique_lab_no__in=merged_labnos,
            culture_performed__isnull=True,
        ).exclude(
            screening__clinic_laboratory__xpert_mtb__in=SS2_XPERT + SS4_XPERT
        )

    elif card_type == "edcs_not_in_tblis_substudy2":
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        tblis_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(
            _ctrl_prefix_q(),
            screening__clinic_laboratory__xpert_mtb__in=SS2_XPERT,
        ).exclude(unique_lab_no__in=tblis_labnos)

    elif card_type == "edcs_not_in_tblis_substudy4":
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        tblis_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(
            _ctrl_prefix_q(),
            screening__clinic_laboratory__xpert_mtb__in=SS4_XPERT,
        ).exclude(unique_lab_no__in=tblis_labnos)

    elif card_type == "edcs_not_in_tblis_uncategorized":
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        tblis_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(_ctrl_prefix_q()).exclude(
            unique_lab_no__in=tblis_labnos
        ).exclude(
            screening__clinic_laboratory__xpert_mtb__in=SS2_XPERT + SS4_XPERT
        )

    elif card_type == "missing_culture_substudy2":
        qs = qs.filter(
            screening__clinic_laboratory__xpert_mtb__in=SS2_XPERT,
            culture_performed__isnull=True,
        )

    elif card_type == "missing_culture_substudy4":
        qs = qs.filter(
            screening__clinic_laboratory__xpert_mtb__in=SS4_XPERT,
            culture_performed__isnull=True,
        )

    elif card_type == "missing_culture":
        qs = qs.filter(culture_performed__isnull=True)

    elif card_type == "coverage":
        # Coverage is a percentage – export the CTRL records that ARE in TBLIS (merged)
        TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")
        TblisRawData = apps.get_model("nanopore", "TblisRawData")
        latest_batch = TblisUploadBatch.objects.first()
        tblis_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch
        ).values("labno") if latest_batch else TblisRawData.objects.none().values("labno")
        qs = qs.filter(_ctrl_prefix_q(), unique_lab_no__in=tblis_labnos)

    else:
        # Fallback: all CTRL records
        qs = qs.filter(_ctrl_prefix_q())

    # General additional filters from URL params
    zone_id = (filters or {}).get("zone")
    site_id = (filters or {}).get("site")
    pid = (filters or {}).get("pid")
    substudy = (filters or {}).get("substudy")

    if zone_id:
        qs = qs.filter(screening__site__district__region__zone_id=zone_id)
    if site_id:
        qs = qs.filter(screening__site_id=site_id)
    if pid:
        qs = qs.filter(screening__pid__icontains=pid)
    if substudy == "Substudy 2":
        qs = qs.filter(screening__clinic_laboratory__xpert_mtb__in=SS2_XPERT)
    elif substudy == "Substudy 4":
        qs = qs.filter(screening__clinic_laboratory__xpert_mtb__in=SS4_XPERT)

    # Always sort by zone → site → pid
    qs = qs.order_by(
        "screening__site__district__region__zone__name",
        "screening__site__name",
        "screening__pid",
    )

    return qs


def _build_tblis_qs(filters):
    """Return a TblisRawData queryset filtered by filters dict."""
    TblisRawData = apps.get_model("nanopore", "TblisRawData")
    TblisUploadBatch = apps.get_model("nanopore", "TblisUploadBatch")

    latest_batch = TblisUploadBatch.objects.first()
    qs = TblisRawData.objects.filter(upload_batch=latest_batch) if latest_batch else TblisRawData.objects.none()

    card_type = (filters or {}).get("card_type", "")

    if card_type == "tblis_not_in_edcs":
        ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")
        zonal_labnos = ZonalLaboratory.objects.values("unique_lab_no")
        qs = qs.exclude(labno__in=zonal_labnos)

    # Sort TBLIS records by labno
    qs = qs.order_by("labno")

    return qs


# ─── main task ────────────────────────────────────────────────────────────────

@shared_task(bind=True)
def export_edcs_tblis_csv(self, filename="edcs_tblis_export.xlsx", filters=None, user_id=None):
    """
    Export EDCS/TBLIS data to Excel based on card_type in filters.

    Always writes to MEDIA_ROOT/exports/<filename>.
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return {"state": "FAILURE", "error": "openpyxl not installed"}

    filters = filters or {}
    card_type = filters.get("card_type", "")
    is_tblis = card_type in TBLIS_CARD_TYPES

    export_dir = os.path.join(settings.MEDIA_ROOT, "exports")
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
