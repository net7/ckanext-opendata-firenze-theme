"""Helper delle pagine editoriali: Annuario, news e ricerca nei contenuti.

`recent_news` e `search_content` sono l'unico adapter a `ckanext-pages`: la
home e la ricerca site-wide leggono lo stesso CMS con le stesse regole di
privacy, ordine e forma della voce.
"""

import logging
import re
import unicodedata

import ckan.plugins.toolkit as toolkit

from . import _common, query
from . import fuzzy as fuzzy_policy
from .constants import ANNUARIO_CHAPTERS

log = logging.getLogger(__name__)


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


def _normalize(text):
    """Minuscolo e senza accenti, per confronti semplici tra testi."""
    text = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(char for char in text if not unicodedata.combining(char)).casefold()


def _terms(text):
    """Termini normalizzati; l'apostrofo separa le parole come fa il tokenizer."""
    return [term for term in re.split(r"[\s'’]+", _normalize(text)) if term]


def matches(text, query):
    """True se ogni termine della query compare nel testo (case/accenti).

    Prima si cerca la sottostringa esatta; se non c'è, si accetta una parola
    entro la distanza fuzzy del termine (1 per 4-5 caratteri, 2 per 6+). Così
    "Datt" trova "Data" e "Farenze" trova "Firenze" anche nelle news/pagine;
    l'apostrofo separa i termini come nel tokenizer ("dell'arie" → "dell",
    "arie").
    """
    terms = _terms(query)
    if not terms:
        return False
    haystack = _normalize(text)
    words = re.findall(r"\w+", haystack)
    for term in terms:
        if term in haystack:
            continue
        distance = fuzzy_policy.distance_for(term)
        if not distance:
            return False
        if not any(fuzzy_policy.within_distance(term, word, distance) for word in words):
            return False
    return True


def _plain_text(value):
    """Testo senza markup, per cercare nelle pagine e mostrare un estratto."""
    return re.sub(r"<[^>]+>", " ", value or "")


def _pages():
    """Tutte le pagine pubbliche di ckanext-pages, o [] se il plugin manca."""
    try:
        return (
            toolkit.get_action("ckanext_pages_list")(
                {"ignore_auth": True},
                {"private": False, "order_publish_date": True},
            )
            or []
        )
    except Exception:
        log.warning("ckanext-pages non disponibile per la ricerca", exc_info=True)
        return []


def recent_news(limit=3):
    """Ultime news dal blog di ckanext-pages (vuoto se non disponibile)."""
    try:
        from ckanext.pages.plugin import get_recent_blog_posts

        posts = get_recent_blog_posts(number=limit) or []
    except Exception:
        log.warning("ckanext-pages non disponibile per le news", exc_info=True)
        return []

    items = []
    for post in posts:
        item = dict(post)
        item["kind"] = "news"
        try:
            item["url"] = toolkit.url_for("pages.blog_show", page=post.get("name"))
        except Exception:
            item["url"] = ""
        items.append(item)
    return items


def search_content(query):
    """News e pagine che contengono tutti i termini della query.

    Ritorna voci omogenee (`kind`, `name`, `title`, `content`, `publish_date`,
    `url`), nell'ordine di pubblicazione di `ckanext_pages_list`. Il limite per
    tipo lo applica il chiamante, perché news e pagine sono sezioni distinte.
    """
    if not _terms(query):
        return []

    items = []
    for page in _pages():
        content = _plain_text(page.get("content"))
        if not matches(f"{page.get('title', '')} {content}", query):
            continue
        is_news = page.get("page_type") == "blog"
        name = page.get("name")
        try:
            url = toolkit.url_for("pages.blog_show" if is_news else "pages.show", page=name)
        except Exception:
            continue
        items.append(
            {
                "kind": "news" if is_news else "page",
                "name": name,
                "title": page.get("title") or name or "",
                "content": content,
                "publish_date": page.get("publish_date"),
                "url": url,
            }
        )
    return items


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_annuario_page": odf_annuario_page,
}
