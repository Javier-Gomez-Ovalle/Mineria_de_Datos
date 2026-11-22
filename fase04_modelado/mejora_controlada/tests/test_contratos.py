import json
import numpy as np
import pandas as pd
import pytest
from fase04_modelado.mejora_controlada.contratos import seleccionar,fraccion,CONFIGS,HIST,OUT,verificar_particiones,verificar_integridad,sha,hash_indices
from fase04_modelado.mejora_controlada.ajuste import predecir
from fase04_modelado.validacion_anidada.seleccion_umbral import seleccionar_umbral
from fase04_modelado.validacion_anidada.particiones import construir_particiones
from fase04_preparacion.seleccion import separar_datos,PREDICTORES,NUMERICAS,CATEGORICAS
from fase04_modelado.mejora_controlada.evaluar import grupos,metricas

@pytest.mark.parametrize('seed',[0,42,123])
def test_umbral_equivalente_exhaustivo(seed):
    rng=np.random.default_rng(seed);y=np.r_[np.ones(8,int),np.zeros(72,int)];s=rng.choice([0,.2,.4,.5,.7,1.],80)
    fast,_=seleccionar(y,s);slow,_=seleccionar_umbral(y,s)
    assert fast['umbral']==slow['umbral'] and float(fraccion(fast))==slow['f1']

def test_umbral_scores_continuos_y_extremos():
    rng=np.random.default_rng(7);y=np.r_[np.ones(5,int),np.zeros(30,int)]
    for s in [rng.random(35),np.zeros(35),np.ones(35)]:
        a,_=seleccionar(y,s);b,_=seleccionar_umbral(y,s);assert a['umbral']==b['umbral']

def test_reproducibilidad_local_y_preprocesador():
    x=pd.DataFrame({'failed_attempts_15min':[0.,1.,2.,0.]*5,'failed_attempts_1h':[0.,2.,3.,1.]*5,'time_since_previous_login_hours':[np.nan,1.,2.,4.]*5,'has_previous_login':[0.,1.,1.,1.]*5,'Device Type':['desktop','mobile']*10,'Country':['NO','RO']*10})[PREDICTORES]
    y=pd.Series([0,1,0,0]*5);a=x.iloc[:16];b=x.iloc[16:].copy();b['Country']='UNSEEN';b['failed_attempts_1h']=99999
    s,audit=predecir(a,y.iloc[:16],b,CONFIGS[0]);s2,audit2=predecir(a,y.iloc[:16],b,CONFIGS[0]);np.testing.assert_allclose(s,s2,rtol=0,atol=1e-15)
    assert 'UNSEEN' not in audit['categorias']['Country'];np.testing.assert_allclose(audit['medianas'],a[NUMERICAS].median())
    assert audit['ros_aplicado'] is False and audit['validacion_inmutable'] and audit['filas_ajuste']==16

def test_rechaza_solapamiento():
    x=pd.DataFrame({'a':[1,2]});y=pd.Series([0,1])
    with pytest.raises(AssertionError):predecir(x,y,x,CONFIGS[0])

def test_bloqueo_test_antes_de_acceso():
    from fase04_modelado.validacion_anidada.auditoria import guardia
    with pytest.raises(PermissionError):guardia('open',('dataset_test_fase04.csv','r',0))

def test_integridad_historica():assert verificar_integridad()==406

@pytest.fixture(scope='module')
def datos():
    df=pd.read_csv('dataset_train_fase04.csv');x,y,k=separar_datos(df);return x,y,k,json.loads((HIST/'particiones.json').read_text(encoding='utf-8'))

def test_particiones_reproducibles(datos):
    x,y,k,parts=datos;verificar_particiones(parts,k['User ID'],len(y));fresh=construir_particiones(y,k['User ID'],5)
    for p,(a,b) in zip(parts,fresh):
        np.testing.assert_array_equal(a,p['ajuste']);np.testing.assert_array_equal(b,p['validacion'])
        inner=construir_particiones(y.iloc[a],k['User ID'].iloc[a],3)
        for q,(c,d) in zip(p['internas'],inner):
            np.testing.assert_array_equal(a[c],q['ajuste']);np.testing.assert_array_equal(a[d],q['validacion'])

