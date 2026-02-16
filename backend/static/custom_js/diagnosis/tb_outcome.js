document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const TbTreatment = document.getElementById("id_tb_treatment");
    const TbTreatmentDate = document.getElementById("id_tb_treatment_date"); // your treatment date field

    // Field to show/hide
    const tbTreatmentOutcomesSections = document.getElementById("tb-treatment-outcomes-sections");

    // Function to toggle visibility
    function toggleTbTreatment() {
        const treatmentValue = String(TbTreatment?.value || "");
        const treatmentDateStr = TbTreatmentDate?.value || "";

        let show = false;
        
        // Only proceed if treatment = 1 and date is not empty
        if (treatmentValue === "1" && treatmentDateStr) {
            const treatmentDate = new Date(treatmentDateStr);
            const now = new Date();

            // Calculate date 6 months ago
            const sixMonthsAgo = new Date();
            sixMonthsAgo.setMonth(now.getMonth() - 6);

            // Show section only if treatment date is at least 6 months ago
            if (!isNaN(treatmentDate.getTime()) && treatmentDate <= sixMonthsAgo) {
                show = true;
            }
        }

        tbTreatmentOutcomesSections.style.display = show ? "block" : "none";
    }

    // Initial state on page load
    toggleTbTreatment();

    // Update when either field changes
    TbTreatment.addEventListener("change", toggleTbTreatment);
    TbTreatmentDate.addEventListener("change", toggleTbTreatment);
});
