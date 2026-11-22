"""Validación de fuentes, eventos, usuarios y métricas antes de analizar."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pandas as pd
from fase04_modelado.metricas import calcular_metricas,METRICAS

RAIZ=Path('fase04_modelado/seleccion_supervisada')
FUENTES={'CV1':Path('fase04_modelado/resultados'),'CV2':Path('fase04_modelado/resultados_cv_usuario')}
NOMBRES={'arbol_baseline':'M1a · Árbol baseline','arbol_ponderado':'M1b · Árbol ponderado','gnb_baseline':'M2a · GaussianNB baseline','gnb_ponderado':'M2b · GaussianNB ponderado','knn_baseline':'M3a · KNN baseline','knn_ros':'M3b · KNN + ROS'}
CLAVE=['User ID','Login Timestamp','IP Address']
TARGET='Is Account Takeover'

def proteger_test(evento,args):
    """Guardia de aperturas: se permite código de pruebas, nunca datos test."""
    if evento=='open' and isinstance(args[0],(str,bytes,Path)):
        nombre=Path(str(args[0])).name.lower()
        if 'test' in nombre and nombre.endswith(('.csv','.npy','.joblib')):raise PermissionError('Acceso a artefactos test prohibido')

def activar_guardia():sys.addaudithook(proteger_test)

def sha(ruta):return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()

def guardar_json(ruta,datos):
    with Path(ruta).open('x',encoding='utf-8') as f:json.dump(datos,f,ensure_ascii=False,indent=2)

def guardar_csv(ruta,datos):
    with Path(ruta).open('x',encoding='utf-8',newline='') as f:datos.to_csv(f,index=False,float_format='%.17g')

class AuditorResultados:
    def __init__(self):
        self.train=pd.read_csv('dataset_train_fase04.csv',usecols=CLAVE+[TARGET])
        self.fuentes={};self.hashes={'dataset_train_fase04.csv':sha('dataset_train_fase04.csv')}

    def verificar(self):
        inventario=json.loads(Path('fase04_clustering/resultados/inventario_previo.json').read_text(encoding='utf-8'))
        for protocolo,r in FUENTES.items():
            for nombre in ['predicciones_oof.csv','comparacion_modelos.csv','metricas_por_fold.csv','distribucion_folds.csv','configuracion_auditoria.json']:
                p=r/nombre;valor=sha(p);assert valor==inventario[p.as_posix()]['sha256'],p
                self.hashes[p.as_posix()]=valor
            config=json.loads((r/'configuracion_auditoria.json').read_text(encoding='utf-8'))
            assert self.hashes['dataset_train_fase04.csv']==config['train_sha256']
            o=pd.read_csv(r/'predicciones_oof.csv');c=pd.read_csv(r/'comparacion_modelos.csv');f=pd.read_csv(r/'metricas_por_fold.csv');d=pd.read_csv(r/'distribucion_folds.csv').set_index('fold')
            assert set(o.modelo)==set(NOMBRES) and not o.duplicated(['modelo','evento_id']).any()
            referencia=None
            for nombre,g in o.groupby('modelo'):
                g=g.sort_values('evento_id').reset_index(drop=True)
                np.testing.assert_array_equal(g.evento_id,np.arange(len(self.train)))
                pd.testing.assert_frame_equal(g[CLAVE],self.train[CLAVE]);np.testing.assert_array_equal(g.y_true,self.train[TARGET].astype(int))
                assert g.groupby('User ID').fold.nunique().eq(1).all()
                if referencia is None:referencia=g.fold.to_numpy()
                else:np.testing.assert_array_equal(g.fold,referencia)
                np.testing.assert_array_equal(g.y_pred,(g.score>=.5).astype(int))
                m=calcular_metricas(g.y_true,g.score);row=c[c.modelo.eq(nombre)].iloc[0]
                for k in ['TP','FP','TN','FN',*METRICAS]:np.testing.assert_allclose(m[k],row[k],rtol=1e-12,atol=1e-15)
                for fold,q in g.groupby('fold'):
                    assert not set(q['User ID'])&set(g.loc[g.fold.ne(fold),'User ID'])
                    esperado={'validacion_eventos':len(q),'validacion_positivos':int(q.y_true.sum()),'validacion_usuarios':q['User ID'].nunique(),'validacion_usuarios_positivos':q.loc[q.y_true.eq(1),'User ID'].nunique()}
                    for k,v in esperado.items():assert d.loc[fold,k]==v
                    mf=calcular_metricas(q.y_true,q.score);row=f[f.modelo.eq(nombre)&f.fold.eq(fold)].iloc[0]
                    for k in ['TP','FP','TN','FN',*METRICAS]:np.testing.assert_allclose(mf[k],row[k],rtol=1e-12,atol=1e-15)
            self.fuentes[protocolo]=(o,c,f,d.reset_index())
        return self
