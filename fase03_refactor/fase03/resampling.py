"""
resampling.py
=============
Remuestreo EXCLUSIVO sobre TRAIN (Etapa 2). Función de módulo, sin estado.

POR QUÉ RandomOverSampler Y NO SMOTE
- Duplica filas reales; no inventa puntos por interpolación. Con muy pocos
  ATO reales, interpolar entre vecinos no es defendible.
- Sin SMOTE no hay restricción de vecinos mínimos.

CUÁNDO SE LLAMA: después del split y del preprocesamiento (la matriz ya es
numérica y sin NaN). NUNCA recibe TEST: la firma solo admite (X_train, y_train).

RIESGO A DOCUMENTAR: con RATIO_OVERSAMPLING=1.0 cada fila positiva se
duplica ~ (n_negativos / n_positivos) veces. El árbol verá muchas copias de
pocos eventos ATO reales. El ratio es configurable en ConfiguracionPipeline.
"""
from imblearn.over_sampling import RandomOverSampler


def _conteo(y):
    return {int(k): int(v) for k, v in y.value_counts().items()}


def remuestrear_train(X_train, y_train, config):
    """Devuelve (X_res, y_res, info). Falla si TRAIN no tiene ambas clases."""
    antes = _conteo(y_train)
    if len(antes) < 2 or min(antes.values()) == 0:
        raise ValueError(f"TRAIN no contiene ambas clases: {antes}. No se remuestrea.")

    sobremuestreador = RandomOverSampler(
        sampling_strategy=config.RATIO_OVERSAMPLING,
        random_state=config.RANDOM_STATE,
    )
    X_res, y_res = sobremuestreador.fit_resample(X_train, y_train)
    despues = _conteo(y_res)

    info = {
        "metodo": "RandomOverSampler",
        "ratio": config.RATIO_OVERSAMPLING,
        "antes": antes,
        "despues": despues,
        "aplicado_a": "TRAIN unicamente",
    }
    print(f"  Remuestreo TRAIN ({info['metodo']}, ratio={info['ratio']}): "
          f"{antes} -> {despues}. TEST no se modifica.")
    return X_res, y_res, info