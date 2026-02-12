document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const Rifampicin = document.getElementById("id_rifampicin");
    const Isoniazid = document.getElementById("id_isoniazid");
    const Ethambutol = document.getElementById("id_ethambutol");


    // Field to show/hide
    const phenotypicDstSecondLineHeader = document.getElementById("phenotypic-dst-second-line-header");
    const secondLineDstPerformed = document.getElementById("second-line-dst-performed");

    // Function to toggle visibility
    function toggleRifampicinIsoniazidEthambutol() {

        const value = String(
            Rifampicin?.value === 1 ||
            Isoniazid?.value === 1 ||
            Ethambutol?.value === 1
        );


        if (value === "1") {
            phenotypicDstSecondLineHeader.style.display = "block";
            secondLineDstPerformed.style.display = "block";
        } else {

            phenotypicDstSecondLineHeader.style.display = "none";
            secondLineDstPerformed.style.display = "none";
        }
    }

    // Initial state on page load
    toggleRifampicinIsoniazidEthambutol();

    // Update when either result changes
    // Rifampicin.addEventListener("change", toggleRifampicinIsoniazidEthambutol);
    // Isoniazid.addEventListener("change", toggleRifampicinIsoniazidEthambutol);
    // Ethambutol.addEventListener("change", toggleRifampicinIsoniazidEthambutol);

    [Rifampicin, Isoniazid, Ethambutol].forEach(el => {
    el?.addEventListener("change", togglePhenotypicPerformed);
    });

});
