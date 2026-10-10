"""Genera el hub guias.html y cada articulo de guias.py.

Por que un generador y no HTML a mano
--------------------------------------
Los cuatro "puente" de generar_seo.py ya sonHTML generado, y el pie y el menu
salen de plantilla_comun.py. Estas guias siguen la mismaVia: el texto vive en
guias.py (una entrada por articulo) y aqui solo se maqueta.

Que el articulo se emitservido y no por fetch()
-----------------------------------------------
Mismo motivo que en las paginas de catalogo: si el texto lo escribe el
JavaScript, un crawler sin ejecutarlo no ve nada. Aqui no hay alternativa: el
contenido ES el HTML, asi que la pregunta no se plantea.

Datos estructurados: Article + FAQPage + BreadcrumbList
-------------------------------------------------------
Google ya no muestra el bloque de FAQ en casi ningun caso, pero el marcado
sigueapareciendo en resultados enriquecidos y, sobre todo, le da a Google una
maquina de leer de lo que trata cada pagina. El Breadcrumb sustituye la URL
con separadores: las guias viven en la raiz y asi lo declaran.
"""
import html as _html
import json
import re
from pathlib import Path

from guias import GUIAS
from plantilla_comun import ICONO_TG, ICONOS, PIE, nav_html

RAIZ = Path(__file__).resolve().parent
BASE = "https://gangasofertas.com"
IMG = f"{BASE}/assets/og-image.png"
CANAL = "https://t.me/GangasOfertasChollos"

# Mapea los slugs de categoria a su etiqueta visible, para los enlaces finales.
ETIQUETA = {
    "general": "Todas las ofertas",
    "moviles-electronica": "Móviles y electrónica",
    "ropa-y-calzado": "Ropa y calzado",
    "gaming-consolas": "Gaming y consolas",
    "higiene-cuidado-personal": "Higiene y cuidado personal",
    "juguetes-infantil": "Juguetes e infantil",
    "papeleria-oficina": "Papelería y oficina",
    "chollos-amazon-telegram": "Chollos en Telegram",
}

# Titulo del hub. Es una pagina de indice: su trabajo es repartir enlaces a los
# articulos, no competir con ellos por una consulta concreta.
# 65 caracteres: se cortaba en el结果显示 de Google a mitad de "GangasOfertas".
# La marca sobra cuando la SERP ya muestra el dominio en la línea de enlace.
HUB_TITULO = "Guías para encontrar chollos y ofertas en Amazon"
HUB_DESC = (
    "Guías prácticas sobre chollos en Amazon: cómo detectar errores de precio, "
    "cómo saber si un descuento es real y cuándo comprar más barato."
)


def esc(v) -> str:
    return _html.escape(str(v if v is not None else ""), quote=True)


def migas(nombre: str, url: str, con_hub: bool = True) -> dict:
    """BreadcrumbList.

    `con_hub=False` es para la propia pagina del hub: si no, la migas sale
    "Inicio > Guias > Guias", con el mismo nodo repetido y una posicion
    duplicada que Google interpreta como breadcrumb manipulado.
    """
    items = [{"@type": "ListItem", "position": 1, "name": "Inicio", "item": f"{BASE}/"}]
    pos = 2
    if con_hub:
        items.append({"@type": "ListItem", "position": pos, "name": "Guías",
                      "item": f"{BASE}/guias.html"})
        pos = 3
    items.append({"@type": "ListItem", "position": pos, "name": nombre, "item": url})
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Articulos
# ─────────────────────────────────────────────────────────────────────────────
PLANTILLA_ART = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{titulo}</title>
<meta name="description" content="{descripcion}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{base}/{slug}.html">

<meta property="og:type" content="article">
<meta property="og:site_name" content="GangasOfertas.com">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descripcion}">
<meta property="og:url" content="{base}/{slug}.html">
<meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{titulo}">
<meta name="twitter:description" content="{descripcion}">
<meta name="twitter:image" content="{img}">

{iconos}
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/icono-tg.css">
<script type="application/ld+json">
{schema}
</script>
</head>
<body>

<header class="cabecera">
  <div class="wrap">
    {icono}
    <h1>{icono_cat} {h1}</h1>
    <p>{resumen}</p>
    <nav class="nav" aria-label="Navegación principal">
{nav}
    </nav>
  </div>
</header>

