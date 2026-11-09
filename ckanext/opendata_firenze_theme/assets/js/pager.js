/* pager.js — etichette accessibili del pager CKAN
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js".
 * Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

  /* Il pager di CKAN usa link icona ("«"/"»") senza nome accessibile: lo
     aggiungo dai data-* del contenitore e marco la pagina corrente. */
  function init() {
    var holder = document.querySelector("[data-rtt-pager-labels]");
    if (!holder) {
      return;
    }
    var byIcon = {
      "fa-chevron-left": holder.getAttribute("data-label-prev"),
      "fa-chevron-right": holder.getAttribute("data-label-next"),
    };
    Array.prototype.forEach.call(
      document.querySelectorAll(".pagination .page-link"),
      function (link) {
        var icon = link.querySelector("i");
        Object.keys(byIcon).forEach(function (cls) {
          if (
            byIcon[cls] &&
            icon &&
            icon.classList.contains(cls) &&
            !link.textContent.trim()
          ) {
            link.setAttribute("aria-label", byIcon[cls]);
          }
        });
      }
    );
    Array.prototype.forEach.call(
      document.querySelectorAll(".pagination .page-item.active > .page-link"),
      function (link) {
        link.setAttribute("aria-current", "page");
      }
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
