document.addEventListener("DOMContentLoaded", function () {
    const secondLineLpa = document.getElementById("id_second_line_lpa");

    // Sub-fields and drugs panel to show/hide when second_line_lpa = No
    const lpa2SubFields = document.getElementById("lpa2-fields");
    const secondLineDrugs = document.getElementById("second-line-drugs");

    function toggleSecondLineLpa() {
        const value = String(secondLineLpa?.value || "");

        if (value === "1") {
            if (lpa2SubFields) lpa2SubFields.style.display = "block";
            if (secondLineDrugs) secondLineDrugs.style.display = "block";
        } else {
            if (lpa2SubFields) lpa2SubFields.style.display = "none";
            if (secondLineDrugs) secondLineDrugs.style.display = "none";
        }
    }

    toggleSecondLineLpa();
    if (secondLineLpa) secondLineLpa.addEventListener("change", toggleSecondLineLpa);
});
