"""Helper delle pagine editoriali: Annuario (capitoli) e news."""

from . import _common
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
    return _common._search(rows=0, fq=f'extras_capitolo:"{chapter}"')["count"]


def odf_annuario_datasets(chapter, limit=12):
    """Dataset del capitolo dell'Annuario (extra `capitolo`), per titolo."""
    if not chapter:
        return []
    data = _common._search(rows=limit, fq=f'extras_capitolo:"{chapter}"', sort="title_string asc")
    return data["results"]
