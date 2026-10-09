"""Rendering degli snippet base riusabili (Section, PageHead, TemaOverline, chip).

Sono macro Jinja e non sono ancora collegate a una pagina: qui si renderizzano
direttamente con l'ambiente Jinja di CKAN (stessi helper `h`/`_` e template del
tema usati dalle pagine), così eventuali errori di sintassi o parametri rotti
emergono subito.
"""

import pytest

PLUGIN = "opendata_firenze_theme"


def _render(src, **context):
    from flask import render_template_string

    return render_template_string(src, **context)


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_tema_overline(with_plugins, with_request_context):
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/tema-overline.html' import tema_overline %}{{ tema_overline('Trasporti') }}"
    )
    assert 'class="rtt-tema-overline rtt-tema-overline--sm"' in html
    assert 'class="rtt-tema-overline__icon"' in html
    assert "Trasporti" in html
    assert "<svg" in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_tema_overline_fallback(with_plugins, with_request_context):
    """Un tema non mappato usa comunque un'icona (griglia generica)."""
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/tema-overline.html'"
        " import tema_overline %}{{ tema_overline('Tema senza icona') }}"
    )
    assert 'class="rtt-tema-overline__text"' in html
    assert "<svg" in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_tema_overline_by_code_and_uri(with_plugins, with_request_context):
    """Accetta label, codice dcatapit ("ENVI") o URI e mostra la label italiana."""
    from_code = _render(
        "{% from 'snippets/opendata_firenze_theme/tema-overline.html' import tema_overline %}{{ tema_overline('ENVI') }}"
    )
    assert "Ambiente" in from_code
    from_uri = _render(
        "{% from 'snippets/opendata_firenze_theme/tema-overline.html' import tema_overline %}"
        "{{ tema_overline('http://publications.europa.eu/resource/authority/data-theme/TRAN') }}"
    )
    assert "Trasporti" in from_uri


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_tema_overline_label_override(with_plugins, with_request_context):
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/tema-overline.html'"
        " import tema_overline %}{{ tema_overline('ENVI', label='Ambiente e territorio') }}"
    )
    assert "Ambiente e territorio" in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_section(with_plugins, with_request_context):
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/section.html' import section %}"
        "{% call section(title='In evidenza',"
        ' action=\'<a class="rtt-actionlink" href="#">Vedi tutti</a>\') %}'
        "<p>contenuto</p>{% endcall %}"
    )
    assert 'class="rtt-section rtt-reveal"' in html
    assert 'class="rtt-section__action"' in html
    assert "In evidenza" in html
    assert '<a class="rtt-actionlink" href="#">Vedi tutti</a>' in html
    assert "contenuto" in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_section_band(with_plugins, with_request_context):
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/section.html' import section %}"
        "{% call section(title='Esplora per tema', band=True) %}x{% endcall %}"
    )
    assert "rtt-section--band" in html
    assert "rtt-section__overlay" in html
    assert "data-on-dark" in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_section_without_title_or_action(with_plugins, with_request_context):
    """Senza titolo/azione il corpo resta l'unico figlio (nessuno spazio vuoto)."""
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/section.html' import section %}"
        "{% call section() %}<p>solo contenuto</p>{% endcall %}"
    )
    assert 'class="rtt-section__body"' in html
    assert "rtt-section__title" not in html
    assert "rtt-section__action" not in html
    assert "solo contenuto" in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_page_head(with_plugins, with_request_context):
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/page-head.html' import page_head %}"
        "{% call page_head(title='Annuario Statistico', lead='Testo guida.',"
        " aside='<span class=\"aside\">x</span>',"
        " crumbs=[{'label': 'Home', 'href': '/'}, {'label': 'Annuario Statistico'}]) %}"
        "<p>extra</p>{% endcall %}"
    )
    assert 'class="rtt-page-head"' in html
    assert 'class="rtt-breadcrumbs"' in html
    assert 'aria-current="page"' in html
    assert "rtt-page-head__lead" in html
    assert "Annuario Statistico" in html
    assert "Testo guida." in html
    assert "extra" in html
    assert '<span class="aside">x</span>' in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_page_head_crumb_kicker(with_plugins, with_request_context):
    """Con una voce intermedia compare il kicker mobile."""
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/page-head.html' import page_head %}"
        "{{ page_head(title='Trasporti',"
        " crumbs=[{'label': 'Home'}, {'label': 'Catalogo'}, {'label': 'Trasporti'}]) }}"
    )
    assert 'class="rtt-crumb-kicker"' in html
    assert "Catalogo" in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_meta_table_shows_zero_skips_empty(with_plugins, with_request_context):
    """0 è un valore valido e va mostrato; None/stringa vuota saltano la riga."""
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/dataset/meta_table.html' import meta_table %}"
        "{{ meta_table([('Download', 0), ('Licenza', none), ('Vuoto', '')]) }}"
    )
    assert "Download" in html
    assert "<td>0</td>" in html
    assert "Licenza" not in html
    assert "Vuoto" not in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_series_panel_renders(with_plugins, with_request_context):
    """La SeriePanel mostra gli altri dataset della stessa serie (escluso sé)."""
    from unittest import mock

    from ckanext.opendata_firenze_theme import helpers

    pkg = {
        "id": "self",
        "name": "self",
        "title": "Self",
        "extras": [{"key": "serie", "value": "Open SDIAF"}],
    }
    found = {
        "results": [
            {"id": "self", "name": "self", "title": "Self"},
            {
                "id": "a",
                "name": "a",
                "title": "Altra banca dati",
                "resources": [{"url": "https://x.test/a.csv", "format": "CSV"}],
            },
        ]
    }

    def fake_search(**kwargs):
        # il ramo "Revisioni temporali" cerca per is_version_of: qui non ce ne sono
        if "is_version_of" in (kwargs.get("fq") or ""):
            return {"results": []}
        return found

    with mock.patch.object(helpers._common, "_search", side_effect=fake_search):
        html = _render(
            "{% from 'snippets/opendata_firenze_theme/dataset/serie.html' import series_panel %}"
            "{{ series_panel(pkg) }}",
            pkg=pkg,
        )
    assert "Altri dataset della serie" in html
    assert "rtt-accordion" in html
    assert "Altra banca dati" in html
    assert "/dataset/a" in html
    # download del file del dataset della serie + bottone (mockup) del pannello
    assert "https://x.test/a.csv" in html
    assert "Scarica tutta la serie" in html
    assert "Vedi la serie" not in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.ckan_config("ckan.site_url", "https://opendata-firenze.test")
