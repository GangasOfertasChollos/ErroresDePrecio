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
publicar_x.py          Publica las ofertas del catálogo en X (API interna de X)
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

## Secciones de campaña

Una sección cubre una campaña concreta. El requisito para tenerla es **ventana
de posicionamiento**: se publica con antelación suficiente para que Google
indexe y.positione antes de que la demanda llegue. Black Friday cumple eso con
holgura (del 2 de octubre al 27 de noviembre). Un evento de 48 horas no lo
cumple, aunque tenga el mismo contenido: se publica el día que ya está pasando y
no hay tiempo de posicionar contra nadie. Por eso Prime Days se retiró el 10 de
octubre de 2026, tres días después de terminar la campaña.

| | Black Friday |
|---|---|
| Campaña | 27 de noviembre de 2026 |
| Generador | `BlackFriday/` (HTML ya generado) |
| Análisis SEO | `BlackFriday/docs/SEO-STRATEGY.md` |

**Sobre las fechas.** La sección publica la fecha de su campaña y el historial,
pero **solo los datos que tienen fuente**, y la fuente se enlaza en la propia
página. Hubo una corrección por esto en la sección retirada: un borrador
afirmaba que Amazon no había anunciado la fecha de octubre de 2026, que era
cierto cuando se escribió y dejó de serlo antes de publicarse. El principio no
cambió (no inventar fechas); lo que cambió es el dato.

> La sección retirada marcaba la campaña como «en marcha» con una cuenta atrás,
> y el sitemap declaraba `daily` en sus dos URLs principales. Eso era correcto
> el 6 y el 7 de octubre y falso a partir del 8. Es el recordatorio de por qué
> una sección de campaña con fecha de caducidad es un pasivo a partir del día
> que termina.

### Tablas anchas dentro de `.prose`

La columna de texto mide 74ch. Una tabla de cuatro o cinco columnas dentro de
ella parte cada celda en tres o cuatro palabras y deja de ser legible, así que
`tabla(..., ancho_completo=True)` la saca a un `.wrap` completo. Las tablas de
dos columnas caben sin problema dentro de `.prose`.

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
- **`MAX_OFERTAS` no puede quedar por debajo de `BACKFILL_LIMIT`.** Ambos valen
  100 por defecto, así que de los 100 mensajes leídos se publican hasta 100
  ofertas. Si alguien deja `MAX_OFERTAS` por debajo, el recorte de
  `_guardar_en_archivo` tiraría ofertas que sí se han leído del canal y el
  catálogo recién reiniciado saldría incompleto solo por el límite: el bot lo
  detecta al arrancar, avisa por log y sube `MAX_OFERTAS` a `BACKFILL_LIMIT`.
- **Se descarta lo que no se puede publicar.** Una oferta sin enlace de Amazon,
  sin título o sin precio no llega a los JSON: serían tarjetas rotas o sin
  información. Cada descarte queda anotado en el log con el motivo.

### Al terminar, el bot se verifica

Al cerrar el backfill, `bot.py` comprueba por log lo que de verdad importa al
arrancar, y avisa si algo no cuadra:

```
[VERIFICACION] general.json=100 ofertas (procesadas: 100, leidas del canal: 100); por categoria -> general=100, higiene-cuidado-personal=8, ...
[VERIFICACION] general.json completo: 100/100 ofertas del canal
[VERIFICACION] Cambios publicados en origin/main. GitHub Pages tardara unos minutos en servirlos.
```

- Si `general.json` se queda corto, dice **cuántas** ofertas faltan de las leídas
  y recuerda mirar `MAX_OFERTAS`.
- Si el `git push` falla, avisa de que **la web sigue mostrando el catálogo
  anterior**, en lugar de dejar un JSON correcto en local que nadie ve.
- Si `AUTO_PUBLICAR=0`, avisa de que los JSON son correctos pero la web no se
  actualizará hasta que alguien haga `git push` a mano.

No aborta nunca: el bot sigue escuchando y recogiendo ofertas nuevas aunque el
backfill haya quedado corto.

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

