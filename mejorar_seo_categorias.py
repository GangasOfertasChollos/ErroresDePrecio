#!/usr/bin/env python3
"""
Script para mejorar el SEO de las páginas de categorías.

Añade:
- Meta keywords específicos
- Schema.org JSON-LD estructurado
- Mejoras en meta descriptions
- Meta tags adicionales (autor, idioma, tema, formato, compatibilidad)
- Meta tags de robots más específicos
- Meta tags de verificación (Google, Bing, Yandex)
"""
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO_PATH = Path(__file__).resolve().parent

# Datos SEO específicos para cada categoría
SEO_DATA = {
    'ropa-y-calzado.html': {
        'title': 'Ropa y calzado en Amazon España | GangasOfertas.com',
        'description': 'Chollos y ofertas de ropa y calzado en Amazon España: zapatillas, camisetas, chaquetas, vaqueros y complementos al mejor precio. Actualizado desde Telegram.',
        'keywords': 'ropa amazon, calzado amazon, zapatillas amazon, camisetas amazon, chaquetas amazon, vaqueros amazon, moda amazon, ofertas ropa, chollos ropa, gangas ropa, descuentos ropa, amazon españa',
        'schema_type': 'ClothingStore',
        'schema_name': 'Ropa y calzado en Amazon España',
    },
    'moviles-electronica.html': {
        'title': 'Móviles y electrónica en Amazon España | GangasOfertas.com',
        'description': 'Chollos y ofertas de móviles y electrónica en Amazon España: smartphones, portátiles, auriculares, tablets y accesorios al mejor precio. Actualizado desde Telegram.',
        'keywords': 'moviles amazon, electronica amazon, smartphones amazon, portatiles amazon, auriculares amazon, tablets amazon, gadgets amazon, ofertas moviles, chollos moviles, gangas electronica, descuentos electronica, amazon españa',
        'schema_type': 'ElectronicsStore',
        'schema_name': 'Móviles y electrónica en Amazon España',
    },
    'gaming-consolas.html': {
        'title': 'Gaming y consolas en Amazon España | GangasOfertas.com',
        'description': 'Chollos y ofertas de gaming y consolas en Amazon España: PS5, Nintendo Switch, Xbox, mandos, videojuegos y accesorios al mejor precio. Actualizado desde Telegram.',
        'keywords': 'gaming amazon, consolas amazon, ps5 amazon, nintendo switch amazon, xbox amazon, mandos amazon, videojuegos amazon, ofertas gaming, chollos gaming, gangas consolas, descuentos videojuegos, amazon españa',
        'schema_type': 'VideoGameStore',
        'schema_name': 'Gaming y consolas en Amazon España',
    },
    'higiene-cuidado-personal.html': {
        'title': 'Higiene y cuidado personal en Amazon España | GangasOfertas.com',
        'description': 'Chollos y ofertas de higiene y cuidado personal en Amazon España: cosmética, cuidado facial, champús, belleza y productos de higiene al mejor precio. Actualizado desde Telegram.',
        'keywords': 'higiene amazon, cuidado personal amazon, cosmetica amazon, cuidado facial amazon, champus amazon, belleza amazon, ofertas higiene, chollos higiene, gangas cosmetica, descuentos belleza, amazon españa',
        'schema_type': 'BeautyStore',
        'schema_name': 'Higiene y cuidado personal en Amazon España',
    },
    'juguetes-infantil.html': {
        'title': 'Juguetes e infantil en Amazon España | GangasOfertas.com',
        'description': 'Chollos y ofertas de juguetes e infantil en Amazon España: LEGO, muñecas, juegos de mesa, puericultura y juguetes educativos al mejor precio. Actualizado desde Telegram.',
        'keywords': 'juguetes amazon, infantil amazon, lego amazon, muñecas amazon, juegos de mesa amazon, puericultura amazon, juguetes educativos amazon, ofertas juguetes, chollos juguetes, gangas infantil, descuentos juguetes, amazon españa',
        'schema_type': 'ToyStore',
        'schema_name': 'Juguetes e infantil en Amazon España',
    },
    'papeleria-oficina.html': {
        'title': 'Papelería y oficina en Amazon España | GangasOfertas.com',
        'description': 'Chollos y ofertas de papelería y oficina en Amazon España: material escolar, sillas de oficina, escritura, cuadernos y organizadores al mejor precio. Actualizado desde Telegram.',
        'keywords': 'papeleria amazon, oficina amazon, material escolar amazon, sillas oficina amazon, escritura amazon, cuadernos amazon, organizadores amazon, ofertas papeleria, chollos papeleria, gangas oficina, descuentos material escolar, amazon españa',
        'schema_type': 'OfficeEquipmentStore',
        'schema_name': 'Papelería y oficina en Amazon España',
    },
}

