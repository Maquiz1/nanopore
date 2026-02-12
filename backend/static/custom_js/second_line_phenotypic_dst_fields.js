document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const SecondLineDstPerformed = document.getElementById("id_second_line_dst_performed");

    // Field to show/hide
    const secondLineDstPerformedDate = document.getElementById("second-line-dst-performed-date");
    const secondLineDstResultsDate = document.getElementById("second-line-dst-results-date");

    const phenotypicDstResultsSecondLineHeader = document.getElementById("phenotypic-dst-results-second-line-header");
    const phenotypicDstResultsSecondLine = document.getElementById("phenotypic-dst-results-second-line");

    // Function to toggle visibility
    function toggleSecondLineDstPerformed() {

        const value = String(SecondLineDstPerformed?.value || "");

        if (value === "1") {
            secondLineDstPerformedDate.style.display = "block";
            secondLineDstResultsDate.style.display = "block";

            phenotypicDstResultsSecondLineHeader.style.display = "block";
            phenotypicDstResultsSecondLine.style.display = "block";
        } else {
            secondLineDstPerformedDate.style.display = "none";
            secondLineDstResultsDate.style.display = "none";

            phenotypicDstResultsSecondLineHeader.style.display = "none";
            phenotypicDstResultsSecondLine.style.display = "none";
        }
    }

    // Initial state on page load
    toggleSecondLineDstPerformed();

    // Update when either result changes
    SecondLineDstPerformed.addEventListener("change", toggleSecondLineDstPerformed);
});
