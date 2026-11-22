"""F1 exacto por conteos. Desempate autorizado sin colapsar decisiones iguales."""
from fractions import Fraction
import hashlib
import numpy as np
import pandas as pd

def seleccionar_umbral(y,score):
    y=np.asarray(y,dtype=int);score=np.asarray(score,dtype=float)
    if not np.isin(y,[0,1]).all() or set(y)!={0,1} or len(y)!=len(score) or not np.isfinite(score).all() or ((score<0)|(score>1)).any():raise ValueError('OOF inválidas')
    candidatos=np.unique(np.r_[score,0.,.5,np.nextafter(1.,np.inf)])
    filas=[];valores=[]
    for t in candidatos:
        pred=score>=t;tp=int((pred&(y==1)).sum());fp=int((pred&(y==0)).sum());fn=int((~pred&(y==1)).sum());tn=int((~pred&(y==0)).sum())
        valor=Fraction(2*tp,2*tp+fp+fn);valores.append(valor)
        filas.append(dict(umbral=float(t),politica='ninguno' if t>1 else 'todos' if t==0 else 'umbral',TP=tp,FP=fp,TN=tn,FN=fn,f1=float(valor),f1_numerador=valor.numerator,f1_denominador=valor.denominator,decisiones_sha256=hashlib.sha256(pred.tobytes()).hexdigest()))
    mejor=max(valores);empatados=[i for i,v in enumerate(valores) if v==mejor]
    indice=min(empatados,key=lambda i:(abs(float(candidatos[i])-.5),-float(candidatos[i])))
    elegido=filas[indice].copy();elegido['umbrales_empatados']=[float(candidatos[i]) for i in empatados]
    for i,f in enumerate(filas):f['empate_maximo']=i in empatados;f['seleccionado']=i==indice
    return elegido,pd.DataFrame(filas)
