"""Exportación exclusiva: nunca sobrescribe resultados."""
import json
from pathlib import Path

def guardar_json(ruta, datos):
    with Path(ruta).open('x',encoding='utf-8') as f:json.dump(datos,f,ensure_ascii=False,indent=2)

def guardar_csv(ruta, datos):
    with Path(ruta).open('x',encoding='utf-8',newline='') as f:datos.to_csv(f,index=False)
