"""Estratificacion por presencia de ATO en usuarios; expansion a eventos."""
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold


def construir_folds_usuario(y, grupos):
    if len(y) != len(grupos) or grupos.isna().any() or not y.isin([0,1]).all():
        raise ValueError('Grupos o etiquetas invalidos')
    usuarios = pd.DataFrame({'User ID':grupos.to_numpy(),'usuario_con_ato':y.to_numpy()}).groupby('User ID',sort=True)['usuario_con_ato'].max()
    skf=StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
    visitas=np.zeros(len(y),dtype=int);usuarios_visitados=[];folds=[];filas=[]
    for numero,(ua,ub) in enumerate(skf.split(usuarios.index,usuarios.to_numpy()),1):
        subtrain=usuarios.index[ua];validacion=usuarios.index[ub]
        a=np.flatnonzero(grupos.isin(subtrain).to_numpy());b=np.flatnonzero(grupos.isin(validacion).to_numpy())
        if set(grupos.iloc[a]) & set(grupos.iloc[b]):raise ValueError('Usuarios compartidos')
        if len(a)+len(b)!=len(y):raise ValueError('Eventos perdidos')
        if set(y.iloc[a])!={0,1} or set(y.iloc[b])!={0,1}:raise ValueError('Fold sin ambas clases')
        visitas[b]+=1;usuarios_visitados.extend(validacion.tolist());folds.append((a,b))
        row={'fold':numero,'usuarios_compartidos':0}
        for nombre,indices in [('subtrain',a),('validacion',b)]:
            u=grupos.iloc[indices].nunique();up=grupos.iloc[indices][y.iloc[indices].eq(1)].nunique();p=int(y.iloc[indices].sum())
            row.update({f'{nombre}_eventos':len(indices),f'{nombre}_usuarios':u,
                        f'{nombre}_positivos':p,f'{nombre}_negativos':len(indices)-p,
                        f'{nombre}_usuarios_positivos':up,f'{nombre}_usuarios_negativos':u-up})
        filas.append(row)
    if not (visitas==1).all():raise ValueError('Cobertura de eventos invalida')
    if len(usuarios_visitados)!=len(set(usuarios_visitados)) or set(usuarios_visitados)!=set(usuarios.index):
        raise ValueError('Cobertura de usuarios invalida')
    return folds,pd.DataFrame(filas)
