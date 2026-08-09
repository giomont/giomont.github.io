#!/usr/bin/env python3
"""
generar.py
----------
Genera los archivos JSON de Wegweiser:

  noticias.json  -> descarga el feed RSS de Tagesschau, categoriza por
                     palabras clave y traduce cada titular (alemán -> inglés,
                     alemán -> español, alemán -> francés) con la API
                     gratuita de MyMemory. Se renueva sola cada vez que
                     Tagesschau publica noticias nuevas.

  arvi.json      -> traduce un subconjunto rotativo de un banco de 100
                     frases en alemán sobre el Parque Arví (Medellín).

  colombia_diversidad.json -> ídem con un banco de 100 frases sobre la
                     diversidad turística de Colombia.

  guia_turistica.json -> ídem con un banco de 100 frases útiles para guías
                     turísticos (orientación, hotel, restaurante, transporte,
                     emergencias, comunicación, dinero, sitios de interés).

  aleman_basico.json -> ídem con un banco de 100 frases básicas de alemán
                     para el guía (categoría única "Grundlagen").

Rotación diaria
----------------
Los cuatro bancos "fijos" (arví, colombia, guía, básico) tienen 100 frases
cada uno. Para no tener que traducir las 100 cada vez (tardaría mucho y
gastaría la cuota gratuita de MyMemory) el script selecciona automáticamente
un subconjunto de ITEMS_POR_LISTA frases, distinto cada día, usando la fecha
como semilla (ver seleccionar_rotando()). Así, cada vez que se corre
`generar.py listas` (o `all`) las listas también "se actualizan" como las
noticias: el contenido va rotando día a día por todo el banco de 100.

Uso:
    python3 generar.py noticias      # solo noticias.json
    python3 generar.py arvi          # solo arvi.json
    python3 generar.py colombia      # solo colombia_diversidad.json
    python3 generar.py guia          # solo guia_turistica.json
    python3 generar.py basico        # solo aleman_basico.json
    python3 generar.py listas        # arvi + colombia + guia + basico (sin noticias)
    python3 generar.py all           # noticias + listas (todo, por defecto)

Para agregar más frases a cualquiera de los bancos, simplemente agregá una
línea en alemán a ARVI_PHRASES, COLOMBIA_PHRASES, GUIA_PHRASES (con su
categoría) o ALEMAN_BASICO_PHRASES más abajo y volvé a correr el script:
la traducción al inglés/español/francés se genera sola.

Solo usa la librería estándar de Python (urllib), sin dependencias externas.
"""

import datetime
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

# Cuántas frases del banco de 100 se traducen y publican en cada corrida.
# El resto queda "en reserva" y va apareciendo en las corridas siguientes
# gracias a seleccionar_rotando().
ITEMS_POR_LISTA = 20

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
# Bancos de frases (100 por lista). Se agregan/editan líneas acá; la
# traducción se genera automáticamente y la rotación diaria se encarga de
# ir mostrando todo el banco de a poco.
# ---------------------------------------------------------------------------