def test_oof_interna_seleccion_y_congelacion(datos):
    x,y,k,parts=datos
    from fractions import Fraction
    from fase04_modelado.modelos import NOMBRES
    for p in parts:
        f=p['fold_externo'];d=json.loads((OUT/f'decision_congelada_{f}.json').read_text(encoding='utf-8'));assert d['oof_sha256']==sha(OUT/f'oof_internas_{f}.csv')
        o=pd.read_csv(OUT/f'oof_internas_{f}.csv',float_precision='round_trip')
        for ci,g in o.groupby('configuracion'):
            assert g.evento_id.is_unique and set(g.evento_id)==set(p['ajuste'])
            np.testing.assert_array_equal(g.y_true,y.iloc[g.evento_id]);np.testing.assert_array_equal(g.usuario,k['User ID'].iloc[g.evento_id])
            for ii,q in enumerate(p['internas'],1):assert set(g[g.fold_interno.eq(ii)].evento_id)==set(q['validacion'])
            dec,_=seleccionar(g.y_true,g.score);assert dec['umbral']==d['configuraciones'][ci]['umbral'];assert fraccion(dec)==fraccion(d['configuraciones'][ci])
        assert d['elegida']==max(range(4),key=lambda i:fraccion(d['configuraciones'][i]))
        old=json.loads((HIST/f'decisiones_congeladas_{f}.json').read_text(encoding='utf-8'));names=list(NOMBRES)+['random_forest'];ratios=[Fraction(old['decisiones'][n]['f1_numerador'],old['decisiones'][n]['f1_denominador']) for n in NOMBRES]+[fraccion(d['configuraciones'][d['elegida']])]
        assert d['selector_ampliado']==names[max(range(7),key=lambda i:ratios[i])]

def test_auditoria_65_ajustes_locales(datos):
    x,y,k,parts=datos;a=json.loads((OUT/'auditoria_ajustes.json').read_text(encoding='utf-8'));assert len(a)==65
    for r in a:
        p=parts[r['fold_externo']-1];q=p if r['nivel']=='externo' else p['internas'][r['fold_interno']-1];xa=x.iloc[q['ajuste']]
        assert r['filas_ajuste']==len(xa) and r['filas_validacion']==len(q['validacion'])
        assert r['ajuste_indices_sha256']==hash_indices(q['ajuste']) and r['validacion_indices_sha256']==hash_indices(q['validacion'])
        np.testing.assert_allclose(r['medianas'],xa[NUMERICAS].median())
        for c in CATEGORICAS:assert set(r['categorias'][c])==set(xa[c].fillna('Desconocido'))
        assert not r['ros_aplicado'] and r['validacion_inmutable'] and r['preprocesador_inmutable']

def test_oof_externa_correspondencia(datos):
    x,y,k,parts=datos;o=pd.read_csv(OUT/'predicciones_externas_rf.csv',float_precision='round_trip').sort_values('evento_id')
    np.testing.assert_array_equal(o.evento_id,np.arange(len(y)));np.testing.assert_array_equal(o.y_true,y)
    for c in k:np.testing.assert_array_equal(o[c],k[c])
    for p in parts:
        f=p['fold_externo'];g=o[o.fold_externo.eq(f)];assert set(g.evento_id)==set(p['validacion']);d=json.loads((OUT/f'decision_congelada_{f}.json').read_text(encoding='utf-8'));assert g.umbral.eq(d['umbral']).all()
    np.testing.assert_array_equal(o.pred_aprendido,(o.score>=o.umbral).astype(int));np.testing.assert_array_equal(o.pred_05,(o.score>=.5).astype(int))

def test_metricas_desde_predicciones():
    globales=pd.read_csv(OUT/'comparacion_global.csv');folds=pd.read_csv(OUT/'metricas_por_fold.csv')
    for name,g in grupos():
        for rule,col in [('aprendido','pred_aprendido'),('fijo_05','pred_05')]:
            r=globales[globales.modelo.eq(name)&globales.regla.eq(rule)].iloc[0];m=metricas(g,col,not name.startswith('selector'))
            for key,val in m.items():np.testing.assert_allclose(r[key],val,rtol=1e-12,atol=1e-15,equal_nan=True)
            for f,v in g.groupby('fold_externo'):
                r=folds[folds.modelo.eq(name)&folds.regla.eq(rule)&folds.fold.eq(f)].iloc[0]
                for key,val in metricas(v,col).items():np.testing.assert_allclose(r[key],val,rtol=1e-12,atol=1e-15,equal_nan=True)

def test_configuracion_y_registros():
    c=json.loads((OUT/'configuracion_congelada.json').read_text(encoding='utf-8'));e=json.loads((OUT/'ejecucion.json').read_text(encoding='utf-8'))
    assert c['propuesta_sha256']==sha('PROPUESTA_EXPERIMENTOS_MEJORA_FASE04.md') and c['train_sha256']==sha('dataset_train_fase04.csv')
    assert e['ajustes']==65 and not e['test_leido'] and not e['modelo_final_entrenado']
    assert c['predictores']==PREDICTORES and all(v['random_state']==42 for v in c['configuraciones'])

def test_graficas_completas():
    from PIL import Image
    c=json.loads((OUT/'catalogo_graficas.json').read_text(encoding='utf-8'));assert len(c)==14
    for v in c:
        with Image.open(OUT/v['archivo']) as im:assert im.width>=1500 and im.height>=1200;im.verify()
        assert (OUT/v['vector']).is_file()
