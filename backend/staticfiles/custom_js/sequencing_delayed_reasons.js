document.addEventListener("DOMContentLoaded", function () {
    const SequencingDelayedReasonsCheckboxes = document.querySelectorAll('input[name="sequencing_delayed_reasons"]');


    // Fields to Hide
    const sequencingDelayedOthers = document.getElementById("id_sequencing_delayed_others");

    function toggSequencingDelayedReasonsCheckboxes() {
        const sequencingDelayedOthersChecked = Array.from(SequencingDelayedReasonsCheckboxes).some(cb => cb.checked && cb.value === "7");

        sequencingDelayedOthers.style.display = sequencingDelayedOthersChecked ? "block" : "none";
    }

    toggSequencingDelayedReasonsCheckboxes();
    SequencingDelayedReasonsCheckboxes.forEach(cb => cb.addEventListener("change", toggSequencingDelayedReasonsCheckboxes));
});

