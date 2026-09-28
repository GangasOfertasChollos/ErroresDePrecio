#!/usr/bin/env python3
"""
Script para recuperar las imágenes de las ofertas existentes.

Este script:
1. Lee los JSON de ofertas existentes
2. Para cada oferta sin imagen, obtiene el mensaje de Telegram por su ID
3. Descarga la imagen del mensaje directamente de Telegram
4. Actualiza el JSON con la ruta local de la imagen

Uso: python recuperar_imagenes.py
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Forzar salida UTF-8 en Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger('recuperar_imagenes')

# Cargar variables de entorno
_env_path = Path(__file__).resolve().parent / '.env'
if _env_path.exists():
    with open(_env_path, encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _key, _, _val = _line.partition('=')
                os.environ.setdefault(_key.strip(), _val.strip())

from telethon import TelegramClient

# Configuración
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '').strip()
MI_CANAL = os.getenv('TELEGRAM_CHANNEL', '@GangasOfertasChollos').strip()

REPO_PATH = Path(__file__).resolve().parent
DATA_PATH = REPO_PATH / 'data'
IMAGES_PATH = DATA_PATH / 'images'

# Crear directorio de imágenes si no existe
IMAGES_PATH.mkdir(parents=True, exist_ok=True)

async def recuperar_imagenes():
    """Recupera las imágenes de las ofertas existentes."""
    if not API_ID or not API_HASH:
        log.error("API_ID o API_HASH no configurados")
        return

    # Conectar a Telegram
    client = TelegramClient('sesion_recuperar', API_ID, API_HASH)
    
    try:
        await client.start()
        log.info("Conectado a Telegram")
        
        # Obtener el canal
        canal = await client.get_entity(MI_CANAL)
        log.info(f"Canal: {canal.title} (@{canal.username})")
        
        # Procesar cada archivo JSON
        for archivo_json in DATA_PATH.glob('*.json'):
            if archivo_json.name == 'categorias.json':
                continue
            
            log.info(f"\nProcesando {archivo_json.name}...")
            
            with open(archivo_json, 'r', encoding='utf-8') as f:
                ofertas = json.load(f)
            
            if not isinstance(ofertas, list):
                continue
            
            recuperadas = 0
            for oferta in ofertas:
                # Si ya tiene imagen local, saltar
                imagen_actual = oferta.get('image', '')
                if imagen_actual and not imagen_actual.startswith('http'):
                    continue
                
                mensaje_id = oferta.get('id')
                if not mensaje_id:
                    continue
                
                try:
                    # Obtener el mensaje de Telegram
                    mensaje = await client.get_messages(canal, ids=mensaje_id)
                    
                    if not mensaje or not mensaje.media:
                        continue
                    
                    # Descargar la imagen
                    nombre = f"oferta_{mensaje_id}"
                    ruta_archivo = IMAGES_PATH / f"{nombre}.jpg"
                    
                    if ruta_archivo.exists():
                        oferta['image'] = f"images/{ruta_archivo.name}"
                        recuperadas += 1
                        continue
                    
                    ruta = await client.download_media(mensaje.media, file=ruta_archivo)
                    
                    if ruta and Path(ruta).exists():
                        oferta['image'] = f"images/{Path(ruta).name}"
                        recuperadas += 1
                        log.info(f"  Recuperada imagen para oferta {mensaje_id}")
                    
                except Exception as e:
                    log.warning(f"  No se pudo recuperar imagen para oferta {mensaje_id}: {e}")
            
            # Guardar el JSON actualizado
            with open(archivo_json, 'w', encoding='utf-8') as f:
                json.dump(ofertas, f, ensure_ascii=False, indent=4)
            
            log.info(f"  {recuperadas} imágenes recuperadas en {archivo_json.name}")
    
    except Exception as e:
        log.error(f"Error: {e}")
    finally:
        await client.disconnect()
        log.info("\nDesconectado de Telegram")

if __name__ == '__main__':
    asyncio.run(recuperar_imagenes())
