"""
preprocessing.py
================
Definición de X e y, imputación y encoding (Etapa 2). Funciones de módulo.

CONTRATO DE COLUMNAS
- y  = Is Account Takeover (normalizado a 0/1, sin NaN).
- X  = solo las columnas de COLUMNAS_FEATURES.
- Fuera de X (identificadores, texto libre, fechas crudas, alta cardinalidad
  no evaluada, o redundantes): ver COLUMNAS_EXCLUIDAS_DE_X. Cada exclusión es
  una decisión, no un descuido.

IMPUTACIÓN (los NaN de esta fase NO son errores)
- Numéricas: mediana calculada SOLO con TRAIN. Además, para distancia y
  velocidad se crea un indicador "_faltante" (0/1) ANTES de imputar, porque
  su NaN no es solo "primer login": también ocurre cuando el país no tiene
  centroide. El indicador conserva esa información. Es función de la propia
  fila (no aprende nada), por lo que no hay leakage.
- Binarias con NaN (p. ej. country_mismatch cuando la IP no se resolvió):
  centinela -1 = "desconocido". El árbol puede aislarlo. No se fuerza a 0.
- Categóricas: "desconocido" + OneHotEncoder(handle_unknown="ignore").

SCALING y PCA: SOLO experimentales (final del módulo). NO los usa pipeline.py.
Un Árbol de Decisión es invariante al escalado, y PCA destruye la
interpretabilidad que justifica usar un árbol.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler

COLUMNA_TARGET = "Is Account Takeover"
COLUMNA_ID_USUARIO = "User ID"

COLUMNAS_NUMERICAS = [
    "failed_attempts_15min", "failed_attempts_1h",
    "time_since_previous_login_hours", "distance_previous_km",
    "required_speed_kmh",
]
COLUMNAS_BINARIAS = [
    "Is Attack IP", "login_exitoso_normalizado", "has_previous_login",
    "impossible_travel", "is_outside_shift", "country_mismatch",
    "inactive_account_success",
]
COLUMNAS_CATEGORICAS = [
    "Device Type", "Rol_Hospitalario", "Pais_Residencia", "Ciudad_Base",
    "Turno_Asignado", "Estado_Cuenta",
]
INDICADORES_FALTANTE = {
    "distance_previous_km": "distance_previous_km_faltante",
    "required_speed_kmh": "required_speed_kmh_faltante",
}
COLUMNAS_BINARIAS_X = COLUMNAS_BINARIAS + list(INDICADORES_FALTANTE.values())
COLUMNAS_FEATURES = COLUMNAS_NUMERICAS + COLUMNAS_BINARIAS_X + COLUMNAS_CATEGORICAS

COLUMNAS_EXCLUIDAS_DE_X = [
    COLUMNA_TARGET, COLUMNA_ID_USUARIO,
    "IP Address", "Nombre_Completo",                        # identificadores
    "Login Timestamp", "previous_login_timestamp", "Fecha_Ingreso",  # fechas crudas
    "Login Successful",                                     # ya está login_exitoso_normalizado
    "Country", "ip_country_code", "ip_country_name",        # redundantes con country_mismatch
    "Region", "City", "ASN", "ip_asn", "ip_as_name", "ip_as_domain",  # alta cardinalidad
]

VALOR_DESCONOCIDO_BINARIO = -1.0
VALOR_DESCONOCIDO_CATEGORICO = "desconocido"


def normalizar_target(serie):
    """Convierte Is Account Takeover a 0/1. Un NaN o un valor no reconocido
    DETIENE el proceso: nunca se asume."""
    if serie.isna().any():
        raise ValueError(
            f"'{COLUMNA_TARGET}' contiene {int(serie.isna().sum())} valores nulos."
        )
    texto = serie.astype(str).str.strip().str.lower()
    mapa = {"true": 1, "false": 0, "1": 1, "0": 0, "1.0": 1, "0.0": 0}
    y = texto.map(mapa)
    if y.isna().any():
        raros = sorted(texto[y.isna()].unique().tolist())[:10]
        raise ValueError(f"Valores no reconocidos en '{COLUMNA_TARGET}': {raros}")
    return y.astype("int64").rename(COLUMNA_TARGET)


def separar_x_y(df):
    """Devuelve (X, y). X nunca contiene el target, User ID ni identificadores."""
    origen = COLUMNAS_NUMERICAS + COLUMNAS_BINARIAS + COLUMNAS_CATEGORICAS
    faltantes = [c for c in origen + [COLUMNA_TARGET] if c not in df.columns]
    if faltantes:
        raise KeyError(f"Faltan columnas necesarias para X/y: {faltantes}")

    y = normalizar_target(df[COLUMNA_TARGET])
    X = df[origen].copy()

    for col in COLUMNAS_NUMERICAS + COLUMNAS_BINARIAS:
        X[col] = X[col].astype("float64")
    for col in COLUMNAS_CATEGORICAS:
        X[col] = X[col].astype("object")

    for col_origen, col_indicador in INDICADORES_FALTANTE.items():
        X[col_indicador] = X[col_origen].isna().astype("float64")

    X = X[COLUMNAS_FEATURES]

    if COLUMNA_TARGET in X.columns or COLUMNA_ID_USUARIO in X.columns:
        raise RuntimeError("LEAKAGE: el target o User ID están en X.")
    prohibidas = sorted(set(X.columns) & set(COLUMNAS_EXCLUIDAS_DE_X))
    if prohibidas:
        raise RuntimeError(f"Columnas excluidas presentes en X: {prohibidas}")
    return X, y


def construir_preprocesador():
    """ColumnTransformer sin ajustar. La salida es DataFrame (set_output)."""
    numerico = SimpleImputer(strategy="median", keep_empty_features=True)
    binario = SimpleImputer(
        strategy="constant", fill_value=VALOR_DESCONOCIDO_BINARIO,
        keep_empty_features=True,
    )
    categorico = Pipeline([
        ("imputador", SimpleImputer(
            strategy="constant", fill_value=VALOR_DESCONOCIDO_CATEGORICO)),
        ("codificador", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    preprocesador = ColumnTransformer(
        transformers=[
            ("num", numerico, COLUMNAS_NUMERICAS),
            ("bin", binario, COLUMNAS_BINARIAS_X),
            ("cat", categorico, COLUMNAS_CATEGORICAS),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )
    preprocesador.set_output(transform="pandas")
    return preprocesador


def verificar_matriz_numerica(X, etiqueta):
    """Bloquea si hay NaN o infinitos después del preprocesamiento."""
    valores = X.to_numpy(dtype="float64")
    n_nan = int(np.isnan(valores).sum())
    n_inf = int(np.isinf(valores).sum())
    if n_nan or n_inf:
        raise ValueError(f"{etiqueta}: {n_nan} NaN y {n_inf} infinitos tras preprocesar.")


def preprocesar_train_test(X_train, X_test):
    """fit SOLO con TRAIN; TEST únicamente recibe transform().
    Devuelve (preprocesador, X_train_t, X_test_t)."""
    preprocesador = construir_preprocesador()
    X_train_t = preprocesador.fit_transform(X_train)   # fit exclusivo de TRAIN
    X_test_t = preprocesador.transform(X_test)         # TEST: sin refit
    verificar_matriz_numerica(X_train_t, "TRAIN")
    verificar_matriz_numerica(X_test_t, "TEST")
    print(f"  Preprocesamiento: TRAIN {X_train_t.shape} | TEST {X_test_t.shape} "
          "(ajustado solo con TRAIN)")
    return preprocesador, X_train_t, X_test_t


# ============================================================================
# EXPERIMENTAL — NO forma parte del pipeline principal
# ============================================================================

def escalar_train_test_experimental(X_train_t, X_test_t):
    """EXPERIMENTAL. RobustScaler ajustado SOLO con TRAIN sobre las numéricas
    continuas (prefijo 'num__'). No lo llama pipeline.py."""
    columnas = [c for c in X_train_t.columns if c.startswith("num__")]
    escalador = RobustScaler().set_output(transform="pandas")
    X_train_e = X_train_t.copy()
    X_test_e = X_test_t.copy()
    X_train_e[columnas] = escalador.fit_transform(X_train_t[columnas])
    X_test_e[columnas] = escalador.transform(X_test_t[columnas])
    return escalador, X_train_e, X_test_e


def evaluar_pca_experimental(X_train_t, umbrales=(0.90, 0.95, 0.99)):
    """EXPERIMENTAL. Recibe SOLO TRAIN (la firma impide ajustar con TEST).
    Estandariza y ajusta PCA para medir dimensionalidad efectiva."""
    X_std = StandardScaler().fit_transform(X_train_t.to_numpy(dtype="float64"))
    pca = PCA(svd_solver="full").fit(X_std)
    acumulada = np.cumsum(pca.explained_variance_ratio_)
    n_para = {
        f"{int(round(u * 100))}%": int(min(np.searchsorted(acumulada, u) + 1, len(acumulada)))
        for u in umbrales
    }
    return {
        "n_features": int(X_std.shape[1]),
        "n_componentes": n_para,
        "varianza_acumulada": acumulada.tolist(),
        "ajustado_con": "TRAIN unicamente",
    }