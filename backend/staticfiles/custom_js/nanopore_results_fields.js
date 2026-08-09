document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const NanoporeResults = document.getElementById("id_nanopore_results");

    // Field to show/hide
    const nanoporeSequencingResults = document.getElementById("nanopore-sequencing-results");

    // Function to toggle visibility
    function toggleNanoporeResults() {

        const value = String(NanoporeResults?.value || "");

        if (value === "1") {
            nanoporeSequencingResults.style.display = "block";
        } else {
            nanoporeSequencingResults.style.display = "none";
        }
    }

    // Initial state on page load
    toggleNanoporeResults();

    // Update when either result changes
    NanoporeResults.addEventListener("change", toggleNanoporeResults);
});
