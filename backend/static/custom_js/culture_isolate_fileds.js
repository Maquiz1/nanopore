document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const CultureIsolate = document.getElementById("id_culture_isolate");

    // Field to show/hide
    const isolateDate = document.getElementById("isolate-date");
    const phenotypicDstHeader = document.getElementById("phenotypic-dst-header");
    const phenotypicPerformed = document.getElementById("phenotypic-performed");

    function toggleCultureIsolate() {
        // const CultureIsolateValue = String(CultureIsolate?.value || "");

        // Show if LJ is 1-4 OR MGIT is 1 - THIS WORKS TOO
        // const show = ["1"].includes(CultureIsolateValue);

        // isolateDate.style.display = show ? "block" : "none";
        // phenotypicDstHeader.style.display = show ? "block" : "none";
        // phenotypicPerformed.style.display = show ? "block" : "none";

        const value = String(CultureIsolate?.value || "");

        if (value === "1") {
            isolateDate.style.display = "block";
            phenotypicDstHeader.style.display = "block";
            phenotypicPerformed.style.display = "block";
        } else {
            isolateDate.style.display = "none";
            phenotypicDstHeader.style.display = "none";
            phenotypicPerformed.style.display = "none";
        }
    }

    // Initial state on page load
    toggleCultureIsolate();

    // Update when either result changes
    CultureIsolate.addEventListener("change", toggleCultureIsolate);
});
