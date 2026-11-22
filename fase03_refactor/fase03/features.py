"""
features.py
===========
Ingeniería de características. Se mantienen como FUNCIONES DE MÓDULO,
no como clases — decisión explícita de la revisión crítica de diseño:
cada una tiene un solo método público, sin estado propio más allá de
'config', y el orden entre ellas es fijo (crear_features_temporales
debe correr antes que crear_feature_impossible_travel y
crear_feature_turnos, porque ambas dependen de columnas que la primera
crea). Al no ser intercambiables ni tener estado propio, envolverlas en
clases habría sido cumplimiento cosmético de "necesitamos clases", no
una necesidad arquitectónica real.

INDEPENDENCIA DEL TARGET E INTEGRIDAD DEL EVENTO
---------------------------------------------
Ninguna función de este módulo lee el target para calcular características.
La etiqueta viaja como columna del evento, también al ordenar y reiniciar
índices. pipeline.py verifica la asociación por clave antes y después.
Las pruebas de corrección verifican además que variar las etiquetas no
altera las características. No se usa una serie externa alineada por índice.
"""
import numpy as np
import pandas as pd

from .config import CENTROIDES_GEOGRAFICOS, VENTANAS_TURNO
from .timestamp_utils import convertir_login_timestamp

VALORES_LOGIN_EXITOSO = {"true", "1", "1.0", "yes", "y", "t", "success", "successful"}
VALORES_LOGIN_FALLIDO = {"false", "0", "0.0", "no", "n", "f", "fail", "failed", "failure"}


def normalizar_login_successful(serie):
    """Conversión DEFENSIVA de 'Login Successful': reconoce booleanos
    nativos, texto ('True'/'False'/'yes'/'no', etc.) y 0/1. Un valor
    ambiguo se marca NaN — NUNCA se asume como éxito o fracaso."""
    def _clasificar(valor):
        if pd.isna(valor):
            return np.nan
        if isinstance(valor, (bool, np.bool_)):
            return bool(valor)
        if isinstance(valor, (int, float, np.integer, np.floating)):
            if valor == 1:
                return True
            if valor == 0:
                return False
            return np.nan
        texto = str(valor).strip().lower()
        if texto in VALORES_LOGIN_EXITOSO:
            return True
        if texto in VALORES_LOGIN_FALLIDO:
            return False
        return np.nan

    valores_originales_unicos = serie.value_counts(dropna=False)
    print("  Valores originales detectados en 'Login Successful':")
    print(valores_originales_unicos.to_string())

    normalizado = serie.apply(_clasificar)
    n_desconocidos = int(normalizado.isna().sum() - serie.isna().sum())

    if n_desconocidos > 0:
        print(f"  [ATENCIÓN] {n_desconocidos:,} valores de 'Login Successful' "
              "no pudieron interpretarse de forma segura y se marcaron como "
              "NaN (política explícita: NO se asumen como éxito ni como "
              "fracaso).")
    else:
        print("  [OK] Todos los valores de 'Login Successful' se "
              "interpretaron correctamente.")

    return normalizado, n_desconocidos


def calcular_rolling_retrospectivo(df, columna_valor, ventana):
    """Ventana móvil retrospectiva (closed='left') POR USUARIO, con
    alineación EXPLÍCITA de índice.

    Se itera manualmente sobre los grupos y se concatena con
    pd.concat(), en vez de usar groupby().apply(): en pandas >= 3.0,
    groupby().apply() puede devolver un DataFrame de una sola fila
    (en vez de concatenar las Series por grupo) cuando el DataFrame
    contiene EXACTAMENTE UN grupo. Con los usuarios reales del
    pipeline esto no ocurre, pero la función no debería depender
    implícitamente de "haber más de un usuario" para ser correcta."""
    partes = []
    for _, grupo in df.groupby("User ID", sort=False):
        serie_temporal = grupo.set_index("Login Timestamp")[columna_valor]
        resultado = serie_temporal.rolling(ventana, closed="left").sum()
        resultado.index = grupo.index
        partes.append(resultado)

    resultados = pd.concat(partes) if partes else pd.Series(dtype=float)
    return resultados.reindex(df.index)


