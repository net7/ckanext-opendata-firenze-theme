import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.opendata_firenze_theme import helpers, views


class OpendataFirenzeThemePlugin(plugins.SingletonPlugin):
    """Tema CKAN del portale Open Data del Comune di Firenze."""

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "opendata_firenze_theme")

    # ITemplateHelpers

    def get_helpers(self):
        return helpers.get_helpers()

    # IBlueprint

    def get_blueprint(self):
        return views.pages

    # IPackageController

    def before_dataset_search(self, search_params):
        """Nasconde dal catalogo le revisioni temporali (dataset con `is_version_of`).

        Convenzione: il dataset **corrente** non ha `is_version_of` ed è l'unico
        visibile in catalogo; le revisioni precedenti lo puntano e qui vengono
        escluse. Restano raggiungibili dal pannello "Revisioni temporali" e dal
        link "Vedi le revisioni", che cercano esplicitamente `is_version_of`: in
        quel caso il filtro non si applica. Vedi `odf_dataset_revisions`.
        """
        haystack = " ".join(str(search_params.get(key) or "") for key in ("q", "fq"))
        if "extras_is_version_of" in haystack:
            return search_params
        fq = search_params.get("fq") or ""
        if isinstance(fq, list):
            fq = " ".join(str(part) for part in fq)
        search_params["fq"] = (fq + " -extras_is_version_of:[* TO *]").strip()
        return search_params
