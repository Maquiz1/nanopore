document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const SequencingDelayed = document.getElementById("id_sequencing_delayed");

    // Field to show/hide
    const sequencingDelayedDays = document.getElementById("id_sequencing_delayed_days");
    const sequencingDelayedReasons = document.getElementById("id_sequencing_delayed_reasons");

    function setDisplay(el, display) {
        if (!el) return;
        const wrapper = el.closest('.col-md-6') || el.closest('.mb-3') || el.parentNode;
        if (wrapper) wrapper.style.display = display;
    }

    // Function to toggle visibility
    function toggleSequencingDelayed() {

        const value = String(SequencingDelayed?.value || "");

        if (value === "1") {
            setDisplay(sequencingDelayedDays, "block");
            setDisplay(sequencingDelayedReasons, "block");
        } else {
            setDisplay(sequencingDelayedDays, "none");
            setDisplay(sequencingDelayedReasons, "none");
        }
    }

    // Initial state on page load
    toggleSequencingDelayed();

    // Update when either result changes
    if (SequencingDelayed) SequencingDelayed.addEventListener("change", toggleSequencingDelayed);
});
