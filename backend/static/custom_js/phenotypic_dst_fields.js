document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const PhenotypicPerformed = document.getElementById("id_phenotypic_performed");

    // Field to show/hide
    const phenotypicDatePerformed = document.getElementById("phenotypic-date-performed");
    const phenotypicDateResults = document.getElementById("phenotypic-date-results");
    const phenotypicDstResultsHeader = document.getElementById("phenotypic-dst-results-header");
    const phenotypicDstResults = document.getElementById("phenotypic-dst-results");

    // Function to toggle visibility
    function togglePhenotypicPerformed() {

        const value = String(PhenotypicPerformed?.value || "");

        if (value === "1") {
            phenotypicDatePerformed.style.display = "block";
            phenotypicDateResults.style.display = "block";
            phenotypicDstResultsHeader.style.display = "block";
            phenotypicDstResults.style.display = "block";
        } else {
            phenotypicDatePerformed.style.display = "none";
            phenotypicDateResults.style.display = "none";
            phenotypicDstResultsHeader.style.display = "none";
            phenotypicDstResults.style.display = "none";
        }
    }

    // Initial state on page load
    togglePhenotypicPerformed();

    // Update when either result changes
    PhenotypicPerformed.addEventListener("change", togglePhenotypicPerformed);
});
