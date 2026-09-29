from pathlib import Path

paginas = [
    'general.html', 'categorias.html', 'ropa-y-calzado.html',
    'moviles-electronica.html', 'gaming-consolas.html',
    'higiene-cuidado-personal.html', 'juguetes-infantil.html',
    'papeleria-oficina.html', 'chollos-de-amazon.html',
    'errores-de-precio-amazon.html', 'articulos-rebajados-amazon.html',
    'chollos-amazon-telegram.html'
]

boton = '<a href="https://t.me/GangasOfertasChollos" class="btn-telegram" target="_blank" rel="noopener">Únete al canal</a>'

for pagina in paginas:
    ruta = Path(pagina)
    if not ruta.exists():
        print(f'  NO EXISTE {pagina}')
        continue
    contenido = ruta.read_text(encoding='utf-8')
    if '</header>' in contenido:
        contenido = contenido.replace('</header>', boton + '\n</header>', 1)
        ruta.write_text(contenido, encoding='utf-8')
        print(f'  OK {pagina}')
    else:
        print(f'  SIN HEADER {pagina}')
