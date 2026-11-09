/* chips.js — chip rimovibili e gestione del focus
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js".
 * Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

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

  function init() {
    initChipRemove();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
