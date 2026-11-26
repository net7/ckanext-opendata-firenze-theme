"""Policy fuzzy condivisa da catalogo e contenuti editoriali.

La distanza segue il criterio `AUTO` dei motori di ricerca: i termini sotto i
4 caratteri restano esatti, quelli di 4-5 caratteri tollerano una modifica,
quelli di 6+ due modifiche. La distanza è di Damerau-Levenshtein (optimal
string alignment), quindi copre anche le trasposizioni come "ambinete" →
"ambiente".
"""

MIN_LENGTH = 4


def distance_for(term):
    """Distanza fuzzy ammessa per un termine (0 = solo esatto)."""
    length = len(term or "")
    if length < MIN_LENGTH:
        return 0
    return 1 if length <= 5 else 2


def within_distance(left, right, max_distance):
    """True se `left` e `right` distano al massimo `max_distance` (Damerau)."""
    if max_distance < 0:
        return False
    if left == right:
        return True
    if abs(len(left) - len(right)) > max_distance:
        return False

    previous_previous = None
    previous = list(range(len(right) + 1))
    for row, left_char in enumerate(left, 1):
        current = [row] + [0] * len(right)
        for column, right_char in enumerate(right, 1):
            cost = 0 if left_char == right_char else 1
            value = min(
                previous[column] + 1,
                current[column - 1] + 1,
                previous[column - 1] + cost,
            )
            if (
                row > 1
                and column > 1
                and left_char == right[column - 2]
                and left[row - 2] == right_char
            ):
                value = min(value, previous_previous[column - 2] + 1)
            current[column] = value
        previous_previous, previous = previous, current
    return previous[-1] <= max_distance
