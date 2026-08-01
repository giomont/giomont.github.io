#!/usr/bin/env python3
"""
generar.py
----------
Genera los archivos JSON de Wegweiser:

  noticias.json  -> descarga el feed RSS de Tagesschau, categoriza por
                     palabras clave y traduce cada titular (alemán -> inglés,
                     alemán -> español) con la API gratuita de MyMemory.

  arvi.json      -> traduce un banco fijo de frases en alemán sobre el
                     Parque Arví (Medellín).

  colombia.json  -> traduce un banco fijo de frases en alemán sobre la
                     diversidad turística de Colombia (Fontur / MinCIT).

  guia_turistica.json -> traduce un banco fijo de frases útiles para guías
                     turísticos (orientación, hotel, restaurante, transporte,
                     emergencias, comunicación, dinero, sitios de interés).

  aleman_basico.json -> traduce un banco fijo de frases básicas de alemán
                     para el guía (categoría única "Grundlagen").

Uso:
    python3 generar.py noticias      # solo noticias.json
    python3 generar.py arvi          # solo arvi.json
    python3 generar.py colombia      # solo colombia_diversidad.json
    python3 generar.py guia          # solo guia_turistica.json
    python3 generar.py basico        # solo aleman_basico.json
    python3 generar.py all           # los cinco (por defecto si no se pasa nada)

Para agregar más frases a cualquiera de los bancos, simplemente agregá una
línea en alemán a ARVI_PHRASES, COLOMBIA_PHRASES, GUIA_PHRASES (con su
categoría) o ALEMAN_BASICO_PHRASES más abajo y volvé a correr el script:
la traducción al inglés/español/francés se genera sola.

Solo usa la librería estándar de Python (urllib), sin dependencias externas.
"""

import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from html import unescape
from urllib.request import urlopen, Request
from urllib.parse import quote

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------

RSS_URL = "https://www.tagesschau.de/xml/rss2/"
MAX_ITEMS = 20                 # cuántas noticias quedan en noticias.json
MYMEMORY_URL = "https://api.mymemory.translated.net/get"
REQUEST_DELAY = 1.2            # segundos entre llamadas a MyMemory (evita 429)
USER_AGENT = "Mozilla/5.0 (Wegweiser-Generator)"

NOTICIAS_FILE = "noticias.json"
ARVI_FILE = "arvi.json"
COLOMBIA_FILE = "colombia_diversidad.json"
GUIA_FILE = "guia_turistica.json"
ALEMAN_BASICO_FILE = "aleman_basico.json"

# Palabras clave para asignar categoría a las noticias (todo en minúsculas).
# El orden importa: se revisa de arriba hacia abajo y se usa la primera
# categoría que haga match.
CATEGORY_KEYWORDS = {
    "Politik": [
        "bundestag", "regierung", "minister", "kanzler", "wahl", "partei",
        "gesetz", "koalition", "bundesrat", "parlament", "spd", "cdu",
        "grüne", "afd", "fdp", "csu", "opposition", "bundespräsident",
    ],
    "Wirtschaft": [
        "wirtschaft", "inflation", "aktie", "börse", "unternehmen", "euro",
        "arbeitsmarkt", "export", "konjunktur", "zoll", "handel", "steuer",
        "preis", "bank", "gehalt", "arbeitslosigkeit", "energiepreis",
    ],
    "Sport": [
        "wm", "em", "bundesliga", "olympia", "tor", "meister", "spiel",
        "fußball", "sport", "trainer", "medaille", "sieg", "niederlage",
    ],
    "Umwelt": [
        "klima", "umwelt", "co2", "erneuerbare", "hitze", "dürre",
        "artenschutz", "wald", "emission", "naturschutz", "flut",
        "temperatur", "erwärmung",
    ],
    # "Welt" queda como categoría por defecto si nada más hace match.
}

# ---------------------------------------------------------------------------
# Bancos de frases fijas (Arví y Colombia)
# Agregá/editá líneas acá; la traducción se genera automáticamente.
# ---------------------------------------------------------------------------

ARVI_PHRASES = [
    "Der Arví-Park liegt im Nordosten von Medellín.",
    "Der Park hat eine Fläche von etwa 16.000 Hektar.",
    "Etwa 1.760 Hektar sind ursprünglicher Nebelwald.",
    "Der Park wurde 1970 zum Naturschutzgebiet erklärt.",
    "Es gibt mehr als 54 Kilometer Wanderwege.",
    "Man erreicht den Park mit der Seilbahn Línea L.",
    "Die Fahrt mit der Seilbahn dauert etwa zwanzig Minuten.",
    "Zuerst fährt man mit der Metro bis zur Station Acevedo.",
    "Dann steigt man in die Seilbahn Línea K nach Santo Domingo um.",
    "Der Park liegt zwischen 2.340 und 2.680 Metern über dem Meeresspiegel.",
    "Die Temperatur liegt normalerweise zwischen zwölf und achtzehn Grad.",
    "Im Park gibt es archäologische Wege der Ureinwohner.",
    "Besucher können wandern, Vögel beobachten und Rad fahren.",
    "Ein Führer begleitet die Besucher auf den Wegen.",
    "Der Park gehört zu den Gemeinden Medellín, Guarne, Bello und Copacabana.",
    "Der Eintritt in die Naturzonen ist meist kostenlos.",
    "Einige geführte Erlebnisse haben einen zusätzlichen Preis.",
    "Die Seilbahn Línea L ist am Montag geschlossen.",
    "Im Park wachsen viele einheimische und angepflanzte Bäume.",
    "Arví ist eines der wichtigsten Ökotourismusprojekte Kolumbiens.",
]

