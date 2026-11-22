from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from fase04_modelado.folds_usuario import construir_folds_usuario


def test_particion_usuario_cobertura_reproducibilidad():
    d=pd.read_csv('dataset_train_fase04.csv',usecols=['User ID','Is Account Takeover'])
    y=d['Is Account Takeover'].astype(int);g=d['User ID']
    a,t=construir_folds_usuario(y,g);b,u=construir_folds_usuario(y,g)
    pd.testing.assert_frame_equal(t,u)
    assert t.validacion_usuarios_positivos.tolist()==[6,7,7,7,7]
    assert t.validacion_positivos.tolist()==[6,7,7,8,8]
    assert t.validacion_eventos.sum()==46305
    visit=np.zeros(len(d),dtype=int);us=[]
    for (ta,va),(tb,vb) in zip(a,b):
        np.testing.assert_array_equal(ta,tb);np.testing.assert_array_equal(va,vb)
        assert not set(g.iloc[ta]) & set(g.iloc[va])
        visit[va]+=1;us.extend(g.iloc[va].unique())
    assert (visit==1).all() and len(us)==len(set(us))==1600
    tabla=d.groupby('User ID',sort=True)['Is Account Takeover'].max()
    for (_,uval),(_,eval_) in zip(StratifiedKFold(5,shuffle=True,random_state=42).split(tabla.index,tabla),a):
        assert set(tabla.index[uval])==set(g.iloc[eval_])


def test_motor_identico_excepto_fold_y_destino():
    original=Path('fase04_modelado/entrenamiento.py').read_text(encoding='utf-8')
    nuevo=Path('fase04_modelado/entrenamiento_cv_usuario.py').read_text(encoding='utf-8')
    esperado=original.replace('from .folds import construir_folds','from .folds_usuario import construir_folds_usuario as construir_folds').replace("salida = Path('fase04_modelado/resultados')","salida = Path('fase04_modelado/resultados_cv_usuario')")
    assert nuevo==esperado
