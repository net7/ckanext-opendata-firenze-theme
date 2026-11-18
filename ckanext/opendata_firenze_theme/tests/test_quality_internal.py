"""Qualita' interna: le azioni di ckanext-qa applicano `odf_quality_view`.

Il modulo richiede ckanext-qa installato (c'e' in dev, non nella CI del tema):
dove l'estensione manca viene saltato.
"""

import pytest

pytest.importorskip("ckanext.qa")

from ckan.tests import factories  # noqa: E402

from ckanext.qa.logic import auth  # noqa: E402

PLUGIN = "opendata_firenze_theme"
QA_PLUGINS = f"{PLUGIN} qa"


def _editor(user_name):
    return {"user": user_name}


@pytest.fixture(autouse=True)
def _qa_tables(with_plugins):
    """Crea le tabelle di ckanext-qa nel DB di test (come `ckan qa init`)."""
    from ckan import model

    from ckanext.qa.model import init_tables

    init_tables(model.meta.engine)


@pytest.mark.ckan_config("ckan.plugins", QA_PLUGINS)
@pytest.mark.usefixtures("with_plugins", "with_request_context")
def test_qa_auth_denies_anonymous(app):
    pkg = factories.Dataset()
    result = auth.qa_package_openness_show({}, {"id": pkg["id"]})
    assert result == {"success": False}


@pytest.mark.ckan_config("ckan.plugins", QA_PLUGINS)
@pytest.mark.usefixtures("with_plugins", "with_request_context")
def test_qa_auth_allows_org_editor(app):
    user = factories.User()
    org = factories.Organization(users=[{"name": user["name"], "capacity": "editor"}])
    pkg = factories.Dataset(owner_org=org["id"])
    result = auth.qa_package_openness_show(_editor(user["name"]), {"id": pkg["id"]})
    assert result == {"success": True}


@pytest.mark.ckan_config("ckan.plugins", QA_PLUGINS)
@pytest.mark.usefixtures("with_plugins", "with_request_context")
def test_qa_resource_auth_uses_the_resource_dataset(app):
    user = factories.User()
    org = factories.Organization(users=[{"name": user["name"], "capacity": "editor"}])
    pkg = factories.Dataset(owner_org=org["id"])
    resource = factories.Resource(package_id=pkg["id"])
    assert auth.qa_resource_show({}, {"id": resource["id"]}) == {"success": False}
    assert auth.qa_resource_show(_editor(user["name"]), {"id": resource["id"]}) == {"success": True}


@pytest.mark.ckan_config("ckan.plugins", QA_PLUGINS)
@pytest.mark.usefixtures("with_plugins")
def test_qa_actions_deny_anonymous_via_api(app):
    pkg = factories.Dataset()
    resource = factories.Resource(package_id=pkg["id"])

    openness = app.get(f"/api/3/action/qa_package_openness_show?id={pkg['id']}")
    assert openness.status_code == 403

    resource_show = app.get(f"/api/3/action/qa_resource_show?id={resource['id']}")
    assert resource_show.status_code == 403
