document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const TbDiagnosisMadeField = document.getElementById("id_tb_diagnosis_made");

    // Field to show/hide
    const clinicalDiagnosisSection = document.getElementById("clinical-diagnosis-section");
    const bacteriologicalDiagnosisSection = document.getElementById("bacteriological-diagnosis-section");
    const tbDiagnosisMadeOtherSections = document.getElementById("tb-diagnosis-made-other-sections");

    function toggleTbDiagnosisMadeField() {
        // const TbDiagnosisMadeFieldValue = String(TbDiagnosisMadeField?.value || "");

        // Show if LJ is 1-4 OR MGIT is 1 - THIS WORKS TOO
        // const show = ["1"].includes(TbDiagnosisMadeFieldValue);

        // clinicalDiagnosisSection.style.display = show ? "block" : "none";
        // bacteriologicalDiagnosisSection.style.display = show ? "block" : "none";
        // tbDiagnosisMadeOtherSections.style.display = show ? "block" : "none";

        const value = String(TbDiagnosisMadeField?.value || "");

        if (value === "1") {
            clinicalDiagnosisSection.style.display = "block";
            bacteriologicalDiagnosisSection.style.display = "none";
            tbDiagnosisMadeOtherSections.style.display = "none";
        }else if (value === "2") {
            clinicalDiagnosisSection.style.display = "none";
            bacteriologicalDiagnosisSection.style.display = "block";
            tbDiagnosisMadeOtherSections.style.display = "none";
        }else if (value === "3") {  // Other
            clinicalDiagnosisSection.style.display = "none";
            bacteriologicalDiagnosisSection.style.display = "none";
            tbDiagnosisMadeOtherSections.style.display = "block";
        } else {
            clinicalDiagnosisSection.style.display = "none";
            bacteriologicalDiagnosisSection.style.display = "none";
            tbDiagnosisMadeOtherSections.style.display = "none";
        }
    }

    // Initial state on page load
    toggleTbDiagnosisMadeField();

    // Update when either result changes
    TbDiagnosisMadeField.addEventListener("change", toggleTbDiagnosisMadeField);
});
