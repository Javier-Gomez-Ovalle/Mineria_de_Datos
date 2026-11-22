"""Recuperación autorizada: un solo fit final, sin folds ni selección de umbral."""
from pathlib import Path
import os, json, math, platform, time, traceback
import numpy as np
import pandas as pd
import scipy, sklearn, joblib
from fase04_modelado.validacion_anidada.auditoria import activar_guardia, sha, ACCESOS
from fase04_preparacion.seleccion import separar_datos
from fase04_preparacion.transformaciones import crear_preprocesador, ajustar_train, transformar
from fase04_modelado.modelos import crear_modelo
from fase04_modelado.auditoria import auditar_preprocesador

DEST=Path('fase04_modelado/recuperacion_referencia_v1_20261122')
PREV=Path('fase04_modelado/ejecucion_referencia_v1')
FROZEN=Path('fase04_modelado/referencia_congelada')
THASH='e5327bd50594edd9d1c67e5076bd53f101c9194b068911e8faf16567f7109095'
THRESHOLD=0.9976439543869569

def json_native(value):
    """Conversión exacta, recursiva y bloqueante; nunca NaN/inf ni coerción textual."""
    if isinstance(value,np.ndarray):return json_native(value.tolist())
    if isinstance(value,np.bool_):return bool(value)
    if isinstance(value,np.integer):return int(value)
    if isinstance(value,np.floating):
        result=float(value)
        if not math.isfinite(result) or type(value)(result)!=value:
            raise ValueError('Flotante NumPy no finito o no representable exactamente como float')
        return result
    if value is None or isinstance(value,(str,bool,int)):return value
    if isinstance(value,float):
        if not math.isfinite(value):raise ValueError('NaN/inf prohibidos')
        return value
    if isinstance(value,(list,tuple)):return [json_native(v) for v in value]
    if isinstance(value,dict):
        if not all(isinstance(k,str) for k in value):raise TypeError('Claves JSON deben ser strings')
        return {k:json_native(v) for k,v in value.items()}
    raise TypeError('Tipo JSON no soportado: '+str(type(value)))

def write_json(name,value):
    # Preparar y validar todo ANTES de abrir: un tipo inválido no deja JSON parcial.
    native=json_native(value);encoded=json.dumps(native,ensure_ascii=False,indent=2,allow_nan=False)
    assert json.loads(encoded)==native
    with (DEST/name).open('x',encoding='utf-8') as f:f.write(encoded)

def write_text(name,value):
    with (DEST/name).open('x',encoding='utf-8') as f:f.write(value)

def inventory():
    result={}
    for root,dirs,files in os.walk('.'):
        dirs[:]=[d for d in dirs if d not in ['.git','__pycache__','.pytest_cache','.venv','venv']]
        for name in files:
            p=Path(root)/name
            if DEST in p.parents:continue
            if 'test' in name.lower() and p.suffix.lower() in ['.csv','.npy','.joblib']:continue
            s=p.stat();result[p.as_posix()]=dict(sha256=sha(p),size=s.st_size,mtime_ns=str(s.st_mtime_ns))
    return result

def check_inventory(baseline):
    for name,v in baseline.items():
        p=Path(name);s=p.stat()
        assert s.st_size==v['size'] and str(s.st_mtime_ns)==v['mtime_ns'] and sha(p)==v['sha256'],name

def test_conversion():
    cases=[(np.int64(2**62),2**62),(np.uint64(2**64-1),2**64-1),(np.bool_(True),True),(np.float32(.25),.25),(np.float64(THRESHOLD),THRESHOLD),(np.array([1,2],dtype=np.int64),[1,2]),({'a':[np.int32(3),None]},{'a':[3,None]})]
    for v,e in cases:assert json.loads(json.dumps(json_native(v),allow_nan=False))==e
    invalid=[float('nan'),float('inf'),np.float64('-inf'),np.float32('nan'),complex(1,2),{1:'key'}]
    for v in invalid:
        try:json_native(v)
        except (TypeError,ValueError):pass
        else:raise AssertionError('Valor inválido aceptado')
    return dict(casos_validos=len(cases),rechazos_esperados=len(invalid),total=len(cases)+len(invalid),fit_de_pruebas=0)

def probabilities(model,matrix):
    col=list(model.classes_).index(1)
    return np.concatenate([model.predict_proba(matrix[i:i+512])[:,col] for i in range(0,len(matrix),512)])

