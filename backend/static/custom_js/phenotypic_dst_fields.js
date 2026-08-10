document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const PhenotypicPerformed = document.getElementById("id_phenotypic_performed");

    // Field to show/hide
    const phenotypicDstFirstLineHeader = document.getElementById("phenotypic-dst-first-line-header");
    const firstLineDstPerformed = document.getElementById("first-line-dst-performed");

    // Function to toggle visibility
    function togglePhenotypicPerformed() {

        const value = String(PhenotypicPerformed?.value || "");

        if (value === "1") {
            phenotypicDstFirstLineHeader.style.display = "block";
            firstLineDstPerformed.style.display = "block";
        } else {
            phenotypicDstFirstLineHeader.style.display = "none";
            firstLineDstPerformed.style.display = "none";
        }
    }

    // Initial state on page load
    togglePhenotypicPerformed();

    // Update when either result changes
    PhenotypicPerformed.addEventListener("change", togglePhenotypicPerformed);
});
