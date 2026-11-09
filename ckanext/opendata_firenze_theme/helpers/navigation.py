"""Percorsi di navigazione (breadcrumb) delle pagine interne.

Un solo punto per la voce Home, per le sezioni note (Catalogo, Collaborazione)
e per il tema DCAT; i template passano solo la foglia (ed eventualmente il
genitore). Prima ogni pagina ricostruiva la stessa lista.
"""

import ckan.plugins.toolkit as toolkit

from .catalog import odf_theme_meta


def odf_breadcrumbs(leaf, section=None, parent=None, theme=None):
    """Lista `{label, href}`: Home, sezione, tema, genitore, foglia.

    `section`: "catalog" (Catalogo) o "contact" (Collaborazione).
    `parent`: eventuale voce intermedia, es. il dataset nella scheda risorsa.
    `theme`: codice/label/URI del tema DCAT, se la pagina è filtrata per tema.
    """
    crumbs = [{"label": toolkit._("Home"), "href": toolkit.url_for("home.index")}]
    if section == "catalog":
        crumbs.append({"label": toolkit._("Catalogo"), "href": toolkit.url_for("dataset.search")})
    elif section == "contact":
        crumbs.append({"label": toolkit._("Collaborazione"), "href": toolkit.url_for("/contact")})
    if theme:
        meta = odf_theme_meta(theme)
        crumbs.append(
            {
                "label": meta["label"] if meta else theme,
                "href": toolkit.url_for("dataset.search", dcat_theme=theme),
            }
        )
    if parent:
        crumbs.append(parent)
    crumbs.append({"label": leaf})
    return crumbs


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_breadcrumbs": odf_breadcrumbs,
}