# Meta tags comunes adicionales
EXTRA_META = '''
<!-- Meta tags adicionales para SEO -->
<meta name="author" content="GangasOfertas.com">
<meta name="language" content="Spanish">
<meta name="theme-color" content="#ff9900">
<meta name="format-detection" content="telephone=no">
<meta name="X-UA-Compatible" content="IE=edge">
<meta name="cache-control" content="public, max-age=31536000">
<meta name="expires" content="2027-12-31">
<meta name="pragma" content="cache">
<meta name="content-language" content="es-ES">
<meta name="designer" content="GangasOfertas.com">
<meta name="distribution" content="global">
<meta name="rating" content="general">
<meta name="target" content="all">
<meta name="googlebot" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="bingbot" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="yandex" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
'''

def generar_schema_ld(seo_data, url_canonica):
    """Genera el JSON-LD de Schema.org para una categoría."""
    return f'''
<!-- Schema.org JSON-LD -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "{seo_data['schema_name']}",
  "description": "{seo_data['description']}",
  "url": "{url_canonica}",
  "inLanguage": "es-ES",
  "isPartOf": {{
    "@type": "WebSite",
    "name": "GangasOfertas.com",
    "url": "https://gangasofertas.com/"
  }},
  "about": {{
    "@type": "{seo_data['schema_type']}",
    "name": "{seo_data['schema_name']}",
    "description": "{seo_data['description']}",
    "url": "{url_canonica}",
    "parentOrganization": {{
      "@type": "Organization",
      "name": "GangasOfertas.com",
      "url": "https://gangasofertas.com/"
    }}
  }},
  "mainEntity": {{
    "@type": "ItemList",
    "name": "{seo_data['schema_name']}",
    "description": "{seo_data['description']}",
    "url": "{url_canonica}",
    "numberOfItems": 30,
    "itemListOrder": "https://schema.org/ItemListOrderDescending"
  }}
}}
</script>
'''

def mejorar_seo_pagina(pagina, seo_data):
    """Mejora el SEO de una página de categoría."""
    ruta = REPO_PATH / pagina
    if not ruta.exists():
        print(f"  [SKIP] {pagina} no existe")
        return False
    
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    url_canonica = f"https://gangasofertas.com/{pagina}"
    
    # 1. Actualizar title
    contenido = re.sub(
        r'<title>.*?</title>',
        f'<title>{seo_data["title"]}</title>',
        contenido
    )
    
    # 2. Actualizar description
    contenido = re.sub(
        r'<meta name="description" content="[^"]*"',
        f'<meta name="description" content="{seo_data["description"]}"',
        contenido
    )
    
    # 3. Añadir keywords si no existen
    if '<meta name="keywords"' not in contenido:
        contenido = contenido.replace(
            '<meta name="description"',
            f'<meta name="keywords" content="{seo_data["keywords"]}">\n<meta name="description"'
        )
    
    # 4. Actualizar og:title
    contenido = re.sub(
        r'<meta property="og:title" content="[^"]*"',
        f'<meta property="og:title" content="{seo_data["title"]}"',
        contenido
    )
    
    # 5. Actualizar og:description
    contenido = re.sub(
        r'<meta property="og:description" content="[^"]*"',
        f'<meta property="og:description" content="{seo_data["description"]}"',
        contenido
    )
    
    # 6. Actualizar twitter:title
    contenido = re.sub(
        r'<meta name="twitter:title" content="[^"]*"',
        f'<meta name="twitter:title" content="{seo_data["title"]}"',
        contenido
    )
    
    # 7. Actualizar twitter:description
    contenido = re.sub(
        r'<meta name="twitter:description" content="[^"]*"',
        f'<meta name="twitter:description" content="{seo_data["description"]}"',
        contenido
    )
    
    # 8. Añadir meta tags adicionales antes de </head>
    if 'Meta tags adicionales para SEO' not in contenido:
        contenido = contenido.replace('</head>', EXTRA_META + '\n</head>')
    
    # 9. Añadir Schema.org JSON-LD antes de </head>
    if 'Schema.org JSON-LD' not in contenido:
        schema = generar_schema_ld(seo_data, url_canonica)
        contenido = contenido.replace('</head>', schema + '\n</head>')
    
    # 10. Guardar cambios
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print(f"  [OK] {pagina} SEO mejorado")
    return True

def main():
    print("Mejorando SEO de las paginas de categorias...")
    for pagina, seo_data in SEO_DATA.items():
        mejorar_seo_pagina(pagina, seo_data)
    print("Listo.")

if __name__ == '__main__':
    main()
