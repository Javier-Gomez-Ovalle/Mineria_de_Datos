"""Contratos de acceso, persistencia exclusiva e integridad histórica."""
from pathlib import Path
import sys,json,hashlib
import numpy as np

RAIZ=Path('fase04_modelado/validacion_anidada')
RESULTADOS=RAIZ/'resultados'
ACCESOS=[]

def guardia(evento,args):
    if evento=='open' and isinstance(args[0],(str,bytes,Path)):
        nombre=Path(str(args[0])).name.lower()
        if 'test' in nombre and nombre.endswith(('.csv','.npy','.joblib')):raise PermissionError('Datos test prohibidos')
        if nombre.endswith(('.csv','.npy','.joblib')):ACCESOS.append(str(args[0]))

def activar_guardia():sys.addaudithook(guardia)

def sha(ruta):return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()

def hash_indices(indices):return hashlib.sha256(np.asarray(indices,dtype=np.int64).tobytes()).hexdigest()

def guardar_json(ruta,datos):
    with Path(ruta).open('x',encoding='utf-8') as f:json.dump(datos,f,ensure_ascii=False,indent=2,allow_nan=False)

def guardar_csv(ruta,datos):
    with Path(ruta).open('x',encoding='utf-8',newline='') as f:datos.to_csv(f,index=False,float_format='%.17g')

def verificar_historicos():
    antes=json.loads((RAIZ/'inventario_previo.json').read_text(encoding='utf-8'))
    for nombre,v in antes.items():
        p=Path(nombre);assert p.is_file(),nombre;s=p.stat()
        assert s.st_size==v['size'] and str(s.st_mtime_ns)==v['mtime_ns'] and sha(p)==v['sha256'],nombre
    return len(antes)
