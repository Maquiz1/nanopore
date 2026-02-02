document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const NanoporeDone = document.getElementById("id_nanopore_done");

    // Field to show/hide
    const nanoporeSequencingDate = document.getElementById("id_nanopore_sequencing_date");
    const epiToMe = document.getElementById("id_epi_to_me");
    const nanoporeResults = document.getElementById("id_nanopore_results");
    const sequencingDelayed = document.getElementById("id_sequencing_delayed");

    // Function to toggle visibility
    function toggleNanoporeDone() {

        const value = String(NanoporeDone?.value || "");

        if (value === "1") {
            nanoporeSequencingDate.style.display = "block";
            epiToMe.style.display = "block";
            nanoporeResults.style.display = "block";
            sequencingDelayed.style.display = "block";
        } else {
            nanoporeSequencingDate.style.display = "none";
            epiToMe.style.display = "none";
            nanoporeResults.style.display = "none";
            sequencingDelayed.style.display = "none";
        }
    }

    // Initial state on page load
    toggleNanoporeDone();

    // Update when either result changes
    NanoporeDone.addEventListener("change", toggleNanoporeDone);
});
