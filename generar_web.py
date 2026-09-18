import json,html
from pathlib import Path
R=Path(__file__).parent; S="https://gangasofertaschollos.github.io/ErroresDePrecio"
for p in (R/"data").glob("*.json"):
 c=p.stem; a=json.loads(p.read_text(encoding="utf8")); cards=""
 for o in a:
  t=html.escape(o.get("title","")); u=html.escape(o.get("amazon_url","#")); i=o.get("image_url","")
  cards+=f'<article><img src="{i}" alt="{t}" loading="lazy" width="600" height="600"><h2>{t}</h2><a href="{u}" rel="nofollow sponsored">Ver oferta en Amazon España</a></article>'
 (R/f"{c}.html").write_text(f'<html lang="es"><head><meta charset="utf-8"><title>Chollos {c} Amazon España</title><meta name="description" content="Ofertas y chollos de Amazon España"></head><body><h1>Chollos {c} Amazon España</h1>{cards}</body></html>',encoding="utf8")