def crear_features_temporales(df, config):
    """Construye failed_attempts_15min/1h, previous_login_timestamp,
    previous_ip, previous_country, time_since_previous_login_hours y
    has_previous_login."""
    print("=" * 60)
    print("[7/8] Creando features de ingeniería (fuerza bruta, temporales)...")
    print("=" * 60)

    print("  Convirtiendo 'Login Timestamp' (entero Unix de 64 bits)...")
    df["Login Timestamp"] = convertir_login_timestamp(
        df["Login Timestamp"], config.VENTANA_FECHAS_RBA_CONOCIDA
    )
    df = df.sort_values(["User ID", "Login Timestamp"]).reset_index(drop=True)

    print("\n  Normalizando 'Login Successful'...")
    login_normalizado, n_desconocidos = normalizar_login_successful(df["Login Successful"])
    df["login_exitoso_normalizado"] = login_normalizado

    # Máscara de FALLOS EXPLÍCITOS únicamente. Un valor desconocido
    # (NaN) no cuenta como fallo ni como éxito dentro de la ventana de
    # fuerza bruta.
    mascara_fallo_explicito = df["login_exitoso_normalizado"] == False  # noqa: E712
    df["is_failed"] = mascara_fallo_explicito.astype(int)

    df["failed_attempts_15min"] = calcular_rolling_retrospectivo(
        df, "is_failed", config.VENTANA_CORTA
    ).fillna(0)
    df["failed_attempts_1h"] = calcular_rolling_retrospectivo(
        df, "is_failed", config.VENTANA_LARGA
    ).fillna(0)

    grp = df.groupby("User ID")
    df["previous_login_timestamp"] = grp["Login Timestamp"].shift(1)
    df["previous_ip"] = grp["IP Address"].shift(1)
    df["previous_country"] = grp["Country"].shift(1)
    del grp

    df["has_previous_login"] = df["previous_login_timestamp"].notna().astype(int)

    delta = df["Login Timestamp"] - df["previous_login_timestamp"]
    df["time_since_previous_login_hours"] = delta.dt.total_seconds() / 3600.0
    del delta

    print(f"\n  failed_attempts_15min -> media: "
          f"{df['failed_attempts_15min'].mean():.3f}")
    print(f"  failed_attempts_1h    -> media: "
          f"{df['failed_attempts_1h'].mean():.3f}")
    print(f"  has_previous_login = 0 (primer evento por usuario): "
          f"{int((df['has_previous_login'] == 0).sum()):,}")
    print(f"  has_previous_login = 1 (con historial previo): "
          f"{int((df['has_previous_login'] == 1).sum()):,}")
    print(f"  Valores de Login Successful no interpretables: {n_desconocidos:,}\n")

    return df, n_desconocidos


def _distancia_haversine(lat1, lon1, lat2, lon2):
    """Distancia aproximada (km) entre dos puntos, fórmula de Haversine."""
    if any(pd.isna(v) for v in [lat1, lon1, lat2, lon2]):
        return np.nan
    R = 6371.0
    lat1_r, lon1_r, lat2_r, lon2_r = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def crear_feature_impossible_travel(df, config):
    """Impossible Travel sobre 'Country' ORIGINAL del RBA (actual y
    anterior) -> centroide representativo ISO2. Refuerza NaN explícito
    en distance_previous_km/required_speed_kmh cuando
    has_previous_login == 0."""
    print("  Calculando Impossible Travel (Haversine + centroides ISO2 sobre "
          "'Country' original del RBA)...")

    def _lat(pais_iso2):
        return CENTROIDES_GEOGRAFICOS.get(pais_iso2, (np.nan, np.nan))[0]

    def _lon(pais_iso2):
        return CENTROIDES_GEOGRAFICOS.get(pais_iso2, (np.nan, np.nan))[1]

    df["_lat_actual"] = df["Country"].apply(_lat)
    df["_lon_actual"] = df["Country"].apply(_lon)
    df["_lat_previa"] = df["previous_country"].apply(_lat)
    df["_lon_previa"] = df["previous_country"].apply(_lon)

    df["distance_previous_km"] = df.apply(
        lambda r: _distancia_haversine(
            r["_lat_previa"], r["_lon_previa"], r["_lat_actual"], r["_lon_actual"]
        ),
        axis=1,
    )

    tiempo_valido = (
        df["time_since_previous_login_hours"].notna()
        & (df["time_since_previous_login_hours"] > 0)
    )
    distancia_valida = df["distance_previous_km"].notna()
    mascara_calculable = tiempo_valido & distancia_valida

    df["required_speed_kmh"] = np.nan
    df.loc[mascara_calculable, "required_speed_kmh"] = (
        df.loc[mascara_calculable, "distance_previous_km"]
        / df.loc[mascara_calculable, "time_since_previous_login_hours"]
    )

    sin_historial = df["has_previous_login"] == 0
    df.loc[sin_historial, "distance_previous_km"] = np.nan
    df.loc[sin_historial, "required_speed_kmh"] = np.nan

    df["impossible_travel"] = 0
    condicion_anomalia = (
        mascara_calculable
        & (~sin_historial)
        & (df["required_speed_kmh"] > config.UMBRAL_VELOCIDAD_KMH)
        & (df["time_since_previous_login_hours"] < config.VENTANA_MAX_HORAS)
    )
    df.loc[condicion_anomalia, "impossible_travel"] = 1

    paises_relevantes = pd.concat(
        [df["Country"], df["previous_country"]]
    ).dropna().unique()
    paises_con_centroide = [p for p in paises_relevantes if p in CENTROIDES_GEOGRAFICOS]
    pct_cobertura_paises = (
        100 * len(paises_con_centroide) / len(paises_relevantes)
        if len(paises_relevantes) else 0.0
    )

    con_historial = df["has_previous_login"] == 1
    if con_historial.sum() > 0:
        ambos_con_centroide = (
            df.loc[con_historial, "Country"].isin(CENTROIDES_GEOGRAFICOS)
            & df.loc[con_historial, "previous_country"].isin(CENTROIDES_GEOGRAFICOS)
        )
        pct_cobertura_registros = 100 * ambos_con_centroide.sum() / con_historial.sum()
    else:
        pct_cobertura_registros = 0.0

    diagnostico_centroides = {
        "paises_relevantes_total": len(paises_relevantes),
        "paises_con_centroide": len(paises_con_centroide),
        "pct_cobertura_paises_distintos": pct_cobertura_paises,
        "pct_cobertura_registros_con_historial": pct_cobertura_registros,
    }

    df = df.drop(columns=["_lat_actual", "_lon_actual", "_lat_previa", "_lon_previa"])

    print(f"    Cobertura de centroides (países distintos, ISO2): "
          f"{len(paises_con_centroide)}/{len(paises_relevantes)} "
          f"({pct_cobertura_paises:.2f}%)")
    print(f"    Cobertura de centroides (registros con historial previo): "
          f"{pct_cobertura_registros:.2f}%")
    print(f"    impossible_travel = 1 -> {int(df['impossible_travel'].sum()):,} registros")
    print(f"    (heurística: velocidad > {config.UMBRAL_VELOCIDAD_KMH} km/h "
          f"Y ventana < {config.VENTANA_MAX_HORAS}h)\n")

    return df, diagnostico_centroides


