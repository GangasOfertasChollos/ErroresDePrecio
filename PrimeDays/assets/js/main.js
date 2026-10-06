/* ==========================================================================
   GangasOfertas.com — Amazon Prime Days
   JS mínimo y progresivamente mejorado. El sitio funciona SIN JS:

   - El menú móvil es un <button> + <nav> que se despliega con .is-open
   - La cuenta atrás muestra texto estático si no hay JS
   - El FAQ usa <details>/<summary> nativo

   No hay analítica, ni cookies, ni peticiones a terceros.
   ========================================================================== */
(function () {
  "use strict";

  /* ----------------------------------------------------------------------
     1. Menú móvil
     ---------------------------------------------------------------------- */
  var toggle = document.querySelector(".nav__toggle");
  var links = document.getElementById("nav-links");

  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Cerrar menú" : "Abrir menú");
    });

    // Cerrar al navegar
    links.addEventListener("click", function (e) {
      if (e.target.closest("a")) {
        links.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });

    // Cerrar con Escape
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && links.classList.contains("is-open")) {
        links.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  /* ----------------------------------------------------------------------
     2. Cuenta atrás → fin de la Fiesta de Ofertas Prime.

     La campaña de octubre de 2026 va del martes 6 al miércoles 7 de
     octubre, y termina a las 23:59 hora peninsular española (Madrid).
     Se fija a esa fecha LOCAL a propósito, para no depender del zona
     horario del visitante ni de que el reloj del servidor esté en UTC.

     Sin JS los <span data-unit> se quedan con el valor estático que trae el
     HTML, así que nunca se ve un "NaN" ni un hueco.
     ---------------------------------------------------------------------- */
  var countdown = document.getElementById("countdown");

  if (countdown) {
    // Miércoles 7 de octubre de 2026, 23:59 hora peninsular.
    var TARGET = new Date(2026, 9, 7, 23, 59, 0);

    var cells = {
      days: countdown.querySelector('[data-unit="days"]'),
      hours: countdown.querySelector('[data-unit="hours"]'),
      mins: countdown.querySelector('[data-unit="mins"]'),
      secs: countdown.querySelector('[data-unit="secs"]'),
      label: countdown.querySelector("[data-countdown-label]")
    };

    var pad = function (n) { return String(n).padStart(2, "0"); };

    function tick() {
      var diff = TARGET.getTime() - new Date().getTime();

      if (diff <= 0) {
        // Terminada: se congela a cero y se avisa una sola vez.
        ["days", "hours", "mins", "secs"].forEach(function (k) {
          if (cells[k]) cells[k].textContent = "00";
        });
        if (cells.label) {
          cells.label.textContent =
            "La Fiesta de Ofertas Prime 2026 ha terminado. Las ofertas de hoy ya no están vigentes.";
        }
        countdown.setAttribute("data-finished", "true");
        return false; // detiene el intervalo
      }

      var s = Math.floor(diff / 1000);
      var d = Math.floor(s / 86400);
      var h = Math.floor((s % 86400) / 3600);
      var m = Math.floor((s % 3600) / 60);
      var sec = s % 60;

      if (cells.days) cells.days.textContent = pad(d);
      if (cells.hours) cells.hours.textContent = pad(h);
      if (cells.mins) cells.mins.textContent = pad(m);
      if (cells.secs) cells.secs.textContent = pad(sec);

      return true;
    }

    if (tick()) {
      var id = setInterval(function () { if (!tick()) clearInterval(id); }, 1000);
    }
  }

  /* ----------------------------------------------------------------------
     3. FAQ: "desplegar todas / plegar todas"
     ---------------------------------------------------------------------- */
  var faqToggle = document.querySelector("[data-faq-toggle]");

  if (faqToggle) {
    faqToggle.addEventListener("click", function () {
      var box = faqToggle.getAttribute("data-faq-target");
      var group = box && document.getElementById(box);
      if (!group) return;

      var items = group.querySelectorAll("details");
      var anyClosed = Array.prototype.some.call(items, function (d) { return !d.open; });

      Array.prototype.forEach.call(items, function (d) { d.open = anyClosed; });
      faqToggle.textContent = anyClosed ? "Plegar todas" : "Desplegar todas";
      faqToggle.setAttribute("aria-expanded", anyClosed ? "true" : "false");
    });
  }

  /* ----------------------------------------------------------------------
     4. Marca los enlaces al canal de Telegram.

     No cambia el comportamiento: solo añade data-channel para poder medir
     los clics por variante (hero, topbar, cta_band...) si algún día se
     conecta una analítica, sin tocar el HTML.
     ---------------------------------------------------------------------- */
  var tgLinks = document.querySelectorAll('a[href^="https://t.me/GangasOfertasChollos"]');
  Array.prototype.forEach.call(tgLinks, function (a) {
    a.setAttribute("data-channel", "GangasOfertasChollos");
  });

  /* ----------------------------------------------------------------------
     5. Enlace activo según la URL real.

     El servidor ya marca aria-current, pero esto lo resuelve también al
     navegar por el historial sin recargar.
     ---------------------------------------------------------------------- */
  var here = location.pathname.split("/").pop() || "index.html";
  var navA = document.querySelectorAll(".nav__links > a");

  Array.prototype.forEach.call(navA, function (a) {
    var href = a.getAttribute("href");
    if (!href) return;
    var file = href.split("#")[0].split("/").pop();
    if (file && file === here) a.setAttribute("aria-current", "page");
  });
})();