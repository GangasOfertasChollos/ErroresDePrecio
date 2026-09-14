# Escaparate de Amazon + bot Termux

Un único canal. El bot NO reenvía a otros canales. Lee nuevas publicaciones, detecta el hashtag, extrae el enlace de Amazon y actualiza la página de categoría.

Instalación:
```bash
pkg update
pkg install python git
git clone https://github.com/gangasofertaschollos/ErroresDePrecio.git
cd ErroresDePrecio
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

Añade el bot como administrador de `@GangasOfertasChollos`.

El botón de cada oferta es **VER OFERTA EN AMAZON** y apunta directamente al enlace de Amazon de la publicación, incluidos enlaces de afiliado.

El bot recibe publicaciones nuevas; Bot API no permite recorrer arbitrariamente todo el historial anterior.


## Categorías

Usa uno de estos hashtags en cada publicación del canal para clasificar la oferta:
- `#ropaycalzado` → Ropa y calzado
- `#higieneycuidadopersonal` → Higiene y cuidado personal
- `#gamingyconsolas` → Gaming y consolas
- `#jugueteseinfantil` → Juguetes e infantil
- `#papeleriayoficina` → Papelería y oficina
- `#movileselectronica` → Móviles y electrónica
- `#general` → General
