"""Validacion estatica del sitio: enlaces, JSON-LD, HTML y referencias a assets."""
import json, re, os
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
fallos, avisos = [], []

def err(m): fallos.append(m); print("  FALLO", m)
def warn(m): avisos.append(m); print("  AVISO", m)

print("== 1. Enlaces internos y assets ==")
for html in sorted(RAIZ.glob("*.html")):
    txt = html.read_text(encoding="utf-8")
    for m in re.finditer(r'(?:href|src)="([^"]+)"', txt):
        ref = m.group(1)
        if ref.startswith(("http://", "https://", "#", "mailto:", "data:")):
            continue
        limpio = ref.split("#")[0].split("?")[0]
        if not limpio:
            continue
        # 404.html vive en la raiz de Pages, por eso usa rutas absolutas
        if limpio.startswith("/"):
            destino = RAIZ / limpio[len("/"):]
        else:
            destino = html.parent / limpio
        if not destino.exists():
            err(f"{html.name} -> {ref} (no existe)")

print("\n== 2. JSON-LD valido ==")
for html in sorted(RAIZ.glob("*.html")):
    for bloque in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html.read_text(encoding="utf-8"), re.S
    ):
        try:
            obj = json.loads(bloque)
        except json.JSONDecodeError as e:
            err(f"{html.name}: JSON-LD invalido -> {e}")
            continue
        # index.html usa @graph, el resto un tipo directo
        tipos = [n.get("@type") for n in obj.get("@graph", [])] if "@graph" in obj else [obj.get("@type")]
        print(f"  OK   {html.name}: {', '.join(str(t) for t in tipos)}")

print("\n== 3. HTML bien formado (etiquetas balanceadas) ==")
class Checker(HTMLParser):
    VACIAS = {"meta","link","img","br","hr","input","source","path","circle","rect","use"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pila, self.errores = [], []
    def handle_starttag(self, tag, attrs):
        if tag not in self.VACIAS:
            self.pila.append(tag)
    def handle_endtag(self, tag):
        if tag in self.VACIAS:
            return
        if not self.pila:
            self.errores.append(f"</{tag}> sin apertura")
        elif self.pila[-1] != tag:
            self.errores.append(f"</{tag}> pero esperaba </{self.pila[-1]}>")
            if tag in self.pila:
                while self.pila and self.pila.pop() != tag:
                    pass
        else:
            self.pila.pop()

for html in sorted(RAIZ.glob("*.html")):
    c = Checker()
    c.feed(html.read_text(encoding="utf-8"))
    if c.errores or c.pila:
        err(f"{html.name}: {'; '.join(c.errores)} | sin cerrar: {c.pila}")
    else:
        print(f"  OK   {html.name}")

print("\n== 4. data-feed apunta a un JSON existente ==")
for html in sorted(RAIZ.glob("*.html")):
    m = re.search(r'data-feed="([^"]+)"', html.read_text(encoding="utf-8"))
    if m:
        destino = RAIZ / "data" / f"{m.group(1)}.json"
        (print if destino.exists() else err)(
            f"{html.name}: data-feed={m.group(1)} -> {'OK' if destino.exists() else 'FALTA ' + str(destino)}")

print("\n== 5. Datos ==")
vacios = []
for j in sorted((RAIZ / "data").glob("*.json")):
    try:
        datos = json.loads(j.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{j.name}: JSON invalido -> {e}"); continue
    if not datos:
        vacios.append(j.name)
        continue
    obligatory = {"id","date","title","price","amazon_url","image","categoria"}
    for o in datos:
        faltan = obligatory - set(o)
        if faltan:
            err(f"{j.name}: oferta {o.get('id')} sin {sorted(faltan)}")
    ids = [o["id"] for o in datos]
    if ids != sorted(ids, reverse=True):
        err(f"{j.name}: no esta ordenado por id descendente -> {ids}")
    print(f"  OK   {j.name}: {len(datos)} ofertas, orden correcto")

if vacios:
    print(f"  NOTA {len(vacios)} JSON sin ofertas: {', '.join(vacios)}")
    print("       Las paginas mostraran 'Todavia no hay ofertas'. Es lo esperado")
    print("       hasta que el bot publique la primera oferta.")

print("\n== 6. Claims que el codigo no sostiene ==")
idx = (RAIZ / "index.html").read_text(encoding="utf-8")
sospechosas = ["monitoriza Amazon", "24 horas al día", "24/7", "3.700", "detecta chollos y errores",
               "Más rápido que Chollómetro", "100% automatizado"]
for frase in sospechosas:
    if frase in idx:
        err(f"index.html sigue con afirmaciones sin respaldo: {frase!r}")
if not fallos:
    print("  OK   ninguna afirmacion no verificable en index.html")

print("\n" + "=" * 56)
print(f"{len(fallos)} FALLOS · {len(avisos)} avisos")
raise SystemExit(1 if fallos else 0)
