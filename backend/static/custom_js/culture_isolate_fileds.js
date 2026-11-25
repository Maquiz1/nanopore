document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const CultureIsolate = document.getElementById("id_culture_isolate");

    // Field to show/hide
    const isolateDate = document.getElementById("isolate-date");
    const isolateUniqueLabNo = document.getElementById("isolate-unique-lab-no");
    const phenotypicDstHeader = document.getElementById("phenotypic-dst-header");
    const phenotypicPerformed = document.getElementById("phenotypic-performed");

    function toggleCultureIsolate() {
        const value = String(CultureIsolate?.value || "");
        // Dar es Salaam (CTRL): question 11 is Na and DST is asked for every positive culture,
        // i.e. whenever question 11 itself is showing (data dictionary D08)
        const isolateBox = document.getElementById("culture-isolate");
        const dstWithoutIsolate = isolateBox?.dataset.dstWithoutIsolate === "1" && isolateBox.style.display !== "none";

        if (dstWithoutIsolate) {
            isolateDate.style.display = "none";
            isolateUniqueLabNo.style.display = "none";
            phenotypicDstHeader.style.display = "block";
            phenotypicPerformed.style.display = "block";
        } else if (value === "1") {
            isolateDate.style.display = "block";
            isolateUniqueLabNo.style.display = "block";
            phenotypicDstHeader.style.display = "block";
            phenotypicPerformed.style.display = "block";
        } else {
            isolateDate.style.display = "none";
            isolateUniqueLabNo.style.display = "none";
            phenotypicDstHeader.style.display = "none";
            phenotypicPerformed.style.display = "none";
        }
    }

    // Initial state on page load
    toggleCultureIsolate();

    // Update when either result changes
    CultureIsolate.addEventListener("change", toggleCultureIsolate);
});
