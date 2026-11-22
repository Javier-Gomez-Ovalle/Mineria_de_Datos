"""Verificación de publicación: sin fit, predicciones, métricas ni lectura de datasets."""
from pathlib import Path
import ast
import hashlib
import importlib.metadata
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def verificar():
    base = ROOT / 'fase04_modelado/recuperacion_referencia_v1_20261122'
    manifest = json.loads((base / 'MANIFIESTO_MODELO_FINAL.json').read_text(encoding='utf-8'))
    evidence = json.loads((base / 'VERIFICACION_MANIFIESTO.json').read_text(encoding='utf-8'))
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(base/'MANIFIESTO_MODELO_FINAL.json') == evidence['manifiesto_sha256']
    checked = {}
    for name, expected in manifest['sha256_archivos'].items():
        assert sha(base/name) == expected, name
        checked[name] = expected
    assert sha(base/'umbral_definitivo.json') == manifest['umbral_sha256']
    assert manifest['umbral'] == 0.9976439543869569
    inventory = json.loads((ROOT/'docs/INVENTARIO_PUBLICACION.json').read_text(encoding='utf-8'))
    public_files = [ROOT/item['ruta'] for item in inventory['archivos']]
    forbidden = [p.name for p in public_files if p.is_file() and p.suffix.lower() in ('.csv','.npy','.npz') and 'test' in p.name.lower()]
    assert not forbidden, forbidden
    count = 0
    for p in public_files:
        if p.suffix != '.py': continue
        compile(p.read_text(encoding='utf-8-sig'), str(p), 'exec')
        count += 1
    import joblib
    from fase04_preparacion.seleccion import PREDICTORES
    from fase04_preparacion.transformaciones import crear_preprocesador
    from fase04_modelado.modelos import crear_modelo
    model = joblib.load(base/'modelo_final.joblib')
    prep = joblib.load(base/'preprocesador_final.joblib')
    assert model.get_params() == manifest['parametros']
    assert model.classes_.tolist() == [0, 1]
    assert len(prep.get_feature_names_out()) == 62
    assert list(prep.feature_names_in_) == PREDICTORES
    versions = {}
    for package in ['numpy','pandas','scikit-learn','scipy','joblib','imbalanced-learn','matplotlib','Pillow','psutil','threadpoolctl','pytest','Faker']:
        try: versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError: versions[package] = None
    return dict(artefactos_verificados=checked, manifiesto_sha256=evidence['manifiesto_sha256'], python=sys.version.split()[0], versiones=versions, python_compilados_en_memoria=count, columnas=62, clases=[0,1], umbral=manifest['umbral'], entrenamiento=False, inferencia=False, metricas_recalculadas=False, datasets_leidos=False, test_distribuido=False)

if __name__ == '__main__':
    print(json.dumps(verificar(), ensure_ascii=False, indent=2))
