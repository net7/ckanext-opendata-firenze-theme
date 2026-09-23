"""Rotte del tema per le pagine editoriali dinamiche.

L'Annuario Statistico e Sviluppatori & LOD non sono pagine statiche
(`ckanext-pages`): la prima elenca i dataset per capitolo, la seconda espone gli
endpoint reali. Vengono quindi servite da template del tema con una rotta
dedicata (niente prefisso `/pages/`, che è il catch-all di ckanext-pages).
"""

import ckan.plugins.toolkit as toolkit
from flask import Blueprint

pages = Blueprint("odf_pages", __name__)


def annuario():
    return toolkit.render("annuario/index.html")


def sviluppatori():
    return toolkit.render("sviluppatori/index.html")


pages.add_url_rule("/annuario-statistico", "annuario", annuario)
pages.add_url_rule("/sviluppatori-e-lod", "sviluppatori", sviluppatori)
