"""Marcado compartido por la seccion Amazon Prime Days de GangasOfertas.com.

Es el equivalente de plantilla_comun.py para la seccion PrimeDays/, que tiene su
propia hoja de estilos (assets/css/style.css) y por tanto su propio esqueleto de
pagina. Igual que en el resto del sitio, el menu, el icono de Telegram y el pie
se definen UNA sola vez aqui: las paginas se generan a partir de este modulo,
as que ningun cambio de maquetacion se deshace al regenerar.
"""
import json

CANAL = "https://t.me/GangasOfertasChollos"
CANAL_HISTORIAL = "https://t.me/s/GangasOfertasChollos"
BASE = "https://gangasofertas.com"
SECCION = f"{BASE}/PrimeDays"

# Imagen social propia de la seccion (1200x630). Antes se reutilizaba la de
# BlackFriday, con el problema de que al compartir una pagina de Prime Days en
# WhatsApp, Telegram o X salia una imagen que decia "Black Friday 2026": marca
# equivocada y, ademas, la URL de la imagen hacia la palabra black-friday.
OG_IMG = f"{SECCION}/assets/img/og-prime-days-2026.png"

ACTUALIZADO = "6 de octubre de 2026"

# Menu de la seccion. El enlace al padre (la portada del sitio) va siempre
# primero y con su propia clase, para que no se confunda con las paginas de la
# seccion.
NAV = [
    ("index.html", "Inicio"),
    ("que-es-amazon-prime-days.html", "Qué es"),
    ("fechas-amazon-prime-days.html", "Fechas"),
    ("ofertas-prime-days-2026.html", "Ofertas"),
    ("descuentos-reales-o-falsos.html", "Descuentos reales"),
    ("como-aprovechar-prime-days.html", "Cómo aprovecharlo"),
    ("canal-telegram-ofertas.html", "Canal Telegram"),
    ("faq.html", "FAQ"),
]

# Enlaces al canal: siempre con sponsored+nofollow+noopener. sponsored porque el
# sitio monetiza con esos enlaces (comision de afiliado) y nofollow por lo mismo;
# Google pide declarar el contenido patrocinado en lugar de fingir que es un
# enlace editorial. Un solo punto de construccion para que no se pueda olvidar
# en una pagina nueva.
_REL_TG = 'target="_blank" rel="sponsored nofollow noopener"'


def tg(texto: str = "Únete al canal de Telegram") -> str:
    """Enlace al canal de Telegram con los atributos de monetizacion correctos."""
    return f'<a href="{CANAL}" {_REL_TG}>{texto}</a>'


def tg_attr(href: str = CANAL, clase: str = "btn btn--tg", texto: str = "Unirme gratis") -> str:
    """Boton completo al canal, para usar como CTA."""
    return f'<a class="{clase}" href="{href}" {_REL_TG}>{texto}</a>'


AVISO_AFILIADOS = (
    "GangasOfertas.com participa en el Programa de Afiliados de Amazon EU. Como "
    "afiliado, obtengo una comisión por las compras que cumplen los requisitos "
    "aplicables. El precio que pagas es el mismo: no pagas nada extra por usar "
    "estos enlaces."
)

AVISO_MARCA = (
    "Amazon, Amazon Prime y Prime Days son marcas de Amazon.com, Inc. y de sus "
    "filiales. Este sitio no está afiliado a Amazon ni tiene relación con la "
    "empresa. No rastreamos Amazon ni controlamos sus precios: recogemos las "
    "ofertas que se anuncian en nuestro canal de Telegram."
)


