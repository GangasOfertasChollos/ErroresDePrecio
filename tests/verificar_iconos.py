"""Comprueba que los iconos referenciados existen de verdad desde cada pagina.

Un href="assets/favicon-32x32.png" es correcto en la raiz y esta ROTO en
BlackFriday/, donde hace falta "../assets/". Resolver contra el directorio del
propio fichero es lo que distingue una cosa de la otra.

Uso: python -X utf8 tests/verificar_iconos.py
"""

from pathlib import Path
import re
import sys

RAIZ = Path(__file__).resolve().parent.parent

htmls = sorted(
    [p for p in RAIZ.glob("*.html") if not re.match(r"^google[0-9a-f]+\.html$", p.name)]
    + list((RAIZ / "BlackFriday").glob("*.html"))
)

faltan = []
comprobados = 0

for f in htmls:
    c = f.read_text(encoding="utf-8")
    base = f.relative_to(RAIZ).parent  # "." en la raiz, "BlackFriday" dentro

    # Los href de icono: rel="icon" y rel="apple-touch-icon"
    etiquetas = re.findall(r'<link rel="(?:icon|apple-touch-icon)"[^>]*href="([^"]+)"', c)
    # Se omite el que no es fichero local (ninguno deberia estarlo)
    for href in etiquetas:
        if href.startswith(("http://", "https://", "//")):
            faltan.append((f.as_posix(), href, "URL absoluta: deberia ser relativa"))
            continue
        destino = (base / href).resolve()
        comprobados += 1
        if not destino.exists():
            faltan.append((f.as_posix(), href, "no existe en disco"))
        elif destino.suffix.lower() not in (".png", ".svg", ".ico", ".jpg", ".jpeg"):
            faltan.append((f.as_posix(), href, f"formato raro: {destino.suffix}"))

print(f"Referencias comprobadas: {comprobados}")
if faltan:
    print("\nFALLAN:")
    for f, h, motivo in faltan:
        print(f"  {f}\n      -> {h}\n      {motivo}")
    sys.exit(1)

# Cada pagina debe declarar el juego completo: 32, 16, 192, apple-touch y el SVG
print("\nCobertura del juego de iconos:")
incompletas = []
for f in htmls:
    c = f.read_text(encoding="utf-8")
    falta = [x for x in ("favicon-32x32.png", "favicon-16x16.png",
                         "icon-192.png", "apple-touch-icon.png")
             if x not in c]
    if falta:
        incompletas.append((f.name, falta))
if incompletas:
    for n, falta in incompletas:
        print(f"  {n}: falta {', '.join(falta)}")
    sys.exit(1)
print(f"  las {len(htmls)} paginas declaran los 4 iconos")

# El apple-touch-icon debe ser PNG: iOS no acepta SVG ahi. Fue un bug real
# (BlackFriday declaraba apple-touch-icon apuntando a un .svg).
print("\nTipos MIME de apple-touch-icon:")
malos = []
for f in htmls:
    c = f.read_text(encoding="utf-8")
    for href in re.findall(r'<link rel="apple-touch-icon"[^>]*href="([^"]+)"', c):
        if not href.lower().endswith(".png"):
            malos.append((f.name, href))
if malos:
    for n, h in malos:
        print(f"  {n}: {h}  (iOS necesita PNG)")
    sys.exit(1)
print("  todos son PNG")

print("\nTODO CORRECTO")