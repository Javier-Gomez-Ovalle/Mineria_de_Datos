"""Verifica contenidos históricos; test solo por tamaño/fecha, sin abrirlo."""
from pathlib import Path
import json,hashlib
from .exportacion import guardar_json

def main():
    r=Path('fase04_clustering/resultados');antes=json.loads((r/'inventario_previo.json').read_text(encoding='utf-8'));fallos=[]
    for nombre,v in antes.items():
        p=Path(nombre)
        if not p.is_file():fallos.append(nombre);continue
        s=p.stat()
        if s.st_size!=v['size'] or str(s.st_mtime_ns)!=v['mtime_ns']:fallos.append(nombre)
        if 'sha256' in v and hashlib.sha256(p.read_bytes()).hexdigest()!=v['sha256']:fallos.append(nombre)
    assert not fallos,fallos
    nuevas=[p for carpeta in ['fase04_clustering','fase04_modelado/resultados_presentacion_supervisado'] for p in Path(carpeta).rglob('*') if p.is_file() and 'cache_graficas' not in p.parts]
    nuevas += [Path('INFORME_CLUSTERING_FASE04.md'),Path('INFORME_PRESENTACION_SUPERVISADO_FASE04.md')]
    guardar_json(r/'verificacion_integridad.json',dict(historicos=len(antes),con_sha256=sum('sha256' in v for v in antes.values()),solo_metadatos=sum('sha256' not in v for v in antes.values()),todos_intactos=True,test_leido=False,git_ejecutado=False,entregables_sha256={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in nuevas}))

if __name__=='__main__':main()
