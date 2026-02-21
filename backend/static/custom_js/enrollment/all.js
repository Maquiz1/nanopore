document.addEventListener("DOMContentLoaded", function () {

    // ===========================
    // Fields
    // ===========================
    const TbDiseasesMedicalCheckboxes = document.querySelectorAll("input[name='diseases_medical']");
    const tbDiseasesSpecifySection = document.getElementById("tb-diseases-specify-section");

    // ===========================
    // Toggle Function
    // ===========================
    function toggleTbDiseasesSpecifySection() {
        const showSection = Array.from(TbDiseasesMedicalCheckboxes)
            .some(cb => cb.value === "11" && cb.checked);

        if (tbDiseasesSpecifySection) {
            tbDiseasesSpecifySection.style.display = showSection ? "block" : "none";
        }
    }

    // ===========================
    // Event Binding
    // ===========================
    TbDiseasesMedicalCheckboxes.forEach(cb =>
        cb.addEventListener("change", toggleTbDiseasesSpecifySection)
    );

    // Initial state on page load
    toggleTbDiseasesSpecifySection();
});