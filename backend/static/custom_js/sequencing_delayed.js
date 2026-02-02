document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const SequencingDelayed = document.getElementById("id_sequencing_delayed");

    // Field to show/hide
    const sequencingDelayedDays = document.getElementById("id_sequencing_delayed_days");
    const sequencingDelayedReasons = document.getElementById("id_sequencing_delayed_reasons");

    // Function to toggle visibility
    function toggleSequencingDelayed() {

        const value = String(SequencingDelayed?.value || "");

        if (value === "1") {
            sequencingDelayedDays.style.display = "block";
            sequencingDelayedReasons.style.display = "block";
        } else {
            sequencingDelayedDays.style.display = "none";
            sequencingDelayedReasons.style.display = "none";
        }
    }

    // Initial state on page load
    toggleSequencingDelayed();

    // Update when either result changes
    SequencingDelayed.addEventListener("change", toggleSequencingDelayed);
});
