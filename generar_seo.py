"""Genera las 4 paginas SEO de entrada y las mantiene sincronizadas con sitemap.xml.

Eran paginas "puente" sin contenido propio: solo una lista de enlaces, sin robots,
sin Open Graph y sin JSON-LD.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
BASE = "https://gangasofertaschollos.github.io/ErroresDePrecio"
IMG = f"{BASE}/assets/og-image.png"
CANAL = "https://t.me/GangasOfertasChollos"

SECCIONES = [
    ("ropa-y-calzado.html", "👔", "Ropa y calzado", "Moda, zapatillas y complementos"),
    ("moviles-electronica.html", "📱", "Móviles y electrónica", "Smartphones, portátiles y gadgets"),
    ("gaming-consolas.html", "🎮", "Gaming y consolas", "PS5, Nintendo Switch y mandos"),
    ("higiene-cuidado-personal.html", "🧴", "Higiene y cuidado personal", "Cosmética, belleza y cuidado"),
    ("juguetes-infantil.html", "🧸", "Juguetes e infantil", "LEGO, muñecas y juegos de mesa"),
    ("papeleria-oficina.html", "📚", "Papelería y oficina", "Material escolar y escritorio"),
    ("general.html", "⚡", "Todas las ofertas", "Feed completo de chollos"),
]

# slug, h1, meta description, parrafos de apoyo
PAGINAS = [
    ("chollos-de-amazon", "Chollos de Amazon", {
        "title": "Chollos de Amazon | Gangas Ofertas y Chollos",
        "desc": "Chollos de Amazon España y ofertas seleccionadas. Descubre precios bajos y oportunidades rebajadas en todas las categorías.",
        "h1": "Chollos de Amazon",
        "intro": "Selección de chollos de Amazon España organizados por categoría, con el precio y el enlace directo al producto.",
        "texto": [
            "Cada chollo que publicamos en el canal de Telegram aparece aquí automáticamente, con el título del producto, el precio detectado y el enlace a Amazon España.",
            "Como los precios en Amazon cambian con frecuencia, el enlace y el precio que ves son los del momento en que se publicó la oferta. Entra en el enlace para comprobar la disponibilidad y el precio final.",
        ],
        "faq": [
            ("¿Cada cuánto se actualizan los chollos?",
             "Cada vez que se publica una oferta nueva en el canal de Telegram. No hay un horario fijo: si no hay nada nuevo, la lista no cambia."),
            ("¿Los precios que aparecen son los definitivos?",
             "Son los precios detectados en el mensaje de Telegram en el momento de publicarlo. Amazon puede cambiarlos en cualquier momento, así que el precio final es el que veas en su web."),
        ],
    }),
    ("errores-de-precio-amazon", "Errores de precio Amazon", {
        "title": "Errores de precio Amazon | Gangas Ofertas y Chollos",
        "desc": "Ofertas y posibles errores de precio en Amazon España. Chollos y oportunidades antes de que se agoten.",
        "h1": "Errores de precio Amazon",
        "intro": "Un error de precio en Amazon es un producto que aparece durante un tiempo a un precio muy por debajo de lo habitual. Estas son las oportunidades que publicamos en el canal.",
        "texto": [
            "Suelen durar pocas horas o incluso minutos. Cuando ocurre, la página de confirmación pide un precio que después no se cobra, y el stock se agota con rapidez.",
            "No podemos garantizar que un error de precio siga vigente ni que el precio se mantenga: la decisión es siempre de Amazon, y nosotros solo publicamos lo que nos llega por el canal.",
        ],
        "faq": [
            ("¿Todos los chollos que veas aquí son errores de precio?",
             "No. La mayoría son ofertas y descuentos reales. Publicamos también los errores de precio que nos llegan, pero no podemos distinguirlos de forma automática al 100%."),
        ],
    }),
    ("articulos-rebajados-amazon", "Artículos rebajados de Amazon", {
        "title": "Artículos rebajados de Amazon | Gangas Ofertas y Chollos",
        "desc": "Selección de artículos rebajados y ofertas de Amazon España. Precios mínimos y descuentos especiales.",
        "h1": "Artículos rebajados de Amazon",
        "intro": "Artículos con descuento publicados en nuestro canal de Telegram, reunidos por categoría para que los encuentres rápido.",
        "texto": [
            "Desde ropa y calzado hasta electrónica, juguetes o papelería: cada artículo incluye su precio detectado y el enlace directo a Amazon España.",
            "Los precios y la disponibilidad pueden cambiar en cualquier momento, por lo que conviene comprobar la ficha del producto antes de comprar.",
        ],
        "faq": [
            ("¿Los artículos rebajados tienen precio garantizado?",
             "No. Mostramos el precio que aparecía en el canal al publicar la oferta. Amazon puede modificarlo o retirar el descuento en cualquier momento."),
        ],
    }),
    ("chollos-amazon-telegram", "Chollos en Telegram", {
        "title": "Chollos de Amazon en Telegram | Gangas Ofertas y Chollos",
        "desc": "Recibe los chollos y ofertas de Amazon España directamente en Telegram. Canal gratuito, sin registro y con avisos al instante.",
        "h1": "Chollos en Telegram",
        "intro": "El canal de Telegram es la fuente de todo lo que publicamos: si una oferta aparece aquí, antes se ha anunciado allí.",
        "texto": [
            "Unirse es gratis y no hace falta crear ninguna cuenta. Cada oferta se publica con el nombre del producto, el precio y el enlace a Amazon España.",
            "Si prefieres consultarlo todo de una sentada, esta web recoge el mismo contenido ordenado por categoría.",
        ],
        "faq": [
            ("¿Tengo que registrarme para ver las ofertas?",
             "No. Ni en la web ni en el canal hace falta ninguna cuenta: solo entrar y mirar."),
            ("¿Cuántas ofertas se publican?",
             "Depende de lo que haya cada día. No publicamos un número fijo diario, pero las que aparecen en el canal quedan recogidas aquí."),
        ],
    }),
]

PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{base}/{slug}.html">

<meta property="og:type" content="article">
<meta property="og:site_name" content="Gangas Ofertas y Chollos">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{base}/{slug}.html">
<meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{img}">

<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/style.css">

<script type="application/ld+json">
{schema}
</script>
</head>
<body>

<header class="cabecera">
  <div class="wrap">
    <h1>{h1}</h1>
    <p>Amazon España · Actualizado desde el canal de Telegram</p>
  </div>
</header>

<main class="contenido wrap">
  <p>{intro}</p>

  <p>{parrafos}</p>

  <h2>Ofertas por categoría</h2>
  <nav class="nav" aria-label="Categorías de ofertas">
    <a href="index.html">← Inicio</a>
{enlaces}
  </nav>

  <h2>Preguntas frecuentes</h2>
{faq_html}

  <p class="enlace-telegram">
    <a class="oferta-comprar" style="display:inline-block;padding:13px 26px" href="{canal}" target="_blank" rel="noopener">Únete al canal de Telegram</a>
  </p>
</main>

<footer class="pie">
  <div class="wrap">
    <p>Gangas Ofertas y Chollos · Amazon España</p>
    <p><a href="index.html">← Volver al inicio</a> · <a href="categorias.html">Todas las categorías</a></p>
    <p style="font-size:11px">Este sitio utiliza enlaces de afiliado de Amazon. Al comprar a través de nuestros enlaces podemos recibir una pequeña comisión sin coste adicional para ti.</p>
  </div>
</footer>

</body>
</html>
"""

