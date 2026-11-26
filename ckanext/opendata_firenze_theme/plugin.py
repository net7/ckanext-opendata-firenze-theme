import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.opendata_firenze_theme import cli, helpers, views
from ckanext.opendata_firenze_theme.helpers import home_blocks, quality, query

from .helpers.catalog_search import catalog_search

# Favicon di CKAN (default di ckan.favicon): il tema la sostituisce con il giglio del Comune,
# ma solo se la configurazione non ne indica gia' un'altra.
CKAN_DEFAULT_FAVICON = "/base/images/ckan.ico"
THEME_FAVICON = "/brand/favicon.ico"

QUALITY_AUTH = "odf_quality_view"


def odf_quality_view(context, data_dict):
    """Auth function: chi puo' vedere il punteggio di qualita' del dataset."""
    return {"success": quality.can_view(context, (data_dict or {}).get("id"))}


@toolkit.side_effect_free
def odf_package_search(context, data_dict):
    """`package_search` con filtro qualità e fallback fuzzy.

    La policy di ricerca (esatta, poi fuzzy solo per le viste) sta nel module
    `helpers.catalog_search`; qui restano l'adapter CKAN e la visibilità della
    qualità.
    """
    result = catalog_search(context, data_dict)

    for pkg in result.get("results", []):
        if not quality.can_view(context, pkg.get("id")):
            quality.strip(pkg)
    return result


class OpendataFirenzeThemePlugin(plugins.SingletonPlugin):
    """Tema CKAN del portale Open Data del Comune di Firenze."""

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigDeclaration)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IClick)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "opendata_firenze_theme")
        if config_.get("ckan.favicon", CKAN_DEFAULT_FAVICON) == CKAN_DEFAULT_FAVICON:
            config_["ckan.favicon"] = THEME_FAVICON

    def update_config_schema(self, schema):
        """Rende aggiornabile da /ckan-admin/homepage l'ordine dei blocchi."""
        schema[home_blocks.OPTION] = [
            toolkit.get_validator("ignore_missing"),
            toolkit.get_validator("unicode_safe"),
        ]
        return schema

    # IConfigDeclaration

    def declare_config_options(self, declaration, key):
        """Dichiara l'opzione cosi' CKAN non la segnala come sconosciuta."""
        declaration.declare(key.ckanext.opendata_firenze_theme.homepage_blocks, "")

    # ITemplateHelpers

    def get_helpers(self):
        return helpers.get_helpers()

    # IBlueprint

    def get_blueprint(self):
        return [views.pages, views.admin]

    # IClick

    def get_commands(self):
        return [cli.cleanup_map_views]

    # IAuthFunctions

    def get_auth_functions(self):
        return {QUALITY_AUTH: odf_quality_view}

    # IActions

    def get_actions(self):
        return {"package_search": odf_package_search}

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        """Aggiunge "Caratteristiche" e "Serie" (policy in `helpers.query`)."""
        return query.dataset_facets(facets_dict)

    def group_facets(self, facets_dict, group_type, package_type):
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        return facets_dict

    # IPackageController

    def before_dataset_index(self, pkg_dict):
        """Indicizza le "Caratteristiche" e la "Serie" del dataset."""
        pkg_dict[query.FEATURES] = helpers.odf_index_features(pkg_dict)
        pkg_dict[query.SERIES] = helpers.odf_index_series(pkg_dict)
        return pkg_dict

    def after_dataset_show(self, context, pkg_dict):
        """Rimuove la qualita' dai package non visibili agli utenti interni."""
        if not quality.can_view(context, pkg_dict.get("id")):
            quality.strip(pkg_dict)
        return pkg_dict

    # IPackageController

    def before_dataset_search(self, search_params):
        """Nasconde dal catalogo le revisioni temporali (policy in `helpers.query`)."""
        return query.hide_revisions(search_params)
