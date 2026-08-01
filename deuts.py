#!/usr/bin/env python3
"""
deuts.py
--------
Genera UN SOLO archivo de audio (deuts.mp3) con TODAS las frases
en ALEMÁN de los JSON de Wegweiser (solo clave "de", se ignoran
en/es/fr).

Orden de archivos (fijo, edítalo en FILES si quieres cambiarlo):
    1. aleman_basico.json
    2. guia_turistica.json
    3. arvi.json
    4. colombia_diversidad.json
    5. noticias.json   (si existe)

Requisitos (instalar antes de correr):
    pip install gTTS pydub
    pkg install ffmpeg -y

Uso:
    python3 deuts.py
    python3 deuts.py --out mi_aleman.mp3
    python3 deuts.py --dir /ruta/donde/estan/los/json
"""

import argparse
import json
import os
import sys
import time

try:
    from gtts import gTTS
except ImportError:
    print("✗ Falta gTTS. Instalalo con: pip install gTTS", file=sys.stderr)
    sys.exit(1)

try:
    from pydub import AudioSegment
except ImportError:
    print("✗ Falta pydub. Instalalo con: pip install pydub", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

FILES = [
    "aleman_basico.json",
    "guia_turistica.json",
    "arvi.json",
    "colombia_diversidad.json",
    "noticias.json",
]

GTTS_LANG_DE = "de"

PAUSE_ENTRE_FRASES_MS = 900       # pausa entre una frase y la siguiente

TEMP_DIR = "temp_audio_deuts"
REQUEST_DELAY = 0.3               # segundos entre llamadas a gTTS (evita bloqueos)


# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------

def cargar_frases(directorio):
    frases = []
    for nombre in FILES:
        ruta = os.path.join(directorio, nombre)
        if not os.path.exists(ruta):
            print(f"✗ No encontrado (se omite): {ruta}", file=sys.stderr)
            continue
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"→ {nombre}: {len(data)} frases")
        frases.extend(data)
    return frases


def tts_a_segmento(texto, indice, temp_dir):
    """Genera TTS en alemán de `texto` y lo devuelve como AudioSegment."""
    ruta_tmp = os.path.join(temp_dir, f"{indice:04d}_de.mp3")
    tts = gTTS(text=texto, lang=GTTS_LANG_DE)
    tts.save(ruta_tmp)
    return AudioSegment.from_mp3(ruta_tmp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Carpeta donde están los JSON")
    parser.add_argument("--out", default="deuts.mp3", help="Nombre del audio final")
    args = parser.parse_args()

    frases = cargar_frases(args.dir)
    if not frases:
        print("✗ No se cargó ninguna frase. Revisa la carpeta --dir.", file=sys.stderr)
        sys.exit(1)

    total = len(frases)
    print(f"\n→ Total de frases a procesar: {total}")
    print("→ Idioma: solo alemán (de)")

    os.makedirs(TEMP_DIR, exist_ok=True)
    silencio_frases = AudioSegment.silent(duration=PAUSE_ENTRE_FRASES_MS)

    audio_final = AudioSegment.empty()
    indice_global = 0
    errores = 0
    omitidas = 0

    for i, entrada in enumerate(frases, start=1):
        texto = entrada.get("de", "").strip()
        if not texto:
            omitidas += 1
            continue

        preview = texto[:40]
        print(f"  [{i}/{total}] {preview}...")

        try:
            seg = tts_a_segmento(texto, indice_global, TEMP_DIR)
            audio_final += seg
            audio_final += silencio_frases
        except Exception as e:
            errores += 1
            print(f"    ! Falló TTS: {e}", file=sys.stderr)

        indice_global += 1
        time.sleep(REQUEST_DELAY)

    print(f"\n→ Exportando a {args.out} ...")
    audio_final.export(args.out, format="mp3")

    # limpiar temporales
    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))
    os.rmdir(TEMP_DIR)

    duracion_min = len(audio_final) / 1000 / 60
    print(f"✓ Listo: {args.out} ({duracion_min:.1f} min, {errores} errores, {omitidas} sin texto 'de')")


if __name__ == "__main__":
    main()
