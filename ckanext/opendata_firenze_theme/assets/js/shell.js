/* shell.js — Shell e stati globali del tema.
 *
 * reveal-on-scroll, header a scomparsa, menu mobile, chiusura dropdown e
 * etichette accessibili del pager di CKAN.
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js" e caricato in
 * fondo al <body> (templates/base.html). Senza JS la pagina resta usabile.
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

  /* Chiude i menu a tendina (faccette, "Ordina per", "Scarica") quando si
     clicca fuori o si preme Escape, come il mockup. La mutua esclusione tra
     faccette e' gia' nativa (attributo `name` sui <details>). */
  function initFacetDismiss() {
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

  /* Il pager di CKAN usa link icona ("«"/"»") senza nome accessibile: lo
     aggiungo dai data-* del contenitore e marco la pagina corrente. */
  function initPagerLabels() {
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

  function init() {
    initReveal();
    initHeader();
    initFacetDismiss();
    initPagerLabels();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
