document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const XpertXdrPerformed = document.getElementById("id_xpert_xdr_performed");

    // Field to show/hide
    const xpertXdrDatePerformed = document.getElementById("id_xpert_xdr_date_performed");
    const xpertXdrHeader = document.getElementById("xpert-xdr-header");
    const xpertXdrResults = document.getElementById("xpert-xdr-results");

    // Function to toggle visibility
    function toggleXpertXdrPerformed() {

        const value = String(XpertXdrPerformed?.value || "");

        if (value === "1") {
            xpertXdrDatePerformed.style.display = "block";
            xpertXdrHeader.style.display = "block";
            xpertXdrResults.style.display = "block";
        } else {
            xpertXdrDatePerformed.style.display = "none";
            xpertXdrHeader.style.display = "none";
            xpertXdrResults.style.display = "none";
        }
    }

    // Initial state on page load
    toggleXpertXdrPerformed();

    // Update when either result changes
    XpertXdrPerformed.addEventListener("change", toggleXpertXdrPerformed);
});
