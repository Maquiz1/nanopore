document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const SecondLineLpa = document.getElementById("id_second_line_lpa");

    // Field to show/hide
    const secondLineLpaDate = document.getElementById("id_second_line_lpa_date");
    const lpa1Mtb = document.getElementById("id_lpa1_mtb");
    const lpa1Rif = document.getElementById("id_lpa2_rfluoroquinolones");
    const lpa2Aminoglycosides = document.getElementById("id_lpa2_aminoglycosides");
    const lpa2Kanamycin = document.getElementById("idlpa2_kanamycin");
    const secondLineDrugs = document.getElementById("second-line-drugs");

    // Function to toggle visibility
    function toggleSecondLineLpa() {

        const value = String(SecondLineLpa?.value || "");

        if (value === "1") {
            secondLineLpaDate.style.display = "block";
            lpa1Mtb.style.display = "block";
            lpa1Rif.style.display = "block";
            lpa2Aminoglycosides.style.display = "block";
            lpa2Kanamycin.style.display = "block";
            secondLineDrugs.style.display = "block";
        } else {
            secondLineLpaDate.style.display = "none";
            lpa1Mtb.style.display = "none";
            lpa1Rif.style.display = "none";
            lpa2Aminoglycosides.style.display = "none";
            lpa2Kanamycin.style.display = "none";
            secondLineDrugs.style.display = "none";
        }
    }

    // Initial state on page load
    toggleSecondLineLpa();

    // Update when either result changes
    SecondLineLpa.addEventListener("change", toggleSecondLineLpa);
});
