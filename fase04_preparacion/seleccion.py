"""Contrato explicito de predictores y separacion de trazabilidad."""
import numpy as np
import pandas as pd

TARGET = "Is Account Takeover"
CLAVE = ["User ID", "Login Timestamp", "IP Address"]
CATEGORICAS = ["Device Type", "Country"]
NUMERICAS = ["failed_attempts_15min", "failed_attempts_1h", "time_since_previous_login_hours"]
BINARIAS = ["has_previous_login"]
PREDICTORES = NUMERICAS + BINARIAS + CATEGORICAS


def seleccionar_predictores(datos):
    """Lista positiva: ninguna columna adicional puede entrar a X."""
    x = datos.loc[:, PREDICTORES].copy()
    for c in NUMERICAS + BINARIAS:
        x[c] = pd.to_numeric(x[c], errors="raise").astype(float)
        if np.isinf(x[c]).any() or (x[c].dropna() < 0).any():
            raise ValueError(f"Magnitud invalida: {c}")
    if not x[BINARIAS[0]].isin([0, 1]).all():
        raise ValueError("Indicador de historial invalido")
    if not x[NUMERICAS[2]].isna().equals(x[BINARIAS[0]].eq(0)):
        raise ValueError("Ausencia del intervalo incoherente con historial")
    for c in CATEGORICAS:
        x[c] = x[c].astype(object).where(x[c].notna(), np.nan)
        x[c] = x[c].replace({"-": np.nan, "": np.nan})
    return x


def separar_datos(datos):
    if datos[TARGET].isna().any() or not datos[TARGET].isin([True, False, 0, 1]).all():
        raise ValueError("Target invalido")
    if datos[CLAVE].isna().any().any() or datos.duplicated(CLAVE).any():
        raise ValueError("Clave de evento invalida")
    return seleccionar_predictores(datos), datos[TARGET].astype('int8').copy(), datos[CLAVE].copy()
