document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const FirstLineLpa = document.getElementById("id_first_line_lpa");

    // Field to show/hide
    const firstLineLpaDate = document.getElementById("id_first_line_lpa_date");
    const lpa1Mtb = document.getElementById("id_lpa1_mtb");
    const lpa1Rif = document.getElementById("id_lpa1_rif");
    const lpa1Inh = document.getElementById("id_lpa1_inh");
    const firstLineDrugs = document.getElementById("first-line-drugs");

    // Function to toggle visibility
    function toggleFirstLineLpa() {

        const value = String(FirstLineLpa?.value || "");

        if (value === "1") {
            firstLineLpaDate.style.display = "block";
            lpa1Mtb.style.display = "block";
            lpa1Rif.style.display = "block";
            lpa1Inh.style.display = "block";
            firstLineDrugs.style.display = "block";
        } else {
            firstLineLpaDate.style.display = "none";
            lpa1Mtb.style.display = "none";
            lpa1Rif.style.display = "none";
            lpa1Inh.style.display = "none";
            firstLineDrugs.style.display = "none";
        }
    }

    // Initial state on page load
    toggleFirstLineLpa();

    // Update when either result changes
    FirstLineLpa.addEventListener("change", toggleFirstLineLpa);
});
