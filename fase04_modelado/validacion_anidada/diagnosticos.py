"""Estabilidad, transferencia y comparación histórica: solo después de congelar."""
import json
import numpy as np
import pandas as pd
from .auditoria import RESULTADOS,activar_guardia,guardar_csv,guardar_json

def main():
    activar_guardia();o=pd.read_csv(RESULTADOS/'predicciones_externas.csv',float_precision='round_trip');s=pd.read_csv(RESULTADOS/'selecciones.csv',float_precision='round_trip');f=pd.read_csv(RESULTADOS/'metricas_por_fold.csv',float_precision='round_trip');filas=[]
    for fold in range(1,6):
        i=pd.read_csv(RESULTADOS/f'oof_internas_{fold}.csv',float_precision='round_trip')
        for nombre in s.modelo.unique():
            for nivel,g in [('interno',i[i.modelo.eq(nombre)]),('externo',o[o.modelo.eq(nombre)&o.fold_externo.eq(fold)])]:
                filas.append(dict(fold_externo=fold,modelo=nombre,nivel=nivel,eventos=len(g),ato=int(g.y_true.sum()),scores_distintos=g.score.nunique(),proporcion_score_0=float(g.score.eq(0).mean()),proporcion_score_1=float(g.score.eq(1).mean()),score_media=float(g.score.mean()),score_p50=float(g.score.quantile(.5)),score_p99=float(g.score.quantile(.99)),score_max=float(g.score.max())))
    guardar_csv(RESULTADOS/'distribucion_scores_transferencia.csv',pd.DataFrame(filas))
    comparacion=s.merge(f[f.regla.eq('aprendido')][['modelo','fold_externo','f1','TP','FP','FN','precision','recall']],on=['modelo','fold_externo']);comparacion['diferencia_f1_externo_interno']=comparacion.f1-comparacion.f1_interno;guardar_csv(RESULTADOS/'transferencia.csv',comparacion)
    a=pd.DataFrame(json.loads((RESULTADOS/'auditoria_ajustes.json').read_text()));tiempos=a.groupby(['modelo','nivel'])[['preprocesamiento_s','ros_s','entrenamiento_s','prediccion_s']].sum().reset_index();guardar_csv(RESULTADOS/'tiempos.csv',tiempos)
    estabilidad=s.groupby('modelo').agg(umbral_min=('umbral','min'),umbral_max=('umbral','max'),umbral_media=('umbral','mean'),umbral_de=('umbral','std'),umbrales_distintos=('umbral','nunique'),veces_seleccionado=('selector','sum')).reset_index();guardar_csv(RESULTADOS/'estabilidad.csv',estabilidad)
    vieja=pd.read_csv('fase04_modelado/resultados_cv_usuario/predicciones_oof.csv');verificaciones=[]
    for nombre,g in o.groupby('modelo'):
        g=g.sort_values('evento_id');v=vieja[vieja.modelo.eq(nombre)].sort_values('evento_id');np.testing.assert_array_equal(g.evento_id,v.evento_id);np.testing.assert_array_equal(g.fold_externo,v.fold);np.testing.assert_allclose(g.score,v.score,rtol=1e-12,atol=1e-15);np.testing.assert_array_equal(g.pred_05,v.y_pred)
        verificaciones.append(dict(modelo=nombre,referencia_cv2_coincide=True,diferencia_score_max=float(np.abs(g.score.to_numpy()-v.score.to_numpy()).max())))
    guardar_json(RESULTADOS/'comparacion_referencia_cv2.json',verificaciones)

if __name__=='__main__':main()