## Publicar en X (Twitter)

`publicar_x.py` publica las ofertas del catálogo en X. **No usa la API de pago**
de X: habla con la API interna de X —la misma que usa la web— con las cookies
de una sesión del navegador. Por eso necesita la cookie `auth_token`, que se
copia de las DevTools.

```bash
python3 publicar_x.py                 # 4 ofertas al día, una por franja
python3 publicar_x.py --simular       # ver cómo quedarían los posts, sin publicar
python3 publicar_x.py --ahora         # publicar ya las pendientes
python3 publicar_x.py --revisar       # comprobar la sesión y los ids de operación
python3 publicar_x.py --limite 3      # publicar tres ofertas y parar
python3 publicar_x.py --verificar     # listar los últimos posts de la cuenta
```

### El horario

Por defecto el script se queda corriendo y publica una oferta en cada franja:

| Franja | Hora |
|---|---|
| Mañana | 08:00 |
| Mediodía | 12:00 |
| Tarde | 17:00 |
| Noche | 21:00 |

Las horas se interpretan en la zona `X_ZONA` (por defecto `Europe/Madrid`).
En Termux el reloj del sistema suele estar en UTC, así que conviene instalar
`tzdata` (`pkg install tzdata`) para que las 08:00 sean las 08:00 en España.

Se cambian con `X_HORAS` en el `.env` o con `--horas`:

```bash
python3 publicar_x.py --horas 09:00,13:00,18:00,21:30
```

El catálogo y el estado se releen en cada franja, así que las ofertas que
`bot.py` añada mientras el script espera entran solas. Si no hay ninguna
pendiente, esa franja se salta. Si el script arranca después de la hora de una
franja, también la salta: no publica dos seguidas para recuperarla. Con
`--limite N` se para después de N ofertas (cada una con su respuesta de enlace;
0 o vacío = sin límite).

Con `--ahora` vuelve el comportamiento anterior: publica las pendientes de
golpe, con `X_PAUSA_SEGUNDOS` de espera entre una y otra.

El proceso tiene que quedarse corriendo. En Termux se ignora `SIGHUP`, así que
cerrar la terminal no lo para; en otros sistemas puede pararlo. En un servidor,
lánzalo con `nohup` o dentro de `tmux`; en Windows, con el Programador de tareas
al iniciar sesión.

### Cómo es el post

El orden es fijo: primero el precio actual, el anterior y el descuento; luego
una pregunta aleatoria (`¿Qué te parece?`, `¿Lo vas a dejar pasar?`,
`¿Te atreves?` y unas cuantas más); después el título con la descripción; y al
final los hashtags. Un post se recorta a los 280 caracteres que cuenta X (las
URLs valen 23, los emojis valen dos). Si la descripción no cabe, se recorta
antes de quitarla; si aun así no cabe, se acorta el título.

**Los enlaces no van en el post principal: van en una respuesta al propio
post.** X resta alcance a los posts que llevan enlaces, así que el enlace de
Amazon (y el de `X_ENLACE_EXTRA`) se publica aparte, unos segundos después.
La respuesta es visible al abrir el post y el post principal queda limpio.

Para volver al comportamiento antiguo, con los enlaces dentro del post:

```bash
python3 publicar_x.py --enlace-en-post
```

o en el `.env`:

```env
X_ENLACE_RESPUESTA=0
```

`X_ENLACE_EXTRA` añade un enlace fijo a la respuesta con los enlaces (por
ejemplo, la web). Sin esa variable solo va el enlace de la oferta.
`X_PAUSA_RESPUESTA` controla los segundos entre el post y la respuesta (30 por
defecto).

> Ojo: la respuesta cuenta como otro post para el límite diario de X. Cada
> oferta gasta dos publicaciones (el post y la respuesta), no una.

### De dónde salen las ofertas

Del catálogo que ya construye `bot.py`: `data/general.json` (feed global) o
`data/<categoria>.json` con `--categoria`. El script no vuelve a rastrear
nada, ni Telegram ni Amazon: solo formatea lo que ya está scraped y lo
publica.

