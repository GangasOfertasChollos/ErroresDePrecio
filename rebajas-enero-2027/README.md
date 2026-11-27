# Rebajas de enero 2027 — GangasOfertas.com

Micrositio estático, sin dependencias externas, en español para España.

- **Sitio principal:** `https://gangasofertas.com/`
- **Micrositio:** `https://gangasofertas.com/rebajas-enero-2027/`
- **Canal de Telegram:** [@GangasOfertasChollos](https://t.me/GangasOfertasChollos) · historial: `https://t.me/s/GangasOfertasChollos`
- **Tema:** rebajas de enero 2027 en España (no es una copia del sitio `BlackFriday/`).

## Fechas clave 2027

- Inicio habitual / ofertas de las grandes cadenas: **viernes 1 de enero**.
- Día de Reyes: **miércoles 6 de enero**.
- Inicio tradicional por ley: **jueves 7 de enero, 00:00** (hora peninsular).
- Fin tradicional: **sábado 6 de marzo** (máximo seis semanas por ley; muchas tiendas van del 7 de enero al 6 de marzo).
- La cuenta atrás (`assets/js/main.js`) apunta a `new Date(2027, 0, 7, 0, 0, 0)`.

## Enfoque de contenido

- Protagonistas: **moda, calzado, hogar, textil de hogar y liquidación de temporada** (no tecnología, que es el fuerte del Black Friday).
- **Amazon no tiene una campaña oficial de rebajas de enero**: rebaja precios todo el año y comete errores de precio, pero no abre un evento oficial.
- Aviso de afiliado y derecho de desistimiento de **14 días** conservados en cada página y en el pie.
- Hashtag usado: `#Rebajas27`. Telegram: `@GangasOfertasChollos`. `t.me/GangasOfertasChollos` presente en cada página.

## Páginas (17 HTML)

- `index.html` — guía principal
- `fechas-rebajas-enero-2027.html` — fecha y calendario
- `ofertas-rebajas-enero-2027.html` — ofertas esperadas
- `chollos-rebajas-enero-2027.html` — gangas y chollos reales
- `como-aprovechar-rebajas.html` — método de compra
- `rebajas-por-categorias.html` — qué baja en cada categoría
- `rebajas-vs-black-friday.html` — rebajas de enero vs Black Friday
- `que-son-las-rebajas-de-enero.html` — origen y significado
- `errores-de-precio-amazon.html` — errores de precio en Amazon
- `evitar-estafas-rebajas.html` — cómo no caer en estafas
- `canal-telegram-ofertas.html` — el canal de Telegram
- `metodologia.html` — cómo detectamos y publicamos
- `sobre-nosotros.html` — quiénes somos
- `faq.html` — preguntas frecuentes
- `aviso-legal.html`, `politica-privacidad.html`, `404.html`

## Estructura

```
rebajas-enero-2027/
├── *.html                 # las 17 páginas
├── sitemap.xml
├── robots.txt
├── llms.txt
├── assets/
│   ├── css/style.css      # sin dependencias externas
│   ├── js/main.js         # menú móvil, cuenta atrás, FAQ (funciona sin JS)
│   └── img/og-rebajas-enero-2027.png  (+ logo/favicons heredados)
└── docs/
    ├── check.ps1          # validador de contenido + HTML básico + SEO + enlaces
    ├── seo-check.ps1      # auditoría SEO
    └── package-deploy.ps1 # empaquetado para Cloudflare Pages
```

## Cómo servir

Cualquier servidor estático. Por ejemplo:

```powershell
# Servir la carpeta raíz del sitio en el puerto 8080
npx http-server . -p 8080 -c-1
```

## Validación

```powershell
powershell -ExecutionPolicy Bypass -File docs\check.ps1
powershell -ExecutionPolicy Bypass -File docs\seo-check.ps1
powershell -ExecutionPolicy Bypass -File docs\package-deploy.ps1 -Zip
```

- `docs\check.ps1`: caracteres no latinos, palabras no españolas, SEO mínima (title >15, description >60, canonical, og, h1 único, enlace al canal, viewport, JSON-LD), enlaces internos rotos, balance `<section>/<div>/<details>`.
- `docs\seo-check.ps1`: `$site = 'https://gangasofertas.com/rebajas-enero-2027'`; unicidad de title/description, longitud, canonical, JSON-LD válido, enlazado interno, CTA, peso. Imagen OG: `assets\img\og-rebajas-enero-2027.png`.
- `docs\package-deploy.ps1`: destino `rebajas-enero-2027-deploy`; excluye `docs/`, `*.md`, `*.ps1`; `sitemap.xml`, `robots.txt`, `llms.txt` incluidos.

## SEO

- `lang="es"`, viewport, `<title>` único (>15), meta description única (60–170), canonical, `og:title`, `og:image` (`og-rebajas-enero-2027.png`), `twitter:card`, `robots`, `theme-color`.
- JSON-LD por página (`BreadcrumbList`, `Article`, `FAQPage`, `HowTo`, `Event`, `ItemList`, `WebSite`, `Organization`, `AboutPage`); `datePublished`/`dateModified` = `2026-11-26`.
- `sitemap.xml` (prefijo `https://gangasofertas.com/rebajas-enero-2027/`, `lastmod` `2026-11-26`), `robots.txt` (`Sitemap`, `Disallow: /docs/`), `llms.txt`.

## Notas

- `docs/`, `README.md`, `*.ps1` no se despliegan.
- El sitio `BlackFriday/` original no se toca; este micrositio es independiente.
- No hay cookies de seguimiento ni formularios; no se recopilan datos personales.
