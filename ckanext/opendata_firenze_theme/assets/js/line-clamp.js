/* line-clamp.js — descrizione: mostra tutto/meno
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js".
 * Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

  function initLineClamp() {
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-rtt-line-clamp]"),
      function (button) {
        var target = document.getElementById(
          button.getAttribute("aria-controls")
        );
        if (!target) {
          return;
        }
        var label = button.querySelector("[data-rtt-clamp-label]");
        button.addEventListener("click", function () {
          var clamped = target.classList.toggle("is-clamped");
          button.setAttribute("aria-expanded", clamped ? "false" : "true");
          if (label) {
            label.textContent = clamped
              ? button.getAttribute("data-label-more")
              : button.getAttribute("data-label-less");
          }
        });
      }
    );
  }

  function init() {
    initLineClamp();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