### La sesión

| Variable | Para qué |
|---|---|
| `X_AUTH_TOKEN` | La cookie `auth_token` de x.com. Es la credencial: trátala como una contraseña. |
| `X_CT0` | El token CSRF. Opcional: si falta, el script se lo pide a X. |
| `X_USUARIO` | El `@usuario` de la cuenta, para los enlaces y para `--verificar`. |

La cookie se saca así: abre x.com con la cuenta que publica, F12 →
Application → Cookies → `https://x.com`, y copia el valor de `auth_token`.

### No se publica dos veces la misma oferta

`estado_x.json` guarda el id de Telegram de cada oferta ya publicada junto al
id de su post. En la siguiente ejecución se las salta. Si el fichero se borra,
el script vuelve a publicar desde el principio del catálogo: para eso está
`X_SOLO_ID_MIN`, que solo deja pasar ofertas con id mayor que el que se le
indique.

### X cambia sus internos cada pocas semanas

Los identificadores de las operaciones de GraphQL caducan, y en 2025 X cambió
el frontend entero: las operaciones ya no se llaman con un id numérico sino con
ids de Relay (`wR5Z_lEibLvkew3tF9w-Sg`) y se piden a `api.x.com/graphql`. Por
eso el script **busca esos ids en el propio JavaScript de x.com** en lugar de
tenerlos escritos, los cachea una semana en `cache_x.json` y los vuelve a
buscar cuando X responde que no conoce la operación. Si alguna vez deja de
funcionar por esto, `X_QUERY_IDS` permite ponerlos a mano.

En el JavaScript de ahora cada operación se declara así:

```js
e.exports={queryId:"wR5Z_lEibLvkew3tF9w-Sg",operationName:"CreateTweet",
           operationType:"mutation",
           metadata:{featureSwitches:["..."],fieldToggles:["..."]}}
```

El script lee de ahí las tres cosas que hacen falta: el `queryId`, el nombre de
la operación y la lista de *feature flags* que esa operación pide.

### Lo que X exige hoy para publicar

Cuatro cosas, y si falta alguna la petición no sale:

1. **Cabeceras de navegador.** El gateway de la API de escritura devuelve un
   `403` sin cuerpo si la petición no lleva `sec-fetch-*`, `sec-ch-ua` y
   `x-client-transaction-id`. El script las manda todas.
2. **Cookies de sesión.** No basta con `auth_token` y `ct0`: el gateway
   espera también `twid` y `guest_id`, que X pone en la web. El script pide
   la portada de x.com al empezar y las guarda.
3. **El cuerpo según la operación.** La web de ahora manda las variables como
   un objeto normal (`tweet_text`, `media`, `semantic_annotation_ids`,
   `disallowed_reply_options`) y las banderas aparte, en los parámetros
   `features` y `fieldToggles` del cuerpo. La mutación vieja
   (`createTweetMutation`) en cambio quiere las banderas dentro de las
   variables, con el nombre largo
   `__relay_internal__pv__xclientsfeatures<nombre>relayprovider`. El script
   monta cada formato según la operación que usa.
4. **La operación correcta.** El script busca en el JavaScript de x.com las
   tres operaciones que necesita: `CreateTweet` (publicar), `UserTweets` (leer
   el perfil) y `UserByScreenName` (sacar el id numérico de la cuenta, que es
   lo que pide la operación de leer).

### Cuando X dice que la petición parece automática

Es el error `226` (*"This request looks like it might be automated"*) y es el
que más aparece. No depende del texto, ni de las cabeceras, ni de las cookies:
es X decidiendo que la petición no viene de su web. Cambia solo, con el
estado de la cuenta y el rato que hace.

Por eso el script **prueba las dos mutaciones**: la de ahora (`CreateTweet`) y
la vieja (`createTweetMutation`), que es la del camino antiguo de la API. X no
aplica las mismas reglas a las dos, así que cuando una responde con el `226`
se prueba la otra. En octubre de 2026 la vieja era la que entraba y la nueva
decía que la petición era automática.

