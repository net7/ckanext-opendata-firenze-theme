import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.opendata_firenze_theme import helpers, views
from ckanext.opendata_firenze_theme.helpers import home_blocks, query

# Favicon di CKAN (default di ckan.favicon): il tema la sostituisce con il giglio del Comune,
# ma solo se la configurazione non ne indica gia' un'altra.
CKAN_DEFAULT_FAVICON = "/base/images/ckan.ico"
THEME_FAVICON = "/brand/favicon.ico"


class OpendataFirenzeThemePlugin(plugins.SingletonPlugin):
    """Tema CKAN del portale Open Data del Comune di Firenze."""

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigDeclaration)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)

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

    # IPackageController

    def before_dataset_search(self, search_params):
        """Nasconde dal catalogo le revisioni temporali (policy in `helpers.query`)."""
        return query.hide_revisions(search_params)
