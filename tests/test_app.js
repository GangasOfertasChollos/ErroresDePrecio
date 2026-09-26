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
    set textContent(v) { this._text = String(v); this.children = []; },
    get textContent() { return this._text || this.children.map(c => c.textContent).join(""); },
    set innerHTML(v) { this._html = v; this.children = []; if (v === "") this._text = ""; },
    get innerHTML() { return this._html; },
    remove() { this._eliminado = true; },
    appendChild(c) { this.children.push(c); return c; },
    addEventListener(ev, fn) { this._ev = this._ev || {}; this._ev[ev] = fn; },
  };
}

function crearDoc(ids) {
  const doc = { head: elem("head"), createElement: elem, _mapa: {} };
  doc.body = elem("body");
  doc.body.dataset = {};
  doc.querySelector = () => ({ textContent: "Prueba" });
  (ids || []).forEach((id) => {
    const e = elem("div"); e._id = id; doc._mapa[id] = e;
  });
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
    "globalThis.__app = { urlSegura, precioAMayor, limpiarTitulo, inyectarSchema, esc };})();"
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
  check("data: bloqueado", A.urlSegura("data:text/html,x") === "#");
  check("vacio -> #", A.urlSegura("") === "#");
  check("basura -> #", A.urlSegura("no soy una url") === "#");

  console.log("\n== precioAMayor ==");
  check("'249.99 EUR' -> '249.99'", A.precioAMayor("249.99 " + EUR) === "249.99", A.precioAMayor("249.99 " + EUR));
  check("'1.299,00 EUR' -> '1299.00'", A.precioAMayor("1.299,00 " + EUR) === "1299.00", A.precioAMayor("1.299,00 " + EUR));
  check("'19,99' -> '19.99'", A.precioAMayor("19,99") === "19.99", A.precioAMayor("19,99"));
  check("vacio -> null", A.precioAMayor("") === null);
  check("'Ver precio' -> null", A.precioAMayor("Ver precio") === null);

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
  }

  console.log("\n" + "=".repeat(56));
  console.log(fallos === 0 ? "TODO CORRECTO" : fallos + " PRUEBAS FALLIDAS");
  process.exit(fallos ? 1 : 0);
})();
