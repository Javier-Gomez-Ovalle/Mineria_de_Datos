"""OOF internas con índices globales y etiquetas solo de la población local."""
import numpy as np
import pandas as pd
from fase04_modelado.modelos import NOMBRES
from .ajuste import AjustadorVariante
from .seleccion_umbral import seleccionar_umbral
from .seleccion_variante import seleccionar_variante

def generar_oof(x_local,y_local,usuarios_local,particiones):
    partes=[];auditorias=[];decisiones={};tablas=[]
    for nombre in NOMBRES:
        score=np.full(len(y_local),np.nan);fold=np.zeros(len(y_local),int);visitas=np.zeros(len(y_local),int)
        for numero,(a,b) in enumerate(particiones,1):
            assert not set(usuarios_local.iloc[a])&set(usuarios_local.iloc[b])
            s,audit=AjustadorVariante(nombre).predecir(x_local.iloc[a],y_local.iloc[a],x_local.iloc[b]);audit.update(nivel='interno',fold_interno=numero);auditorias.append(audit)
            score[b]=s;fold[b]=numero;visitas[b]+=1
        assert np.all(visitas==1) and np.isfinite(score).all()
        partes.append(pd.DataFrame(dict(evento_id=x_local.index.to_numpy(),usuario=usuarios_local.to_numpy(),fold_interno=fold,modelo=nombre,y_true=y_local.to_numpy(),score=score)))
        elegido,tabla=seleccionar_umbral(y_local,score);decisiones[nombre]=elegido;tabla['modelo']=nombre;tablas.append(tabla)
    return pd.concat(partes,ignore_index=True),decisiones,seleccionar_variante(decisiones),pd.concat(tablas,ignore_index=True),auditorias
