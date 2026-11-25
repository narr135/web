(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        const list = document.getElementById("shelf-items");
        const status = document.getElementById("reorder-status");
        if (!list || typeof Sortable === "undefined") {
            return;
        }

        const reorderUrl = list.dataset.reorderUrl;
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (!reorderUrl || !csrfInput) {
            return;
        }

        function setStatus(message, isError) {
            if (!status) {
                return;
            }
            status.textContent = message;
            status.classList.toggle("text-danger", Boolean(isError));
            status.classList.toggle("text-success", !isError && Boolean(message));
        }

        Sortable.create(list, {
            handle: ".drag-handle",
            animation: 160,
            ghostClass: "sortable-ghost",
            chosenClass: "sortable-chosen",
            onEnd: async function () {
                const order = Array.from(list.querySelectorAll("[data-item-id]")).map(
                    function (item) {
                        return Number(item.dataset.itemId);
                    }
                );
                setStatus("Saving order…", false);
                try {
                    const response = await fetch(reorderUrl, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": csrfInput.value,
                        },
                        body: JSON.stringify({ order: order }),
                    });
                    if (!response.ok) {
                        throw new Error("Reorder failed");
                    }
                    setStatus("Order saved", false);
                    window.setTimeout(function () {
                        setStatus("", false);
                    }, 2200);
                } catch (error) {
                    setStatus("Could not save the new order. Refresh and try again.", true);
                }
            },
        });
    });
})();
