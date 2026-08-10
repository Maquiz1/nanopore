document.addEventListener("DOMContentLoaded", function () {
    const SequencingDelayedReasonsCheckboxes = document.querySelectorAll('input[name="sequencing_delayed_reasons"]');

    // Fields to Hide
    const sequencingDelayedOthers = document.getElementById("id_sequencing_delayed_others");

    function setDisplay(el, display) {
        if (!el) return;
        const wrapper = el.closest('.col-md-6') || el.closest('.mb-3') || el.parentNode;
        if (wrapper) wrapper.style.display = display;
    }

    function toggSequencingDelayedReasonsCheckboxes() {
        const sequencingDelayedOthersChecked = Array.from(SequencingDelayedReasonsCheckboxes).some(cb => cb.checked && cb.value === "7");
        
        setDisplay(sequencingDelayedOthers, sequencingDelayedOthersChecked ? "block" : "none");
    }

    toggSequencingDelayedReasonsCheckboxes();
    SequencingDelayedReasonsCheckboxes.forEach(cb => cb.addEventListener("change", toggSequencingDelayedReasonsCheckboxes));
});
