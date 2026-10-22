"""TBLIS -> EDCS/TBLIS mapping rules (nanopore/tasks_tblis_raw.py)."""
from nanopore.models import EdcsTblisZonal
from nanopore.tasks_tblis_raw import apply_tblis_transformations
from nanopore.test_access import AccessTestBase
from options.models import MicroscopyType, YesNo


class MicroscopyTypeTests(AccessTestBase):
    def setUp(self):
        MicroscopyType.objects.create(pk=1, value=1, name="Direct sputum")
        MicroscopyType.objects.create(pk=2, value=2, name="Decontaminated sputum")
        self.edcs = EdcsTblisZonal.objects.create(screening=self.screenings["A1"], unique_lab_no="LAB-A1")

    def merge(self, **row):
        apply_tblis_transformations(self.edcs, row, "LAB-A1")
        return self.edcs.microscopy_type_id

    def test_fm_microscopy_is_direct_sputum(self):
        self.assertEqual(self.merge(fm_date="2025-03-01", fm_res="POSITIVE   1+ AFBs Seen"), 1)

    def test_zn_microscopy_is_direct_sputum(self):
        self.assertEqual(self.merge(zn_res="NEGATIVE - No AFBs seen"), 1)

    def test_no_microscopy_leaves_type_unchanged(self):
        self.assertIsNone(self.merge(rctdate="2025-03-01"))


class XpertXdrTests(AccessTestBase):
    """Option tables as in the live database: in Two/Three the pk differs from the value."""

    def setUp(self):
        from options.models import XpertXDRResults, XpertXDRResultsThree, XpertXDRResultsTwo
        for pk, value, name in [(1, 1, "Low Resistance DETECTED"), (2, 2, "Resistance DETECTED"),
                                (3, 3, "Resistance NOT DETECTED"), (4, 4, "Resistance INDETERMINATE")]:
            XpertXDRResults.objects.create(pk=pk, value=value, name=name)
        for pk, value, name in [(1, 2, "Resistance DETECTED"), (2, 3, "Resistance NOT DETECTED")]:
            XpertXDRResultsTwo.objects.create(pk=pk, value=value, name=name)
        for pk, value, name in [(1, 2, "Resistance DETECTED"), (2, 3, "Resistance NOT DETECTED"),
                                (3, 4, "Resistance INDETERMINATE")]:
            XpertXDRResultsThree.objects.create(pk=pk, value=value, name=name)
        self.edcs = EdcsTblisZonal.objects.create(screening=self.screenings["A1"], unique_lab_no="LAB-A1")

    def merge(self, **row):
        apply_tblis_transformations(self.edcs, row, "LAB-A1")
        return self.edcs

    def test_results_are_stored_by_name(self):
        edcs = self.merge(
            gxxdr_isoniazid="Resistance Detected",
            gxxdr_flq="Resistance not Detected",
            gxxdr_amikacin="Resistance not Detected",
            gxxdr_kanamycin="Indeterminate",
            gxxdr_ethionamide="Resistance Detected",
        )
        self.assertEqual(edcs.xpert_xdr_isoniazid.name, "Resistance DETECTED")
        self.assertEqual(edcs.xpert_xdr_fluoroquinolones.name, "Resistance NOT DETECTED")
        self.assertEqual(edcs.xpert_xdr_amikacin.name, "Resistance NOT DETECTED")
        self.assertEqual(edcs.xpert_xdr_kanamycin.name, "Resistance INDETERMINATE")
        self.assertEqual(edcs.xpert_xdr_ethionamide.name, "Resistance DETECTED")

    def test_results_without_an_option_stay_empty(self):
        edcs = self.merge(gxxdr_ethionamide="Indeterminate", gxxdr_capreomycin="MTB Not Detected")
        self.assertIsNone(edcs.xpert_xdr_ethionamide_id)
        self.assertIsNone(edcs.xpert_xdr_capreomycin_id)


class PhenotypicDstTests(AccessTestBase):
    def setUp(self):
        from options.models import PhenotypicDSTResults
        for pk, name in enumerate(["Resistant", "Susceptible", "Contaminated", "Invalid", "Not Done"], start=1):
            PhenotypicDSTResults.objects.create(pk=pk, value=pk, name=name)
        self.edcs = EdcsTblisZonal.objects.create(screening=self.screenings["A1"], unique_lab_no="LAB-A1")

    def merge(self, **row):
        apply_tblis_transformations(self.edcs, row, "LAB-A1")
        return self.edcs

    def test_indeterminate_is_invalid(self):
        edcs = self.merge(ljdst1_rifampicin="Resistance Indeterminate", mgitdst2_levofloxacin="Indeterminate")
        self.assertEqual(edcs.rifampicin.name, "Invalid")
        self.assertEqual(edcs.levofloxacin.name, "Invalid")

    def test_mtb_not_detected_is_not_done(self):
        self.assertEqual(self.merge(mgitdst2_linezolid="MTB Not Detected").linezolid.name, "Not Done")

    def test_lj_not_detected_falls_back_to_mgit(self):
        edcs = self.merge(ljdst1_isoniazid="MTB Not Detected", mgitdst1_isoniazid="Resistant")
        self.assertEqual(edcs.isoniazid.name, "Resistant")