<main class="contenido wrap">
  <article class="editorial">
{cuerpo}
    <h3>Preguntas frecuentes</h3>
    <div class="faq">
{faq}
    </div>
    <p class="editorial__rel">{enlaces}</p>
    <p class="editorial__nota">Escrito en GangasOfertas.com. Recuerda que los precios
      que aparecen en la web son los que se detectaron al publicar cada oferta en el
      canal de Telegram: <a href="BlackFriday/metodologia.html">cómo trabajamos</a> y
      <a href="BlackFriday/sobre-nosotros.html">quiénes somos</a>.</p>
  </article>

  <h2>Otras guías</h2>
  <nav class="nav subnav" aria-label="Otras guías">
{otras}
  </nav>

  <p class="enlace-telegram">
    <a class="oferta-comprar" style="display:inline-block;padding:13px 26px" href="{canal}" target="_blank" rel="noopener">Únete al canal de Telegram</a>
  </p>
</main>

{pie}

</body>
</html>
"""


def cuerpo_articulo(secciones) -> str:
    partes = []
    for h2, parrafos in secciones:
        partes.append(f"<h3>{esc(h2)}</h3>")
        for p in parrafos:
            partes.append(f"<p>{p}</p>")
    return "\n".join(partes)


def bloque_faq(faq, prefijo: str) -> str:
    lineas = []
    for i, (q, r) in enumerate(faq, 1):
        lineas.append(f'<details id="{prefijo}-{i}"><summary>{esc(q)}</summary>'
                      f"<p>{r}</p></details>")
    return "\n".join(lineas)


def schema_articulo(slug, titulo, descripcion, faq) -> str:
    url = f"{BASE}/{slug}.html"
    grafo = [
        migas(titulo, url),
        {
            "@type": "Article",
            "@id": f"{url}#article",
            "headline": titulo,
            "description": descripcion,
            "inLanguage": "es-ES",
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "author": {"@type": "Organization", "name": "GangasOfertas.com",
                       "url": f"{BASE}/"},
            "publisher": {"@type": "Organization", "name": "GangasOfertas.com",
                          "url": f"{BASE}/"},
            "image": IMG,
        },
        {
            "@type": "FAQPage",
            "@id": f"{url}#faq",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": r}}
                           for q, r in faq],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": grafo},
                      ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Hub
# ─────────────────────────────────────────────────────────────────────────────
PLANTILLA_HUB = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{titulo}</title>
<meta name="description" content="{descripcion}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{base}/guias.html">

<meta property="og:type" content="website">
<meta property="og:site_name" content="GangasOfertas.com">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descripcion}">
<meta property="og:url" content="{base}/guias.html">
<meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{titulo}">
<meta name="twitter:description" content="{descripcion}">
<meta name="twitter:image" content="{img}">

{iconos}
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/icono-tg.css">
<script type="application/ld+json">
{schema}
</script>
</head>
<body>

<header class="cabecera">
  <div class="wrap">
    {icono}
    <h1>📚 Guías de chollos y ofertas</h1>
    <p>Cómo encontrar ofertas reales en Amazon España y no perder tiempo en rebajas infladas</p>
    <nav class="nav" aria-label="Navegación principal">
{nav}
    </nav>
  </div>
</header>

<main class="contenido wrap">
  <div class="editorial">
    <h2 class="editorial__h2">Guías para comprar mejor en Amazon</h2>
    <p>En este sitio publicamos las ofertas que llegan a nuestro canal de Telegram. Pero un
      descuento del 50% en la etiqueta no siempre significa que ahorras la mitad: a menudo
      el precio de referencia se ha inflado unos días antes. Estas guías explican cómo
      comprobarlo, cuándo comprar y dónde mirar, con métodos que puedes aplicar tú mismo.</p>
    <p>No rastreamos Amazon ni seguimos sus precios de forma continua: recogemos lo que se
      publica en <a href="https://t.me/GangasOfertasChollos" target="_blank" rel="noopener">@GangasOfertasChollos</a>.
      Por eso lo que explicamos aquí es comprobable por ti con las herramientas públicas
      (historial de precios, comparadores, la propia ficha del producto), y no dependemos
      de ninguna promesa nuestra.</p>
    <ul class="editorial__lista">
      <li><strong>Empieza por el método.</strong> Si solo vas a leer una, lee
        <a href="ofertas-reales-vs-descuentos-falsos.html">oferta real o descuento falso</a>:
        es la que decide si lo que has visto es un ahorro o una etiqueta.</li>
      <li><strong>Si buscas errores de precio:</strong>
        <a href="como-detectar-errores-de-precio-amazon.html">cómo detectar errores de precio</a>
        explica las señales y los horarios.</li>
      <li><strong>Si quieres comprar más barato sin repetir la búsqueda:</strong>
        <a href="amazon-warehouse-outlet-y-devoluciones.html">Warehouse, Outlet y devoluciones</a>
        son tres secciones con descuentos del 20 al 50% que casi nadie mira.</li>
      <li><strong>Si quieres saber cuándo comprar:</strong>
        <a href="cuando-comprar-en-amazon-espana.html">el calendario de precios</a> explica el
        patrón de cada categoría.</li>
    </ul>
  </div>

  <h2>Todas las guías</h2>
  <div class="rejilla" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
{tarjetas}
  </div>

  <h2>Ofertas por categoría</h2>
  <nav class="nav subnav" aria-label="Categorías de ofertas">
{enlaces_cat}
  </nav>

  <p class="enlace-telegram">
    <a class="oferta-comprar" style="display:inline-block;padding:13px 26px" href="{canal}" target="_blank" rel="noopener">Únete al canal de Telegram</a>
  </p>
</main>

{pie}

</body>
</html>
"""


