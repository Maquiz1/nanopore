document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const PhenotypicPerformed = document.getElementById("id_phenotypic_performed");

    // Field to show/hide
    const isolateUniqueLabNo = document.getElementById("isolate-unique-lab-no");

    // const phenotypicDatePerformed = document.getElementById("phenotypic-date-performed");
    // const phenotypicDateResults = document.getElementById("phenotypic-date-results");

    const phenotypicDstFirstLineHeader = document.getElementById("phenotypic-dst-first-line-header");
    const firstLineDstPerformed = document.getElementById("first-line-dst-performed");

    // Function to toggle visibility
    function togglePhenotypicPerformed() {

        const value = String(PhenotypicPerformed?.value || "");

        if (value === "1") {
            isolateUniqueLabNo.style.display = "block";

            // phenotypicDatePerformed.style.display = "block";
            // phenotypicDateResults.style.display = "block";

            phenotypicDstFirstLineHeader.style.display = "block";
            firstLineDstPerformed.style.display = "block";

        } else {
            isolateUniqueLabNo.style.display = "none";

            // phenotypicDatePerformed.style.display = "none";
            // phenotypicDateResults.style.display = "none";

            phenotypicDstFirstLineHeader.style.display = "none";
            firstLineDstPerformed.style.display = "none";
        }
    }

    // Initial state on page load
    togglePhenotypicPerformed();

    // Update when either result changes
    PhenotypicPerformed.addEventListener("change", togglePhenotypicPerformed);
});
