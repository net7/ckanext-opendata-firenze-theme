/* dropdowns.js — chiusura dei menu a tendina (faccette, ordina, scarica)
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js".
 * Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

  /* Chiude i menu a tendina (faccette, "Ordina per", "Scarica") quando si
     clicca fuori o si preme Escape, come il mockup. La mutua esclusione tra
     faccette e' gia' nativa (attributo `name` sui <details>). */
  function init() {
    var selector = ".rtt-facet[open], .rtt-sort[open], .rtt-download[open]";
    var inside =
      "details[open].rtt-facet, details[open].rtt-sort, details[open].rtt-download";
    var closeAll = function () {
      Array.prototype.forEach.call(
        document.querySelectorAll(selector),
        function (dropdown) {
          dropdown.open = false;
        }
      );
    };
    document.addEventListener("mousedown", function (event) {
      var target = event.target;
      if (!target || !target.closest) {
        closeAll();
        return;
      }
      if (target.closest(inside)) {
        return;
      }
      closeAll();
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeAll();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
