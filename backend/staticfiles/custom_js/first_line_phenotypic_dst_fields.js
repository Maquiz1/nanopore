document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const FirstLineDstPerformed = document.getElementById("id_first_line_dst_performed");

    // Field to show/hide

    // const phenotypicDatePerformed = document.getElementById("phenotypic-date-performed");
    // const phenotypicDateResults = document.getElementById("phenotypic-date-results");

    const firstLineDstPerformedDate = document.getElementById("first-line-dst-performed-date");
    const firstLineDstResultsDate = document.getElementById("first-line-dst-results-date");

    const phenotypicDstResultsFirstLineHeader = document.getElementById("phenotypic-dst-results-first-line-header");
    const phenotypicDstResultsFirstLine = document.getElementById("phenotypic-dst-results-first-line");

    // Function to toggle visibility
    function toggleFirstLineDstPerformed() {

        const value = String(FirstLineDstPerformed?.value || "");

        if (value === "1") {
            // phenotypicDatePerformed.style.display = "block";
            // phenotypicDateResults.style.display = "block";

            firstLineDstPerformedDate.style.display = "block";
            firstLineDstResultsDate.style.display = "block";

            phenotypicDstResultsFirstLineHeader.style.display = "block";
            phenotypicDstResultsFirstLine.style.display = "block";

        } else {

            // phenotypicDatePerformed.style.display = "none";
            // phenotypicDateResults.style.display = "none";

            firstLineDstPerformedDate.style.display = "none";
            firstLineDstResultsDate.style.display = "none";

            phenotypicDstResultsFirstLineHeader.style.display = "none";
            phenotypicDstResultsFirstLine.style.display = "none";

        }
    }

    // Initial state on page load
    toggleFirstLineDstPerformed();

    // Update when either result changes
    FirstLineDstPerformed.addEventListener("change", toggleFirstLineDstPerformed);
});
