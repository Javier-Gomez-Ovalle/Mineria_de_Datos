"""Enumera todos los estados de decisión observados; no optimiza costes."""
import numpy as np
from sklearn.metrics import average_precision_score

def calcular(y,score,umbral):
    y=np.asarray(y,dtype=int);score=np.asarray(score,dtype=float)
    if len(y)!=len(score) or not np.isin(y,[0,1]).all() or not np.isfinite(score).all() or ((score<0)|(score>1)).any():raise ValueError('Entradas inválidas')
    pred=score>=umbral;tp=int((pred&(y==1)).sum());fp=int((pred&(y==0)).sum());fn=int((~pred&(y==1)).sum());tn=int((~pred&(y==0)).sum())
    precision=tp/(tp+fp) if tp+fp else 0.;recall=tp/(tp+fn) if tp+fn else 0.
    return dict(umbral=float(umbral),TP=tp,FP=fp,TN=tn,FN=fn,precision=precision,recall=recall,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.,average_precision=float(average_precision_score(y,score)) if y.sum() else 0.,alertas=tp+fp,porcentaje_alertas=100*(tp+fp)/len(y),sin_predicciones_positivas=not bool(tp+fp))

def rejilla(score):
    """Incluye scores únicos, referencias comunes y extremo sin alertas.

    Para regla >=, cada score observado representa (score_previo, score].
    El siguiente float por encima de 1 representa la política sin alertas.
    """
    return np.unique(np.r_[score,[0.,.2,.4,.5,1.,np.nextafter(1.,np.inf)]])

def frontera(tabla):
    """No dominado si nadie detecta más con igual/menor FP o igual TP/menor FP."""
    return [not (((tabla.TP>=r.TP)&(tabla.FP<=r.FP))&((tabla.TP>r.TP)|(tabla.FP<r.FP))).any() for r in tabla.itertuples()]
