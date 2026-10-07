"""Prueba de _regenerar_html() y del listado de paginas generadas.

No hace falta Telegram ni credenciales: se importa bot.py con las variables de
entorno puestas para que no intente conectarse, y se comprueba que la lista de
paginas que el bot va a subir es exactamente la que los generadores escriben
(mas sitemap.xml) y que no incluye nada de BlackFriday/ ni PrimeDays/.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

fallos = []


def err(m):
    fallos.append(m)
    print("  FALLO", m)


def check(nombre, cond, detalle=""):
    print(("  OK   " if cond else "  FALLO ") + nombre + ("" if cond else f" -> {detalle}"))
    if not cond:
        fallos.append(nombre)


print("== 1. _paginas_generadas() lista lo que hay que subir ==")
import bot

paginas = bot._paginas_generadas()
print(f"  {len(paginas)} entradas")

esperadas = {
    "ropa-y-calzado.html", "moviles-electronica.html", "gaming-consolas.html",
    "higiene-cuidado-personal.html", "juguetes-infantil.html",
    "papeleria-oficina.html", "general.html", "guias.html",
    "como-detectar-errores-de-precio-amazon.html",
    "ofertas-reales-vs-descuentos-falsos.html",
    "amazon-warehouse-outlet-y-devoluciones.html",
    "cuando-comprar-en-amazon-espana.html", "guia-completa-chollos-amazon.html",
    "mejores-canales-telegram-ofertas.html", "sitemap.xml",
}
check("son las 15 esperadas", set(paginas) == esperadas,
      f"faltan {esperadas - set(paginas)}, sobran {set(paginas) - esperadas}")

# Lo importante para no romper nada: nada de BlackFriday/ ni PrimeDays/.
malas = [p for p in paginas if p.startswith(("BlackFriday", "PrimeDays", "docs"))]
check("no toca BlackFriday/ ni PrimeDays/", not malas, str(malas))

# Y todos los archivos existen de verdad, que es lo que git add staging hara.
inexistentes = [p for p in paginas if not (RAIZ / p).exists()]
check("todos los archivos existen", not inexistentes, str(inexistentes))

print("\n== 2. _regenerar_html() ejecuta los tres generadores sin fallos ==")
fallos_gen = bot._regenerar_html()
check("ningun generador falla", not fallos_gen, str(fallos_gen))

print("\n== 3. Tras regenerar, general.html trae las ofertas del JSON ==")
import json
import re

ofertas = json.loads((RAIZ / "data" / "general.json").read_text(encoding="utf-8"))
html = (RAIZ / "general.html").read_text(encoding="utf-8")
tarjetas = len(re.findall(r'<article class="oferta"', html))
check("general.html sirve las ofertas del JSON",
      tarjetas >= len(ofertas), f"{tarjetas} tarjetas vs {len(ofertas)} ofertas")

print("\n== 4. Regenerar es idempotente (no ensucia el arbol) ==")
import subprocess

antes = subprocess.run(["git", "status", "--porcelain"], cwd=RAIZ,
                       capture_output=True, text=True, encoding="utf-8").stdout
bot._regenerar_html()
despues = subprocess.run(["git", "status", "--porcelain"], cwd=RAIZ,
                         capture_output=True, text=True, encoding="utf-8").stdout
check("dos ejecuciones seguidas no generan diferencias",
      antes == despues, f"antes={antes!r} despues={despues!r}")

print("\n== 5. REGENERAR_HTML es configurable ==")
check("REGENERAR_HTML se lee del entorno",
      bot.REGENERAR_HTML == (os.getenv("REGENERAR_HTML", "1").strip().lower()
                             in ("1", "true", "yes", "si")))
check("GENERADORES en el orden correcto (HTML antes que sitemap)",
      bot.GENERADORES == ("generar_categorias.py", "generar_guias.py",
                          "generar_sitemap.py"), str(bot.GENERADORES))

print("\n== 6. Sin ofertas nuevas no se regenera el HTML ==")
# La tarea periodica entra en publicar_en_git() cada PUBLICAR_CADA_S segundos.
# Regenerar antes de comprobar si data/ ha cambiado lanzaba los tres
# generadores en cada pasada, con el canal callado. Se comprueba el orden
# leyendo el codigo: el chequeo de data/ tiene que ir antes que la llamada a
# _regenerar_html().
import inspect

fuente = inspect.getsource(bot.publicar_en_git)
# La llamada real es 'asyncio.to_thread(_regenerar_html)': sin parentesis,
# porque se pasa la funcion. Buscarla con parentesis no la encuentra.
pos_check = fuente.find("'status', '--porcelain', '--', 'data/'")
pos_regen = fuente.find("_regenerar_html")
pos_salida = fuente.find("No hay cambios que publicar")
check("el generador aparece en el codigo", pos_regen != -1)
check("data/ se comprueba ANTES de regenerar",
      pos_check != -1 and pos_check < pos_regen,
      f"check={pos_check} regen={pos_regen}")
check("el chequeo limita a data/, no al arbol entero",
      "--', 'data/'" in fuente,
      "un status sobre todo el arbol haria que un HTML sin commitear "
      "disparase el push en cada pasada")
check("se sale antes de regenerar si no hay cambios",
      pos_salida != -1 and pos_salida < pos_regen,
      f"salida={pos_salida} regen={pos_regen}")

print("\n" + "=" * 56)
print(f"{len(fallos)} FALLOS")
raise SystemExit(1 if fallos else 0)