COLOMBIA_PHRASES = [
    "Kolumbien nennt sich \"das Land der Schönheit\".",
    "Das Land hat mehr als 1.900 Vogelarten.",
    "Kolumbien hat elf Ausdrucksformen auf der UNESCO-Liste des immateriellen Erbes.",
    "Das Ministerium für Handel, Industrie und Tourismus fördert die Kampagne \"Entdecke die Vielfalt Kolumbiens\".",
    "Fontur unterstützt touristische Projekte in mehr als 650 Gemeinden.",
    "Kolumbien hat 32 Departamentos mit sehr unterschiedlichen Landschaften.",
    "Der Kulturtourismus bringt jährlich etwa 300 Milliarden Pesos ein.",
    "Es gibt ein Netz von historischen Dörfern, die \"Pueblos Patrimonio\" genannt werden.",
    "Die Vereinigten Staaten sind der wichtigste Herkunftsmarkt für Besucher.",
    "Danach kommen Besucher vor allem aus Mexiko, Peru, Ecuador und Chile.",
    "Kolumbien bietet Strände, Anden und tropischen Regenwald im selben Land.",
    "Der Gemeinschaftstourismus stärkt kleine lokale Unternehmen.",
    "San Agustín in Huila ist bekannt für archäologische Steinfiguren.",
    "Die Kaffeeregion ist UNESCO-Weltkulturerbe.",
    "Kolumbien hat auch touristische Angebote für die LGBTIQ+ Gemeinschaft.",
    "Kreuzfahrtreisende nach Kolumbien haben stark zugenommen.",
    "Kolumbien möchte bis 2030 ein führendes nachhaltiges Reiseziel sein.",
    "Medellín, Cartagena und Bogotá sind die meistbesuchten Städte.",
    "Die kolumbianische Küche ist Teil der touristischen Vielfalt.",
    "Jede Region Kolumbiens hat eine eigene kulturelle Identität.",
]

# guia_turistica.json: cada frase tiene su propia categoría (tupla de dos
# elementos: texto en alemán, categoría).
GUIA_PHRASES = [
    ("Entschuldigung, wo ist der Bahnhof?", "Orientierung"),
    ("Ich hätte gerne ein Zimmer für zwei Nächte.", "Hotel"),
    ("Können Sie mir den Weg zum Museum zeigen?", "Orientierung"),
    ("Die Rechnung, bitte.", "Restaurant"),
    ("Haben Sie eine Speisekarte auf Englisch?", "Restaurant"),
    ("Wie viel kostet ein Ticket für die U-Bahn?", "Transport"),
    ("Ich brauche einen Arzt.", "Notfälle"),
    ("Sprechen Sie Englisch?", "Kommunikation"),
    ("Könnten Sie das bitte wiederholen?", "Kommunikation"),
    ("Wo kann ich Geld wechseln?", "Geld"),
    ("Ist das WLAN kostenlos?", "Hotel"),
    ("Um wie viel Uhr öffnet das Museum?", "Sehenswürdigkeiten"),
    ("Ich bin allergisch gegen Nüsse.", "Restaurant"),
    ("Können Sie mir ein Taxi rufen?", "Transport"),
    ("Wo ist die nächste Apotheke?", "Notfälle"),
    ("Ich möchte eine Stadtführung buchen.", "Sehenswürdigkeiten"),
    ("Haben Sie vegetarische Gerichte?", "Restaurant"),
    ("Wie komme ich zum Flughafen?", "Transport"),
    ("Könnten Sie langsamer sprechen, bitte?", "Kommunikation"),
    ("Vielen Dank für Ihre Hilfe!", "Kommunikation"),
]

# aleman_basico.json: todas las frases usan la categoría única "Grundlagen".
ALEMAN_BASICO_PHRASES = [
    "Guten Tag! Wie kann ich Ihnen helfen?",
    "Ich heiße Giovanni und bin Ihr Reiseführer.",
    "Willkommen in Kolumbien!",
    "Wie viel kostet das?",
    "Wo ist die Toilette, bitte?",
    "Ich verstehe nicht, können Sie das wiederholen?",
    "Bitte folgen Sie mir.",
    "Wir treffen uns um neun Uhr.",
    "Das Wetter ist heute sehr schön.",
    "Haben Sie Fragen?",
    "Der Ausflug dauert drei Stunden.",
    "Bitte trinken Sie viel Wasser.",
    "Vorsicht, der Weg ist steil!",
    "Es tut mir leid, ich spreche wenig Deutsch.",
    "Vielen Dank für Ihren Besuch!",
    "Mein Name ist Giovanni. Wie heißen Sie?",
    "Zählen wir zusammen: eins, zwei, drei.",
    "Links ist der Eingang, rechts ist der Ausgang.",
    "Wir fahren jetzt mit der Seilbahn.",
    "Bis bald und gute Reise!",
]

