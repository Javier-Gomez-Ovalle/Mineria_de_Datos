"""Invariantes evento-target antes y después de la ingeniería de características.

El target viaja como columna del evento. La referencia usa la clave de negocio,
no el índice de pandas ni posiciones que cambian con sort/reset_index.
"""
from pandas.api.types import is_datetime64_any_dtype

from .preprocessing import COLUMNA_TARGET, normalizar_target
from .timestamp_utils import convertir_login_timestamp


CLAVE_EVENTO = ["User ID", "Login Timestamp", "IP Address"]


def capturar_asociacion_target(df):
    """Valida y copia clave/etiqueta sin modificar el DataFrame recibido.

La fecha se canoniza solo en esta referencia para admitir la conversión
Unix/texto -> datetime que realiza features.py. Claves nulas o duplicadas
se rechazan: nunca se resuelve una asociación ambigua por posición.
"""
    columnas = CLAVE_EVENTO + [COLUMNA_TARGET]
    faltantes = [col for col in columnas if col not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas de asociación evento-target: {faltantes}")
    if not df.columns.is_unique:
        raise ValueError("Columnas duplicadas en la asociación evento-target.")
    referencia = df[columnas].copy()
    fecha = referencia["Login Timestamp"]
    if not is_datetime64_any_dtype(fecha.dtype):
        referencia["Login Timestamp"] = convertir_login_timestamp(fecha)
    for col in CLAVE_EVENTO:
        if referencia[col].isna().any() or referencia[col].astype(str).str.strip().eq("").any():
            raise ValueError(f"Clave de evento nula, vacía o inválida: {col}")
    if referencia.duplicated(CLAVE_EVENTO).any():
        raise ValueError("Clave de evento duplicada: asociación ambigua.")
    referencia[COLUMNA_TARGET] = normalizar_target(referencia[COLUMNA_TARGET])
    return referencia.reset_index(drop=True)


def verificar_asociacion_target(df, referencia):
    """Exige los mismos eventos y etiquetas, cualquiera que sea su orden."""
    actual = capturar_asociacion_target(df)
    esperado = capturar_asociacion_target(referencia)
    if len(actual) != len(esperado):
        raise ValueError("Cambió el número de filas: pérdida o adición de eventos.")
    cruce = actual.merge(
        esperado, on=CLAVE_EVENTO, how="outer", validate="one_to_one",
        suffixes=("_actual", "_original"), indicator=True,
    )
    if not cruce["_merge"].eq("both").all():
        raise ValueError("Cambió la identidad de los eventos: claves ausentes o nuevas.")
    if not cruce[f"{COLUMNA_TARGET}_actual"].eq(cruce[f"{COLUMNA_TARGET}_original"]).all():
        raise ValueError("Desalineación: cambió la etiqueta original de algún evento.")
