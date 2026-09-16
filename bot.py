import json
import re
from pathlib import Path
from telethon import TelegramClient, events

API_ID = 31029230
API_HASH = '027e3d6b82fc3330defc4fcd1ee0a06a'
MI_CANAL = '@GangasOfertasChollos'

REPO_PATH = Path('.').resolve()
DATA_PATH = REPO_PATH / 'data'
DICCIONARIO_PATH = REPO_PATH / 'categorias.json'
MAX_OFERTAS = 30

client = TelegramClient('sesion_json_bot', API_ID, API_HASH)

def cargar_diccionario():
    with open(DICCIONARIO_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

PALABRAS_CATEGORIAS = cargar_diccionario()

def clasificar_oferta(texto):
    texto = texto.lower()
    puntuaciones = {}
    for categoria, palabras in PALABRAS_CATEGORIAS.items():
        puntuaciones[categoria] = sum(
            1 for palabra in palabras
            if re.search(r'(?<!\w)' + re.escape(palabra.lower()) + r'(?!\w)', texto)
        )
    categoria = max(puntuaciones, key=puntuaciones.get)
    return categoria if puntuaciones[categoria] else 'general'

def extraer_enlace_amazon(texto):
    m = re.search(r'https?://(?:www\.)?amazon\.es/[^\s<>)]+', texto, re.I)
    if m:
        return m.group(0).rstrip('.,')
    m = re.search(r'https?://amzn\.to/[^\s<>)]+', texto, re.I)
    return m.group(0).rstrip('.,') if m else ''

def extraer_precio(texto):
    for patron in [r'(\d+[,.]\d{2})\s*€', r'€\s*(\d+[,.]\d{2})', r'(\d+)\s*€']:
        m = re.search(patron, texto)
        if m:
            return m.group(1).replace(',', '.') + ' €'
    return ''

def extraer_titulo(texto):
    lineas = [x.strip() for x in texto.splitlines() if x.strip()]
    return lineas[0][:200] if lineas else 'Oferta Amazon'

def actualizar_json(categoria, mensaje):
    archivo = DATA_PATH / f'{categoria}.json'
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    try:
        datos = json.loads(archivo.read_text(encoding='utf-8')) if archivo.exists() else []
    except Exception:
        datos = []

    enlace = extraer_enlace_amazon(mensaje.text or '')
    if enlace and any(x.get('amazon_url') == enlace for x in datos):
        print('[=] Oferta duplicada')
        return

    datos.insert(0, {
        'id': mensaje.id,
        'date': mensaje.date.isoformat() if mensaje.date else '',
        'title': extraer_titulo(mensaje.text or ''),
        'price': extraer_precio(mensaje.text or ''),
        'amazon_url': enlace,
        'categoria': categoria
    })
    archivo.write_text(json.dumps(datos[:MAX_OFERTAS], ensure_ascii=False, indent=4), encoding='utf-8')
    print(f'[✓] Guardado local: {archivo}')

@client.on(events.NewMessage(chats=MI_CANAL))
async def detector_ofertas(event):
    texto = event.message.text
    if not texto:
        return
    categoria = clasificar_oferta(texto)
    print(f'[+] ID {event.message.id} → {categoria}')
    actualizar_json(categoria, event.message)

if __name__ == '__main__':
    print('BOT OFERTAS - SOLO JSON LOCAL')
    print(f'Canal: {MI_CANAL}')
    print(f'Diccionario: {DICCIONARIO_PATH}')
    print('Git: DESACTIVADO')
    client.start()
    client.run_until_disconnected()
