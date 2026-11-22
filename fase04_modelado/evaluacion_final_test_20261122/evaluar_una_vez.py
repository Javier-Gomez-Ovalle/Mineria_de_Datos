"""Evaluación final autorizada, una inferencia, sin ajuste ni optimización.

El marcador exclusivo impide volver a ejecutar este procedimiento en el destino.
El test se lee como bytes una vez para hash y luego se analiza desde memoria.
"""
from pathlib import Path
from io import BytesIO
from datetime import datetime, timezone, timedelta
import os, sys, json, hashlib, platform, traceback
import numpy as np
import pandas as pd
import scipy, sklearn, joblib
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, average_precision_score, roc_auc_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from fase04_preparacion.seleccion import separar_datos, PREDICTORES

OUT=Path('fase04_modelado/evaluacion_final_test_20261122')
REF=Path('fase04_modelado/recuperacion_referencia_v1_20261122')
TEST=Path('dataset_test_fase04.csv')
EXPECTED_TEST='90c50ab404c3fcef6cc33e59387aec4ac405f41200e6aa61c0f8bf1db43c72fa'
EXPECTED={'modelo_final.joblib':'d23a2a0f93d64682931608829a030e9615be43990e4ae43d99262b5a9254ff5e','preprocesador_final.joblib':'01fbfd1f162dda4c7e31946da3e4cc19e87d9badfac235d662345369096168c6','umbral_definitivo.json':'e5327bd50594edd9d1c67e5076bd53f101c9194b068911e8faf16567f7109095'}
T=0.9976439543869569
COUNTS={'lecturas_archivo_test':0,'cargas_dataframe_test':0,'transformaciones_test':0,'inferencias_test':0,'evaluaciones_metricas':0,'intentos_fit':0}
CHECKS=[]

def now():return datetime.now(timezone(timedelta(hours=-5))).isoformat()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(name,value):
    encoded=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)
    with (OUT/name).open('x',encoding='utf-8') as f:f.write(encoded)
