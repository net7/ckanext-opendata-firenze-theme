"""Rendering degli snippet base riusabili (Section, PageHead, TemaOverline, chip).

Sono macro Jinja e non sono ancora collegate a una pagina: qui si renderizzano
direttamente con l'ambiente Jinja di CKAN (stessi helper `h`/`_` e template del
tema usati dalle pagine), così eventuali errori di sintassi o parametri rotti
emergono subito.
"""

import pytest

PLUGIN = "opendata_firenze_theme"


def _render(src):
    from flask import render_template_string

    return render_template_string(src)


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_tema_overline(with_plugins, with_request_context):
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/tema-overline.html' import tema_overline %}{{ tema_overline('Trasporti') }}"
    )
    assert 'class="rtt-overline rtt-overline--sm"' in html
    assert 'class="rtt-overline__icon"' in html
    assert "Trasporti" in html
    assert "<svg" in html


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
def test_tema_overline_fallback(with_plugins, with_request_context):
    """Un tema non mappato usa comunque un'icona (griglia generica)."""
    html = _render(
        "{% from 'snippets/opendata_firenze_theme/tema-overline.html'"
        " import tema_overline %}{{ tema_overline('Tema senza icona') }}"
    )
    assert 'class="rtt-overline__text"' in html
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
        ' action=\'<a class="rtt-action" href="#">Vedi tutti</a>\') %}'
        "<p>contenuto</p>{% endcall %}"
    )
    assert 'class="rtt-section rtt-reveal"' in html
    assert 'class="rtt-section__action"' in html
    assert "In evidenza" in html
    assert '<a class="rtt-action" href="#">Vedi tutti</a>' in html
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
