"""Pruebas reproducibles sin estimadores ni conjunto test."""
import ast,json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from PIL import Image
from sklearn.metrics import confusion_matrix,precision_score,recall_score,f1_score,average_precision_score
from fase04_modelado.seleccion_supervisada.auditoria import RAIZ,AuditorResultados,activar_guardia,proteger_test,NOMBRES
from fase04_modelado.seleccion_supervisada.umbrales import calcular,rejilla

@pytest.fixture(scope='module')
def auditor():
    activar_guardia();return AuditorResultados().verificar()

def leer(nombre):return pd.read_csv(RAIZ/'resultados'/f'{nombre}.csv',float_precision='round_trip')

def test_correspondencia_y_hashes(auditor):
    assert len(auditor.train)==46305 and auditor.train['Is Account Takeover'].sum()==36
    registro=json.loads((RAIZ/'resultados/auditoria_fuentes.json').read_text(encoding='utf-8'));assert registro['hashes']==auditor.hashes

@pytest.mark.parametrize('protocolo',['CV1','CV2'])
def test_cobertura_separacion_y_reproducibilidad(auditor,protocolo):
    o=auditor.fuentes[protocolo][0]
    for _,g in o.groupby('modelo'):
        assert len(g)==46305 and g.evento_id.is_unique and g.groupby('User ID').fold.nunique().eq(1).all()
        for fold,q in g.groupby('fold'):assert not set(q['User ID'])&set(g.loc[g.fold.ne(fold),'User ID'])
    for nombre in NOMBRES:
        g=o[o.modelo.eq(nombre)];scores=np.concatenate([v[0].loc[v[0].modelo.eq(nombre),'score'] for v in auditor.fuentes.values()]);grid=rejilla(scores)
        np.testing.assert_array_equal(grid,rejilla(scores[::-1]));exportado=leer('umbrales_globales');np.testing.assert_array_equal(grid,exportado.loc[exportado.protocolo.eq(protocolo)&exportado.modelo.eq(nombre),'umbral'])

@pytest.mark.parametrize('protocolo',['CV1','CV2'])
def test_metricas_exhaustivas_y_folds(auditor,protocolo):
    o=auditor.fuentes[protocolo][0]
    for fuente in ['umbrales_globales','umbrales_por_fold']:
        t=leer(fuente);t=t[t.protocolo.eq(protocolo)]
        for row in t.itertuples():
            g=o[o.modelo.eq(row.modelo)]
            if fuente.endswith('fold'):g=g[g.fold.eq(row.fold)]
            pred=g.score>=row.umbral;tn,fp,fn,tp=confusion_matrix(g.y_true,pred,labels=[0,1]).ravel()
            assert (row.TP,row.FP,row.TN,row.FN)==(tp,fp,tn,fn)
            np.testing.assert_allclose([row.precision,row.recall,row.f1,row.average_precision],[precision_score(g.y_true,pred,zero_division=0),recall_score(g.y_true,pred,zero_division=0),f1_score(g.y_true,pred,zero_division=0),average_precision_score(g.y_true,g.score)],atol=1e-15)
            assert row.alertas==tp+fp and row.sin_predicciones_positivas==(tp+fp==0)
            np.testing.assert_allclose(row.porcentaje_alertas,100*(tp+fp)/len(g))

def test_empates_sin_alertas_y_ap():
    y=[0,1,0,1];s=[0,.2,.4,.4];a=calcular(y,s,.4);b=calcular(y,s,np.nextafter(1.,np.inf))
    assert (a['TP'],a['FP'],a['FN'],a['TN'])==(1,1,1,1)
    assert b['precision']==b['recall']==b['f1']==b['alertas']==0 and b['sin_predicciones_positivas']
    assert a['average_precision']==b['average_precision']
    with pytest.raises(ValueError):calcular(y,[0,np.nan,.4,.4],.4)

def test_igualdad_gaussian_y_knn_ros(auditor):
    for o,*_ in auditor.fuentes.values():
        grupos={n:g.sort_values('evento_id') for n,g in o.groupby('modelo')}
        np.testing.assert_array_equal(grupos['gnb_baseline'].score,grupos['gnb_ponderado'].score)
        assert set(grupos['gnb_baseline'].score)=={0.,1.}
        np.testing.assert_array_equal(grupos['knn_baseline'].score>=.2,grupos['knn_ros'].score>=.2)

def test_errores_alineados(auditor):
    e=leer('errores_eventos_referencias')
    for (protocolo,nombre,t),g in e.groupby(['protocolo','modelo','umbral']):
        o=auditor.fuentes[protocolo][0];o=o[o.modelo.eq(nombre)].set_index('evento_id');q=o.loc[g.evento_id]
        np.testing.assert_array_equal(g.y_true,q.y_true);np.testing.assert_array_equal(g.y_pred,(q.score>=t).astype(int))
        assert g.evento_id.is_unique and g.y_true.ne(g.y_pred).all()
        np.testing.assert_array_equal(g.tipo_error,np.where(g.y_true.eq(1),'FN','FP'))

def test_bloqueo_test_y_ausencia_ajuste():
    for nombre in ['dataset_test_fase04.csv','X_test_distancias_fase04.npy','y_test_fase04.npy']:
        with pytest.raises(PermissionError):proteger_test('open',(nombre,'r',0))
    proteger_test('open',('test_seleccion.py','r',0))
    for p in RAIZ.glob('*.py'):
        arbol=ast.parse(p.read_text(encoding='utf-8'))
        assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ['fit','fit_transform','fit_predict','partial_fit'] for n in ast.walk(arbol))

def test_graficas_y_confusiones():
    catalogo=json.loads((RAIZ/'catalogo_graficas.json').read_text(encoding='utf-8'));assert len(catalogo)==24
    assert sum('confusiones' in c['nombre'] for c in catalogo)==12
    for c in catalogo:
        with Image.open(c['png']) as im:assert min(im.info['dpi'])>=299 and min(im.size)>1000
        svg=Path(c['svg']).read_text(encoding='utf-8');assert '<svg' in svg and '36 ATO' in svg
    detalle=RAIZ/'graficas/08_detalle_fp_umbrales_positivos.png'
    with Image.open(detalle) as im:assert min(im.info['dpi'])>=299
    assert detalle.with_suffix('.svg').is_file()

def test_resumen_folds():
    f=leer('umbrales_por_fold');r=leer('resumen_folds')
    for row in r.itertuples():
        q=f[f.protocolo.eq(row.protocolo)&f.modelo.eq(row.modelo)&f.umbral.eq(row.umbral)]
        assert len(q)==5
        for m in ['precision','recall','f1','average_precision']:
            np.testing.assert_allclose([getattr(row,m+'_mean'),getattr(row,m+'_std')],[q[m].mean(),q[m].std(ddof=1)],atol=1e-15)