ARVI_PHRASES = [
    # --- Ubicación y datos generales (original) ---
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
    # --- Flora ---
    "Im Nebelwald wachsen viele Arten von Orchideen.",
    "Man findet dort auch Bromelien und Moose an den Bäumen.",
    "Der Wald beherbergt jahrhundertealte Eichen.",
    "Viele Pflanzen im Park werden für traditionelle Medizin genutzt.",
    "Es gibt einen botanischen Lehrpfad mit beschrifteten Pflanzen.",
    # --- Fauna ---
    "Im Park leben mehr als 200 Vogelarten.",
    "Man kann Kolibris an den Blumen beobachten.",
    "Auch Eichhörnchen und Opossums leben im Wald.",
    "Nachts hört man manchmal den Ruf von Eulen.",
    "Schmetterlinge verschiedener Farben fliegen zwischen den Bäumen.",
    "Es gibt ein Schmetterlingshaus für Besucher.",
    # --- Aktivitäten ---
    "Besucher können an geführten Nachtwanderungen teilnehmen.",
    "Es gibt Workshops über traditionelle Landwirtschaft.",
    "Man kann im Park Fahrrad fahren.",
    "Familien können auf dem Bauernmarkt lokale Produkte kaufen.",
    "Es gibt einen Abenteuerpark mit Seilrutschen.",
    "Kinder können im Interpretationszentrum spielerisch lernen.",
    "Am Wochenende finden oft kulturelle Veranstaltungen statt.",
    # --- Wanderwege ---
    "Der Weg \"Piedras Blancas\" führt zu großen Felsformationen.",
    "Ein anderer Weg führt zum Aussichtspunkt \"Mirador Astronómico\".",
    "Die Wanderwege sind unterschiedlich schwer.",
    "Manche Wege eignen sich auch für Familien mit kleinen Kindern.",
    "Wanderführer erklären die Bedeutung der Pflanzen und Tiere.",
    "Auf einigen Wegen kann man alte Steinwege der Ureinwohner sehen.",
    # --- Ökosystem ---
    "Der Nebelwald speichert große Mengen an Wasser.",
    "Der Park liefert einen Teil des Trinkwassers für Medellín.",
    "Der Wald hilft, das Klima der Region zu regulieren.",
    "Viele Bäche entspringen im Gebiet des Parks.",
    "Der Nebelwald ist wichtig für den Wasserkreislauf der Stadt.",
    # --- Verkehrsanbindung ---
    "Von der Seilbahnstation Arví aus gibt es Busse ins Zentrum.",
    "Man kann auch mit dem Fahrrad zum Park fahren.",
    "Es gibt Parkplätze für Besucher mit eigenem Auto.",
    "Die Anfahrt mit der Seilbahn bietet einen Blick über die Stadt.",
    "Am Wochenende ist die Seilbahn oft sehr voll.",
    # --- Umweltschutz ---
    "Der Park arbeitet mit lokalen Gemeinden am Naturschutz.",
    "Besucher werden gebeten, ihren Müll mitzunehmen.",
    "Es gibt Programme zur Wiederaufforstung im Park.",
    "Freiwillige helfen bei der Pflege der Wanderwege.",
    "Der Park schützt bedrohte Pflanzen- und Tierarten.",
    # --- Gemeinschaft / Artesanías ---
    "Lokale Handwerker verkaufen Kunsthandwerk im Park.",
    "Man findet dort auch handgemachten Schmuck.",
    "Die Gemeinden im Park leben teilweise von nachhaltigem Tourismus.",
    "Es gibt kleine Cafés mit Blick auf den Wald.",
    "Lokale Familien bieten traditionelle Gerichte an.",
    # --- Klima ---
    "Im Park regnet es häufig, besonders am Nachmittag.",
    "Es empfiehlt sich, eine Regenjacke mitzunehmen.",
    "Die Luftfeuchtigkeit im Nebelwald ist sehr hoch.",
    "Am Morgen ist oft dichter Nebel zu sehen.",
    # --- Sicherheit ---
    "Besucher sollten festes Schuhwerk tragen.",
    "Es ist ratsam, auf den markierten Wegen zu bleiben.",
    "Bei Gewitter sollte man offene Aussichtspunkte meiden.",
    "Ein Erste-Hilfe-Kasten ist im Besucherzentrum verfügbar.",
    "Die Parkwächter helfen bei Notfällen.",
    # --- Empfehlungen ---
    "Am besten besucht man den Park früh am Morgen.",
    "An Wochentagen ist weniger los als am Wochenende.",
    "Eine Wasserflasche sollte man immer dabeihaben.",
    "Sonnencreme wird trotz des Nebels empfohlen.",
    "Ein Fernglas ist ideal für die Vogelbeobachtung.",
    # --- Geschichte ---
    "Vor der spanischen Kolonialzeit lebten dort indigene Gemeinschaften.",
    "Archäologen haben im Park alte Wege und Terrassen gefunden.",
    "Die Region war einst ein wichtiger Handelsweg der Ureinwohner.",
    "Im 20. Jahrhundert wurde das Gebiet zum Wasserschutzgebiet erklärt.",
    "Seit 2008 wird der Park touristisch entwickelt.",
    # --- Bildung ---
    "Das Interpretationszentrum informiert über die Geschichte des Parks.",
    "Schulen organisieren oft Exkursionen in den Park.",
    "Es gibt Umweltbildungsprogramme für Kinder.",
    "Führungen erklären die Bedeutung des Nebelwaldes.",
    # --- Sterne-Beobachtung ---
    "Wegen der geringen Lichtverschmutzung kann man Sterne gut beobachten.",
    "Es werden gelegentlich astronomische Nächte organisiert.",
    "Der Mirador Astronómico ist ein beliebter Ort dafür.",
    # --- Ruhe / Meditation ---
    "Viele Besucher kommen zum Wandern und zur Entspannung.",
    "Der Wald wird oft für Achtsamkeitsübungen genutzt.",
    "Die Ruhe des Waldes zieht auch Künstler an.",
    # --- Familienausflüge ---
    "Der Park ist ein beliebtes Ziel für Familienausflüge.",
    "Es gibt Picknickbereiche mit Tischen und Bänken.",
    "Kinder können im Streichelzoo Tiere kennenlernen.",
    "Am Eingang gibt es Informationstafeln für Besucher.",
    # --- Fotografie ---
    "Fotografen schätzen das besondere Licht im Nebelwald.",
    "Der Park bietet viele Motive für Naturfotografie.",
    "Drohnenflüge sind in bestimmten Zonen eingeschränkt.",
]

