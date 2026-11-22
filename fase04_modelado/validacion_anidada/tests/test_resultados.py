"""Audita artefactos reales sin repetir los 120 ajustes del experimento."""
import json
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import confusion_matrix,f1_score,average_precision_score
from fase04_preparacion.seleccion import separar_datos,NUMERICAS,CATEGORICAS,PREDICTORES
from fase04_modelado.modelos import NOMBRES
from fase04_modelado.validacion_anidada.auditoria import RESULTADOS,activar_guardia,verificar_historicos,hash_indices,sha
from fase04_modelado.validacion_anidada.particiones import construir_particiones
from fase04_modelado.validacion_anidada.seleccion_umbral import seleccionar_umbral
from fase04_modelado.validacion_anidada.seleccion_variante import seleccionar_variante

@pytest.fixture(scope='module')
def datos():
    activar_guardia();d=pd.read_csv('dataset_train_fase04.csv');x,y,c=separar_datos(d)
    p=json.loads((RESULTADOS/'particiones.json').read_text());o=pd.read_csv(RESULTADOS/'predicciones_externas.csv',float_precision='round_trip')
    return x,y,c,p,o

def test_particiones_reproducibles_y_usuarios(datos):
    x,y,c,p,o=datos;ext=construir_particiones(y,c['User ID'],5);visitas=np.zeros(len(y),int)
    for (a,b),registro in zip(ext,p):
        np.testing.assert_array_equal(a,registro['ajuste']);np.testing.assert_array_equal(b,registro['validacion']);visitas[b]+=1
        assert not set(c.iloc[a]['User ID'])&set(c.iloc[b]['User ID'])
        internas=construir_particiones(y.iloc[a],c.iloc[a]['User ID'],3);v=[]
        for (ia,ib),r in zip(internas,registro['internas']):
            np.testing.assert_array_equal(a[ia],r['ajuste']);np.testing.assert_array_equal(a[ib],r['validacion']);v+=r['validacion']
            assert not set(c.iloc[r['ajuste']]['User ID'])&set(c.iloc[r['validacion']]['User ID'])
        np.testing.assert_array_equal(np.sort(v),a)
    assert np.all(visitas==1)

def test_oof_internas_y_seleccion_exacta(datos):
    x,y,c,p,o=datos
    for r in p:
        fold=r['fold_externo'];t=pd.read_csv(RESULTADOS/f'oof_internas_{fold}.csv',float_precision='round_trip');s=json.loads((RESULTADOS/f'decisiones_congeladas_{fold}.json').read_text(encoding='utf-8'));d={}
        assert sha(RESULTADOS/f'oof_internas_{fold}.csv')==s['oof_sha256']
        for n,g in t.groupby('modelo'):
            assert g.evento_id.is_unique;np.testing.assert_array_equal(g.evento_id,r['ajuste']);np.testing.assert_array_equal(g.y_true,y.iloc[g.evento_id]);np.testing.assert_array_equal(g.usuario,c.iloc[g.evento_id]['User ID'])
            for j,inner in enumerate(r['internas'],1):np.testing.assert_array_equal(g.loc[g.fold_interno.eq(j),'evento_id'],inner['validacion'])
            elegido,_=seleccionar_umbral(g.y_true,g.score);assert elegido==s['decisiones'][n];d[n]=elegido
        assert seleccionar_variante(d)==s['selector']

def test_oof_externas_decisiones_y_selector(datos):
    x,y,c,p,o=datos
    for n,g in o.groupby('modelo'):
        g=g.sort_values('evento_id');np.testing.assert_array_equal(g.evento_id,np.arange(len(y)));np.testing.assert_array_equal(g.y_true,y);pd.testing.assert_frame_equal(g[list(c)].reset_index(drop=True),c)
        np.testing.assert_array_equal(g.pred_aprendido,(g.score>=g.umbral).astype(int));np.testing.assert_array_equal(g.pred_05,(g.score>=.5).astype(int))
    for fold,g in o.groupby('fold_externo'):
        s=json.loads((RESULTADOS/f'decisiones_congeladas_{fold}.json').read_text(encoding='utf-8'))
        for n,q in g.groupby('modelo'):assert q.umbral.eq(s['decisiones'][n]['umbral']).all() and q.selector.eq(n==s['selector']['modelo']).all()
    selector=pd.read_csv(RESULTADOS/'predicciones_selector.csv',float_precision='round_trip');pd.testing.assert_frame_equal(selector,o[o.selector].reset_index(drop=True));assert selector.evento_id.nunique()==len(y)

