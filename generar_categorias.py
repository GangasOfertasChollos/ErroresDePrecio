"""Genera las 7 paginas de catalogo a partir de una unica definicion.

Antes cada HTML repetia ~20 lineas de CSS y ~55 de JS identicas; cualquier
correccion habia que replicarla 7 veces. Ahora comparten assets/style.css y
assets/app.js, y este script es la unica fuente que hay que editar.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

NAV = [
    ("ropa-y-calzado.html", "Ropa y calzado"),
    ("moviles-electronica.html", "Móviles y electrónica"),
    ("gaming-consolas.html", "Gaming y consolas"),
    ("higiene-cuidado-personal.html", "Higiene y cuidado personal"),
    ("juguetes-infantil.html", "Juguetes e infantil"),
    ("papeleria-oficina.html", "Papelería y oficina"),
    ("general.html", "Todas"),
]

# slug, h1, subtitulo, descripcion SEO, icono
CATEGORIAS = [
    ("ropa-y-calzado", "Ropa y calzado", "Moda, zapatillas, abrigos y complementos",
     "Chollos y ofertas de ropa y calzado en Amazon España: zapatillas, camisetas, chaquetas y complementos al mejor precio.", "👔"),
    ("moviles-electronica", "Móviles y electrónica", "Smartphones, informática, audio y gadgets",
     "Chollos y ofertas de móviles y electrónica en Amazon España: smartphones, portátiles, auriculares y accesorios al mejor precio.", "📱"),
    ("gaming-consolas", "Gaming y consolas", "PS5, Nintendo Switch, mandos y videojuegos",
     "Chollos y ofertas de gaming en Amazon España: PS5, Nintendo Switch, Xbox, mandos y videojuegos al mejor precio.", "🎮"),
    ("higiene-cuidado-personal", "Higiene y cuidado personal", "Cosmética, cuidado facial, champús y belleza",
     "Chollos y ofertas de higiene y cuidado personal en Amazon España: champús, perfumes, cosmética y afeitadoras al mejor precio.", "🧴"),
    ("juguetes-infantil", "Juguetes e infantil", "LEGO, muñecas, juegos de mesa y puericultura",
     "Chollos y ofertas de juguetes e infantil en Amazon España: LEGO, muñecas, juegos de mesa y puericultura al mejor precio.", "🧸"),
    ("papeleria-oficina", "Papelería y oficina", "Material escolar, sillas de oficina y escritura",
     "Chollos y ofertas de papelería y oficina en Amazon España: cuadernos, bolígrafos, grapadoras y sillas de oficina al mejor precio.", "📚"),
    ("general", "Todas las ofertas", "El feed completo con las mejores gangas de Amazon España",
     "Todos los chollos, ofertas y errores de precio de Amazon España en un solo feed: ropa, tecnología, gaming, juguetes y más.", "⚡"),
]

PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{h1} en Amazon España | Gangas Ofertas y Chollos</title>
<meta name="description" content="{descripcion}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="https://gangasofertaschollos.github.io/ErroresDePrecio/{slug}.html">

<meta property="og:type" content="website">
<meta property="og:site_name" content="Gangas Ofertas y Chollos">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{h1} | Gangas Ofertas y Chollos">
<meta property="og:description" content="{descripcion}">
<meta property="og:url" content="https://gangasofertaschollos.github.io/ErroresDePrecio/{slug}.html">
<meta property="og:image" content="https://gangasofertaschollos.github.io/ErroresDePrecio/assets/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{h1} | Gangas Ofertas y Chollos">
<meta name="twitter:description" content="{descripcion}">
<meta name="twitter:image" content="https://gangasofertaschollos.github.io/ErroresDePrecio/assets/og-image.png">

<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/style.css">
<meta name="google-site-verification" content="E4_nuunpXWLlV4jpR5qmBPKLhB2kFV_MTM6N_J9xRSc">
</head>
<body data-feed="{slug}">

<header class="cabecera">
  <div class="wrap">
    <h1>{icono} {h1}</h1>
    <p>{subtitulo}</p>
    <nav class="nav" aria-label="Categorías de ofertas">
{nav}
    </nav>
  </div>
</header>

<main class="contenido wrap">
  <div id="estado" class="estado" role="status">Cargando ofertas…</div>
  <section id="ofertas" class="rejilla" aria-live="polite"></section>
  <p class="enlace-telegram">
    ¿Quieres más? <a href="https://t.me/GangasOfertasChollos" target="_blank" rel="noopener">Únete al canal de Telegram</a>
  </p>
</main>

<footer class="pie">
  <div class="wrap">
    <p>Gangas Ofertas y Chollos · Amazon España · Ofertas publicadas desde Telegram</p>
    <p><a href="index.html">← Volver al inicio</a> · <a href="categorias.html">Todas las categorías</a></p>
    <p style="font-size:11px">Este sitio utiliza enlaces de afiliado de Amazon. Al comprar a través de nuestros enlaces podemos recibir una pequeña comisión sin coste adicional para ti.</p>
  </div>
</footer>

<script src="assets/app.js" defer></script>
</body>
</html>
"""

for slug, h1, subtitulo, descripcion, icono in CATEGORIAS:
    items = "\n".join(
        f'      <a href="{href}"{" aria-current=\"page\"" if href == slug + ".html" else ""}>{label}</a>'
        for href, label in NAV
    )
    html = PLANTILLA.format(slug=slug, h1=h1, subtitulo=subtitulo,
                            descripcion=descripcion, icono=icono, nav=items)
    destino = RAIZ / f"{slug}.html"
    destino.write_text(html, encoding="utf-8", newline="")
    print(f"  generado {destino.name} ({len(html)} bytes)")
