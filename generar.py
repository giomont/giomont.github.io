import json
import urllib.request
import xml.etree.ElementTree as ET

# Función sencilla para traducir usando MyMemory API
def traducir(texto):
    try:
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(texto)}&langpair=de|es"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        return data['responseData']['translatedText']
    except Exception:
        return "Traducción no disponible"

url = "https://www.tagesschau.de/xml/rss2/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    print("⏳ Obteniendo y traduciendo noticias en alemán...")
    response = urllib.request.urlopen(req)
    xml_data = response.read()
    root = ET.fromstring(xml_data)
    
    items = root.findall('.//item')[:20]
    noticias = []

    for idx, item in enumerate(items, 1):
        title = item.find('title').text if item.find('title') is not None else ""
        category = item.find('category').text if item.find('category') is not None else "Wirtschaft"
        
        # Mapeo simple de categorías
        cat_map = {
            "Inland": "Politik",
            "Ausland": "Politik",
            "Wirtschaft": "Wirtschaft",
            "Investigativ": "Kultur"
        }
        cat_final = cat_map.get(category, "Wirtschaft")
        
        # Traducir titular
        traduccion = traducir(title)
        
        noticias.append({
            "id": idx,
            "category": cat_final,
            "text_de": title,
            "text_es": traduccion
        })
        print(f"[{idx}/20] Procesada: {title[:30]}...")

    with open('noticias.json', 'w', encoding='utf-8') as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

    print("\n✅ ¡Las 20 noticias traducidas se guardaron en noticias.json!")

except Exception as e:
    print(f"\n❌ Error: {e}")