class CultureMethodTests(AccessTestBase):
    def setUp(self):
        from options.models import CultureMethod
        CultureMethod.objects.create(pk=1, value=1, name="Lj")
        CultureMethod.objects.create(pk=2, value=2, name="Mgit")
        YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        self.edcs = EdcsTblisZonal.objects.create(screening=self.screenings["A1"], unique_lab_no="LAB-A1")

    def methods(self, **row):
        apply_tblis_transformations(self.edcs, row, "LAB-A1")
        return list(self.edcs.culture_method.values_list("name", flat=True))

    def test_both_ticked_when_both_done(self):
        self.assertEqual(sorted(self.methods(lj_innocdate="2025-03-01", mgit_entrydate="2025-03-02")), ["Lj", "Mgit"])

    def test_mgit_only(self):
        self.assertEqual(self.methods(mgit_entrydate="2025-03-02"), ["Mgit"])


class CultureResultTests(AccessTestBase):
    def setUp(self):
        from options.models import LJCultureResult, MGITCultureResult
        for pk, name in enumerate(["Scanty", "1+", "2+", "3+", "Negative", "Contamination", "MOTT"], start=1):
            LJCultureResult.objects.create(pk=pk, value=pk, name=name)
        for pk, name in enumerate(["Positive", "Negative", "Contamination", "MOTT"], start=1):
            MGITCultureResult.objects.create(pk=pk, value=pk, name=name)
        YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        self.edcs = EdcsTblisZonal.objects.create(screening=self.screenings["A1"], unique_lab_no="LAB-A1")

    def merge(self, **row):
        apply_tblis_transformations(self.edcs, row, "LAB-A1")
        return self.edcs

    def test_mgit_text_rules(self):
        cases = {
            "POSITIVE - 3 Colonies": "Positive",
            "POSITIVE": "Positive",
            "NEGATIVE": "Negative",
            "CONTAMINATED": "Contamination",
            "Contaminated": "Contamination",
            "POSITIVE FOR NTM": "MOTT",
        }
        for text, expected in cases.items():
            self.edcs.mgit_results = None
            self.assertEqual(self.merge(mgit_res=text).mgit_results.name, expected, text)

    def test_mott_identification_overrides_lj_and_mgit(self):
        edcs = self.merge(
            lj_res="POSITIVE - 3+ Colonies", mgit_res="POSITIVE",
            id_res="Mycobacteria other than M.tuberculosis",
        )
        self.assertEqual(edcs.lj_results.name, "MOTT")
        self.assertEqual(edcs.mgit_results.name, "MOTT")

    def test_negative_identification_is_not_mott(self):
        edcs = self.merge(lj_res="NEGATIVE", mgit_res="NEGATIVE", id_res="Negative")
        self.assertEqual(edcs.lj_results.name, "Negative")
        self.assertEqual(edcs.mgit_results.name, "Negative")

    def test_mott_only_applies_to_cultures_that_were_done(self):
        edcs = self.merge(lj_res="POSITIVE - 3+ Colonies", id_res="Mycobacteria other than M.tuberculosis")
        self.assertEqual(edcs.lj_results.name, "MOTT")
        self.assertIsNone(edcs.mgit_results_id)  # no MGIT culture in this row


class DstDateTests(AccessTestBase):
    def setUp(self):
        YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        self.edcs = EdcsTblisZonal.objects.create(screening=self.screenings["A1"], unique_lab_no="LAB-A1")

    def merge(self, **row):
        apply_tblis_transformations(self.edcs, row, "LAB-A1")
        return self.edcs

    def test_performed_date_is_lj_setup_date(self):
        edcs = self.merge(LJDST1_SETUPDATE="2025-04-24", ljdst1_entrydate="2025-06-04", ljdst1_date="2025-06-03",
                          LJDST2_SETUPDATE="2025-05-01", ljdst2_date="2025-07-01")
        self.assertEqual(str(edcs.first_line_dst_performed_date), "2025-04-24")
        self.assertEqual(str(edcs.second_line_dst_performed_date), "2025-05-01")
        self.assertEqual(edcs.first_line_dst_performed_id, 1)
        self.assertEqual(edcs.second_line_dst_performed_id, 1)

    def test_mgit_only_dst_is_performed_without_a_date(self):
        edcs = self.merge(mgitdst1_date="2025-03-13")
        self.assertEqual(edcs.first_line_dst_performed_id, 1)
        self.assertIsNone(edcs.first_line_dst_performed_date)
        self.assertEqual(str(edcs.first_line_dst_results_date), "2025-03-13")

    def test_results_date_prefers_lj_like_the_results(self):
        edcs = self.merge(ljdst1_date="2025-06-03", mgitdst1_date="2025-03-13")
        self.assertEqual(str(edcs.first_line_dst_results_date), "2025-06-03")

    def test_no_dst_is_not_performed(self):
        edcs = self.merge(rctdate="2025-01-01")
        self.assertEqual(edcs.first_line_dst_performed_id, 2)
        self.assertEqual(edcs.second_line_dst_performed_id, 2)


