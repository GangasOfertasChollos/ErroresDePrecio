"""Genera las 7 paginas de catalogo a partir de una unica definicion.

Antes cada HTML repetia ~20 lineas de CSS y ~55 de JS identicas; cualquier
correccion habia que replicarla 7 veces. Ahora comparten assets/style.css y
assets/app.js, y este script es la unica fuente que hay que editar.

El menu, el icono de Telegram y el pie se toman de plantilla_comun.py para que
regenerar las paginas no deshaga el trabajo de maquetacion. El texto de cada
categoria sale de contenido_categoria.py.

Que las ofertas se pinten en el HTML y no solo con fetch()
------------------------------------------------------
Este es el cambio que justifico el modulo. Las paginas se generaban con un
<section id="ofertas"> vacio y un fetch() a data/<slug>.json: el HTML servido
no contenia ni una oferta, ni un titulo de producto, ni un precio. Para un
crawler eran paginas de cuarenta palabras, es decir, thin content.

Ahora el HTML llega con las tarjetas ya escritas, y assets/app.js solo refresca
los datos cuando puede. El usuario ve las ofertas antes (sin esperar al
fetch) y el crawler las encuentra. El JSON sigue siendo la fuente de verdad de
la ultima ejecucion del bot; aqui se usa para "quemar" lo que hay en el HTML.

Por que no se genera un HTML por oferta
---------------------------------------
Se descarto. Serian paginas de producto con una descripcion generica y sin
historial de precios, que es exactamente el perfil de contenido pobre que este
proyecto quiere evitar. El texto util se concentra en las paginas de categoria,
que si pueden dar una opinion propia y enlazarse entre si.
"""
import html as _html
import json
import re
from datetime import date
from pathlib import Path

from contenido_categoria import CONTENIDO
from plantilla_comun import ICONO_TG, NAV, PIE, nav_html

RAIZ = Path(__file__).resolve().parent
BASE = "https://gangasofertas.com"
IMG = f"{BASE}/assets/og-image.png"
CANAL = "https://t.me/GangasOfertasChollos"

# slug, h1 (cabecera), subtitulo, icono. El texto largo y el SEO salen de
# contenido_categoria.py; aqui solo queda lo que va en la cabecera visible.
CATEGORIAS = [
    ("ropa-y-calzado", "Ropa y calzado", "Moda, zapatillas, abrigos y complementos", "👔"),
    ("moviles-electronica", "Móviles y electrónica", "Smartphones, informática, audio y gadgets", "📱"),
    ("gaming-consolas", "Gaming y consolas", "PS5, Nintendo Switch, mandos y videojuegos", "🎮"),
    ("higiene-cuidado-personal", "Higiene y cuidado personal", "Cosmética, cuidado facial, champús y belleza", "🧴"),
    ("juguetes-infantil", "Juguetes e infantil", "LEGO, muñecas, juegos de mesa y puericultura", "🧸"),
    ("papeleria-oficina", "Papelería y oficina", "Material escolar, sillas de oficina y escritura", "📚"),
    ("general", "Todas las ofertas", "El feed completo con las mejores gangas de Amazon España", "⚡"),
]

# Etiqueta corta para los enlaces cruzados entre categorias.
ETIQUETA = {slug: h1 for slug, h1, _s, _i in CATEGORIAS}


# ─────────────────────────────────────────────────────────────────────────────
# Lectura de datos y utilidades
# ─────────────────────────────────────────────────────────────────────────────
def cargar(slug: str) -> list:
    ruta = RAIZ / "data" / f"{slug}.json"
    if not ruta.exists():
        return []
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return datos if isinstance(datos, list) else []


def esc(valor) -> str:
    return _html.escape(str(valor if valor is not None else ""), quote=True)


def a_numero(es):
    """"4.22 €" / "4,22 €" / "4.22" -> float. None si no hay cifra."""
    s = str(es or "").replace(" ", "").replace(" ", "")
    s = re.sub(r"[^\d.,]", "", s)
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if len(s.split(",")[-1]) == 2 else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def fecha_corta(iso: str) -> str:
    if not iso:
        return ""
    try:
        return date.fromisoformat(str(iso)[:10]).strftime("%d/%m/%Y")
    except ValueError:
        return ""


RE_ANTES = re.compile(
    r"\b(?:antes|pvp|precio\s+anterior|val(?:or|ia)\s+anterior)\b\s*(?:de\s*)?[:\-]?\s*"
    r"([0-9][0-9.,\u00a0 ]*)\s*(?:€|eur)?", re.I)
RE_PORCENTAJE = re.compile(r"(\d{1,3}(?:[.,]\d+)?)\s*%")
RE_PORCENTAJE_EN = re.compile(r"descuento|ahorro|rebaja|\boff\b", re.I)


