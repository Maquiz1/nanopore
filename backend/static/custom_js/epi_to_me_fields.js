document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const EpiToMe = document.getElementById("id_epi_to_me");

    // Field to show/hide
    const epiToMeDate = document.getElementById("id_epi_to_me_date");
    const epiToMeVersion = document.getElementById("id_epi_to_me_version");
    const sequencingResults = document.getElementById("id_sequencing_results");

    function setDisplay(el, display) {
        if (!el) return;
        const wrapper = el.closest('.col-md-6') || el.closest('.mb-3') || el.parentNode;
        if (wrapper) wrapper.style.display = display;
    }

    // Function to toggle visibility
    function toggleEpiToMe() {

        const value = String(EpiToMe?.value || "");

        if (value === "1") {
            setDisplay(epiToMeDate, "block");
            setDisplay(epiToMeVersion, "block");
            setDisplay(sequencingResults, "block");
        } else {
            setDisplay(epiToMeDate, "none");
            setDisplay(epiToMeVersion, "none");
            setDisplay(sequencingResults, "none");
        }
    }

    // Initial state on page load
    toggleEpiToMe();

    // Update when either result changes
    if (EpiToMe) EpiToMe.addEventListener("change", toggleEpiToMe);
});