# ---------------------------------------------------------------------------
# 1) Descargar y parsear el feed RSS (solo para noticias.json)
# ---------------------------------------------------------------------------

def fetch_rss(url):
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=15) as resp:
        return resp.read()


def parse_items(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.findall(".//item"):
        title_el = item.find("title")
        title = unescape((title_el.text or "").strip()) if title_el is not None else ""
        if title:
            items.append(title)
    return items


def clean_title(title):
    """Quita etiquetas HTML residuales y espacios raros de un titular."""
    title = re.sub(r"<[^>]+>", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


# ---------------------------------------------------------------------------
# 2) Categorización por palabras clave (solo para noticias.json)
# ---------------------------------------------------------------------------

def categorize(text):
    lower = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return cat
    return "Welt"


# ---------------------------------------------------------------------------
# 3) Traducción con MyMemory (de -> en, de -> es)
# ---------------------------------------------------------------------------

def translate(text, target_lang):
    """Traduce `text` del alemán a `target_lang` ('en' o 'es') usando
    la API gratuita de MyMemory. Si falla, devuelve el texto original
    para que el script nunca se caiga por completo."""
    langpair = f"de|{target_lang}"
    url = f"{MYMEMORY_URL}?q={quote(text)}&langpair={langpair}"
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        translated = data.get("responseData", {}).get("translatedText", "")
        translated = unescape(translated).strip()
        return translated if translated else text
    except Exception as e:
        print(f"  ! Traducción a {target_lang} falló para «{text[:40]}...»: {e}", file=sys.stderr)
        return text


def translate_entry(de_text, cat):
    en_text = translate(de_text, "en")
    time.sleep(REQUEST_DELAY)
    es_text = translate(de_text, "es")
    time.sleep(REQUEST_DELAY)
    fr_text = translate(de_text, "fr")
    time.sleep(REQUEST_DELAY)
    return {"de": de_text, "en": en_text, "es": es_text, "fr": fr_text, "cat": cat}


# ---------------------------------------------------------------------------
# 4) Generadores por fuente
# ---------------------------------------------------------------------------

def generar_noticias():
    print(f"→ Descargando feed: {RSS_URL}")
    try:
        xml_bytes = fetch_rss(RSS_URL)
    except Exception as e:
        print(f"✗ No se pudo descargar el feed RSS: {e}", file=sys.stderr)
        return

    titles = parse_items(xml_bytes)
    titles = [clean_title(t) for t in titles if clean_title(t)]
    titles = titles[:MAX_ITEMS]
    print(f"→ {len(titles)} titulares encontrados")

    noticias = []
    for i, de_text in enumerate(titles, start=1):
        print(f"  [{i}/{len(titles)}] {de_text}")
        cat = categorize(de_text)
        noticias.append(translate_entry(de_text, cat))

    guardar(noticias, NOTICIAS_FILE)


def generar_desde_pares(pares, output_file, label):
    """pares: lista de tuplas (texto_alemán, categoría)."""
    print(f"→ Generando {label} ({len(pares)} frases)")
    resultado = []
    for i, (de_text, cat) in enumerate(pares, start=1):
        print(f"  [{i}/{len(pares)}] {de_text}")
        resultado.append(translate_entry(de_text, cat))
    guardar(resultado, output_file)


def generar_desde_banco(phrases, cat, output_file, label):
    """Banco con categoría única para todas las frases (Arví, Colombia, básico)."""
    generar_desde_pares([(p, cat) for p in phrases], output_file, label)


def generar_arvi():
    generar_desde_banco(ARVI_PHRASES, "Arví", ARVI_FILE, "Arví")


def generar_colombia():
    generar_desde_banco(COLOMBIA_PHRASES, "Kolumbien", COLOMBIA_FILE, "Diversidad Colombia")


def generar_guia():
    generar_desde_pares(GUIA_PHRASES, GUIA_FILE, "Guía turística")


def generar_basico():
    generar_desde_banco(ALEMAN_BASICO_PHRASES, "Grundlagen", ALEMAN_BASICO_FILE, "Alemán básico")


def guardar(items, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"✓ Listo: {len(items)} frases guardadas en {output_file}")


# ---------------------------------------------------------------------------
# 5) Programa principal
# ---------------------------------------------------------------------------

GENERADORES = {
    "noticias": generar_noticias,
    "arvi": generar_arvi,
    "colombia": generar_colombia,
    "guia": generar_guia,
    "basico": generar_basico,
}


def main():
    args = sys.argv[1:]
    modo = args[0].lower() if args else "all"

    if modo == "all":
        for fn in GENERADORES.values():
            fn()
            print()
    elif modo in GENERADORES:
        GENERADORES[modo]()
    else:
        print(f"✗ Modo desconocido: {modo}")
        print(f"  Usá uno de: {', '.join(GENERADORES.keys())}, all")
        sys.exit(1)


if __name__ == "__main__":
    main()
