(function () {
    "use strict";

    const STORAGE_KEY = "libra-theme";

    function currentTheme() {
        try {
            return localStorage.getItem(STORAGE_KEY) === "dark" ? "dark" : "light";
        } catch (error) {
            return document.documentElement.getAttribute("data-bs-theme") || "light";
        }
    }

    function updateIcons(theme) {
        document.querySelectorAll("[data-theme-icon]").forEach(function (icon) {
            icon.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
        });
        document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
            const label = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
            button.setAttribute("aria-label", label);
            button.setAttribute("title", label);
        });
    }

    function applyTheme(theme, persist) {
        const normalized = theme === "dark" ? "dark" : "light";
        document.documentElement.setAttribute("data-bs-theme", normalized);
        if (persist) {
            try {
                localStorage.setItem(STORAGE_KEY, normalized);
            } catch (error) {
                /* localStorage can be unavailable in private mode */
            }
        }
        updateIcons(normalized);
        document.dispatchEvent(
            new CustomEvent("libra:themechange", { detail: { theme: normalized } })
        );
    }

    document.addEventListener("click", function (event) {
        const toggle = event.target.closest("[data-theme-toggle]");
        if (!toggle) {
            return;
        }
        event.preventDefault();
        applyTheme(currentTheme() === "dark" ? "light" : "dark", true);
    });

    window.addEventListener("storage", function (event) {
        if (event.key === STORAGE_KEY && event.newValue) {
            applyTheme(event.newValue, false);
        }
    });

    applyTheme(currentTheme(), false);
})();
