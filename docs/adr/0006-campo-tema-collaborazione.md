# 6. Campo "Tema di riferimento" del form Collaborazione non implementato

## Stato

Accettata

## Contesto

Il mockup della pagina Collaborazione (`screens/partecipa.jsx`) prevede quattro
campi: Nome e cognome, Email, **Tema di riferimento (facoltativo)** — un select
con i temi del catalogo — e la richiesta. Il tema è l'unico campo facoltativo.

Il form è l'override di `contact/form.html` di `ckanext-contact`, che invia i
dati con un POST. La validazione lato server
(`ckanext/contact/routes/_helpers.py::validate`) considera **obbligatorio ogni
campo presente in `data_dict`**, con due sole eccezioni: `save` e `subject`:

```python
optional_fields = {"subject"}
...
for field, value in data_dict.items():
    ...
    if field in optional_fields:
        continue
    if value is None or value == "":
        errors[field] = ["Missing Value"]
```

Non esiste quindi modo, con l'estensione così com'è, di inviare un campo
facoltativo: se il select resta vuoto il server risponde "Missing Value".

I trucchi usati altrove non si applicano: il checkbox privacy è seguito da un
hidden omonimo vuoto per *imporre* un valore non vuoto, mentre qui serve
l'opposto (accettare il vuoto).

## Decisione

Il campo **non viene implementato**: il form del tema ha i tre campi rimanenti
(Nome, Email, Richiesta), che sono tutti obbligatori, più il consenso privacy.

Motivo: aggiungere il campo richiede di modificare `ckanext-contact`, che è una
dipendenza di deployment (un clone in `src/`, non codice del tema); una patch
locale andrebbe mantenuta a ogni aggiornamento e introdurrebbe un
comportamento diverso da upstream.

## Alternative valutate

1. **Opzione "Non specificato" sempre valorizzata.** Il select avrebbe una voce
   di default con valore non vuoto (es. "Non indicato"), quindi il campo non è
   mai vuoto e la validazione passa. Scartata: tradisce il mockup (che mostra il
   placeholder "Scegli un tema", cioè il vuoto) e sporca l'email con un valore
   fittizio.
2. **Campo con nome diverso + hidden.** Una coppia select/hidden non risolve:
   se il select è vuoto invia comunque la stringa vuota, che è quella che vince.
3. **Patch a `ckanext-contact`** per introdurre una lista di campi facoltativi
   configurabile (es. `ckanext.contact.optional_fields`). È la strada corretta
   se il campo diventa un requisito: va proposta a monte o mantenuta come patch
   documentata, con un ADR dedicato.

## Conseguenze

- La pagina Collaborazione resta con uno scostamento noto dal mockup (manca il
  select del tema).
- Se il campo diventa necessario, la via è l'opzione 3 (patch/config a monte),
  non un aggiramento nel template.
