document.addEventListener("DOMContentLoaded", function () {
    const culturePerformed = document.getElementById("id_culture_performed");
    const microscopyMethod = document.getElementById("culture_method");
    const microscopyType = document.getElementById("microscopy_type");
    const microscopyDate = document.getElementById("microscopy_date");
    const microscopyResults = document.getElementById("microscopy_results");

    function toggleCulture() {
        const value = String(culturePerformed?.value || "");
        if (value === "1") {
            microscopyMethod.style.display = "block";
            microscopyType.style.display = "block";
            microscopyDate.style.display = "block";
            microscopyResults.style.display = "block";
        } else {
            microscopyMethod.style.display = "none";
            microscopyType.style.display = "none";
            microscopyDate.style.display = "none";
            microscopyResults.style.display = "none";
        }
    }

    toggleCulture();
    culturePerformed.addEventListener("change", toggleCulture);
});