def main() -> None:
    # ── articulos ──
    for slug, h1, titulo, descripcion, icono_cat, resumen, secciones, faq, enlaces in GUIAS:
        otras = "\n".join(
            f'    <a href="{otro[0]}.html">{otro[5]} · {otro[1]}</a>'
            for otro in GUIAS if otro[0] != slug)

        enlaces_html = "Ver también las ofertas de " + " · ".join(
            f'<a href="{e}.html">{esc(ETIQUETA.get(e, e))}</a>' for e in enlaces) \
            if enlaces else ""

        html = PLANTILLA_ART.format(
            slug=slug, titulo=esc(titulo), descripcion=esc(descripcion),
            base=BASE, img=IMG, canal=CANAL, h1=esc(h1), resumen=esc(resumen),
            icono_cat=icono_cat,
            nav=nav_html(f"{slug}.html"),
            icono=ICONO_TG.format(prefijo="", canal=CANAL),
        iconos=ICONOS.format(p="assets/"),
            cuerpo=cuerpo_articulo(secciones),
            faq=bloque_faq(faq, slug),
            enlaces=enlaces_html,
            otras=otras,
            schema=schema_articulo(slug, titulo, descripcion, faq),
            pie=PIE,
        )
        destino = RAIZ / f"{slug}.html"
        destino.write_text(html, encoding="utf-8", newline="\r\n")
        palabras = len(re.sub(r"<[^>]+>", " ", _html.unescape(html)).split())
        print(f"  generado {destino.name} ({palabras} palabras)")

    # ── hub ──
    tarjetas = "\n".join(
        f'    <a href="{g[0]}.html" class="oferta">\n'
        f'      <div class="oferta-cuerpo">\n'
        f'        <div class="oferta-titulo">{g[4]} {esc(g[1])}</div>\n'
        f'        <div class="oferta-meta">{esc(g[5])}</div>\n'
        f"      </div>\n"
        f"    </a>"
        for g in GUIAS)

    # Solo las categorias del catalogo: las entradas que apuntan a una pagina
    # SEO suelta (chollos-amazon-telegram) ya estan en el pie de este.
    CATALOGO = ["general", "moviles-electronica", "ropa-y-calzado", "gaming-consolas",
                "higiene-cuidado-personal", "juguetes-infantil", "papeleria-oficina"]
    enlaces_cat = "\n".join(
        f'    <a href="{slug}.html">{esc(ETIQUETA[slug])}</a>' for slug in CATALOGO)

    schema_hub = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            migas("Guías", f"{BASE}/guias.html", con_hub=False),
            {
                "@type": "CollectionPage",
                "@id": f"{BASE}/guias.html#collection",
                "url": f"{BASE}/guias.html",
                "name": "Guías de chollos y ofertas",
                "description": HUB_DESC,
                "inLanguage": "es-ES",
                "isPartOf": {"@id": f"{BASE}/#website"},
                "hasPart": [
                    {"@type": "Article", "headline": g[1],
                     "url": f"{BASE}/{g[0]}.html"} for g in GUIAS
                ],
            },
        ],
    }, ensure_ascii=False, indent=2)

    hub = PLANTILLA_HUB.format(
        titulo=esc(HUB_TITULO), descripcion=esc(HUB_DESC), base=BASE, img=IMG,
        canal=CANAL, nav=nav_html("guias.html"),
        icono=ICONO_TG.format(prefijo="", canal=CANAL),
        iconos=ICONOS.format(p="assets/"),
        tarjetas=tarjetas, enlaces_cat=enlaces_cat, schema=schema_hub, pie=PIE,
    )
    destino = RAIZ / "guias.html"
    destino.write_text(hub, encoding="utf-8", newline="\r\n")
    print(f"  generado guias.html ({len(GUIAS)} guias listadas)")


if __name__ == "__main__":
    main()