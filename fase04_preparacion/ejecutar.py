"""CLI reproducible: python -B -m fase04_preparacion.ejecutar.

Escritura exclusiva en una carpeta nueva. Nunca entrena modelos.
"""
import hashlib
import json
from pathlib import Path
import platform
import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from .seleccion import separar_datos, CATEGORICAS, NUMERICAS, PREDICTORES, CLAVE
from .transformaciones import REPRESENTACIONES, crear_preprocesador, ajustar_train, transformar


def sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def ejecutar(raiz=Path('.'), salida=None):
    raiz = Path(raiz)
    salida = Path(salida) if salida is not None else raiz / 'artefactos_preprocesamiento_fase04'
    if salida.exists():
        raise FileExistsError(f'No se sobrescriben artefactos: {salida}')
    rutas = {s: raiz / f'dataset_{s}_fase04.csv' for s in ('train', 'test')}
    hashes = {s: sha256(p) for s, p in rutas.items()}
    train = pd.read_csv(rutas['train'])
    test = pd.read_csv(rutas['test'])
    if len(train) != 46305 or len(test) != 11115 or train.shape[1] != 35 or list(train) != list(test):
        raise ValueError('Particion no esperada')
    if set(train['User ID']) & set(test['User ID']):
        raise ValueError('Usuarios compartidos')
    x_train, y_train, claves_train = separar_datos(train)
    x_test, y_test, claves_test = separar_datos(test)
    if (y_train.sum(), y_test.sum()) != (36, 9):
        raise ValueError('Conteos de target no esperados')
    # Toda decision de seleccion esta fijada en seleccion.py antes de leer test.
    modelos, matrices, metadatos = {}, {}, {}
    for nombre in REPRESENTACIONES:
        prep = crear_preprocesador(nombre)
        a = ajustar_train(prep, x_train)
        huella_antes = joblib.hash(prep)
        b = transformar(prep, x_test)
        if joblib.hash(prep) != huella_antes:
            raise RuntimeError('Transformar test altero el preprocesador')
        otro = crear_preprocesador(nombre)
        np.testing.assert_array_equal(a, ajustar_train(otro, x_train))
        np.testing.assert_array_equal(b, transformar(otro, x_test))
        modelos[nombre] = prep
        matrices[nombre] = {'train': a, 'test': b}
        categorias = prep.named_transformers_['cat'].named_steps['onehot'].categories_
        metadatos[nombre] = {
            'columnas': prep.get_feature_names_out().tolist(),
            'categorias': {c: v.tolist() for c, v in zip(CATEGORICAS, categorias)},
            'medianas_train': prep.named_transformers_['num'].named_steps['imputar'].statistics_.tolist(),
            'formas': {'train': list(a.shape), 'test': list(b.shape)},
            'fit_test': False, 'reproducible': True,
        }
        if nombre == 'distancias':
            scaler = prep.named_transformers_['num'].named_steps['escalar']
            metadatos[nombre]['media_log_train'] = scaler.mean_.tolist()
            metadatos[nombre]['escala_log_train'] = scaler.scale_.tolist()
    # Las escrituras solo empiezan despues de validar todas las matrices.
    salida.mkdir()
    for nombre, prep in modelos.items():
        with (salida / f'preprocesador_{nombre}_fase04.joblib').open('xb') as f:
            joblib.dump(prep, f)
        cargado = joblib.load(salida / f'preprocesador_{nombre}_fase04.joblib')
        for s, x in [('train', x_train), ('test', x_test)]:
            matriz = matrices[nombre][s]
            ruta = salida / f'X_{s}_{nombre}_fase04.npy'
            with ruta.open('xb') as f:
                np.save(f, matriz, allow_pickle=False)
            np.testing.assert_array_equal(np.load(ruta, allow_pickle=False), matriz)
            np.testing.assert_array_equal(transformar(cargado, x), matriz)
    for s, y, claves in [('train', y_train, claves_train), ('test', y_test, claves_test)]:
        with (salida / f'y_{s}_fase04.npy').open('xb') as f:
            np.save(f, y.to_numpy(), allow_pickle=False)
        trazabilidad = claves.copy()
        trazabilidad.insert(0, 'fila_matriz', np.arange(len(claves)))
        trazabilidad.to_csv(salida / f'trazabilidad_{s}_fase04.csv', index=False, mode='x')
        pd.testing.assert_frame_equal(pd.read_csv(salida / f'trazabilidad_{s}_fase04.csv'), trazabilidad)
        np.testing.assert_array_equal(np.load(salida / f'y_{s}_fase04.npy'), y)
    if hashes != {s: sha256(p) for s, p in rutas.items()}:
        raise RuntimeError('Origen modificado')
    manifest = {
        'origen_sha256': hashes,
        'versiones': {'python': platform.python_version(), 'pandas': pd.__version__,
                     'numpy': np.__version__, 'scipy': scipy.__version__, 'sklearn': sklearn.__version__, 'joblib': joblib.__version__},
        'predictores': PREDICTORES, 'representaciones': metadatos,
        'perfil_train': {c: {'tipo': str(train[c].dtype), 'nulos': int(train[c].isna().sum()),
                             'distintos': int(train[c].nunique())} for c in train},
        'desconocidos_test_solo_diagnostico': {c: int((~x_test[c].isin(x_train[c].dropna().unique()) & x_test[c].notna()).sum()) for c in CATEGORICAS},
        'integridad': {'usuarios_compartidos': 0, 'filas_train': len(train), 'filas_test': len(test),
                      'target_fuera_X': True, 'sin_remuestreo': True, 'fuentes_intactas': True},
        'artefactos_sha256': {p.name: sha256(p) for p in salida.iterdir() if p.is_file()},
    }
    with (salida / 'manifiesto_fase04.json').open('x', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(json.dumps({'salida': str(salida), 'formas': {k: v['formas'] for k, v in metadatos.items()}}))
    return manifest


if __name__ == '__main__':
    ejecutar()
