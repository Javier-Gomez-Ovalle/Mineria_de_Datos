"""Métricas externas por evento y usuario, sin modificar decisiones."""
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix,precision_score,recall_score,f1_score,average_precision_score
from .auditoria import RESULTADOS,activar_guardia,guardar_csv,guardar_json,sha
import json

def medir(y,score,pred,usuarios,ap=True):
    y=np.asarray(y,int);pred=np.asarray(pred,int);score=np.asarray(score,float)
    assert np.isin(y,[0,1]).all() and np.isin(pred,[0,1]).all() and np.isfinite(score).all()
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    t=pd.DataFrame(dict(usuario=np.asarray(usuarios),y=y,pred=pred));up=t.groupby('usuario').y.max();detectados=t.loc[(t.y==1)&(t.pred==1),'usuario'].nunique();alertados=set(t.loc[t.pred==1,'usuario']);sinato=set(up[up==0].index)
    return dict(TP=int(tp),FP=int(fp),TN=int(tn),FN=int(fn),precision=precision_score(y,pred,zero_division=0),recall=recall_score(y,pred,zero_division=0),f1=f1_score(y,pred,zero_division=0),average_precision=float(average_precision_score(y,score)) if ap else np.nan,alertas=int(pred.sum()),porcentaje_alertas=float(100*pred.mean()),sin_predicciones_positivas=not bool(pred.sum()),eventos=len(y),usuarios=len(up),usuarios_ato=int(up.sum()),usuarios_ato_detectados=int(detectados),usuarios_ato_omitidos=int(up.sum()-detectados),usuarios_sin_ato_con_alerta=len(sinato&alertados),usuarios_con_fp=int(t.loc[(t.y==0)&(t.pred==1),'usuario'].nunique()))

def main():
    activar_guardia();o=pd.read_csv(RESULTADOS/'predicciones_externas.csv',float_precision='round_trip');filas=[];globales=[]
    for externo in range(1,6):
        congelada=json.loads((RESULTADOS/f'decisiones_congeladas_{externo}.json').read_text(encoding='utf-8'));assert sha(RESULTADOS/f'oof_internas_{externo}.csv')==congelada['oof_sha256']
        for nombre,g in o[o.fold_externo.eq(externo)].groupby('modelo'):
            assert g.umbral.eq(congelada['decisiones'][nombre]['umbral']).all()
            np.testing.assert_array_equal(g.pred_aprendido,(g.score>=g.umbral).astype(int));np.testing.assert_array_equal(g.pred_05,(g.score>=.5).astype(int))
    for nombre,g in o.groupby('modelo',sort=False):
        for regla,col in [('aprendido','pred_aprendido'),('fijo_05','pred_05')]:
            globales.append(dict(modelo=nombre,regla=regla,**medir(g.y_true,g.score,g[col],g['User ID'])))
            for fold,p in g.groupby('fold_externo'):filas.append(dict(modelo=nombre,regla=regla,fold_externo=fold,**medir(p.y_true,p.score,p[col],p['User ID'])))
    selector=o[o.selector].copy();assert len(selector)==46305 and selector.evento_id.is_unique
    for regla,col in [('aprendido','pred_aprendido'),('fijo_05','pred_05')]:
        globales.append(dict(modelo='selector_conjunto',regla=regla,**medir(selector.y_true,selector.score,selector[col],selector['User ID'],ap=False)))
        for fold,p in selector.groupby('fold_externo'):filas.append(dict(modelo='selector_conjunto',regla=regla,fold_externo=fold,modelo_seleccionado=p.modelo.iloc[0],**medir(p.y_true,p.score,p[col],p['User ID'])))
    # Referencia del selector: mismas variantes elegidas por F1 interno con umbral aprendido, aplicadas a 0,5.
    fm=pd.DataFrame(filas);gm=pd.DataFrame(globales);metricas=['precision','recall','f1','average_precision','TP','FP','FN','alertas','usuarios_ato_detectados','usuarios_ato_omitidos','usuarios_sin_ato_con_alerta']
    resumen=fm.groupby(['modelo','regla'])[metricas].agg(['mean','std','min','max']);resumen.columns=['_'.join(c) for c in resumen.columns]
    guardar_csv(RESULTADOS/'metricas_por_fold.csv',fm);guardar_csv(RESULTADOS/'metricas_globales.csv',gm);guardar_csv(RESULTADOS/'resumen_folds.csv',resumen.reset_index());guardar_csv(RESULTADOS/'predicciones_selector.csv',selector)
    errores=[]
    for regla,col in [('aprendido','pred_aprendido'),('fijo_05','pred_05')]:
        e=o[o.y_true.ne(o[col])].copy();e['regla']=regla;e['tipo_error']=np.where(e.y_true.eq(1),'FN','FP');errores.append(e)
    guardar_csv(RESULTADOS/'errores_externos.csv',pd.concat(errores,ignore_index=True))
    print(gm[['modelo','regla','TP','FP','FN','precision','recall','f1','average_precision']].to_string(index=False))

if __name__=='__main__':main()
