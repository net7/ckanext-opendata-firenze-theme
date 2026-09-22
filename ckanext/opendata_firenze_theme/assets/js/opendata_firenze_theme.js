/* opendata_firenze_theme
 *
 * Comportamenti dello shell: header a scomparsa, menu mobile, selettore lingua,
 * reveal-on-scroll. Caricato in fondo al <body> (templates/base.html).
 */
(function () {
  "use strict";

  function initReveal() {
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

  function initHeader() {
    var header = document.querySelector("[data-rtt-header]");
    if (!header) {
      return;
    }
    var reduce =
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var hidden = false;
    var last = Math.max(0, window.scrollY);
    var acc = 0;
    var raf = 0;
    var threshold = 18;

    var setHidden = function (value) {
      if (value === hidden) {
        return;
      }
      hidden = value;
      header.classList.toggle("is-hidden", value);
    };

    if (!reduce) {
      window.addEventListener(
        "scroll",
        function () {
          if (raf) {
            return;
          }
          raf = window.requestAnimationFrame(function () {
            var y = Math.max(0, window.scrollY);
            var dy = y - last;
            if (dy > 0 !== acc > 0) {
              acc = 0;
            }
            acc += dy;
            if (y < 96) {
              setHidden(false);
              acc = 0;
            } else if (acc > threshold) {
              setHidden(true);
              acc = 0;
            } else if (acc < -threshold) {
              setHidden(false);
              acc = 0;
            }
            last = y;
            raf = 0;
          });
        },
        { passive: true }
      );
    }

    var toggle = header.querySelector("[data-rtt-menu-toggle]");
    var mobileNav = header.querySelector("[data-rtt-mobile-nav]");
    if (!toggle || !mobileNav) {
      return;
    }

    var setMenu = function (open) {
      mobileNav.classList.toggle("is-open", open);
      toggle.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute(
        "aria-label",
        open
          ? toggle.getAttribute("data-label-close")
          : toggle.getAttribute("data-label-open")
      );
      document.documentElement.classList.toggle("rtt-nav-open", open);
      if (open) {
        setHidden(false);
      }
    };

    toggle.addEventListener("click", function () {
      setMenu(!mobileNav.classList.contains("is-open"));
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && mobileNav.classList.contains("is-open")) {
        setMenu(false);
        toggle.focus();
      }
    });

    /* Soglia desktop condivisa con la CSS (max-width:1024px in
       assets/css/opendata_firenze_theme.css): se cambia qui va cambiata anche lì. */
    var desktop = window.matchMedia("(min-width: 1025px)");
    var onDesktop = function (event) {
      if (event.matches) {
        setMenu(false);
      }
    };
    if (desktop.addEventListener) {
      desktop.addEventListener("change", onDesktop);
    }
  }

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

  /* Chiude i menu a tendina delle faccette e dell'"Ordina per" quando si clicca
     fuori o si preme Escape, come il mockup. La mutua esclusione tra faccette
     e' gia' nativa (attributo `name` sui <details>). */
  function initFacetDismiss() {
    var closeAll = function () {
      Array.prototype.forEach.call(
        document.querySelectorAll(".rtt-facet[open], .rtt-sort[open]"),
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
      if (target.closest("details[open].rtt-facet, details[open].rtt-sort")) {
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

  function init() {
    initReveal();
    initHeader();
    initChipRemove();
    initFacetDismiss();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
