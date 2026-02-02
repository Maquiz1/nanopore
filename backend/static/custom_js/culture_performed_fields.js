document.addEventListener("DOMContentLoaded", function () {
    const cultureMethodCheckboxes = document.querySelectorAll('input[name="culture_method"]');

    const ljHeader = document.getElementById("lj-header");
    const ljInoculationDate = document.getElementById("lj-inoculation-date");
    const ljResultsDate = document.getElementById("lj-results-date");
    const ljResults = document.getElementById("lj-results");

    const mgitHeader = document.getElementById("mgit-header");
    const mgitInoculationDate = document.getElementById("mgit-inoculation-date");
    const mgitResultsDate = document.getElementById("mgit-results-date");
    const mgitResults = document.getElementById("mgit-results");

    function togglecultureMethod() {
        const ljChecked = Array.from(cultureMethodCheckboxes).some(cb => cb.checked && cb.value === "1");
        const mgitChecked = Array.from(cultureMethodCheckboxes).some(cb => cb.checked && cb.value === "2");

        ljHeader.style.display = ljChecked ? "block" : "none";
        ljInoculationDate.style.display = ljChecked ? "block" : "none";
        ljResultsDate.style.display = ljChecked ? "block" : "none";
        ljResults.style.display = ljChecked ? "block" : "none";

        mgitHeader.style.display = mgitChecked ? "block" : "none";
        mgitInoculationDate.style.display = mgitChecked ? "block" : "none";
        mgitResultsDate.style.display = mgitChecked ? "block" : "none";
        mgitResults.style.display = mgitChecked ? "block" : "none";
    }

    togglecultureMethod();
    cultureMethodCheckboxes.forEach(cb => cb.addEventListener("change", togglecultureMethod));
});
