"""
exportacion.py
==============
Selección de columnas finales + escritura de dataset_final_modelo.csv.
Se mantiene como FUNCIÓN, mismo criterio que validacion.py/features.py.
"""


def exportar_dataset_final(df, config):
    """Exporta dataset_final_modelo.csv. 'Is Account Takeover' queda
    como ÚLTIMA columna, sin modificaciones."""
    columnas_finales = [
        "User ID", "IP Address", "Login Timestamp", "Login Successful",
        "login_exitoso_normalizado",
        "Device Type", "Is Attack IP",
        "Country", "Region", "City", "ASN",
        "ip_country_code", "ip_country_name", "ip_asn", "ip_as_name", "ip_as_domain",
        "Nombre_Completo", "Rol_Hospitalario", "Pais_Residencia",
        "Ciudad_Base", "Turno_Asignado", "Estado_Cuenta", "Fecha_Ingreso",
        "failed_attempts_15min", "failed_attempts_1h",
        "has_previous_login",
        "previous_login_timestamp", "time_since_previous_login_hours",
        "distance_previous_km", "required_speed_kmh", "impossible_travel",
        "is_outside_shift", "country_mismatch", "inactive_account_success",
        "Is Account Takeover",
    ]
    columnas_presentes = [c for c in columnas_finales if c in df.columns]
    df_final = df[columnas_presentes]

    df_final.to_csv(config.OUT_DATASET_FINAL, index=False)
    return df_final