COLOMBIA_PHRASES = [
    # --- Original ---
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
    # --- Regionen ---
    "Die Karibikküste Kolumbiens ist bekannt für ihre weißen Sandstrände.",
    "Die Pazifikküste bietet Wale, Mangroven und ursprüngliche Natur.",
    "Die Anden durchqueren das Land von Süden nach Norden.",
    "Im Amazonasgebiet lebt ein Großteil der Artenvielfalt Kolumbiens.",
    "Die Region Orinoquía ist bekannt für ihre weiten Ebenen, die Llanos.",
    "Die Insel San Andrés gehört zum kolumbianischen Karibikgebiet.",
    "Die Wüste La Guajira liegt im äußersten Norden des Landes.",
    "Das Kaffee-Dreieck liegt zwischen den Departamentos Caldas, Quindío und Risaralda.",
    "Die Region Antioquia ist für ihre Berglandschaften bekannt.",
    "Jede Region Kolumbiens hat ein eigenes typisches Essen.",
    # --- Städte ---
    "Bogotá liegt auf einer Hochebene in den Anden.",
    "Cartagena ist berühmt für seine koloniale Altstadt.",
    "Medellín wird oft \"Stadt des ewigen Frühlings\" genannt.",
    "Cali gilt als Hauptstadt der Salsa-Musik.",
    "Santa Marta ist die älteste Stadt Kolumbiens.",
    "Barranquilla ist bekannt für seinen Karneval.",
    "Popayán wird wegen seiner weißen Gebäude \"weiße Stadt\" genannt.",
    "Villa de Leyva hat einen der größten Kopfsteinpflasterplätze Südamerikas.",
    # --- Natur / Nationalparks ---
    "Der Nationalpark Tayrona liegt an der Karibikküste.",
    "Der Nationalpark Los Nevados hat schneebedeckte Vulkane.",
    "Das Tal Cocora ist berühmt für seine hohen Wachspalmen.",
    "Der Amazonas-Regenwald erstreckt sich über mehrere Departamentos.",
    "Der Nationalpark Chicaque liegt in der Nähe von Bogotá.",
    "Kolumbien hat 59 Nationalparks und Schutzgebiete.",
    "Der Cocuy-Nationalpark bietet Gletscher und hohe Gipfel.",
    "Kolumbien ist eines der artenreichsten Länder der Welt.",
    "Im Land gibt es mehr als 1.900 Vogelarten.",
    "Der Fluss Caño Cristales wird wegen seiner Farben \"Regenbogenfluss\" genannt.",
    # --- Kultur / Feste ---
    "Der Karneval von Barranquilla ist UNESCO-Weltkulturerbe.",
    "Das Ibero-Amerikanische Theaterfestival findet in Bogotá statt.",
    "Die Blumenparade in Medellín heißt \"Feria de las Flores\".",
    "Beim Fest der Vírgenes werden traditionell Kerzen angezündet.",
    "In San Basilio de Palenque lebt eine der ersten freien afrikanischen Gemeinschaften Amerikas.",
    "Kolumbien hat eine große kulturelle Vielfalt durch indigene, afrikanische und europäische Wurzeln.",
    "Es gibt mehr als 80 indigene Völker in Kolumbien.",
    "Das Vallenato-Festival findet jährlich in Valledupar statt.",
    "Die Osterprozessionen in Popayán sind UNESCO-immaterielles Erbe.",
    "Kolumbien feiert im August den Gründungstag von Cartagena.",
    # --- Gastronomie ---
    "Die Bandeja Paisa ist ein typisches Gericht aus Antioquia.",
    "Arepas werden in ganz Kolumbien auf unterschiedliche Weise zubereitet.",
    "Ajiaco ist eine traditionelle Suppe aus Bogotá.",
    "An der Karibikküste isst man viel Fisch und Kokosreis.",
    "Empanadas sind ein beliebter Snack im ganzen Land.",
    "Tropische Früchte wie Lulo und Guanábana wachsen in Kolumbien.",
    "Der kolumbianische Kaffee gilt als einer der besten der Welt.",
    "Chocolate santafereño wird traditionell mit Käse serviert.",
    # --- Musik / Tanz ---
    "Cumbia ist einer der bekanntesten Musikstile Kolumbiens.",
    "Salsa hat in Cali eine besonders starke Tradition.",
    "Vallenato wird oft mit Akkordeon gespielt.",
    "Champeta stammt ursprünglich aus Cartagena.",
    "Bambuco ist ein traditioneller Tanz aus der Andenregion.",
    "Musik spielt bei fast jedem kolumbianischen Fest eine zentrale Rolle.",
    # --- Kaffee ---
    "Die kolumbianische Kaffeeregion ist UNESCO-Weltkulturerbe.",
    "Viele Kaffeefincas bieten Führungen für Touristen an.",
    "Der Kaffeeanbau prägt die Kultur der Region stark.",
    "Besucher können den Prozess vom Anbau bis zur Tasse erleben.",
    "Kolumbien exportiert Kaffee in viele Länder der Welt.",
    "Die Ernte des Kaffees erfolgt meist von Hand.",
    # --- Handwerk ---
    "Die Wayuu-Gemeinschaft ist bekannt für ihre gewebten Taschen.",
    "Kunsthandwerk aus Filigranarbeit stammt aus Mompox.",
    "Sombrero vueltiao ist ein traditioneller Hut aus der Karibikregion.",
    "Keramikkunst hat in mehreren Regionen Kolumbiens eine lange Tradition.",
    "Handwerksmärkte findet man in fast jeder Stadt Kolumbiens.",
    # --- Abenteuertourismus ---
    "In San Gil kann man Rafting und Paragliding ausprobieren.",
    "Der Nationalpark Los Nevados eignet sich für Bergsteigen.",
    "Tauchen ist an den Riffen von San Andrés sehr beliebt.",
    "In der Sierra Nevada de Santa Marta gibt es mehrtägige Wandertouren.",
    "Canyoning wird in mehreren Regionen Kolumbiens angeboten.",
    "Mountainbiking ist in der Kaffeeregion sehr beliebt.",
    # --- Nachhaltigkeit ---
    "Viele Gemeinschaften setzen auf nachhaltigen Ökotourismus.",
    "Indigene Reservate bieten oft geführte Naturerlebnisse an.",
    "Kolumbien möchte den nachhaltigen Tourismus weiter ausbauen.",
    "Der Schutz der Artenvielfalt hat für den Tourismus hohe Priorität.",
    "Lokale Gemeinschaften profitieren direkt vom Ökotourismus.",
    # --- Sicherheit / Praktisches ---
    "Es wird empfohlen, offizielle Reiseführer zu buchen.",
    "In vielen Touristenorten gibt es spezielle Touristenpolizei.",
    "Es ist ratsam, sich vor der Reise über die Region zu informieren.",
    "Reisende sollten wichtige Dokumente immer bei sich tragen.",
    "In höher gelegenen Gebieten sollte man sich langsam akklimatisieren.",
    "Kolumbien hat in den letzten Jahren stark in Tourismus-Sicherheit investiert.",
]

