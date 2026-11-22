"""
validacion.py
=============
Validaciones bloqueantes que DETIENEN la ejecución si fallan.

Se mantiene como FUNCIÓN, no como clase: no tiene estado propio más
allá de 'config' y un único método público — envolverla en una clase
habría sido cumplimiento cosmético, no una necesidad arquitectónica
(mismo criterio aplicado en features.py tras la revisión crítica).
"""
import pandas as pd


def validar_calidad_bloqueante(df, usuarios_seleccionados, config):
    """Validaciones CRÍTICAS que DETIENEN la ejecución si fallan."""
    print("=" * 60)
    print("[8/8] Ejecutando validaciones BLOQUEANTES...")
    print("=" * 60)

    errores = []

    if len(set(usuarios_seleccionados)) != config.N_USUARIOS:
        errores.append(
            f"Se esperaban {config.N_USUARIOS} usuarios únicos, "
            f"hay {len(set(usuarios_seleccionados))}."
        )

    usuarios_en_df = set(df["User ID"].unique())
    faltan_en_df = set(usuarios_seleccionados) - usuarios_en_df
    if faltan_en_df:
        errores.append(
            f"{len(faltan_en_df)} usuarios seleccionados no aparecen en el "
            "dataset integrado final (integridad referencial < 100%)."
        )

    conteo_final = df["User ID"].value_counts()
    insuficientes = conteo_final[conteo_final < config.MIN_EVENTOS_USUARIO]
    if len(insuficientes) > 0:
        errores.append(
            f"{len(insuficientes)} usuarios tienen menos de "
            f"{config.MIN_EVENTOS_USUARIO} eventos en el dataset final."
        )

    if not pd.api.types.is_datetime64_any_dtype(df["Login Timestamp"]):
        errores.append("'Login Timestamp' no quedó convertido a datetime64.")

    orden_correcto = df.groupby("User ID")["Login Timestamp"].apply(
        lambda s: s.is_monotonic_increasing
    ).all()
    if not orden_correcto:
        errores.append(
            "El dataset no está correctamente ordenado por "
            "['User ID', 'Login Timestamp'] ascendente en todos los grupos."
        )

    columnas_obligatorias_salida = [
        "User ID", "Login Timestamp", "Is Account Takeover",
        "failed_attempts_15min", "failed_attempts_1h",
        "has_previous_login",
        "impossible_travel", "is_outside_shift",
        "country_mismatch", "inactive_account_success",
    ]
    faltantes_salida = [c for c in columnas_obligatorias_salida if c not in df.columns]
    if faltantes_salida:
        errores.append(f"Faltan columnas obligatorias de salida: {faltantes_salida}")

    if "Is Account Takeover" not in df.columns:
        errores.append("'Is Account Takeover' (Ground Truth) no está presente.")
    elif df["Is Account Takeover"].isna().all():
        errores.append("'Is Account Takeover' está completamente vacío.")

    fecha_min = df["Login Timestamp"].min()
    fecha_max = df["Login Timestamp"].max()
    if pd.notna(fecha_min) and fecha_min.year < 1990:
        errores.append(
            f"'Login Timestamp' produjo fechas implausibles (mínimo: "
            f"{fecha_min}). Esto sugiere que la unidad del timestamp se "
            "infirió incorrectamente."
        )

    if "has_previous_login" in df.columns:
        primer_evento = df["has_previous_login"] == 0
        fuga_distancia = primer_evento & df["distance_previous_km"].notna()
        fuga_velocidad = primer_evento & df["required_speed_kmh"].notna()
        if fuga_distancia.any() or fuga_velocidad.any():
            errores.append(
                "Se encontraron valores NO nulos de 'distance_previous_km' o "
                "'required_speed_kmh' en registros con has_previous_login=0 "
                "(primer evento del usuario). Esto viola la regla de missing "
                "semántico: la ausencia de historial debe producir NaN, "
                "nunca un valor calculado."
            )

    if "country_mismatch" in df.columns and "ip_country_code" in df.columns:
        ip_no_resuelta = df["ip_country_code"].isna()
        mismatch_deberia_ser_nan_pero_no_lo_es = (
            ip_no_resuelta & df["country_mismatch"].notna()
        )
        if mismatch_deberia_ser_nan_pero_no_lo_es.any():
            errores.append(
                "'country_mismatch' tiene valores no nulos en registros donde "
                "'ip_country_code' es NaN (IP no resuelta). Sin país de IP "
                "conocido, el mismatch debe ser NaN."
            )

    if errores:
        mensaje = (
            "VALIDACIÓN BLOQUEANTE FALLIDA — el dataset final NO se exportará.\n"
            "Errores encontrados:\n" + "\n".join(f"  - {e}" for e in errores)
        )
        raise RuntimeError(mensaje)

    print("  [OK] Todas las validaciones bloqueantes pasaron correctamente.\n")
    return True
