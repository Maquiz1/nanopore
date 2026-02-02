document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const EpiToMe = document.getElementById("id_epi_to_me");

    // Field to show/hide
    const epiToMeDate = document.getElementById("id_epi_to_me_date");
    const epiToMeVersion = document.getElementById("id_epi_to_me_version");
    const sequencingResults = document.getElementById("id_sequencing_results");

    // Function to toggle visibility
    function toggleEpiToMe() {

        const value = String(EpiToMe?.value || "");

        if (value === "1") {
            epiToMeDate.style.display = "block";
            epiToMeVersion.style.display = "block";
            sequencingResults.style.display = "block";
        } else {
            epiToMeDate.style.display = "none";
            epiToMeVersion.style.display = "none";
            sequencingResults.style.display = "none";
        }
    }

    // Initial state on page load
    toggleEpiToMe();

    // Update when either result changes
    EpiToMe.addEventListener("change", toggleEpiToMe);
});
