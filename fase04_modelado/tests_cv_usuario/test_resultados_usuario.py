from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest
from imblearn.over_sampling import RandomOverSampler
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits
from fase04_modelado.auditoria import verificar_oof
from fase04_modelado.modelos import crear_modelo,NOMBRES
from fase04_modelado.metricas import calcular_metricas,METRICAS
from fase04_preparacion.seleccion import separar_datos

R=Path('fase04_modelado/resultados_cv_usuario')


def test_correspondencia_y_metricas_completas():
    d=pd.read_csv('dataset_train_fase04.csv');_,y,claves=separar_datos(d)
    p=pd.read_csv(R/'predicciones_oof.csv');c=pd.read_csv(R/'comparacion_modelos.csv').set_index('modelo');f=pd.read_csv(R/'metricas_por_fold.csv')
    verificar_oof(p,y,claves,NOMBRES)
    assert len(p)==46305*6 and len(f)==30
    assert p.groupby('User ID').fold.nunique().eq(1).all()
    assert p.groupby('evento_id').fold.nunique().eq(1).all()
    for nombre in NOMBRES:
        a=p[p.modelo==nombre]
        for k,v in calcular_metricas(a.y_true,a.score).items():np.testing.assert_allclose(c.loc[nombre,k],v)
        for fold in range(1,6):
            b=a[a.fold==fold];row=f[(f.modelo==nombre)&(f.fold==fold)].iloc[0]
            for k,v in calcular_metricas(b.y_true,b.score).items():np.testing.assert_allclose(row[k],v)
        for k in METRICAS:
            np.testing.assert_allclose(c.loc[nombre,k+'_media_folds'],f[f.modelo==nombre][k].mean())
            np.testing.assert_allclose(c.loc[nombre,k+'_sd_folds'],f[f.modelo==nombre][k].std(ddof=1))


def test_parametros_iguales_a_primera_ejecucion():
    viejo=pd.read_csv('fase04_modelado/resultados/metricas_por_fold.csv')
    nuevo=pd.read_csv(R/'metricas_por_fold.csv')
    for nombre in NOMBRES:
        esperado=json.loads(viejo[viejo.modelo==nombre].parametros.iloc[0])
        for _,r in nuevo[nuevo.modelo==nombre].iterrows():
            assert json.loads(r.parametros)==esperado and r.umbral==.5
    audit=json.loads((R/'configuracion_auditoria.json').read_text())
    assert len(audit['auditoria_folds'])==30 and audit['test_leido'] is False
    for a in audit['auditoria_folds']:
        assert a['controles']=='OK'
        if a['modelo']=='knn_ros':assert a['remuestreo_indices_solo_subtrain']


@pytest.mark.parametrize('nombre',list(NOMBRES))
def test_reproducibilidad_modelos_y_remuestreo(nombre):
    # Caso pequeno controlado: no representa una segunda corrida del dataset real.
    x=np.arange(120,dtype=float).reshape(30,4)%17;y=np.array([0]*25+[1]*5)
    scores=[]
    with threadpool_limits(limits=2):
        for _ in range(2):
            xx,yy=x.copy(),y.copy();kw={}
            if nombre=='knn_ros':xx,yy=RandomOverSampler(random_state=42,sampling_strategy=1.0).fit_resample(xx,yy)
            if nombre=='gnb_ponderado':kw['sample_weight']=compute_sample_weight('balanced',yy)
            _,model=crear_modelo(nombre);model.fit(xx,yy,**kw);scores.append(model.predict_proba(x))
    np.testing.assert_array_equal(*scores)
