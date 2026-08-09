document.addEventListener("DOMContentLoaded", function () {
    // Result fields
    const XpertXdrPerformed = document.getElementById("id_xpert_xdr_performed");

    // Field to show/hide
    const xpertXdrDatePerformedSection = document.getElementById("xpert-xdr-date-performed");
    const xpertXdrHeader = document.getElementById("xpert-xdr-header");
    const xpertXdrResults = document.getElementById("xpert-xdr-results");

    // Function to toggle visibility
    function toggleXpertXdrPerformed() {

        const value = String(XpertXdrPerformed?.value || "");

        if (value === "1") {
            if (xpertXdrDatePerformedSection) xpertXdrDatePerformedSection.style.display = "block";
            if (xpertXdrHeader) xpertXdrHeader.style.display = "block";
            if (xpertXdrResults) xpertXdrResults.style.display = "block";
        } else {
            if (xpertXdrDatePerformedSection) xpertXdrDatePerformedSection.style.display = "none";
            if (xpertXdrHeader) xpertXdrHeader.style.display = "none";
            if (xpertXdrResults) xpertXdrResults.style.display = "none";
        }
    }

    // Initial state on page load
    toggleXpertXdrPerformed();

    // Update when dropdown changes
    XpertXdrPerformed.addEventListener("change", toggleXpertXdrPerformed);
});