def test_revisions_panel_renders(with_plugins, with_request_context):
    """Il ramo "Revisioni temporali": accordion con anno, link e download."""
    from unittest import mock

    from ckanext.opendata_firenze_theme import helpers

    # dataset corrente (senza is_version_of): le revisioni sono chi lo punta
    pkg = {
        "id": "self",
        "name": "popolazione",
        "title": "Popolazione residente 2025",
        "extras": [{"key": "serie", "value": "Popolazione"}],
    }
    found = {
        "results": [
            {"id": "self", "name": "popolazione", "title": "Popolazione residente 2025"},
            {
                "id": "a",
                "name": "pop-2024",
                "title": "Popolazione residente 2024",
                "resources": [{"url": "https://x.test/pop-2024.csv", "format": "CSV", "size": 1536}],
            },
        ]
    }
    with mock.patch.object(helpers._common, "_search", return_value=found):
        html = _render(
            "{% from 'snippets/opendata_firenze_theme/dataset/serie.html' import series_panel %}"
            "{{ series_panel(pkg) }}",
            pkg=pkg,
        )
    assert "Revisioni temporali" in html
    assert "rtt-accordion" in html
    assert "Revisioni precedenti · 1" in html
    assert "Anno 2024" in html
    assert "/dataset/pop-2024" in html
    # download del file della revisione + bottone (mockup) del pannello
    assert "https://x.test/pop-2024.csv" in html
    assert "Scarica tutta la serie" in html
    assert "Vedi le revisioni" not in html
    # con le revisioni il ramo serie non deve comparire
    assert "Altri dataset della serie" not in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_aside_realtime_label(with_plugins, with_request_context):
    """Il riquadro "In sintesi" mostra "Aggiornato" solo per i dataset realtime."""
    pkg = {
        "metadata_created": "2026-09-01T10:00:00",
        "metadata_modified": "2026-09-01T10:00:00",
        "frequency": "REALTIME",
        "license_title": "CC-BY 4.0",
        "resources": [],
        "tracking_summary": {"total": 5, "recent": 2},
        "extras": [],
    }
    src = (
        "{% from 'snippets/opendata_firenze_theme/dataset/aside.html' import dataset_aside %}"
        "{{ dataset_aside(pkg, [], {}, is_realtime) }}"
    )
    rt = _render(src, pkg=pkg, is_realtime=True)
    assert "Aggiornato" in rt
    assert "Ultima modifica" not in rt
    plain = _render(src, pkg=pkg, is_realtime=False)
    assert "Ultima modifica" in plain
    assert "Aggiornato" not in plain


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_row_preview_button(with_plugins, with_request_context):
    """Il link "Vedi anteprima" è aggiornato dal JS alla modale (con fallback)."""
    pkg = {"name": "demo", "type": "dataset"}
    res = {
        "id": "r1",
        "name": "Eventi (CSV)",
        "format": "CSV",
        "url_type": "upload",
        "url": "",
        "size": 1536,
        "tracking_summary": {"total": 3},
    }
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/dataset/resource_row.html' import resource_row %}"
        "{{ resource_row(pkg, res) }}",
        pkg=pkg,
        res=res,
    )
    assert "data-rtt-preview" in html
    assert 'data-preview-name="Eventi (CSV)"' in html
    assert 'data-preview-format="CSV"' in html
    assert 'data-preview-full="/dataset/demo/resource/r1"' in html
    # senza JS resta un link valido alla scheda risorsa (progressive enhancement)
    assert '<a class="rtt-btn rtt-btn--text rtt-btn--sm" href="/dataset/demo/resource/r1" data-rtt-preview' in html
    # il conteggio dei download per risorsa non compare più (vedi adr/0007):
    # la fixture lo passa apposta, così il test fallirebbe se tornasse nel template.
    assert "Download" not in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_dataset_aside_has_no_download_counter(with_plugins, with_request_context):
    """Il riquadro "In sintesi" mostra le Visualizzazioni, non i download (adr/0007).

    Il totale dei download era la somma dei `tracking_summary` delle risorse:
    passiamo una risorsa con un conteggio non nullo proprio per verificare che
    non ricompaia.
    """
    pkg = {
        "metadata_created": "2026-09-01T10:00:00",
        "metadata_modified": "2026-09-01T10:00:00",
        "license_title": "CC-BY 4.0",
        "tracking_summary": {"total": 5, "recent": 2},
        "resources": [{"tracking_summary": {"total": 3}}],
        "extras": [],
    }
    src = (
        "{% from 'snippets/opendata_firenze_theme/dataset/aside.html' import dataset_aside %}"
        "{{ dataset_aside(pkg, [], {}) }}"
    )
    html = _render(src, pkg=pkg)
    assert "Visualizzazioni" in html
    assert "Download" not in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_preview_modal_renders(with_plugins, with_request_context):
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/dataset/preview_modal.html'"
        " import resource_preview_modal %}{{ resource_preview_modal() }}"
    )
    assert "<dialog" in html
    assert "data-rtt-preview-modal" in html
    assert "data-rtt-preview-iframe" in html
    assert "data-rtt-preview-close" in html
    assert "Vedi la scheda della risorsa" in html
    assert "Nessuna anteprima disponibile per questa risorsa." in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_preview_url_first_view(with_plugins, with_request_context):
    """L'URL della modale è la prima vista della risorsa."""
    from unittest import mock

    from ckanext.opendata_firenze_theme import helpers

    with mock.patch.object(
        helpers.resource.toolkit,
        "get_action",
        return_value=lambda context, data: [{"id": "v1"}],
    ):
        url = helpers.odf_resource_preview_url({"name": "demo", "type": "dataset"}, {"id": "r1"})
    assert url == "/dataset/demo/resource/r1/view/v1"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_resource_preview_url_without_views(with_plugins, with_request_context):
    """Senza viste (o senza id) l'helper non espone un URL."""
    from unittest import mock

    from ckanext.opendata_firenze_theme import helpers

    with mock.patch.object(
        helpers.resource.toolkit,
        "get_action",
        return_value=lambda context, data: [],
    ):
        assert helpers.odf_resource_preview_url({"name": "demo"}, {"id": "r1"}) == ""
    assert helpers.odf_resource_preview_url({"name": "demo"}, {}) == ""


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_chip(with_plugins, with_request_context):
    html = _render("{% from 'snippets/opendata_firenze_theme/chip.html' import chip %}{{ chip('CSV', size='sm') }}")
    assert 'class="rtt-chip rtt-chip--sm"' in html
    assert 'class="rtt-chip__label"' in html
    assert "CSV" in html
    assert "rtt-chip__remove" not in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_chip_selected_dismissible(with_plugins, with_request_context):
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/chip.html' import chip %}"
        "{{ chip('Trasporti', state='selected', dismissible=True) }}"
    )
    assert "rtt-chip--dismissible" in html
    assert "is-selected" in html
    assert '<button class="rtt-chip__remove" type="button" aria-label="' in html
    assert "data-rtt-chip-remove" in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_format_and_status_chip(with_plugins, with_request_context):
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/chip.html'"
        " import format_chip, status_chip %}"
        "{{ format_chip('GeoJSON', 'geo') }}{{ status_chip('HVD', 'aperto') }}"
    )
    assert 'class="rtt-format-chip rtt-format-chip--geo"' in html
    assert "GeoJSON" in html
    assert 'class="rtt-status-chip"' in html
    assert 'data-tone="aperto"' in html
