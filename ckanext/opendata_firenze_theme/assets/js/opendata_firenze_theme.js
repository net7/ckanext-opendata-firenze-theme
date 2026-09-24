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

  /* "Mostra tutto/meno" della descrizione del dataset: toglie/rimette il clamp
     a 3 righe. Il testo completo resta comunque nei Metadati avanzati. */
  function initLineClamp() {
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-rtt-line-clamp]"),
      function (button) {
        var target = document.getElementById(
          button.getAttribute("aria-controls")
        );
        if (!target) {
          return;
        }
        var label = button.querySelector("[data-rtt-clamp-label]");
        button.addEventListener("click", function () {
          var clamped = target.classList.toggle("is-clamped");
          button.setAttribute("aria-expanded", clamped ? "false" : "true");
          if (label) {
            label.textContent = clamped
              ? button.getAttribute("data-label-more")
              : button.getAttribute("data-label-less");
          }
        });
      }
    );
  }

  /* Console SQL della scheda dataset: esegue la query in sola lettura via
     datastore_search_sql e mostra le prime righe. Endpoint pubblico, nessun
     segreto; il server rifiuta le query di scrittura. La query viaggia in POST
     (niente limiti di lunghezza URL / query nei log) e la richiesta precedente
     viene annullata, così vince sempre l'ultima query lanciata. */
  function initSqlConsole() {
    var run = document.querySelector("[data-rtt-sql-run]");
    var box = document.querySelector("[data-rtt-sql]");
    var out = document.querySelector("[data-rtt-sql-result]");
    if (!run || !box || !out) {
      return;
    }
    var base = run.getAttribute("data-rtt-api") || "/api/3/action";
    // Messaggio d'errore tradotto dal template (l'IIFE non ha accesso a this._()).
    var errorText = out.getAttribute("data-rtt-sql-error") || "";
    // CKAN protegge dal CSRF le POST con sessione (le richieste con API token
    // sono esenti): il token sta nei <meta> emessi dal base.html di CKAN.
    var csrfField = document.querySelector('meta[name="csrf_field_name"]');
    var csrfMeta = csrfField
      ? document.querySelector(
          'meta[name="' + csrfField.getAttribute("content") + '"]'
        )
      : null;
    var csrfToken = csrfMeta ? csrfMeta.getAttribute("content") : "";
    var pending = null;
    var render = function (payload) {
      out.replaceChildren();
      if (!payload || !payload.success) {
        var p = document.createElement("p");
        p.className = "rtt-api__error";
        p.textContent =
          (payload && payload.error && payload.error.message) || errorText;
        out.appendChild(p);
        return;
      }
      var result = payload.result || {};
      var fields = result.fields || [];
      var records = result.records || [];
      var table = document.createElement("table");
      var thead = document.createElement("thead");
      var htr = document.createElement("tr");
      fields.forEach(function (field) {
        var th = document.createElement("th");
        th.textContent = field.id;
        htr.appendChild(th);
      });
      thead.appendChild(htr);
      table.appendChild(thead);
      var tbody = document.createElement("tbody");
      records.slice(0, 20).forEach(function (record) {
        var tr = document.createElement("tr");
        fields.forEach(function (field) {
          var td = document.createElement("td");
          td.textContent =
            record[field.id] == null ? "" : String(record[field.id]);
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      out.appendChild(table);
    };
    run.addEventListener("click", function () {
      out.hidden = false;
      out.textContent = "…";
      if (pending) {
        pending.abort();
      }
      pending = new AbortController();
      var headers = {
        Accept: "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
      };
      if (csrfToken) {
        headers["X-CSRFToken"] = csrfToken;
      }
      fetch(base + "/datastore_search_sql", {
        method: "POST",
        headers: headers,
        body: new URLSearchParams({ sql: box.value }).toString(),
        signal: pending.signal,
      })
        .then(function (response) {
          return response.json();
        })
        .then(render)
        .catch(function (error) {
          if (error && error.name === "AbortError") {
            return;
          }
          render(null);
        });
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
    initReveal();
    initHeader();
    initChipRemove();
    initFacetDismiss();
    initLineClamp();
    initSqlConsole();
    initCommentCounter();
    initContactTipo();
    initCopyButtons();
    initPagerLabels();
    initCarousels();
    initPlaceholderLinks();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
