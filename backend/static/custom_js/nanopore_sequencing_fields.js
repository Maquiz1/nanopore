document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const NanoporeDone = document.getElementById("id_nanopore_done");

    // Field to show/hide
    const nanoporeSequencingDate = document.getElementById("id_nanopore_sequencing_date");
    const epiToMe = document.getElementById("id_epi_to_me");
    const nanoporeResults = document.getElementById("id_nanopore_results");
    const sequencingDelayed = document.getElementById("id_sequencing_delayed");

    function setDisplay(el, display) {
        if (!el) return;
        const wrapper = el.closest('.col-md-6') || el.closest('.mb-3') || el.parentNode;
        if (wrapper) wrapper.style.display = display;
    }

    // Function to toggle visibility
    function toggleNanoporeDone() {

        const value = String(NanoporeDone?.value || "");

        if (value === "1") {
            setDisplay(nanoporeSequencingDate, "block");
            setDisplay(epiToMe, "block");
            setDisplay(nanoporeResults, "block");
            setDisplay(sequencingDelayed, "block");
        } else {
            setDisplay(nanoporeSequencingDate, "none");
            setDisplay(epiToMe, "none");
            setDisplay(nanoporeResults, "none");
            setDisplay(sequencingDelayed, "none");
        }
    }

    // Initial state on page load
    toggleNanoporeDone();

    // Update when either result changes
    if (NanoporeDone) NanoporeDone.addEventListener("change", toggleNanoporeDone);
});
