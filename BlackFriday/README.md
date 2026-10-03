# Black Friday 2026 — GangasOfertas.com

Lander SEO estático para el canal de Telegram **[@GangasOfertasChollos](https://t.me/GangasOfertasChollos)**.

- **17 páginas** · ~34.000 palabras · HTML/CSS/JS puro, sin dependencias ni build
- **0 peticiones a terceros**: sin fuentes externas, sin cookies, sin analítica
- **8 clusters de keywords**, datos estructurados en todas las páginas, 81 enlaces al canal
- Dominio actual: `https://gangasofertas.com/BlackFriday` (Cloudflare Pages)

---

## Estructura

```
index.html                          Pillar: Black Friday 2026 (4.100 palabras) + FAQ
fecha-black-friday-2026.html        Calendario y fechas
ofertas-black-friday-2026.html      Descuentos por categoría
gangas-black-friday.html            Gangas vs. falsos descuentos
canal-telegram-ofertas.html         El canal (diferenciador)
errores-de-precio-amazon.html       Errores de precio + Keepa
como-aprovechar-black-friday.html   Método de compra en 5 pasos
black-friday-vs-cyber-monday.html   Comparativa de las dos fechas
black-friday-por-categorias.html    Guía por categoría
que-es-el-black-friday.html         Origen y significado
evitar-estafas-black-friday.html    Seguridad y phishing
faq.html                            16 preguntas frecuentes
metodologia.html                    Cómo verificamos las ofertas
sobre-nosotros.html                 El proyecto
aviso-legal.html · politica-privacidad.html
404.html

sitemap.xml · robots.txt · llms.txt
assets/css/style.css · assets/js/main.js · assets/img/
docs/SEO-STRATEGY.md                Research de keywords + análisis de competidores
docs/check.ps1                      Validador de contenido
docs/seo-check.ps1                  Auditoría SEO
docs/migrate-domain.ps1             Migración de dominio (buscar y reemplazar + backup)
docs/package-deploy.ps1             Empaqueta la carpeta que se sube a Cloudflare Pages
```

---

## Validación

```powershell
powershell -ExecutionPolicy Bypass -File docs\check.ps1      # contenido y estructura
powershell -ExecutionPolicy Bypass -File docs\seo-check.ps1  # auditoría SEO
```

Estado actual: **0 errores, 0 avisos**.

---

## Vista previa local

```powershell
python -m http.server 8765
# http://127.0.0.1:8765/
```

---

## Publicación

El sitio es estático, así que sirve en cualquier hosting. El hosting actual es **Cloudflare Pages**
con **drag & drop**.

### Desplegar (drag & drop)

```powershell
powershell -ExecutionPolicy Bypass -File docs\package-deploy.ps1
```

El script arma una carpeta limpia en `%TEMP%\BlackFriday-deploy` con solo lo publicable — el HTML,
`assets/` y `sitemap.xml` / `robots.txt` / `llms.txt` — y deja fuera `docs/`, `README.md` y los `.ps1`.
Con drag & drop se sube la carpeta **entra**: cualquier cosa en la raíz acaba en producción.

Después:

1. Cloudflare Dashboard → Workers & Pages → tu proyecto → **Create a new deployment** → **Upload assets**
2. Arrastra `C:\Users\<tu-usuario>\AppData\Local\Temp\BlackFriday-deploy`
3. Espera al build y comprueba que `robots.txt` ya devuelve el dominio nuevo

El script verifica antes de dejarte arrastrar: que no queden restos del dominio anterior, que no haya
`.ps1` ni `.md` en el paquete, que el meta tag de Search Console esté en la portada, que el canonical
sea el correcto y que estén las 17 páginas. Si algo falla, no se despliega.

> ⚠️ El plan gratis de Cloudflare Pages limita a **500 despliegues/mes**. Cada drag & drop cuenta.
> Con la frecuencia de esta temporada no hay problema, pero si te pasas, toca conectar git.

### Otros hostings

**GitHub Pages**
```bash
git init && git add . && git commit -m "Black Friday 2026"
git branch -M main
git remote add origin https://github.com/<usuario>/<repo>.git
git push -u origin main
# Settings > Pages > Deploy from a branch > main / (root)
```

**Netlify / Vercel**
- Build command: *(vacío)* · Output directory: `/`
- O simplemente arrastra la carpeta al deploy de Netlify.

---

## Migración de dominio

Los dominios aparecen en todos los ficheros con el mismo prefijo, así que basta con un reemplazo global.
**No lo hagas a mano.** Usa el script, que además hace copia de seguridad:

```powershell
powershell -ExecutionPolicy Bypass -File docs\migrate-domain.ps1 `
  -OldPrefix 'https://gangasofertas.com/BlackFriday' `
  -NewPrefix 'https://tudominio.com'

powershell -ExecutionPolicy Bypass -File docs\check.ps1
powershell -ExecutionPolicy Bypass -File docs\seo-check.ps1
```

El prefijo antiguo se indica **sin barra final** para que la portada conserve la suya:

```
https://antiguo.com/           ->  https://nuevo.com/
https://antiguo.com/faq.html   ->  https://nuevo.com/faq.html
```

Cubre los `<link rel="canonical">`, `og:url`, `twitter:image`, los JSON-LD, `sitemap.xml`, `robots.txt`,
`llms.txt`, los scripts de auditoría y los documentos. `docs\seo-check.ps1` lleva el dominio en `$site`
para validar los canonicals, así que también se actualiza solo.

> ⚠️ El backup se escribe en el directorio temporal, **fuera** de la raíz del sitio. Si lo dejaras dentro,
> el hosting lo publicaría como duplicado con los canonicals antiguos.

---

## Antes de subir a producción

1. [x] Migrar a Cloudflare Pages — `https://gangasofertas.com/BlackFriday`
2. [ ] **Redesplegar**: producción sigue sirviendo los canonicals de `github.io` hasta que subas los ficheros
3. [ ] Verificar la propiedad en Search Console (ver abajo)
4. [ ] Bing Webmaster Tools → importar desde GSC
5. [ ] Revisar los precios de la tabla de categorías con datos reales de la campaña
6. [ ] Actualizar `dateModified` en los JSON-LD
7. [ ] Empezar a publicar el canal desde redes a partir del 23 de noviembre
8. [ ] Si más adelante compras dominio propio: reejecuta `docs\migrate-domain.ps1` y añade una
      redirección 301 de `pages.dev` al nuevo dominio en el panel de Cloudflare

### Verificación de Search Console

El sitio usa el método **meta tag**, en la portada (`index.html`, línea 13):

```html
```

Google solo necesita el tag en **una** página, así que no está en las otras 16. Espera a que
Google rastree la portada tras el redespliegue; si tarda, pulsa **Verificar** otra vez en Search Console.

Cuando migres a un dominio propio, el token **sigue siendo válido** (pertenece a la propiedad, no a la URL),
pero mueve el tag a la portada nueva y vuelve a verificar.

---

## Avisos

Los enlaces al canal y a Amazon llevan `rel="sponsored nofollow noopener"`: el sitio monetiza con comisiones de
afiliación de Amazon y **no cobra nada al usuario**. El detalle está en `metodologia.html` y `aviso-legal.html`.

Los precios publicados caducan y los errores de precio duran minutos. Verifica siempre antes de comprar.