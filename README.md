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
index.html             Portada
<slug>.html            Páginas de catálogo, una por categoría
BlackFriday/           Sección Black Friday 2026 (17 páginas, CSS y assets propios)
generar_*.py           Generadores de HTML y sitemap
tests/                 Pruebas del bot, del front y del sitio
CNAME                  Dominio personalizado de GitHub Pages: gangasofertas.com
```

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

La miniatura se obtiene con *link unfurling*, el mismo mecanismo que usan
Facebook o WhatsApp al pegar un enlace: se pide la página pública del mensaje
(`https://t.me/<canal>/<id>`) y se lee su etiqueta `og:image`. Se elige esa vía
porque es la única que funciona:

| Vía | Resultado |
|---|---|
| `og:image` de `t.me/canal/ID` | **Sí.** ~0,8 s, sin CAPTCHA, imagen real |
| `og:image` de la ficha de `amazon.es` | No: devuelve una página de CAPTCHA a cualquier cliente automatizado |
| Deducir la URL de la imagen del ASIN | No: el nombre del fichero no es derivable (devuelve un GIF de 1×1) |

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
