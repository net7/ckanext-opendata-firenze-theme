/* home.js — Home.
 *
 * carosello della sezione "In evidenza".
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js" e caricato in
 * fondo al <body> (templates/base.html). Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

  /* Carosello della home: il track scorre; qui aggiungo indicatori a linee,
     disabilito le frecce ai bordi e sincronizzo gli indicatori allo scroll.
     Senza JS resta il solo track scorrevole (niente frecce/indicatori). */
  function initCarousels() {
    var dotLabel = function (carousel, i) {
      var base = carousel.getAttribute("data-dot-label") || "";
      return (base ? base + " " : "") + (i + 1);
    };
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-rtt-carousel]"),
      function (carousel) {
        var track = carousel.querySelector(".rtt-carousel__track");
        var dots = carousel.querySelector("[data-rtt-carousel-dots]");
        var prev = carousel.querySelector("[data-rtt-carousel-prev]");
        var next = carousel.querySelector("[data-rtt-carousel-next]");
        if (!track || !dots || !prev || !next) {
          return;
        }
        // passo di una card (larghezza + gap), misurato dal secondo item
        var step = function () {
          var items = track.children;
          if (items.length > 1) {
            return items[1].offsetLeft - items[0].offsetLeft;
          }
          return track.clientWidth;
        };
        var perView = function () {
          return Math.max(1, Math.round(track.clientWidth / step()));
        };
        var pages = function () {
          return Math.max(1, Math.ceil(track.children.length / perView()));
        };
        var maxScroll = function () {
          return Math.max(0, track.scrollWidth - track.clientWidth);
        };
        var current = function () {
          if (maxScroll() <= 0) {
            return 0;
          }
          if (track.scrollLeft >= maxScroll() - 1) {
            return pages() - 1;
          }
          return Math.min(
            pages() - 1,
            Math.round(track.scrollLeft / (perView() * step()))
          );
        };
        /* Cambio pagina immediato, come il mockup: il suo carosello è una griglia
           che scambia le card, senza animazione. */
        var goTo = function (i) {
          var page = Math.max(0, Math.min(pages() - 1, i));
          track.scrollLeft = Math.min(page * perView() * step(), maxScroll());
        };
        var render = function () {
          var n = pages();
          if (dots.childElementCount !== n) {
            dots.textContent = "";
            for (var i = 0; i < n; i++) {
              var dot = document.createElement("button");
              dot.type = "button";
              dot.setAttribute("aria-label", dotLabel(carousel, i));
              dot.dataset.index = String(i);
              dots.appendChild(dot);
            }
          }
          var c = current();
          Array.prototype.forEach.call(dots.children, function (dot, i) {
            dot.classList.toggle("is-active", i === c);
            if (i === c) {
              dot.setAttribute("aria-current", "true");
            } else {
              dot.removeAttribute("aria-current");
            }
          });
          prev.disabled = track.scrollLeft <= 0;
          next.disabled =
            track.scrollLeft + track.clientWidth >= track.scrollWidth - 1;
        };
        var scheduleRender = function () {
          window.clearTimeout(track._rttCarouselTimer);
          track._rttCarouselTimer = window.setTimeout(render, 80);
        };
        prev.addEventListener("click", function () {
          goTo(current() - 1);
        });
        next.addEventListener("click", function () {
          goTo(current() + 1);
        });
        dots.addEventListener("click", function (event) {
          var dot =
            event.target && event.target.closest
              ? event.target.closest("button")
              : null;
          if (dot) {
            goTo(Number(dot.dataset.index));
          }
        });
        track.addEventListener("scroll", scheduleRender, { passive: true });
        window.addEventListener("resize", scheduleRender);
        carousel.classList.add("is-ready");
        render();
      }
    );
  }

  function init() {
    initCarousels();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
