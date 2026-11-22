"""Ejecuta 90 ajustes internos y 30 externos; congela antes de evaluar."""
from pathlib import Path
import time,platform
import numpy as np
import pandas as pd
import sklearn,imblearn,psutil
from sklearn import config_context
from threadpoolctl import threadpool_limits
from fase04_preparacion.seleccion import separar_datos
from fase04_modelado.modelos import NOMBRES
from .auditoria import RESULTADOS,activar_guardia,sha,guardar_csv,guardar_json,ACCESOS,verificar_historicos
from .particiones import construir_particiones,describir
from .oof_internas import generar_oof
from .ajuste import AjustadorVariante

def main():
    activar_guardia();assert not RESULTADOS.exists();verificar_historicos()
    ruta=Path('dataset_train_fase04.csv');huella=sha(ruta)
    assert huella=='98d4d4970ada7bf11ec2e76f89e93c46c76c3d097043020598638547f977e53f'
    df=pd.read_csv(ruta);x,y,claves=separar_datos(df);usuarios=df['User ID']
    assert len(y)==46305 and int(y.sum())==36 and usuarios.nunique()==1600
    exteriores=construir_particiones(y,usuarios,5);RESULTADOS.mkdir()
    guardar_json(RESULTADOS/'configuracion_congelada.json',dict(fecha='2026-11-21',externos=5,internos=3,semilla=42,unidad='evento',criterio='F1 OOF interno agrupado',regla='score >= umbral',desempate_umbral='distancia a 0.5; luego mayor',desempate_variante=list(NOMBRES),politicas_extremas={'todos':0.,'ninguno':float(np.nextafter(1.,np.inf))},calibracion=False,optimizacion_hiperparametros=False,referencia=.5,hilos=2,lote_prediccion=512,working_memory_MiB=256,train_sha256=huella,especificacion_sha256=sha('PROPUESTA_VALIDACION_ANIDADA_FASE04.md'),versiones=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,imblearn=imblearn.__version__)))
    particiones=[];distribucion=[];predicciones=[];auditorias=[];selecciones=[];inicio=time.perf_counter();rss=0
    with threadpool_limits(limits=2),config_context(working_memory=256):
        for externo,(a,b) in enumerate(exteriores,1):
            internas=construir_particiones(y.iloc[a],usuarios.iloc[a],3)
            particiones.append(dict(fold_externo=externo,ajuste=a.tolist(),validacion=b.tolist(),internas=[dict(ajuste=a[ia].tolist(),validacion=a[ib].tolist()) for ia,ib in internas]))
            distribucion.append(describir(y,usuarios,a,b,externo))
            for j,(ia,ib) in enumerate(internas,1):distribucion.append(describir(y,usuarios,a[ia],a[ib],externo,j))
            oof,decisiones,selector,candidatos,audits=generar_oof(x.iloc[a],y.iloc[a],usuarios.iloc[a],internas)
            oof['fold_externo']=externo;candidatos['fold_externo']=externo
            guardar_csv(RESULTADOS/f'oof_internas_{externo}.csv',oof);guardar_csv(RESULTADOS/f'candidatos_internos_{externo}.csv',candidatos)
            congelacion=dict(fold_externo=externo,decisiones=decisiones,selector=selector,oof_sha256=sha(RESULTADOS/f'oof_internas_{externo}.csv'))
            ruta_congelada=RESULTADOS/f'decisiones_congeladas_{externo}.json';guardar_json(ruta_congelada,congelacion);hash_congelada=sha(ruta_congelada)
            for audit in audits:audit['fold_externo']=externo
            auditorias.extend(audits)
            for nombre in NOMBRES:
                s,audit=AjustadorVariante(nombre).predecir(x.iloc[a],y.iloc[a],x.iloc[b]);audit.update(nivel='externo',fold_interno=0,fold_externo=externo,decisiones_sha256=hash_congelada);auditorias.append(audit)
                d=decisiones[nombre];p=claves.iloc[b].copy();p.insert(0,'evento_id',b);p['fold_externo']=externo;p['modelo']=nombre;p['score']=s;p['umbral']=d['umbral'];p['politica']=d['politica'];p['pred_aprendido']=(s>=d['umbral']).astype(int);p['pred_05']=(s>=.5).astype(int);p['selector']=nombre==selector['modelo'];predicciones.append(p)
                selecciones.append(dict(fold_externo=externo,modelo=nombre,umbral=d['umbral'],politica=d['politica'],f1_interno=d['f1'],selector=nombre==selector['modelo'],numero_empates_umbral=len(d['umbrales_empatados']),numero_empates_variantes=len(selector['variantes_empatadas'])))
            assert sha(ruta_congelada)==hash_congelada
            rss=max(rss,psutil.Process().memory_info().rss)
            print(f'Externo {externo}: 18 ajustes internos y 6 reajustes completos; decisiones congeladas, sin evaluar y externa.',flush=True)
    # Las etiquetas externas se adjuntan solo cuando las cinco selecciones están congeladas.
    oof=pd.concat(predicciones,ignore_index=True);oof['y_true']=y.iloc[oof.evento_id].to_numpy()
    for nombre,g in oof.groupby('modelo'):np.testing.assert_array_equal(np.sort(g.evento_id),np.arange(len(y)))
    guardar_csv(RESULTADOS/'predicciones_externas.csv',oof);guardar_csv(RESULTADOS/'selecciones.csv',pd.DataFrame(selecciones));guardar_csv(RESULTADOS/'distribucion_folds.csv',pd.DataFrame(distribucion))
    guardar_json(RESULTADOS/'particiones.json',particiones);guardar_json(RESULTADOS/'auditoria_ajustes.json',auditorias)
    assert len(auditorias)==120 and sha(ruta)==huella
    guardar_json(RESULTADOS/'ejecucion.json',dict(ajustes_internos=90,reajustes_externos=30,modelo_final_entrenado=False,test_leido=False,segundos=time.perf_counter()-inicio,rss_observado_bytes=rss,accesos_datos=sorted(set(ACCESOS)),historicos_intactos=verificar_historicos()))
    print('120 ajustes terminados. Evaluación externa pendiente en módulo separado.',flush=True)

if __name__=='__main__':main()
