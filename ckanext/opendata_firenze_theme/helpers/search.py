"""Ricerca site-wide: dataset (evidenze), news e pagine.

Il module produce un valore unico (`q` + `groups`) che la view passa al
template; ogni gruppo ha la stessa forma (`id`, `title`, `entries`, `kind`) e
il template si limita a iterarlo. La ricerca del catalogo passa da
`_common._search(view=True)`, che entra nell'azione e quindi nel fallback fuzzy
di `helpers.catalog_search`.
"""

import ckan.plugins.toolkit as toolkit

from . import _common, content


def _dataset_group(query, data):
    items = data.get("results") or []
    if not items:
        return None
    return {
        "id": "datasets",
        "title": toolkit._("Dataset"),
        "count": data.get("count") or 0,
        "all_url": toolkit.url_for("dataset.search", q=query),
        "all_label": toolkit._("Vedi tutti i dataset"),
        "note": (
            toolkit._("Nessun risultato esatto: sono mostrati i dataset con termini simili.")
            if data.get("odf_fuzzy")
            else ""
        ),
        "entries": items,
        "kind": "dataset",
    }


def _news_group(items):
    if not items:
        return None
    return {
        "id": "news",
        "title": toolkit._("News"),
        "all_url": toolkit.url_for("pages.blog_index"),
        "all_label": toolkit._("Tutte le news"),
        "entries": items,
        "kind": "news",
    }


def _pages_group(items):
    if not items:
        return None
    return {
        "id": "pages",
        "title": toolkit._("Pagine"),
        "entries": items,
        "kind": "page",
    }


def odf_site_search(query, dataset_limit=12, content_limit=6):
    """Risultati della ricerca site-wide per `query`.

    I dataset passano da `package_search` (con fallback fuzzy nel wrapper
    dell'azione); news e pagine dall'adapter `content`.
    """
    query = (query or "").strip()
    if not query:
        return {"q": "", "groups": []}

    datasets = _common._search(
        view=True,
        q=query,
        rows=dataset_limit,
        facet=False,
        sort="score desc, metadata_modified desc",
    )
    items = content.search_content(query)
    groups = [
        _dataset_group(query, datasets),
        _news_group([item for item in items if item["kind"] == "news"][:content_limit]),
        _pages_group([item for item in items if item["kind"] == "page"][:content_limit]),
    ]
    return {"q": query, "groups": [group for group in groups if group]}


# La ricerca site-wide è chiamata dalla view, non dai template: non è un
# helper da registrare in ITemplateHelpers.
HELPERS = {}
