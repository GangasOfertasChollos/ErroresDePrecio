"""Comprueba que no queda ninguna referencia viva a las URLs retiradas.

Al resolver el href hay que tener en cuenta el directorio del propio fichero:
"errores-de-precio-amazon.html" dentro de BlackFriday/ es
BlackFriday/errores-de-precio-amazon.html, que es una pagina DISTINTA que sigue
viva y en el sitemap. Comparar solo el basename daria 60 falsos positivos.

Ademas genera reglas.txt con los 301 que hay que crear en Cloudflare, porque
GitHub Pages no sirve .htaccess y no puede hacer la redireccion por si mismo.

Uso: python -X utf8 tests/verificar_301.py
"""

from pathlib import Path
import re
import sys

RAIZ = Path(__file__).resolve().parent.parent
BASE = "https://gangasofertas.com"

# slug retirado en la raiz -> destino
REDIRIGIR = {
    "chollos-de-amazon": "general.html",
    "articulos-rebajados-amazon": "general.html",
    "errores-de-precio-amazon": "como-detectar-errores-de-precio-amazon.html",
    "chollos-amazon-telegram": "mejores-canales-telegram-ofertas.html",
}

# Las ocho URLs de la seccion retirada. Se avisan aparte porque el 301 depende
# de si Search Console tiene impresiones de ellas.
PRIMEDAYS = [
    "PrimeDays/index.html",
    "PrimeDays/que-es-amazon-prime-days.html",
    "PrimeDays/fechas-amazon-prime-days.html",
    "PrimeDays/ofertas-prime-days-2026.html",
    "PrimeDays/descuentos-reales-o-falsos.html",
    "PrimeDays/como-aprovechar-prime-days.html",
    "PrimeDays/canal-telegram-ofertas.html",
    "PrimeDays/faq.html",
]


def resolver(ruta_html: Path, href: str) -> str:
    """href relativo -> ruta desde la raiz del repositorio."""
    href = href.split("#")[0].split("?")[0]
    if href.startswith("/"):
        return href.lstrip("/")
    partes = [p for p in ruta_html.relative_to(RAIZ).parts[:-1] if p not in (".", "")]
    for seg in href.split("/"):
        if seg == "..":
            if partes:
                partes.pop()
        elif seg not in (".", ""):
            partes.append(seg)
    return "/".join(partes)


def main() -> None:
    htmls = sorted(
        [p for p in RAIZ.glob("*.html") if not p.name.startswith("google")]
        + list((RAIZ / "BlackFriday").glob("*.html"))
    )

    problemas = []
    for f in htmls:
        c = f.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]+)"', c):
            if href.startswith(("http://", "https://", "#", "mailto:", "tel:", "data:")):
                continue
            destino = resolver(f, href)
            if destino in REDIRIGIR and destino.endswith(".html"):
                problemas.append((f.relative_to(RAIZ).as_posix(), href, destino))

    print("Referencias vivas a URLs retiradas (raiz):")
    if problemas:
        for f, h, d in problemas:
            print(f"  FALLO  {f} -> {h}  (resuelve a {d})")
    else:
        print("  ninguna")

    # Comprobar tambien que las URLs retiradas ya no existen en disco
    print("\nFicheros de las URLs retiradas:")
    for slug in REDIRIGIR:
        p = RAIZ / f"{slug}.html"
        print(f"  {'AUN EXISTE' if p.exists() else 'borrado     '}  {slug}.html")

    # Links rotos generales (util tras un borrado masivo)
    print("\nEnlaces rotos en todo el sitio:")
    rotos = 0
    for f in htmls:
        c = f.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]+)"', c):
            if href.startswith(("http://", "https://", "#", "mailto:", "tel:", "data:")):
                continue
            d = resolver(f, href)
            if not d or "/" in d and not d.endswith(".html"):
                if d.endswith((".png", ".css", ".js", ".jpg", ".svg", ".webp")):
                    if not (RAIZ / d).exists():
                        print(f"  FALLO  {f.relative_to(RAIZ)} -> {href}")
                        rotos += 1
                continue
            if not (RAIZ / d).exists():
                print(f"  FALLO  {f.relative_to(RAIZ)} -> {href}  (no existe {d})")
                rotos += 1
    if not rotos:
        print("  ninguno")

    generar_reglas()

    if problemas or rotos:
        sys.exit(1)


