/* dataset.js — Scheda dataset.
 *
 * "Mostra tutto/meno" della descrizione, console SQL (datastore_search_sql) e
 * modale "Vedi anteprima" della risorsa (widget CKAN).
 *
 * IIFE autonomo, incluso nel bundle "opendata_firenze_theme-js" e caricato in
 * fondo al <body> (templates/base.html). Senza JS la pagina resta usabile.
 */
(function () {
  "use strict";

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

  /* Modale "Vedi anteprima" (ResourcePreviewModal del mockup): apre un
     <dialog> con il widget CKAN della risorsa, senza navigare alla scheda
     risorsa. Se la risorsa non ha viste, mostra lo stato vuoto con il
     download. Un solo <dialog> per pagina, popolato dai data-* del bottone. */
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
    initLineClamp();
    initSqlConsole();
    initResourcePreview();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
