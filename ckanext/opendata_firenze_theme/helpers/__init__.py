"""Helper del tema, registrati in ITemplateHelpers (plugin.py).

Re-export dei moduli del package: template e test li usano come `h.odf_*` /
`helpers.odf_*`. Le costanti stanno in `constants`, la formattazione in
`format`, le query Solr (sostituibili nei test) in `_common`.
"""

from . import _common  # noqa: F401  (esposto per i test: helpers._common._search)
from ._common import odf_number
from .catalog import odf_facet_all_url, odf_facet_groups, odf_package_theme
from .constants import (
    ANNUARIO_CHAPTERS,
    FACET_ORDER,
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
    odf_dataset_formats,
    odf_dataset_geometry,
    odf_dataset_is_geo,
    odf_dataset_openness,
    odf_dataset_related,
    odf_dataset_size,
    odf_datastore_resource_id,
    odf_format_is_geo,
    odf_pkg_extra,
    odf_sql_console_enabled,
)
from .editorial import odf_annuario_chapters, odf_annuario_count, odf_annuario_datasets
from .format import FREQUENCY_LABELS, odf_date, odf_filesize, odf_frequency_label
from .home import (
    odf_dataset_count,
    odf_featured_datasets,
    odf_geo_datasets,
    odf_geo_search_query,
    odf_home_kpis,
    odf_most_viewed,
    odf_news,
    odf_theme_counts,
    odf_themes,
)
from .resource import odf_resource_download_url, odf_resource_view_title

__all__ = [
    "odf_number",
    "odf_facet_all_url",
    "odf_facet_groups",
    "odf_package_theme",
    "ANNUARIO_CHAPTERS",
    "FACET_ORDER",
    "GEO_FORMATS",
    "GEO_FORMATS_UPPER",
    "GEOMETRY_SHAPES",
    "THEME_CODES",
    "THEMES",
    "VIEW_TITLES",
    "odf_dataset_badges",
    "odf_dataset_contact",
    "odf_dataset_downloads",
    "odf_dataset_formats",
    "odf_dataset_geometry",
    "odf_dataset_is_geo",
    "odf_dataset_openness",
    "odf_dataset_related",
    "odf_dataset_size",
    "odf_datastore_resource_id",
    "odf_format_is_geo",
    "odf_pkg_extra",
    "odf_sql_console_enabled",
    "odf_annuario_chapters",
    "odf_annuario_count",
    "odf_annuario_datasets",
    "FREQUENCY_LABELS",
    "odf_date",
    "odf_filesize",
    "odf_frequency_label",
    "odf_dataset_count",
    "odf_featured_datasets",
    "odf_geo_datasets",
    "odf_geo_search_query",
    "odf_home_kpis",
    "odf_most_viewed",
    "odf_news",
    "odf_theme_counts",
    "odf_themes",
    "odf_resource_download_url",
    "odf_resource_view_title",
]


def get_helpers():
    return {
        "odf_dataset_count": odf_dataset_count,
        "odf_package_theme": odf_package_theme,
        "odf_facet_all_url": odf_facet_all_url,
        "odf_facet_groups": odf_facet_groups,
        "odf_home_kpis": odf_home_kpis,
        "odf_themes": odf_themes,
        "odf_featured_datasets": odf_featured_datasets,
        "odf_most_viewed": odf_most_viewed,
        "odf_geo_datasets": odf_geo_datasets,
        "odf_geo_search_query": odf_geo_search_query,
        "odf_news": odf_news,
        "odf_annuario_chapters": odf_annuario_chapters,
        "odf_annuario_count": odf_annuario_count,
        "odf_annuario_datasets": odf_annuario_datasets,
        "odf_pkg_extra": odf_pkg_extra,
        "odf_dataset_formats": odf_dataset_formats,
        "odf_format_is_geo": odf_format_is_geo,
        "odf_dataset_badges": odf_dataset_badges,
        "odf_dataset_geometry": odf_dataset_geometry,
        "odf_dataset_is_geo": odf_dataset_is_geo,
        "odf_number": odf_number,
        "odf_dataset_openness": odf_dataset_openness,
        "odf_dataset_related": odf_dataset_related,
        "odf_dataset_contact": odf_dataset_contact,
        "odf_dataset_downloads": odf_dataset_downloads,
        "odf_resource_download_url": odf_resource_download_url,
        "odf_resource_view_title": odf_resource_view_title,
        "odf_dataset_size": odf_dataset_size,
        "odf_sql_console_enabled": odf_sql_console_enabled,
        "odf_datastore_resource_id": odf_datastore_resource_id,
        "odf_date": odf_date,
        "odf_frequency_label": odf_frequency_label,
        "odf_filesize": odf_filesize,
    }
