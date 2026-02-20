// document.addEventListener("DOMContentLoaded", function () {

//     // ===== Fields =====
//     const TbDiagnosisMadeField = document.getElementById("id_tb_diagnosis_made");
//     const TbDiagnosisField = document.getElementById("id_tb_diagnosis");

//     const clinicalDiagnosisSection = document.getElementById("clinical-diagnosis-section");
//     const bacteriologicalDiagnosisSection = document.getElementById("bacteriological-diagnosis-section");
//     const tbDiagnosisMadeOtherSections = document.getElementById("tb-diagnosis-made-other-sections");
//     const tbDiagnosisMadeSections = document.getElementById("tb-diagnosis-made-sections");

//     // Safety check
//     if (!TbDiagnosisMadeField || !TbDiagnosisField) return;

//     // ===== Helper function to hide all child sections =====
//     function hideAll() {
//         if (clinicalDiagnosisSection) clinicalDiagnosisSection.style.display = "none";
//         if (bacteriologicalDiagnosisSection) bacteriologicalDiagnosisSection.style.display = "none";
//         if (tbDiagnosisMadeOtherSections) tbDiagnosisMadeOtherSections.style.display = "none";
//     }

//     // ===== Main toggle function =====
//     function toggleTbDiagnosisMadeField() {
//         const diagnosisValue = TbDiagnosisField.value || "";
//         const value = TbDiagnosisMadeField.value || "";

//         // Hide everything if TB diagnosis is not 1
//         if (diagnosisValue !== "1") {
//             if (tbDiagnosisMadeSections) tbDiagnosisMadeSections.style.display = "none";
//             hideAll();
//             return;
//         }

//         // Ensure parent container is visible
//         if (tbDiagnosisMadeSections) tbDiagnosisMadeSections.style.display = "block";

//         // Hide all first
//         hideAll();

//         // Show relevant section based on value
//         if (value === "1") {
//             if (clinicalDiagnosisSection) clinicalDiagnosisSection.style.display = "block";
//         } else if (value === "2") {
//             if (bacteriologicalDiagnosisSection) bacteriologicalDiagnosisSection.style.display = "block";
//         } else if (value === "3") {
//             if (tbDiagnosisMadeOtherSections) tbDiagnosisMadeOtherSections.style.display = "block";
//         }
//     }

//     // ===== Initial load =====
//     toggleTbDiagnosisMadeField();

//     // ===== Event listeners =====
//     if (TbDiagnosisMadeField) {
//         TbDiagnosisMadeField.addEventListener("change", toggleTbDiagnosisMadeField);
//     }

//     // Listen for the cross-file custom event
//     document.addEventListener("tbDiagnosisUpdated", toggleTbDiagnosisMadeField);

// });