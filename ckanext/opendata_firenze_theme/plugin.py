import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.logic.action.get import package_search as core_package_search

from ckanext.opendata_firenze_theme import helpers, views
from ckanext.opendata_firenze_theme.helpers import home_blocks, query

# Favicon di CKAN (default di ckan.favicon): il tema la sostituisce con il giglio del Comune,
# ma solo se la configurazione non ne indica gia' un'altra.
CKAN_DEFAULT_FAVICON = "/base/images/ckan.ico"
THEME_FAVICON = "/brand/favicon.ico"

QUALITY_AUTH = "odf_quality_view"


def _can_view_quality(context, pkg_id):
    """Qualita' del metadato: solo uso interno.

    Ammessi sysadmin e chi puo' modificare un dataset di un'organizzazione
    (editor/admin dell'org). I dataset senza organizzazione restano visibili
    solo ai sysadmin: il default CKAN di `package_update` per i package non
    posseduti sarebbe troppo permissivo.
    """
    # Stessa semantica di `check_access`: i contesti interni (report, task,
    # export) con `ignore_auth` non sono soggetti alla policy.
    if context.get("ignore_auth"):
        return True
    user = context.get("auth_user_obj") or context.get("user")
    if isinstance(user, str):
        user = model.User.get(user)
    if user is None:
        return False
    if not getattr(user, "is_authenticated", True):
        return False
    if getattr(user, "sysadmin", False):
        return True
    if not pkg_id:
        return False
    pkg = model.Package.get(pkg_id)
    if pkg is None or not pkg.owner_org:
        return False
    try:
        return bool(toolkit.check_access("package_update", context, {"id": pkg_id}))
    except toolkit.NotAuthorized:
        return False


def odf_quality_view(context, data_dict):
    """Auth function: chi puo' vedere il punteggio di qualita' del dataset."""
    return {"success": _can_view_quality(context, (data_dict or {}).get("id"))}


def _strip_quality(pkg_dict):
    """Rimuove i dati QA da un package (API pubblica, search, pagina)."""
    pkg_dict.pop("qa", None)
    extras = pkg_dict.get("extras")
    if isinstance(extras, dict):
        extras.pop("openness_score", None)
    elif isinstance(extras, list):
        pkg_dict["extras"] = [
            extra
            for extra in extras
            if not (isinstance(extra, dict) and extra.get("key") == "openness_score")
        ]
    for resource in pkg_dict.get("resources") or []:
        if isinstance(resource, dict):
            resource.pop("qa", None)


@toolkit.side_effect_free
def odf_package_search(context, data_dict):
    """`package_search` con filtro qualità sui risultati (API e catalogo)."""
    result = core_package_search(context, data_dict)
    for pkg in result.get("results", []):
        if not _can_view_quality(context, pkg.get("id")):
            _strip_quality(pkg)
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
        if not _can_view_quality(context, pkg_dict.get("id")):
            _strip_quality(pkg_dict)
        return pkg_dict

    # IPackageController

    def before_dataset_search(self, search_params):
        """Nasconde dal catalogo le revisioni temporali (policy in `helpers.query`)."""
        return query.hide_revisions(search_params)
