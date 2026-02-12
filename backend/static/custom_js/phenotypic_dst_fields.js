document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const PhenotypicPerformed = document.getElementById("id_phenotypic_performed");

    // Field to show/hide
    const phenotypicDatePerformed = document.getElementById("phenotypic-date-performed");

    const phenotypicDstResultsHeader = document.getElementById("phenotypic-dst-results-header");
    const phenotypicDateResults = document.getElementById("phenotypic-date-results");
    const phenotypicDstResults = document.getElementById("phenotypic-dst-results");

    const isolateUniqueLabNo = document.getElementById("isolate-unique-lab-no");

    const phenotypicDstResultsFirstLineHeader = document.getElementById("phenotypic-dst-results-first-line-header");
    const firstLineDstPerformedDate = document.getElementById("first-line-dst-performed-date");
    const firstLineDstResultsDate = document.getElementById("first-line-dst-results-date");

    const phenotypicDstResultsSecondLineHeader = document.getElementById("phenotypic-dst-results-second-line-header");
    const secondLineDstPerformedDate = document.getElementById("second-line-dst-performed-date");
    const secondLineDstResultsDate = document.getElementById("second-line-dst-results-date");

    const phenotypicDstResultsOtherHeader = document.getElementById("phenotypic-dst-results-other-header");
    const phenotypicDstResultsOther = document.getElementById("phenotypic-dst-results-other");


    // Function to toggle visibility
    function togglePhenotypicPerformed() {

        const value = String(PhenotypicPerformed?.value || "");

        if (value === "1") {
            phenotypicDstResultsHeader.style.display = "block";
            phenotypicDatePerformed.style.display = "block";
            phenotypicDateResults.style.display = "block";

            phenotypicDstResults.style.display = "block";

            isolateUniqueLabNo.style.display = "block";
            phenotypicDstResultsFirstLineHeader.style.display = "block";
            firstLineDstPerformedDate.style.display = "block";
            firstLineDstResultsDate.style.display = "block";

            phenotypicDstResultsSecondLineHeader.style.display = "block";
            secondLineDstPerformedDate.style.display = "block";
            secondLineDstResultsDate.style.display = "block";

            phenotypicDstResultsOtherHeader.style.display = "block";
            phenotypicDstResultsOther.style.display = "block";
        } else {
            phenotypicDatePerformed.style.display = "none";
            phenotypicDateResults.style.display = "none";
            phenotypicDstResultsHeader.style.display = "none";

            phenotypicDstResults.style.display = "none";

            isolateUniqueLabNo.style.display = "none";
            phenotypicDstResultsFirstLineHeader.style.display = "none";
            firstLineDstPerformedDate.style.display = "none";
            firstLineDstResultsDate.style.display = "none";
            phenotypicDstResultsSecondLineHeader.style.display = "none";
            secondLineDstPerformedDate.style.display = "none";
            secondLineDstResultsDate.style.display = "none";

            phenotypicDstResultsOtherHeader.style.display = "none";
            phenotypicDstResultsOther.style.display = "none";
        }
    }

    // Initial state on page load
    togglePhenotypicPerformed();

    // Update when either result changes
    PhenotypicPerformed.addEventListener("change", togglePhenotypicPerformed);
});