import html as _html
import json
import re as _re


def construir_schema(faq):
    """JSON-LD de la FAQ. Se limpia el HTML de las respuestas: schema.org
    espera texto plano, no etiquetas."""
    grafo = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": _html.escape(p),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": _re.sub(r"<[^>]+>", "", r).strip(),
                },
            }
            for p, r in faq
        ],
    }
    return json.dumps(grafo, ensure_ascii=False, indent=2)


for slug, _unused, datos in PAGINAS:
    enlaces = "\n".join(
        f'    <a href="{href}">{icono} {nombre}</a>' for href, icono, nombre, _ in SECCIONES
    )
    parrafos = "\n\n".join(f"  <p>{p}</p>" for p in datos["texto"])
    faq_html = "\n".join(
        f'  <details>\n    <summary>{_html.escape(p)}</summary>\n    <p>{r}</p>\n  </details>'
        for p, r in datos["faq"]
    )
    schema = construir_schema(datos["faq"])

    pagina = PLANTILLA.format(
        slug=slug, title=datos["title"], desc=datos["desc"], h1=datos["h1"],
        intro=datos["intro"], parrafos=parrafos, enlaces=enlaces, faq_html=faq_html,
        schema=schema, base=BASE, img=IMG, canal=CANAL,
    )
    destino = RAIZ / f"{slug}.html"
    destino.write_text(pagina, encoding="utf-8", newline="")
    print(f"  generado {destino.name} ({len(pagina)} bytes)")
