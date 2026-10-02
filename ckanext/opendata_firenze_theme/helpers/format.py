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


def odf_time_ago(value):
    """Tempo relativo in italiano ('pochi minuti fa', '3 ore fa', '2 giorni fa').

    Usato per i dataset "in aggiornamento continuo" (extra `realtime`), dove il
    mockup mostra "Aggiornato: pochi minuti fa" invece della data assoluta.
    Per valori vecchi (o non parsabili) ricade sulla data assoluta `odf_date`.
    """
    if not value:
        return ""
    from datetime import datetime, timezone

    try:
        if hasattr(value, "timestamp"):
            when = value
        else:
            when = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - when
    except (TypeError, ValueError):
        return odf_date(value)

    minutes = max(delta.total_seconds(), 0) / 60
    if minutes < 60:
        return "pochi minuti fa"
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours} ora fa" if hours == 1 else f"{hours} ore fa"
    days = hours // 24
    if days < 30:
        return f"{days} giorno fa" if days == 1 else f"{days} giorni fa"
    return odf_date(value)


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
