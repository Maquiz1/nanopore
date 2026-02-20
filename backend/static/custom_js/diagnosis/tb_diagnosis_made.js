document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const TbDiagnosisMadeField = document.getElementById("id_tb_diagnosis_made");
    const TbDiagnosisField = document.getElementById("id_tb_diagnosis");

    // Field to show/hide
    const clinicalDiagnosisSection = document.getElementById("clinical-diagnosis-section");
    const bacteriologicalDiagnosisSection = document.getElementById("bacteriological-diagnosis-section");
    const tbDiagnosisMadeOtherSections = document.getElementById("tb-diagnosis-made-other-sections");

    // function toggleTbDiagnosisMadeField() {
    //     // const TbDiagnosisMadeFieldValue = String(TbDiagnosisMadeField?.value || "");

    //     const value = String(TbDiagnosisMadeField?.value || "");

    //     if (value === "1") {
    //         clinicalDiagnosisSection.style.display = "block";
    //         bacteriologicalDiagnosisSection.style.display = "none";
    //         tbDiagnosisMadeOtherSections.style.display = "none";
    //     }else if (value === "2") {
    //         clinicalDiagnosisSection.style.display = "none";
    //         bacteriologicalDiagnosisSection.style.display = "block";
    //         tbDiagnosisMadeOtherSections.style.display = "none";
    //     }else if (value === "3") {  // Other
    //         clinicalDiagnosisSection.style.display = "none";
    //         bacteriologicalDiagnosisSection.style.display = "none";
    //         tbDiagnosisMadeOtherSections.style.display = "block";
    //     } else {
    //         clinicalDiagnosisSection.style.display = "none";
    //         bacteriologicalDiagnosisSection.style.display = "none";
    //         tbDiagnosisMadeOtherSections.style.display = "none";
    //     }
    // }

    function toggleTbDiagnosisMadeField() {
        const diagnosisValue = tbDiagnosisField?.value || "";
        const value = String(TbDiagnosisMadeField?.value || "");

        // If TB diagnosis is not 1, hide everything
        if (diagnosisValue !== "1") {
            clinicalDiagnosisSection.style.display = "none";
            bacteriologicalDiagnosisSection.style.display = "none";
            tbDiagnosisMadeOtherSections.style.display = "none";
            return;
        }

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

    if (TbDiagnosisField) {
        TbDiagnosisField.addEventListener("change", toggleTbDiagnosisMadeField);
    }
    // Initial state on page load
    toggleTbDiagnosisMadeField();

    // Update when either result changes
    TbDiagnosisMadeField.addEventListener("change", toggleTbDiagnosisMadeField);
});
