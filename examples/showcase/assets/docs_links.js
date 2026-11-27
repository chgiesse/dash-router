// Links inside rendered Markdown are plain <a> tags, so the browser would reload the page.
// Route same-origin app links through the router instead (pushState + the event dcc.Location listens to).
(function () {
    // dcc.Markdown renders headings without ids. Give them GitHub-style ids so `page.md#anchor`
    // links written for GitHub also work in the app.
    function slugify(text) {
        return text.trim().toLowerCase().replace(/[^\w\- ]/g, "").replace(/ /g, "-");
    }

    function addHeadingIds() {
        document.querySelectorAll(".docs-markdown :is(h1, h2, h3, h4):not([id])").forEach(function (h) {
            h.id = slugify(h.textContent || "");
        });
    }

    function scrollToAnchor(anchor) {
        addHeadingIds();
        const target = document.getElementById(decodeURIComponent(anchor));
        if (target) target.scrollIntoView();
        return !!target;
    }

    new MutationObserver(addHeadingIds).observe(document.documentElement, { childList: true, subtree: true });

    document.addEventListener("click", function (e) {
        if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        const a = e.target instanceof Element ? e.target.closest(".docs-markdown a[href]") : null;
        if (!a) return;
        const href = a.getAttribute("href");
        if (!href) return;
        if (href.startsWith("#")) {
            e.preventDefault();
            scrollToAnchor(href.slice(1));
            return;
        }
        if (!href.startsWith("/") || href.startsWith("//")) return;
        if (a.target && a.target !== "_self") return;

        e.preventDefault();
        const hashAt = href.indexOf("#");
        const path = hashAt >= 0 ? href.slice(0, hashAt) : href;
        const anchor = hashAt >= 0 ? href.slice(hashAt + 1) : "";
        if (path === window.location.pathname && anchor) {
            scrollToAnchor(anchor);
            return;
        }
        window.history.pushState({}, "", path);
        window.dispatchEvent(new CustomEvent("_dashprivate_pushstate"));
        window.scrollTo(0, 0);
        if (anchor) {
            // The new page streams in after the click; retry until its heading exists.
            let tries = 0;
            const timer = setInterval(function () {
                if (scrollToAnchor(anchor) || ++tries > 20) clearInterval(timer);
            }, 100);
        }
    });
})();
