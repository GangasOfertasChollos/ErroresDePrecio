"""Genera las 7 paginas de catalogo a partir de una unica definicion.

Antes cada HTML repetia ~20 lineas de CSS y ~55 de JS identicas; cualquier
correccion habia que replicarla 7 veces. Ahora comparten assets/style.css y
assets/app.js, y este script es la unica fuente que hay que editar.

El menu, el icono de Telegram y el pie se toman de plantilla_comun.py para que
regenerar las paginas no deshaga el trabajo de maquetacion.
"""
from pathlib import Path

from plantilla_comun import ICONO_TG, NAV, PIE, nav_html

RAIZ = Path(__file__).resolve().parent

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

<title>{h1} en Amazon España | GangasOfertas.com</title>
<meta name="description" content="{descripcion}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="https://gangasofertas.com/{slug}.html">

<meta property="og:type" content="website">
<meta property="og:site_name" content="GangasOfertas.com">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{h1} | GangasOfertas.com">
<meta property="og:description" content="{descripcion}">
<meta property="og:url" content="https://gangasofertas.com/{slug}.html">
<meta property="og:image" content="https://gangasofertas.com/assets/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{h1} | GangasOfertas.com">
<meta name="twitter:description" content="{descripcion}">
<meta name="twitter:image" content="https://gangasofertas.com/assets/og-image.png">

<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/style.css">
<meta name="google-site-verification" content="E4_nuunpXWLlV4jpR5qmBPKLhB2kFV_MTM6N_J9xRSc">
<meta name="google-site-verification" content="uzqlh-QjEzCDqWUTkJpgkqlJsHSt0Xjbh82vV-orJQ8">
</head>
<body data-feed="{slug}">
{icono}
<header class="cabecera">
  <div class="wrap">
    <h1>{icono_cat} {h1}</h1>
    <p>{subtitulo}</p>
    <nav class="nav" aria-label="Navegación principal">
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

{pie}

<script src="assets/app.js" defer></script>
</body>
</html>
"""

for slug, h1, subtitulo, descripcion, icono_cat in CATEGORIAS:
    html = PLANTILLA.format(
        slug=slug, h1=h1, subtitulo=subtitulo, descripcion=descripcion,
        icono_cat=icono_cat, nav=nav_html(f"{slug}.html"),
        icono=ICONO_TG.format(prefijo="", canal="https://t.me/GangasOfertasChollos"),
        pie=PIE,
    )
    destino = RAIZ / f"{slug}.html"
    # La raiz del repositorio usa CRLF de forma consistente (ver .gitattributes
    # y el resto de HTML); con newline="" se emitiria LF y quedaria mezclado.
    destino.write_text(html, encoding="utf-8", newline="\r\n")
    print(f"  generado {destino.name} ({len(html)} bytes)")
