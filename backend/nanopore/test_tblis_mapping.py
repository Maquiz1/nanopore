"""The TBLIS mapping document must describe every field the merge fills (nanopore/tblis_mapping.py)."""
from django.urls import reverse

from nanopore.models import EdcsTblisZonal
from nanopore.tasks_tblis_raw import apply_tblis_transformations
from nanopore.test_access import AccessTestBase
from nanopore.tblis_mapping import FIELD_RULES, build_mapping
from options.models import (
    CultureMethod, INHResultLPA, XpertXDRResults, XpertXDRResultsThree, XpertXDRResultsTwo, YesNo,
)
from utils import access

DATE = "2025-03-01"
# A TBLIS row with every column the merge reads filled in.
FULL_ROW = {
    "labno": "LAB-A1", "rctdate": DATE, "appearance": "Mucoid", "volume": "3",
    "fm_date": DATE, "fm_res": "POSITIVE   1+ AFBs Seen", "zn_date": DATE, "zn_res": "NEGATIVE - No AFBs seen",
    "lj_innocdate": DATE, "lj_date": DATE, "lj_res": "POSITIVE - 3+ Colonies", "id_res": "Mycobacteria tuberculosis complex",
    "mgit_entrydate": DATE, "mgit_date": DATE, "mgit_res": "POSITIVE",
    "ljdst1_date": DATE, "ljdst2_date": DATE, "mgitdst1_date": DATE, "mgitdst2_date": DATE,
    "LJDST1_SETUPDATE": DATE, "LJDST2_SETUPDATE": DATE,
    "ljdst1_rifampicin": "Sensitive", "ljdst1_isoniazid": "Sensitive", "ljdst1_ethambutol": "Sensitive",
    "mgitdst1_rifampicin": "Sensitive", "mgitdst1_isoniazid": "Sensitive", "mgitdst1_ethambutol": "Sensitive",
    **{f"mgitdst2_{d}": "Resistant" for d in (
        "levofloxacin", "bedaquiline", "linezolid", "clofazimine", "cycloserine", "delamanid",
        "ethionamide", "prothionamide", "pas", "pretomanid")},
    "gxxdr_date": DATE,
    **{f"gxxdr_{d}": "Resistance Detected" for d in ("isoniazid", "flq", "amikacin", "kanamycin", "capreomycin", "ethionamide")},
    "lpa1_date": DATE, "lpa1_mtbc": "MTBC Detected", "lpa1_rifampicin": "Sensitive", "lpa1_isoniazid": "Sensitive",
    "lpa2_date": DATE, "lpa2_mtbc": "MTBC Detected", "lpa2_flq": "Sensitive", "lpa2_ag_cp": "Sensitive", "lpa2_low_kan": "Sensitive",
}


class TblisMappingTests(AccessTestBase):
    def setUp(self):
        YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        for pk, name in ((1, "Lj"), (2, "Mgit")):
            CultureMethod.objects.create(pk=pk, value=pk, name=name)
        for pk in range(1, 8):
            INHResultLPA.objects.create(pk=pk, value=pk, name=f"INH {pk}")
        for model, names in ((XpertXDRResults, ["Low Resistance DETECTED", "Resistance DETECTED"]),
                             (XpertXDRResultsTwo, ["Resistance DETECTED"]), (XpertXDRResultsThree, ["Resistance DETECTED"])):
            for pk, name in enumerate(names, start=1):
                model.objects.create(pk=pk, value=pk, name=name)
        self.edcs = EdcsTblisZonal.objects.create(screening=self.screenings["A1"], unique_lab_no="LAB-A1")

    def snapshot(self):
        values = {f.attname: getattr(self.edcs, f.attname) for f in EdcsTblisZonal._meta.concrete_fields}
        for f in EdcsTblisZonal._meta.many_to_many:
            values[f.name] = sorted(getattr(self.edcs, f.name).values_list("pk", flat=True))
        return values

    def test_every_field_the_merge_fills_is_documented(self):
        before = self.snapshot()
        apply_tblis_transformations(self.edcs, dict(FULL_ROW), "LAB-A1")
        after = self.snapshot()
        changed = {name[:-3] if name.endswith("_id") else name for name in after if after[name] != before[name]}
        documented = {rule[0] for rule in FIELD_RULES}
        self.assertTrue(changed, "the merge changed nothing")
        self.assertEqual(changed - documented, set(), "add these fields to FIELD_RULES in nanopore/tblis_mapping.py")

    def test_documented_fields_exist(self):
        names = {f.name for f in EdcsTblisZonal._meta.get_fields()}
        self.assertEqual({rule[0] for rule in FIELD_RULES} - names, set())

    def test_every_field_appears_once(self):
        mapping = build_mapping()
        listed = [row[1] for row in mapping["mapped"]] + [row[1] for row in mapping["not_mapped"]]
        self.assertEqual(len(listed), len(set(listed)))

    def test_downloads_for_edcs_viewers_only(self):
        url = reverse("nanopore:tblis-mapping-download", args=["excel"])
        self.client.force_login(self.make_user("nurse", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.make_user("lab", [access.LABORATORY_TECHNICIAN], sites=[self.alab]))
        self.assertTrue(self.client.get(url).content.startswith(b"PK"))
        pdf = self.client.get(reverse("nanopore:tblis-mapping-download", args=["pdf"]))
        self.assertTrue(pdf.content.startswith(b"%PDF"))
