"""Nomi degli enti: rimozione del prefisso e post-processing dell'harvest."""

import json

import pytest
from ckan.plugins import toolkit
from ckan.tests import factories

from ckanext.opendata_firenze_theme.helpers import agents

PLUGIN = "opendata_firenze_theme"

CREATOR = json.dumps(
    [
        {
            "creator_identifier": "c_d612",
            "creator_name": {
                "it": "Comune di Firenze - Direzione Ambiente",
                "en": "Comune di Firenze - Direzione Ambiente",
            },
        }
    ]
)


def _extras(pkg):
    extras = pkg.get("extras") or {}
    if isinstance(extras, dict):
        return extras
    return {e.get("key"): e.get("value") for e in extras if isinstance(e, dict)}


def test_strip_prefix_only_known_prefix():
    assert agents.strip_prefix("Comune di Firenze - Direzione Cultura") == "Direzione Cultura"
    assert agents.strip_prefix("Comune di Firenze") == "Comune di Firenze"
    assert agents.strip_prefix("Publiacqua S.p.A") == "Publiacqua S.p.A"
    assert agents.strip_prefix("Comune di Firenze - ") == ""
    # I doppi spazi delle due varianti arvestite vengono normalizzati.
    assert (
        agents.strip_prefix("Comune di Firenze - Direzione Generale -  Servizio X")
        == "Direzione Generale - Servizio X"
    )


def test_normalize_notes_known_attributions():
    assert (
        agents.normalize_notes("Fonte: Comune di Firenze - Direzione Cultura. Resto.")
        == "Fonte: Direzione Cultura. Resto."
    )
    assert (
        agents.normalize_notes("Elaborazioni del Comune di Firenze - Ufficio di Statistica")
        == "Elaborazioni dell'Ufficio di Statistica"
    )
    assert (
        agents.normalize_notes("personale del Comune di Firenze - Comparto scuola")
        == "personale del Comparto scuola"
    )
    assert (
        agents.normalize_notes("dati nel Comune di Firenze - Comparto scuola")
        == "dati nel Comparto scuola"
    )
    # Preposizioni articolate anche per unità non presenti oggi in catalogo.
    assert (
        agents.normalize_notes("modello del Comune di Firenze - Direzione Cultura")
        == "modello della Direzione Cultura"
    )
    assert (
        agents.normalize_notes("dati nel Comune di Firenze - Ufficio di Statistica")
        == "dati nell'Ufficio di Statistica"
    )
    assert (
        agents.normalize_notes("iscritti del Comune di Firenze - Anagrafe popolazione")
        == "iscritti dell'Anagrafe popolazione"
    )
    # "Asse V PIUSS" non è un ente: il prefisso resta.
    assert (
        agents.normalize_notes("Beneficiario: Comune di Firenze - Asse V PIUSS")
        == "Beneficiario: Comune di Firenze - Asse V PIUSS"
    )


def test_normalize_package_list_extras():
    data = {
        "author": "Comune di Firenze - Direzione Cultura",
        "maintainer": "Comune di Firenze - Direzione Cultura",
        "notes": "Fonte: Comune di Firenze - Direzione Cultura.",
        "extras": [
            {"key": "holder_name", "value": "Comune di Firenze - Direzione Cultura"},
            {"key": "publisher_name", "value": "Comune di Firenze - Direzione Cultura"},
            {"key": "creator", "value": CREATOR},
            {
                "key": "publisher",
                "value": json.dumps(
                    [
                        {
                            "publisher_identifier": "c_d612",
                            "publisher_name": {
                                "it": "Comune di Firenze - Direzione Urbanistica",
                                "en": "Comune di Firenze - Direzione Urbanistica",
                            },
                        }
                    ]
                ),
            },
        ],
    }
    agents.normalize_package(data)

    extras = _extras(data)
    assert extras["holder_name"] == "Direzione Cultura"
    assert extras["publisher_name"] == "Direzione Cultura"
    creator = json.loads(extras["creator"])[0]
    assert creator["creator_name"]["it"] == "Direzione Ambiente"
    assert creator["creator_name"]["en"] == "Direzione Ambiente"
    publisher = json.loads(extras["publisher"])[0]
    assert publisher["publisher_name"]["it"] == "Direzione Urbanistica"
    assert data["author"] == "Direzione Cultura"
    assert data["maintainer"] == "Direzione Cultura"
    assert data["notes"] == "Fonte: Direzione Cultura."


def test_normalize_package_top_level_and_dict_extras():
    data = {
        "creator": CREATOR,
        "holder_name": "Comune di Firenze - Direzione Ambiente",
        "publisher_name": "Comune di Firenze - Direzione Ambiente",
        "extras": {"serie": "Open SDIAF"},
    }
    agents.normalize_package(data)

    assert data["holder_name"] == "Direzione Ambiente"
    assert data["publisher_name"] == "Direzione Ambiente"
    assert json.loads(data["creator"])[0]["creator_name"]["it"] == "Direzione Ambiente"
    assert data["extras"] == {"serie": "Open SDIAF"}


def test_normalize_package_is_idempotent():
    data = {
        "author": "Direzione Cultura",
        "notes": "Fonte: Direzione Cultura.",
        "extras": [{"key": "holder_name", "value": "Direzione Cultura"}],
    }
    before = json.dumps(data, sort_keys=True)
    agents.normalize_package(data)
    assert json.dumps(data, sort_keys=True) == before


def test_normalize_package_survives_broken_json():
    data = {"extras": [{"key": "creator", "value": "{non-json"}]}
    agents.normalize_package(data)
    assert _extras(data)["creator"] == "{non-json"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_package_create_removes_prefix():
    """Il create passa dal chained action, come l'import dell'harvest."""
    pkg = factories.Dataset(
        author="Comune di Firenze - Direzione Cultura",
        maintainer="Comune di Firenze - Direzione Cultura",
        notes="Fonte: Comune di Firenze - Direzione Cultura.",
        extras=[
            {"key": "holder_name", "value": "Comune di Firenze - Direzione Cultura"},
            {"key": "creator", "value": CREATOR},
        ],
    )
    data = toolkit.get_action("package_show")({"ignore_auth": True}, {"id": pkg["id"]})
    assert data["author"] == "Direzione Cultura"
    assert data["maintainer"] == "Direzione Cultura"
    assert data["notes"] == "Fonte: Direzione Cultura."
    extras = _extras(data)
    assert extras["holder_name"] == "Direzione Cultura"
    assert json.loads(extras["creator"])[0]["creator_name"]["it"] == "Direzione Ambiente"


@pytest.mark.ckan_config("ckan.plugins", PLUGIN)
@pytest.mark.usefixtures("with_plugins")
def test_package_update_removes_prefix():
    """L'update (harvest compreso) normalizza i campi ente."""
    pkg = factories.Dataset(author="Direzione Cultura", notes="Nessun prefisso.")
    toolkit.get_action("package_update")(
        {"ignore_auth": True},
        {
            "id": pkg["id"],
            "author": "Comune di Firenze - Direzione Cultura",
            "notes": "Fonte: Comune di Firenze - Direzione Cultura.",
            "extras": [],
        },
    )
    data = toolkit.get_action("package_show")({"ignore_auth": True}, {"id": pkg["id"]})
    assert data["author"] == "Direzione Cultura"
    assert data["notes"] == "Fonte: Direzione Cultura."
