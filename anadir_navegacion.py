#!/usr/bin/env python3
"""
Script para añadir un menú de navegación consistente a todas las páginas HTML.
"""
import re
import sys
from pathlib import Path

# Forzar salida UTF-8 en Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO_PATH = Path(__file__).resolve().parent

# El menu no se escribe aqui: se toma de plantilla_comun, que es la unica
# definicion. Antes esta lista era una tercera copia del menu y divergia de
# la de generar_categorias.py en cuanto se anadia una entrada.
from plantilla_comun import nav_html


def menu_html(actual: str = "") -> str:
    return (
        '\n<nav class="nav" aria-label="Navegacion principal">\n'
        + nav_html(actual, sangria="  ")
        + "\n</nav>\n"
    )

NAV_CSS = '''
/* ===== Menu de navegacion ===== */
.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 0;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.nav a {
  color: #fff;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  background: rgba(255,255,255,0.05);
}

.nav a:hover {
  background: rgba(255,255,255,0.15);
  transform: translateY(-1px);
}

.nav a[aria-current="page"] {
  background: #ff9900;
  color: #000;
}

@media (max-width: 768px) {
  .nav {
    justify-content: center;
  }
  .nav a {
    padding: 6px 12px;
    font-size: 13px;
  }
}
'''

def annadir_navegacion():
    paginas = [
        'index.html',
        'general.html',
        'categorias.html',
        'ropa-y-calzado.html',
        'moviles-electronica.html',
        'gaming-consolas.html',
        'higiene-cuidado-personal.html',
        'juguetes-infantil.html',
        'papeleria-oficina.html',
    ]

    for pagina in paginas:
        ruta = REPO_PATH / pagina
        if not ruta.exists():
            print(f"  [SKIP] {pagina} no existe")
            continue

        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()

        # Los generadores (generar_categorias.py / generar_seo.py) ya escriben el
        # menu con la tilde en "Navegación". Se buscan las dos variantes para no
        # insertar un segundo menu en esas paginas.
        if 'aria-label="Navegacion principal"' in contenido or 'aria-label="Navegación principal"' in contenido:
            print(f"  [OK] {pagina} ya tiene menu")
            continue

        if '.nav {' not in contenido:
            if '</style>' in contenido:
                contenido = contenido.replace('</style>', NAV_CSS + '\n</style>')
            else:
                contenido = contenido.replace('</head>', f'<style>{NAV_CSS}</style>\n</head>')

        if '<header' in contenido:
            match = re.search(r'(<header[^>]*>.*?</header>)', contenido, re.DOTALL)
            if match:
                header = match.group(1)
                nuevo_header = header.replace('</header>', menu_html(pagina) + '\n</header>')
                contenido = contenido.replace(header, nuevo_header)
        else:
            contenido = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + menu_html(pagina), contenido)

        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)

        print(f"  [OK] {pagina} actualizada")

if __name__ == '__main__':
    print("Anadiendo menu de navegacion...")
    annadir_navegacion()
    print("Listo.")
