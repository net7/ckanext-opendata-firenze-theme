import pytest
from ckan.plugins import plugin_loaded


@pytest.mark.ckan_config("ckan.plugins", "opendata_firenze_theme")
@pytest.mark.usefixtures("with_plugins")
def test_plugin():
    assert plugin_loaded("opendata_firenze_theme")
