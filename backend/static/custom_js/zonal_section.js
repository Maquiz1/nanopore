// Zonal Lab section forms: show a question only when the answer it depends on opens it.
// The rules come from the server (nanopore/forms/laboratory/zonal/section_forms.py, data-when-*),
// which also clears hidden answers on save, so the page and the saved record agree.
document.addEventListener("DOMContentLoaded", function () {
    const dependents = Array.from(document.querySelectorAll("[data-when-field]"));
    if (!dependents.length) return;

    function selected(name) {
        // The chosen option ids of a question, or none when the question itself is hidden.
        const inputs = Array.from(document.querySelectorAll(`[name="${name}"]`));
        if (!inputs.length) return [];
        const holder = inputs[0].closest("[data-when-field]");
        if (holder && holder.hidden) return [];
        return inputs.flatMap(input => {
            if (input.tagName === "SELECT") return input.value ? [input.value] : [];
            if (input.type === "checkbox" || input.type === "radio") return input.checked ? [input.value] : [];
            return [];
        });
    }

    function refresh() {
        // Parents come before their children on the page, so one pass settles a chain.
        dependents.forEach(holder => {
            const opens = holder.dataset.whenIn.split(",");
            holder.hidden = !selected(holder.dataset.whenField).some(value => opens.includes(value));
        });
    }

    refresh();
    document.addEventListener("change", refresh);
});
