# GangasOfertas.com

Web de ofertas Amazon España y bot de Telegram. Se publica en
**https://gangasofertas.com** (GitHub Pages detrás de Cloudflare).

Un bot escucha el canal de Telegram, extrae el título, el precio y el enlace de
cada oferta, la clasifica por categoría y la guarda en `data/*.json`. La web lee
esos JSON y los muestra en un catálogo por categorías.

> **Qué es y qué no es este proyecto.** No rastrea Amazon ni monitoriza sus
> precios. Recopila las ofertas que se publican en el canal de Telegram; Amazon
> es quien decide en cada momento si ese precio sigue disponible.

## Estructura

```
bot.py                 Bot de Telethon
categorias.json        Diccionario de palabras clave por categoría
data/*.json            Ofertas (generados por el bot)
assets/style.css       Estilos compartidos por todas las páginas
assets/app.js          Carga y render del catálogo (+ JSON-LD dinámico)
assets/icono-tg.css    Componentes comunes a las dos paletas (icono, reduced-motion)
assets/icono-tg.jpg    Icono del canal (esquina superior derecha)
index.html             Portada
<slug>.html            Páginas de catálogo, una por categoría
BlackFriday/           Sección Black Friday 2026 (17 páginas, CSS y assets propios)
plantilla_comun.py     Marcado compartido: menú, icono y pie
generar_*.py           Generadores de HTML y sitemap
tests/                 Pruebas del bot, del front y del sitio
CNAME                  Dominio personalizado de GitHub Pages: gangasofertas.com
.gitattributes         CRLF en la raíz, LF en BlackFriday/
```

## Diseño

Dos hojas de estilo, las dos **de fondo claro**:

| | Fichero | Acento |
|---|---|---|
| Sitio principal | `assets/style.css` | naranja Amazon (`--naranja-texto` para texto) |
| Sección Black Friday | `BlackFriday/assets/css/style.css` | negro (`--accent`) |

El negro se usa como elemento de marca —barra superior, botones, barra de
marca— sobre fondo blanco. Los colores de marca que no llegan a 4.5:1 sobre
blanco (como el naranja `#ff9900`, que da 2.1:1) están **restringidos a bordes
y rellenos**; para texto se usa el tono oscuro equivalente (`--naranja-texto`).

Todo el color pasa por variables CSS. Si quieres cambiar la paleta, edita el
bloque `:root` de cada hoja y no toques las reglas.

Lo que **no** depende de la paleta vive en `assets/icono-tg.css`, que las dos
hojas cargan: así el icono del canal y la regla de `prefers-reduced-motion`
tienen una sola definición en lugar de una por hoja.

El icono del canal (`assets/icono-tg.jpg`) se inserta **dentro del div que
contiene el `<h1>`** de cada página, no flotando sobre el viewport. Hay cuatro
estructuras de cabecera distintas y todas están contempladas en el CSS:

| Página | Contenedor |
|---|---|
| Portada | `<header class="hero"><div>` |
| Catálogos, SEO, ofertas en vivo | `<header class="cabecera"><div class="wrap">` |
| Sección Black Friday | `<header class="site-header"><div class="wrap nav">` |
| 404 | `<main class="error404">` |

Esos contenedores son `position: relative`, así que el icono se coloca con
`position: absolute` en su esquina superior derecha. Si añades una cabecera
nueva, añade su selector a esa lista en `assets/icono-tg.css` o el icono
saldrá flotando sobre el contenido.

`plantilla_comun.py` es la única fuente del menú, del icono y del pie. Los
tres generadores la importan, de modo que regenerar las páginas no deshace los
cambios de maquetación y los menús no divergen entre sí.

> `404.html` usa **rutas absolutas** a propósito: GitHub Pages lo sirve a
> cualquier profundidad (por ejemplo `/BlackFriday/no-existe.html`), donde una
> ruta relativa como `general.html` apuntaría a `/BlackFriday/general.html` y
> no existiría. Los validadores no lo detectan porque resuelven siempre contra
> la raíz del repositorio.

La sección Black Friday tiene su propia hoja porque su diseño original era
oscuro; se migró a claro cambiando `--bg` a `#ffffff` y `--accent` a negro, y
ajustando los ~29 colores que estaban fijados en las reglas.

## Dominio

`CNAME` fija `gangasofertas.com` como dominio de GitHub Pages, así que **todos
los canonical, `og:url` y el `sitemap.xml` deben apuntar a
`https://gangasofertas.com/`**. La URL de GitHub (`*.github.io`) queda
despublicada: si alguna vez se vuelve a subir, Google verá dos versiones del
mismo contenido.