def nav_html(actual: str, sangria: str = "      ") -> str:
    """Menu de la seccion. `actual` se marca con aria-current="page".

    El ultimo elemento no lleva salto de linea: la plantilla lo coloca
    seguido a la apertura de <nav>, y un "\n" de mas ahi solo desplaza la
    primera fila del menu en el reparto en varias lineas.
    """
    entradas = [
        f'{sangria}<a class="nav__padre" href="../index.html" '
        f'title="Volver a GangasOfertas.com">⌂ GangasOfertas.com</a>',
        # Enlace a la otra seccion de campana. Con la clase nav__otro para que se
        # distinga de las paginas de esta seccion (mismo criterio que en
        # BlackFriday/index.html).
        f'{sangria}<a class="nav__otro" href="../BlackFriday/index.html" '
        f'title="La campaña del 27 de noviembre de 2026">Black Friday</a>',
    ]
    for href, label in NAV:
        marca = ' aria-current="page"' if href == actual else ""
        entradas.append(f'{sangria}<a href="{href}"{marca}>{label}</a>')
    entradas.append(f'{sangria}{tg_attr(clase="btn btn--tg btn--sm", texto="Unirme gratis")}')
    # Primer elemento pegado al <nav>, el resto en su propia linea.
    return "\n".join([entradas[0]] + entradas[1:])


PIE_GRUPOS = [
    ("Amazon Prime Days", [
        ("index.html", "Guía completa"),
        ("que-es-amazon-prime-days.html", "Qué son los Prime Days"),
        ("fechas-amazon-prime-days.html", "Fechas y calendario"),
        ("ofertas-prime-days-2026.html", "Ofertas por categoría"),
    ]),
    ("Guías", [
        ("descuentos-reales-o-falsos.html", "Descuentos reales o falsos"),
        ("como-aprovechar-prime-days.html", "Cómo aprovecharlo"),
        ("canal-telegram-ofertas.html", "El canal de Telegram"),
        ("faq.html", "Preguntas frecuentes"),
    ]),
    ("Catálogo en vivo", [
        (f"{BASE}/general.html", "Todas las ofertas"),
        (f"{BASE}/categorias.html", "Todas las categorías"),
        (f"{BASE}/moviles-electronica.html", "Móviles y electrónica"),
        (f"{BASE}/gaming-consolas.html", "Gaming y consolas"),
    ]),
    ("Otras secciones", [
        (f"{BASE}/index.html", "Portada"),
        (f"{BASE}/chollos-de-amazon.html", "Chollos de Amazon"),
        (f"{BASE}/errores-de-precio-amazon.html", "Errores de precio"),
        (f"{BASE}/BlackFriday/index.html", "Black Friday 2026"),
    ]),
    ("Confianza y legal", [
        (f"{BASE}/BlackFriday/metodologia.html", "Cómo trabajamos"),
        (f"{BASE}/BlackFriday/sobre-nosotros.html", "Sobre nosotros"),
        (f"{BASE}/BlackFriday/aviso-legal.html", "Aviso legal"),
        (f"{BASE}/BlackFriday/politica-privacidad.html", "Política de privacidad"),
    ]),
]


def _grupo(titulo: str, enlaces: list) -> str:
    items = "\n".join(
        f'          <li><a href="{href}">{label}</a></li>' for href, label in enlaces
    )
    return f"""      <div>
        <h4>{titulo}</h4>
        <ul>
{items}
        </ul>
      </div>"""


PIE = f"""<footer class="site-footer">
  <div class="wrap">
    <div class="footer__grid">
      <div>
        <a class="brand" href="index.html" style="margin-bottom:14px">
          <span class="brand__mark" aria-hidden="true">%</span>
          <span>GangasOfertas.com
            <span class="brand__sub">Amazon Prime Days · España</span>
          </span>
        </a>
        <p class="footer__about">
          Canal de Telegram especializado en gangas, chollos y errores de precio de Amazon España.
          Cada oferta que publicamos llega también a la web, con su precio y su enlace.
        </p>
        <p style="margin-top:1rem">{tg_attr(clase="btn btn--tg btn--sm")}</p>
      </div>
{chr(10).join(_grupo(t, e) for t, e in PIE_GRUPOS)}
    </div>
    <div class="footer__bottom">
      <span>© 2026 GangasOfertas.com · Amazon España · Actualizado desde el canal de Telegram</span>
      <span>{tg("@GangasOfertasChollos")}</span>
    </div>
    <p class="footer__disclaimer">{AVISO_AFILIADOS}</p>
    <p class="footer__disclaimer">{AVISO_MARCA} Como comprador en España tienes 14 días naturales de
      desistimiento desde la recepción del producto.</p>
  </div>
</footer>"""


PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{{titulo}}</title>
<meta name="description" content="{{desc}}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{{canonical}}">
<meta name="theme-color" content="#14181f">

<meta property="og:type" content="article">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="GangasOfertas.com — Amazon Prime Days">
<meta property="og:title" content="{{titulo}}">
<meta property="og:description" content="{{desc}}">
<meta property="og:url" content="{{canonical}}">
<meta property="og:image" content="{{og_img}}">
<meta property="og:image:alt" content="{{alt_img}}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{titulo}}">
<meta name="twitter:description" content="{{desc}}">
<meta name="twitter:image" content="{{og_img}}">

<link rel="icon" href="{{base}}/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/css/style.css">
<link rel="stylesheet" href="../assets/icono-tg.css">

{{schema}}</head>

<body>
<a class="skip-link" href="#contenido">Saltar al contenido principal</a>

<div class="topbar">
  <strong>Amazon Prime Days</strong> · Cada ganga de Amazon España te llega al instante en
  {{tg_topbar}}
</div>

<header class="site-header">
  <div class="wrap nav">
    {{icono}}
    <a class="brand" href="index.html">
      <span class="brand__mark" aria-hidden="true">%</span>
      <span>GangasOfertas.com
        <span class="brand__sub">Amazon Prime Days · España</span>
      </span>
    </a>
    <button class="nav__toggle" type="button" aria-expanded="false" aria-controls="nav-links" aria-label="Abrir menú">☰</button>
    <nav class="nav__links" id="nav-links" aria-label="Navegación principal">
{{nav}}    </nav>
  </div>
</header>

<main id="contenido">

  <nav class="breadcrumb wrap" aria-label="Ruta de navegación">
    <ol>
      <li><a href="{{base}}/index.html">Inicio</a></li>
      <li><a href="index.html">Prime Days</a></li>
      <li aria-current="page">{{miga}}</li>
    </ol>
  </nav>

{{cuerpo}}
</main>

{{pie}}

