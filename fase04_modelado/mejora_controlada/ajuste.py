"""Ajuste sin etiquetas de validación; responsabilidad limitada a un fold."""
import time
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from fase04_preparacion.transformaciones import crear_preprocesador, ajustar_train, transformar
from fase04_modelado.auditoria import auditar_preprocesador
from .contratos import hash_indices

def crear_bosque(config):
    return RandomForestClassifier(n_estimators=100,max_features='sqrt',bootstrap=True,class_weight='balanced_subsample',random_state=42,n_jobs=2,**config)

def predecir(xa,ya,xb,config):
    assert xa.index.is_unique and xb.index.is_unique and not set(xa.index)&set(xb.index)
    assert xa.index.equals(ya.index) and set(ya)=={0,1}
    t=time.perf_counter();prep=crear_preprocesador('arbol');a=ajustar_train(prep,xa)
    before=joblib.hash(prep);b=transformar(prep,xb);assert before==joblib.hash(prep)
    audit=auditar_preprocesador(prep,xa);pre_s=time.perf_counter()-t
    original=joblib.hash(b);model=crear_bosque(config);t=time.perf_counter();model.fit(a,ya);fit_s=time.perf_counter()-t
    t=time.perf_counter();score=model.predict_proba(b)[:,list(model.classes_).index(1)];pred_s=time.perf_counter()-t
    assert joblib.hash(b)==original and np.isfinite(score).all()
    audit.update(ajuste_indices_sha256=hash_indices(xa.index),validacion_indices_sha256=hash_indices(xb.index),filas_validacion=len(xb),ros_aplicado=False,validacion_inmutable=True,preprocesador_inmutable=True,preprocesamiento_s=pre_s,entrenamiento_s=fit_s,prediccion_s=pred_s,parametros=model.get_params())
    return score,audit
