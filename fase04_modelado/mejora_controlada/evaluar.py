"""Evalúa predicciones congeladas; no entrena ni cambia reglas."""
import json
import numpy as np
import pandas as pd
from fase04_modelado.validacion_anidada.evaluacion import medir
from .contratos import *

def metricas(g,col='pred_aprendido',ap=True):
    r=medir(g.y_true,g.score,g[col],g['User ID'],ap=ap)
    r.update(f2=5*r['TP']/(5*r['TP']+4*r['FN']+r['FP']) if 5*r['TP']+4*r['FN']+r['FP'] else 0.,especificidad=r['TN']/(r['TN']+r['FP']),FPR=r['FP']/(r['TN']+r['FP']),recall_usuarios=r['usuarios_ato_detectados']/r['usuarios_ato'])
    return r

def grupos():
    old=pd.read_csv(HIST/'predicciones_externas.csv',float_precision='round_trip');new=pd.read_csv(OUT/'predicciones_externas_rf.csv',float_precision='round_trip')
    joint=[]
    for fold in range(1,6):
        d=json.loads((OUT/f'decision_congelada_{fold}.json').read_text(encoding='utf-8'));name=d['selector_ampliado']
        g=new if name=='random_forest' else old[old.modelo.eq(name)]
        joint.append(g[g.fold_externo.eq(fold)].copy())
    joint=pd.concat(joint,ignore_index=True)
    return [(n,g) for n,g in old.groupby('modelo',sort=False)]+[('random_forest',new),('selector_historico',old[old.selector].copy()),('selector_ampliado',joint)]

def main():
    activar_guardia();verificar_integridad();groups=grupos();globales=[];folds=[];usuarios=[];errores=[]
    train=pd.read_csv('dataset_train_fase04.csv',usecols=['User ID','Country','Device Type','has_previous_login','failed_attempts_1h'])
    for name,g in groups:
        g=g.sort_values('evento_id');np.testing.assert_array_equal(g.evento_id,np.arange(len(train)))
        np.testing.assert_array_equal(g['User ID'],train['User ID'])
        for rule,col in [('aprendido','pred_aprendido'),('fijo_05','pred_05')]:
            globales.append(dict(modelo=name,regla=rule,**metricas(g,col,not name.startswith('selector'))))
            for f,v in g.groupby('fold_externo'):folds.append(dict(modelo=name,regla=rule,fold=f,**metricas(v,col)))
        if name=='selector_ampliado':csv_nuevo(OUT/'predicciones_selector_ampliado.csv',g)
        w=g.copy();w['FP']=((w.y_true==0)&(w.pred_aprendido==1)).astype(int);w['FN']=((w.y_true==1)&(w.pred_aprendido==0)).astype(int);w['TP']=((w.y_true==1)&(w.pred_aprendido==1)).astype(int)
        u=w.groupby('User ID').agg(eventos=('y_true','size'),ATO=('y_true','sum'),TP=('TP','sum'),FP=('FP','sum'),FN=('FN','sum')).reset_index();u['modelo']=name;usuarios.append(u)
        w=w.join(train[['Country','Device Type','has_previous_login','failed_attempts_1h']],on='evento_id')
        for c in ['Country','Device Type','has_previous_login','failed_attempts_1h']:
            v=w.groupby(c).agg(eventos=('y_true','size'),ATO=('y_true','sum'),TP=('TP','sum'),FP=('FP','sum'),FN=('FN','sum')).reset_index().rename(columns={c:'valor'});v['perfil']=c;v['modelo']=name;v['FPR']=v.FP/(v.eventos-v.ATO).replace(0,np.nan);errores.append(v)
    gm=pd.DataFrame(globales);fm=pd.DataFrame(folds)
    csv_nuevo(OUT/'comparacion_global.csv',gm);csv_nuevo(OUT/'metricas_por_fold.csv',fm)
    metrics=['precision','recall','f1','f2','average_precision','FPR','TP','FP','FN','recall_usuarios']
    summary=fm.groupby(['modelo','regla'])[metrics].agg(['mean','std','min','max']);summary.columns=['_'.join(c) for c in summary.columns];csv_nuevo(OUT/'resumen_folds.csv',summary.reset_index())
    csv_nuevo(OUT/'metricas_por_usuario.csv',pd.concat(usuarios,ignore_index=True));csv_nuevo(OUT/'errores_por_perfil.csv',pd.concat(errores,ignore_index=True))
    references=[]
    for protocol,folder in [('CV1','resultados'),('CV2','resultados_cv_usuario')]:
        t=pd.read_csv(Path('fase04_modelado')/folder/'comparacion_modelos.csv');t['protocolo']=protocol;references.append(t)
    csv_nuevo(OUT/'referencias_cv1_cv2.csv',pd.concat(references,ignore_index=True))
    print(gm[gm.regla.eq('aprendido')][['modelo','TP','FP','FN','precision','recall','f1','average_precision','usuarios_ato_detectados']].to_string(index=False))

if __name__=='__main__':main()
