import numpy as np
import pandas as pd
import pytest
import joblib
from fase04_modelado.folds import construir_folds
from fase04_modelado.metricas import calcular_metricas
from fase04_modelado.auditoria import auditar_preprocesador,verificar_oof
from fase04_preparacion.seleccion import seleccionar_predictores
from fase04_preparacion.transformaciones import crear_preprocesador,ajustar_train,transformar


def muestra():
    return pd.DataFrame({'failed_attempts_15min':[0.,1.,2.], 'failed_attempts_1h':[0.,2.,3.],
        'time_since_previous_login_hours':[np.nan,2.,4.], 'has_previous_login':[0,1,1],
        'Device Type':['desktop','mobile','desktop'], 'Country':['NO','US','NO']})


@pytest.mark.parametrize('tipo',['arbol','gaussian_nb','distancias'])
def test_ajuste_solo_subtrain(tipo):
    x=muestra();p=crear_preprocesador(tipo);ajustar_train(p,x);auditar_preprocesador(p,x)
    h=joblib.hash(p);v=x.copy();v['Country']='NUEVO';v['failed_attempts_1h']=1e9
    assert np.isfinite(transformar(p,v)).all();assert joblib.hash(p)==h
    with pytest.raises(AssertionError):auditar_preprocesador(p,v)


def test_identificadores_target_excluidos():
    x=muestra();base=seleccionar_predictores(x)
    x['User ID']=123;x['Is Account Takeover']=True;x['impossible_travel']=1
    pd.testing.assert_frame_equal(base,seleccionar_predictores(x))


def test_log_invalido_bloquea():
    x=muestra();x.loc[0,'failed_attempts_1h']=-2
    with pytest.raises(ValueError):seleccionar_predictores(x)


def test_metricas_conteos_y_umbral():
    m=calcular_metricas([0,0,1,1],[.1,.5,.8,.2])
    assert (m['TN'],m['FP'],m['FN'],m['TP'])==(1,1,1,1)
    assert m['precision']==m['recall']==m['f1']==.5
    assert calcular_metricas([0,1],[0,0])['sin_predicciones_positivas']


def test_fold_real_y_reproducibilidad():
    d=pd.read_csv('dataset_train_fase04.csv',usecols=['User ID','Is Account Takeover'])
    y=d['Is Account Takeover'].astype(int);g=d['User ID']
    a,t=construir_folds(y,g);b,_=construir_folds(y,g)
    assert t.validacion_positivos.tolist()==[10,8,1,8,9]
    for (aa,ab),(ba,bb) in zip(a,b):
        np.testing.assert_array_equal(aa,ba);np.testing.assert_array_equal(ab,bb)


def test_oof_detecta_desalineacion():
    y=pd.Series([0,1]);claves=pd.DataFrame({'User ID':[1,2]})
    p=pd.DataFrame({'evento_id':[0,1],'modelo':['m','m'],'y_true':[0,1],'User ID':[1,2],'score':[0,.9],'y_pred':[0,1]})
    verificar_oof(p,y,claves,['m'])
    p.loc[1,'User ID']=3
    with pytest.raises(AssertionError):verificar_oof(p,y,claves,['m'])