Además el script **acuerda qué mutación es la buena**: guarda en
`estado_x.json` la que funcionó por última vez y la prueba primero la
siguiente vez, porque gastar un intento con la que no entra también se nota.

Si las dos fallan, no conviene reintentar seguido: en el `226` y en el `344`
lo que se agota es la paciencia de X con la cuenta. Publicar a mano un post
desde el navegador y esperar es lo que funciona.

### El cupo diario de la cuenta

X lleva la cuenta por separado: tweets y mensajes comparten un cupo por día.
Cuando se llena, la respuesta es el error `344` (*"You have reached your daily
limit for sending Tweets and messages"*). No es un fallo del script, así que
el script **espera y reintenta la misma oferta**: `X_ESPERA_CUOTA` (1800 s
por defecto) y `X_REINTENTOS_CUOTA` (8) marcan cada cuánto y cuántas veces.

Este cupo es mucho más bajo en cuentas nuevas o sin verificar el email y el
teléfono. Si aparece el 344 por las mañanas, la solución es verificar la
cuenta en *Configuración → Seguridad y acceso a la cuenta → Seguridad*, no
esperar.

El cupo parece ser **de los posts que hace el script**, no de los que se
escriben a mano en el navegador: el 21 de octubre de 2026 la cuenta seguía
publicando a mano sin problemas mientras la API ya estaba bloqueada.

> **Cómo estaba esto en octubre de 2026.** Durante unos días la API devolvió
> `344` (cupo diario) mientras la misma cuenta publicaba sin problema a mano
> desde el navegador, y no se encontraba la diferencia. Comparando el
> JavaScript de x.com con lo que mandaba el script se vio que el script
> usaba la mutación vieja con el cuerpo viejo, y que la web de ahora usa
> `CreateTweet` con `features` y `fieldToggles`. Con las dos mutaciones a
> prueba y el cuerpo de cada una, se publica: el 21 de octubre de 2026
> salieron los posts `2112918253248876709` y `2112926399275090143`. Al día
> siguiente el cupo de la API se llenó. Del ritmo se sabe esto: con 90 s de
> pausa entre posts, el segundo ya salía con el `226`, y con 10 min de espera
> el que respondía era el `344`.

### Las imágenes

Si la oferta tiene imagen, se sube a `upload.x.com` y se adjunta al post. Si
la subida falla, el post sale igual sin imagen: es un fallo degradado, no un
error. Se puede desactivar con `X_CON_IMAGEN=0` o `--sin-imagen`.

> Ojo: las imágenes del catálogo vienen del CDN de Telegram (`cdn4.telesco.pe`)
> y caducan. En octubre de 2026 las 100 URLs de `data/general.json` devolvían
> 404, así que los posts salían sin foto. Con `X_CON_IMAGEN=0` el script no
> pierde tiempo intentándolo.

### En Termux (Android)

El script **solo usa la biblioteca estándar de Python**: no hay `pip install`,
ni Chromium, ni root, ni navegador. En Termux:

```bash
pkg install python tzdata tmux   # si no están
cd ~/ErroresDePrecio
cp .env.example .env             # si aún no existe; rellena X_AUTH_TOKEN
python3 publicar_x.py --simular
```

Para dejarlo publicando en segundo plano:

```bash
termux-wake-lock
tmux new -s x
python3 publicar_x.py
# Ctrl+B, luego D: sales de tmux sin parar el script
```

Sin tmux, con `nohup`:

```bash
termux-wake-lock
nohup python3 publicar_x.py >> salida_x.log 2>&1 &
```

Para pararlo:

```bash
tmux kill-session -t x     # si se lanzó con tmux
pkill -f publicar_x.py     # si se lanzó con nohup
termux-wake-unlock
```

El script ignora `SIGHUP`, así que cerrar la terminal no lo para. Se para con
Ctrl+C, `kill <pid>` o `pkill`. Android puede matar procesos en segundo plano:
`termux-wake-lock` y quitar Termux de la optimización de batería reducen el
riesgo. Las horas se leen en `X_ZONA` (por defecto `Europe/Madrid`), no en la
hora del sistema: así las 08:00 son las 08:00 en España aunque Termux esté en
UTC.

Cada ejecución de `--revisar` o de publicación puede descargar el JavaScript
de x.com para buscar los ids de las operaciones: son unos 6 segundos y un
par de megabytes, y se cachean una semana. En una conexión de móvil, mejor
tener la cache ya hecha.

> **Nota sobre las condiciones de X.** Publicar por la API interna va contra
> los términos de servicio de X, que prohíben el acceso automatizado a su web
> sin permiso. Con una cuenta propia y un volumen bajo el riesgo es que te
> limiten o suspendan la cuenta; con la API oficial de pago no hay ese
> problema, pero cuesta unos 200 €/mes.

## Regenerar el HTML

Las páginas de catálogo y las guías se generan con scripts para que todas
compartan estructura y estilos. Si cambias una sección, edita el generador y
vuelve a lanzarlo, **en este orden**:

```bash
python generar_categorias.py    # 7 páginas de catálogo
python generar_guias.py         # guias.html + 6 artículos
python generar_sitemap.py       # sitemap.xml (verifica que las URLs existen)
```

> Los generadores se ejecutan siempre en ese orden y en una sola pasada.
> `generar_categorias.py` es la fuente de las 7 páginas de catálogo: si algo
> las modifica a mano, se pierde al regenerarlas. Por eso las páginas se
> regeneran, no se parchean.

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

`description`, `brand`, `gtin` y `mpn` se publican tal cual como
`itemprop`/JSON-LD, así que un valor inventado es información falsa en los
resultados de Google. De ahí las reglas:

- **`gtin`** solo se rellena con un GTIN de verdad (EAN-8, UPC-A o EAN-13)
  **validado por su dígito de control**. Los hashtags se quitan antes de
  buscar, para que un `#12345678` no se cuele.
- **`mpn`** (código de pieza) va en su **propia** propiedad, no dentro de
  `gtin`: un MPN como `RLC-810A` no es un código de barras. Antes el fallback
  a MPN estaba dentro de `gtin` y **ninguno de los 28 valores que había en
  `data/` era un GTIN**: todos eran hashtags (`Blackfriday26`) o códigos de
  pieza (`HC5880`, `6-Cores`), y se publicaban como `itemprop="gtin"`.
  Se busca fuera de los enlaces, porque el tag de afiliado del propio bot
  (`?tag=gangas054-21`) también tiene guion y dígitos, y también fuera de los
  hashtags.
- **`description`** descarta las líneas que solo son precios
  (`"16,91 € (antes 29,99 €)"`), las etiquetas del canal (`|#Chollos|`, las
  internas como `PRECIO OFERTA`), los enlaces en markdown con la CTA de otro
  bot (`[📉 Miss Avisos...](https://t.me/MissAvisosbot?start=...)`, que se borran
  enteros, con su texto y su URL) y las llamadas a la acción de otros canales
  (`👉 Míralo en Ofertitas.es`). El precio ya vive en sus propios campos.
- **`brand`** descarta los emojis que se cuelan (`⌨️ GXTrust`) y los
  fragmentos que no son una marca (`"Alfombrilla de"`, `"Neceser"`); si no hay
  marca, el campo queda vacío y el frontend lo omite. Tampoco se publica
  `OFERTA AMAZON`, que es el marcador de posición del bot, no una marca.

### El título nunca es el marcador de posición

Cuando un mensaje del canal no trae un título real, `extraer_titulo` devuelve
`Oferta Amazon` y la oferta se **descarta**. La comparación es
*case-insensitive* porque el canal lo escribe en mayúsculas: con la comparación
exacta, 22 ofertas se publicaban con `title` y `brand` = `"OFERTA AMAZON"`
(14 de 98 en `general.json`, y 6 de 12 —la mitad— en `moviles-electronica.json`).

Cuando un dato no está, el campo va vacío. Es preferible a inventarlo.

## Comprobar los cambios

```bash
python tests/test_bot.py            # extracción, clasificación, escritura, límites
python tests/test_formato_canal.py  # formato real de los mensajes del canal
python tests/test_unfurl.py         # unfurling y caché (red simulada)
python tests/test_flujo.py          # extremo a extremo: mensaje -> JSON -> página
node tests/test_app.js              # render, escapado, whitelist de URLs, JSON-LD
python tests/validar_sitio.py       # enlaces, JSON-LD, HTML, sitemap, afirmaciones
python tests/auditar_seo.py         # titles, descriptions, H1, schema, enlazado, thin
python tests/verificar_301.py       # enlaces rotos + genera reglas.txt
python tests/verificar_iconos.py    # los <link rel=icon> resuelven y existen
python tests/validar_contenido.py   # volumen y limpieza del copy de cada categoría
python tests/validar_orden.py       # orden ofertas→texto, clases y JSON-LD
python tests/test_publicar_html.py  # el bot regenera y sube el HTML correcto
```

`auditar_seo.py` barre las 39 páginas y comprueba lo transversal que los otros
validadores no miran: unicidad y longitud de `<title>` y `description`, un solo
H1, canonical que apunte al dominio, `og:` completos, presencia de JSON-LD,
y el grafo de enlaces internos (entrantes y salientes) para detectar páginas
huérfanas. **No falla el build: informa**, porque casi todo lo que reporta es
una decisión de contenido y no un error.

> Solo recorre `*.html` de la raíz y `BlackFriday/*.html`. Cualquier sección
> nueva necesita su equivalente, como ocurrió con Prime Days.

`validar_servido.py` comprueba lo que un crawler recibe de verdad por HTTP, no lo
que hay en disco. Acepta un dominio como argumento:

```bash
python tests/validar_servido.py                          # contra gangasofertas.com
python tests/validar_servido.py http://localhost:8124     # contra un servidor local
```

Contra el sitio desplegado añade dos comprobaciones que en local no tienen
sentido: que las URLs del sitemap responden de verdad (una URL que solo
existe en el repositorio no la encuentra Google) y que el dominio y sus
variantes `www` / `http` resuelven a la misma canónica. Reintenta cada
petición tres veces, porque sin eso un corte de red al leer `general.html`
(~240 KB) se lee como un sitio caído.

`test_publicar_html.py` comprueba que el bot sube el HTML regenerado y que la
lista de páginas no toca `BlackFriday/`.

```bash
python tests/verificar_301.py   # enlaces rotos + genera reglas.txt
```

`verificar_301.py` resuelve cada `href` contra el directorio del fichero que lo
contiene y comprueba que el destino existe en disco. Hay dos motivos por los
que el chequeo tiene que ser así:

- **Un `href="errores-de-precio-amazon.html"` dentro de `BlackFriday/` no es el
  mismo enlace que en la raíz.** Resuelto correctamente apunta a
  `BlackFriday/errores-de-precio-amazon.html`, que es una página distinta y
  sigue viva. Comparar solo el basename daba 60 falsos positivos.
- Es el validador que detecta lo que rompe un borrado masivo de páginas, que es
  justo lo que pasó el 10 de octubre de 2026.

Además **genera `reglas.txt`** con los 301 que hay que crear en Cloudflare:
GitHub Pages no sirve `.htaccess`, así que las redirecciones no se pueden
declarar en el repositorio. Ese fichero se regenera, no se edita a mano.

## Iconos de la página

`generar_favicon.ps1` genera los PNG de `icono.jpg` y enlaza el juego completo
en las 35 páginas:

```bash
powershell -ExecutionPolicy Bypass -File generar_favicon.ps1              # genera y enlaza
powershell -ExecutionPolicy Bypass -File generar_favicon.ps1 -SoloGenerar  # solo genera
```

| Fichero | Tamaño | Para qué |
|---|---|---|
| `favicon-16x16.png` | 16 | pestaña, navegadores antiguos |
| `favicon-32x32.png` | 32 | pestaña en escritorio y Chrome |
| `favicon-48x48.png` | 48 | Windows |
| `icon-192.png` | 192 | instalación de PWA |
| `apple-touch-icon.png` | 180 | iOS, icono de inicio |
| `favicon.svg` | vector | red de seguridad para navegadores con SVG |

El bloque vive en `plantilla_comun.py` como constante `ICONOS`, así que los tres
generadores emiten lo mismo. `prefijo` permite resolver desde `BlackFriday/`,
donde hace falta `../assets/`.

Tres cosas que costaron un rato y no volver a tropezar:

- **PowerShell no distingue mayúsculas en los nombres de variable.** Escribir
  `$bloque` donde la plantilla se llama `$Bloque` las convierte en la *misma*
  variable: el placeholder `{p}` desaparecía en la primera página y todas las
  siguientes heredaban `assets/` sin el `../` de BlackFriday.
- **En `BlackFriday/` los dos `<link rel="stylesheet">` están en la misma
  línea.** Un ancla de regex que exija salto de línea al final no encuentra
  dónde insertar y la página se queda sin favicon en silencio.
- **`googleXXXX.html` no es una página**, es el fichero de verificación de
  Search Console: una línea de texto sin `<head>`. El script lo excluye.

Sobre el 512: la especificación de PWA lo pide, pero pesa 501 KB y sin un
`manifest` ningún navegador lo descarga. No se genera por eso.

> **La ilustración se ve bien a 180 px y es indescifrable a 32 px.** Es un
> favicon demasiado detallado para el tamaño real de una pestaña. Si algún día
> molesta en la barra del navegador, la opción es un recorte más simple para
> 16/32 y dejar la imagen entera solo para `apple-touch-icon`.

## Generar las páginas

Las páginas de catálogo y las guías no se escriben a mano: el texto vive en
`contenido_categoria.py` y `guias.py`, y los generadores son la única fuente
del HTML.

```bash
python generar_categorias.py   # las 7 páginas de catálogo
python generar_guias.py        # guias.html + 6 artículos
python generar_sitemap.py      # sitemap.xml (verifica que cada URL exista)
```

`generar_categorias.py` lee `data/<slug>.json` y **escribe las ofertas en el
HTML**, no solo en el JSON. Antes las páginas se generaban con un
`<section id="ofertas">` vacío que `app.js` rellenaba con `fetch()`: lo que
recibía un crawler eran cuarenta palabras y ni una sola oferta. Ahora el HTML
llega con las tarjetas ya escritas y `app.js` solo refresca los datos; si el
`fetch` falla, no borra lo que ya hay.

Si se toca la lógica de precios hay que tocar las dos copias: `precios()` en
`generar_categorias.py` y `preciosDe()` en `assets/app.js`. Si divergieran, la
página cambiaría sola al cargar el script.

### Páginas «puente»: retiradas el 10 de octubre de 2026

Había cuatro páginas de 300-360 palabras generadas por `generar_seo.py`
(`chollos-de-amazon`, `articulos-rebajados-amazon`, `errores-de-precio-amazon`,
`chollos-amazon-telegram`). Tenían un H1, dos párrafos, una lista de enlaces a
las categorías y un par de preguntas frecuentes.

 Las cuatro competían entre sí —todas apuntaban a «chollos de Amazon»— y con páginas
que ya las cubrían mejor. Se retiraron y sus URLs van con 301 a la página que
hoy ocupa esa intención:

| Retirada | Ahora la cubre |
|---|---|
| `chollos-de-amazon` | `general.html` (6.617 palabras, 100 ofertas) |
| `articulos-rebajados-amazon` | `general.html` |
| `errores-de-precio-amazon` | `como-detectar-errores-de-precio-amazon.html` (1.932) |
| `chollos-amazon-telegram` | `mejores-canales-telegram-ofertas.html` (1.406) |

Sus FAQ tampoco apportaban nada: las cinco preguntas ya estaban contestadas en
`general.html` y en las guías. `generar_seo.py` se borró con ellas.

> La lección está en `guias.py`, que ya las señalaba como el problema antes de
> que existieran las guías que las reemplazan. **Una página que solo enlaza a
> otras no es una página**: es un UUID con contenido, y Google la lee como thin
> content. Si una URL nueva no tiene algo que contar que no esté ya en otra
> parte, no debería existir.

Las redirecciones no se pueden declarar en el repositorio (GitHub Pages no
sirve `.htaccess`); van en Cloudflare. Ver `reglas.txt`, que genera
`tests/verificar_301.py`.

### El bot regenera el HTML al publicar

Antes el bot escribía los JSON y los subía, pero el HTML se generaba a mano.
Como las páginas se sirven con las ofertas escritas dentro, el repositorio
acababa con los JSON de una tanda y el HTML de la anterior: las ofertas nuevas
no llegaban al crawler hasta que alguien se acordaba de regenerar.

`publicar_en_git()` ahora ejecuta los tres generadores antes del `git add` y
los incluye en el mismo commit:

```
data/*.json + generar_categorias.py + generar_guias.py + generar_sitemap.py
  -> un solo commit -> un solo push
```

Detalles que importan:

- **Se comprueba `data/` antes de regenerar nada.** La tarea periódica entra en
  `publicar_en_git()` cada `PUBLICAR_CADA_S` segundos, así que regenerar sin
  mirar antes lanzaba los tres generadores (tres procesos de Python) en cada
  pasada, con el canal callado. Con el chequeo previo, el HTML solo se
  regenera cuando hay ofertas nuevas de verdad.
- El HTML se regenera **antes de commitear**, nunca después: si el commit
  saliera sin él, el repositorio quedaría con los JSON de una tanda y el HTML de
  la anterior. Un commit vacío no es posible porque `data/` acaba de cambiar.
- Las páginas se listan una a una (`_paginas_generadas()`) en vez de usar
  `git add *.html`, porque un pathspec con comodín también alcanzaría
  `BlackFriday/`.
- Si un generador falla, **no se aborta la subida**: es preferible subir los
  JSON con el HTML viejo a no subir nada. El fallo queda en el log con la salida
  del generador.
- Se puede desactivar con `REGENERAR_HTML=0`, que devuelve el bot al
  comportamiento anterior (solo `data/`).

`test_publicar_html.py` incluye una comprobación del **orden** dentro de
`publicar_en_git()`: que el chequeo de `data/` preceda a la regeneración y que
el retorno por "no hay cambios" también. Es un detalle fácil de deshacer por
error, y cuesta tres procesos de Python por minuto.

### Orden dentro de una página de categoría

```
h1 (cabecera)
  h2  Móviles y electrónica en Amazon España   ← cuenta de ofertas
      [grid de tarjetas]
  h2  Ofertas de móviles y electrónica en Amazon España
      h3  Móviles: el precio oficial casi nunca es el precio real
      h3  Cómo elegir y cuándo comprar
      h3  Preguntas frecuentes
```

El listado va **antes** que el texto. Quien llega a una página de categoría
busca precios, y 600-800 palabras antes del primer producto hacen que se vaya.

No cuesta SEO: un crawler recorre la página entera, así que el texto se sigue
leyendo e indexando igual, y el `ItemList` del JSON-LD no depende de la posición.
Lo que sí cambia es la UX, y en una página transaccional manda la intención de
compra. El texto editorial queda como respuesta larga para quien la busca.

`tests/validar_orden.py` fija el orden, las clases del CSS nuevo y que el
JSON-LD siga declarando `ItemList` y `FAQPage`.

> `validar_sitio.py` recorre `RAIZ.glob("*.html")`, así que **no baja a los
> subdirectorios** y no ve `BlackFriday/`. Por eso la sección tiene sus propios
> validadores, que sí resuelven las referencias relativas contra el directorio
> de cada HTML.

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
| `MAX_OFERTAS` | `100` | Ofertas guardadas por JSON. Si queda por debajo de `BACKFILL_LIMIT`, el bot lo sube al arrancar |
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
