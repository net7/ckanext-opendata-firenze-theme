"""Separatore CSV: parser, fallback di render e post-processing dell'harvest."""

import pytest
from ckan.plugins import toolkit
from ckan.tests import factories

from ckanext.opendata_firenze_theme.helpers import separator

PLUGIN = "opendata_firenze_theme"

NOTE_SEMICOLON = 'Il separatore delle risorse CSV è ";" (lett. punto e virgola).'
NOTE_COMMA = 'Il separatore delle risorse CSV è "," (lett. virgola).'


def _extras(pkg):
    extras = pkg.get("extras") or {}
    if isinstance(extras, dict):
        return extras
    return {e.get("key"): e.get("value") for e in extras if isinstance(e, dict)}


def test_from_notes_variants():
    assert separator.from_notes(NOTE_SEMICOLON) == ";"
    assert separator.from_notes(NOTE_COMMA) == ","
    assert separator.from_notes("Il dataset non dichiara il separatore.") == ""
    # Anche i nomi, non solo i simboli.
    assert separator.from_notes('Il separatore delle risorse CSV è "TAB".') == "\t"
    assert separator.from_notes("Il separatore delle risorse CSV è il punto e virgola.") == ";"
    assert separator.from_notes("Il separatore delle risorse CSV è la virgola.") == ","
    assert separator.from_notes("Il separatore delle risorse CSV è la barra verticale.") == "|"


def test_normalize_accepts_symbols_and_labels():
    assert separator.normalize(";") == ";"
    assert separator.normalize("\t") == "\t"
    assert separator.normalize("TAB") == "\t"
    assert separator.normalize("tabulazione") == "\t"
    assert separator.normalize("punto e virgola") == ";"
    assert separator.normalize("sconosciuto") == ""


def test_value_prefers_extra_then_notes_no_default():
    assert (
        separator.value({"extras": [{"key": "separatore", "value": "|"}], "notes": NOTE_SEMICOLON})
        == "|"
    )
    assert separator.value({"notes": NOTE_SEMICOLON}) == ";"
    assert separator.value({}) == ""


def test_ensure_extra_handles_list_dict_and_partial_update():
    data = {"notes": NOTE_SEMICOLON, "extras": []}
    separator.ensure_extra(data, create=True)
    assert data["extras"] == [{"key": "separatore", "value": ";"}]

    data = {"notes": NOTE_COMMA, "extras": {"serie": "Open SDIAF"}}
    separator.ensure_extra(data, create=True)
    assert data["extras"] == {"serie": "Open SDIAF", "separatore": ","}

    # un update parziale senza extras non deve creare un extra isolato
    data = {"notes": NOTE_SEMICOLON}
    separator.ensure_extra(data)
    assert "extras" not in data


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_package_create_extracts_separator():
    """Il create passa dal chained action, come l'import dell'harvest."""
    pkg = factories.Dataset(
        notes=NOTE_SEMICOLON,
        resources=[{"format": "CSV", "url": "http://example.com/eventi.csv"}],
    )
    data = toolkit.get_action("package_show")({"ignore_auth": True}, {"id": pkg["id"]})
    assert _extras(data)["separatore"] == ";"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_package_update_extracts_separator():
    """L'update (harvest compreso) aggiunge l'extra se manca."""
    pkg = factories.Dataset(notes="Nessun separatore dichiarato.")
    data = toolkit.get_action("package_show")({"ignore_auth": True}, {"id": pkg["id"]})
    assert "separatore" not in _extras(data)

    toolkit.get_action("package_update")(
        {"ignore_auth": True},
        {"id": pkg["id"], "notes": NOTE_COMMA, "extras": []},
    )
    data = toolkit.get_action("package_show")({"ignore_auth": True}, {"id": pkg["id"]})
    assert _extras(data)["separatore"] == ","


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_existing_separator_extra_wins():
    """Un extra già valorizzato non viene sovrascritto dalla descrizione."""
    pkg = factories.Dataset(
        notes=NOTE_SEMICOLON,
        extras=[{"key": "separatore", "value": ","}],
    )
    data = toolkit.get_action("package_show")({"ignore_auth": True}, {"id": pkg["id"]})
    assert _extras(data)["separatore"] == ","
