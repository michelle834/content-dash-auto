#!/usr/bin/env python3
"""Baja las miniaturas de los posts de la semana al repo y actualiza
datos-1a1.json.

Uso:
    python3 scripts/miniaturas.py entrada.json [--semana AAAA-MM-DD]

entrada.json es una lista de {"red": "tt"|"ig"|"li", "id": "<id del post>",
"url": "<miniatura de Windsor>", "texto": "<opcional>"}: video_thumbnail_url de
tiktok_organic, media_thumbnail_url (o media_url si es imagen o carrusel) de
instagram, y share_image_url de linkedin_organic. "texto" solo hace falta en
LinkedIn (share_text), porque la hoja del dash no trae el texto de esos posts.

Las ligas de TikTok e Instagram caducan en días, por eso se guardan como
archivo: thumbs/<red>-<id>.jpg, de 240 px de ancho (sips, de macOS).
YouTube no necesita: su miniatura sale de i.ytimg.com con el id del video.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(RAIZ, "thumbs")
INDICE = os.path.join(RAIZ, "datos-1a1.json")


def bajar(url, destino):
    tmp = destino + ".tmp"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r, open(tmp, "wb") as fh:
        fh.write(r.read())
    # a JPG de 240 px de ancho; sips lee webp en macOS reciente
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "60",
                    "--resampleWidth", "240", tmp, "--out", destino],
                   check=True, capture_output=True)
    os.remove(tmp)


def limpiar(t):
    """LinkedIn manda los hashtags como {hashtag|\\#|Tema} y escapa paréntesis."""
    t = re.sub(r"\{hashtag\|\\?#\|([^}]*)\}", r"#\1", t)
    t = t.replace("\\(", "(").replace("\\)", ")")
    return re.sub(r"\s+", " ", t).strip()


def main(entrada, semana=None):
    items = json.load(open(entrada, encoding="utf-8"))
    os.makedirs(CARPETA, exist_ok=True)
    indice = json.load(open(INDICE, encoding="utf-8")) if os.path.exists(INDICE) else {}
    thumbs = indice.get("thumbs", {})
    textos = indice.get("textos", {})
    nuevas = fallas = 0
    for it in items:
        red, pid, url = it.get("red"), str(it.get("id") or ""), it.get("url")
        if red not in ("tt", "ig", "li") or not pid:
            continue
        if it.get("texto"):
            textos[pid] = limpiar(it["texto"])[:400]
        if not url:
            continue
        nombre = f"{red}-{pid}.jpg"
        ruta = os.path.join(CARPETA, nombre)
        if not os.path.exists(ruta):
            try:
                bajar(url, ruta)
                nuevas += 1
            except Exception as e:  # una miniatura que falla no detiene las demás
                fallas += 1
                print("falló", nombre, e, file=sys.stderr)
                continue
        thumbs[pid] = "thumbs/" + nombre
    cdmx = timezone(timedelta(hours=-6))
    indice["thumbs"] = thumbs
    indice["textos"] = textos
    indice["generado"] = datetime.now(cdmx).strftime("%Y-%m-%d %H:%M")
    if semana:
        indice["ultima_semana"] = semana
    with open(INDICE, "w", encoding="utf-8") as fh:
        json.dump(indice, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"ok: {nuevas} nuevas, {fallas} fallas, {len(thumbs)} en total")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    sem = None
    if "--semana" in args:
        i = args.index("--semana")
        sem = args[i + 1]
        del args[i:i + 2]
    main(args[0], sem)