def test_preprocesamiento_ros_pesos_locales(datos):
    x,y,c,p,o=datos;audits=json.loads((RESULTADOS/'auditoria_ajustes.json').read_text());assert len(audits)==120
    for a in audits:
        registro=p[a['fold_externo']-1];split=registro if a['nivel']=='externo' else registro['internas'][a['fold_interno']-1];ia=split['ajuste'];ib=split['validacion'];local=x.iloc[ia];ya=y.iloc[ia]
        assert a['ajuste_indices_sha256']==hash_indices(ia) and a['validacion_indices_sha256']==hash_indices(ib)
        assert a['entrada_predictores']==PREDICTORES and a['filas_ajuste']==len(ia) and a['filas_validacion']==len(ib)
        np.testing.assert_allclose(a['medianas'],local[NUMERICAS].median())
        for columna in CATEGORICAS:assert set(a['categorias'][columna])==set(local[columna].fillna('Desconocido'))
        if 'media_escalado' in a:
            z=np.log1p(local[NUMERICAS].fillna(local[NUMERICAS].median()));np.testing.assert_allclose(a['media_escalado'],z.mean());np.testing.assert_allclose(a['varianza_escalado'],z.var(ddof=0))
        for clase in [0,1]:assert a['clases_ajuste'][str(clase)]==int(ya.eq(clase).sum());assert a['pesos_teoricos_locales'][str(clase)]==len(ya)/(2*ya.eq(clase).sum())
        assert a['preprocesador_inmutable'] and a['validacion_inmutable']
        if a['modelo']=='knn_ros':assert a['ros_solo_ajuste'] and a['filas_ajuste_modelo']==2*ya.eq(0).sum()
        else:assert not a['ros_aplicado'] and a['filas_ajuste_modelo']==len(ia)
        if a['modelo']=='gnb_ponderado':assert a['sample_weight_local']
        if a['modelo']=='arbol_ponderado':assert a['class_weight_local'] and a['parametros']['class_weight']=='balanced'

def test_metricas_globales_y_folds(datos):
    *_,o=datos
    for archivo in ['metricas_globales.csv','metricas_por_fold.csv']:
        t=pd.read_csv(RESULTADOS/archivo,float_precision='round_trip')
        for row in t.itertuples():
            g=o[o.selector] if row.modelo=='selector_conjunto' else o[o.modelo.eq(row.modelo)]
            if archivo=='metricas_por_fold.csv':g=g[g.fold_externo.eq(row.fold_externo)]
            pred=g.pred_aprendido if row.regla=='aprendido' else g.pred_05;tn,fp,fn,tp=confusion_matrix(g.y_true,pred).ravel()
            assert (row.TP,row.FP,row.TN,row.FN)==(tp,fp,tn,fn);np.testing.assert_allclose(row.f1,f1_score(g.y_true,pred,zero_division=0))
            if row.modelo=='selector_conjunto' and archivo=='metricas_globales.csv':assert np.isnan(row.average_precision)
            else:np.testing.assert_allclose(row.average_precision,average_precision_score(g.y_true,g.score))
            positivos=set(g.loc[g.y_true.eq(1),'User ID']);detectados=set(g.loc[g.y_true.eq(1)&pred.eq(1),'User ID']);alertas=set(g.loc[pred.eq(1),'User ID'])
            assert row.usuarios_ato_detectados==len(detectados) and row.usuarios_ato_omitidos==len(positivos-detectados) and row.usuarios_sin_ato_con_alerta==len(alertas-positivos)

def test_historicos_preservados():assert verificar_historicos()>0
