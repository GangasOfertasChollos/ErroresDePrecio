"""Genera sitemap.xml con <lastmod> y verifica que todas las URLs existen.

El sitemap anterior no declaraba lastmod en un sitio que actualiza a diario,
y no habia ninguna comprobacion de que las URLs apuntaran a archivos reales.
"""
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
BASE = "https://gangasofertaschollos.github.io/ErroresDePrecio"
HOY = date.today().isoformat()

# ruta, changefreq, prioridad
PAGINAS = [
    ("index.html", "daily", "1.0"),
    ("general.html", "daily", "0.9"),
    ("categorias.html", "weekly", "0.8"),
    # catalogos: se actualizan cada vez que el bot publica
    ("moviles-electronica.html", "daily", "0.9"),
    ("ropa-y-calzado.html", "daily", "0.8"),
    ("gaming-consolas.html", "daily", "0.8"),
    ("higiene-cuidado-personal.html", "daily", "0.7"),
    ("juguetes-infantil.html", "daily", "0.7"),
    ("papeleria-oficina.html", "daily", "0.7"),
    # paginas SEO
    ("chollos-de-amazon.html", "weekly", "0.8"),
    ("errores-de-precio-amazon.html", "weekly", "0.8"),
    ("articulos-rebajados-amazon.html", "weekly", "0.7"),
    ("chollos-amazon-telegram.html", "weekly", "0.7"),
]

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)

urlset = ET.Element(f"{{{NS}}}urlset")
for ruta, freq, prioridad in PAGINAS:
    destino = RAIZ / ruta
    if not destino.exists():
        raise SystemExit(f"ERROR: {ruta} esta en el sitemap pero no existe")
    u = ET.SubElement(urlset, f"{{{NS}}}url")
    ET.SubElement(u, f"{{{NS}}}loc").text = f"{BASE}/{ruta}"
    ET.SubElement(u, f"{{{NS}}}lastmod").text = HOY
    ET.SubElement(u, f"{{{NS}}}changefreq").text = freq
    ET.SubElement(u, f"{{{NS}}}priority").text = prioridad

xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(urlset, encoding="unicode")
(RAIZ / "sitemap.xml").write_text(xml + "\n", encoding="utf-8", newline="")
print(f"  sitemap.xml: {len(PAGINAS)} URLs, todas verificadas, lastmod={HOY}")

# ── comprobacion cruzada: ningun HTML fuera del sitemap ──
en_sitemap = {r for r, _, _ in PAGINAS}
htmls = {p.name for p in RAIZ.glob("*.html")} - {"404.html"}
faltan = htmls - en_sitemap
if faltan:
    print(f"  AVISO: HTML sin registrar en el sitemap: {sorted(faltan)}")
else:
    print("  OK: todas las paginas .html estan en el sitemap")
