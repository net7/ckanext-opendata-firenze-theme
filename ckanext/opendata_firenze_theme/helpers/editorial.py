"""Helper delle pagine editoriali: Annuario (capitoli) e news."""

from . import _common, query
from .constants import ANNUARIO_CHAPTERS


def odf_annuario_chapters():
    """I 13 capitoli dell'Annuario (indice 1-based + nome).

    Nessuna query: il conteggio per capitolo si chiede a `odf_annuario_count`
    solo per il capitolo visualizzato. Il facet `extras_capitolo` di Solr è
    tokenizzato (restituisce le singole parole: "ambient", "territorio"), quindi
    non può dare il numero di dataset di un capitolo.
    """
    return [{"index": index, "name": name} for index, name in enumerate(ANNUARIO_CHAPTERS, start=1)]


def odf_annuario_count(chapter):
    """Numero di dataset di un capitolo dell'Annuario (extra `capitolo`).

    Il campo `extras_capitolo` è tokenizzato in Solr: il conteggio va fatto con
    una query sul valore esatto del capitolo (0 se il capitolo è vuoto/assente).
    """
    if not chapter:
        return 0
    return _common._search(rows=0, fq=query.chapter(chapter))["count"]


def odf_annuario_datasets(chapter, limit=None):
    """Dataset del capitolo dell'Annuario (extra `capitolo`), per titolo.

    Con `limit=None` mostra tutti i dataset del capitolo (cap di sicurezza a 200),
    così il numero di card coincide col conteggio mostrato.
    """
    if not chapter:
        return []
    rows = limit if limit is not None else 200
    data = _common._search(rows=rows, fq=query.chapter(chapter), sort="title_string asc")
    return data["results"]


def odf_annuario_page(chapter=None):
    """Dati della pagina Annuario per il capitolo richiesto (o il primo).

    Selezione, validazione, conteggio e righe in un solo punto: il template
    rende soltanto.
    """
    chapters = odf_annuario_chapters()
    names = [item["name"] for item in chapters]
    selected = chapter if chapter in names else (names[0] if names else "")
    current = next((item for item in chapters if item["name"] == selected), None)
    count = odf_annuario_count(selected)
    return {
        "chapters": chapters,
        "selected": selected,
        "current": current,
        "count": count,
        "datasets": odf_annuario_datasets(selected, limit=count),
    }


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_annuario_page": odf_annuario_page,
}
