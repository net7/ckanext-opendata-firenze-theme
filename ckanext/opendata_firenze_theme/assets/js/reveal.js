/* reveal.js — reveal-on-scroll delle sezioni
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js".
 * Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

  function init() {
    if (!document.body || !("IntersectionObserver" in window)) {
      return;
    }
    var reduce =
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    document.documentElement.classList.add("js-reveal");
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-revealed");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px 14% 0px", threshold: 0 }
    );
    var scan = function (root) {
      if (!root.querySelectorAll) {
        return;
      }
      var nodes = root.querySelectorAll(
        ".rtt-reveal:not(.is-revealed), .rtt-stagger:not(.is-revealed)"
      );
      Array.prototype.forEach.call(nodes, function (el) {
        if (reduce) {
          el.classList.add("is-revealed");
          return;
        }
        var rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight * 0.94 && rect.bottom > 0) {
          el.classList.add("reveal-instant", "is-revealed");
        } else {
          io.observe(el);
        }
      });
    };
    scan(document);
    new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        Array.prototype.forEach.call(mutation.addedNodes, function (node) {
          if (node.nodeType === 1) {
            scan(node);
          }
        });
      });
    }).observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
