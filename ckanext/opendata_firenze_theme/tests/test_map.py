"""Helper della mappa: layer WMS dichiarato dalla risorsa.

Il viewer WMS di ckanext-geoview accetta un fragment `#layer` sull'URL della
risorsa; i WMS del vecchio portale dichiarano il layer solo nella descrizione
("Il Layer di riferimento è ..."). La risoluzione sta qui, in Python, così è
testabile senza un browser e la patch JS legge solo il valore risolto.
"""

import pytest

from ckanext.opendata_firenze_theme import helpers

URL = "https://tms.comune.fi.it/tiles/service/wms?version=1.3.0"


def test_wms_layer_from_fragment():
    assert helpers.odf_wms_layer({"url": URL + "#mobilita:tram"}) == "mobilita:tram"


def test_wms_layer_from_description():
    assert (
        helpers.odf_wms_layer(
            {"url": URL, "description": "Il Layer di riferimento è mobilita:tram"}
        )
        == "mobilita:tram"
    )


def test_wms_layer_fragment_wins_over_description():
    assert (
        helpers.odf_wms_layer(
            {
                "url": URL + "#pianificazione:vigente",
                "description": "Il Layer di riferimento è mobilita:tram",
            }
        )
        == "pianificazione:vigente"
    )


def test_wms_layer_from_description_with_trailing_punctuation():
    assert (
        helpers.odf_wms_layer(
            {"url": URL, "description": "Il Layer di riferimento è mobilita:tram."}
        )
        == "mobilita:tram"
    )


@pytest.mark.parametrize(
    "res",
    (
        {"url": URL},
        {"url": URL, "description": "Web Map Service"},
        {"url": URL + "#"},
        {},
        None,
    ),
)
def test_wms_layer_absent(res):
    assert helpers.odf_wms_layer(res) is None