# guia_turistica.json: cada frase tiene su propia categoría (tupla de dos
# elementos: texto en alemán, categoría).
GUIA_PHRASES = [
    # --- Original ---
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
    # --- Orientierung ---
    ("Entschuldigung, wie komme ich zum Hauptplatz?", "Orientierung"),
    ("Ist das Rathaus weit von hier entfernt?", "Orientierung"),
    ("Können Sie mir die Richtung zum Hafen zeigen?", "Orientierung"),
    ("Wo befindet sich die nächste Bushaltestelle?", "Orientierung"),
    ("Gibt es hier in der Nähe einen Stadtplan?", "Orientierung"),
    ("Wie weit ist es bis zum Aussichtspunkt?", "Orientierung"),
    ("Muss ich hier rechts oder links abbiegen?", "Orientierung"),
    ("Wo ist der Eingang zum Park?", "Orientierung"),
    ("Können Sie mir helfen, mich zu orientieren?", "Orientierung"),
    ("Ist dieser Weg der kürzeste zum Zentrum?", "Orientierung"),
    # --- Hotel ---
    ("Ich habe ein Zimmer für heute Nacht reserviert.", "Hotel"),
    ("Um wie viel Uhr ist der Check-out?", "Hotel"),
    ("Können Sie mein Gepäck aufbewahren?", "Hotel"),
    ("Gibt es einen Weckdienst im Hotel?", "Hotel"),
    ("Ist Frühstück im Preis inbegriffen?", "Hotel"),
    ("Können Sie mir ein anderes Zimmer geben?", "Hotel"),
    ("Gibt es einen Aufzug in diesem Hotel?", "Hotel"),
    ("Wo finde ich den Pool des Hotels?", "Hotel"),
    ("Kann ich früher einchecken?", "Hotel"),
    ("Funktioniert die Klimaanlage im Zimmer?", "Hotel"),
    # --- Restaurant ---
    ("Können wir einen Tisch für vier Personen haben?", "Restaurant"),
    ("Was empfehlen Sie uns heute?", "Restaurant"),
    ("Ist dieses Gericht scharf?", "Restaurant"),
    ("Wir hätten gerne die Getränkekarte.", "Restaurant"),
    ("Kann ich das Gericht ohne Fleisch bekommen?", "Restaurant"),
    ("Gibt es hier lokale Spezialitäten?", "Restaurant"),
    ("Können Sie das bitte zum Mitnehmen einpacken?", "Restaurant"),
    ("Akzeptieren Sie Kreditkarten?", "Restaurant"),
    ("Wir würden gern draußen sitzen.", "Restaurant"),
    ("Können wir noch etwas Wasser bekommen?", "Restaurant"),
    # --- Transport ---
    ("Wann fährt der nächste Bus ab?", "Transport"),
    ("Wo kann ich ein Ticket für den Zug kaufen?", "Transport"),
    ("Gibt es eine direkte Verbindung zum Flughafen?", "Transport"),
    ("Ist dieser Sitzplatz noch frei?", "Transport"),
    ("Wie lange dauert die Fahrt bis zur Küste?", "Transport"),
    ("Kann ich das Ticket im Voraus reservieren?", "Transport"),
    ("Fährt dieser Bus zum Stadtzentrum?", "Transport"),
    ("Wo finde ich einen Taxistand?", "Transport"),
    ("Gibt es einen Fahrradverleih in der Nähe?", "Transport"),
    ("Muss ich hier umsteigen?", "Transport"),
    # --- Notfälle ---
    ("Rufen Sie bitte sofort einen Krankenwagen!", "Notfälle"),
    ("Ich habe meinen Reisepass verloren.", "Notfälle"),
    ("Wo ist das nächste Krankenhaus?", "Notfälle"),
    ("Ich habe mich verletzt, können Sie mir helfen?", "Notfälle"),
    ("Bitte rufen Sie die Polizei.", "Notfälle"),
    ("Mir ist schlecht, ich brauche einen Arzt.", "Notfälle"),
    ("Gibt es hier eine Notaufnahme?", "Notfälle"),
    ("Mein Gepäck wurde gestohlen.", "Notfälle"),
    ("Ich habe eine allergische Reaktion.", "Notfälle"),
    ("Wo finde ich die nächste Feuerwache?", "Notfälle"),
    # --- Kommunikation ---
    ("Ich verstehe leider nur ein bisschen Deutsch.", "Kommunikation"),
    ("Können Sie das bitte aufschreiben?", "Kommunikation"),
    ("Wie sagt man das auf Spanisch?", "Kommunikation"),
    ("Können Sie das für mich übersetzen?", "Kommunikation"),
    ("Ich brauche einen Moment, um zu antworten.", "Kommunikation"),
    ("Bitte sprechen Sie etwas langsamer.", "Kommunikation"),
    ("Können Sie das Wort buchstabieren?", "Kommunikation"),
    ("Ich habe eine Frage zu unserer Route.", "Kommunikation"),
    ("Verzeihung, ich habe das nicht verstanden.", "Kommunikation"),
    ("Danke, dass Sie so geduldig sind.", "Kommunikation"),
    # --- Geld ---
    ("Wo finde ich den nächsten Geldautomaten?", "Geld"),
    ("Akzeptieren Sie auch US-Dollar?", "Geld"),
    ("Kann ich hier mit Karte bezahlen?", "Geld"),
    ("Wie ist der aktuelle Wechselkurs?", "Geld"),
    ("Wo kann ich eine Quittung bekommen?", "Geld"),
    ("Gibt es hier eine Bank in der Nähe?", "Geld"),
    ("Können Sie mir kleineres Geld wechseln?", "Geld"),
    ("Ist Trinkgeld in Kolumbien üblich?", "Geld"),
    ("Wie viel kostet der Eintritt insgesamt?", "Geld"),
    ("Gibt es einen Rabatt für Gruppen?", "Geld"),
    # --- Sehenswürdigkeiten ---
    ("Wie lange dauert die Führung durch das Museum?", "Sehenswürdigkeiten"),
    ("Gibt es einen Audioguide auf Deutsch?", "Sehenswürdigkeiten"),
    ("Wann schließt diese Sehenswürdigkeit?", "Sehenswürdigkeiten"),
    ("Ist Fotografieren hier erlaubt?", "Sehenswürdigkeiten"),
    ("Gibt es einen ermäßigten Eintritt für Studenten?", "Sehenswürdigkeiten"),
    ("Können wir eine Gruppenführung buchen?", "Sehenswürdigkeiten"),
    ("Welche Sehenswürdigkeit empfehlen Sie als Erstes?", "Sehenswürdigkeiten"),
    ("Gibt es einen Souvenirladen am Ausgang?", "Sehenswürdigkeiten"),
    ("Ist der Zugang für Rollstühle möglich?", "Sehenswürdigkeiten"),
    ("Wie weit ist es zum nächsten Aussichtspunkt?", "Sehenswürdigkeiten"),
]

