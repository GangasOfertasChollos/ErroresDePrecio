/* Ejecuta assets/app.js de verdad contra los JSON reales con un DOM minimo,
   para comprobar el render, el escapado, la whitelist de URLs y el JSON-LD. */
const fs = require("fs");
const path = require("path");

const RAIZ = path.resolve(__dirname, "..");
const EUR = "\u20AC";
let fallos = 0;
const check = (nombre, cond, detalle) => {
  if (cond) console.log("  OK   " + nombre);
  else { fallos++; console.log("  FALLO " + nombre + " -> " + (detalle === undefined ? "" : detalle)); }
};

function elem(tag) {
  return {
    tagName: tag.toUpperCase(), children: [], atributos: {}, _text: "", _html: "", _id: null,
    parentElement: null,
    set textContent(v) { this._text = String(v); this.children = []; },
    get textContent() { return this._text || this.children.map(c => c.textContent).join(""); },
    set innerHTML(v) { this._html = v; this.children = []; if (v === "") this._text = ""; },
    get innerHTML() { return this._html; },
    remove() { this._eliminado = true; },
    appendChild(c) { this.children.push(c); c.parentElement = this; return c; },
    insertAdjacentHTML(pos, html) {
      // Solo se usa con pos="afterbegin" (ver mostrarEstado en app.js).
      if (pos !== "afterbegin") throw new Error("pos no soportada: " + pos);
      this._prepend = (this._prepend || "") + html;
    },
    // app.js pregunta si el contenedor ya trae tarjetas servidas por el
    // generador antes de vaciarlo: si el fetch falla, las ofertas del HTML se
    // conservan y el aviso se antepone.
    querySelector(sel) {
      if (sel !== ".oferta") return null;
      return (this._html || "").indexOf('class="oferta"') >= 0 ? { _match: true } : null;
    },
    // contains() hace falta porque app.js comprueba si el #estado es el
    // placeholder que cuelga de #ofertas (páginas de catálogo) o un <p> aparte
    // (black-friday-2026.html).
    contains(nodo) {
      if (nodo === this) return true;
      return this.children.some((c) => c.contains && c.contains(nodo));
    },
    addEventListener(ev, fn) { this._ev = this._ev || {}; this._ev[ev] = fn; },
  };
}

function crearDoc(ids, anidarEstado) {
  const doc = { head: elem("head"), createElement: elem, _mapa: {} };
  doc.body = elem("body");
  doc.body.dataset = {};
  doc.querySelector = () => ({ textContent: "Prueba" });
  (ids || []).forEach((id) => {
    const e = elem("div"); e._id = id; doc._mapa[id] = e;
  });
  // Por defecto el #estado cuelga de #ofertas, que es como lo montan las 7
  // páginas de catálogo (general.html:52 y las de su hermana).
  // Con anidarEstado === false quedan como hermanos, que es la forma de
  // black-friday-2026.html: el "Cargando ofertas..." va dentro de #ofertas y el
  // #estado es un <p> aparte, así que al fallar hay que limpiar el contenedor.
  if (anidarEstado !== false && doc._mapa.ofertas && doc._mapa.estado) {
    doc._mapa.ofertas.appendChild(doc._mapa.estado);
    doc._mapa.ofertas._html = "Cargando ofertas...";
  }
  doc.getElementById = (id) => doc._mapa[id] || null;
  return doc;
}

function ejecutarApp(doc, respuesta) {
  global.document = doc;
  global.window = { location: { href: "http://x/general.html" } };
  global.console.error = () => {};
  global.fetch = () => {
    if (respuesta === "__fallo__") return Promise.reject(new Error("red"));
    if (respuesta === "__404__") return Promise.resolve({ ok: false, status: 404 });
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(respuesta) });
  };
  const src = fs.readFileSync(path.join(RAIZ, "assets", "app.js"), "utf8");
  const instrumentado = src.replace(
    "})();",
    "globalThis.__app = { urlSegura, precioAMayor, limpiarTitulo, inyectarSchema, esc, preciosDe };})();"
  );
  new Function("document", "window", "fetch", "console", "URL", instrumentado)(
    doc, global.window, global.fetch, console, URL
  );
  return new Promise((r) => setTimeout(r, 10));
}

const leerJson = (p) => JSON.parse(fs.readFileSync(path.join(RAIZ, p), "utf8"));

