document.addEventListener("DOMContentLoaded", function () {

    const PhenotypicDstRifampicin = document.getElementById("id_rifampicin");
    const PhenotypicDstIsoniazid = document.getElementById("id_isoniazid");
    const PhenotypicDstEthambutol = document.getElementById("id_ethambutol");

    const phenotypicDstSecondLineHeader = document.getElementById("phenotypic-dst-second-line-header");
    const secondLineDstPerformed = document.getElementById("second-line-dst-performed");

    function toggleRifampicinIsoniazidEthambutol() {

        const isPositive =
            PhenotypicDstRifampicin?.value == "1" ||
            PhenotypicDstIsoniazid?.value == "1" ||
            PhenotypicDstEthambutol?.value == "1";

        phenotypicDstSecondLineHeader.style.display = isPositive ? "block" : "none";
        secondLineDstPerformed.style.display = isPositive ? "block" : "none";
    }

    toggleRifampicinIsoniazidEthambutol();

    [PhenotypicDstRifampicin, PhenotypicDstIsoniazid, PhenotypicDstEthambutol]
      .forEach(el => el?.addEventListener("change", toggleRifampicinIsoniazidEthambutol));
});
