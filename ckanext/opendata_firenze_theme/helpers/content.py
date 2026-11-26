"""Contenuti editoriali: adapter unico per news e pagine.

Il module possiede il contratto del CMS (`ContentSource`) e la ricerca nei
contenuti. In produzione il source chiama `ckanext-pages`; nei test si passa un
source in-memory, così news e pagine sono coperte anche senza il plugin.
"""

import logging
import re
import unicodedata

import ckan.plugins.toolkit as toolkit

from . import fuzzy as fuzzy_policy

log = logging.getLogger(__name__)


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


def _load_pages(page_type=None):
    """Pagine pubbliche da ckanext-pages, o [] se il plugin manca."""
    data = {"private": False, "order_publish_date": True}
    if page_type:
        data["page_type"] = page_type
    try:
        return toolkit.get_action("ckanext_pages_list")({"ignore_auth": True}, data) or []
    except Exception:
        log.warning("ckanext-pages non disponibile per la ricerca", exc_info=True)
        return []


class ContentSource:
    """Sorgente di news e pagine; l'adapter reale è `ckanext-pages`.

    `load_pages(page_type)` riceve `"blog"` per le news e `None` per tutte le
    pagine. Nei test basta passare una funzione in-memory.
    """

    def __init__(self, load_pages=None):
        self._load_pages = load_pages or _load_pages

    def recent_news(self, limit=3):
        """Ultime news dal blog, normalizzate per la card della home."""
        items = []
        for post in self._load_pages("blog")[:limit]:
            item = dict(post)
            item["kind"] = "news"
            try:
                item["url"] = toolkit.url_for("pages.blog_show", page=post.get("name"))
            except Exception:
                item["url"] = ""
            items.append(item)
        return items

    def search_content(self, query):
        """News e pagine che contengono tutti i termini della query.

        Ritorna voci omogenee (`kind`, `name`, `title`, `content`,
        `publish_date`, `url`), nell'ordine di pubblicazione. Il limite per
        tipo lo applica il chiamante.
        """
        if not _terms(query):
            return []

        items = []
        for page in self._load_pages():
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


def default_source():
    """Source di produzione (`ckanext-pages`)."""
    return ContentSource()


def recent_news(limit=3, source=None):
    """Ultime news; `source` è iniettabile nei test."""
    return (source or default_source()).recent_news(limit)


def search_content(query, source=None):
    """News e pagine che corrispondono alla query; `source` è iniettabile."""
    return (source or default_source()).search_content(query)
