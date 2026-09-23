"""Pagine editoriali (step 8): Annuario e Sviluppatori & LOD.

Il form di Collaborazione (ckanext-contact) è testato in `test_contact.py`,
che salta se l'estensione non è installata.
"""

import pytest
from ckan.tests import factories

PLUGIN = "opendata_firenze_theme"


def _body(response):
    return response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_annuario_page(app):
    body = _body(app.get("/annuario-statistico"))
    assert "rtt-annuario__grid" in body
    assert "Annuario Statistico del Comune di Firenze" in body
    # 13 capitoli nella SideNav
    assert body.count("rtt-sidenav__item") == 13
    assert "Capitolo 01 di 13" in body
    # senza l'extra `capitolo` i capitoli sono vuoti
    assert "Nessun dataset di questo capitolo" in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_annuario_lists_chapter_datasets(app):
    factories.Dataset(
        title="Trasporti di prova",
        extras=[{"key": "capitolo", "value": "Trasporti"}],
    )
    body = _body(app.get("/annuario-statistico?capitolo=Trasporti"))
    assert "Trasporti di prova" in body
    assert "Nessun dataset di questo capitolo" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_sviluppatori_page(app):
    body = _body(app.get("/sviluppatori-e-lod"))
    assert "Endpoint CKAN" in body
    assert "package_search" in body
    # le azioni dei pannelli sono markup, non devono finire escapate
    assert '&lt;span class="rtt-body-sm"' not in body
    rdf = _body(app.get("/sviluppatori-e-lod?tab=rdf"))
    assert "Risorse RDF" in rdf
    assert "package_metadata_rdf_dcat_ap_it" in rdf
    geo = _body(app.get("/sviluppatori-e-lod?tab=geo"))
    assert "GetCapabilities" in geo
