/* copy.js — pulsanti "Copia"
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js".
 * Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

  function initCopyButtons() {
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-rtt-copy]"),
      function (button) {
        var wrap = button.closest(".rtt-code-wrap");
        var code = wrap ? wrap.querySelector("code") : null;
        var label = button.querySelector("[data-rtt-copy-label]");
        if (!code || !label || !navigator.clipboard) {
          button.hidden = true;
          return;
        }
        var original = label.textContent;
        button.addEventListener("click", function () {
          navigator.clipboard.writeText(code.textContent).then(function () {
            label.textContent =
              button.getAttribute("data-label-copied") || original;
            window.setTimeout(function () {
              label.textContent = original;
            }, 1600);
          });
        });
      }
    );
  }

  function init() {
    initCopyButtons();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
