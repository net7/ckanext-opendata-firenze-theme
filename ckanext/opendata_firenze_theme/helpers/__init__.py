"""Helper del tema, registrati in ITemplateHelpers (plugin.py).

Re-export dei moduli del package: template e test li usano come `h.odf_*` /
`helpers.odf_*`. Le costanti stanno in `constants`, la formattazione in
`format`, le query Solr (sostituibili nei test) in `_common`.
"""

from . import (  # noqa: F401
    _common,
    catalog,
    dataset,
    dataset_page,
    editorial,
    format,
    home,
    home_blocks,
    home_sections,
    navigation,
    resource,
)
from ._common import odf_number
from .catalog import (
    odf_active_filters,
    odf_facet_all_url,
    odf_facet_groups,
    odf_package_theme,
    odf_theme_meta,
)
from .constants import (
    ANNUARIO_CHAPTERS,
    GEO_FORMATS,
    GEO_FORMATS_UPPER,
    GEOMETRY_SHAPES,
    THEME_CODES,
    THEMES,
    VIEW_TITLES,
)
from .dataset import (
    odf_dataset_badges,
    odf_dataset_contact,
    odf_dataset_downloads,
    odf_dataset_facts,
    odf_dataset_formats,
    odf_dataset_geometry,
    odf_dataset_is_geo,
    odf_dataset_is_hvd,
    odf_dataset_is_lod,
    odf_dataset_is_realtime,
    odf_dataset_is_series,
    odf_dataset_map_resource,
    odf_dataset_openness,
    odf_dataset_related,
    odf_datastore_resource_id,
    odf_format_is_geo,
    odf_index_features,
    odf_index_series,
    odf_pkg_extra,
    odf_sql_console_enabled,
)
from .dataset_page import odf_dataset_page
from .editorial import (
    odf_annuario_chapters,
    odf_annuario_count,
    odf_annuario_datasets,
    odf_annuario_page,
)
from .format import odf_date, odf_filesize, odf_frequency_label, odf_time_ago
from .home import (
    odf_dataset_count,
    odf_featured_datasets,
    odf_geo_datasets,
    odf_geo_search_query,
    odf_home_kpis,
    odf_latest_datasets,
    odf_lod_datasets,
    odf_most_viewed,
    odf_news,
    odf_theme_counts,
    odf_themes,
    odf_themes_visible,
)
from .home_blocks import entries_from_form, odf_home_blocks, odf_home_blocks_admin
from .home_sections import odf_home_sections
from .navigation import odf_breadcrumbs
from .query import FACET_ORDER
from .resource import (
    odf_resource_download_url,
    odf_resource_filename,
    odf_resource_preview,
    odf_resource_preview_url,
    odf_resource_separator,
    odf_resource_view_title,
    odf_resource_views,
    odf_views_map_first,
)
from .series import (
    odf_dataset_revisions,
    odf_dataset_series,
    odf_series_context,
    odf_series_info,
)

# Moduli che dichiarano i propri helper in `HELPERS`: il registro dei template
# è derivato da lì. Aggiungere un helper costa la voce in `HELPERS` e l'import
# in questo file; `__all__` e `get_helpers()` non vanno più toccati. La lista
# esplicita in `tests/test_plugin.py` resta di proposito: è la guardia contro
# le rimozioni silenziose.
HELPER_MODULES = (
    catalog,
    dataset,
    dataset_page,
    editorial,
    format,
    home,
    home_blocks,
    home_sections,
    navigation,
    resource,
    _common,
)

_REGISTRY = {}
for _module in HELPER_MODULES:
    _REGISTRY.update(_module.HELPERS)

# Nomi pubblici che non sono helper da template: costanti e funzioni usate da
# plugin, viste e test.
_PUBLIC_CONSTANTS = ("THEMES",)
_PUBLIC_FUNCTIONS = (
    "odf_dataset_facts",
    "odf_dataset_is_series",
    "odf_dataset_revisions",
    "odf_dataset_series",
    "odf_index_features",
    "odf_index_series",
    "odf_theme_counts",
    "odf_home_blocks_admin",
    "entries_from_form",
    "odf_annuario_chapters",
    "odf_annuario_count",
    "odf_annuario_datasets",
    "odf_dataset_badges",
    "odf_dataset_contact",
    "odf_dataset_count",
    "odf_dataset_downloads",
    "odf_dataset_geometry",
    "odf_dataset_map_resource",
    "odf_dataset_openness",
    "odf_dataset_related",
    "odf_featured_datasets",
    "odf_home_kpis",
    "odf_latest_datasets",
    "odf_lod_datasets",
    "odf_news",
    "odf_series_context",
    "odf_series_info",
    "odf_themes",
    "odf_themes_visible",
    "odf_resource_preview_url",
)

__all__ = [*_REGISTRY, *_PUBLIC_CONSTANTS, *_PUBLIC_FUNCTIONS]


def get_helpers():
    """Helper registrati in ITemplateHelpers (plugin.py)."""
    return dict(_REGISTRY)
