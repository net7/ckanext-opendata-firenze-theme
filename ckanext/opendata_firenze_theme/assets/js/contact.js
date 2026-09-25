/* contact.js — Form Collaborazione.
 *
 * contatore caratteri ed etichetta/placeholder del campo richiesta in base
 * al tipo scelto.
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js" e caricato in
 * fondo al <body> (templates/base.html). Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

  /* Contatore caratteri della richiesta (form Collaborazione). Senza JS resta
     la sola nota senza conteggio. */
  function initCommentCounter() {
    var field = document.querySelector("[data-rtt-counter-field]");
    var box = document.querySelector("[data-rtt-counter]");
    var value = document.querySelector("[data-rtt-counter-value]");
    if (!field || !box || !value) {
      return;
    }
    var update = function () {
      value.textContent = String(field.value.length);
    };
    box.hidden = false;
    field.addEventListener("input", update);
    update();
  }

  /* Form Collaborazione: etichetta e placeholder del campo richiesta seguono il
     tipo scelto. I testi arrivano dai data-* dei radio (già tradotti lato
     server), così non serve alcuna stringa i18n nel JS. Senza JS restano quelli
     del tipo selezionato lato server. */
  function initContactTipo() {
    var label = document.querySelector("[data-rtt-tipo-label]");
    var field = document.querySelector("[data-rtt-counter-field]");
    var radios = document.querySelectorAll("[data-rtt-tipo]");
    if (!label || !field || !radios.length) {
      return;
    }
    var sync = function () {
      Array.prototype.forEach.call(radios, function (radio) {
        if (!radio.checked) {
          return;
        }
        label.textContent =
          radio.getAttribute("data-text-label") || label.textContent;
        field.setAttribute(
          "placeholder",
          radio.getAttribute("data-placeholder") || ""
        );
      });
    };
    Array.prototype.forEach.call(radios, function (radio) {
      radio.addEventListener("change", sync);
    });
    sync();
  }

  function init() {
    initCommentCounter();
    initContactTipo();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