def precios(o) -> dict:
    """Misma logica que preciosDe() en assets/app.js.

    Se mantiene el par de funciones a proposito, no por descuido. Si el
    renderizado del servidor y el del navegador dieran cifras distintas, la
    pagina cambiaria sola al cargar, que es el peor sintoma posible en una web
    de precios. Cuando se toque una, hay que tocar la otra.
    """
    actual = a_numero(o.get("price"))
    texto = f"{o.get('description') or ''} \n {o.get('title') or ''}"

    anterior = None
    for cand in [o.get("old_price"), (RE_ANTES.search(texto).group(1)
                                      if RE_ANTES.search(texto) else None)]:
        n = a_numero(cand)
        # Solo vale como "antes" si es mayor que el precio actual.
        if n and n > 0 and (actual is None or n > actual):
            anterior = n
            break

    descuento = None
    if actual and actual > 0 and anterior and anterior > actual:
        pct = round((anterior - actual) / anterior * 100)
        descuento = pct if pct > 0 else None
    if descuento is None:
        for cand in [o.get("discount")] + [m.group(1) for m in RE_PORCENTAJE.finditer(texto)]:
            n = a_numero(cand)
            if n and 0 < n < 100:
                # Rechaza un "%" suelto que no sea una rebaja ("80% de bateria").
                pos = texto.find(cand) if isinstance(cand, str) else -1
                ctx = texto[max(0, pos - 26):pos + 40] if pos >= 0 else ""
                if cand == o.get("discount") or RE_PORCENTAJE_EN.search(ctx) \
                        or re.search(r"[-−–(]\s*$", texto[max(0, pos - 3):pos] or ""):
                    descuento = round(n)
                    break

    return {
        "actual": actual,
        "anterior": anterior,
        "descuento": descuento,
        "texto_actual": str(o.get("price") or "Ver precio"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tarjeta en HTML: identica a la que pinta app.js
# ─────────────────────────────────────────────────────────────────────────────
def tarjeta(o) -> str:
    p = precios(o)
    fecha = fecha_corta(o.get("date", ""))
    titulo = esc(re.sub(r"\*{1,3}", "", str(o.get("title") or "Oferta Amazon")).strip())

    img = ""
    if o.get("image"):
        img = (f'<div class="oferta-img"><img src="{esc(o["image"])}" alt="{titulo}" '
               f'loading="lazy" decoding="async" itemprop="image"></div>')

    antes = (f'<span class="oferta-precio-antes">{esc(f"{p["anterior"]:.2f} €")}</span>'
             if p["anterior"] else '<span class="oferta-precio-antes es-hueco">No disponible</span>')
    dto = (f'<span class="oferta-descuento">-{p["descuento"]}%</span>'
           if p["descuento"] else '<span class="oferta-descuento es-hueco">Sin descuento</span>')
    vacio_antes = "" if p["anterior"] else " es-hueco"
    vacio_dto = "" if p["descuento"] else " es-hueco"

    precios_html = (
        '<div class="oferta-precios">'
        '<div class="oferta-precio-caja">'
        '<span class="oferta-precio-etiqueta">Precio actual</span>'
        f'<span class="oferta-precio" itemprop="price" content="{p["actual"]:.2f}" '
        f'>{esc(p["texto_actual"])}</span>'
        "</div>"
        '<div class="oferta-precio-caja">'
        '<span class="oferta-precio-etiqueta">Precio anterior</span>'
        + antes +
        "</div>"
        f'<div class="oferta-precio-caja oferta-precio-caja--descuento{vacio_antes}{vacio_dto}">'
        '<span class="oferta-precio-etiqueta">Descuento</span>'
        + dto +
        "</div></div>"
    )

    desc = (f'<div class="oferta-descripcion" itemprop="description">{esc(o["description"])}</div>'
            if o.get("description") else "")

    url = esc(o.get("amazon_url", ""))

    extra = ""
    if o.get("brand"):
        extra += f'<meta itemprop="brand" content="{esc(o["brand"])}">'
    if o.get("gtin"):
        extra += f'<meta itemprop="gtin" content="{esc(o["gtin"])}">'
    if o.get("mpn"):
        extra += f'<meta itemprop="mpn" content="{esc(o["mpn"])}">'

    return (
        f'<article class="oferta" itemscope itemtype="https://schema.org/Offer">'
        f'{img}<div class="oferta-cuerpo">'
        f'<div class="oferta-titulo" itemprop="name">{titulo}</div>'
        f'{precios_html}'
        f'<div class="oferta-meta">{esc(fecha)}</div>'
        f'{desc}'
        "</div>"
        f'<a class="oferta-comprar" href="{url}" target="_blank" '
        f'rel="nofollow sponsored noopener" itemprop="url">Ver oferta en Amazon</a>'
        '<meta itemprop="priceCurrency" content="EUR">'
        '<meta itemprop="availability" content="https://schema.org/InStock">'
        '<meta itemprop="itemCondition" content="https://schema.org/NewCondition">'
        '<meta itemprop="seller" content="Amazon España">'
        f"{extra}</article>"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Bloque editorial
# ─────────────────────────────────────────────────────────────────────────────
def bloque_editorial(slug: str) -> str:
    d = CONTENIDO[slug]
    # Sin h1 propio: el de la cabecera (<h1>📱 Móviles y electrónica</h1>) ya es
    # el titular de la pagina y meter un segundo h1 con el mismo texto solo
    # confunde al crawler. Este h2 es la variante larga, la que incluye
    # "en Amazon España" y por tanto la intencion de busqueda completa.
    partes = ['<div class="editorial">']
    partes.append(f'<h2 class="editorial__h2">{esc(d["h1"])}</h2>')
    for p in d["intro"]:
        partes.append(f"<p>{p}</p>")

    for h2, parrafos in d["secciones"]:
        partes.append(f"<h3>{esc(h2)}</h3>")
        for p in parrafos:
            partes.append(f"<p>{p}</p>")

    # Guia de compra: es el bloque mas enlazable del sitio, asi que sus
    # titulos van en h4 para no competir con los h3 de las secciones.
    if d["como_elegir"]:
        partes.append("<h3>Cómo elegir y cuándo comprar</h3>")
        partes.append('<ul class="editorial__lista">')
        for h3, p in d["como_elegir"]:
            partes.append(f"<li><strong>{esc(h3)}.</strong> {p}</li>")
        partes.append("</ul>")

    partes.append("<h3>Preguntas frecuentes</h3>")
    partes.append('<div class="faq">')
    for i, (q, r) in enumerate(d["faq"], 1):
        partes.append(f'<details id="faq-{slug}-{i}"><summary>{esc(q)}</summary>'
                      f"<p>{r}</p></details>")
    partes.append("</div>")

    # Enlaces cruzados: reparte autoridad entre categorias y le dice al crawler
    # que estas paginas forman un conjunto y no siete sueltas.
    rel = [r for r in d["relacionados"] if r != slug]
    if rel:
        enlaces = " · ".join(
            f'<a href="{r}.html">{esc(ETIQUETA.get(r, r))}</a>' for r in rel)
        partes.append('<p class="editorial__rel">Ofertas relacionadas: ' + enlaces + "</p>")

    partes.append('<p class="editorial__nota">Los precios y la disponibilidad '
                  "son los que se detectaron al publicar la oferta en el canal de "
                  'Telegram. <a href="BlackFriday/metodologia.html">Cómo trabajamos</a> '
                  "y <a href=\"BlackFriday/aviso-legal.html\">aviso legal</a>.</p>")
    partes.append("</div>")

    return "\n".join(partes)


# ─────────────────────────────────────────────────────────────────────────────
# Datos estructurados
# ─────────────────────────────────────────────────────────────────────────────
def migas(slug: str) -> str:
    """BreadcrumbList. Las categorias cuelgan de la portada, no de general.html:
    son paginas hermanas, no hijas del feed."""
    items = [{"@type": "ListItem", "position": 1, "name": "Inicio",
              "item": f"{BASE}/"}]
    if slug != "general":
        items.append({"@type": "ListItem", "position": 2, "name": "Categorías",
                      "item": f"{BASE}/categorias.html"})
        items.append({"@type": "ListItem", "position": 3,
                      "name": ETIQUETA[slug], "item": f"{BASE}/{slug}.html"})
    else:
        items.append({"@type": "ListItem", "position": 2, "name": "Todas las ofertas",
                      "item": f"{BASE}/{slug}.html"})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def schema_pagina(slug: str, ofertas: list) -> dict:
    d = CONTENIDO[slug]
    grafo = [
        migas(slug),
        {
            "@type": "CollectionPage",
            "@id": f"{BASE}/{slug}.html#collection",
            "url": f"{BASE}/{slug}.html",
            "name": d["h1"],
            "description": d["descripcion"],
            "inLanguage": "es-ES",
            "isPartOf": {"@id": f"{BASE}/#website"},
            "breadcrumb": {"@id": f"{BASE}/{slug}.html#breadcrumb"},
        },
    ]

    # El ItemList va en el HTML, no lo inyecta el JS. Google lo lee igual, pero
    # asi las ofertas quedan declaradas aunque no llegue a ejecutar el script.
    items = [o for o in ofertas if precios(o)["actual"] is not None]
    if items:
        grafo.append({
            "@type": "ItemList",
            "@id": f"{BASE}/{slug}.html#lista",
            "name": d["h1"],
            "numberOfItems": len(items),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i,
                    "url": f"{BASE}/{slug}.html#{i}",
                    "item": {
                        "@type": "Offer",
                        "name": re.sub(r"\*{1,3}", "", str(o.get("title") or "Oferta Amazon")).strip(),
                        "url": o.get("amazon_url") or f"{BASE}/{slug}.html",
                        "image": o.get("image") or IMG,
                        "priceCurrency": "EUR",
                        "price": f'{precios(o)["actual"]:.2f}',
                        "availability": "https://schema.org/InStock",
                        "itemCondition": "https://schema.org/NewCondition",
                        "seller": {"@type": "Organization", "name": "Amazon España"},
                    },
                }
                for i, o in enumerate(items[:30], 1)
            ],
        })

    grafo.append({
        "@type": "FAQPage",
        "@id": f"{BASE}/{slug}.html#faq",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": r}}
            for q, r in d["faq"]
        ],
    })

    return {"@context": "https://schema.org", "@graph": grafo}


