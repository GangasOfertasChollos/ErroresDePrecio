"""Genera sitemap.xml con <lastmod> y verifica que todas las URLs existen.

El sitemap anterior no declaraba lastmod en un sitio que actualiza a diario,
y no habia ninguna comprobacion de que las URLs apuntaran a archivos reales.

Desde la migracion a gangasofertas.com el sitemap es unico y absoluto: incluye
la portada del sitio y tambien la seccion BlackFriday/, que se sirve como
subcarpeta del mismo dominio.
"""
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
BASE = "https://gangasofertas.com"
HOY = date.today().isoformat()

# ruta relativa a la raiz del repo, changefreq, prioridad
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
    # listado de ofertas en vivo del tema Black Friday en la raiz
    ("black-friday-2026.html", "daily", "0.8"),
    # ── seccion Black Friday ──
    ("BlackFriday/index.html", "weekly", "0.9"),
    ("BlackFriday/fecha-black-friday-2026.html", "weekly", "0.8"),
    ("BlackFriday/ofertas-black-friday-2026.html", "weekly", "0.8"),
    ("BlackFriday/gangas-black-friday.html", "weekly", "0.8"),
    ("BlackFriday/que-es-el-black-friday.html", "weekly", "0.7"),
    ("BlackFriday/como-aprovechar-black-friday.html", "weekly", "0.7"),
    ("BlackFriday/black-friday-por-categorias.html", "weekly", "0.7"),
    ("BlackFriday/black-friday-vs-cyber-monday.html", "weekly", "0.7"),
    ("BlackFriday/errores-de-precio-amazon.html", "weekly", "0.8"),
    ("BlackFriday/canal-telegram-ofertas.html", "weekly", "0.7"),
    ("BlackFriday/evitar-estafas-black-friday.html", "weekly", "0.6"),
    ("BlackFriday/faq.html", "weekly", "0.7"),
    ("BlackFriday/metodologia.html", "monthly", "0.5"),
    ("BlackFriday/sobre-nosotros.html", "monthly", "0.4"),
    ("BlackFriday/aviso-legal.html", "yearly", "0.3"),
    ("BlackFriday/politica-privacidad.html", "yearly", "0.3"),
]

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)


def url_para(ruta: str) -> str:
    """index.html se sirve en la raiz del dominio, sin /index.html."""
    if ruta == "index.html":
        return f"{BASE}/"
    if ruta.endswith("/index.html"):
        return f"{BASE}/{ruta[: -len('index.html')]}"
    return f"{BASE}/{ruta}"


urlset = ET.Element(f"{{{NS}}}urlset")
for ruta, freq, prioridad in PAGINAS:
    destino = RAIZ / ruta
    if not destino.exists():
        raise SystemExit(f"ERROR: {ruta} esta en el sitemap pero no existe")
    u = ET.SubElement(urlset, f"{{{NS}}}url")
    ET.SubElement(u, f"{{{NS}}}loc").text = url_para(ruta)
    ET.SubElement(u, f"{{{NS}}}lastmod").text = HOY
    ET.SubElement(u, f"{{{NS}}}changefreq").text = freq
    ET.SubElement(u, f"{{{NS}}}priority").text = prioridad

if hasattr(ET, "indent"):  # Python 3.9+: deja el XML legible como estaba
    ET.indent(urlset, space="  ")

xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(urlset, encoding="unicode")
(RAIZ / "sitemap.xml").write_text(xml + "\n", encoding="utf-8", newline="")
print(f"  sitemap.xml: {len(PAGINAS)} URLs, todas verificadas, lastmod={HOY}")

# ── comprobacion cruzada: ningun HTML fuera del sitemap ──
en_sitemap = {r for r, _, _ in PAGINAS}
htmls = {
    p.relative_to(RAIZ).as_posix()
    for p in RAIZ.rglob("*.html")
    if ".git" not in p.parts
    and ".venv" not in p.parts
    and "__pycache__" not in p.parts
    and "docs" not in p.parts
} - {"404.html", "BlackFriday/404.html", "googlea9c410decf5a46ae.html"}
faltan = htmls - en_sitemap
if faltan:
    print(f"  AVISO: HTML sin registrar en el sitemap: {sorted(faltan)}")
else:
    print("  OK: todas las paginas .html estan en el sitemap")
