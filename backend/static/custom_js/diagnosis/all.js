document.addEventListener("DOMContentLoaded", function () {

    // ===== TB Diagnosis =====
    const tbDiagnosisField = document.getElementById("id_tb_diagnosis");
    const tbDiagnosisDateSections = document.getElementById("tb-diagnosis-date-sections");
    const tbDiagnosisMadeSections = document.getElementById("tb-diagnosis-made-sections");
    const tbSections = document.getElementById("tb-sections");

    // ===== TB Diagnosis Made =====
    const TbDiagnosisMadeField = document.getElementById("id_tb_diagnosis_made");
    const clinicalDiagnosisSection = document.getElementById("clinical-diagnosis-section");
    const bacteriologicalDiagnosisSection = document.getElementById("bacteriological-diagnosis-section");
    const tbDiagnosisMadeOtherSections = document.getElementById("tb-diagnosis-made-other-sections");

    // ===== TB Treatment =====
    const tbTreatmentField = document.getElementById("id_tb_treatment");
    const tbTreatmentStartedSection = document.querySelector("#tb-treatment-started-section");
    const tbTreatmentFacilitySection = document.querySelector("#tb-treatment-facility-section");
    const tbTreatmentReasonSection = document.querySelector("#tb-treatment-reason-section");
    const tbRegimenChangeSection = document.getElementById("regimen-change-section");
    const tbTreatmentOutcomesSections = document.getElementById("tb-treatment-outcomes-sections");

    // ===== TB Regimen =====
    const tbRegimenField = document.getElementById("id_tb_regimen");
    const tbRegimenOtherSection = document.querySelector("#tb-regimen-other-section");

    // ===== Non-TB & Other =====
    const nonTbSections = document.getElementById("non-tb-sections");
    const tbOtherDiagnosisField = document.getElementById("id_tb_other_diagnosis");
    const tbOtherSpecifySection = document.getElementById("tb-other-specify-section");

    // ===== Regimen Change Modal =====
    const regimenChangedField = document.getElementById("id_regimen_changed");
    const addBtn = document.getElementById("addRegimenBtn");
    const regimenModalEl = document.getElementById("regimenChangeModal");
    const regimenModal = new bootstrap.Modal(regimenModalEl);
    const regimenForm = document.getElementById("regimenForm");
    const regimenIdInput = document.getElementById("regimenId");
    const regimenScreeningInput = document.getElementById("regimenScreeningId");
    const regimenTableBody = document.querySelector("#regimenChangesTable tbody");

    // ===== Helper Functions =====
    function toggleTbSections() {
        if (!tbDiagnosisField) return;

        if (tbDiagnosisField.value === "1") {
            if (tbDiagnosisDateSections) tbDiagnosisDateSections.style.display = "block";
            if (tbDiagnosisMadeSections) tbDiagnosisMadeSections.style.display = "block";
            if (tbTreatmentOutcomesSections) tbTreatmentOutcomesSections.style.display = "block";
            if (nonTbSections) nonTbSections.style.display = "none";
        } else if (tbDiagnosisField.value === "2") {
            if (tbSections) tbSections.style.display = "none";
            if (tbDiagnosisDateSections) tbDiagnosisDateSections.style.display = "none";
            if (tbDiagnosisMadeSections) tbDiagnosisMadeSections.style.display = "none";
            if (tbTreatmentOutcomesSections) tbTreatmentOutcomesSections.style.display = "none";
            if (nonTbSections) nonTbSections.style.display = "block";
        }
        toggleTbDiagnosisMadeField(); // always evaluate made field after diagnosis change
    }

    function hideAllDiagnosisMade() {
        if (clinicalDiagnosisSection) clinicalDiagnosisSection.style.display = "none";
        if (bacteriologicalDiagnosisSection) bacteriologicalDiagnosisSection.style.display = "none";
        if (tbDiagnosisMadeOtherSections) tbDiagnosisMadeOtherSections.style.display = "none";
    }

    function toggleTbDiagnosisMadeField() {
        if (!TbDiagnosisMadeField || !tbDiagnosisField) return;

        const diagnosisValue = tbDiagnosisField.value || "";
        const madeValue = TbDiagnosisMadeField.value || "";

        // Hide if TB diagnosis is not 1
        if (diagnosisValue !== "1") {
            if (tbDiagnosisMadeSections) tbDiagnosisMadeSections.style.display = "none";
            hideAllDiagnosisMade();
            return;
        }

        // Ensure parent container visible
        if (tbDiagnosisMadeSections) tbDiagnosisMadeSections.style.display = "block";

        hideAllDiagnosisMade();

        if (madeValue === "1") {
            if (clinicalDiagnosisSection) clinicalDiagnosisSection.style.display = "block";
        } else if (madeValue === "2") {
            if (bacteriologicalDiagnosisSection) bacteriologicalDiagnosisSection.style.display = "block";
        } else if (madeValue === "3") {
            if (tbDiagnosisMadeOtherSections) tbDiagnosisMadeOtherSections.style.display = "block";
        }
    }

    function toggleTbTreatmentSections() {
        if (!tbTreatmentField) return;
        const value = tbTreatmentField.value;

        // Hide all
        if (tbTreatmentStartedSection) tbTreatmentStartedSection.style.display = "none";
        if (tbTreatmentFacilitySection) tbTreatmentFacilitySection.style.display = "none";
        if (tbTreatmentReasonSection) tbTreatmentReasonSection.style.display = "none";
        if (tbRegimenChangeSection) tbRegimenChangeSection.style.display = "none";
        if (tbTreatmentOutcomesSections) tbTreatmentOutcomesSections.style.display = "none";

        if (value === "1") {
            if (tbTreatmentStartedSection) tbTreatmentStartedSection.style.display = "block";
            if (tbRegimenChangeSection) tbRegimenChangeSection.style.display = "block";
            if (tbTreatmentOutcomesSections) tbTreatmentOutcomesSections.style.display = "block";
        } else if (value === "2") {
            if (tbTreatmentFacilitySection) tbTreatmentFacilitySection.style.display = "block";
        } else if (value === "3") {
            if (tbTreatmentReasonSection) tbTreatmentReasonSection.style.display = "block";
        }
    }

    function toggleTbRegimenSection() {
        if (!tbRegimenField || !tbRegimenOtherSection) return;
        tbRegimenOtherSection.style.display = tbRegimenField.value === "7" ? "block" : "none";
    }

    function toggleTbOtherSpecify() {
        if (!tbOtherDiagnosisField || !tbOtherSpecifySection) return;
        tbOtherSpecifySection.style.display = (tbOtherDiagnosisField.value === "3" || tbOtherDiagnosisField.value === "6") ? "block" : "none";
    }

    function toggleAddButton() {
        if (!regimenChangedField || !addBtn) return;
        addBtn.style.display = (regimenChangedField.value === "1") ? "inline-block" : "none";
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
    if (addBtn) {
        addBtn.addEventListener("click", function () {
            regimenForm.reset();
            regimenIdInput.value = "";
            regimenScreeningInput.value = this.dataset.screeningId;
            regimenForm.action = this.dataset.saveUrl;
            document.getElementById("regimenModalTitle").textContent = "Add Regimen Change";
            regimenModal.show();
        });
    }

    // ===== Regimen form submit =====
    if (regimenForm) {
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
                        </td>`;
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
    }

    // ===== Event Listeners =====
    if (tbDiagnosisField) tbDiagnosisField.addEventListener("change", toggleTbSections);
    if (TbDiagnosisMadeField) TbDiagnosisMadeField.addEventListener("change", toggleTbDiagnosisMadeField);
    if (tbTreatmentField) tbTreatmentField.addEventListener("change", toggleTbTreatmentSections);
    if (tbRegimenField) tbRegimenField.addEventListener("change", toggleTbRegimenSection);
    if (tbOtherDiagnosisField) {
        tbOtherDiagnosisField.addEventListener("change", toggleTbOtherSpecify);
    }
    if (regimenChangedField) regimenChangedField.addEventListener("change", toggleAddButton);

    // ===== Initial Calls =====
    toggleTbSections();
    toggleTbTreatmentSections();
    toggleTbRegimenSection();
    toggleTbOtherSpecify();
    toggleAddButton();
    toggleTbDiagnosisMadeField();
    bindRegimenButtons();

});