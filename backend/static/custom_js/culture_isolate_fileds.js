document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const CultureIsolate = document.getElementById("id_culture_isolate");

    // Field to show/hide
    const IsolateDate = document.getElementById("isolate-date");

    function toggleCultureIsolate() {
        const CultureIsolateValue = String(CultureIsolate?.value || "");

        // Show if LJ is 1-4 OR MGIT is 1
        const show = ["1"].includes(CultureIsolateValue);

        IsolateDate.style.display = show ? "block" : "none";
    }

    // Initial state on page load
    toggleCultureIsolate();

    // Update when either result changes
    CultureIsolate.addEventListener("change", toggleCultureIsolate);
});
