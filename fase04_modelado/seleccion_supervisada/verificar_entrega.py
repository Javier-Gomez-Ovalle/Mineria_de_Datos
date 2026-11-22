"""Integridad histórica y manifiesto de la nueva entrega."""
from pathlib import Path
import json
from .auditoria import RAIZ,activar_guardia,sha,guardar_json

def main():
    activar_guardia();antes=json.loads((RAIZ/'inventario_previo.json').read_text(encoding='utf-8'));fallos=[]
    for nombre,v in antes.items():
        p=Path(nombre)
        if not p.is_file():fallos.append(nombre);continue
        s=p.stat()
        if s.st_size!=v['size'] or str(s.st_mtime_ns)!=v['mtime_ns']:fallos.append(nombre)
        if 'sha256' in v and sha(p)!=v['sha256']:fallos.append(nombre)
    assert not fallos,fallos
    entregables=[p for p in RAIZ.rglob('*') if p.is_file() and 'cache_graficas' not in p.parts]+[Path('INFORME_SELECCION_SUPERVISADA_FASE04.md')]
    guardar_json(RAIZ/'resultados/verificacion_entrega.json',dict(historicos=len(antes),sha256_comprobados=sum('sha256' in v for v in antes.values()),solo_metadatos=sum('sha256' not in v for v in antes.values()),todos_intactos=True,test_leido=False,modelos_entrenados=0,operaciones_git=False,hashes_entregables={p.as_posix():sha(p) for p in entregables}))
    print('Integridad OK:',len(antes),'historicos')

if __name__=='__main__':main()
