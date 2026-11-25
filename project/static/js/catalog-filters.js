/* Live catalog filters. Keeps the submit button as a no-JS fallback. */
(function () {
    "use strict";

    const form = document.querySelector(".catalog-filters");
    if (!form) {
        return;
    }

    form.classList.add("catalog-filters--live");

    const search = form.querySelector('input[name="q"]');
    const selects = form.querySelectorAll("select");
    let timer = null;
    let submitting = false;
    let lastQuery = search ? search.value : "";

    function applyNow() {
        window.clearTimeout(timer);
        timer = null;
        if (submitting) {
            return;
        }
        submitting = true;
        if (typeof form.requestSubmit === "function") {
            form.requestSubmit();
        } else {
            form.submit();
        }
    }

    selects.forEach(function (select) {
        select.addEventListener("change", applyNow);
    });

    if (search) {
        search.addEventListener("input", function () {
            const value = search.value;
            if (value === lastQuery) {
                return;
            }
            window.clearTimeout(timer);
            timer = window.setTimeout(function () {
                search.value = search.value.trim();
                lastQuery = search.value;
                applyNow();
            }, 400);
        });
    }

    form.addEventListener("submit", function () {
        window.clearTimeout(timer);
        timer = null;
    });
})();