def generar_reglas() -> None:
    L = [
        "# Redirecciones 301 — reglas de Cloudflare",
        "# Generado por tests/verificar_301.py. No editar a mano: se regenera.",
        "#",
        "# Cloudflare > Rules > Bulk Redirects (o Single Redirects, una por URL).",
        "# GitHub Pages no sirve .htaccess, asi que la redireccion tiene que",
        "# hacerse aqui. Sin ella, estas URLs devuelven 404 y se pierde el",
        "# poco peso que tuvieran.",
        "#",
        "# Contexto: el 10 de octubre de 2026 se retiraron cuatro paginas",
        "# 'puente' de 300-360 palabras que competian entre si y con paginas que",
        "# ya las cubrian. Cada 301 pasa el peso a la pagina que hoy cubre esa intencion.",
        "",
        "| Origen | Destino |",
        "|---|---|",
    ]
    for slug, destino in REDIRIGIR.items():
        L.append(f"| `{BASE}/{slug}.html` | `{BASE}/{destino}` |")
    L += [
        "",
        "## Formato de texto plano (para Cloudflare Bulk Redirects)",
        "",
        "```",
    ]
    for slug, destino in REDIRIGIR.items():
        L.append(f"{BASE}/{slug}.html {BASE}/{destino} 301")
    L += [
        "```",
        "",
        "## Comprobacion tras crearlas",
        "",
        "```bash",
        "curl -sI https://gangasofertas.com/chollos-de-amazon.html | Select-String -Pattern 'HTTP|location'",
        "```",
        "",
        "Debe devolver `HTTP/2 301` y `location: https://gangasofertas.com/general.html`.",
        "Cloudflare tarda unos minutos en propagar la regla.",
        "",
        "## PrimeDays: decidir antes de redirigir",
        "",
        "Las ocho URLs de la seccion PrimeDays tambien se retiraron ese dia.",
        "A diferencia de estas cuatro, aqui el 301 depende de Search Console:",
        "",
        "- **Con impresiones** → aplica 301 hacia su equivalente en `/BlackFriday/`:",
        "",
    ]
    equivalencias = {
        "index.html": "BlackFriday/index.html",
        "que-es-amazon-prime-days.html": "BlackFriday/que-es-el-black-friday.html",
        "fechas-amazon-prime-days.html": "BlackFriday/fecha-black-friday-2026.html",
        "ofertas-prime-days-2026.html": "BlackFriday/ofertas-black-friday-2026.html",
        "descuentos-reales-o-falsos.html": "BlackFriday/gangas-black-friday.html",
        "como-aprovechar-prime-days.html": "BlackFriday/como-aprovechar-black-friday.html",
        "canal-telegram-ofertas.html": "BlackFriday/canal-telegram-ofertas.html",
        "faq.html": "BlackFriday/faq.html",
    }
    for origen, destino in equivalencias.items():
        L.append(f"  - `{BASE}/PrimeDays/{origen}` → `{BASE}/{destino}`")
    L += [
        "",
        "- **Sin impresiones** → no hace falta redirigir. Una URL que nunca se",
        "  posicionó no tiene peso que traspasar y un 404 no penaliza. Ahorra",
        "  ocho reglas que no hacen falta.",
        "",
    ]
    (RAIZ / "reglas.txt").write_text("\n".join(L), encoding="utf-8", newline="\n")
    print(f"\nreglas.txt escrito ({len(REDIRIGIR)} 301 + {len(PRIMEDAYS)} de PrimeDays pendientes de decidir)")


main()