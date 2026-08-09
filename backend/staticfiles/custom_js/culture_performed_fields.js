document.addEventListener("DOMContentLoaded", function () {
    const CulturePerformed = document.getElementById("id_culture_performed");

    // Fields To Hide
    const cultureMethod = document.getElementById("culture_method");
    const microscopyType = document.getElementById("microscopy_type");
    const microscopyDate = document.getElementById("microscopy_date");
    const microscopyResults = document.getElementById("microscopy_results");

    function toggleCulture() {
        const value = String(CulturePerformed?.value || "");
        
        if (value === "1") {
            cultureMethod.style.display = "block";
            microscopyType.style.display = "block";
            microscopyDate.style.display = "block";
            microscopyResults.style.display = "block";
        } else {
            cultureMethod.style.display = "none";
            microscopyType.style.display = "none";
            microscopyDate.style.display = "none";
            microscopyResults.style.display = "none";
        }
    }

    toggleCulture();
    CulturePerformed.addEventListener("change", toggleCulture);
});
