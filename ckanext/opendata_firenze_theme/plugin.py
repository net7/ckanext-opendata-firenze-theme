import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.opendata_firenze_theme import helpers


class OpendataFirenzeThemePlugin(plugins.SingletonPlugin):
    """Tema CKAN del portale Open Data del Comune di Firenze."""

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "opendata_firenze_theme")

    # ITemplateHelpers

    def get_helpers(self):
        return helpers.get_helpers()
