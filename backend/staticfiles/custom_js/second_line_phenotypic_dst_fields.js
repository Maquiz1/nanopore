document.addEventListener("DOMContentLoaded", function () {

    const SecondLineDstPerformed = document.getElementById("id_second_line_dst_performed");

    const secondLineDstPerformedDate = document.getElementById("second-line-dst-performed-date");
    const secondLineDstResultsDate = document.getElementById("second-line-dst-results-date");

    const phenotypicDstResultsSecondLineHeader = document.getElementById("phenotypic-dst-results-second-line-header");
    const phenotypicDstResultsSecondLine = document.getElementById("phenotypic-dst-results-second-line");

    function toggleSecondLineDstPerformed() {

        const isPerformed = SecondLineDstPerformed?.value == "1";

        [
            secondLineDstPerformedDate,
            secondLineDstResultsDate,
            phenotypicDstResultsSecondLineHeader,
            phenotypicDstResultsSecondLine
        ].forEach(el => {
            if (el) el.style.display = isPerformed ? "block" : "none";
        });
    }

    // Initial state
    toggleSecondLineDstPerformed();

    // Listener
    SecondLineDstPerformed?.addEventListener("change", toggleSecondLineDstPerformed);
});