<script src="assets/js/main.js" defer></script>
</body>
</html>
"""

# El icono lleva los mismos atributos de monetizacion que el resto de enlaces
# al canal. Es el mismo destino, asi que si este se queda en rel="noopener" la
# pagina mezcla dos criterios para un unico enlace y los validadores no lo
# pueden exigir de forma uniforme.
ICONO_TG = (
    f'<a class="icono-tg" href="{CANAL}" target="_blank" rel="sponsored nofollow noopener" '
    'aria-label="Únete al canal de Telegram @GangasOfertasChollos" '
    'title="Canal de Telegram @GangasOfertasChollos">'
    '<img src="../assets/icono-tg.jpg" alt="" width="180" height="160"></a>'
)


def url_pagina(slug: str) -> str:
    """URL canonica de una pagina de la seccion. index.html se sirve sin nombre."""
    return f"{SECCION}/" if slug == "index.html" else f"{SECCION}/{slug}"


def migas_pagina(miga: str) -> str:
    return f'  <nav class="breadcrumb wrap" aria-label="Ruta de navegación">\n' \
           f'    <ol>\n' \
           f'      <li><a href="{BASE}/index.html">Inicio</a></li>\n' \
           f'      <li><a href="index.html">Prime Days</a></li>\n' \
           f'      <li aria-current="page">{miga}</li>\n' \
           f'    </ol>\n' \
           f'  </nav>'


def schema_breadcrumb(miga: str, slug: str) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio",
             "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "Amazon Prime Days",
             "item": f"{SECCION}/"},
            {"@type": "ListItem", "position": 3, "name": miga, "item": url_pagina(slug)},
        ],
    }


def schema_article(titulo: str, desc: str, slug: str, publicado: str, modificado: str) -> dict:
    return {
        "@type": "Article",
        "headline": titulo,
        "description": desc,
        "datePublished": publicado,
        "dateModified": modificado,
        "inLanguage": "es-ES",
        "image": OG_IMG,
        "author": {"@type": "Organization", "name": "GangasOfertas.com", "url": f"{BASE}/"},
        "publisher": {"@type": "Organization", "name": "GangasOfertas.com", "url": f"{BASE}/"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url_pagina(slug)},
    }


def schema_faq(preguntas: list) -> dict:
    """FAQPage. preguntas = lista de tuplas (pregunta, respuesta)."""
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": p,
                "acceptedAnswer": {"@type": "Answer", "text": r},
            }
            for p, r in preguntas
        ],
    }


def bloque_jsonld(*nodos: dict) -> str:
    """Serializa varios nodos en un unico @graph."""
    return '<script type="application/ld+json">\n' + json.dumps(
        {"@context": "https://schema.org", "@graph": list(nodos)},
        ensure_ascii=False, indent=2
    ) + "\n</script>\n"


def faq_html(preguntas: list, abierta: bool = False) -> str:
    """Markup del FAQ. Cada <details> es un <summary> + cuerpo, igual que en
    BlackFriday, para que la hoja de estilos aplique los mismos estilos."""
    partes = []
    for i, (p, r) in enumerate(preguntas):
        open_attr = " open" if (abierta and i == 0) else ""
        partes.append(
            f'        <details{open_attr}>\n'
            f'          <summary>{p}</summary>\n'
            f'          <div class="faq__body"><p>{r}</p></div>\n'
            f'        </details>'
        )
    return "\n".join(partes)


def render(titulo: str, desc: str, slug: str, miga: str, cuerpo: str,
           schema: dict | None = None, alt_img: str = "Amazon Prime Days en España") -> str:
    """Ensambla una pagina completa de la seccion.

    La sustitucion es por replaces explicitos y NO con str.format. El motivo es
    que `cuerpo` es HTML escrito a mano que puede contener llaves (por ejemplo
    en un atributo style o en un fragmento de JavaScript): con .format, una
    llave suelta en el cuerpo seria interpretada como campo y el fallo aparece
    lejos de su causa. Ademas {{ }} en la PLANTILLA se imprimirian literales.
    """
    grafo = list(schema.values()) if schema else []
    if grafo:
        # El grafo se envuelve en un unico @graph siempre con BreadcrumbList,
        # que es el tipo que mas ayuda a entender la jerarquia en la SERP.
        if not any(n.get("@type") == "BreadcrumbList" for n in grafo):
            grafo.insert(0, schema_breadcrumb(miga, slug))

    cuerpo = cuerpo.replace("{{MIGAS}}", migas_pagina(miga))

    html = PLANTILLA
    for marcador, valor in (
        ("{{titulo}}", titulo),
        ("{{desc}}", desc),
        ("{{canonical}}", url_pagina(slug)),
        ("{{base}}", BASE),
        ("{{og_img}}", OG_IMG),
        ("{{alt_img}}", alt_img),
        ("{{schema}}", bloque_jsonld(*grafo) if grafo else ""),
        ("{{nav}}", nav_html(slug)),
        ("{{icono}}", ICONO_TG),
        ("{{cuerpo}}", cuerpo),
        ("{{pie}}", PIE),
        ("{{miga}}", miga),
        ("{{tg_topbar}}", tg("@GangasOfertasChollos")),
    ):
        html = html.replace(marcador, valor)
    return html