# aleman_basico.json: todas las frases usan la categoría única "Grundlagen".
ALEMAN_BASICO_PHRASES = [
    # --- Original ---
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
    # --- Begrüßung / Höflichkeit ---
    "Guten Morgen! Ich hoffe, Sie haben gut geschlafen.",
    "Guten Abend, herzlich willkommen zur Abendtour.",
    "Wie geht es Ihnen heute?",
    "Es freut mich, Sie kennenzulernen.",
    "Bitte, nach Ihnen.",
    "Entschuldigen Sie die Verspätung.",
    "Es tut mir leid für die Unannehmlichkeiten.",
    "Ich wünsche Ihnen einen schönen Tag.",
    "Auf Wiedersehen und bis zum nächsten Mal!",
    "Schönen Aufenthalt in Kolumbien!",
    # --- Zahlen / Zeit ---
    "Wir treffen uns in fünf Minuten.",
    "Der Ausflug beginnt um acht Uhr morgens.",
    "Wir haben noch zehn Minuten Zeit.",
    "Es ist jetzt Viertel nach neun.",
    "Die Pause dauert eine halbe Stunde.",
    "Wir sind in zwanzig Minuten am Ziel.",
    "Bitte seien Sie pünktlich um sieben Uhr.",
    "Der Rückweg dauert etwa eine Stunde.",
    "Wir haben noch drei Stopps vor uns.",
    "Es ist gleich Mittag.",
    # --- Wetter ---
    "Heute ist es sehr sonnig.",
    "Es könnte später regnen.",
    "Bitte nehmen Sie einen Regenschirm mit.",
    "Am Morgen ist es oft neblig.",
    "Die Temperatur ist heute angenehm kühl.",
    "Es wird heute Nachmittag windig sein.",
    "Ziehen Sie sich warm an, es ist kalt.",
    "Die Sonne ist hier sehr stark.",
    # --- Anweisungen / Führung ---
    "Bitte bleiben Sie in der Gruppe.",
    "Folgen Sie mir bitte auf diesem Weg.",
    "Wir machen jetzt eine kurze Pause.",
    "Bitte passen Sie hier auf die Stufen auf.",
    "Hier können Sie Fotos machen.",
    "Bitte berühren Sie die Pflanzen nicht.",
    "Wir gehen jetzt weiter zum nächsten Punkt.",
    "Bitte bleiben Sie auf dem markierten Weg.",
    "Halten Sie sich bitte am Geländer fest.",
    "Wir warten hier auf die restliche Gruppe.",
    # --- Fragen / Antworten ---
    "Haben alle ihre Wasserflasche dabei?",
    "Fühlt sich jemand nicht gut?",
    "Möchten Sie eine Pause machen?",
    "Ist die Route für Sie zu anstrengend?",
    "Haben Sie noch Fragen zur Tour?",
    "Möchten Sie mehr über diese Pflanze erfahren?",
    "Gefällt Ihnen die Aussicht?",
    "Sind Sie bereit für den nächsten Abschnitt?",
    "Brauchen Sie eine Pause zum Fotografieren?",
    "Ist allen warm genug angezogen?",
    # --- Notfall / Sicherheit ---
    "Bleiben Sie bitte ruhig, alles ist unter Kontrolle.",
    "Im Notfall folgen Sie bitte meinen Anweisungen.",
    "Der Notausgang ist dort drüben.",
    "Bitte melden Sie sich, wenn etwas fehlt.",
    "Achten Sie bitte auf Ihre persönlichen Sachen.",
    "Wenn Sie sich verlaufen, bleiben Sie an Ort und Stelle.",
    "Ich habe immer ein Erste-Hilfe-Set dabei.",
    "Bitte informieren Sie mich über Allergien.",
    # --- Small talk ---
    "Woher kommen Sie?",
    "Ist das Ihr erster Besuch in Kolumbien?",
    "Wie gefällt Ihnen die Reise bisher?",
    "Was hat Ihnen am besten gefallen?",
    "Möchten Sie ein Foto von der Gruppe?",
    "Reisen Sie allein oder mit Familie?",
    "Wie lange bleiben Sie in Medellín?",
    "Kennen Sie schon die kolumbianische Küche?",
    # --- Abschied / Dank ---
    "Vielen Dank, dass Sie an der Tour teilgenommen haben.",
    "Ich hoffe, die Tour hat Ihnen gefallen.",
    "Es war mir eine Freude, Sie zu begleiten.",
    "Bitte bewerten Sie unsere Tour, wenn möglich.",
    "Kommen Sie gerne wieder nach Kolumbien.",
    "Ich hoffe, wir sehen uns bald wieder.",
    "Passen Sie gut auf sich auf.",
    "Gute Heimreise!",
    # --- Alltag / Reisebegleitung ---
    "Haben Sie genug Sonnencreme dabei?",
    "Vergessen Sie nicht, Ihre Kamera aufzuladen.",
    "Bitte trinken Sie regelmäßig Wasser.",
    "Wir machen jetzt eine kurze Fotopause.",
    "Der Bus wartet schon auf uns.",
    "Bitte zählen wir kurz die Gruppe durch.",
    "Hat jemand sein Handy verloren?",
    "Wir sind fast am Ausgangspunkt zurück.",
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
# 3) Rotación diaria de los bancos fijos (arví, colombia, guía, básico)
# ---------------------------------------------------------------------------

def seleccionar_rotando(items, cantidad, dia=None):
    """Selecciona `cantidad` elementos de `items`, rotando de forma
    determinística según la fecha: cada día se publica un subconjunto
    distinto (pero estable durante ese día) del banco completo. Si el
    banco tiene menos elementos que `cantidad`, se devuelven todos.

    Esto hace que, igual que noticias.json cambia solo porque Tagesschau
    publica titulares nuevos, las listas fijas también "se actualicen":
    cada corrida de generar.py muestra una porción distinta del banco de
    100 frases, hasta recorrerlo por completo y empezar de nuevo.
    """
    if not items:
        return []
    if cantidad >= len(items):
        return list(items)
    if dia is None:
        dia = datetime.date.today().toordinal()
    # multiplicamos el día por un número que no es múltiplo del tamaño
    # típico de los bancos, para que la ventana avance de forma pareja.
    inicio = (dia * 7) % len(items)
    rotado = items[inicio:] + items[:inicio]
    return rotado[:cantidad]


# ---------------------------------------------------------------------------
# 4) Traducción con MyMemory (de -> en, de -> es, de -> fr)
# ---------------------------------------------------------------------------

def translate(text, target_lang):
    """Traduce `text` del alemán a `target_lang` ('en', 'es' o 'fr') usando
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
# 5) Generadores por fuente
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
    print(f"→ Generando {label} ({len(pares)} frases de este banco rotativo)")
    resultado = []
    for i, (de_text, cat) in enumerate(pares, start=1):
        print(f"  [{i}/{len(pares)}] {de_text}")
        resultado.append(translate_entry(de_text, cat))
    guardar(resultado, output_file)


def generar_desde_banco(phrases, cat, output_file, label):
    """Banco con categoría única para todas las frases (Arví, Colombia, básico)."""
    generar_desde_pares([(p, cat) for p in phrases], output_file, label)


def generar_arvi():
    seleccion = seleccionar_rotando(ARVI_PHRASES, ITEMS_POR_LISTA)
    generar_desde_banco(seleccion, "Arví", ARVI_FILE, "Arví")


def generar_colombia():
    seleccion = seleccionar_rotando(COLOMBIA_PHRASES, ITEMS_POR_LISTA)
    generar_desde_banco(seleccion, "Kolumbien", COLOMBIA_FILE, "Diversidad Colombia")


def generar_guia():
    seleccion = seleccionar_rotando(GUIA_PHRASES, ITEMS_POR_LISTA)
    generar_desde_pares(seleccion, GUIA_FILE, "Guía turística")


def generar_basico():
    seleccion = seleccionar_rotando(ALEMAN_BASICO_PHRASES, ITEMS_POR_LISTA)
    generar_desde_banco(seleccion, "Grundlagen", ALEMAN_BASICO_FILE, "Alemán básico")


def guardar(items, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"✓ Listo: {len(items)} frases guardadas en {output_file}")


# ---------------------------------------------------------------------------
# 6) Programa principal
# ---------------------------------------------------------------------------

# Generadores individuales (uno por archivo JSON).
GENERADORES = {
    "noticias": generar_noticias,
    "arvi": generar_arvi,
    "colombia": generar_colombia,
    "guia": generar_guia,
    "basico": generar_basico,
}

# Nombres de los generadores que forman el grupo "listas" (todo menos noticias).
LISTAS_MODOS = ("arvi", "colombia", "guia", "basico")


def generar_listas():
    """Regenera las cuatro listas fijas (con su porción rotada del día),
    sin tocar noticias.json."""
    for nombre in LISTAS_MODOS:
        GENERADORES[nombre]()
        print()


def main():
    args = sys.argv[1:]
    modo = args[0].lower() if args else "all"

    if modo == "all":
        generar_noticias()
        print()
        generar_listas()
    elif modo == "listas":
        generar_listas()
    elif modo in GENERADORES:
        GENERADORES[modo]()
    else:
        print(f"✗ Modo desconocido: {modo}")
        print(f"  Usá uno de: {', '.join(GENERADORES.keys())}, listas, all")
        sys.exit(1)


if __name__ == "__main__":
    main()
