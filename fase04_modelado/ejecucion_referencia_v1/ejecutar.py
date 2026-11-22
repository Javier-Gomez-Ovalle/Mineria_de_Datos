"""Ejecución autorizada de referencia_arbol_ponderado_v1. Sin acceso a test.

Persistencia exclusiva; cualquier excepción detiene la ejecución y se registra.
No ejecutar de nuevo sobre este destino.
"""
from pathlib import Path
import os, json, time, platform, traceback
import numpy as np
import pandas as pd
import scipy, sklearn, joblib
from fase04_modelado.validacion_anidada.auditoria import activar_guardia, sha, hash_indices, ACCESOS
from fase04_modelado.validacion_anidada.particiones import construir_particiones, describir
from fase04_modelado.validacion_anidada.ajuste import AjustadorVariante
from fase04_modelado.validacion_anidada.seleccion_umbral import seleccionar_umbral
from fase04_modelado.validacion_anidada.evaluacion import medir
from fase04_modelado.modelos import crear_modelo
from fase04_modelado.auditoria import auditar_preprocesador
from fase04_preparacion.seleccion import separar_datos
from fase04_preparacion.transformaciones import crear_preprocesador, ajustar_train, transformar

DEST = Path('fase04_modelado/ejecucion_referencia_v1')
FROZEN = Path('fase04_modelado/referencia_congelada')
CHECKS = []

def js(name, value):
    with (DEST/name).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)

def csv(name, value):
    with (DEST/name).open('x', encoding='utf-8', newline='') as f:
        value.to_csv(f, index=False, float_format='%.17g')

def txt(name, value):
    with (DEST/name).open('x', encoding='utf-8') as f: f.write(value)

def check(label, condition):
    if not condition: raise AssertionError(label)
    CHECKS.append(label)

def tabla(frame):
    return '| '+' | '.join(map(str,frame.columns))+' |\n|'+'|'.join(['---']*len(frame.columns))+'|\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))+'\n'

def snapshot():
    out={}
    for root, dirs, files in os.walk('.'):
        dirs[:]=[d for d in dirs if d not in ['.git','__pycache__','.pytest_cache','.venv','venv']]
        for name in files:
            p=Path(root)/name
            if DEST in p.parents: continue
            if 'test' in name.lower() and p.suffix.lower() in ['.csv','.npy','.joblib']: continue
            s=p.stat();out[p.as_posix()]=dict(size=s.st_size,mtime_ns=str(s.st_mtime_ns),sha256=sha(p))
    return out

def scores(model, matrix):
    col=list(model.classes_).index(1)
    return np.concatenate([model.predict_proba(matrix[i:i+512])[:,col] for i in range(0,len(matrix),512)])

