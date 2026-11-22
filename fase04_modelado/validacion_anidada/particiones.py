"""Estratificación de usuarios dentro de la población local autorizada."""
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

def construir_particiones(y,usuarios,n_splits):
    if len(y)!=len(usuarios) or usuarios.isna().any() or not y.isin([0,1]).all():raise ValueError('Población inválida')
    tabla=pd.DataFrame({'usuario':usuarios.to_numpy(),'positivo':y.to_numpy()}).groupby('usuario',sort=True).positivo.max()
    if tabla.value_counts().min()<n_splits:raise ValueError('Soporte insuficiente para estratos')
    skf=StratifiedKFold(n_splits=n_splits,shuffle=True,random_state=42);visitas=np.zeros(len(y),int);salida=[]
    for a,b in skf.split(tabla.index,tabla.to_numpy()):
        ia=np.flatnonzero(usuarios.isin(tabla.index[a]).to_numpy());ib=np.flatnonzero(usuarios.isin(tabla.index[b]).to_numpy())
        assert not set(usuarios.iloc[ia])&set(usuarios.iloc[ib])
        assert len(ia)+len(ib)==len(y) and set(y.iloc[ia])==set(y.iloc[ib])=={0,1}
        visitas[ib]+=1;salida.append((ia,ib))
    assert np.all(visitas==1)
    return salida

def describir(y,usuarios,a,b,externo,interno=0):
    fila=dict(fold_externo=externo,fold_interno=interno,usuarios_compartidos=len(set(usuarios.iloc[a])&set(usuarios.iloc[b])))
    for nombre,i in [('ajuste',a),('validacion',b)]:
        fila.update({f'{nombre}_eventos':len(i),f'{nombre}_usuarios':usuarios.iloc[i].nunique(),f'{nombre}_ato':int(y.iloc[i].sum()),f'{nombre}_negativos':int((1-y.iloc[i]).sum()),f'{nombre}_usuarios_ato':usuarios.iloc[i][y.iloc[i].eq(1)].nunique()})
    return fila
