// Nanopore section (Zonal Lab, EDCS/TBLIS and CTRL forms): a question and its label show or hide
// together, and a hidden answer hides everything that depends on it. 1 = Yes on every question here.
document.addEventListener("DOMContentLoaded", function () {
    const section = document.querySelector("[data-nano-section]");
    if (!section) return;

    const answer = (name) => section.querySelector(`[name="${name}"]`)?.value || "";
    const isYes = (name) => answer(name) === "1";
    const toggle = (selector, show) => section.querySelectorAll(selector).forEach((el) => { el.hidden = !show; });
    const otherReasonChecked = () => Array.from(section.querySelectorAll('input[name="sequencing_delayed_reasons"]'))
        .some((box) => box.checked && /^\s*other/i.test(box.closest("label")?.textContent || ""));

    function refresh() {
        const done = isYes("nanopore_done");
        const epi = done && isYes("epi_to_me");
        const delayed = done && isYes("sequencing_delayed");

        toggle('[data-nano-when="done"]', done);
        toggle('[data-nano-when="epi"]', epi);
        toggle('[data-nano-when="results"]', done && isYes("nanopore_results"));
        toggle('[data-nano-when="delayed"]', delayed);
        toggle('[data-nano-when="other-reason"]', delayed && otherReasonChecked());
    }

    section.addEventListener("change", refresh);
    refresh();
});
