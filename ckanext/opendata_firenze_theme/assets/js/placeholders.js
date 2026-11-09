/* placeholders.js — link segnaposto
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js".
 * Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

  function initPlaceholderLinks() {
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-rtt-placeholder]"),
      function (link) {
        link.addEventListener("click", function (event) {
          event.preventDefault();
        });
      }
    );
  }

  function init() {
    initPlaceholderLinks();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
