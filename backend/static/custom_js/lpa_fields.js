document.addEventListener("DOMContentLoaded", function () {
    const lpaField = document.getElementById("id_lpa");

    const lpa1Header = document.getElementById("lpa1-header");
    const lpa1Section = document.getElementById("lpa1-section");
    const lpa2Header = document.getElementById("lpa2-header");
    const lpa2Section = document.getElementById("lpa2-section");

    function toggleLpa() {
        const value = String(lpaField?.value || "");

        if (value === "1") {
            if (lpa1Header) lpa1Header.style.display = "block";
            if (lpa1Section) lpa1Section.style.display = "flex";
            if (lpa2Header) lpa2Header.style.display = "block";
            if (lpa2Section) lpa2Section.style.display = "flex";
        } else {
            if (lpa1Header) lpa1Header.style.display = "none";
            if (lpa1Section) lpa1Section.style.display = "none";
            if (lpa2Header) lpa2Header.style.display = "none";
            if (lpa2Section) lpa2Section.style.display = "none";
        }
    }

    toggleLpa();
    if (lpaField) lpaField.addEventListener("change", toggleLpa);
});
