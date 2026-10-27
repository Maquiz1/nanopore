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

        if (!tbDiagnosisField || !tbDiagnosisMadeField) return;

        const diagnosis = tbDiagnosisField.value;
        const val = tbDiagnosisMadeField.value;

        hideDiagnosisMade();

        // Only evaluate if TB diagnosis = YES
        if (diagnosis !== "1") return;

        if (val === "1" && clinicalDiagnosisSection) {
            clinicalDiagnosisSection.style.display = "block";
        }

        else if (val === "2" && bacteriologicalDiagnosisSection) {
            bacteriologicalDiagnosisSection.style.display = "block";
        }

        else if (val === "3" && tbDiagnosisMadeOtherSections) {
            tbDiagnosisMadeOtherSections.style.display = "block";
        }
    }

    function toggleTbSections() {
        if (!tbDiagnosisField) return;

        const value = tbDiagnosisField.value;

        if (value === "1") {   // TB Diagnosed
            if (tbDiagnosisDateSections) tbDiagnosisDateSections.style.display = "block";
            if (tbDiagnosisMadeSections) tbDiagnosisMadeSections.style.display = "block";
            if (tbSections) tbSections.style.display = "block";
            if (nonTbSections) nonTbSections.style.display = "none";

            // Now evaluate how diagnosis was made
            toggleTbDiagnosisMade();

        } else {   // Not TB
            if (tbDiagnosisDateSections) tbDiagnosisDateSections.style.display = "none";
            if (tbDiagnosisMadeSections) tbDiagnosisMadeSections.style.display = "none";
            if (tbSections) tbSections.style.display = "none";
            if (nonTbSections) nonTbSections.style.display = "block";
            
            tbDiagnosisMadeField.value = "";
            hideDiagnosisMade();
        }
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

        // "Other, specify" — matched on the label so it does not depend on the option's id
        const option = regimenReasonField.options[regimenReasonField.selectedIndex];
        const isOther = !!option && option.value !== "" && /other/i.test(option.text);
        regimenSpecifySection.style.display = isOther ? "block" : "none";
        if (!isOther) {
            const specify = document.getElementById("id_specify");
            if (specify) specify.value = "";
        }
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
    // 10(a) Was the regimen changed? → Regimen changes table
    // ===========================
    const regimenNotice = document.getElementById("regimenNotice");
    const regimenChangesCard = document.getElementById("regimenChangesCard");
    const regimenFormErrors = document.getElementById("regimenFormErrors");
    const csrfToken = regimenForm ? regimenForm.querySelector("[name=csrfmiddlewaretoken]").value : "";

    function selectedText(select) {
        if (!select || select.selectedIndex < 0 || !select.value) return "";
        return select.options[select.selectedIndex].text.trim().toLowerCase();
    }

    function regimenRows() {
        return regimenTableBody ? regimenTableBody.querySelectorAll("tr[id^='regimenRow']").length : 0;
    }

    function toggleAddButton() {
        // Name kept: the treatment toggles call it too
        const treated = tbTreatmentField && tbTreatmentField.value === "1";
        const answer = selectedText(regimenChangedField);   // "yes" / "no" / ""
        const rows = regimenRows();

        // Table: when the regimen changed, or when changes exist that need sorting out
        if (regimenChangesCard) regimenChangesCard.style.display = (treated && answer === "yes") || rows ? "block" : "none";
        if (addBtn) addBtn.style.display = treated && answer === "yes" ? "inline-block" : "none";

        const emptyRow = regimenTableBody && regimenTableBody.querySelector(".df-empty-row");
        if (emptyRow) emptyRow.style.display = rows ? "none" : "";

        let message = "";
        if (rows && answer !== "yes") {
            message = answer === "no"
                ? "10(a) says the regimen was not changed, but changes are recorded. Delete them, or answer Yes."
                : "Changes are recorded below. Answer 10(a) with Yes, or delete them.";
        } else if (treated && answer === "yes" && !rows) {
            message = "Add at least one regimen change before saving the form.";
        }
        if (regimenNotice) {
            regimenNotice.textContent = message;
            regimenNotice.style.display = message ? "block" : "none";
        }
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

    function showRegimenErrors(errors) {
        if (!regimenFormErrors) return;
        if (!errors) { regimenFormErrors.style.display = "none"; regimenFormErrors.textContent = ""; return; }
        const labels = {date: "Date", drug: "Drug(s)", changes: "Nature of change", reason: "Reason", specify: "Specify", __all__: ""};
        regimenFormErrors.innerHTML = "";
        Object.keys(errors).forEach(key => {
            const line = document.createElement("div");
            line.textContent = (labels[key] ? labels[key] + ": " : "") + [].concat(errors[key]).join(" ");
            regimenFormErrors.appendChild(line);
        });
        regimenFormErrors.style.display = "block";
    }

    function editHandler() {
        const regimenId = this.dataset.id;
        const editUrl = this.dataset.editUrl;
        const saveUrl = this.dataset.saveUrl;
        const screeningId = this.dataset.screeningId;

        regimenForm.reset();
        showRegimenErrors(null);
        regimenIdInput.value = regimenId;
        regimenScreeningInput.value = screeningId;
        regimenForm.action = saveUrl;
        document.getElementById("regimenModalTitle").textContent = "Edit regimen change";

        fetch(editUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
            .then(res => res.json())
            .then(data => {
                Object.keys(data.fields).forEach(key => {
                    const input = regimenForm.querySelector(`#id_${key}`);
                    if(input) input.value = data.fields[key];
                });
                toggleRegimenSpecify();
                regimenModal.show();
            })
            .catch(() => alert("Could not load this regimen change. Please reload the page and try again."));
    }

    function deleteHandler() {
        const deleteUrl = this.dataset.deleteUrl;
        const rowId = `regimenRow${this.dataset.id}`;
        if(!confirm("Delete this regimen change? It goes to the Recycle Bin.")) return;

        fetch(deleteUrl, {
            method: "DELETE",
            headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": csrfToken }
        }).then(res => res.json())
          .then(data => {
            if(data.success) {
                const row = document.getElementById(rowId);
                if(row) row.remove();
                toggleAddButton();
            } else {
                alert("Could not delete: " + JSON.stringify(data.errors));
            }
          })
          .catch(() => alert("Could not delete this regimen change. Please try again."));
    }

    function escapeHtml(value) {
        const div = document.createElement("div");
        div.textContent = value == null ? "" : String(value);
        return div.innerHTML;
    }

    if(addBtn) {
        addBtn.addEventListener("click", function () {
            regimenForm.reset();
            showRegimenErrors(null);
            regimenIdInput.value = "";
            regimenScreeningInput.value = this.dataset.screeningId;
            regimenForm.action = this.dataset.saveUrl;
            document.getElementById("regimenModalTitle").textContent = "Add regimen change";
            toggleRegimenSpecify();
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
                if(!data.success) { showRegimenErrors(data.errors); return; }
                regimenModal.hide();
                const rowId = `regimenRow${data.regimen_id}`;
                let row = document.getElementById(rowId);
                const html = `
                    <td class="text-nowrap" data-label="Date">${escapeHtml(data.date) || "—"}</td>
                    <td data-label="Drug(s)">${escapeHtml(data.drug) || "—"}</td>
                    <td data-label="Change">${escapeHtml(data.changes) || "—"}</td>
                    <td data-label="Reason">${escapeHtml(data.reason) || "—"}${data.specify ? `<div class="df-muted">${escapeHtml(data.specify)}</div>` : ""}</td>
                    <td class="df-row-actions">
                        <button type="button" class="btn btn-sm btn-outline-primary editRegimenBtn"
                            data-id="${data.regimen_id}"
                            data-edit-url="/nanopore/regimen/${data.regimen_id}/edit/"
                            data-save-url="${regimenForm.action}"
                            data-screening-id="${escapeHtml(regimenScreeningInput.value)}"><i class="fas fa-pen"></i> Edit</button>
                        <button type="button" class="btn btn-sm btn-outline-danger deleteRegimenBtn"
                            data-id="${data.regimen_id}"
                            data-delete-url="/nanopore/regimen/${data.regimen_id}/delete/"><i class="fas fa-trash"></i></button>
                    </td>`;
                if(row) row.innerHTML = html;
                else if(regimenTableBody) {
                    const newRow = document.createElement("tr");
                    newRow.id = rowId;
                    newRow.innerHTML = html;
                    regimenTableBody.insertBefore(newRow, regimenTableBody.querySelector(".df-empty-row"));
                }
                bindRegimenButtons();
                toggleAddButton();
            })
            .catch(() => showRegimenErrors({__all__: "Could not save. Check your connection and try again."}));
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
    if(tbTreatmentField) tbTreatmentField.addEventListener("change", function () { toggleTbTreatmentSections(); toggleAddButton(); });
    const tbTreatmentDateField = document.getElementById("id_tb_treatment_date");
    if(tbTreatmentDateField) tbTreatmentDateField.addEventListener("change", toggleTbTreatmentSections);
    if(tbRegimenField) tbRegimenField.addEventListener("change", toggleTbRegimenSection);
    if(tbOtherDiagnosisField) tbOtherDiagnosisField.addEventListener("change", toggleTbOtherSpecify);
    if(regimenChangedField) regimenChangedField.addEventListener("change", toggleAddButton);

    toggleRegimenSpecify();

    if (regimenReasonField) regimenReasonField.addEventListener("change", toggleRegimenSpecify);
    if (regimenModalEl) {
        regimenModalEl.addEventListener("shown.bs.modal", function () {
            toggleRegimenSpecify();
        });
    }
});