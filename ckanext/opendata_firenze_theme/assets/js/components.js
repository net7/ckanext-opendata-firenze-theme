/* components.js — Componenti riusabili.
 *
 * rimozione dei chip, pulsanti "Copia" dei blocchi di codice e link
 * segnaposto.
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js" e caricato in
 * fondo al <body> (templates/base.html). Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

  /* Chip dismissibili: un click su [data-rtt-chip-remove] rimuove il chip dal
     DOM e notifica i consumer con un evento "rtt-chip-remove" (bubbling,
     cancelable: `preventDefault()` annulla la rimozione), emesso prima della
     rimozione. Dopo la rimozione il focus passa al chip rimovibile successivo
     (o al precedente), così la navigazione da tastiera non torna a <body>.
     Per i filtri che devono aggiornare l'URL si usa la variante <a href> del
     macro (remove_href), che funziona anche senza JS. */
  function initChipRemove() {
    document.addEventListener("click", function (event) {
      var target = event.target;
      var button =
        target && target.closest
          ? target.closest("[data-rtt-chip-remove]")
          : null;
      if (!button) {
        return;
      }
      var chip = button.closest(".rtt-chip");
      if (!chip || !chip.parentNode) {
        return;
      }
      event.preventDefault();
      var buttons = Array.prototype.slice.call(
        chip.parentNode.querySelectorAll("[data-rtt-chip-remove]")
      );
      var index = buttons.indexOf(button);
      var next =
        index > -1 ? buttons[index + 1] || buttons[index - 1] || null : null;
      var labelNode = chip.querySelector(".rtt-chip__label");
      var remove = chip.dispatchEvent(
        new CustomEvent("rtt-chip-remove", {
          bubbles: true,
          cancelable: true,
          detail: {
            label: labelNode ? labelNode.textContent.trim() : "",
            chip: chip,
          },
        })
      );
      if (!remove || !chip.parentNode) {
        return;
      }
      chip.parentNode.removeChild(chip);
      if (next && next.isConnected && next.focus) {
        next.focus();
      }
    });
  }

  /* Pulsante "Copia" dei blocchi di codice (pagina Sviluppatori). Senza
     clipboard API il pulsante viene nascosto. */
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

  /* Link segnaposto (LodView/LodLive, endpoint SPARQL, archivi nazionali): non
     hanno ancora una destinazione, quindi il click non deve saltare in cima
     alla pagina. Restano nel DOM come nel mockup, con un title esplicativo. */
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
    initChipRemove();
    initCopyButtons();
    initPlaceholderLinks();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