El host canónico es el **apex sin `www`**. `www.gangasofertas.com` se redirige al
apex con una regla de Cloudflare, porque GitHub Pages solo tiene verificado el
apex y proxiar `www` devolvía un error 522.

## Puesta en marcha

```bash
pip install -r requirements.txt
cp .env.example .env      # rellena API_ID, API_HASH y TELEGRAM_CHANNEL
python bot.py
```

La primera vez Telegram pedirá un código de confirmación: el bot lo avisa por
consola y por `bot.log`. Si ejecutas el bot como servicio y se cuelga esperando
ese código, borra `sesion_json_bot.session` y autorízalo en una terminal
interactiva.

### El catálogo se reconstruye en cada arranque

Al arrancar, el bot hace tres cosas, en este orden:

1. **Lee** los últimos `BACKFILL_LIMIT` (100) mensajes del canal.
2. **Borra todas las ofertas y todas las imágenes**: los JSON de `data/` se
   vacían y `data/images/` se elimina entero.
3. **Vuelve a publicar** esas ofertas en los JSON, ya saneadas, y las sube a
   git.

Lo publicado es por tanto siempre el estado actual del canal: no se acumulan
ofertas caducadas ni retoques a mano, y un JSON corrupto se regenera solo. Lo
mismo pasa al **reconectar** tras una caída de conexión, porque durante el corte
las ofertas se pierden y `events.NewMessage` solo dispara con lo que llega
después.

Detalles que conviene tener presentes:

- **El borrado va después de leer el historial, nunca antes.** Si Telegram
  falla, el canal está vacío o no se puede acceder, se conserva el catálogo
  anterior en lugar de dejar la web vacía y sin repuesto. Hay pruebas de esto
  en `tests/test_flujo.py`.
- **Mirar 100 mensajes no es publicar 100 ofertas.** `MAX_OFERTAS` (30) sigue
  mandando: cada JSON guarda como máximo 30 ofertas, las más recientes. Para
  publicar más, sube `MAX_OFERTAS`.
- **Se descarta lo que no se puede publicar.** Una oferta sin enlace de Amazon,
  sin título o sin precio no llega a los JSON: serían tarjetas rotas o sin
  información. Cada descarte queda anotado en el log con el motivo.

Con `REINICIAR_CATALOGO=0` se conserva el comportamiento anterior: los JSON se
van llenando de forma incremental y el backfill solo rellena huecos.

## Publicación

La web se sirve desde GitHub Pages, así que los cambios en `data/` tienen que
llegar al repositorio. Hay dos formas:

**Automática (recomendada).** Actívala en `.env`:

```bash
AUTO_PUBLICAR=1
```

El bot hace `git add data/`, `commit` y `push` por su cuenta, agrupando las
subidas cada `PUBLICAR_CADA_SEGUNDOS` (60 por defecto) para no crear un commit
por oferta. Necesita git instalado, el remoto configurado y credenciales de
push (por ejemplo un token o una clave SSH).

**Manual.** Si prefieres no dar acceso al bot:

```bash
git add data/
git commit -m "Actualizar ofertas"
git push
```

## Regenerar el HTML

Las páginas de catálogo y las páginas SEO se generan con scripts para que
todas compartan estructura y estilos. Si cambias una sección, edita el
generador y vuelve a lanzarlo:

```bash
python generar_categorias.py    # 7 páginas de catálogo
python generar_seo.py           # 4 páginas SEO
python generar_sitemap.py       # sitemap.xml (verifica que las URLs existen)
```

## Imágenes y formato de los mensajes

Las ofertas no guardan imágenes en disco: el campo `image` guarda una **URL**.
Por eso `data/` solo contiene los siete JSON de ofertas y ningún binario.

La miniatura se obtiene con *link unfurling*, el mismo mecanismo que usan
Facebook o WhatsApp al pegar un enlace: se pide la página pública del mensaje
(`https://t.me/<canal>/<id>`) y se lee su etiqueta `og:image`. Se elige esa vía
porque es la única que funciona:

| Vía | Resultado |
|---|---|
| `og:image` de `t.me/canal/ID` | **Sí.** ~0,8 s, sin CAPTCHA, imagen real |
| `og:image` de la ficha de `amazon.es` | No: devuelve una página de CAPTCHA a cualquier cliente automatizado |
| Deducir la URL de la imagen del ASIN | No: el nombre del fichero no es derivable (devuelve un GIF de 1×1) |

> Antes el bot bajaba cada foto a `data/images/` y guardaba la ruta local. Eso
> dejaba 35 MB de binarios en el repositorio y rutas que el navegador no puede
> resolver, así que el paso se eliminó del todo: `extraer_imagen` solo devuelve
> URLs. `limpiar_imagenes_huerfanas()` avisa si ese directorio vuelve a
> aparecer.

