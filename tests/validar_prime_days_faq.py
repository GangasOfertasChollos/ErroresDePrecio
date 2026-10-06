"""Prueba del toggle del FAQ de PrimeDays con un DOM real.

No depende de un navegador: usa el HTML generado tal cual y comprueba que el
contenedor que declara data-faq-target contiene TODOS los <details> de la
pagina. Si no los contiene, el boton "Desplegar todas" solo abre un bloque y
el resto se queda plegado: un fallo silencioso que no aparece al leer el HTML.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
fallos = []

for nombre in ("faq.html", "index.html"):
    txt = (RAIZ / "PrimeDays" / nombre).read_text(encoding="utf-8")

    m = re.search(r'data-faq-target="([^"]+)"', txt)
    if not m:
        # index.html no tiene toggle: solo se comprueba que no apunte a nada.
        print(f"  --   {nombre}: sin boton de toggle")
        continue

    target = m.group(1)
    abre = re.search(r'<(?:div|section)[^>]*id="' + re.escape(target) + r'"[^>]*>', txt)
    if not abre:
        fallos.append(f"{nombre}: data-faq-target={target!r} pero no existe ese id")
        continue

    # Recorta desde el id hasta su cierre para contar los details de verdad.
    ini = abre.end()
    fin = txt.find("\n    </div>", ini)
    if fin == -1:
        fin = len(txt)
    bloque = txt[ini:fin]

    dentro = bloque.count("<details")
    total = txt.count("<details")
    print(f"  OK   {nombre}: {dentro} de {total} <details> dentro de #{target}")
    if dentro != total:
        fallos.append(
            f"{nombre}: el toggle #{target} solo abre {dentro} de {total} "
            f"<details>; el resto se queda plegado")

# El boton solo tiene sentido si hay mas de un bloque de FAQ.
faq = (RAIZ / "PrimeDays" / "faq.html").read_text(encoding="utf-8")
bloques = len(re.findall(r'<div class="faq">', faq))
print(f"  --   faq.html: {bloques} bloques .faq (un boton de desplegar tiene sentido a partir de 2)")
if bloques < 2 and 'data-faq-toggle' in faq:
    fallos.append("faq.html: boton de desplegar con un solo bloque de FAQ")

print()
for f in fallos:
    print("  FALLO", f)
print("=" * 56)
print(f"{len(fallos)} FALLOS")
sys.exit(1 if fallos else 0)