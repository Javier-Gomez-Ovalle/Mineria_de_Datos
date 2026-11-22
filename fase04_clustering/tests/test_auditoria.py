"""Pruebas de contratos y resultados, sin entrenamiento supervisado ni test."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import pytest
from PIL import Image
from sklearn.cluster import KMeans
from scipy.cluster.hierarchy import linkage,cut_tree
from threadpoolctl import threadpool_limits
from fase04_clustering.datos import PreparadorDatos
from fase04_clustering.evaluacion_externa import resumir_externo
from fase04_preparacion.seleccion import PREDICTORES,CLAVE,TARGET,seleccionar_predictores
from fase04_modelado.metricas import calcular_metricas,METRICAS

R=Path('fase04_clustering/resultados')

@pytest.fixture(scope='module')
def datos():return PreparadorDatos().cargar()

def test_exclusion_y_invariancia(datos):
    x=datos.x.copy();x[TARGET]=1;x['User ID']='prohibido';x['IP Address']='prohibido'
    pd.testing.assert_frame_equal(seleccionar_predictores(x),datos.x)
    assert list(datos.preprocesador.feature_names_in_)==PREDICTORES
    assert not any(v in ' '.join(datos.preprocesador.get_feature_names_out()) for v in CLAVE+[TARGET])

def test_transformaciones_finitas(datos):
    p=datos.preprocesador.named_transformers_['num'];raw=datos.x[PREDICTORES[:3]]
    medianas=raw.median().to_numpy();np.testing.assert_array_equal(p.named_steps['imputar'].statistics_,medianas)
    log=np.log1p(raw.fillna(raw.median()).to_numpy());np.testing.assert_allclose(p.named_steps['escalar'].mean_,log.mean(axis=0))
    np.testing.assert_allclose(datos.matriz[:,:3],(log-log.mean(axis=0))/log.std(axis=0),atol=1e-12)
    assert np.isfinite(datos.matriz).all()

def test_reproducibilidad(datos):
    a=np.load(R/'candidatos.npz');indices=np.sort(np.random.default_rng(42).choice(len(datos.x),4000,replace=False));np.testing.assert_array_equal(indices,a['indices_muestra'])
    with threadpool_limits(limits=2):
        m=KMeans(n_clusters=2,n_init=10,random_state=42,max_iter=300,algorithm='lloyd').fit(datos.matriz)
        np.testing.assert_array_equal(m.labels_,a['kmeans_2'])
        np.testing.assert_array_equal(cut_tree(linkage(datos.matriz[indices],method='ward'),n_clusters=2).ravel(),a['ward_2'])

@pytest.mark.parametrize('nombre',['kmeans_2','ward_2'])
def test_correspondencia_perfiles_externa(datos,nombre):
    t=pd.read_csv(R/f'etiquetas_{nombre}.csv');a=np.load(R/'candidatos.npz');assert t.evento_id.is_unique
    np.testing.assert_array_equal(t.cluster,a[nombre]);pd.testing.assert_frame_equal(t[CLAVE],datos.claves.iloc[t.evento_id][CLAVE].reset_index(drop=True))
    frozen=json.loads((R/'seleccion_congelada.json').read_text(encoding='utf-8'));assert hashlib.sha256((R/f'etiquetas_{nombre}.csv').read_bytes()).hexdigest()==frozen['seleccion'][nombre]['sha256']
    y=pd.read_csv('dataset_train_fase04.csv',usecols=[TARGET])[TARGET].astype(int);t[TARGET]=y.iloc[t.evento_id].to_numpy()
    pd.testing.assert_frame_equal(resumir_externo(t),pd.read_csv(R/f'evaluacion_externa_{nombre}.csv'),check_dtype=False)
    perfil=pd.read_csv(R/f'perfil_numerico_{nombre}.csv');x=datos.x.iloc[t.evento_id].copy();x['cluster']=t.cluster.to_numpy()
    np.testing.assert_allclose(perfil.failed_attempts_1h_mean,x.groupby('cluster').failed_attempts_1h.mean())
    cat=pd.read_csv(R/f'perfil_categorico_{nombre}.csv');assert cat.groupby(['cluster','variable']).eventos.sum().tolist()==[int(v) for v in np.repeat(t.groupby('cluster').size().values,3)]

@pytest.mark.parametrize('carpeta',['resultados','resultados_cv_usuario'])
def test_oof_metricas_y_confusiones(carpeta):
    r=Path('fase04_modelado')/carpeta;o=pd.read_csv(r/'predicciones_oof.csv');c=pd.read_csv(r/'comparacion_modelos.csv').set_index('modelo');f=pd.read_csv(r/'metricas_por_fold.csv')
    for n,p in o.groupby('modelo'):
        assert len(p)==46305 and p.evento_id.nunique()==46305
        np.testing.assert_array_equal(p.y_pred,(p.score>=.5).astype(int))
        m=calcular_metricas(p.y_true,p.score)
        for key in ['TP','FP','TN','FN',*METRICAS]:np.testing.assert_allclose(m[key],c.loc[n,key],atol=1e-14)
        assert sum(m[k] for k in ['TP','FP','TN','FN'])==46305
        for fold,q in p.groupby('fold'):
            mf=calcular_metricas(q.y_true,q.score);row=f[f.modelo.eq(n)&f.fold.eq(fold)].iloc[0]
            for key in ['TP','FP','TN','FN',*METRICAS]:np.testing.assert_allclose(mf[key],row[key],atol=1e-14)

def test_png_svg():
    rutas=list((R/'graficas').glob('*.png'))+list(Path('fase04_modelado/resultados_presentacion_supervisado').rglob('*.png'))
    assert len(rutas)==30
    for p in rutas:
        assert p.with_suffix('.svg').is_file()
        with Image.open(p) as im:assert min(im.info['dpi'])>=299 and min(im.size)>1000

def test_consistencia_exportacion():
    t=pd.read_csv('fase04_modelado/resultados_presentacion_supervisado/metricas_verificadas.csv')
    for protocolo,carpeta in [('CV1','resultados'),('CV2','resultados_cv_usuario')]:
        original=pd.read_csv(Path('fase04_modelado')/carpeta/'comparacion_modelos.csv')
        pd.testing.assert_frame_equal(t[t.protocolo.eq(protocolo)].drop(columns='protocolo').reset_index(drop=True),original,check_dtype=False)
