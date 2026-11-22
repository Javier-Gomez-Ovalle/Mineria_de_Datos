"""Contratos de selección, aislamiento y ajustes locales."""
import numpy as np
import pandas as pd
import pytest
from fase04_modelado.modelos import NOMBRES
from fase04_preparacion.seleccion import seleccionar_predictores,PREDICTORES
from fase04_modelado.validacion_anidada.auditoria import activar_guardia
from fase04_modelado.validacion_anidada.particiones import construir_particiones
from fase04_modelado.validacion_anidada.seleccion_umbral import seleccionar_umbral
from fase04_modelado.validacion_anidada.seleccion_variante import seleccionar_variante
from fase04_modelado.validacion_anidada.evaluacion import medir
from fase04_modelado.validacion_anidada.ajuste import AjustadorVariante
from fase04_modelado.validacion_anidada.oof_internas import generar_oof

def datos_pequenos():
    n=60
    return pd.DataFrame({'failed_attempts_15min':np.arange(n)%3,'failed_attempts_1h':np.arange(n)%5,'time_since_previous_login_hours':np.arange(n)+1.,'has_previous_login':1.,'Device Type':['desktop','mobile']*(n//2),'Country':['NO','US']*(n//2)})[PREDICTORES]

def test_desempate_proximidad_y_mayor():
    # Con los tres umbrales se producen las mismas decisiones; debe preferirse 0,5.
    e,t=seleccionar_umbral([0,1],[.1,.8]);assert e['umbral']==.5 and set(e['umbrales_empatados'])=={.5,.8}
    # F1 2/3 en t=.25 y .75; F1 menor en .5; distancias iguales -> .75.
    e,t=seleccionar_umbral([1,0,0,1],[.75,.6,.55,.25]);assert e['umbral']==.75 and set(e['umbrales_empatados'])=={0.,.25,.75}
    assert t[t.empate_maximo].f1.nunique()==1

def test_orden_historico_y_politicas():
    e,t=seleccionar_umbral([0,1],[0.,0.]);assert e['politica']=='todos'
    assert set(t.politica)>={'todos','ninguno'} and t.loc[t.politica.eq('ninguno'),'TP'].eq(0).all()
    s=seleccionar_variante({n:e for n in reversed(NOMBRES)});assert s['modelo']==next(iter(NOMBRES)) and s['variantes_empatadas']==list(NOMBRES)

def test_metrica_sin_alertas_y_usuarios():
    m=medir([1,1,0,0],[.2,.3,.1,.2],[0,0,0,0],[1,1,2,3])
    assert m['precision']==m['recall']==m['f1']==0 and m['sin_predicciones_positivas']
    assert m['usuarios_ato_omitidos']==1 and m['usuarios_sin_ato_con_alerta']==0

def test_bloqueo_efectivo_test():
    activar_guardia()
    for nombre in ['dataset_test_fase04.csv','X_test_distancias_fase04.npy','y_test_fase04.npy']:
        with pytest.raises(PermissionError):open(nombre,'rb')

def test_exclusion_de_predictores():
    x=datos_pequenos();x['User ID']=123;x['Is Account Takeover']=1;x['IP Address']='x';x['Login Timestamp']='x'
    assert list(seleccionar_predictores(x))==PREDICTORES

@pytest.mark.parametrize('nombre',list(NOMBRES))
def test_ajuste_real_local_pequeno(nombre):
    x=datos_pequenos();y=pd.Series(([0]*8+[1]*2)*6)
    score,a=AjustadorVariante(nombre).predecir(x.iloc[:40],y.iloc[:40],x.iloc[40:])
    assert len(score)==20 and np.isfinite(score).all() and a['filas_ajuste']==40 and a['filas_validacion']==20
    assert a['entrada_predictores']==PREDICTORES and a['preprocesador_inmutable'] and a['validacion_inmutable']
    assert a['clases_ajuste']=={'0':32,'1':8} and a['pesos_teoricos_locales']=={'0':.625,'1':2.5}
    if nombre=='knn_ros':assert a['ros_solo_ajuste'] and a['clases_despues_ros']=={'0':32,'1':32}
    else:assert not a['ros_aplicado'] and a['filas_ajuste_modelo']==40

def test_invariancia_etiquetas_externas_indices_fijos(monkeypatch):
    x=datos_pequenos();usuarios=pd.Series(np.arange(60));y=pd.Series(([0,0,0,1]*15));a=np.arange(48);b=np.arange(48,60)
    internas=construir_particiones(y.iloc[a],usuarios.iloc[a],3)
    # Doble de ajuste determinista: la selección real recibe solo y de A.
    def predecir(self,xa,ya,xb):return np.full(len(xb),float(ya.mean())),{}
    monkeypatch.setattr(AjustadorVariante,'predecir',predecir)
    r1=generar_oof(x.iloc[a],y.iloc[a],usuarios.iloc[a],internas)
    alterada=y.copy();alterada.iloc[b]=1-alterada.iloc[b]
    r2=generar_oof(x.iloc[a],alterada.iloc[a],usuarios.iloc[a],internas)
    assert r1[1]==r2[1] and r1[2]==r2[2];pd.testing.assert_frame_equal(r1[0],r2[0])