const EUR2 = "\u20AC";
const EJEMPLO = [
  { id: 2, date: "2026-09-25T12:00:00", title: "Smartphone Xiaomi Redmi Note 13", price: "249.99 " + EUR2, amazon_url: "https://www.amazon.es/dp/B0ABC1", image: "", categoria: "moviles-electronica" },
  { id: 1, date: "2026-09-25T09:00:00", title: "Portatil Lenovo IdeaPad 1", price: "1.299,00 " + EUR2, amazon_url: "https://amzn.to/xyz", image: "", categoria: "moviles-electronica" },
];

function leerDatosCatalogo() {
  const reales = leerJson("data/moviles-electronica.json");
  if (Array.isArray(reales) && reales.length) return reales;
  console.log("  (nota: data/ esta vacio, se usan ofertas de ejemplo)");
  return EJEMPLO;
}

(async () => {
  console.log("\n== Render del catalogo con datos reales ==");
  // Si data/ esta vacio (repo recien clonado, bot sin ofertas) se generan ofertas
  // de ejemplo para que la prueba siga cubriendo el render de verdad.
  const datos = leerDatosCatalogo();
  const doc = crearDoc(["ofertas", "estado"]);
  doc.body.dataset = { feed: "moviles-electronica" };
  await ejecutarApp(doc, datos);

  const cont = doc.getElementById("ofertas");
  const salida = cont.innerHTML;
  check("una tarjeta por oferta", (salida.match(/class="oferta"/g) || []).length === datos.length,
    (salida.match(/class="oferta"/g) || []).length + " vs " + datos.length);
  check("quita el mensaje de estado", doc.getElementById("estado")._eliminado === true);
  check("incluye el precio", salida.includes(datos[0].price), salida.slice(0, 300));
  check("rel de afiliado presente", salida.includes('rel="nofollow sponsored noopener"'));
  check("los enlaces de la oferta se respetan", salida.includes("oferta-comprar"),
    "no hay enlaces de compra");
  check("listener de error de imagen registrado", typeof (cont._ev && cont._ev.error) === "function");

  console.log("\n== XSS con datos manipulados ==");
  const malicioso = [{
    id: 1, date: "2026-01-01T00:00:00", price: "10.00 " + EUR, categoria: "general",
    title: '<img src=x onerror="alert(1)">"roto"&',
    amazon_url: 'https://www.amazon.es/dp/B01" onmouseover="alert(1)',
    image: '"><script>alert(2)</script>',
  }];
  const doc2 = crearDoc(["ofertas", "estado"]);
  doc2.body.dataset = { feed: "general" };
  await ejecutarApp(doc2, malicioso);
  const h = doc2.getElementById("ofertas").innerHTML;

  // Invariante real: al des-escapar las entidades, los tokens peligrosos siguen
  // siendo texto plano y nunca sintaxis HTML.
  const descapada = h
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");

  check("el titulo queda como texto plano",
    descapada.indexOf('<img src=x onerror="alert(1)">"roto"&') !== -1 &&
    !/alt="[^"]*<img/.test(h), (h.match(/alt="[^"]*"/) || [])[0]);
  check("ningun <img inyectado por el titulo", (h.match(/<img /g) || []).length <= 1,
    (h.match(/<img /g) || []).length);
  check("ningun <script> en el render", !/<script/i.test(h));
  check("el src malicioso no rompe el atributo",
    h.indexOf('src="&quot;&gt;&lt;script&gt;alert(2)&lt;/script&gt;"') !== -1 &&
    !/src="[^"]*"\s+onerror/i.test(descapada), (h.match(/oferta-img"><img[^>]*>/) || [])[0]);  check("el href con comillas no rompe el atributo",
    !/href="[^"]*"[^>]*onmouseover/i.test(descapada) && h.indexOf("%22") !== -1,
    (h.match(/oferta-comprar"[^>]*/) || [])[0]);
  // Un handler inyectado seria un ATRIBUTO llamado on*. Para distinguirlo del
  // texto escapado dentro de un valor, se vacian primero los valores entrecomillados.
  const soloNombres = (tag) => tag.replace(/"[^"]*"/g, '""');
  const etiquetas = h.match(/<[a-z]+ [^>]*>/gi) || [];
  check("ningun atributo on* real (handlers inyectados)",
    etiquetas.every((t) => !/\son[a-z]+\s*=/i.test(soloNombres(t))),
    etiquetas.filter((t) => /\son[a-z]+\s*=/i.test(soloNombres(t))).join(" | "));
  check("el onerror aparece solo dentro del valor de alt (inerte)",
    /alt="[^"]*onerror=/.test(h), (h.match(/alt="[^"]*"/) || [])[0]);

  console.log("\n== Estados de la pagina ==");
  const vacio = crearDoc(["ofertas", "estado"]);
  vacio.body.dataset = { feed: "general" };
  await ejecutarApp(vacio, []);
  check("array vacio -> mensaje util",
    vacio.getElementById("estado").textContent.indexOf("Todav") !== -1,
    vacio.getElementById("estado").textContent);

  const error = crearDoc(["ofertas", "estado"]);
  error.body.dataset = { feed: "general" };
  await ejecutarApp(error, "__fallo__");
  check("fallo de red -> mensaje de error",
    error.getElementById("estado").textContent.indexOf("No se han podido cargar") !== -1,
    error.getElementById("estado").textContent);

  const http404 = crearDoc(["ofertas", "estado"]);
  http404.body.dataset = { feed: "general" };
  await ejecutarApp(http404, "__404__");
  check("HTTP 404 -> mensaje de error",
    http404.getElementById("estado").textContent.indexOf("No se han podido cargar") !== -1);

  const malformado = crearDoc(["ofertas", "estado"]);
  malformado.body.dataset = { feed: "general" };
  await ejecutarApp(malformado, { no: "es un array" });
  check("JSON no-array -> mensaje de formato",
    malformado.getElementById("estado").textContent.indexOf("formato no") !== -1,
    malformado.getElementById("estado").textContent);

  // black-friday-2026.html: el #estado es un <p> HERMANO de #ofertas y el texto
  // de carga vive dentro de #ofertas. Antes de vaciar el contenedor, el
  // "Cargando ofertas..." se quedaba pegado al lado del error.
  console.log("\n== HTML ya servido con tarjetas (fallo de red) ==");
  // generar_categorias.py escribe las ofertas en el HTML. Si el fetch falla,
  // app.js no debe vaciar #ofertas: la pagina perderia su contenido por un
  // fallo de red, y quien llega sin JavaScript no veria ninguna oferta.
  const servido = crearDoc(["ofertas", "estado"]);
  servido.body.dataset = { feed: "general" };
  // Se emula el HTML generado: #estado no cuelga de #ofertas porque con
  // ofertas ya no se emite, y #ofertas trae tarjetas.
  const of = servido.getElementById("ofertas");
  of._html = '<article class="oferta" id="1">PS5</article>';
  of.children = [];
  // crearDoc cuelga #estado de #ofertas por defecto; con ofertas ya servidas
  // el generador no lo emite, asi que se saca de ahi.
  servido.getElementById("estado").parentElement = null;
  await ejecutarApp(servido, "__fallo__");
  check("las tarjetas del HTML no se borran al fallar el fetch",
    (of.innerHTML || "").indexOf('class="oferta"') !== -1,
    of.innerHTML);
  check("el aviso de error se antepone sin limpiar",
    (of._prepend || "").indexOf("No se han podido cargar") !== -1, of._prepend);
  check("no se crea un #estado nuevo sobre las tarjetas",
    servido.getElementById("estado")._text === "", servido.getElementById("estado")._text);

  console.log("\n== Estado con #estado aparte (black-friday-2026.html) ==");
  const hermano = crearDoc(["ofertas", "estado"], false);
  hermano.body.dataset = { feed: "general" };
  await ejecutarApp(hermano, "__fallo__");
  check("el error sale en el #estado",
    hermano.getElementById("estado").textContent.indexOf("No se han podido cargar") !== -1,
    hermano.getElementById("estado").textContent);
  check("y se limpia el 'Cargando ofertas...' de dentro de #ofertas",
    hermano.getElementById("ofertas").innerHTML === "",
    hermano.getElementById("ofertas").innerHTML);

  const hermanoOk = crearDoc(["ofertas", "estado"], false);
  hermanoOk.body.dataset = { feed: "general" };
  await ejecutarApp(hermanoOk, EJEMPLO);
  check("con datos, #ofertas se rellena y no queda el texto de carga",
    hermanoOk.getElementById("ofertas").innerHTML.indexOf("Cargando") === -1 &&
    hermanoOk.getElementById("ofertas").innerHTML.indexOf("<article") !== -1,
    hermanoOk.getElementById("ofertas").innerHTML.slice(0, 120));

  console.log("\n== urlSegura (whitelist) ==");
  const A = globalThis.__app;
  check("amazon.es permitido", A.urlSegura("https://www.amazon.es/dp/B01") === "https://www.amazon.es/dp/B01");
  check("amazon.com permitido", A.urlSegura("https://amazon.com/dp/B01").indexOf("amazon.com") !== -1);
  check("amzn.to permitido", A.urlSegura("https://amzn.to/abc").indexOf("amzn.to") !== -1);
  check("javascript: bloqueado", A.urlSegura("javascript:alert(1)") === "#");
  check("otro dominio bloqueado", A.urlSegura("https://evil.com/x") === "#");
  check("suplantacion amazon.es.evil.com bloqueada", A.urlSegura("https://amazon.es.evil.com/x") === "#",
    A.urlSegura("https://amazon.es.evil.com/x"));
  check("notamazon.es bloqueado", A.urlSegura("https://notamazon.es/x") === "#");
  // El bot acepta 9 formas de enlace (DOMINIOS_LINK en bot.py). Antes solo se
  // miraba el dominio padre, asi que 'amazon.evil' pasaba (padre 'amazon') y
  // 'amzlink.to' se bloqueaba (padre 'amzlink') aunque el bot lo extrae: la
  // tarjeta salia con href="#" y el boton no llevaba a ninguna parte.
  check("amazon.evil bloqueado (TLD real, padre 'amazon')", A.urlSegura("https://amazon.evil/dp/X") === "#",
    A.urlSegura("https://amazon.evil/dp/X"));
  check("amazon.zip bloqueado", A.urlSegura("https://amazon.zip/dp/X") === "#");
  check("amazon.click bloqueado", A.urlSegura("https://amazon.click/dp/X") === "#");
  check("amazon.top bloqueado", A.urlSegura("https://amazon.top/dp/X") === "#");
  check("amazon.link bloqueado", A.urlSegura("https://amazon.link/dp/X") === "#");
  check("amazon.cfd bloqueado", A.urlSegura("https://amazon.cfd/dp/X") === "#");
  check("amazon.es.evil bloqueado", A.urlSegura("https://amazon.es.evil/dp/X") === "#");
  check("amazonx.es bloqueado", A.urlSegura("https://amazonx.es/dp/X") === "#");
  check("amazon.espana bloqueado", A.urlSegura("https://amazon.espana/dp/X") === "#");
  check("amazon.com.mx permitido", A.urlSegura("https://amazon.com.mx/dp/B1").indexOf("amazon.com.mx") !== -1);
  check("amazon.co.uk permitido", A.urlSegura("https://amazon.co.uk/dp/B1").indexOf("amazon.co.uk") !== -1);
  check("smile.amazon.es permitido", A.urlSegura("https://smile.amazon.es/dp/B1").indexOf("smile.amazon.es") !== -1);
  check("amazon.es. con punto final permitido", A.urlSegura("https://amazon.es./dp/B1") !== "#",
    A.urlSegura("https://amazon.es./dp/B1"));
  check("amzlink.to permitido (lo usa el canal)", A.urlSegura("https://amzlink.to/abc").indexOf("amzlink.to") !== -1,
    A.urlSegura("https://amzlink.to/abc"));
  check("amzlink.eu permitido", A.urlSegura("https://amzlink.eu/abc").indexOf("amzlink.eu") !== -1);
  check("amzn.eu permitido", A.urlSegura("https://amzn.eu/abc").indexOf("amzn.eu") !== -1);
  check("amazon.co.uk permitido", A.urlSegura("https://amazon.co.uk/dp/B1").indexOf("amazon.co.uk") !== -1);
  check("amazon.es.evil.com sigue bloqueado", A.urlSegura("https://www.amazon.es.evil.com/x") === "#");
  check("data: bloqueado", A.urlSegura("data:text/html,x") === "#");
  check("vacio -> #", A.urlSegura("") === "#");
  check("basura -> #", A.urlSegura("no soy una url") === "#");

  console.log("\n== precioAMayor ==");
  check("'249.99 EUR' -> '249.99'", A.precioAMayor("249.99 " + EUR) === "249.99", A.precioAMayor("249.99 " + EUR));
  check("'1.299,00 EUR' -> '1299.00'", A.precioAMayor("1.299,00 " + EUR) === "1299.00", A.precioAMayor("1.299,00 " + EUR));
  check("'19,99' -> '19.99'", A.precioAMayor("19,99") === "19.99", A.precioAMayor("19,99"));
  check("vacio -> null", A.precioAMayor("") === null);
  check("'Ver precio' -> null", A.precioAMayor("Ver precio") === null);

  console.log("\n== precio actual / anterior / descuento ==");
  const P = A.preciosDe;
  const completo = P({ price: "29.75 " + EUR, old_price: "59.99 " + EUR, discount: "-50%" });
  check("las tres cifras del propio mensaje", completo.actual === "29.75 " + EUR &&
    completo.anterior === "59.99 " + EUR && completo.descuento === "-50%", JSON.stringify(completo));

  // El bot deja old_price y discount vacios cuando el precio anterior no venia
  // con la etiqueta del canal, pero el dato sigue en la descripcion.
  const enDesc = P({ price: "172.99 " + EUR, old_price: "", discount: "", description: "172,99 " + EUR + " (antes 296,06 " + EUR + ")" });
  check("recupera el 'antes' de la descripcion", enDesc.anterior === "296.06 " + EUR, enDesc.anterior);
  check("calcula el descuento que faltaba", enDesc.descuento === "-42%", enDesc.descuento);

  // Algunas veces el precio anterior solo aparece en el titulo, con 'PVP'.
  const enTitulo = P({ price: "74.35 " + EUR, title: "Figura coleccionista PVP: 124.99 " + EUR });
  check("recupera el 'PVP' del titulo", enTitulo.anterior === "124.99 " + EUR, enTitulo.anterior);

  const pctTitulo = P({ price: "41.99 " + EUR, title: "Chollo Auriculares por solo 41,99" + EUR + " (-40%)" });
  check("recupera el descuento del titulo", pctTitulo.descuento === "-40%", pctTitulo.descuento);

  // Un porcentaje que no es de descuento no debe cogerse ("80% de bateria").
  const falso = P({ price: "20.21 " + EUR, description: "Pestanas mas densas, con un 80% de garantia de por vida." });
  check("un '%' que no es descuento se ignora", falso.descuento === null, falso.descuento);

  // Un "antes" que no es mayor que el actual es ruido del parser: se descarta.
  const ruido = P({ price: "49.99 " + EUR, old_price: "9.99 " + EUR, discount: "" });
  check("'antes' menor que el actual -> descartado", ruido.anterior === null, ruido.anterior);
  check("y sin ese dato tampoco hay descuento", ruido.descuento === null, ruido.descuento);

  // Sin nada de nada: se devuelven null (el render los pintara como hueco).
  const vacio2 = P({ price: "9.00 " + EUR, old_price: "", discount: "", title: "Juego PS5", description: "" });
  check("el precio actual nunca falta si hay price", vacio2.actual === "9.00 " + EUR, vacio2.actual);
  check("sin datos: anterior a null", vacio2.anterior === null, vacio2.anterior);
  check("sin datos: descuento a null", vacio2.descuento === null, vacio2.descuento);

  // Invariante de la pagina: aunque no haya nada, las tres cajas se pintan.
  const doc3 = crearDoc(["ofertas", "estado"]);
  doc3.body.dataset = { feed: "general" };
  await ejecutarApp(doc3, [
    { id: 1, date: "2026-01-01", title: "Juego PS5", price: "9.00 " + EUR, amazon_url: "https://www.amazon.es/dp/B01", categoria: "general" },
    { id: 2, date: "2026-01-01", title: "Altavoz", price: "39.99 " + EUR, old_price: "59.99 " + EUR, discount: "-33%", amazon_url: "https://www.amazon.es/dp/B02", categoria: "general" },
  ]);
  const tarjetas = doc3.getElementById("ofertas").innerHTML.split('<article class="oferta"').slice(1);
  check("las 3 cifras se pintan en TODAS las tarjetas", tarjetas.length === 2 &&
    tarjetas.every((t) => /Precio actual/.test(t) && /Precio anterior/.test(t) && /Descuento/.test(t) &&
      /class="oferta-precio"/.test(t) && /class="oferta-precio-antes/.test(t) && /class="oferta-descuento/.test(t)),
    tarjetas.length);
  check("sin datos el hueco de 'antes' va explicito", /oferta-precio-antes es-hueco">No disponible/.test(tarjetas[0]),
    (tarjetas[0].match(/oferta-precio-antes[^<]*<[^>]*>([^<]*)/) || [])[1]);
  check("sin datos el hueco de 'descuento' va explicito", /oferta-descuento es-hueco">Sin descuento/.test(tarjetas[0]),
    (tarjetas[0].match(/oferta-descuento[^<]*<[^>]*>([^<]*)/) || [])[1]);
  check("con datos NO se marca el hueco", !/es-hueco/.test(tarjetas[1]), tarjetas[1].slice(0, 200));

  console.log("\n== JSON-LD dinamico ==");
  const nuevoDoc = crearDoc(["ofertas", "estado"]);
  nuevoDoc.body.dataset = { feed: "moviles-electronica" };
  await ejecutarApp(nuevoDoc, datos);
  const scripts = nuevoDoc.head.children;
  check("inyecta 1 ItemList",
    scripts.length === 1 && JSON.parse(scripts[0].textContent)["@type"] === "ItemList", scripts.length);
  if (scripts.length) {
    const s = JSON.parse(scripts[0].textContent);
    check("numberOfItems correcto", s.numberOfItems === datos.length, s.numberOfItems);
    check("position empieza en 1", s.itemListElement[0].position === 1);
    check("price con 2 decimales", /^\d+\.\d{2}$/.test(s.itemListElement[0].item.price), s.itemListElement[0].item.price);
    check("priceCurrency EUR", s.itemListElement[0].item.priceCurrency === "EUR");
    // Con datos reales todas son de Amazon; con el ejemplo, tambien amzn.to.
    check("solo urls de amazon o amzn",
      s.itemListElement.every((x) => /amazon\.|amzn\./.test(x.item.url)),
      s.itemListElement.map((x) => x.item.url).join(" "));
    check("sin HTML en el JSON-LD", !/<[a-z/]/i.test(JSON.stringify(s)));

    // gtin y mpn van en propiedades distintas: un MPN no es un GTIN, y
    // publicarlo como itemprop="gtin" es informacion falsa.
    const conCodigos = [
      { id: 9, date: "2026-10-01T10:00:00", title: "Altavoz con MPN", price: "19,99 " + EUR2,
        amazon_url: "https://www.amazon.es/dp/B0MPN", image: "", gtin: "8412345678905", mpn: "RLC-810A" },
      { id: 8, date: "2026-10-01T10:00:00", title: "Solo GTIN", price: "9,99 " + EUR2,
        amazon_url: "https://www.amazon.es/dp/B0GTI", image: "", gtin: "012345678905" },
    ];
    const docCod = crearDoc(["ofertas", "estado"]);
    docCod.body.dataset = { feed: "general" };
    await ejecutarApp(docCod, conCodigos);
    const items = docCod.head.children.length
      ? JSON.parse(docCod.head.children[0].textContent).itemListElement.map((x) => x.item) : [];
    check("el GTIN real va en gtin", items[0] && items[0].gtin === "8412345678905", JSON.stringify(items[0]));
    check("el MPN va en mpn, no en gtin", items[0] && items[0].mpn === "RLC-810A", JSON.stringify(items[0]));
    check("y gtin no se pisa con el MPN", items[0] && !/RLC/.test(items[0].gtin || ""), JSON.stringify(items[0]));
    check("una oferta solo con GTIN no inventa mpn",
      items[1] && items[1].gtin === "012345678905" && !items[1].mpn, JSON.stringify(items[1]));

    // Y en el HTML (microdata)
    const htmlCod = docCod.getElementById("ofertas").innerHTML;
    check('microdata itemprop="gtin" con el GTIN', htmlCod.includes('itemprop="gtin" content="8412345678905"'));
    check('microdata itemprop="mpn" con el MPN', htmlCod.includes('itemprop="mpn" content="RLC-810A"'));
  }

  console.log("\n" + "=".repeat(56));
  console.log(fallos === 0 ? "TODO CORRECTO" : fallos + " PRUEBAS FALLIDAS");
  process.exit(fallos ? 1 : 0);
})();
