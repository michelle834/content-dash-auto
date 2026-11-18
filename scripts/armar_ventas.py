#!/usr/bin/env python3
"""Arma datos-ventas.json (pestaña «Signups y ventas») a partir de las
respuestas del Querybuilder de heru.

Uso:
    python3 scripts/armar_ventas.py crudo.json datos-ventas.json

crudo.json trae las respuestas tal cual ({columns, rows}) de las consultas
guardadas, corridas del 1 de septiembre de 2026 a ayer:

  ventas              f7fc8d98-183a-42e4-9d24-65f447dee7c2  Ventas por red de la última liga
  signups_link        ea8fb52b-8e3a-4dc6-a3ed-e833c17e8ce9  Signups por link de cada red, por mes
  nuevos_declarados   4b6920e1-3c1e-4eb2-b23c-09fca5b48424  Clientes nuevos por red declarada
  signups_declarados  25dbdeb4-2c0a-44a8-b5c4-1ebc2e615a58  Signups por «cómo conociste heru»
                      (una corrida por mes: {"AAAA-MM": {columns, rows}})

El repo es público: aquí solo entran conteos agregados. Si una respuesta trae
una columna que no sea de conteo o de etiqueta, el script se detiene.
"""
import json
import sys
from datetime import datetime, timezone, timedelta

REDES = ["facebook", "instagram", "tiktok", "youtube", "linkedin", "whatsapp_grupo"]
# Columnas permitidas: si aparece otra (correo, nombre, teléfono…), se detiene.
PERMITIDAS = {
    "mes", "red", "tipo", "med", "camp", "cont", "ventas", "ventas_nuevos",
    "visitantes", "signups", "red_declarada", "clientes_nuevos",
    "discovery_source", "accounts",
}


def filas(bloque):
    cols = bloque["columns"]
    raras = set(cols) - PERMITIDAS
    if raras:
        sys.exit(f"Columna no permitida en datos públicos: {sorted(raras)}")
    return [dict(zip(cols, r)) for r in bloque["rows"]]


def n(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def main(src, dst):
    crudo = json.load(open(src, encoding="utf-8"))
    meses = sorted(crudo["signups_declarados"].keys())

    def vacio():
        return {m: {r: {"organico": 0, "pauta": 0} for r in REDES} for m in meses}

    ventas, ventas_nuevos = vacio(), vacio()
    piezas = {}
    for f in filas(crudo["ventas"]):
        m, red, tipo = f["mes"], f["red"], f["tipo"]
        if red not in REDES or m not in ventas:
            continue  # whatsapp_otros = mensajes de heru (utility), no es una red
        ventas[m][red][tipo] += n(f["ventas"])
        ventas_nuevos[m][red][tipo] += n(f["ventas_nuevos"])
        if tipo == "organico" and (f.get("cont") or f.get("camp")):
            k = (red, f.get("camp") or "", f.get("cont") or "")
            p = piezas.setdefault(k, {"red": red, "utm_campaign": k[1], "utm_content": k[2],
                                      "meses": {}, "ventas": 0})
            p["ventas"] += n(f["ventas"])
            p["meses"][m] = p["meses"].get(m, 0) + n(f["ventas"])

    sig_link = vacio()
    visit_link = vacio()
    for f in filas(crudo["signups_link"]):
        m, red, tipo = f["mes"], f["red"], f["tipo"]
        if red in REDES and m in sig_link:
            sig_link[m][red][tipo] += n(f["signups"])
            visit_link[m][red][tipo] += n(f["visitantes"])

    nuevos_decl = {m: {r: 0 for r in REDES} for m in meses}
    for f in filas(crudo["nuevos_declarados"]):
        if f["red_declarada"] in REDES and f["mes"] in nuevos_decl:
            nuevos_decl[f["mes"]][f["red_declarada"]] += n(f["clientes_nuevos"])

    # «¿Cómo nos conociste?»: YouTube y WhatsApp no son opción → None (no 0)
    sig_decl, sig_total = {}, {}
    for m in meses:
        rows = filas(crudo["signups_declarados"][m])
        por = {f["discovery_source"]: n(f["signups"]) for f in rows}
        sig_total[m] = sum(por.values())
        sig_decl[m] = {r: (por.get(r, 0) if r in ("facebook", "instagram", "tiktok", "linkedin") else None)
                       for r in REDES}

    cdmx = timezone(timedelta(hours=-6))
    out = {
        "generado": datetime.now(cdmx).strftime("%Y-%m-%d %H:%M"),
        "desde": crudo["desde"],
        "hasta": crudo["hasta"],
        "meses": meses,
        "redes": REDES,
        "signups_declarados": sig_decl,
        "signups_totales": sig_total,
        "signups_link": sig_link,
        "visitantes_link": visit_link,
        "ventas": ventas,
        "ventas_clientes_nuevos": ventas_nuevos,
        "clientes_nuevos_declarados": nuevos_decl,
        "piezas_con_venta": sorted(piezas.values(), key=lambda p: (-p["ventas"], p["red"])),
        "consultas": {
            "ventas": "f7fc8d98-183a-42e4-9d24-65f447dee7c2",
            "signups_link": "ea8fb52b-8e3a-4dc6-a3ed-e833c17e8ce9",
            "nuevos_declarados": "4b6920e1-3c1e-4eb2-b23c-09fca5b48424",
            "signups_declarados": "25dbdeb4-2c0a-44a8-b5c4-1ebc2e615a58",
        },
    }
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("ok:", dst, "·", len(meses), "meses ·", len(out["piezas_con_venta"]), "piezas con venta")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
