# Actualización de los lunes · pestañas «Signups y ventas» y «1:1»

Programación: cada lunes a las 8:00 am, hora de Ciudad de México (cron `0 8 * * 1`).
Es el prompt de la tarea programada. Corre en la Mac de Mich con Claude Code: si la
Mac está apagada a esa hora, corre cuando se prenda.

---

Eres el encargado de refrescar dos pestañas del Content Dash de heru (la marca se
escribe siempre «heru», en minúscula). Repo local: `~/repos/content-dash-auto`.
Solo lees datos de heru y de Windsor; nunca cambias nada en una cuenta.

## Fechas (hora de Ciudad de México)

- `LUNES` = lunes de la semana pasada; `DOMINGO` = ayer. Ejemplo: si hoy es
  lunes 23 de noviembre de 2026, la semana es del 16 al 22.
- `AYER` = ayer, en AAAA-MM-DD.

## 1 · Preparar el repo

```bash
cd ~/repos/content-dash-auto && git checkout main && git pull --ff-only
```

Si `git pull` falla o hay cambios sin commitear, detente y avísale a Mich.

## 2 · Signups y ventas (Querybuilder de heru)

Consulta `heru_help` con la categoría `querybuilder` si no lo has hecho en esta
sesión. Corre por id, sin reescribirlas, con `start_date = 2026-09-01` y
`end_date = AYER`, `max_rows` 500:

- `f7fc8d98-183a-42e4-9d24-65f447dee7c2` → `ventas`
- `ea8fb52b-8e3a-4dc6-a3ed-e833c17e8ce9` → `signups_link`
- `4b6920e1-3c1e-4eb2-b23c-09fca5b48424` → `nuevos_declarados`
- `25dbdeb4-2c0a-44a8-b5c4-1ebc2e615a58` → `signups_declarados`, **una corrida por
  mes** (del 1 al último día de cada mes; el mes en curso, del 1 a AYER)

Guarda las respuestas `{columns, rows}` tal cual en un archivo temporal fuera del
repo, con esta forma:

```json
{"desde": "2026-09-01", "hasta": "AYER",
 "ventas": {...}, "signups_link": {...}, "nuevos_declarados": {...},
 "signups_declarados": {"2026-09": {...}, "2026-10": {...}, "...": {...}}}
```

y corre:

```bash
python3 scripts/armar_ventas.py /ruta/temporal/crudo.json datos-ventas.json
```

Las respuestas solo traen conteos. Si alguna trae nombres, correos, teléfonos o
RFC, detente: el repo es público.

## 3 · 1:1 (Windsor): miniaturas y texto de LinkedIn

Las métricas de la pestaña 1:1 se leen en vivo de la hoja del dash; aquí solo se
guardan las miniaturas, porque las ligas de TikTok, Instagram y LinkedIn caducan.

Con `get_data` de Windsor, de `LUNES − 1 día` a `DOMINGO + 1 día` (para cubrir el
desfase de UTC):

- `tiktok_organic`: `video_id`, `video_create_datetime`, `video_thumbnail_url`
- `instagram`: `media_id`, `timestamp`, `media_type`, `media_thumbnail_url`, `media_url`
- `linkedin_organic`: `share_id`, `share_published_time`, `share_image_url`, `share_text`

Arma una lista en un archivo temporal:
`[{"red":"tt","id":video_id,"url":video_thumbnail_url}, {"red":"ig","id":media_id,"url":media_thumbnail_url o, si viene vacío, media_url}, {"red":"li","id":share_id,"url":share_image_url,"texto":share_text}]`
(en Instagram, si `media_type` es VIDEO usa `media_thumbnail_url`; `media_url` de un
video es el .mp4 y no sirve) y corre:

```bash
python3 scripts/miniaturas.py /ruta/temporal/thumbs.json --semana LUNES
```

## 4 · Revisar y publicar

```bash
python3 -m http.server 8765
```

Abre `http://localhost:8765/metricas.html`, pestañas «Signups y ventas» y «1:1»: que
carguen sin errores en la consola y que la semana del 1:1 sea la de `LUNES` a
`DOMINGO`. Luego:

```bash
git add datos-ventas.json datos-1a1.json thumbs/
git commit -m "Dash: signups y ventas al AYER y miniaturas de la semana del LUNES"
git push
```

Esto publica el sitio (GitHub Pages sirve `main`). Solo agrega esos tres caminos:
nunca `git add -A`.

## 5 · Avisar

Responde con una línea: ventas por liga de redes en el mes en curso, el mejor post
de la semana (red y número de interacciones) y la liga
https://michelle834.github.io/content-dash-auto/metricas.html. Si algo falló, dilo
en una línea y no hagas push de datos a medias.