# ─────────────────────────────────────────────────────────────────────────────
# Plantilla
# ─────────────────────────────────────────────────────────────────────────────
PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{titulo}</title>
<meta name="description" content="{descripcion}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{base}/{slug}.html">

<meta property="og:type" content="website">
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

<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/icono-tg.css">
<meta name="google-site-verification" content="E4_nuunpXWLlV4jpR5qmBPKLhB2kFV_MTM6N_J9xRSc">
<meta name="google-site-verification" content="uzqlh-QjEzCDqWUTkJpgkqlJsHSt0Xjbh82vV-orJQ8">
<script type="application/ld+json">
{schema}
</script>
</head>
<body data-feed="{slug}">

<header class="cabecera">
  <div class="wrap">
    {icono}
    <h1>{icono_cat} {h1_cabecera}</h1>
    <p>{subtitulo}</p>
    <nav class="nav" aria-label="Navegación principal">
{nav}
    </nav>
  </div>
</header>

<main class="contenido wrap">

  {editorial}

  {estado_bloque}
  <section id="ofertas" class="rejilla" aria-live="polite">{tarjetas}</section>

  <p class="enlace-telegram">
    ¿Quieres más? <a href="{canal}" target="_blank" rel="noopener">Únete al canal de Telegram</a>
  </p>

