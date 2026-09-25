"""Formattazione per la UI: date, dimensioni file, etichette di frequenza."""

# Etichette italiane per i codici frequenza EU (dcatapit usa il vocabolario
# `frequency` di Publications Office: ANNUAL, MONTHLY, IRREG…).
FREQUENCY_LABELS = {
    "ANNUAL": "annuale",
    "BIENNIAL": "biennale",
    "BIWEEKLY": "quindicinale",
    "CONT": "continua",
    "DAILY": "giornaliera",
    "HOURLY": "oraria",
    "IRREG": "irregolare",
    "MONTHLY": "mensile",
    "QUARTERLY": "trimestrale",
    "REALTIME": "in tempo reale",
    "SEMIANNUAL": "semestrale",
    "TRIENNIAL": "triennale",
    "UNKNOWN": "non nota",
    "WEEKLY": "settimanale",
}


def odf_date(value, fmt="%d/%m/%Y"):
    """Data ISO/datetime -> 'gg/mm/aaaa'; stringa vuota se assente."""
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime(fmt)
    text = str(value)
    try:
        from datetime import datetime

        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime(fmt)
    except ValueError:
        return text[:10]


def odf_frequency_label(code):
    """Etichetta italiana di un codice frequenza EU (fallback: codice)."""
    if not code:
        return ""
    return FREQUENCY_LABELS.get(str(code).upper(), str(code))


def odf_filesize(size):
    """Byte -> '1,2 MB' (it-IT); stringa vuota se non disponibile."""
    if not size:
        return ""
    try:
        value = float(size)
    except (TypeError, ValueError):
        return ""
    if value <= 0:
        return ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f}".replace(".", ",") + f" {unit}"
        value /= 1024
    return ""
