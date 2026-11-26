"""Dati dei blocchi della home, raccolti una volta sola per render.

Il registro in `home_blocks.BLOCKS` possiede id, template, campi e builder dei
dati; questo module esegue i builder nell'ordine configurato, condividendo la
cache del render. I template dei blocchi restano renderer puri.

Il nome `block_data` (non `section`) evita la collisione con il macro
`section` importato dai blocchi.
"""

from .home_blocks import BLOCKS

_BY_ID = {block["id"]: block for block in BLOCKS}


def odf_home_sections(blocks):
    """`{id_blocco: dati}` per i blocchi attivi, nell'ordine di `blocks`.

    L'entry configurata (testi, periodo) vince sul descriptor; il descriptor
    fornisce builder e limite. Così il registro è l'unica fonte dei dati e
    questo module non conosce nessun blocco.
    """
    cache = {}
    sections = {}
    for entry in blocks:
        descriptor = _BY_ID[entry["id"]]
        block = {**descriptor, **entry}
        sections[entry["id"]] = descriptor["builder"](cache, block)
    return sections


# Nomi esposti ai template (`h.<nome>`); il registro in __init__ è
# derivato da questi mapping.
HELPERS = {
    "odf_home_sections": odf_home_sections,
}
