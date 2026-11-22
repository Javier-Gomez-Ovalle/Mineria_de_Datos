"""Un ajuste recibe X/y de ajuste y solo X de validación. No accede a y externa."""
import time,json
import numpy as np
import joblib
from imblearn.over_sampling import RandomOverSampler
from sklearn.utils.class_weight import compute_sample_weight
from fase04_modelado.modelos import crear_modelo
from fase04_modelado.auditoria import auditar_preprocesador
from fase04_preparacion.transformaciones import crear_preprocesador,ajustar_train,transformar
from .auditoria import hash_indices

class AjustadorVariante:
    def __init__(self,nombre):self.nombre=nombre

    def predecir(self,x_ajuste,y_ajuste,x_validacion):
        assert x_ajuste.index.is_unique and x_validacion.index.is_unique
        assert not set(x_ajuste.index)&set(x_validacion.index)
        assert set(y_ajuste)=={0,1} and x_ajuste.index.equals(y_ajuste.index)
        representacion,modelo=crear_modelo(self.nombre);inicio=time.perf_counter();prep=crear_preprocesador(representacion)
        xa=ajustar_train(prep,x_ajuste);huella=joblib.hash(prep);xb=transformar(prep,x_validacion);assert joblib.hash(prep)==huella
        segundos_pre=time.perf_counter()-inicio;audit=auditar_preprocesador(prep,x_ajuste)
        num=prep.named_transformers_['num']
        if 'escalar' in num.named_steps:audit['media_escalado']=num.named_steps['escalar'].mean_.tolist();audit['varianza_escalado']=num.named_steps['escalar'].var_.tolist()
        audit.update(modelo=self.nombre,ajuste_indices_sha256=hash_indices(x_ajuste.index),validacion_indices_sha256=hash_indices(x_validacion.index),filas_validacion=len(xb),preprocesador_inmutable=True,entrada_predictores=list(x_ajuste.columns))
        ya=y_ajuste.to_numpy();audit['clases_ajuste']={str(c):int((ya==c).sum()) for c in [0,1]}
        audit['pesos_teoricos_locales']={str(c):float(len(ya)/(2*(ya==c).sum())) for c in [0,1]}
        inicio=time.perf_counter();validacion_hash=joblib.hash(xb);audit['ros_aplicado']=self.nombre=='knn_ros'
        if self.nombre=='knn_ros':
            ros=RandomOverSampler(random_state=42,sampling_strategy=1.0);original_xa,original_ya=xa,ya
            xa,ya=ros.fit_resample(xa,ya)
            np.testing.assert_array_equal(xa,original_xa[ros.sample_indices_]);np.testing.assert_array_equal(ya,original_ya[ros.sample_indices_])
            assert ros.sample_indices_.min()>=0 and ros.sample_indices_.max()<len(x_ajuste)
            audit.update(ros_solo_ajuste=True,ros_indices_sha256=hash_indices(ros.sample_indices_),clases_despues_ros={str(c):int((ya==c).sum()) for c in [0,1]})
        segundos_ros=time.perf_counter()-inicio;kwargs={}
        if self.nombre=='gnb_ponderado':
            pesos=compute_sample_weight('balanced',ya)
            for c in [0,1]:np.testing.assert_allclose(pesos[ya==c],len(ya)/(2*(ya==c).sum()))
            kwargs['sample_weight']=pesos;audit['sample_weight_local']=True
        if self.nombre=='arbol_ponderado':assert modelo.class_weight=='balanced';audit['class_weight_local']=True
        inicio=time.perf_counter();modelo.fit(xa,ya,**kwargs);segundos_fit=time.perf_counter()-inicio
        inicio=time.perf_counter();col=int(np.flatnonzero(modelo.classes_==1)[0]);score=np.concatenate([modelo.predict_proba(xb[i:i+512])[:,col] for i in range(0,len(xb),512)]);segundos_pred=time.perf_counter()-inicio
        assert joblib.hash(xb)==validacion_hash and np.isfinite(score).all() and ((score>=0)&(score<=1)).all()
        audit.update(validacion_inmutable=True,filas_ajuste_modelo=len(ya),preprocesamiento_s=segundos_pre,ros_s=segundos_ros,entrenamiento_s=segundos_fit,prediccion_s=segundos_pred,parametros=modelo.get_params())
        return score,audit