class LjScantyRuleTests(AccessTestBase):
    def setUp(self):
        from options.models import LJCultureResult
        for pk, name in enumerate(["Scanty", "1+", "2+", "3+", "Negative", "Contamination", "MOTT"], start=1):
            LJCultureResult.objects.create(pk=pk, value=pk, name=name)
        YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        self.edcs = EdcsTblisZonal.objects.create(screening=self.screenings["A1"], unique_lab_no="LAB-A1")

    def lj(self, text):
        self.edcs.lj_results = None
        apply_tblis_transformations(self.edcs, {"lj_res": text}, "LAB-A1")
        return self.edcs.lj_results.name if self.edcs.lj_results_id else None

    def test_known_texts_unchanged(self):
        self.assertEqual(self.lj("POSITIVE - 3+ Colonies"), "3+")
        self.assertEqual(self.lj("POSITIVE - 7 Colonies"), "Scanty")
        self.assertEqual(self.lj("NEGATIVE"), "Negative")

    def test_unknown_positive_without_plus_is_scanty(self):
        self.assertEqual(self.lj("POSITIVE - 60 Colonies"), "Scanty")

    def test_unknown_other_text_is_reported(self):
        from nanopore.models import EdcsTblisMismatch
        self.assertIsNone(self.lj("POSITIVE 5+ something new"))
        self.assertTrue(EdcsTblisMismatch.objects.filter(field_name__startswith="lj_results (unrecognised").exists())


class MicroscopyZeroTests(AccessTestBase):
    def setUp(self):
        from options.models import CultureMicroscopyResults
        CultureMicroscopyResults.objects.create(pk=1, value=1, name="negative")
        MicroscopyType.objects.create(pk=1, value=1, name="Direct sputum")
        YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        self.edcs = EdcsTblisZonal.objects.create(screening=self.screenings["A1"], unique_lab_no="LAB-A1")

    def test_zero_is_not_stored_and_flagged(self):
        from nanopore.models import EdcsTblisMismatch
        apply_tblis_transformations(self.edcs, {"fm_date": "2025-03-01", "fm_res": "0"}, "LAB-A1")
        self.assertIsNone(self.edcs.microscopy_results_id)
        self.assertTrue(EdcsTblisMismatch.objects.filter(field_name__contains="needs quality check", tblis_value="0").exists())

    def test_normal_result_still_stored(self):
        apply_tblis_transformations(self.edcs, {"fm_res": "NEGATIVE - No AFBs seen"}, "LAB-A1")
        self.assertEqual(self.edcs.microscopy_results_id, 1)


class LpaConductedTests(AccessTestBase):
    def setUp(self):
        YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        self.edcs = EdcsTblisZonal.objects.create(screening=self.screenings["A1"], unique_lab_no="LAB-A1")

    def merge(self, **row):
        apply_tblis_transformations(self.edcs, row, "LAB-A1")
        return self.edcs

    def test_first_and_second_line_done(self):
        edcs = self.merge(lpa1_date="2025-02-14", lpa2_date="2025-02-19")
        self.assertEqual((edcs.lpa_id, edcs.first_line_lpa_id, edcs.second_line_lpa_id), (1, 1, 1))
        self.assertEqual(str(edcs.first_line_lpa_date), "2025-02-14")
        self.assertEqual(str(edcs.second_line_lpa_date), "2025-02-19")

    def test_first_line_only(self):
        edcs = self.merge(lpa1_mtbc="MTBC Not Detected")
        self.assertEqual((edcs.lpa_id, edcs.first_line_lpa_id, edcs.second_line_lpa_id), (1, 1, 2))

    def test_no_lpa_is_no(self):
        edcs = self.merge(rctdate="2025-01-01")
        self.assertEqual((edcs.lpa_id, edcs.first_line_lpa_id, edcs.second_line_lpa_id), (2, 2, 2))
        self.assertIsNone(edcs.first_line_lpa_date)


class XpertXdrPerformedTests(AccessTestBase):
    def setUp(self):
        YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        self.edcs = EdcsTblisZonal.objects.create(screening=self.screenings["A1"], unique_lab_no="LAB-A1")

    def test_yes_with_date(self):
        apply_tblis_transformations(self.edcs, {"gxxdr_date": "2025-05-01"}, "LAB-A1")
        self.assertEqual(self.edcs.xpert_xdr_performed_id, 1)
        self.assertEqual(str(self.edcs.xpert_xdr_date_performed), "2025-05-01")

    def test_no_without_date(self):
        apply_tblis_transformations(self.edcs, {"rctdate": "2025-01-01"}, "LAB-A1")
        self.assertEqual(self.edcs.xpert_xdr_performed_id, 2)
