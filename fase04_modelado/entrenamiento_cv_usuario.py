"""Una ejecucion completa de seis variantes en cinco folds, sin lectura de test."""
import json
import hashlib
import time
import platform
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import psutil
import sklearn
import imblearn
from imblearn.over_sampling import RandomOverSampler
from sklearn.utils.class_weight import compute_sample_weight
from sklearn import config_context
from threadpoolctl import threadpool_limits
from fase04_preparacion.seleccion import separar_datos
from fase04_preparacion.transformaciones import crear_preprocesador, ajustar_train, transformar
from .folds_usuario import construir_folds_usuario as construir_folds
from .modelos import crear_modelo, NOMBRES
from .metricas import calcular_metricas, METRICAS
from .auditoria import auditar_preprocesador, verificar_oof


def ejecutar():
    salida = Path('fase04_modelado/resultados_cv_usuario')
    if salida.exists():
        raise FileExistsError(salida)
    ruta = Path('dataset_train_fase04.csv')
    sha = hashlib.sha256(ruta.read_bytes()).hexdigest()
    assert sha == '98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f'
    df = pd.read_csv(ruta)
    x,y,claves = separar_datos(df)
    assert len(y)==46305 and y.sum()==36 and df['User ID'].nunique()==1600
    folds, tabla_folds = construir_folds(y,df['User ID'])
    print(tabla_folds.to_string(index=False),flush=True)
    salida.mkdir(parents=True)
    tabla_folds.to_csv(salida/'distribucion_folds.csv',index=False,mode='x')
    metricas, predicciones, auditorias = [], [], []
    proceso = psutil.Process()
    rss = proceso.memory_info().rss
    inicio=time.perf_counter()
    with threadpool_limits(limits=2), config_context(working_memory=256):
        for nombre in NOMBRES:
            representacion, _ = crear_modelo(nombre)
            for fold,(a,b) in enumerate(folds,1):
                t=time.perf_counter()
                prep=crear_preprocesador(representacion)
                xa=ajustar_train(prep,x.iloc[a])
                huella=joblib.hash(prep)
                xb=transformar(prep,x.iloc[b])
                assert joblib.hash(prep)==huella
                segundos_pre=time.perf_counter()-t
                audit=auditar_preprocesador(prep,x.iloc[a])
                audit.update(modelo=nombre,fold=fold,subtrain_indices_sha256=hashlib.sha256(a.tobytes()).hexdigest())
                _,modelo=crear_modelo(nombre)
                ya=y.iloc[a].to_numpy()
                validacion_hash=joblib.hash((xb,y.iloc[b]))
                t=time.perf_counter()
                if nombre=='knn_ros':
                    ros=RandomOverSampler(random_state=42,sampling_strategy=1.0)
                    original_xa,original_ya=xa,ya
                    xa,ya=ros.fit_resample(xa,ya)
                    np.testing.assert_array_equal(xa,original_xa[ros.sample_indices_])
                    np.testing.assert_array_equal(ya,original_ya[ros.sample_indices_])
                    audit['remuestreo_indices_solo_subtrain']=True
                segundos_ros=time.perf_counter()-t
                kwargs={}
                if nombre=='gnb_ponderado':
                    pesos=compute_sample_weight('balanced',ya)
                    for clase in [0,1]:
                        np.testing.assert_allclose(pesos[ya==clase],len(ya)/(2*(ya==clase).sum()))
                    kwargs['sample_weight']=pesos
                    audit['pesos_clase']={str(c):float(pesos[ya==c][0]) for c in [0,1]}
                t=time.perf_counter();modelo.fit(xa,ya,**kwargs);segundos_fit=time.perf_counter()-t
                t=time.perf_counter()
                col=int(np.flatnonzero(modelo.classes_==1)[0])
                score=np.concatenate([modelo.predict_proba(xb[i:i+512])[:,col] for i in range(0,len(xb),512)])
                segundos_pred=time.perf_counter()-t
                assert joblib.hash((xb,y.iloc[b]))==validacion_hash
                fila={'modelo':nombre,'nombre':NOMBRES[nombre],'fold':fold,**calcular_metricas(y.iloc[b],score),
                      'preprocesamiento_s':segundos_pre,'sobremuestreo_s':segundos_ros,'entrenamiento_s':segundos_fit,
                      'prediccion_s':segundos_pred,'filas_ajuste_modelo':len(ya),'columnas':xa.shape[1],
                      'parametros':json.dumps(modelo.get_params(),sort_keys=True),'umbral':.5}
                metricas.append(fila)
                parte=claves.iloc[b].copy();parte.insert(0,'evento_id',b)
                parte['fold']=fold;parte['modelo']=nombre;parte['y_true']=y.iloc[b].to_numpy()
                parte['score']=score;parte['y_pred']=(score>=.5).astype(int)
                predicciones.append(parte);auditorias.append(audit)
                rss=max(rss,proceso.memory_info().rss)
                print(f'{nombre} fold={fold}: TP={fila["TP"]} FP={fila["FP"]} FN={fila["FN"]} AP={fila["average_precision"]:.6f} pred={segundos_pred:.2f}s',flush=True)
    fm=pd.DataFrame(metricas);oof=pd.concat(predicciones,ignore_index=True)
    verificar_oof(oof,y,claves,NOMBRES)
    resumen=[]
    for nombre in NOMBRES:
        p=oof[oof.modelo==nombre].sort_values('evento_id');f=fm[fm.modelo==nombre]
        row={'modelo':nombre,'nombre':NOMBRES[nombre],**calcular_metricas(p.y_true,p.score)}
        for m in METRICAS:
            row[m+'_media_folds']=f[m].mean();row[m+'_sd_folds']=f[m].std(ddof=1)
        for m in ['preprocesamiento_s','sobremuestreo_s','entrenamiento_s','prediccion_s']:
            row[m]=f[m].sum()
        row.update(parametros=f.parametros.iloc[0],umbral=.5,folds_completados=len(f))
        resumen.append(row)
    comp=pd.DataFrame(resumen)
    for nombre,datos in [('comparacion_modelos',comp),('metricas_por_fold',fm),('predicciones_oof',oof)]:
        datos.to_csv(salida/f'{nombre}.csv',index=False,mode='x')
    assert hashlib.sha256(ruta.read_bytes()).hexdigest()==sha
    config={'train_sha256':sha,'folds':5,'shuffle':True,'random_state':42,'umbral':.5,'test_leido':False,
            'versiones':{'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'pandas':pd.__version__,'imblearn':imblearn.__version__},
            'recursos':{'hilos':2,'lote_prediccion':512,'working_memory_MiB':256,'rss_max_observado_bytes':rss,'duracion_s':time.perf_counter()-inicio},
            'auditoria_folds':auditorias}
    with (salida/'configuracion_auditoria.json').open('x',encoding='utf-8') as f:json.dump(config,f,indent=2)
    tablas={'comparacion':comp.to_dict('records'),'folds':fm.to_dict('records'),'distribucion':tabla_folds.to_dict('records')}
    with (salida/'tablas_exportacion.json').open('x',encoding='utf-8') as f:json.dump(tablas,f,indent=2)
    print(comp[['modelo','TP','FP','FN',*METRICAS]].to_string(index=False),flush=True)


if __name__=='__main__':
    ejecutar()
