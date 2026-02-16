    document.addEventListener("DOMContentLoaded", function () {

        // ===== Fields =====
        const tbDiagnosisField = document.getElementById("id_tb_diagnosis");
        const tbDiagnosisDateSections = document.getElementById("tb-diagnosis-date-sections");
        const tbDiagnosisMadeSections = document.getElementById("tb-diagnosis-made-sections");
        const tbSections = document.getElementById("tb-sections");


        // ===== Field References =====
        const tbDiagnosisMadeField = document.getElementById("id_tb_diagnosis_made");
        const clinicalDiagnosisSection = document.querySelector(".clinical-diagnosis-section");
        const bacteriologicalDiagnosisSection = document.querySelector(".bacteriological-diagnosis-section");
        const tbDiagnosisMadeOtherSections = document.getElementById("tb-diagnosis-made-other-sections");


        // ===== Field References =====
        const tbTreatmentField = document.getElementById("id_tb_treatment");
        const tbTreatmentStartedSection = document.querySelector("#tb-treatment-started-section");
        const tbTreatmentFacilitySection = document.querySelector("#tb-treatment-facility-section");
        const tbTreatmentReasonSection = document.querySelector("#tb-treatment-reason-section");
        const tbRegimenChangeSection = document.getElementById("regimen-change-section");

        // ===== Field References =====
        const tbRegimenField = document.getElementById("id_tb_regimen");
        // const tbRegimenChangedSection = document.querySelector("#regimen-changed-section");
        const tbRegimenOtherSection = document.querySelector("#tb-regimen-other-section");

        // ===== Non-TB Sections =====
        const nonTbSections = document.getElementById("non-tb-sections");
        const tbTreatmentOutcomesSections = document.getElementById("tb-treatment-outcomes-sections");

        // ===== Field References =====
        const tbOtherDiagnosisField = document.getElementById("id_tb_other_diagnosis");
        const tbOtherSpecifySection = document.getElementById("tb-other-specify-section");

        // ===== Regimen Change Elements =====
        const regimenChangedField = document.getElementById("id_regimen_changed");
        const addBtn = document.getElementById("addRegimenBtn");
        const regimenModalEl = document.getElementById("regimenChangeModal");
        const regimenModal = new bootstrap.Modal(regimenModalEl);
        const regimenForm = document.getElementById("regimenForm");
        const regimenIdInput = document.getElementById("regimenId");
        const regimenScreeningInput = document.getElementById("regimenScreeningId");
        const regimenTableBody = document.querySelector("#regimenChangesTable tbody");



        // ===== Functions =====
        function toggleTbSections() {
            if (tbDiagnosisField.value === "1") {
                tbDiagnosisDateSections.style.display = "block";
                tbDiagnosisMadeSections.style.display = "block";
                tbTreatmentOutcomesSections.style.display = "block";
                nonTbSections.style.display = "none";
            } else if (tbDiagnosisField.value === "2") {
                tbSections.style.display = "none";
                tbDiagnosisDateSections.style.display = "none";
                tbDiagnosisMadeSections.style.display = "none";
                tbTreatmentOutcomesSections.style.display = "none";
                nonTbSections.style.display = "block";
            }
        }

        // ===== Toggle Clinical/Bacteriological Sections =====
        function toggleDiagnosisMadeSections() {
            if (tbDiagnosisMadeField.value === "1") {  // Clinical
                clinicalDiagnosisSection.style.display = "block";
                bacteriologicalDiagnosisSection.style.display = "none";
                tbDiagnosisMadeOtherSections.style.display = "none";
            } else if (tbDiagnosisMadeField.value === "2") {  // Bacteriological
                clinicalDiagnosisSection.style.display = "none";
                bacteriologicalDiagnosisSection.style.display = "block";
                tbDiagnosisMadeOtherSections.style.display = "none";
            } else if (tbDiagnosisMadeField.value === "3") {  // Other
                clinicalDiagnosisSection.style.display = "none";
                bacteriologicalDiagnosisSection.style.display = "none";
                tbDiagnosisMadeOtherSections.style.display = "block";
            } else {
                clinicalDiagnosisSection.style.display = "none";
                bacteriologicalDiagnosisSection.style.display = "none";
                tbDiagnosisMadeOtherSections.style.display = "none";
            }
        }

        // ===== Helper function to show/hide sections =====
        function toggleTbTreatmentSections() {
            const value = tbTreatmentField ? tbTreatmentField.value : "";

            // Hide all sections by default
            tbTreatmentStartedSection.style.display = "none";
            tbTreatmentFacilitySection.style.display = "none";
            tbTreatmentReasonSection.style.display = "none";
            tbRegimenChangeSection.style.display = "none";
            tbTreatmentOutcomesSections.style.display = "none";
            // Show based on selection
            if (value === "1") {
                // TB treatment = 1 → Show Started + Regimen Change
                tbTreatmentStartedSection.style.display = "block";
                tbRegimenChangeSection.style.display = "block";
                tbTreatmentOutcomesSections.style.display = "block";
            } else if (value === "2") {
                // TB treatment = 2 → Show Facility
                tbTreatmentFacilitySection.style.display = "block";
                tbTreatmentOutcomesSections.style.display = "none";
            } else if (value === "3") {
                // TB treatment = 3 → Show Reason
                tbTreatmentReasonSection.style.display = "block";
                tbTreatmentOutcomesSections.style.display = "none";
            }
        }

        // ===== Helper function for TB Regimen Other =====
        function toggleTbRegimenSection() {
            const value = tbRegimenField ? tbRegimenField.value : "";

            // Hide by default
            tbRegimenOtherSection.style.display = "none";

            // Show when value = 7
            if (value === "7") {
                tbRegimenOtherSection.style.display = "block";
            }
        }

        function toggleTbOtherSpecify() {
            if (!tbOtherDiagnosisField || !tbOtherSpecifySection) return;

            if (tbOtherDiagnosisField.value === "3" || tbOtherDiagnosisField.value === "6") {
                tbOtherSpecifySection.style.display = "block";
            } else {
                tbOtherSpecifySection.style.display = "none";
            }
        }


        // ===== Toggle Add Regimen Button =====
        function toggleAddButton() {
            if (regimenChangedField.value === "1") {
                addBtn.style.display = "inline-block";
            } else {
                addBtn.style.display = "none";
            }
        }

        function bindRegimenButtons() {
            document.querySelectorAll(".editRegimenBtn").forEach(btn => {
                btn.removeEventListener("click", editHandler);
                btn.addEventListener("click", editHandler);
            });
            document.querySelectorAll(".deleteRegimenBtn").forEach(btn => {
                btn.removeEventListener("click", deleteHandler);
                btn.addEventListener("click", deleteHandler);
            });
        }

        function editHandler() {
            const regimenId = this.dataset.id;
            const editUrl = this.dataset.editUrl;
            const saveUrl = this.dataset.saveUrl;
            const screeningId = this.dataset.screeningId;

            regimenIdInput.value = regimenId;
            regimenScreeningInput.value = screeningId;
            regimenForm.action = saveUrl;
            document.getElementById("regimenModalTitle").textContent = "Edit Regimen Change";

            fetch(editUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
                .then(res => res.json())
                .then(data => {
                    Object.keys(data.fields).forEach(key => {
                        const input = document.getElementById(`id_${key}`);
                        if (input) input.value = data.fields[key];
                    });
                    regimenModal.show();
                });
        }

        function deleteHandler() {
            const deleteUrl = this.dataset.deleteUrl;
            const rowId = `regimenRow${this.dataset.id}`;
            if (!confirm("Are you sure you want to delete this regimen change?")) return;

            fetch(deleteUrl, {
                method: "DELETE",
                headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": "{{ csrf_token }}" }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        const row = document.getElementById(rowId);
                        if (row) row.remove();
                    } else {
                        alert("Error deleting regimen: " + JSON.stringify(data.errors));
                    }
                });
        }

        // ===== Add button click =====
        addBtn.addEventListener("click", function () {
            regimenForm.reset();
            regimenIdInput.value = "";
            regimenScreeningInput.value = this.dataset.screeningId;
            regimenForm.action = this.dataset.saveUrl;
            document.getElementById("regimenModalTitle").textContent = "Add Regimen Change";
            regimenModal.show();
        });

        // ===== Regimen form AJAX submit =====
        regimenForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const formData = new FormData(regimenForm);
            fetch(regimenForm.action, {
                method: "POST",
                body: formData,
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        regimenModal.hide();
                        const rowId = `regimenRow${data.regimen_id}`;
                        let row = document.getElementById(rowId);
                        const html = `
                        <td>${data.date}</td>
                        <td>${data.drug}</td>
                        <td>${data.changes}</td>
                        <td>${data.reason}</td>
                        <td>
                            <button class="btn btn-sm btn-warning editRegimenBtn"
                                    data-id="${data.regimen_id}"
                                    data-edit-url="/nanopore/regimen/${data.regimen_id}/edit/"
                                    data-save-url="${regimenForm.action}"
                                    data-screening-id="${regimenScreeningInput.value}">
                                Edit
                            </button>
                            <button class="btn btn-sm btn-danger deleteRegimenBtn"
                                    data-id="${data.regimen_id}"
                                    data-delete-url="/nanopore/regimen/${data.regimen_id}/delete/">
                                Delete
                            </button>
                        </td>
                    `;
                        if (row) row.innerHTML = html;
                        else if (regimenTableBody) {
                            const newRow = document.createElement("tr");
                            newRow.id = rowId;
                            newRow.innerHTML = html;
                            regimenTableBody.prepend(newRow);
                        }
                        bindRegimenButtons();
                    } else {
                        alert("Error: " + JSON.stringify(data.errors));
                    }
                });
        });

        // ===== Initial calls & event binding =====
        toggleTbSections();
        toggleDiagnosisMadeSections();
        // ===== Run on load =====
        toggleTbTreatmentSections();
        toggleTbRegimenSection();

        toggleAddButton();
        tbDiagnosisField.addEventListener("change", toggleTbSections);
        tbDiagnosisMadeField.addEventListener("change", toggleDiagnosisMadeSections);
        // ===== Run on change =====
        // if (tbDiagnosisMadeField) {
        //     tbDiagnosisMadeField.addEventListener("change", toggleDiagnosisMadeSections);
        // }

        if (tbTreatmentField) {
            tbTreatmentField.addEventListener("change", toggleTbTreatmentSections);
        }

        if (tbRegimenField) {
            tbRegimenField.addEventListener("change", toggleTbRegimenSection);
        }

        if (tbOtherDiagnosisField) {
            tbOtherDiagnosisField.addEventListener("change", toggleTbOtherSpecify);
            toggleTbOtherSpecify(); // initialize on page load
        }


        regimenChangedField.addEventListener("change", toggleAddButton);
        bindRegimenButtons();

    });
