"""Qualità interna del metadato: visibilità, rimozione e punteggio.

Una sola policy per le tre superfici che mostrano o nascondono `qa`:
`plugin.odf_package_search`, `after_dataset_show` e la scheda dataset. Il
plugin resta l'adapter CKAN; qui c'è il comportamento.
"""

import ckan.model as model
import ckan.plugins.toolkit as toolkit

from . import _common


def can_view(context, pkg_id):
    """Qualità visibile solo a sysadmin e a chi può modificare il dataset.

    I dataset senza organizzazione restano visibili solo ai sysadmin: il
    default CKAN di `package_update` per i package non posseduti sarebbe
    troppo permissivo.
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


def strip(pkg_dict):
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


def openness(pkg):
    """Openness di ckanext-qa (0-5) con etichetta/tono, o None."""
    qa = pkg.get("qa") or {}
    raw = qa.get("openness_score")
    if raw is None:
        raw = _common.pkg_field(pkg, "openness_score")
    try:
        score = int(raw)
    except (TypeError, ValueError):
        return None
    if score >= 4:
        label, tier = toolkit._("Alta"), "high"
    elif score == 3:
        label, tier = toolkit._("Buona"), "medium"
    else:
        label, tier = toolkit._("Bassa"), "low"
    return {"score": score, "label": label, "tier": tier}