</main>

{pie}

<script src="assets/app.js" defer></script>
</body>
</html>
"""


def main() -> None:
    for slug, h1_cabecera, subtitulo, icono_cat in CATEGORIAS:
        d = CONTENIDO[slug]
        ofertas = cargar(slug)
        # El #estado solo se emite cuando NO hay tarjetas. Si las hay, el
        # HTML ya viene completo y un "Cargando ofertas..." seria mentira: el
        # usuario ve las ofertas antes de que corra el script. App.js lo quita
        # si llega a refrescar, y si el fetch falla lo coloca el mismo.
        if ofertas:
            estado_bloque = ""
        else:
            estado_bloque = ('<div id="estado" class="estado" role="status">'
                             "Todavía no hay ofertas publicadas en esta sección. "
                             "Únete al canal de Telegram para recibirlas en cuanto "
                             "se publiquen.</div>")
        # El id de cada tarjeta coincide con la "position" del ItemList del
        # JSON-LD, para que ambos se refieran a la misma oferta.
        tarjetas = "".join(
            tarjeta(o).replace('<article class="oferta"',
                               f'<article class="oferta" id="{i}"', 1)
            for i, o in enumerate(ofertas, 1))

        schema = json.dumps(schema_pagina(slug, ofertas), ensure_ascii=False, indent=2)

        html = PLANTILLA.format(
            slug=slug,
            titulo=d["titulo_seo"],
            descripcion=esc(d["descripcion"]),
            base=BASE, img=IMG, canal=CANAL,
            h1_cabecera=h1_cabecera, subtitulo=subtitulo, icono_cat=icono_cat,
            nav=nav_html(f"{slug}.html"),
            icono=ICONO_TG.format(prefijo="", canal=CANAL),
            editorial=bloque_editorial(slug),
            estado_bloque=estado_bloque, tarjetas=tarjetas,
            schema=schema, pie=PIE,
        )
        destino = RAIZ / f"{slug}.html"
        # La raiz del repositorio usa CRLF de forma consistente (ver .gitattributes
        # y el resto de HTML); con newline="" se emitiria LF y quedaria mezclado.
        destino.write_text(html, encoding="utf-8", newline="\r\n")
        palabras = len(re.sub(r"<[^>]+>", " ", html).split())
        print(f"  generado {destino.name} ({palabras} palabras, "
              f"{len(ofertas)} ofertas servidas en el HTML)")


if __name__ == "__main__":
    main()