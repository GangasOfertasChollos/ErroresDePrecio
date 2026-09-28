#!/usr/bin/env python3
"""
Script para limpiar las imágenes rotas de los JSON de ofertas.

Las imágenes de telesco.pe tienen URLs que expiran con el tiempo.
Este script elimina esas URLs de los JSON para que el frontend
no intente cargar imágenes que ya no existen.

Uso: python limpiar_imagenes_rotas.py
"""

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / 'data'

def limpiar_imagenes_rotas():
    """Elimina las URLs de telesco.pe de todos los JSON de ofertas."""
    if not DATA_PATH.exists():
        print(f"El directorio {DATA_PATH} no existe")
        return
    
    total_limpio = 0
    
    for archivo_json in DATA_PATH.glob('*.json'):
        try:
            with open(archivo_json, 'r', encoding='utf-8') as f:
                ofertas = json.load(f)
            
            if not isinstance(ofertas, list):
                continue
            
            modificadas = False
            for oferta in ofertas:
                imagen = oferta.get('image', '')
                # Si la imagen es de telesco.pe, eliminarla
                if 'telesco.pe' in imagen or 't.me' in imagen:
                    oferta['image'] = ''
                    modificadas = True
                    total_limpio += 1
            
            if modificadas:
                with open(archivo_json, 'w', encoding='utf-8') as f:
                    json.dump(ofertas, f, ensure_ascii=False, indent=4)
                print(f"  Limpiadas {total_limpio} imágenes de {archivo_json.name}")
        
        except Exception as e:
            print(f"  Error procesando {archivo_json.name}: {e}")
    
    print(f"\nTotal: {total_limpio} imágenes rotas eliminadas")

if __name__ == '__main__':
    print("Limpiando imágenes rotas de los JSON...")
    limpiar_imagenes_rotas()
