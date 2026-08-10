document.addEventListener("DOMContentLoaded", function () {
    const firstLineLpa = document.getElementById("id_first_line_lpa");

    // Sub-fields and drugs panel to show/hide when first_line_lpa = No
    const lpa1SubFields = document.getElementById("lpa1-fields");
    const firstLineDrugs = document.getElementById("first-line-drugs");

    function toggleFirstLineLpa() {
        const value = String(firstLineLpa?.value || "");

        if (value === "1") {
            if (lpa1SubFields) lpa1SubFields.style.display = "block";
            if (firstLineDrugs) firstLineDrugs.style.display = "block";
        } else {
            if (lpa1SubFields) lpa1SubFields.style.display = "none";
            if (firstLineDrugs) firstLineDrugs.style.display = "none";
        }
    }

    toggleFirstLineLpa();
    if (firstLineLpa) firstLineLpa.addEventListener("change", toggleFirstLineLpa);
});