def main():
    activar_guardia();start=time.perf_counter()
    check('Destino nuevo sin resultados previos',not (DEST/'inventario_previo.json').exists())
    old=json.loads((FROZEN/'inventario_previo.json').read_text(encoding='utf-8'))
    m=json.loads((FROZEN/'manifiesto_entrega.json').read_text(encoding='utf-8'))
    for name,h in m['sha256_entregables'].items():check('Hash congelado '+name,sha(name)==h)
    for name,v in old.items():
        if name=='README_ESTADO_FASE04.md':continue
        p=Path(name);s=p.stat();check('Integridad histórica '+name,s.st_size==v['size'] and str(s.st_mtime_ns)==v['mtime_ns'] and sha(p)==v['sha256'])
    baseline=snapshot();js('inventario_previo.json',baseline)
    evidence=json.loads((FROZEN/'evidencia_congelacion.json').read_text(encoding='utf-8'))
    versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,scipy=scipy.__version__,joblib=joblib.__version__)
    check('Versiones exactas',versions==evidence['versiones'])
    check('SHA train autorizado',sha('dataset_train_fase04.csv')==evidence['train_sha256'])
    df=pd.read_csv('dataset_train_fase04.csv');x,y,keys=separar_datos(df);users=keys['User ID']
    check('Contrato población train',len(y)==46305 and int(y.sum())==36 and users.nunique()==1600 and users[y.eq(1)].nunique()==34)
    check('User ID entero int64',str(users.dtype)=='int64')
    params=crear_modelo('arbol_ponderado')[1].get_params();check('Parámetros modelo exactos',params==evidence['parametros'])
    js('configuracion_ejecucion.json',dict(procedimiento='referencia_arbol_ponderado_v1',fecha='2026-11-21',versiones=versions,parametros=params,train_sha256=evidence['train_sha256'],especificacion_sha256=sha('PROCEDIMIENTO_REFERENCIA_CONGELADO_FASE04.md'),predictores=list(x),n_splits=3,semilla=42,criterio='F1 OOF por evento; desempate distancia a 0.5, después mayor',test_autorizado=False))
    parts=construir_particiones(y,users,3);repeat=construir_particiones(y,users,3)
    for (a,b),(c,d) in zip(parts,repeat):check('Partición reproducible',np.array_equal(a,c) and np.array_equal(b,d))
    js('particiones.json',[dict(fold=i,ajuste=a.tolist(),validacion=b.tolist()) for i,(a,b) in enumerate(parts,1)])
    sc=np.full(len(y),np.nan);coverage=np.zeros(len(y),int);folds=np.zeros(len(y),int);audits=[];dist=[]
    for i,(a,b) in enumerate(parts,1):
        check(f'Usuarios separados fold {i}',not set(users.iloc[a])&set(users.iloc[b]))
        s,audit=AjustadorVariante('arbol_ponderado').predecir(x.iloc[a],y.iloc[a],x.iloc[b])
        check(f'Configuración efectiva fold {i}',audit['parametros']==params and not audit['ros_aplicado'])
        sc[b]=s;coverage[b]+=1;folds[b]=i;audits.append(dict(fold=i,**audit));dist.append(describir(y,users,a,b,0,i))
        print(f'Fold {i}/3 completado: {len(a)} ajuste, {len(b)} validacion.',flush=True)
    check('Una OOF por evento',bool((coverage==1).all() and np.isfinite(sc).all()))
    check('Un fold por usuario',pd.DataFrame(dict(usuario=users,fold=folds)).groupby('usuario').fold.nunique().eq(1).all())
    csv('distribucion_folds.csv',pd.DataFrame(dist));js('auditoria_folds.json',audits)
    oof=keys.copy();oof.insert(0,'evento_id',np.arange(len(y)));oof['fold']=folds;oof['y_true']=y;oof['score']=sc
    csv('predicciones_oof.csv',oof)
    loaded=pd.read_csv(DEST/'predicciones_oof.csv',float_precision='round_trip')
    check('Roundtrip OOF exacto',np.array_equal(loaded.score,sc) and np.array_equal(loaded.y_true,y))
    for c in keys:check('Trazabilidad OOF '+c,np.array_equal(loaded[c],keys[c]))
    choice,candidates=seleccionar_umbral(loaded.y_true,loaded.score);t=choice['umbral'];csv('candidatos_umbral.csv',candidates)
    js('umbral_definitivo.json',dict(procedimiento='referencia_arbol_ponderado_v1',**choice,oof_sha256=sha(DEST/'predicciones_oof.csv'),regla='score >= umbral',origen='OOF de tres modelos internos distintos; no calibrados',valor_final_congelado=True))
    threshold_hash=sha(DEST/'umbral_definitivo.json')
    pred=(sc>=t).astype(int);metrics=medir(y,sc,pred,users)
    check('Matriz coincide con selección',all(metrics[k]==choice[k] for k in ['TP','FP','TN','FN']))
    again,_=seleccionar_umbral(loaded.y_true,loaded.score);check('Selección reproducible sin ajuste nuevo',again==choice)
    js('metricas_oof_seleccion.json',metrics);oof['pred_umbral']=pred;csv('decisiones_oof.csv',oof)
    freq=[];summaries=[];foldmetrics=[]
    for f in [0,1,2,3]:
        g=oof if f==0 else oof[oof.fold.eq(f)]
        for value,v in g.groupby('score'):
            freq.append(dict(fold=f,score=value,eventos=len(v),ATO=int(v.y_true.sum()),negativos=int((v.y_true==0).sum())))
        summaries.append(dict(fold=f,n=len(g),unicos=g.score.nunique(),ceros=int(g.score.eq(0).sum()),unos=int(g.score.eq(1).sum()),**{str(k):float(v) for k,v in g.score.describe(percentiles=[.01,.25,.5,.75,.9,.99]).items()}))
        if f:foldmetrics.append(dict(fold=f,**medir(g.y_true,g.score,g.pred_umbral,g['User ID'])))
    csv('valores_probabilidades_oof.csv',pd.DataFrame(freq));csv('distribucion_probabilidades_oof.csv',pd.DataFrame(summaries));csv('metricas_por_fold_umbral_seleccionado.csv',pd.DataFrame(foldmetrics))
    # Umbral ya congelado antes del ajuste final. Sin comparaciones entre familias.
    prep=crear_preprocesador('arbol');t0=time.perf_counter();matrix=ajustar_train(prep,x);finalaudit=auditar_preprocesador(prep,x)
    check('62 columnas finales y nombres exactos',list(prep.get_feature_names_out())==evidence['columnas_esperadas_full_train'] and matrix.shape==(46305,62))
    _,model=crear_modelo('arbol_ponderado');model.fit(matrix,y)
    check('Parámetros finales exactos',model.get_params()==params)
    finalaudit.update(parametros=model.get_params(),clases=model.classes_.tolist(),pesos_clase={str(c):float(len(y)/(2*(y==c).sum())) for c in [0,1]},filas_ajuste=len(y),n_features_in=int(model.n_features_in_),profundidad_observada=model.get_depth(),hojas_observadas=model.get_n_leaves(),ajuste_indices_sha256=hash_indices(x.index),segundos_ajuste_final=time.perf_counter()-t0)
    js('auditoria_modelo_final.json',finalaudit)
    for name,obj in [('preprocesador_final.joblib',prep),('modelo_final.joblib',model)]:
        with (DEST/name).open('xb') as f:joblib.dump(obj,f,compress=3)
    prep2=joblib.load(DEST/'preprocesador_final.joblib');model2=joblib.load(DEST/'modelo_final.joblib')
    prep_hash=joblib.hash(prep2);matrix2=transformar(prep2,x)
    check('Transformador serializado idéntico en todo train',np.array_equal(matrix,matrix2) and joblib.hash(prep2)==prep_hash)
    s1=scores(model,matrix);s2=scores(model2,matrix2)
    check('Probabilidades serializadas idénticas en todo train',np.array_equal(s1,s2))
    check('Decisiones serializadas idénticas en todo train',np.array_equal(s1>=t,s2>=t))
    check('Umbral inmutable tras ajuste final',sha(DEST/'umbral_definitivo.json')==threshold_hash)
    # No se publican métricas de resustitución como rendimiento: scores finales solo verifican serialización.
    js('esquema_final.json',dict(predictores=list(x),columnas_transformadas=list(prep.get_feature_names_out()),clases=model.classes_.tolist(),target='Is Account Takeover',clave=list(keys),regla='predict_proba clase 1 >= umbral',umbral=t))
    for name,v in baseline.items():
        p=Path(name);s=p.stat();check('Integridad posterior '+name,s.st_size==v['size'] and str(s.st_mtime_ns)==v['mtime_ns'] and sha(p)==v['sha256'])
    csv('trazabilidad_usuarios_folds.csv',pd.DataFrame(dict(usuario=users,fold=folds,usuario_con_ato=y)).groupby('usuario',sort=True).agg(fold=('fold','first'),usuario_con_ato=('usuario_con_ato','max'),eventos=('fold','size')).reset_index())
    js('verificaciones.json',dict(comprobaciones_aprobadas=len(CHECKS),detalle=CHECKS,ajustes_modelo=4,ajustes_preprocesador=4,historicos_intactos=len(baseline),test_leido=False,test_hasheado=False,git_ejecutado=False,instalaciones=False,incidencias=[],serializacion_validada_en='46305 eventos de train',reproducibilidad='particiones y selección repetidas sin fit; no se repitieron los cuatro entrenamientos'))
    js('registro_ejecucion.json',dict(segundos=time.perf_counter()-start,ajustes_internos=3,ajustes_finales=1,accesos_datos=ACCESOS,fecha='2026-11-21',test_evaluado=False))
    txt('RESULTADOS_SELECCION_UMBRAL.md',f'''# Selección del umbral de referencia

Fecha: 2026-11-21. Procedimiento referencia_arbol_ponderado_v1.

Umbral definitivo **{t!r}**, decisión score >= umbral. F1 OOF **{metrics['f1']:.12g}**, Precision {metrics['precision']:.12g}, Recall {metrics['recall']:.12g}.

| Real / predicción | No ATO | ATO |
|---|---:|---:|
| No ATO | {metrics['TN']} | {metrics['FP']} |
| ATO | {metrics['FN']} | {metrics['TP']} |

{len(candidates)} candidatos: scores únicos, 0, 0.5 y np.nextafter(1,inf). F1 exacto = {choice['f1_numerador']}/{choice['f1_denominador']}. Empates máximos: {choice['umbrales_empatados']}. Desempate por distancia a 0.5, luego mayor. Política: {choice['politica']}. Tabla completa: candidatos_umbral.csv; registro inmutable: umbral_definitivo.json.

Las 46.305 OOF proceden de **tres modelos diferentes**, cada uno ajustado sin los usuarios de su validación. Sus puntuaciones no tienen calibración común garantizada. Se maximizó F1 sobre la concatenación por evento conforme al protocolo, no la media de folds.

**Este F1 se utilizó para seleccionar el umbral: no es una estimación independiente del rendimiento final.** Las métricas por fold con este umbral también son descriptivas porque el umbral fue elegido usando las etiquetas OOF de los tres folds.

Distribución de scores (fold 0: concatenación):

{tabla(pd.DataFrame(summaries))}

Todos los valores exactos y frecuencias por clase/fold están en valores_probabilidades_oof.csv. Todas las probabilidades por evento están en predicciones_oof.csv. AP concatenada OOF = {metrics['average_precision']:.12g}; no equivale a media AP por fold. No se utiliza AP para elegir t.

El árbol final se ajustó con todo train. Cambian soporte, pesos balanced y particiones del árbol: no está garantizada equivalencia entre sus probabilidades y las OOF. El umbral se transfiere sin calibración ni retoques; la equivalencia tras serializar solo comprueba el mismo modelo final, no su equivalencia con los tres modelos internos. No se sustituyó el umbral por una media histórica ni se consultó test.
''')
    txt('INFORME_EJECUCION_REFERENCIA_FASE04.md',f'''# Ejecución controlada del procedimiento de referencia

Fecha: 2026-11-21. referencia_arbol_ponderado_v1. **Modelo final entrenado y congelado; test cerrado; Fase 4 abierta.**

Se ejecutaron exactamente tres árboles/preprocesadores internos y un árbol/preprocesador final. No se probaron otros algoritmos, parámetros, semillas ni reglas. Sin incidencias ni desviaciones.

## Datos y preflight

Train: dataset_train_fase04.csv; SHA-256 `{evidence['train_sha256']}`. 46.305 eventos, 1.600 usuarios, 36 ATO, 34 usuarios positivos. Se verificaron hashes congelados, contratos, versiones y {len(baseline)} archivos históricos antes/después. Test se excluyó antes de stat/hash y se protegió con guardia de acceso. No se modificaron históricos, README, datos ni código previo; sin Git ni instalaciones.

## Configuración efectiva

```json
{json.dumps(params,indent=2)}
```

Versiones:
```json
{json.dumps(versions,indent=2)}
```

Seis entradas, en orden: {', '.join(x.columns)}. Mediana local en las tres numéricas, indicador intacto, imputación categórica Desconocido y One-Hot denso handle_unknown=ignore. Sin log1p, escalado ni ROS. Cada fold aprendió sus categorías/medianas; final sobre todo train, matriz 46.305×62. Esquema completo en esquema_final.json; medianas, categorías, pesos y dimensiones en auditoria_folds.json y auditoria_modelo_final.json. Clave e identificadores solo para trazabilidad.

## Folds y reproducibilidad

StratifiedKFold sobre usuarios ordenados y estrato max(target), n_splits=3, shuffle=True, random_state=42; expansión a todos los eventos. Ningún usuario cruza ajuste/validación; una OOF por evento y un fold por usuario.

{tabla(pd.DataFrame(dist))}

Se reconstruyeron las particiones dos veces con igualdad exacta. Scores y claves OOF sobreviven al CSV con precisión round_trip. La selección se repitió sobre OOF guardadas, con igualdad exacta de decisión y empates. No se repitieron entrenamientos para perseguir resultados. El script ejecutar.py conserva la implementación y falla ante salidas existentes; una réplica requeriría destino nuevo y mantener fuentes/versiones congeladas.

## Selección y transferencia

Umbral `{t!r}`; F1 de selección {metrics['f1']:.12g}; TP={metrics['TP']}, FP={metrics['FP']}, TN={metrics['TN']}, FN={metrics['FN']}. Detalle en RESULTADOS_SELECCION_UMBRAL.md. Este F1 no es validación independiente: se optimizó sobre las mismas OOF. Scores OOF proceden de tres estimadores; trasladar t al ajuste final completo no garantiza equivalencia de escalas ni de calibración. No se interpretan probabilidades ponderadas como riesgos calibrados.

## Artefactos y verificación

preprocesador_final.joblib y modelo_final.joblib son nuevos. Se recargaron y compararon transformaciones, probabilidades y decisiones en todos los eventos de train: igualdad exacta. La verificación no es evaluación de generalización y no se reporta F1 de resustitución. El umbral fue guardado antes del ajuste final y su hash permaneció intacto.

MANIFIESTO_MODELO_FINAL.json incluye hashes de artefactos y evidencia; no incluye su propio hash para evitar autorreferencia. Configuración, selección, OOF, particiones, auditorías, inventario y verificaciones permiten reproducir y comprobar el procedimiento. {len(CHECKS)} comprobaciones explícitas aprobadas (incluyen hashes por archivo); no se ejecutó pytest ni se cuentan estas comprobaciones como tests independientes.

La elección del árbol es referencia académica retrospectiva por F1 histórico, no ganador demostrado. Persisten pocos positivos, solapamiento de predictores, limitaciones de representación e inestabilidad. No se ha probado rendimiento final ni aptitud para producción.

**Condición de parada cumplida.** No se abrió, leyó, inspeccionó, hasheó ni evaluó test. No hay autorización para evaluarlo. El siguiente paso es revisión de entregables y autorización posterior explícita; hasta entonces no ejecutar evaluación final.
''')
    files=[p for p in DEST.iterdir() if p.is_file()]
    js('MANIFIESTO_MODELO_FINAL.json',dict(procedimiento='referencia_arbol_ponderado_v1',fecha='2026-11-21',estado='entrenado_congelado_sin_evaluar_test',umbral=t,parametros=params,versiones=versions,train_sha256=evidence['train_sha256'],metricas_oof_de_seleccion_no_independientes=metrics,ajustes=4,historicos_intactos=len(baseline),test_leido=False,test_evaluado=False,incidencias=[],sha256_archivos={p.name:sha(p) for p in files}))
    print(json.dumps(dict(umbral=t,metricas_oof=metrics,artefactos={n:sha(DEST/n) for n in ['preprocesador_final.joblib','modelo_final.joblib','umbral_definitivo.json']},historicos=len(baseline)),ensure_ascii=True),flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        path=DEST/'INCIDENCIA_EJECUCION.txt'
        if not path.exists():txt(path.name,traceback.format_exc())
        raise
