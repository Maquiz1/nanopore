// document.addEventListener("DOMContentLoaded", function () {
//     // Result fields
//     const LjResults = document.getElementById("id_lj_results");
//     const MgitResults = document.getElementById("id_mgit_results");

//     // Field to show/hide
//     const IsolateHeader = document.getElementById("isolate-header");
//     const cultureIsolate = document.getElementById("culture-isolate");
//     const IsolateDate = document.getElementById("isolate-date");

//     function toggleCultureIsolate() {
//         const ljValue = String(LjResults?.value || "");
//         const mgitValue = String(MgitResults?.value || "");

//         // Show if LJ is 1-4 OR MGIT is 1
//         const show = ["1", "2", "3", "4"].includes(ljValue) || mgitValue === "1";

//         IsolateHeader.style.display = show ? "block" : "none";
//         cultureIsolate.style.display = show ? "block" : "none";
//         IsolateDate.style.display = show ? "block" : "none";
//     }

//     // Initial state on page load
//     toggleCultureIsolate();

//     // Update when either result changes
//     LjResults.addEventListener("change", toggleCultureIsolate);
//     MgitResults.addEventListener("change", toggleCultureIsolate);
// });