def crear_feature_turnos(df):
    """is_outside_shift, respetando turnos que cruzan medianoche."""
    print("  Calculando is_outside_shift (respetando turnos nocturnos)...")

    def _fuera_de_turno(hora, turno):
        if turno not in VENTANAS_TURNO or pd.isna(hora):
            return np.nan
        inicio, fin = VENTANAS_TURNO[turno]
        if inicio < fin:
            dentro = inicio <= hora < fin
        else:
            dentro = hora >= inicio or hora < fin
        return 0 if dentro else 1

    df["_hora_login"] = df["Login Timestamp"].dt.hour
    df["is_outside_shift"] = df.apply(
        lambda r: _fuera_de_turno(r["_hora_login"], r.get("Turno_Asignado", np.nan)),
        axis=1,
    )
    df = df.drop(columns=["_hora_login"])

    print(f"    Registros fuera de turno: "
          f"{int(df['is_outside_shift'].fillna(0).sum()):,}\n")
    return df


def crear_features_negocio(df):
    """country_mismatch (ISO2 de Pais_Residencia vs ISO2 nativo de
    ip_country_code, ambos normalizados a mayúsculas) e
    inactive_account_success."""
    print("  Calculando country_mismatch e inactive_account_success...")

    if "ip_country_code" not in df.columns:
        raise RuntimeError(
            "ERROR: 'ip_country_code' no está disponible; country_mismatch "
            "requiere el código ISO2 resuelto por IPinfo."
        )

    pais_residencia_iso2 = df["Pais_Residencia"].astype("string").str.upper()
    ip_country_code_iso2 = df["ip_country_code"].astype("string").str.upper()

    ambos_conocidos = pais_residencia_iso2.notna() & ip_country_code_iso2.notna()
    df["country_mismatch"] = np.nan
    df.loc[ambos_conocidos, "country_mismatch"] = (
        pais_residencia_iso2[ambos_conocidos] != ip_country_code_iso2[ambos_conocidos]
    ).astype(int)

    df["inactive_account_success"] = (
        (df["Estado_Cuenta"] == "Inactivo")
        & (df["login_exitoso_normalizado"] == True)  # noqa: E712
    ).astype(int)

    n_no_resuelto = int((~ambos_conocidos).sum())
    print(f"    country_mismatch = 1 -> "
          f"{int(df['country_mismatch'].fillna(0).sum()):,} registros")
    print(f"    country_mismatch = NaN (IP no resuelta u otro dato faltante): "
          f"{n_no_resuelto:,} registros")
    print(f"    inactive_account_success = 1 -> "
          f"{int(df['inactive_account_success'].sum()):,} registros\n")

    return df