Las URLs obtenidas se cachean en memoria, así que el backfill no repite
peticiones. Si el bot no está en el canal no puede construir la URL pública, y
la oferta se publica sin imagen.

Los mensajes del canal tienen una estructura fija que el bot aprovecha, porque
es más fiable que buscar números sueltos:

```
🩹 VANSKIVA – Parche de silicona para cicatrices 4 cm x 1,5 m

💸 Ahora: 13,99 €
🏷️ Antes: 25,99 €
📉 Descuento: -46 %
💰 Ahorras: 12,00 €
🔗

https://www.amazon.es/dp/B0GCQX9YY4?tag=gangas054-21
```

De ahí se extraen el título, el precio de oferta (`price`), el precio original
(`old_price`), el descuento (`discount`) y el enlace. Se aceptan tanto el
enlace directo como los acortadores `amzn.to`, `amzn.eu` y `amzlink.to`.

### Los campos que van a schema.org

`description`, `brand` y `gtin` se publican tal cual como
`itemprop`/JSON-LD, así que un valor inventado es información falsa en los
resultados de Google. De ahí las reglas:

- **`gtin`** solo se rellena con un GTIN de verdad (EAN-8, UPC-A o EAN-13)
  **validado por su dígito de control**, o con un MPN que lleve letras *y*
  dígitos. Se buscan fuera de los enlaces, porque el tag de afiliado del
  propio bot (`?tag=gangas054-21`) también tiene guion y dígitos. Antes se
  aceptaba cualquier palabra de 6 a 20 caracteres, así que casi todas las
  ofertas publishaban como `gtin` la marca o un sustantivo del título
  (`"Scottex"`, `"OFERTA"`, `"Zapatillas"`).
- **`description`** descarta las líneas que solo son precios
  (`"16,91 € (antes 29,99 €)"`), las etiquetas del canal (`|#Chollos|`) y las
  llamadas a la acción de otros canales (`👉 Míralo en Ofertitas.es`). El
  precio ya vive en sus propios campos.
- **`brand`** descarta los emojis que se cuelan (`⌨️ GXTrust`) y los
  fragmentos que no son una marca (`"Alfombrilla de"`, `"Neceser"`); si no hay
  marca, el campo queda vacío y el frontend lo omite.

Cuando un dato no está, el campo va vacío. Es preferible a inventarlo.

## Comprobar los cambios

```bash
python tests/test_bot.py            # extracción, clasificación, escritura, límites
python tests/test_formato_canal.py  # formato real de los mensajes del canal
python tests/test_unfurl.py         # unfurling y caché (red simulada)
python tests/test_flujo.py          # extremo a extremo: mensaje -> JSON -> página
node tests/test_app.js              # render, escapado, whitelist de URLs, JSON-LD
python tests/validar_sitio.py       # enlaces, JSON-LD, HTML, sitemap, afirmaciones
```

Las pruebas no necesitan credenciales de Telegram ni conexión: sustituyen el
cliente y el `fetch` por dobles de prueba y trabajan sobre copias en un
directorio temporal. `data/` puede estar vacío; en ese caso `test_app.js` usa
ofertas de ejemplo.

## Configuración

Todo en `.env` (ver `.env.example`):

| Variable | Por defecto | Para qué |
|---|---|---|
| `API_ID` / `API_HASH` | — | Credenciales de Telegram (obligatorias) |
| `TELEGRAM_CHANNEL` | `@GangasOfertasChollos` | Canal que se escucha |
| `MAX_OFERTAS` | `30` | Ofertas guardadas por JSON |
| `BACKFILL_LIMIT` | `100` | Mensajes del histórico a recuperar al arrancar (`0` desactiva) |
| `REINICIAR_CATALOGO` | `1` | Borrar ofertas e imágenes al arrancar y reconstruirlas desde el canal (`0` conserva lo que haya) |
| `USAR_UNFURL` | `1` | Obtener la miniatura desde la página pública del mensaje (`0` desactiva) |
| `TIMEOUT_UNFURL` | `15` | Segundos de espera al pedir la miniatura |
| `AUTO_PUBLICAR` | `0` | Publica `data/` en git automáticamente |
| `GIT_REMOTO` / `GIT_RAMA` | `origin` / `main` | Destino del push |
| `PUBLICAR_CADA_SEGUNDOS` | `60` | Frecuencia máxima de publicación |

## Categorías

Las palabras de clasificación se editan en `categorias.json`. La búsqueda
ignora tildes y mayúsculas, y las coincidencias son por palabra completa, así
que `pantalón` y `pantalon` funcionan igual. Cuando dos categorías empatan,
gana la que aparece antes en el archivo.
