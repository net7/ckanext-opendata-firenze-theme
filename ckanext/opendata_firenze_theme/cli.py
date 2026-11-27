"""Comandi di manutenzione del tema."""

import click
from ckan import model
from ckan.lib.datapreview import get_view_plugin
from ckan.plugins import toolkit

from ckanext.opendata_firenze_theme.helpers import _common, separator
from ckanext.opendata_firenze_theme.helpers.map import GENERIC_MAP_VIEW_TYPES


def _duplicate_map_views(resource_id=None):
    """Viste generiche da rimuovere: stessa risorsa con un `geojson_view`.

    La specializzazione evita di crearle sulle risorse nuove (patch a
    ckanext-geoview), ma quelle gia' in DB restano: questo comando le elenca e,
    con `--delete`, elimina quelle auto-create.
    """
    query = model.Session.query(model.ResourceView.resource_id).filter(
        model.ResourceView.view_type == "geojson_view"
    )
    if resource_id:
        query = query.filter(model.ResourceView.resource_id == resource_id)
    resource_ids = [row[0] for row in query.distinct()]
    if not resource_ids:
        return []
    duplicates = model.Session.query(model.ResourceView).filter(
        model.ResourceView.resource_id.in_(resource_ids)
    )
    if resource_id:
        duplicates = duplicates.filter(model.ResourceView.resource_id == resource_id)
    return (
        duplicates.filter(model.ResourceView.view_type.in_(GENERIC_MAP_VIEW_TYPES))
        .order_by(model.ResourceView.resource_id, model.ResourceView.id)
        .all()
    )


def _is_auto_view(view):
    """True se la vista sembra creata automaticamente, senza personalizzazioni."""
    if view.description not in (None, ""):
        return False
    if view.config not in (None, {}):
        return False
    plugin = get_view_plugin(view.view_type)
    if plugin is None:
        return False
    default_title = plugin.info().get("default_title")
    return bool(default_title) and view.title == default_title


@click.command("odf-cleanup-map-views")
@click.option(
    "--delete",
    "delete_",
    is_flag=True,
    help="Elimina le viste auto-create (default: dry-run).",
)
@click.option(
    "--all",
    "delete_all",
    is_flag=True,
    help="Elimina anche le viste personalizzate (implica --delete).",
)
@click.option(
    "--resource-id",
    "resource_id",
    help="Limita il controllo/cleanup a una singola risorsa.",
)
def cleanup_map_views(delete_, delete_all, resource_id):
    """Elimina i geo_view/geoview duplicati sulle risorse con geojson_view.

    Senza flag fa dry-run. `--delete` rimuove solo le viste con titolo,
    descrizione e config di default; `--all` rimuove anche quelle
    personalizzate, quindi va usato come intervento esplicito.
    """
    if get_view_plugin("geojson_view") is None:
        raise click.ClickException(
            "geojson_view non e' abilitato: non elimino le viste generiche, "
            "la risorsa resterebbe senza mappa."
        )

    views = _duplicate_map_views(resource_id)
    if not views:
        click.echo("Nessuna vista mappa duplicata.")
        return

    auto_ids = {view.id for view in views if _is_auto_view(view)}
    for view in views:
        kind = "auto" if view.id in auto_ids else "personalizzata"
        click.echo(f"{view.resource_id}\t{view.view_type}\t{view.id}\t{kind}\t{view.title or ''}")

    if not delete_ and not delete_all:
        click.echo(
            f"{len(views)} viste duplicate; --delete elimina le "
            f"{len(auto_ids)} auto-create, --all anche le personalizzate."
        )
        return

    to_delete = views if delete_all else [view for view in views if view.id in auto_ids]
    delete_view = toolkit.get_action("resource_view_delete")
    for view in to_delete:
        delete_view({"ignore_auth": True}, {"id": view.id})

    skipped = len(views) - len(to_delete)
    if skipped:
        click.echo(f"{skipped} viste personalizzate lasciate (usa --all).")
    click.echo(f"Eliminate {len(to_delete)} viste duplicate.")


def _extra_value(pkg, key):
    return separator.normalize(_common.pkg_field(pkg, key))


def _candidates(context, dataset):
    """Package da esaminare: uno solo, oppure quelli con la frase in descrizione."""
    show = toolkit.get_action("package_show")
    if dataset:
        try:
            yield show(context, {"id": dataset})
        except toolkit.ObjectNotFound as exc:
            raise click.ClickException(f"Dataset non trovato: {dataset}") from exc
        return
    query = (
        model.Session.query(model.Package).filter_by(state="active").order_by(model.Package.name)
    )
    for pkg in query:
        if not separator.from_notes(pkg.notes):
            yield None
            continue
        try:
            yield show(context, {"id": pkg.id})
        except toolkit.ObjectNotFound:
            yield None


@click.command("odf-extract-separators")
@click.option(
    "--apply",
    "apply_",
    is_flag=True,
    help="Scrive l'extra (default: dry-run).",
)
@click.option(
    "--dataset",
    "dataset",
    help="Limita a un dataset (nome o id).",
)
@click.option(
    "--limit",
    type=int,
    default=0,
    help="Limita il numero di dataset aggiornati (0 = tutti).",
)
def extract_separators(apply_, dataset, limit):
    """Estrae il separatore CSV dalla descrizione e lo salva in `extras.separatore`.

    Il post-processing dell'harvest lo fa già per i dataset nuovi/aggiornati
    (package_create/package_update); questo comando serve per il backfill dei
    dataset già in catalogo. Senza `--apply` è un dry-run.
    """
    context = {"ignore_auth": True}
    patch = toolkit.get_action("package_patch")
    counts = {"added": 0, "present": 0, "no_note": 0, "errors": 0}

    for pkg in _candidates(context, dataset):
        if pkg is None:
            counts["no_note"] += 1
            continue
        name = pkg.get("name") or pkg.get("id")
        sep = separator.from_notes(pkg.get("notes"))
        if not sep:
            counts["no_note"] += 1
            continue
        if _extra_value(pkg, "separatore"):
            counts["present"] += 1
            continue

        if not apply_:
            counts["added"] += 1
            click.echo(f"{name}\t{sep}")
        else:
            try:
                # Copia con la stessa forma di extras di package_show.
                data = {"notes": pkg.get("notes"), "extras": pkg.get("extras") or []}
                separator.ensure_extra(data, create=True)
                patch(context, {"id": pkg["id"], "extras": data["extras"]})
                counts["added"] += 1
            except Exception as exc:  # noqa: BLE001 - un dataset rotto non ferma il backfill
                counts["errors"] += 1
                click.echo(f"Errore su {name}: {exc}", err=True)
        if limit and counts["added"] >= limit:
            break

    verb = "Aggiornati" if apply_ else "Da aggiornare"
    click.echo(
        f"{verb}: {counts['added']}; già presenti: {counts['present']}; "
        f"senza nota: {counts['no_note']}; errori: {counts['errors']}."
    )
