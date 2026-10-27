"""Rotte del tema: pagine editoriali e amministrazione della homepage.

L'Annuario Statistico e Sviluppatori & LOD non sono pagine statiche
(`ckanext-pages`): la prima elenca i dataset per capitolo, la seconda espone gli
endpoint reali. Vengono quindi servite da template del tema con una rotta
dedicata (niente prefisso `/pages/`, che è il catch-all di ckanext-pages).

La rotta `/ckan-admin/homepage` gestisce i blocchi della home: salva ordine e
blocchi attivi con l'azione standard `config_option_update` (in `system_info`).
"""

import json

import ckan.plugins.toolkit as toolkit
from flask import Blueprint, request

from ckanext.opendata_firenze_theme.helpers import home_blocks

pages = Blueprint("odf_pages", __name__)
admin = Blueprint("odf_admin", __name__)


def annuario():
    return toolkit.render("annuario/index.html")


def sviluppatori():
    return toolkit.render("sviluppatori/index.html")


pages.add_url_rule("/annuario-statistico", "annuario", annuario)
pages.add_url_rule("/sviluppatori-e-lod", "sviluppatori", sviluppatori)


@admin.route("/ckan-admin/homepage", methods=["GET", "POST"], endpoint="homepage_blocks")
def homepage_blocks():
    """Attiva/disattiva e riordina i blocchi della home (solo sysadmin)."""
    context = {"user": toolkit.g.user}
    try:
        toolkit.check_access("config_option_update", context, {})
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._("Serve un amministratore di sistema."))

    if request.method == "POST":
        blocks = home_blocks.odf_home_blocks_admin()
        current = [block["id"] for block in blocks]
        orders = {block["id"]: request.form.get("order_%s" % block["id"]) for block in blocks}
        texts = {
            block["id"]: {field: request.form.get("%s_%s" % (field, block["id"])) for field in block["fields"]}
            for block in blocks
        }
        entries = home_blocks.entries_from_form(request.form.getlist("enabled"), orders, texts, current)
        errors = home_blocks.validate_entries(entries)
        if errors:
            return toolkit.render(
                "admin/homepage_blocks.html",
                extra_vars={
                    "blocks": home_blocks.admin_blocks(entries),
                    "errors": errors,
                    "error_summary": toolkit._("Controlla i campi evidenziati."),
                },
            )
        toolkit.get_action("config_option_update")(context, {home_blocks.OPTION: json.dumps(entries)})
        toolkit.h.flash_success(toolkit._("Blocchi della homepage aggiornati."))
        return toolkit.redirect_to("odf_admin.homepage_blocks")

    return toolkit.render(
        "admin/homepage_blocks.html",
        extra_vars={"blocks": home_blocks.odf_home_blocks_admin()},
    )
