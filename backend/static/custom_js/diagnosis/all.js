document.addEventListener("DOMContentLoaded", function () {
    // ===========================
    // Fields
    // ===========================
    const tbDiagnosisField = document.getElementById("id_tb_diagnosis");
    const tbDiagnosisMadeField = document.getElementById("id_tb_diagnosis_made");

    const tbDiagnosisDateSections = document.getElementById("tb-diagnosis-date-sections");
    const tbDiagnosisMadeSections = document.getElementById("tb-diagnosis-made-sections");
    const tbDiagnosisMadeOtherSections = document.getElementById("tb-diagnosis-made-other-sections");
    const clinicalDiagnosisSection = document.getElementById("clinical-diagnosis-section");
    const bacteriologicalDiagnosisSection = document.getElementById("bacteriological-diagnosis-section");
    const tbSections = document.getElementById("tb-sections");

    const tbDiagnosedClinicallyField = document.getElementById("id_tb_diagnosed_clinically");
    const tbDiagnosedClinicallyCheckboxes = document.querySelectorAll("input[name='tb_diagnosed_clinically']");
    const tbClinicallyOtherSection = document.getElementById("tb-clinically-other");

    const tbTreatmentField = document.getElementById("id_tb_treatment");
    const tbTreatmentStartedSection = document.getElementById("tb-treatment-started-section");
    const tbTreatmentFacilitySection = document.getElementById("tb-treatment-facility-section");
    const tbTreatmentReasonSection = document.getElementById("tb-treatment-reason-section");
    const tbRegimenChangeSection = document.getElementById("regimen-change-section");
    const tbRegimenField = document.getElementById("id_tb_regimen");
    const tbRegimenOtherSection = document.getElementById("tb-regimen-other-section");

    const nonTbSections = document.getElementById("non-tb-sections");
    const tbTreatmentOutcomesSections = document.getElementById("tb-treatment-outcomes-sections");

    const tbOtherDiagnosisField = document.getElementById("id_tb_other_diagnosis");
    const tbOtherSpecifySection = document.getElementById("tb-other-specify-section");

    const regimenChangedField = document.getElementById("id_regimen_changed");
    const addBtn = document.getElementById("addRegimenBtn");
    const regimenModalEl = document.getElementById("regimenChangeModal");
    const regimenModal = new bootstrap.Modal(regimenModalEl);
    const regimenForm = document.getElementById("regimenForm");
    const regimenIdInput = document.getElementById("regimenId");
    const regimenScreeningInput = document.getElementById("regimenScreeningId");
    const regimenTableBody = document.querySelector("#regimenChangesTable tbody");

    const regimenReasonField = document.getElementById("id_reason");
    const regimenSpecifySection = document.getElementById("regimen-specify-section");

    // ===========================
    // TB Diagnosis Made
    // ===========================
    function hideDiagnosisMade() {
        // if(tbDiagnosisMadeSections) tbDiagnosisMadeSections.style.display = "none";
        if(tbDiagnosisMadeOtherSections) tbDiagnosisMadeOtherSections.style.display = "none";
        if(clinicalDiagnosisSection) clinicalDiagnosisSection.style.display = "none";
        if(bacteriologicalDiagnosisSection) bacteriologicalDiagnosisSection.style.display = "none";
    }

    function toggleTbDiagnosisMade() {
        if(!tbDiagnosisField || !tbDiagnosisMadeField) return;
        if(tbDiagnosisField.value !== "1") {
            hideDiagnosisMade();
            return;
        }
        const val = tbDiagnosisMadeField.value;
        hideDiagnosisMade();
        if(val === "1" && clinicalDiagnosisSection) clinicalDiagnosisSection.style.display = "block";
        else if(val === "2" && bacteriologicalDiagnosisSection) bacteriologicalDiagnosisSection.style.display = "block";
        else if(val === "3" && tbDiagnosisMadeOtherSections) tbDiagnosisMadeOtherSections.style.display = "block";
    }

    function toggleTbSections() {
        if(!tbDiagnosisField) return;
        if(tbDiagnosisField.value === "1") {
            if(tbDiagnosisDateSections) tbDiagnosisDateSections.style.display = "block";
            if(tbDiagnosisMadeSections) tbDiagnosisMadeSections.style.display = "block";
            if(tbSections) tbSections.style.display = "block";
            if(nonTbSections) nonTbSections.style.display = "none";
        } else {
            if(tbDiagnosisDateSections) tbDiagnosisDateSections.style.display = "none";
            if(tbDiagnosisMadeSections) tbDiagnosisMadeSections.style.display = "none";
            if(tbSections) tbSections.style.display = "none";
            if(nonTbSections) nonTbSections.style.display = "block";
        }
        toggleTbDiagnosisMade();
    }

    function toggleTbClinicallyOther() {
        const anyChecked = Array.from(tbDiagnosedClinicallyCheckboxes)
                                .some(cb => cb.value === "9" && cb.checked);
        tbClinicallyOtherSection.style.display = anyChecked ? "block" : "none";
    }

    // ===========================
    // TB Treatment Sections + Outcome logic
    // ===========================
    function toggleTbTreatmentSections() {
        if(!tbTreatmentField) return;
        const value = tbTreatmentField.value;

        if(tbTreatmentStartedSection) tbTreatmentStartedSection.style.display = "none";
        if(tbTreatmentFacilitySection) tbTreatmentFacilitySection.style.display = "none";
        if(tbTreatmentReasonSection) tbTreatmentReasonSection.style.display = "none";
        if(tbRegimenChangeSection) tbRegimenChangeSection.style.display = "none";
        if(tbTreatmentOutcomesSections) tbTreatmentOutcomesSections.style.display = "none";

        if(value === "1") {
            if(tbTreatmentStartedSection) tbTreatmentStartedSection.style.display = "block";
            if(tbRegimenChangeSection) tbRegimenChangeSection.style.display = "block";

            // Outcome logic: only show if treatment date ≥ 6 months ago
            if(tbTreatmentOutcomesSections) {
                const treatmentDateStr = document.getElementById("id_tb_treatment_date")?.value || "";
                let showOutcome = false;
                if(treatmentDateStr) {
                    const treatmentDate = new Date(treatmentDateStr);
                    const now = new Date();
                    const sixMonthsAgo = new Date();
                    sixMonthsAgo.setMonth(now.getMonth() - 6);
                    if(!isNaN(treatmentDate.getTime()) && treatmentDate <= sixMonthsAgo) {
                        showOutcome = true;
                    }
                }
                tbTreatmentOutcomesSections.style.display = showOutcome ? "block" : "none";
            }
        } else if(value === "2") {
            if(tbTreatmentFacilitySection) tbTreatmentFacilitySection.style.display = "block";
        } else if(value === "3") {
            if(tbTreatmentReasonSection) tbTreatmentReasonSection.style.display = "block";
        }
    }

    // ===========================
    // TB Regimen Other
    // ===========================
    function toggleTbRegimenSection() {
        if(!tbRegimenField) return;
        const value = tbRegimenField.value;
        if(tbRegimenOtherSection) tbRegimenOtherSection.style.display = (value === "7") ? "block" : "none";
    }

    function toggleRegimenSpecify() {
        if (!regimenReasonField || !regimenSpecifySection) return;

        const value = regimenReasonField.value;
        regimenSpecifySection.style.display = (value === "3") ? "block" : "none";
    }

    // ===========================
    // TB Other Specify
    // ===========================
    function toggleTbOtherSpecify() {
        if(!tbOtherDiagnosisField || !tbOtherSpecifySection) return;
        const value = tbOtherDiagnosisField.value;
        tbOtherSpecifySection.style.display = (value === "3" || value === "6") ? "block" : "none";
    }

    // ===========================
    // Regimen Add Button
    // ===========================
    function toggleAddButton() {
        if(!regimenChangedField || !addBtn) return;
        addBtn.style.display = (regimenChangedField.value === "1") ? "inline-block" : "none";
    }

    // ===========================
    // Regimen Table Buttons
    // ===========================
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
                    if(input) input.value = data.fields[key];
                });
                regimenModal.show();
            });
    }

    function deleteHandler() {
        const deleteUrl = this.dataset.deleteUrl;
        const rowId = `regimenRow${this.dataset.id}`;
        if(!confirm("Are you sure you want to delete this regimen change?")) return;

        fetch(deleteUrl, {
            method: "DELETE",
            headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": "{{ csrf_token }}" }
        }).then(res => res.json())
          .then(data => {
            if(data.success) {
                const row = document.getElementById(rowId);
                if(row) row.remove();
            } else {
                alert("Error deleting regimen: " + JSON.stringify(data.errors));
            }
          });
    }

    if(addBtn) {
        addBtn.addEventListener("click", function () {
            regimenForm.reset();
            regimenIdInput.value = "";
            regimenScreeningInput.value = this.dataset.screeningId;
            regimenForm.action = this.dataset.saveUrl;
            document.getElementById("regimenModalTitle").textContent = "Add Regimen Change";
            regimenModal.show();
        });
    }

    if(regimenForm) {
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
                if(data.success) {
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
                                data-screening-id="${regimenScreeningInput.value}">Edit</button>
                            <button class="btn btn-sm btn-danger deleteRegimenBtn"
                                data-id="${data.regimen_id}"
                                data-delete-url="/nanopore/regimen/${data.regimen_id}/delete/">Delete</button>
                        </td>`;
                    if(row) row.innerHTML = html;
                    else if(regimenTableBody) {
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

    // ===========================
    // Initial calls & bindings
    // ===========================
    toggleTbSections();
    toggleTbTreatmentSections();
    toggleTbRegimenSection();
    toggleTbOtherSpecify();
    toggleAddButton();
    bindRegimenButtons();
    // Initial state
    // toggleTbClinicallyOther();
    // Attach change listener to all checkboxes
    tbDiagnosedClinicallyCheckboxes.forEach(cb => cb.addEventListener("change", toggleTbClinicallyOther));

    // Initial state
    toggleTbClinicallyOther();

    // Update whenever selection changes
    tbDiagnosedClinicallyField.addEventListener("change", toggleTbClinicallyOther);

    if(tbDiagnosisField) tbDiagnosisField.addEventListener("change", toggleTbSections);
    if(tbDiagnosisMadeField) tbDiagnosisMadeField.addEventListener("change", toggleTbDiagnosisMade);
    if(tbTreatmentField) tbTreatmentField.addEventListener("change", toggleTbTreatmentSections);
    if(tbRegimenField) tbRegimenField.addEventListener("change", toggleTbRegimenSection);
    if(tbOtherDiagnosisField) tbOtherDiagnosisField.addEventListener("change", toggleTbOtherSpecify);
    if(regimenChangedField) regimenChangedField.addEventListener("change", toggleAddButton);

    toggleRegimenSpecify();

    // if (regimenReasonField) {
    //     regimenReasonField.addEventListener("change", toggleRegimenSpecify);
    // }
    // ADD THIS HERE
    if (regimenModalEl) {
        regimenModalEl.addEventListener("shown.bs.modal", function () {
            toggleRegimenSpecify();
        });
    }
});