def textfile(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:f.write(value)
def check(name,ok):
    if not bool(ok):raise AssertionError(name)
    CHECKS.append(name)

def access_guard(event,args):
    if event!='open' or not isinstance(args[0],(str,bytes,Path)):return
    p=Path(os.fsdecode(args[0]));name=p.name.lower()
    if 'test' in name and p.suffix.lower() in ['.csv','.npy','.joblib']:
        if p.resolve()==TEST.resolve():
            if COUNTS['lecturas_archivo_test']!=0:raise PermissionError('Segunda apertura de test prohibida')
            COUNTS['lecturas_archivo_test']+=1
        elif OUT.resolve() not in p.resolve().parents:raise PermissionError('Artefacto test no autorizado')

def no_fit(*args,**kwargs):
    COUNTS['intentos_fit']+=1
    raise RuntimeError('fit y fit_transform prohibidos en evaluacion final')

def inventory():
    result={}
    for root,dirs,files in os.walk('.'):
        dirs[:]=[d for d in dirs if d not in ['.git','__pycache__','.pytest_cache','.venv','venv']]
        for name in files:
            p=Path(root)/name
            if OUT in p.parents:continue
            if 'test' in name.lower() and p.suffix.lower() in ['.csv','.npy','.joblib']:continue
            s=p.stat();result[p.as_posix()]=dict(size=s.st_size,mtime_ns=str(s.st_mtime_ns),sha256=sha(p))
    return result

def main():
    sys.addaudithook(access_guard)
    save('INICIO_EVALUACION_UNICA.json',dict(inicio=now(),procedimiento='referencia_arbol_ponderado_v1',advertencia='No reejecutar: incluso si falla debe documentarse la incidencia.',autorizacion='Adjunto 50422d45-422d-4786-9fba-2671a6d18e57'))
    started=now();baseline=inventory();save('INVENTARIO_PREVIO.json',baseline)
    split=Path('INFORME_PARTICION_FASE04.md').read_text(encoding='utf-8')
    check('Ruta y SHA test documentados en informe de particion', '`dataset_test_fase04.csv`' in split and EXPECTED_TEST in split)
    for name,h in EXPECTED.items():check('SHA congelado '+name,sha(REF/name)==h)
    proof=json.loads((REF/'VERIFICACION_MANIFIESTO.json').read_text(encoding='utf-8'))
    manifest_hash=sha(REF/'MANIFIESTO_MODELO_FINAL.json')
    check('SHA manifiesto congelado',manifest_hash==proof['manifiesto_sha256'])
    manifest=json.loads((REF/'MANIFIESTO_MODELO_FINAL.json').read_text(encoding='utf-8'))
    for name,h in manifest['sha256_archivos'].items():check('Entrada manifiesto '+name,sha(REF/name)==h)
    check('Identidad procedimiento',manifest['procedimiento']=='referencia_arbol_ponderado_v1')
    check('Identidad modelo y preprocesador',manifest['artefactos']=={n:EXPECTED[n] for n in ['modelo_final.joblib','preprocesador_final.joblib']})
    threshold=json.loads((REF/'umbral_definitivo.json').read_text(encoding='utf-8'))
    check('Umbral exacto en JSON y manifiesto',threshold['umbral']==T==manifest['umbral'])
    versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,scipy=scipy.__version__,joblib=joblib.__version__)
    check('Versiones congeladas',versions==manifest['versiones'])
    model=joblib.load(REF/'modelo_final.joblib');prep=joblib.load(REF/'preprocesador_final.joblib')
    check('Tipos artefactos',isinstance(model,DecisionTreeClassifier) and isinstance(prep,ColumnTransformer))
    frozen=json.loads(Path('fase04_modelado/referencia_congelada/evidencia_congelacion.json').read_text(encoding='utf-8'))
    check('Parametros exactos',model.get_params()==manifest['parametros']==frozen['parametros'])
    check('Seis predictores y orden',list(prep.feature_names_in_)==PREDICTORES and len(PREDICTORES)==6)
    check('62 columnas transformadas',list(prep.get_feature_names_out())==frozen['columnas_esperadas_full_train'] and model.n_features_in_==62)
    check('Clases binarias',np.array_equal(model.classes_,np.array([0,1])))
    check('SHA train solo para comprobar separacion',sha('dataset_train_fase04.csv')==manifest['train_sha256'])
    train_users=pd.read_csv('dataset_train_fase04.csv',usecols=['User ID'])['User ID']
    train_columns=list(pd.read_csv('dataset_train_fase04.csv',nrows=0).columns)
    # Única lectura física del archivo test. Su hash se verifica antes de parsear datos.
    raw=TEST.read_bytes();test_hash=hashlib.sha256(raw).hexdigest()
    check('SHA test autorizado',test_hash==EXPECTED_TEST)
    save('PREFLIGHT_APROBADO.json',dict(fecha_hora=now(),hashes={**EXPECTED,'MANIFIESTO_MODELO_FINAL.json':manifest_hash,'test':test_hash},versiones=versions,comprobaciones=CHECKS.copy(),test_parseado=False))
    for cls in [DecisionTreeClassifier,ColumnTransformer,Pipeline,SimpleImputer,OneHotEncoder]:
        cls.fit=no_fit
        if hasattr(cls,'fit_transform'):cls.fit_transform=no_fit
    COUNTS['cargas_dataframe_test']+=1;df=pd.read_csv(BytesIO(raw));del raw
    check('Dimensiones y esquema',df.shape==(11115,35) and list(df.columns)==train_columns)
    x,y,keys=separar_datos(df);users=keys['User ID']
    check('Conteos test esperados',users.nunique()==400 and int(y.sum())==9 and users[y.eq(1)].nunique()==9)
    check('Usuarios sin solapamiento train/test',not set(users)&set(train_users))
    check('User ID entero',str(users.dtype)=='int64')
    prep_state=joblib.hash(prep);model_state=joblib.hash(model)
    COUNTS['transformaciones_test']+=1;matrix=prep.transform(x)
    check('Matriz de inferencia valida',matrix.shape==(11115,62) and np.isfinite(matrix).all())
    save('INFERENCIA_INICIADA.json',dict(fecha_hora=now(),filas=len(y),umbral=T,regla='score >= umbral',llamadas_previstas=1))
    COUNTS['inferencias_test']+=1;prob=model.predict_proba(matrix)
    check('Probabilidades validas',prob.shape==(11115,2) and np.isfinite(prob).all() and ((prob>=0)&(prob<=1)).all())
    score=prob[:,list(model.classes_).index(1)];pred=(score>=T).astype(np.int8)
    check('Artefactos en memoria inmutables',joblib.hash(prep)==prep_state and joblib.hash(model)==model_state)
    predictions=pd.DataFrame(dict(evento_id=np.arange(len(y)),probabilidad_positiva=score,prediccion=pred,etiqueta_real=y.to_numpy()))
    with (OUT/'PREDICCIONES_TEST.csv').open('x',encoding='utf-8',newline='') as f:predictions.to_csv(f,index=False,float_format='%.17g')
    COUNTS['evaluaciones_metricas']+=1
    tn,fp,fn,tp=map(int,confusion_matrix(y,pred,labels=[0,1]).ravel())
    metrics=dict(TP=tp,FP=fp,TN=tn,FN=fn,precision=float(precision_score(y,pred,zero_division=0)),recall=float(recall_score(y,pred,zero_division=0)),f1=float(f1_score(y,pred,zero_division=0)),average_precision=float(average_precision_score(y,score)),roc_auc=float(roc_auc_score(y,score)),f2=float(5*tp/(5*tp+4*fn+fp)) if 5*tp+4*fn+fp else 0.,especificidad=float(tn/(tn+fp)),FPR=float(fp/(fp+tn)),alertas=int(pred.sum()))
    positives=set(users[y.eq(1)]);detected=set(users[(y.to_numpy()==1)&(pred==1)]);fpusers=set(users[(y.to_numpy()==0)&(pred==1)])
    usermetrics=dict(usuarios_totales=400,usuarios_con_ato=9,usuarios_ato_detectados=len(detected),usuarios_ato_omitidos=len(positives-detected),usuarios_sin_ato_con_alerta_falsa=len(fpusers-positives),usuarios_con_algun_fp=len(fpusers),usuarios_con_ato_y_algun_fp=len(fpusers&positives),usuarios_sin_ato_y_algun_fp=len(fpusers-positives))
    check('Coherencia conteos calculados',tp+fn==9 and tn+fp==11106 and len(detected)+len(positives-detected)==9)
    # Históricos solo como contexto, sin recomputar predicciones o métricas.
    historical=pd.read_csv('fase04_modelado/validacion_anidada/resultados/metricas_globales.csv')
    hr=historical[(historical.modelo=='arbol_ponderado')&(historical.regla=='aprendido')].iloc[0]
    hist={k:int(hr[k]) for k in ['TP','FP','TN','FN']};hist.update({k:float(hr[k]) for k in ['precision','recall','f1','average_precision']})
    for name,v in baseline.items():
        p=Path(name);s=p.stat();check('Historico intacto '+name,s.st_size==v['size'] and str(s.st_mtime_ns)==v['mtime_ns'] and sha(p)==v['sha256'])
    check('Una sola evaluacion e inferencia',COUNTS==dict(lecturas_archivo_test=1,cargas_dataframe_test=1,transformaciones_test=1,inferencias_test=1,evaluaciones_metricas=1,intentos_fit=0))
    audit=dict(inicio=started,fin=now(),procedimiento='referencia_arbol_ponderado_v1',ruta_test=TEST.as_posix(),fuente_ruta='INFORME_PARTICION_FASE04.md',hash_test=test_hash,hashes_artefactos={**EXPECTED,'MANIFIESTO_MODELO_FINAL.json':manifest_hash},versiones=versions,parametros=model.get_params(),predictores=PREDICTORES,umbral=T,regla='probabilidad clase 1 >= umbral',dimensiones_test=[11115,35],dimensiones_transformadas=[11115,62],eventos_ato=9,usuarios=400,usuarios_ato=9,metricas_evento=metrics,metricas_usuario=usermetrics,contadores=COUNTS,fit_ejecutado=False,ajustes_bloqueados=True,historicos_intactos=len(baseline),comprobaciones=CHECKS,incidencias=[],evaluacion_unica=True,predicciones_sin_IP_ni_UserID=True)
    save('AUDITORIA_EVALUACION_TEST.json',audit)
    eventrows='\n'.join(f'| {k} | {v} |' for k,v in metrics.items())
    userrows='\n'.join(f'| {k} | {v} |' for k,v in usermetrics.items())
    comparison='\n'.join(f'| {k} | {hist[k]} | {threshold[k]} | {metrics[k]} |' for k in ['TP','FP','TN','FN','f1'])
    interpretation=f'El modelo detectó {tp} de nueve ATO y omitió {fn}; generó {fp} falsas alarmas. Detectó {len(detected)} de nueve usuarios positivos. La precision fue {metrics["precision"]:.6f} y el recall {metrics["recall"]:.6f}. '
    if tp==0:interpretation+='En esta partición no recuperó ningún ATO, por lo que no demostró utilidad de detección al umbral congelado.'
    else:interpretation+='Hubo detección de ATO en esta partición, cuyo alcance debe valorarse junto con las omisiones y falsas alarmas, sin extrapolar aptitud productiva.'
    report=f'''# Evaluación final única de test — Fase 4

Fecha/hora de ejecución: {started} a {audit['fin']} (America/Bogota, UTC−05:00).

## Objetivo, autorización y dictamen

Evaluación independiente del procedimiento congelado referencia_arbol_ponderado_v1, autorizada expresamente por el adjunto 50422d45-422d-4786-9fba-2671a6d18e57. Se realizó una única lectura física del CSV, una carga desde memoria, una transformación y **una llamada predict_proba sobre los 11.115 eventos completos**. Cero fit, fit_transform, selección de umbral o comparaciones con otros algoritmos.

{interpretation}

Se aceptan estos resultados como definitivos de esta evaluación del proyecto. No se modifica ningún elemento ni se repetirá la evaluación. No se presenta el modelo como listo para producción.

## Entradas e integridad

Ruta exacta test: dataset_test_fase04.csv, identificada en INFORME_PARTICION_FASE04.md. SHA-256 `{test_hash}`. El archivo se leyó una sola vez como bytes para verificar hash antes de analizar su contenido; el parseo posterior se hizo desde esos mismos bytes, sin reabrirlo.

Directorio de referencia: {REF.as_posix()}/.

| Artefacto | SHA-256 verificado |
|---|---|
| modelo_final.joblib | {EXPECTED['modelo_final.joblib']} |
| preprocesador_final.joblib | {EXPECTED['preprocesador_final.joblib']} |
| umbral_definitivo.json | {EXPECTED['umbral_definitivo.json']} |
| MANIFIESTO_MODELO_FINAL.json | {manifest_hash} |

El hash del manifiesto se contrastó con VERIFICACION_MANIFIESTO.json. Se verificaron identidad, parámetros completos, versiones y seis predictores contra la evidencia congelada. Modelo Gini/best, class_weight=balanced, semilla 42, sin nuevos parámetros. Parámetros y versiones completos en AUDITORIA_EVALUACION_TEST.json.

## Contratos e inferencia

Se confirmaron 11.115 filas y 35 columnas en el orden del esquema train, 400 usuarios, nueve ATO y nueve usuarios positivos. Clave User ID + Login Timestamp + IP Address única/no nula, target binario/no nulo e intersección de usuarios train/test cero. No se exportaron IP ni User ID.

Seis predictores en orden: {', '.join(PREDICTORES)}. Se aplicó la normalización de entrada aprobada y únicamente transform del preprocesador recuperado: medianas aprendidas, indicador intacto y One-Hot aprendido con desconocidas ignoradas. Matriz finita 11.115×62. No se ajustaron vocabularios ni imputadores. El score es predict_proba de clase 1 y y_pred=(score >= {T!r}). Modelo y preprocesador conservaron su estado en memoria y sus hashes en disco.

## Matriz de confusión y métricas por evento

| Real / predicción | No ATO | ATO |
|---|---:|---:|
| No ATO | {tn} | {fp} |
| ATO | {fn} | {tp} |

| Métrica | Valor |
|---|---:|
{eventrows}

Funciones sklearn.metrics: confusion_matrix(labels=[0,1]); precision_score, recall_score y f1_score con zero_division=0; average_precision_score(y,score) y roc_auc_score(y,score), sin binarizar scores para estas dos últimas. Precision=TP/(TP+FP), Recall=TP/(TP+FN), F1=2TP/(2TP+FP+FN); denominador cero se representa como 0. F2=5TP/(5TP+4FN+FP), especificidad=TN/(TN+FP), FPR=FP/(FP+TN). No se utiliza accuracy como criterio principal.

Se emitieron {metrics['alertas']} alertas, de las cuales {fp} fueron falsas y {tp} verdaderas. La proporción de alertas verdaderas es {metrics['precision']:.6f} (si no hubiera alertas, Precision=0 por convención no implicaría una proporción empírica estimable).

AP mide ranking con las probabilidades originales, no éxito de la regla de clasificación. ROC-AUC es calculable porque hay ambas clases, pero abundantes negativos y solo nueve positivos pueden ocultar el problema de falsas alarmas; no sustituye Precision/Recall/AP ni demuestra utilidad operativa. No se ensayan otros umbrales para reinterpretar el resultado.

## Métricas por usuario

| Conteo | Valor |
|---|---:|
{userrows}

Un usuario ATO se considera detectado únicamente si al menos un evento ATO suyo fue correctamente alertado. Una falsa alarma en otro login no lo convierte en detectado. Los usuarios con FP se separan entre cuentas que tuvieron ATO y cuentas sin ATO. Son conteos de personas/cuentas distintas, no número de eventos.

## Comparación histórica, sin mezclar evidencias

| Métrica | Anidada histórica externa, train | OOF para seleccionar t, train | Test independiente, único |
|---|---:|---:|---:|
{comparison}

La anidada histórica tuvo Precision {hist['precision']:.8f} y Recall {hist['recall']:.8f}; en test son {metrics['precision']:.8f} y {metrics['recall']:.8f}. Se trata de poblaciones de tamaño distinto, distintos estimadores y umbrales históricos por fold frente a un único modelo/umbral final. No se suman matrices ni se atribuye causalidad a las diferencias. El resultado test muestra recall {'mayor' if metrics['recall']>hist['recall'] else 'menor' if metrics['recall']<hist['recall'] else 'igual'} y F1 {'mayor' if metrics['f1']>hist['f1'] else 'menor' if metrics['f1']<hist['f1'] else 'igual'} que esos valores históricos; con nueve ATO no demuestra una diferencia estable de rendimiento.

El F1 0.17391304347826086 de OOF se usó para elegir el umbral: no es una estimación independiente, ni un resultado de test, ni evidencia adicional de generalización. El modelo final se entrenó con todo train y la transferencia del umbral desde tres estimadores OOF no garantizaba equivalencia de probabilidades. No se ajustó esa transferencia con test.

## Interpretación académica y limitaciones

Cada uno de los nueve ATO representa 1/9 de los positivos: un solo acierto cambia recall en aproximadamente 11,11 puntos porcentuales. Hay nueve usuarios positivos, por lo que pocos casos condicionan mucho las métricas. Los eventos de un usuario no son independientes; el resultado describe esta partición por usuarios y no garantiza rendimiento temporal futuro.

La comparación académica permite justificar la referencia por F1 anidado histórico, no una superioridad universal. Esta prueba independiente complementa la historia sin borrar el carácter retrospectivo de la elección de familia. El escaso soporte positivo, limitaciones de representación y falta de criterio operativo de costes impiden acreditar producción, tanto si el resultado es favorable como si es desfavorable. Un resultado adverso no autoriza ajustes y uno favorable no demuestra robustez.

## Auditoría, entregables y cierre de evaluación

Se verificó integridad de {len(baseline)} archivos históricos permitidos antes/después, incluidos modelo, preprocesador y umbral. No se reabrió test para un segundo hash: se conserva la huella de los bytes exactos analizados. Sin incidencias ni discrepancias. No se realizaron operaciones Git, instalaciones, modificaciones de Fase 3 ni escrituras en datasets/históricos.

PREDICCIONES_TEST.csv conserva solo evento_id (posición original base cero), probabilidad_positiva, prediccion y etiqueta_real. No incluye IP ni identificadores de usuario. AUDITORIA_EVALUACION_TEST.json guarda contratos, parámetros, métricas, contadores y versiones. MANIFIESTO_EVALUACION_TEST.json registra hashes de entradas y salidas. Los marcadores exclusivos impiden volver a ejecutar este script sobre el destino; la guardia impide una segunda apertura del test durante el proceso. fit/fit_transform quedaron bloqueados.

**La evaluación única queda cerrada.** Se detiene el trabajo sin nuevos ajustes, análisis exploratorios, predicciones o evaluaciones. Los resultados se aceptan para el proyecto; esta conclusión no certifica aptitud productiva.
'''
    textfile('INFORME_EVALUACION_FINAL_TEST_FASE04.md',report)
    outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file()}
    final_manifest=dict(procedimiento='referencia_arbol_ponderado_v1',estado='EVALUACION_UNICA_CERRADA',inicio=started,fin=now(),versiones=versions,entradas={'test':dict(ruta=TEST.as_posix(),sha256=test_hash),'artefactos':dict(directorio=REF.as_posix(),sha256={**EXPECTED,'MANIFIESTO_MODELO_FINAL.json':manifest_hash}),'train_solo_control_separacion':dict(ruta='dataset_train_fase04.csv',sha256=manifest['train_sha256'])},umbral=T,contadores=COUNTS,ajustes_ejecutados=0,evaluacion_unica=True,sha256_entregables=outputs,nota='No contiene hash de sí mismo; test no reabierto tras inferencia.')
    save('MANIFIESTO_EVALUACION_TEST.json',final_manifest)
    check('Manifiesto legible',json.loads((OUT/'MANIFIESTO_EVALUACION_TEST.json').read_text(encoding='utf-8'))==final_manifest)
    print(json.dumps(dict(metricas=metrics,usuarios=usermetrics,contadores=COUNTS,historicos_intactos=len(baseline),manifiesto_sha256=sha(OUT/'MANIFIESTO_EVALUACION_TEST.json')),ensure_ascii=True),flush=True)

if __name__=='__main__':
    try:main()
    except Exception:
        if not (OUT/'INCIDENCIA_EVALUACION.txt').exists():textfile('INCIDENCIA_EVALUACION.txt',traceback.format_exc())
        raise
