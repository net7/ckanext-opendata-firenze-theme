/* preview.js — modale "Vedi anteprima"
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js".
 * Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

  function initResourcePreview() {
    var dialog = document.querySelector("[data-rtt-preview-modal]");
    if (!dialog || typeof dialog.showModal !== "function") {
      return;
    }
    var chip = dialog.querySelector("[data-rtt-preview-chip]");
    var title = dialog.querySelector("[data-rtt-preview-title]");
    var iframe = dialog.querySelector("[data-rtt-preview-iframe]");
    var empty = dialog.querySelector("[data-rtt-preview-empty]");
    var download = dialog.querySelector("[data-rtt-preview-download]");
    var full = dialog.querySelector("[data-rtt-preview-full]");

    Array.prototype.forEach.call(
      dialog.querySelectorAll("[data-rtt-preview-close]"),
      function (button) {
        button.addEventListener("click", function () {
          dialog.close();
        });
      }
    );
    // Clic sul backdrop (il target è il <dialog> stesso): chiude.
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) {
        dialog.close();
      }
    });
    // Alla chiusura azzera la src e ripristina lo scroll della pagina.
    dialog.addEventListener("close", function () {
      document.body.style.overflow = "";
      if (iframe) {
        iframe.removeAttribute("src");
        iframe.hidden = true;
      }
    });

    Array.prototype.forEach.call(
      document.querySelectorAll("[data-rtt-preview]"),
      function (button) {
        button.addEventListener("click", function (event) {
          event.preventDefault();
          var name = button.getAttribute("data-preview-name") || "";
          var format = button.getAttribute("data-preview-format") || "";
          var geo = button.getAttribute("data-preview-geo") === "true";
          var view = button.getAttribute("data-preview-view") || "";
          var fullUrl = button.getAttribute("data-preview-full") || "#";
          var downloadUrl = button.getAttribute("data-preview-download") || "";

          if (title) {
            title.textContent = name;
          }
          if (chip) {
            chip.textContent = format;
            chip.classList.toggle("rtt-format-chip--geo", geo);
            chip.classList.toggle("rtt-format-chip--neutral", !geo);
            chip.hidden = !format;
          }
          if (full) {
            full.setAttribute("href", fullUrl);
          }
          if (download) {
            // Il download è il fallback dello stato vuoto: con una vista
            // l'anteprima basta (il mockup non ha il bottone nel modale).
            if (!view && downloadUrl) {
              download.setAttribute("href", downloadUrl);
              download.hidden = false;
            } else {
              download.hidden = true;
            }
          }
          if (iframe && view) {
            iframe.setAttribute("title", name);
            iframe.setAttribute("src", view);
            iframe.hidden = false;
            if (empty) {
              empty.hidden = true;
            }
          } else {
            if (iframe) {
              iframe.hidden = true;
            }
            if (empty) {
              empty.hidden = false;
            }
          }
          dialog.showModal();
          // Blocca lo scroll della pagina dietro (come nel mockup).
          document.body.style.overflow = "hidden";
        });
      }
    );
  }

  function init() {
    initResourcePreview();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
