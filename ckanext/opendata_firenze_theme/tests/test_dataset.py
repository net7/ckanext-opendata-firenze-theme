"""Scheda dataset: rendering delle due viste e helper dedicati."""

from unittest import mock

import pytest
from ckan.tests import factories

PLUGIN = "opendata_firenze_theme"


def _body(response):
    return response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_dataset_page_renders_essential(app):
    pkg = factories.Dataset(
        title="Dataset di prova",
        notes="Una descrizione di prova.",
        author="Comune di Firenze",
        author_email="dati@comune.fi.it",
    )
    body = _body(app.get(f"/dataset/{pkg['name']}"))
    assert "rtt-dataset" in body
    assert "Vista essenziale" in body
    assert "Metadati avanzati" in body
    assert "Risorse scaricabili" in body
    assert "In sintesi" in body
    assert "Titolare del dato" in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_dataset_download_links_are_not_tracked(app):
    """I link di download del tema non portano `resource-url-analytics`.

    È la classe su cui il JS di CKAN aggancia il click per registrare un
    download: senza, nessun evento `resource` viene inviato (adr/0007). Il test
    serve a non reintrodurla per sbaglio.
    """
    pkg = factories.Dataset(title="Dataset di prova")
    factories.Resource(package_id=pkg["id"], name="Risorsa di prova", format="CSV")
    body = _body(app.get(f"/dataset/{pkg['name']}"))
    assert "Risorsa di prova" in body
    assert "resource-url-analytics" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_dataset_page_renders_advanced(app):
    pkg = factories.Dataset(title="Dataset di prova")
    body = _body(app.get(f"/dataset/{pkg['name']}?tab=avanzata"))
    assert "Metadati DCAT-AP_IT" in body
    assert "Extras e interoperabilità" in body
    assert "API e formati semantici" in body
    # l'azione del pannello è markup, non deve finire escapata
    assert '&lt;span class="rtt-body-sm"' not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_dataset_no_editor_action_for_anonymous(app):
    pkg = factories.Dataset(title="Dataset di prova")
    body = _body(app.get(f"/dataset/{pkg['name']}"))
    assert "Gestisci" not in body
    assert f"/dataset/edit/{pkg['name']}" not in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_sql_console_enabled_helper(with_plugins, with_request_context, monkeypatch):
    import ckan.lib.helpers as ckan_h

    from ckanext.opendata_firenze_theme import helpers

    monkeypatch.setattr(ckan_h, "datastore_search_sql_enabled", lambda: True, raising=False)
    assert helpers.odf_sql_console_enabled() is True

    monkeypatch.setattr(ckan_h, "datastore_search_sql_enabled", lambda: False, raising=False)
    assert helpers.odf_sql_console_enabled() is False

    # senza ckanext-datastore l'helper non esiste: niente errore
    monkeypatch.delattr(ckan_h, "datastore_search_sql_enabled", raising=False)
    assert helpers.odf_sql_console_enabled() is False


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_helpers(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    assert helpers.odf_filesize(None) == ""
    assert helpers.odf_filesize(1536) == "1,5 KB"
    assert helpers.odf_frequency_label("IRREG") == "irregolare"
    assert helpers.odf_frequency_label("XYZ") == "XYZ"
    assert helpers.odf_dataset_formats(
        {"resources": [{"format": "csv"}, {"format": "CSV"}, {"format": "GeoJSON"}]}
    ) == [
        "csv",
        "GeoJSON",
    ]

    # geometria normalizzata, qualunque sia il maiuscolo dell'extra
    assert (
        helpers.odf_dataset_geometry({"extras": [{"key": "geometria", "value": "Punto"}]})
        == "punto"
    )
    assert helpers.odf_dataset_geometry({"extras": [{"key": "geometria", "value": "x"}]}) is None

    pkg = {
        "extras": [{"key": "hvd", "value": "true"}],
        "resources": [{"format": "GeoJSON"}],
    }
    kinds = {b["kind"] for b in helpers.odf_dataset_badges(pkg)}
    assert kinds == {"hvd", "geo"}

    # un dataset con una risorsa RDF è "Linked Open Data" (badge della testata
    # e filtro "Caratteristiche" del catalogo)
    lod = {"resources": [{"format": "csv"}, {"format": "rdf"}]}
    assert helpers.odf_dataset_is_lod(lod) is True
    assert "lod" in {b["kind"] for b in helpers.odf_dataset_badges(lod)}
    assert helpers.odf_dataset_is_lod({"resources": [{"format": "CSV"}]}) is False

    # campo Solr `odf_features` (faccetta "Caratteristiche"): funziona sia sul
    # package_show sia sul dict appiattito di before_dataset_index
    assert helpers.odf_index_features(lod) == ["alfanumerico", "lod"]
    index_dict = {"res_format": ["GeoJSON"], "extras_hvd": "true"}
    assert helpers.odf_index_features(index_dict) == ["geo", "hvd"]

    # regola unica di "geodato": badge, faccetta e card concordano
    assert helpers.odf_dataset_is_geo({"extras": [{"key": "spatial", "value": "true"}]}) is True
    assert helpers.odf_dataset_is_geo({"extras": [{"key": "spatial", "value": "false"}]}) is False
    assert helpers.odf_index_features({"extras": [{"key": "spatial", "value": "false"}]}) == [
        "alfanumerico"
    ]
    assert helpers.odf_index_features({"extras": [{"key": "spatial", "value": "true"}]}) == ["geo"]
    # `spatial` è spesso una WKT, non una parola booleana: conta comunque
    wkt = {"extras": [{"key": "spatial", "value": "POLYGON((0 0, 1 0, 1 1, 0 0))"}]}
    assert helpers.odf_dataset_is_geo(wkt) is True
    assert helpers.odf_index_features(wkt) == ["geo"]
    # geometria non riconosciuta: resta un geodato, ma senza forma nel badge
    geometry_only = {"extras": [{"key": "geometria", "value": "x"}]}
    assert helpers.odf_dataset_is_geo(geometry_only) is True
    assert helpers.odf_index_features(geometry_only) == ["geo"]
    assert helpers.odf_dataset_badges(geometry_only)[0]["label"] == "Geodati"
    # extras appiattiti di package_search: stessa risposta del package_show
    flat = {"extras_geometria": "area", "extras_spatial_geometry": "true"}
    assert helpers.odf_dataset_is_geo(flat) is True
    assert helpers.odf_index_features(flat) == ["geo"]
    assert helpers.odf_dataset_is_hvd({"extras_hvd": "true"}) is True
    assert "hvd" in {b["kind"] for b in helpers.odf_dataset_badges({"extras_hvd": "true"})}

    # ckanext-dcat rinomina le chiavi con l'etichetta nelle viste: `theme` -> `Theme`
    assert helpers.odf_pkg_extra({"extras": [{"key": "Theme", "value": "x"}]}, "theme") == "x"
    assert helpers.odf_pkg_extra({"extras": {"Theme": "y"}}, "theme") == "y"
    assert helpers.odf_pkg_extra({"extras": [{"key": "serie", "value": "S"}]}, "serie") == "S"
    assert helpers.odf_pkg_extra({"extras": []}, "serie") is None

    # i campi schema dcatapit escono in cima al package (convert_from_extras)
    assert helpers.odf_pkg_extra({"is_version_of": "u"}, "is_version_of") == "u"
    assert helpers.odf_pkg_extra({"is_version_of": "u", "extras": []}, "is_version_of") == "u"
    # l'extra esatto ha la precedenza sul top-level
    assert (
        helpers.odf_pkg_extra({"serie": "TOP", "extras": [{"key": "serie", "value": "S"}]}, "serie")
        == "S"
    )


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_realtime_badge_truthiness(with_plugins, with_request_context):
    """`realtime` segue `_truthy`: "false" non è realtime (fonte unica per
    badge e aside, altrimenti l'aside mostrerebbe "Aggiornato" a vuoto)."""
    from ckanext.opendata_firenze_theme import helpers

    def kinds(value):
        pkg = {"extras": [{"key": "realtime", "value": value}]}
        return {b["kind"] for b in helpers.odf_dataset_badges(pkg)}

    assert "realtime" in kinds("true")
    assert "realtime" in kinds("1")
    assert "realtime" not in kinds("false")
    assert "realtime" not in kinds("0")


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_series_helper(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    # senza serie non si interroga il catalogo
    assert helpers.odf_dataset_series({"id": "x"}) == []

    pkg = {"id": "self", "extras": [{"key": "serie", "value": "Open SDIAF"}]}
    found = {
        "results": [
            {"id": "self", "name": "self", "title": "Sé stesso"},
            {"id": "a", "name": "a", "title": "A", "res_format": ["CSV", "CSV", "GeoJSON"]},
            {"id": "b", "name": "b", "title": "B"},
        ]
    }
    with mock.patch.object(helpers._common, "_search", return_value=found):
        series = helpers.odf_dataset_series(pkg)
    # sé stesso escluso, formati deduplicati da Solr (res_format)
    assert [s["name"] for s in series] == ["a", "b"]
    assert series[0]["formats"] == ["CSV", "GeoJSON"]


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.ckan_config("ckan.site_url", "https://opendata-firenze.test")
def test_series_context_prefers_revisions(with_plugins, with_request_context):
    """Il contesto sceglie le revisioni quando ci sono (come il mockup)."""
    from ckanext.opendata_firenze_theme import helpers

    pkg = {"id": "self", "name": "self", "extras": [{"key": "serie", "value": "S"}]}
    found = {"results": [{"id": "r", "name": "r-2024", "title": "R 2024"}], "count": 2}
    with mock.patch.object(helpers._common, "_search", return_value=found):
        context = helpers.odf_series_context(pkg)
    assert context["kind"] == "revisions"
    assert context["label"] == ""
    assert context["total"] == 2
    assert [item["name"] for item in context["items"]] == ["r-2024"]


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.ckan_config("ckan.site_url", "https://opendata-firenze.test")
def test_series_context_falls_back_to_series(with_plugins, with_request_context):
    """Senza revisioni, il contesto è la serie dichiarata dall'extra."""
    from ckanext.opendata_firenze_theme import helpers

    pkg = {"id": "self", "name": "self", "extras": [{"key": "serie", "value": "S"}]}

    def fake_search(**params):
        if "is_version_of" in (params.get("fq") or ""):
            return {"results": [], "count": 0}
        return {"results": [{"id": "a", "name": "a", "title": "A"}], "count": 3}

    with mock.patch.object(helpers._common, "_search", side_effect=fake_search):
        context = helpers.odf_series_context(pkg)
    assert context["kind"] == "series"
    assert context["label"] == "S"
    assert context["total"] == 3
    assert [item["name"] for item in context["items"]] == ["a"]


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.ckan_config("ckan.site_url", "https://opendata-firenze.test")
def test_series_context_empty(with_plugins, with_request_context):
    """Senza serie e senza revisioni il pannello non ha nulla da mostrare."""
    from ckanext.opendata_firenze_theme import helpers

    with mock.patch.object(helpers._common, "_search", return_value={"results": []}):
        assert helpers.odf_series_context({"id": "x", "name": "x"}) == {
            "kind": None,
            "label": "",
            "total": 0,
            "items": [],
            "serie": "",
            "serie_total": 0,
        }


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.ckan_config("ckan.site_url", "https://opendata-firenze.test")
def test_dataset_revisions_helper(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    # nessuna revisione -> lista vuota
    with mock.patch.object(helpers._common, "_search", return_value={"results": []}):
        assert helpers.odf_dataset_revisions({"id": "x", "name": "x"}) == []

    # dataset CORRENTE (senza is_version_of): cerca chi lo referenzia
    canonical = {"id": "self", "name": "popolazione", "title": "Popolazione residente"}
    found = {
        "results": [
            {"id": "self", "name": "popolazione", "title": "Popolazione residente"},
            {
                "id": "a",
                "name": "pop-2024",
                "title": "Popolazione residente 2024",
                "resources": [
                    {"url": "https://x.test/pop-2024.csv", "format": "CSV", "size": 1536}
                ],
            },
            {
                "id": "b",
                "name": "pop-2023",
                "title": "Popolazione residente",
                "extras": [{"key": "temporal_start", "value": "01-01-2023"}],
                "resources": [{"url": "https://x.test/pop-2023.csv", "format": "CSV"}],
            },
        ]
    }
    with mock.patch.object(helpers._common, "_search", return_value=found) as search:
        revisions = helpers.odf_dataset_revisions(canonical)
    assert [r["name"] for r in revisions] == ["pop-2024", "pop-2023"]
    # anno: dal titolo (2024) e dal periodo di riferimento (2023)
    assert [r["year"] for r in revisions] == ["2024", "2023"]
    assert revisions[0]["formats"] == ["CSV"]
    # download e peso dal primo file della revisione
    assert revisions[0]["download"] == "https://x.test/pop-2024.csv"
    assert revisions[0]["size"] == "1,5 KB"
    assert revisions[1]["size"] == ""
    # la ricerca usa la URL di scheda del corrente (in fq cita is_version_of)
    fqs = [call.kwargs["fq"] for call in search.call_args_list]
    assert any("/dataset/popolazione" in fq for fq in fqs)

    # REVISIONE: elenca il corrente (risolto) + gli altri con lo stesso is_version_of
    root = "https://opendata-firenze.test/dataset/popolazione"
    revision = {"id": "a", "name": "pop-2024", "is_version_of": root}
    siblings = {
        "results": [
            {"id": "a", "name": "pop-2024", "title": "Popolazione residente 2024"},
            {"id": "b", "name": "pop-2023", "title": "Popolazione residente 2023"},
        ]
    }
    with (
        mock.patch.object(helpers._common, "_search", return_value=siblings) as search,
        mock.patch(
            "ckanext.opendata_firenze_theme.helpers.dataset._dataset_by_uri_root",
            return_value={"id": "self", "name": "popolazione", "title": "Popolazione residente"},
        ),
    ):
        revisions = helpers.odf_dataset_revisions(revision)
    assert [r["name"] for r in revisions] == ["popolazione", "pop-2023"]
    fqs = [call.kwargs["fq"] for call in search.call_args_list]
    assert f'extras_is_version_of:"{root}"' in fqs

    # più valori (dcatapit li serializza separati da virgola): tutti nella query
    multi = {"id": "a", "name": "pop-2024", "is_version_of": f"{root},https://example.test/x"}
    with (
        mock.patch.object(helpers._common, "_search", return_value={"results": []}) as search,
        mock.patch(
            "ckanext.opendata_firenze_theme.helpers.dataset._dataset_by_uri_root", return_value=None
        ),
    ):
        helpers.odf_dataset_revisions(multi)
    fqs = [call.kwargs["fq"] for call in search.call_args_list]
    assert f'extras_is_version_of:"{root}"' in fqs
    assert 'extras_is_version_of:"https://example.test/x"' in fqs


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_revision_year_fallback(with_plugins, with_request_context):
    """L'anno della revisione viene da temporal_start, poi version, poi il titolo."""
    from ckanext.opendata_firenze_theme.helpers.dataset import _revision_year_from

    # 1. periodo di riferimento (vince su tutto)
    assert (
        _revision_year_from(
            {
                "title": "Dati 1999",
                "version": "2001",
                "extras": [{"key": "temporal_start", "value": "01-01-2024"}],
            }
        )
        == "2024"
    )
    # 1b. temporal_end, se manca temporal_start
    assert (
        _revision_year_from(
            {"title": "Dati", "extras": [{"key": "temporal_end", "value": "31-12-2022"}]}
        )
        == "2022"
    )
    # 2. versione
    assert _revision_year_from({"title": "Dati 1999", "version": "2001"}) == "2001"
    # 3. titolo (ultima spiaggia)
    assert _revision_year_from({"title": "Dati 1999"}) == "1999"
    # 4. nessuna fonte -> None
    assert _revision_year_from({"title": "Dati"}) is None


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_revisions_end_to_end(with_request_context):
    """Integrazione reale (Solr + filtro): il pannello trova la revisione, il
    catalogo la nasconde. Copre i punti che hanno già generato bug: lettura di
    `is_version_of`, phrase-query Solr sull'URL, filtro del catalogo."""
    import uuid

    from ckan.plugins import toolkit
    from ckan.tests import factories

    from ckanext.opendata_firenze_theme import helpers

    # `ckan.site_url` non è sovrascrivibile col marker: si usa quello reale
    base = (toolkit.config.get("ckan.site_url") or "").rstrip("/")
    tag = uuid.uuid4().hex[:8]
    canonical_name = f"canon-{tag}"
    revision_name = f"rev-{tag}"
    factories.Dataset(name=canonical_name, title=f"Indicatore {tag}")
    factories.Dataset(
        name=revision_name,
        title=f"Indicatore 2024 {tag}",
        extras=[{"key": "is_version_of", "value": f"{base}/dataset/{canonical_name}"}],
    )

    canonical = toolkit.get_action("package_show")({"ignore_auth": True}, {"id": canonical_name})
    revisions = helpers.odf_dataset_revisions(canonical)
    assert [r["name"] for r in revisions] == [revision_name]
    assert revisions[0]["year"] == "2024"

    def count(fq):
        return toolkit.get_action("package_search")({"ignore_auth": True}, {"fq": fq, "rows": 1})[
            "count"
        ]

    # il catalogo mostra il corrente e nasconde la revisione
    assert count(f'name:"{canonical_name}"') == 1
    assert count(f'name:"{revision_name}"') == 0


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_time_ago_helper(with_plugins, with_request_context):
    from datetime import datetime, timedelta, timezone

    from ckanext.opendata_firenze_theme import helpers

    now = datetime.now(timezone.utc)
    assert helpers.odf_time_ago(None) == ""
    assert helpers.odf_time_ago((now - timedelta(minutes=5)).isoformat()) == "pochi minuti fa"
    assert helpers.odf_time_ago((now - timedelta(hours=1)).isoformat()) == "1 ora fa"
    assert helpers.odf_time_ago((now - timedelta(hours=3)).isoformat()) == "3 ore fa"
    assert helpers.odf_time_ago((now - timedelta(days=1)).isoformat()) == "1 giorno fa"
    assert helpers.odf_time_ago((now - timedelta(days=2)).isoformat()) == "2 giorni fa"
    # oltre i 30 giorni ricade sulla data assoluta
    old = now - timedelta(days=400)
    assert helpers.odf_time_ago(old.isoformat()) == old.strftime("%d/%m/%Y")
    # valore non parsabile: nessun errore, resta la stringa troncata
    assert helpers.odf_time_ago("not-a-date") == "not-a-date"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_related_helper(with_plugins, with_request_context):
    from ckanext.opendata_firenze_theme import helpers

    # senza tema non si interroga il catalogo
    assert helpers.odf_dataset_related({"id": "x"}) == []

    pkg = {
        "id": "self",
        "extras": [{"key": "theme", "value": '[".../data-theme/ENVI"]'}],
    }
    found = {"results": [{"id": "self"}, {"id": "a"}, {"id": "b"}, {"id": "c"}]}
    with mock.patch.object(helpers._common, "_search", return_value=found):
        related = helpers.odf_dataset_related(pkg, limit=2)
    assert [r["id"] for r in related] == ["a", "b"]


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_filename_and_separator(with_plugins, with_request_context):
    """Nome file (solo se l'URL ne ha uno vero) e separatore CSV dichiarato."""
    from ckanext.opendata_firenze_theme import helpers

    assert (
        helpers.odf_resource_filename(
            {"url": "https://example.test/archivio/Biblioteche%20SDIAF.csv?v=1"}
        )
        == "Biblioteche SDIAF.csv"
    )
    # link senza nome di file: niente da mostrare (non si inventa)
    assert helpers.odf_resource_filename({"url": "https://example.test/wms"}) == ""
    assert helpers.odf_resource_filename({"url": "https://example.test/dataset"}) == ""
    # gli script lato server non sono nomi di file
    assert helpers.odf_resource_filename({"url": "https://example.test/download.php?id=42"}) == ""

    # il separatore arriva solo dall'extra `separatore` e solo sulle risorse CSV
    pkg = {"extras": [{"key": "separatore", "value": ";"}]}
    assert "punto e virgola" in helpers.odf_resource_separator(pkg, {"format": "CSV"})
    assert helpers.odf_resource_separator(pkg, {"format": "SHP"}) == ""
    assert helpers.odf_resource_separator({}, {"format": "CSV"}) == ""


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_map_resource_and_views_order(with_plugins, with_request_context):
    """ "Vedi su mappa": prima risorsa geografica e mappa prima delle altre viste."""
    from ckanext.opendata_firenze_theme import helpers

    pkg = {"resources": [{"id": "csv", "format": "CSV"}, {"id": "geo", "format": "GeoJSON"}]}
    assert helpers.odf_dataset_map_resource(pkg)["id"] == "geo"
    assert helpers.odf_dataset_map_resource({"resources": [{"format": "CSV"}]}) is None

    views = [{"view_type": "datatables_view"}, {"view_type": "geojson_view"}]
    assert [view["view_type"] for view in helpers.odf_views_map_first(views)] == [
        "geojson_view",
        "datatables_view",
    ]
    assert helpers.odf_views_map_first([]) == []


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_series_helpers(with_plugins, with_request_context):
    """Serie: badge (extra `serie`) e campo Solr `odf_series` per il filtro."""
    from ckanext.opendata_firenze_theme import helpers

    pkg = {"extras": [{"key": "serie", "value": "Open SDIAF"}]}
    assert helpers.odf_dataset_is_series(pkg) is True
    assert helpers.odf_dataset_is_series({"extras": []}) is False
    assert helpers.odf_index_series(pkg) == ["Open SDIAF"]
    assert helpers.odf_index_series({"extras": []}) == []
    # dict di package_search: extra appiattito
    assert helpers.odf_pkg_extra({"extras_serie": "Open SDIAF"}, "serie") == "Open SDIAF"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_dataset_page_shows_map_button(app):
    """Un dataset con risorsa geografica espone il pulsante "Vedi su mappa"."""
    pkg = factories.Dataset(title="Dataset geografico")
    factories.Resource(
        package_id=pkg["id"], name="Geo", format="GeoJSON", url="https://example.test/a.geojson"
    )
    body = _body(app.get(f"/dataset/{pkg['name']}"))
    assert "Vedi su mappa" in body


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_series_info_single_search(with_plugins, with_request_context):
    """Conteggio e membri della serie con una sola ricerca (scheda dataset)."""
    from ckanext.opendata_firenze_theme import helpers

    pkg = {"id": "self", "extras": [{"key": "serie", "value": "Open SDIAF"}]}
    found = {
        "count": 3,
        "results": [
            {"id": "self", "name": "self", "title": "Self"},
            {"id": "a", "name": "a", "title": "Altra banca dati", "resources": []},
        ],
    }
    with mock.patch.object(helpers._common, "_search", return_value=found) as search:
        info = helpers.odf_series_info(pkg)
    assert search.call_count == 1
    assert info["serie"] == "Open SDIAF"
    assert info["count"] == 3
    assert [member["name"] for member in info["members"]] == ["a"]
    assert helpers.odf_series_info({"extras": []}) == {"serie": "", "count": 0, "members": []}