def main():
    activar_guardia();start=time.perf_counter()
    assert not (DEST/'inventario_previo.json').exists(),'Destino ya utilizado'
    previous=json.loads((PREV/'MANIFIESTO_MODELO_FINAL.json').read_text(encoding='utf-8'))
    for name,h in previous['sha256_archivos'].items():assert sha(PREV/name)==h,name
    assert sha(PREV/'umbral_definitivo.json')==THASH
    threshold=json.loads((PREV/'umbral_definitivo.json').read_text(encoding='utf-8'))
    assert threshold['umbral']==THRESHOLD and threshold['f1']==0.17391304347826086
    assert [threshold[k] for k in ['TP','FP','TN','FN']]==[8,48,46221,28]
    assert sha(PREV/'predicciones_oof.csv')==threshold['oof_sha256']
    # Verificación de integridad, sin cargar OOF ni candidatos para recalcular decisiones.
    frozen_manifest=json.loads((FROZEN/'manifiesto_entrega.json').read_text(encoding='utf-8'))
    for name,h in frozen_manifest['sha256_entregables'].items():assert sha(name)==h,name
    check_inventory(json.loads((PREV/'inventario_previo.json').read_text(encoding='utf-8')))
    baseline=inventory();write_json('inventario_previo.json',baseline)
    evidence=json.loads((FROZEN/'evidencia_congelacion.json').read_text(encoding='utf-8'))
    versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,scipy=scipy.__version__,joblib=joblib.__version__)
    assert versions==evidence['versiones']==previous['versiones']
    assert sha('dataset_train_fase04.csv')==evidence['train_sha256']
    partial=(PREV/'auditoria_modelo_final.json').read_text(encoding='utf-8')
    assert partial.rstrip().endswith('"hojas_observadas":')
    tests=test_conversion();write_json('pruebas_conversion.json',tests)
    df=pd.read_csv('dataset_train_fase04.csv');x,y,keys=separar_datos(df)
    assert len(y)==46305 and int(y.sum())==36 and keys['User ID'].nunique()==1600 and keys.loc[y.eq(1),'User ID'].nunique()==34
    prep=crear_preprocesador('arbol');_,model=crear_modelo('arbol_ponderado')
    assert model.get_params()==evidence['parametros']==previous['parametros']
    matrix=ajustar_train(prep,x);audit=auditar_preprocesador(prep,x)
    assert matrix.shape==(46305,62) and list(prep.get_feature_names_out())==evidence['columnas_esperadas_full_train']
    model.fit(matrix,y)  # ÚNICO fit de modelo en esta recuperación.
    leaves=model.get_n_leaves();depth=model.get_depth()
    # Prueba directa del punto de fallo original, sin escribir otro archivo parcial.
    assert isinstance(leaves,np.integer)
    try:json.dumps({'hojas_observadas':leaves})
    except TypeError:original_error_confirmed=True
    else:raise AssertionError('No se reproduce el tipo que causó el fallo original')
    audit.update(parametros=model.get_params(),clases=model.classes_,filas_ajuste=len(y),profundidad_observada=depth,hojas_observadas=leaves,pesos_clase={str(c):len(y)/(2*int((y==c).sum())) for c in [0,1]},tipo_original_hojas=str(type(leaves)),incidencia_reproducida_sin_escritura=original_error_confirmed)
    write_json('auditoria_modelo_final.json',audit)
    for name,obj in [('preprocesador_final.joblib',prep),('modelo_final.joblib',model)]:
        with (DEST/name).open('xb') as f:joblib.dump(obj,f,compress=3)
        assert (DEST/name).stat().st_size>0
    artifact_hashes={n:sha(DEST/n) for n in ['preprocesador_final.joblib','modelo_final.joblib']}
    prep2=joblib.load(DEST/'preprocesador_final.joblib');model2=joblib.load(DEST/'modelo_final.joblib')
    assert model2.get_params()==model.get_params()==evidence['parametros']
    assert np.array_equal(model2.classes_,model.classes_) and list(model2.classes_)==[0,1]
    assert list(prep2.get_feature_names_out())==evidence['columnas_esperadas_full_train']
    hash_p=joblib.hash(prep2);matrix2=transformar(prep2,x)
    assert np.array_equal(matrix,matrix2) and joblib.hash(prep2)==hash_p
    score=probabilities(model,matrix);score2=probabilities(model2,matrix2)
    assert np.isfinite(score).all() and ((score>=0)&(score<=1)).all()
    # Tolerancia cero: la recarga del mismo estimador debe conservar scores exactamente.
    np.testing.assert_allclose(score,score2,rtol=0,atol=0)
    assert np.array_equal(score>=THRESHOLD,score2>=THRESHOLD)
    verify=dict(filas_verificadas=len(x),origen='todo train; solo equivalencia de serializacion, no evaluacion',rtol=0,atol=0,diferencia_maxima=float(np.abs(score-score2).max()),matrices_identicas=True,probabilidades_identicas=True,decisiones_identicas=True,clases=model2.classes_.tolist(),columnas=62,umbral=THRESHOLD)
    write_json('evidencia_recarga.json',verify)
    write_json('esquema_final.json',dict(predictores=list(x),columnas_transformadas=list(prep2.get_feature_names_out()),clases=model2.classes_,target='Is Account Takeover',clave=list(keys),umbral=THRESHOLD,regla='predict_proba clase 1 >= umbral'))
    # Copia byte a byte del registro original, no generación ni selección de otro umbral.
    with (DEST/'umbral_definitivo.json').open('xb') as f:f.write((PREV/'umbral_definitivo.json').read_bytes())
    assert sha(DEST/'umbral_definitivo.json')==THASH==sha(PREV/'umbral_definitivo.json')
    check_inventory(baseline)
    for name,h in previous['sha256_archivos'].items():assert sha(PREV/name)==h,name
    write_json('verificaciones.json',dict(artefactos_previos_verificados=len(previous['sha256_archivos']),historicos_intactos=len(baseline),versiones_exactas=True,train_hash_correcto=True,parametros_exactos=True,ajustes_modelo=1,ajustes_preprocesador=1,folds_ejecutados=0,selecciones_umbral_ejecutadas=0,umbral_sha256=THASH,pruebas_conversion=tests,recarga=verify,test_leido=False,test_hasheado=False,git_ejecutado=False,incidencias_nuevas=[]))
    write_json('registro_ejecucion.json',dict(fecha='2026-11-22',segundos=time.perf_counter()-start,accesos_datos=ACCESOS,fuentes_verificadas=previous['sha256_archivos']))
    report=f'''# Recuperación técnica del modelo de referencia — Fase 4

Fecha: 2026-11-22. Procedimiento referencia_arbol_ponderado_v1. **Recuperación completada; modelo serializado y verificado, test cerrado.**

## Incidencia y solución

El archivo original auditoria_modelo_final.json termina en `"hojas_observadas":`. Ese campo se obtiene de model.get_n_leaves(), que devuelve {type(leaves)!s} en este entorno. Se confirmó el TypeError de json.dumps con ese escalar tras el único ajuste final. El error no se produjo en las OOF ni en la selección de umbral. Se conserva intacto el JSON parcial y su traceback en {PREV.as_posix()}/.

La nueva función json_native convierte explícitamente enteros NumPy a int, booleanos a bool, flotantes NumPy finitos exactamente representables a float y arrays/estructuras anidadas recursivamente. Rechaza NaN, infinitos, complejos, tipos no soportados, claves no string y flotantes que perderían precisión. No sustituye inválidos por cero/null/texto. json.dumps usa allow_nan=False y valida la cadena completa antes de abrir el destino exclusivo, evitando archivos parciales ante errores de conversión. {tests['total']} casos de conversión/rechazo aprobados (7 válidos y 6 inválidos), sin ajustes de prueba.

## Integridad y configuración

Se verificaron todos los archivos del manifiesto fallido, incluidos OOF, candidatos, particiones, umbral, resultados y auditoría parcial. Se verificaron fuentes congeladas, versiones exactas, contratos y SHA de train `{evidence['train_sha256']}`. {len(baseline)} archivos históricos permitidos permanecen iguales por hash/tamaño/mtime; test se excluyó antes de inspeccionar metadatos o contenido.

Train: 46.305 eventos, 1.600 usuarios, 36 ATO y 34 usuarios positivos. Seis predictores aprobados, mediana local, binaria intacta y One-Hot aprobado; sin escalado, log1p ni ROS. **Un ajuste final del preprocesador y un ajuste final del árbol**; cero folds y cero selecciones nuevas. No se ejecutaron otros modelos ni se cambiaron parámetros.

```json
{json.dumps(model.get_params(),indent=2)}
```

Versiones:
```json
{json.dumps(versions,indent=2)}
```

El árbol recuperado tiene profundidad {int(depth)} y {int(leaves)} hojas. Estos son resultados del ajuste, no hiperparámetros nuevos. No existe artefacto del ajuste perdido con el que comparar bit a bit: reproducibilidad respaldada por fuentes/datos/semilla/versiones idénticos. No se afirma una comparación imposible con el modelo anterior en memoria.

## Umbral conservado

Umbral exacto **{THRESHOLD!r}**, regla score >= umbral. Registro copiado byte a byte, SHA-256 `{THASH}`. Se conservan F1 OOF de selección 0.17391304347826086, TP=8, FP=48, TN=46.221 y FN=28. No se recalcularon umbral ni métricas OOF.

El F1 se optimizó en OOF de tres estimadores distintos y no estima independientemente rendimiento final. El ajuste con todo train puede cambiar la escala de scores; transferir el umbral no garantiza calibración/equivalencia con OOF. La prueba de recarga compara el mismo modelo antes/después de guardar, no demuestra transferencia o generalización.

## Artefactos y recarga

| Artefacto | SHA-256 |
|---|---|
| modelo_final.joblib | {artifact_hashes['modelo_final.joblib']} |
| preprocesador_final.joblib | {artifact_hashes['preprocesador_final.joblib']} |
| umbral_definitivo.json | {THASH} |

Ambos joblib existen y tienen tamaño positivo. Se recargaron, verificando parámetros, clases [0,1] y los 62 nombres de columnas esperados. Sobre **todos los 46.305 eventos de train**, las matrices, probabilidades y decisiones coinciden exactamente. Tolerancia rtol=0, atol=0; diferencia máxima={verify['diferencia_maxima']}. No se calcularon métricas de rendimiento sobre esos scores de resustitución.

Evidencia: auditoria_modelo_final.json, evidencia_recarga.json, esquema_final.json, verificaciones.json, pruebas_conversion.json, inventario_previo.json y registro_ejecucion.json. MANIFIESTO_MODELO_FINAL.json registra parámetros, versiones, umbral y hashes; su recarga se comprueba antes de declarar completada esta recuperación. El manifiesto no se incluye en su propio hash.

## Estado final

Sin incidencias nuevas ni desviaciones. No se sobrescribió ningún archivo previo; implementación y salidas nuevas en {DEST.as_posix()}/. Sin instalaciones ni operaciones Git. Test no se abrió, leyó, inspeccionó, procesó, hasheó ni evaluó.

**Detención tras verificación.** La evaluación final exige autorización posterior e independiente. Fase 4 continúa abierta; esto no acredita un detector satisfactorio ni ganador definitivo.
'''
    write_text('INFORME_RECUPERACION_TECNICA_FASE04.md',report)
    files=[p for p in DEST.iterdir() if p.is_file()]
    manifest=dict(fecha='2026-11-22',procedimiento='referencia_arbol_ponderado_v1',estado='RECUPERADO_CONGELADO_SIN_EVALUAR_TEST',umbral=THRESHOLD,umbral_sha256=THASH,train_sha256=evidence['train_sha256'],parametros=model.get_params(),versiones=versions,metricas_oof_historicas_no_recalculadas=previous['metricas_oof_seleccion'],artefactos=artifact_hashes,equivalencia=verify,historicos_intactos=len(baseline),ajustes_finales_repetidos=1,folds_repetidos=0,umbral_recalculado=False,test_leido=False,test_evaluado=False,sha256_archivos={p.name:sha(p) for p in files})
    write_json('MANIFIESTO_MODELO_FINAL.json',manifest)
    loaded=json.loads((DEST/'MANIFIESTO_MODELO_FINAL.json').read_text(encoding='utf-8'))
    assert loaded==json_native(manifest)
    for name,h in loaded['sha256_archivos'].items():assert sha(DEST/name)==h,name
    write_json('VERIFICACION_MANIFIESTO.json',dict(manifiesto_sha256=sha(DEST/'MANIFIESTO_MODELO_FINAL.json'),json_valido=True,contenido_identico=True,hashes_archivos_verificados=len(loaded['sha256_archivos']),test_evaluado=False))
    print(json.dumps(dict(estado=loaded['estado'],artefactos=artifact_hashes,umbral=THRESHOLD,verificaciones_conversion=tests,historicos=len(baseline),hojas=int(leaves),profundidad=int(depth),diferencia_maxima=verify['diferencia_maxima']),ensure_ascii=True))

if __name__=='__main__':
    try:main()
    except Exception:
        if not (DEST/'INCIDENCIA_RECUPERACION.txt').exists():write_text('INCIDENCIA_RECUPERACION.txt',traceback.format_exc())
        raise
