document.addEventListener("DOMContentLoaded", function () {

    // ===== Fields =====
    const TbDiagnosisMadeField = document.getElementById("id_tb_diagnosis_made");
    const TbDiagnosisField = document.getElementById("id_tb_diagnosis");

    // ===== Sections =====
    const clinicalDiagnosisSection = document.getElementById("clinical-diagnosis-section");
    const bacteriologicalDiagnosisSection = document.getElementById("bacteriological-diagnosis-section");
    const tbDiagnosisMadeOtherSections = document.getElementById("tb-diagnosis-made-other-sections");

    // ===== Safety check (avoid JS errors if elements missing) =====
    if (!TbDiagnosisMadeField || !TbDiagnosisField) return;

    function toggleTbDiagnosisMadeField() {

        const diagnosisValue = String(TbDiagnosisField.value || "");
        const value = String(TbDiagnosisMadeField.value || "");

        // If TB Diagnosis is NOT "1", hide everything
        if (diagnosisValue !== "1") {
            clinicalDiagnosisSection.style.display = "none";
            bacteriologicalDiagnosisSection.style.display = "none";
            tbDiagnosisMadeOtherSections.style.display = "none";
            return;
        }

        // Otherwise toggle based on Diagnosis Made
        if (value === "1") {
            clinicalDiagnosisSection.style.display = "block";
            bacteriologicalDiagnosisSection.style.display = "none";
            tbDiagnosisMadeOtherSections.style.display = "none";

        } else if (value === "2") {
            clinicalDiagnosisSection.style.display = "none";
            bacteriologicalDiagnosisSection.style.display = "block";
            tbDiagnosisMadeOtherSections.style.display = "none";

        } else if (value === "3") {
            clinicalDiagnosisSection.style.display = "none";
            bacteriologicalDiagnosisSection.style.display = "none";
            tbDiagnosisMadeOtherSections.style.display = "block";

        } else {
            clinicalDiagnosisSection.style.display = "none";
            bacteriologicalDiagnosisSection.style.display = "none";
            tbDiagnosisMadeOtherSections.style.display = "none";
        }
    }

    // ===== Run on page load =====
    toggleTbDiagnosisMadeField();

    // ===== Re-run when either field changes =====
    TbDiagnosisMadeField.addEventListener("change", toggleTbDiagnosisMadeField);
    TbDiagnosisField.addEventListener("change", toggleTbDiagnosisMadeField);

});