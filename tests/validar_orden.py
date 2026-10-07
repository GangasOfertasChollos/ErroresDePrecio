"""Comprueba que el CSS nuevo existe para las clases que emite el generador,
y que no hay clases referenciadas en el HTML que falten en la hoja."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
fallos = []

CSS = (RAIZ / "assets" / "style.css").read_text(encoding="utf-8")

print("== 1. Clases nuevas presentes en style.css ==")
for clase in ("catalogo__cabecera", "editorial--final", "editorial", "faq"):
    if f".{clase}" not in CSS:
        fallos.append(clase)
        print(f"  FALLO .{clase} no esta en style.css")
    else:
        print(f"  OK   .{clase}")

print("\n== 2. Variables usadas por el CSS nuevo, definidas en :root ==")
root = re.search(r":root\s*\{(.*?)\}", CSS, re.S)
definidas = set(re.findall(r"(--[a-z-]+)\s*:", root.group(1) if root else ""))
bloque = CSS[CSS.index(".catalogo__cabecera"):] if ".catalogo__cabecera" in CSS else ""
usadas = set(re.findall(r"var\((--[a-z-]+)\)", bloque))
huerfanas = usadas - definidas
if huerfanas:
    print("  FALLO variables sin definir:", sorted(huerfanas))
    fallos.append("vars")
else:
    print(f"  OK   {len(usadas)} variables usadas, todas definidas en :root")

print("\n== 3. Orden y clases en las paginas generadas ==")
for slug in ("general", "moviles-electronica", "juguetes-infantil", "papeleria-oficina"):
    h = (RAIZ / f"{slug}.html").read_text(encoding="utf-8")
    main = h[h.index("<main"):h.index("</main>")]

    if main.find('id="ofertas"') > main.find('class="editorial'):
        print(f"  FALLO {slug}: el editorial va antes de las ofertas")
        fallos.append(slug)
        continue
    if 'class="catalogo__cabecera"' not in main:
        print(f"  FALLO {slug}: falta la cabecera del catalogo")
        fallos.append(slug)
        continue
    if 'class="editorial editorial--final"' not in main:
        print(f"  FALLO {slug}: el editorial no lleva editorial--final")
        fallos.append(slug)
        continue

    # El h2 de la cabecera del catalogo debe ser el primero del main.
    h2 = re.findall(r"<h2[^>]*>(.*?)</h2>", main, re.S)
    limpio = [re.sub(r"<[^>]+>", "", x).strip() for x in h2]
    print(f"  OK   {slug:24} ofertas -> '{limpio[0]}' | texto -> '{limpio[1]}'")

print("\n== 4. El JSON-LD sigue declarando el ItemList y el FAQPage ==")
for slug in ("general", "moviles-electronica"):
    h = (RAIZ / f"{slug}.html").read_text(encoding="utf-8")
    bloque = re.search(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
    import json
    obj = json.loads(bloque.group(1))
    tipos = [n.get("@type") for n in obj.get("@graph", [])]
    faltan = [t for t in ("ItemList", "FAQPage", "CollectionPage") if t not in tipos]
    if faltan:
        print(f"  FALLO {slug}: falta {faltan}")
        fallos.append(slug)
    else:
        print(f"  OK   {slug}: {', '.join(str(t) for t in tipos)}")

print("\n" + "=" * 50)
print(f"{len(fallos)} FALLOS")
raise SystemExit(1 if fallos else 0)