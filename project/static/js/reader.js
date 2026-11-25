/* global ePub */

(function () {
    "use strict";

    const configElement = document.getElementById("reader-config");
    if (!configElement) {
        return;
    }

    const config = JSON.parse(configElement.textContent);
    const csrfInput = document.getElementById("csrf-token");

    const elements = {
        shell: document.getElementById("reader-shell"),
        content: document.getElementById("reader-content"),
        loading: document.getElementById("reader-loading"),
        error: document.getElementById("reader-error"),
        errorMessage: document.getElementById("reader-error-message"),
        saveStatus: document.getElementById("save-status"),
        progressFill: document.getElementById("progress-fill"),
        progressLabel: document.getElementById("progress-label"),
        topProgressLabel: document.getElementById("top-progress-label"),
        progressBar: document.getElementById("reader-progressbar"),
        pdfControls: document.getElementById("pdf-controls"),
        epubControls: document.getElementById("epub-controls"),
        txtControls: document.getElementById("txt-controls"),
        pdfPageInput: document.getElementById("pdf-page-input"),
        pdfPageCount: document.getElementById("pdf-page-count"),
        pdfPrev: document.getElementById("pdf-prev"),
        pdfNext: document.getElementById("pdf-next"),
        pdfZoomLabel: document.getElementById("pdf-zoom-label"),
        epubPrev: document.getElementById("epub-prev"),
        epubNext: document.getElementById("epub-next"),
        fullscreen: document.getElementById("fullscreen-toggle"),
    };

    const state = {
        percent: clamp(Number(config.initialPercent) || 0, 0, 100),
        locator: config.initialLocator || {},
        dirty: false,
        saving: false,
        saveTimer: null,
        lastSaved: "",
        ready: false,
        pdf: null,
        pdfPage: 1,
        pdfZoom: 1,
        pdfRenderTask: null,
        pdfRenderToken: 0,
        epubBook: null,
        rendition: null,
        epubCfi: "",
        locationsReady: false,
        epubFontSize: storedNumber("libra-epub-font", 20, 13, 34),
        txtFontSize: storedNumber("libra-txt-font", 19, 13, 34),
        restoringTxt: false,
        errorShown: false,
    };

    function clamp(value, minimum, maximum) {
        return Math.min(maximum, Math.max(minimum, value));
    }

    function storedNumber(key, fallback, minimum, maximum) {
        try {
            const stored = Number(localStorage.getItem(key));
            if (Number.isFinite(stored) && stored >= minimum && stored <= maximum) {
                return stored;
            }
        } catch (error) {
            /* localStorage may be unavailable */
        }
        return fallback;
    }

    function storeNumber(key, value) {
        try {
            localStorage.setItem(key, String(value));
        } catch (error) {
            /* ignore */
        }
    }

    function updateProgressUI(percent) {
        const value = clamp(Number(percent) || 0, 0, 100);
        const rounded = Math.round(value);
        if (elements.progressFill) {
            elements.progressFill.style.width = value + "%";
        }
        if (elements.progressLabel) {
            elements.progressLabel.textContent = rounded + "%";
        }
        if (elements.topProgressLabel) {
            elements.topProgressLabel.textContent = rounded + "%";
        }
        if (elements.progressBar) {
            elements.progressBar.setAttribute("aria-valuenow", String(rounded));
        }
    }

    function scheduleSave() {
        if (!config.isAuthenticated) {
            return;
        }
        window.clearTimeout(state.saveTimer);
        state.saveTimer = window.setTimeout(flushProgress, 1200);
    }

    function setProgress(percent, locator, persist) {
        state.percent = clamp(Number(percent) || 0, 0, 100);
        state.locator = locator || {};
        updateProgressUI(state.percent);
        if (persist !== false && config.isAuthenticated) {
            state.dirty = true;
            scheduleSave();
        }
    }

    function setSaveStatus(message) {
        if (elements.saveStatus) {
            elements.saveStatus.textContent = message;
        }
    }

    async function flushProgress() {
        if (!config.isAuthenticated || !state.dirty || state.saving || !csrfInput) {
            return;
        }

        const payload = JSON.stringify({
            locator: state.locator,
            percent: Math.round(state.percent * 100) / 100,
        });
        if (payload === state.lastSaved) {
            state.dirty = false;
            return;
        }

        state.saving = true;
        setSaveStatus("Saving…");
        try {
            const response = await fetch(config.progressUrl, {
                method: "POST",
                credentials: "same-origin",
                keepalive: true,
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfInput.value,
                },
                body: payload,
            });
            if (!response.ok) {
                throw new Error("Save failed");
            }
            state.lastSaved = payload;
            state.dirty = false;
            setSaveStatus("Saved");
            window.setTimeout(function () {
                if (elements.saveStatus && elements.saveStatus.textContent === "Saved") {
                    setSaveStatus("");
                }
            }, 2000);
        } catch (error) {
            state.dirty = true;
            setSaveStatus("Not saved — check your connection");
        } finally {
            state.saving = false;
        }
    }

    function showError(message) {
        state.errorShown = true;
        if (elements.loading) {
            elements.loading.hidden = true;
        }
        if (elements.content) {
            elements.content.hidden = true;
        }
        if (elements.error) {
            elements.error.hidden = false;
        }
        if (elements.errorMessage) {
            elements.errorMessage.textContent = message;
        }
    }

    function hideLoading() {
        if (elements.loading) {
            elements.loading.hidden = true;
        }
    }

    function showControls(format) {
        elements.pdfControls.hidden = format !== "pdf";
        elements.epubControls.hidden = format !== "epub";
        elements.txtControls.hidden = format !== "txt";
    }

    /* ---------------------------------------------------------
       PDF
       --------------------------------------------------------- */

    function bindPdfControls() {
        elements.pdfPrev.addEventListener("click", function () {
            goToPdfPage(state.pdfPage - 1);
        });
        elements.pdfNext.addEventListener("click", function () {
            goToPdfPage(state.pdfPage + 1);
        });
        elements.pdfPageInput.addEventListener("change", function () {
            goToPdfPage(Number(elements.pdfPageInput.value));
        });
        elements.pdfPageInput.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                goToPdfPage(Number(elements.pdfPageInput.value));
                elements.pdfPageInput.blur();
            }
        });
        document.getElementById("pdf-zoom-in").addEventListener("click", function () {
            changePdfZoom(0.15);
        });
        document.getElementById("pdf-zoom-out").addEventListener("click", function () {
            changePdfZoom(-0.15);
        });
        document.getElementById("pdf-fit").addEventListener("click", function () {
            state.pdfZoom = 1;
            updatePdfZoomLabel();
            renderPdfPage(state.pdfPage, { persist: false });
        });
        window.addEventListener("resize", debounced(function () {
            if (state.pdf) {
                renderPdfPage(state.pdfPage, { persist: false });
            }
        }, 220));
        document.addEventListener("keydown", function (event) {
            if (event.target.matches("input, textarea, select")) {
                return;
            }
            if (event.key === "ArrowLeft" || event.key === "PageUp") {
                event.preventDefault();
                goToPdfPage(state.pdfPage - 1);
            } else if (event.key === "ArrowRight" || event.key === "PageDown") {
                event.preventDefault();
                goToPdfPage(state.pdfPage + 1);
            }
        });
    }

    function debounced(callback, wait) {
        let timer = null;
        return function () {
            window.clearTimeout(timer);
            timer = window.setTimeout(callback, wait);
        };
    }

    function updatePdfZoomLabel() {
        if (elements.pdfZoomLabel) {
            elements.pdfZoomLabel.textContent = Math.round(state.pdfZoom * 100) + "%";
        }
    }

    function changePdfZoom(delta) {
        state.pdfZoom = clamp(Math.round((state.pdfZoom + delta) * 100) / 100, 0.5, 2.5);
        updatePdfZoomLabel();
        renderPdfPage(state.pdfPage, { persist: false });
    }

    function goToPdfPage(pageNumber) {
        if (!state.pdf) {
            return;
        }
        const target = clamp(
            Math.round(Number(pageNumber) || 1),
            1,
            state.pdf.numPages
        );
        if (target !== state.pdfPage) {
            renderPdfPage(target, { persist: true });
        } else {
            elements.pdfPageInput.value = target;
        }
    }

    async function renderPdfPage(pageNumber, options) {
        if (!state.pdf) {
            return;
        }
        const page = clamp(
            Math.round(Number(pageNumber) || 1),
            1,
            state.pdf.numPages
        );
        const token = ++state.pdfRenderToken;

        if (state.pdfRenderTask) {
            try {
                state.pdfRenderTask.cancel();
            } catch (error) {
                /* already finished */
            }
        }

        try {
            const pdfPage = await state.pdf.getPage(page);
            if (token !== state.pdfRenderToken) {
                return;
            }

            const unscaled = pdfPage.getViewport({ scale: 1 });
            const horizontalPadding = window.innerWidth < 768 ? 24 : 48;
            const available = Math.max(
                280,
                elements.content.clientWidth - horizontalPadding
            );
            const fitScale = available / unscaled.width;
            const viewport = pdfPage.getViewport({
                scale: Math.max(0.2, fitScale * state.pdfZoom),
            });
            const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);

            let canvas = elements.content.querySelector("canvas");
            if (!canvas) {
                canvas = document.createElement("canvas");
                elements.content.appendChild(canvas);
            }

            canvas.width = Math.floor(viewport.width * pixelRatio);
            canvas.height = Math.floor(viewport.height * pixelRatio);
            canvas.style.width = Math.floor(viewport.width) + "px";
            canvas.style.height = Math.floor(viewport.height) + "px";

            const context = canvas.getContext("2d", { alpha: false });
            context.save();
            context.fillStyle = "#ffffff";
            context.fillRect(0, 0, canvas.width, canvas.height);
            context.restore();

            state.pdfRenderTask = pdfPage.render({
                canvasContext: context,
                viewport: viewport,
                transform: pixelRatio !== 1 ? [pixelRatio, 0, 0, pixelRatio, 0, 0] : null,
            });
            await state.pdfRenderTask.promise;

            if (token !== state.pdfRenderToken) {
                return;
            }

            state.pdfPage = page;
            elements.pdfPageInput.value = page;
            elements.pdfPageInput.max = state.pdf.numPages;
            elements.pdfPageCount.textContent = state.pdf.numPages;
            elements.pdfPrev.disabled = page <= 1;
            elements.pdfNext.disabled = page >= state.pdf.numPages;
            elements.content.scrollTop = 0;

            if (!state.ready) {
                state.ready = true;
                hideLoading();
            }

            setProgress(
                (page / state.pdf.numPages) * 100,
                { kind: "pdf", page: page },
                Boolean(options && options.persist)
            );
        } catch (error) {
            if (error && (error.name === "RenderingCancelledException" || error.name === "AbortException")) {
                return;
            }
            if (token === state.pdfRenderToken) {
                console.error(error);
                showError("This PDF could not be rendered. It may be damaged or password-protected.");
            }
        }
    }

    async function initPdf() {
        const pdfjs = await import(config.pdfLibUrl);
        pdfjs.GlobalWorkerOptions.workerSrc = config.pdfWorkerUrl;

        const loadingTask = pdfjs.getDocument({
            url: config.fileUrl,
            standardFontDataUrl: config.pdfStandardFontsUrl,
        });
        state.pdf = await loadingTask.promise;

        const initialPage = clamp(
            Number(config.initialLocator && config.initialLocator.page) || 1,
            1,
            state.pdf.numPages
        );
        state.pdfPage = initialPage;
        elements.content.classList.add("reader-content--pdf");
        bindPdfControls();
        updatePdfZoomLabel();
        await renderPdfPage(initialPage, { persist: false });
    }

    /* ---------------------------------------------------------
       EPUB
       --------------------------------------------------------- */

    function epubThemeColors() {
        const dark = document.documentElement.getAttribute("data-bs-theme") === "dark";
        return dark
            ? { background: "#1a201c", color: "#ece6d8", link: "#86b7a5" }
            : { background: "#fffdf8", color: "#1f2a24", link: "#2f5d50" };
    }

    function applyEpubThemeToDocument(doc) {
        if (!doc || !doc.head) {
            return;
        }
        const colors = epubThemeColors();
        let style = doc.getElementById("libra-reader-theme");
        if (!style) {
            style = doc.createElement("style");
            style.id = "libra-reader-theme";
            doc.head.appendChild(style);
        }
        style.textContent = [
            "html, body { background: " + colors.background + " !important; }",
            "body, body * { color: " + colors.color + " !important; }",
            "a, a * { color: " + colors.link + " !important; }",
            "img, svg { max-width: 100% !important; height: auto !important; }",
        ].join("\n");
        try {
            doc.documentElement.style.background = colors.background;
        } catch (error) {
            /* ignore */
        }
    }

    function applyEpubTheme() {
        if (!state.rendition) {
            return;
        }
        state.rendition.getContents().forEach(function (contents) {
            applyEpubThemeToDocument(contents.document);
        });
    }

    function updateEpubPercentFromLocation(location, persistOverride) {
        if (!location || !location.start) {
            return;
        }
        const cfi = location.start.cfi;
        if (!cfi) {
            return;
        }
        state.epubCfi = cfi;
        let percent;
        if (
            state.locationsReady &&
            state.epubBook.locations &&
            state.epubBook.locations.length()
        ) {
            percent = state.epubBook.locations.percentageFromCfi(cfi) * 100;
        } else {
            const index = Number(location.start.index) || 0;
            const total = (state.epubBook.spine && state.epubBook.spine.length) || 1;
            percent = (index / total) * 100;
        }
        setProgress(
            percent,
            { kind: "epub", cfi: cfi },
            persistOverride === undefined ? state.ready : persistOverride
        );
        if (elements.epubPrev) {
            elements.epubPrev.disabled = Boolean(location.atStart);
        }
        if (elements.epubNext) {
            elements.epubNext.disabled = Boolean(location.atEnd);
        }
    }

    function applyEpubFontSize() {
        if (state.rendition) {
            state.rendition.themes.fontSize(state.epubFontSize + "px");
        }
    }

    function changeEpubFont(delta) {
        state.epubFontSize = clamp(state.epubFontSize + delta, 13, 34);
        storeNumber("libra-epub-font", state.epubFontSize);
        applyEpubFontSize();
    }

    async function initEpub() {
        if (typeof window.ePub !== "function") {
            throw new Error("EPUB reader library did not load.");
        }
        elements.content.classList.add("reader-content--epub");

        // Fetch the archive ourselves. ePub.js infers the input type from the URL
        // suffix, and our authenticated file endpoint has no ".epub" extension.
        const response = await fetch(config.fileUrl, { credentials: "same-origin" });
        if (!response.ok) {
            throw new Error("The EPUB file could not be downloaded.");
        }
        const archive = await response.arrayBuffer();
        state.epubBook = window.ePub(archive);
        state.rendition = state.epubBook.renderTo(elements.content, {
            width: "100%",
            height: "100%",
            flow: "paginated",
            spread: "auto",
            minSpreadWidth: 820,
			allowScriptedContent: false,
        });

        state.rendition.hooks.content.register(function (contents) {
            applyEpubThemeToDocument(contents.document);
            try {
                contents.document.addEventListener("keydown", function (event) {
                    if (event.key === "ArrowLeft") {
                        state.rendition.prev();
                    } else if (event.key === "ArrowRight") {
                        state.rendition.next();
                    }
                });
            } catch (error) {
                /* ignore */
            }
            applyEpubFontSize();
        });

        state.rendition.on("relocated", updateEpubPercentFromLocation);

        document.getElementById("epub-prev").addEventListener("click", function () {
            state.rendition.prev();
        });
        document.getElementById("epub-next").addEventListener("click", function () {
            state.rendition.next();
        });
        document.getElementById("epub-font-down").addEventListener("click", function () {
            changeEpubFont(-1);
        });
        document.getElementById("epub-font-up").addEventListener("click", function () {
            changeEpubFont(1);
        });

        document.addEventListener("libra:themechange", applyEpubTheme);

        await state.epubBook.ready;
        applyEpubFontSize();

        state.epubBook.locations
            .generate(1600)
            .then(function () {
                state.locationsReady = true;
                if (state.epubCfi) {
                    const percent =
                        state.epubBook.locations.percentageFromCfi(state.epubCfi) * 100;
                    if (Number.isFinite(percent)) {
                        state.percent = clamp(percent, 0, 100);
                        updateProgressUI(state.percent);
                    }
                }
            })
            .catch(function () {
                /* location generation is an enhancement; reading still works */
            });

        const initialCfi =
            config.initialLocator && typeof config.initialLocator.cfi === "string"
                ? config.initialLocator.cfi
                : "";
        try {
            await state.rendition.display(initialCfi || undefined);
        } catch (error) {
            if (initialCfi) {
                await state.rendition.display();
            } else {
                throw error;
            }
        }

        state.ready = true;
        hideLoading();

        const current = state.rendition.currentLocation();
        if (current && current.start) {
            updateEpubPercentFromLocation(current, false);
        } else {
            setProgress(state.percent, state.locator, false);
        }
    }

    /* ---------------------------------------------------------
       TXT
       --------------------------------------------------------- */

    function applyTxtFontSize() {
        const article = elements.content.querySelector(".txt-reader");
        if (article) {
            article.style.setProperty("--reader-font-size", state.txtFontSize + "px");
        }
    }

    function txtMaxScroll() {
        return Math.max(1, elements.content.scrollHeight - elements.content.clientHeight);
    }

    function restoreTxtPosition(ratio) {
        state.restoringTxt = true;
        window.requestAnimationFrame(function () {
            window.requestAnimationFrame(function () {
                elements.content.scrollTop = ratio * txtMaxScroll();
                window.setTimeout(function () {
                    state.restoringTxt = false;
                }, 160);
            });
        });
    }

    function changeTxtFont(delta) {
        const ratio = elements.content.scrollTop / txtMaxScroll();
        state.txtFontSize = clamp(state.txtFontSize + delta, 13, 34);
        storeNumber("libra-txt-font", state.txtFontSize);
        applyTxtFontSize();
        restoreTxtPosition(ratio);
    }

    async function initTxt() {
        const response = await fetch(config.fileUrl, { credentials: "same-origin" });
        if (!response.ok) {
            throw new Error("The text file could not be downloaded.");
        }
        const text = await response.text();
        elements.content.classList.add("reader-content--txt");

        const article = document.createElement("article");
        article.className = "txt-reader";
        article.textContent = text;
        elements.content.appendChild(article);
        applyTxtFontSize();

        const initialRatio = clamp(
            Number(config.initialLocator && config.initialLocator.ratio) || 0,
            0,
            1
        );
        restoreTxtPosition(initialRatio);
        setProgress(initialRatio * 100, { kind: "txt", ratio: initialRatio }, false);

        const handleScroll = debounced(function () {
            if (state.restoringTxt) {
                return;
            }
            const ratio = clamp(elements.content.scrollTop / txtMaxScroll(), 0, 1);
            setProgress(ratio * 100, { kind: "txt", ratio: Math.round(ratio * 1000000) / 1000000 }, true);
        }, 300);
        elements.content.addEventListener("scroll", handleScroll, { passive: true });

        document.getElementById("txt-font-down").addEventListener("click", function () {
            changeTxtFont(-1);
        });
        document.getElementById("txt-font-up").addEventListener("click", function () {
            changeTxtFont(1);
        });

        document.addEventListener("keydown", function (event) {
            if (event.target.matches("input, textarea, select")) {
                return;
            }
            if (event.key === "ArrowDown" || event.key === "PageDown") {
                event.preventDefault();
                elements.content.scrollBy({ top: elements.content.clientHeight * 0.82, behavior: "smooth" });
            } else if (event.key === "ArrowUp" || event.key === "PageUp") {
                event.preventDefault();
                elements.content.scrollBy({ top: -elements.content.clientHeight * 0.82, behavior: "smooth" });
            }
        });

        state.ready = true;
        hideLoading();
    }

    /* ---------------------------------------------------------
       Shared UI
       --------------------------------------------------------- */

    function bindFullscreen() {
        if (!elements.fullscreen || !elements.shell) {
            return;
        }
        elements.fullscreen.addEventListener("click", async function () {
            try {
                if (!document.fullscreenElement) {
                    await elements.shell.requestFullscreen();
                } else {
                    await document.exitFullscreen();
                }
            } catch (error) {
                /* fullscreen may be unavailable */
            }
        });
        document.addEventListener("fullscreenchange", function () {
            const icon = elements.fullscreen.querySelector("i");
            if (icon) {
                icon.className = document.fullscreenElement
                    ? "bi bi-fullscreen-exit"
                    : "bi bi-arrows-fullscreen";
            }
        });
    }

    async function start() {
        showControls(config.format);
        bindFullscreen();
        updateProgressUI(state.percent);

        window.addEventListener("pagehide", function () {
            if (state.dirty) {
                flushProgress();
            }
        });
        document.addEventListener("visibilitychange", function () {
            if (document.visibilityState === "hidden" && state.dirty) {
                flushProgress();
            }
        });

        try {
            if (config.format === "pdf") {
                await initPdf();
            } else if (config.format === "epub") {
                await initEpub();
            } else if (config.format === "txt") {
                await initTxt();
            } else {
                throw new Error("Unsupported format.");
            }
        } catch (error) {
            console.error(error);
            const message =
                config.format === "epub"
                    ? "This EPUB could not be opened. It may be damaged or use an unsupported layout."
                    : config.format === "pdf"
                      ? "This PDF could not be opened. It may be damaged or password-protected."
                      : "This text file could not be opened.";
            showError(message);
        }
    }

    start();
})();
