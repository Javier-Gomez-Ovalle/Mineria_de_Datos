"""
diagnostico.py
==============
Métricas descriptivas del dataset final + impresión del checklist
obligatorio. Se mantiene como FUNCIONES, mismo criterio que
validacion.py y features.py.
"""
import pandas as pd


def generar_metricas_diagnosticas(df, usuarios_seleccionados, diagnostico_global,
                                   diagnostico_subconjunto, diagnostico_resolucion,
                                   diagnostico_centroides, n_login_desconocidos,
                                   config):
    """Recolecta TODAS las métricas informativas para el checklist final."""
    metricas = {
        "n_usuarios_seleccionados": len(usuarios_seleccionados),
        "diagnostico_global": diagnostico_global,
        "diagnostico_subconjunto": diagnostico_subconjunto,
        "diagnostico_resolucion": diagnostico_resolucion,
        "diagnostico_centroides": diagnostico_centroides,
        "n_login_desconocidos": n_login_desconocidos,
    }

    usuarios_en_df = set(df["User ID"].unique())
    metricas["pct_integridad_referencial"] = (
        100 * len(usuarios_en_df & set(usuarios_seleccionados)) / len(usuarios_seleccionados)
        if usuarios_seleccionados else 0.0
    )

    metricas["orden_temporal_correcto"] = bool(
        df.groupby("User ID")["Login Timestamp"]
        .apply(lambda s: s.is_monotonic_increasing).all()
    )
    metricas["timestamp_es_datetime"] = pd.api.types.is_datetime64_any_dtype(
        df["Login Timestamp"]
    )
    metricas["rango_fechas_login"] = (
        str(df["Login Timestamp"].min()), str(df["Login Timestamp"].max())
    )

    conteo_gt = df["Is Account Takeover"].value_counts(dropna=False)
    metricas["ground_truth_counts"] = conteo_gt.to_dict()
    metricas["ground_truth_pct"] = (100 * conteo_gt / conteo_gt.sum()).round(2).to_dict()

    metricas["impossible_travel_total"] = int(df["impossible_travel"].sum())
    metricas["fuera_de_turno_total"] = int(df["is_outside_shift"].fillna(0).sum())
    metricas["inactive_success_total"] = int(df["inactive_account_success"].sum())

    metricas["has_previous_login_0"] = int((df["has_previous_login"] == 0).sum())
    metricas["has_previous_login_1"] = int((df["has_previous_login"] == 1).sum())

    metricas["country_mismatch_1"] = int(df["country_mismatch"].fillna(0).sum())
    metricas["country_mismatch_nan"] = int(df["country_mismatch"].isna().sum())

    paises_residencia_unicos = set(df["Pais_Residencia"].dropna().unique())
    metricas["paises_residencia_no_reconocidos"] = sorted(
        paises_residencia_unicos - config.ISO2_RECONOCIDOS
    )

    columnas_clave = [
        "ip_country_code", "ip_country_name", "distance_previous_km",
        "required_speed_kmh", "previous_login_timestamp",
        "login_exitoso_normalizado",
    ]
    metricas["nulos_columnas_clave"] = {
        c: int(df[c].isna().sum()) for c in columnas_clave if c in df.columns
    }

    print("  Resumen de métricas de calidad calculadas:")
    print(f"    Integridad referencial: {metricas['pct_integridad_referencial']:.2f}%")
    print(f"    Orden temporal correcto: {metricas['orden_temporal_correcto']}")
    print(f"    Rango de fechas de login: {metricas['rango_fechas_login']}")
    print(f"    Distribución Ground Truth: {metricas['ground_truth_counts']}")
    print(f"    has_previous_login=0 / =1: {metricas['has_previous_login_0']:,} / "
          f"{metricas['has_previous_login_1']:,}")
    print(f"    country_mismatch=1 / NaN: {metricas['country_mismatch_1']:,} / "
          f"{metricas['country_mismatch_nan']:,}")
    print(f"    Nulos en columnas clave: {metricas['nulos_columnas_clave']}\n")

    return metricas


def imprimir_checklist_final(df_final, metricas, config):
    """Checklist final con TODAS las métricas calculadas en tiempo real."""
    diag_sub = metricas["diagnostico_subconjunto"]
    diag_global = metricas["diagnostico_global"]
    diag_res = metricas["diagnostico_resolucion"]
    diag_cent = metricas["diagnostico_centroides"]
    gt_counts = metricas["ground_truth_counts"]
    gt_pct = metricas["ground_truth_pct"]

    print("=" * 60)
    print("CHECKLIST FINAL — FASE 03 CRISP-DM (Arquitectura modular, Etapa 1)")
    print("=" * 60)
    print()
    print(f"[OK] Usuarios seleccionados: {metricas['n_usuarios_seleccionados']}")
    print(f"[OK] Historial mínimo por usuario: >= {config.MIN_EVENTOS_USUARIO} eventos")
    print(f"[OK] Integridad referencial User ID: "
          f"{metricas['pct_integridad_referencial']:.2f}%")
    print()
    print(f"[INFO] Total registros procesados para los usuarios seleccionados: "
          f"{len(df_final):,}")
    print()
    print(f"[INFO] Rango de fechas de 'Login Timestamp': "
          f"{metricas['rango_fechas_login'][0]} -> {metricas['rango_fechas_login'][1]}")
    print()
    print(f"[INFO] --- Diagnóstico IP: SUBCONJUNTO de usuarios seleccionados ---")
    print(f"[INFO] IPv4: {diag_sub['total_ipv4']:,} ({diag_sub['pct_ipv4']:.2f}%)")
    print(f"[INFO] IPv6: {diag_sub['total_ipv6']:,} ({diag_sub['pct_ipv6']:.2f}%)")
    print(f"[INFO] IP inválidas/nulas: {diag_sub['total_invalidas']:,} "
          f"({diag_sub['pct_invalidas']:.2f}%)")
    print()
    print(f"[INFO] --- Diagnóstico IP: RBA GLOBAL, solo referencia ---")
    print(f"[INFO] IPv4: {diag_global['total_ipv4']:,} ({diag_global['pct_ipv4']:.2f}%)")
    print(f"[INFO] IPv6: {diag_global['total_ipv6']:,} ({diag_global['pct_ipv6']:.2f}%)")
    print(f"[INFO] IP inválidas/nulas: {diag_global['total_invalidas']:,} "
          f"({diag_global['pct_invalidas']:.2f}%)")
    print()
    print(f"[INFO] IPs IPv4 resueltas mediante IPinfo: "
          f"{diag_res['ipv4_unicas_resueltas']:,}")
    print(f"[INFO] IPs IPv4 no resueltas: {diag_res['ipv4_unicas_no_resueltas']:,}")
    print(f"[INFO] Porcentaje de resolución IPv4: "
          f"{diag_res['pct_resolucion_ipv4']:.2f}%")
    print()
    print(f"[INFO] Cobertura centroides ISO2 (países distintos): "
          f"{diag_cent['pct_cobertura_paises_distintos']:.2f}% "
          f"({diag_cent['paises_con_centroide']}/{diag_cent['paises_relevantes_total']})")
    print(f"[INFO] Cobertura centroides (registros con historial previo): "
          f"{diag_cent['pct_cobertura_registros_con_historial']:.2f}%")
    print()
    print(f"[INFO] has_previous_login = 0 (primer evento): "
          f"{metricas['has_previous_login_0']:,}")
    print(f"[INFO] has_previous_login = 1 (con historial): "
          f"{metricas['has_previous_login_1']:,}")
    print()
    print(f"[INFO] impossible_travel = 1: {metricas['impossible_travel_total']:,}")
    print(f"[INFO] registros fuera de turno: {metricas['fuera_de_turno_total']:,}")
    print(f"[INFO] cuentas inactivas con login exitoso: "
          f"{metricas['inactive_success_total']:,}")
    print(f"[INFO] valores de 'Login Successful' no interpretables: "
          f"{metricas['n_login_desconocidos']:,}")
    print()
    print(f"[INFO] country_mismatch = 1: {metricas['country_mismatch_1']:,}")
    print(f"[INFO] country_mismatch = NaN (IP no resuelta): "
          f"{metricas['country_mismatch_nan']:,}")
    if metricas["paises_residencia_no_reconocidos"]:
        print(f"[ATENCIÓN] Códigos ISO2 en Pais_Residencia fuera del set "
              f"reconocido: {metricas['paises_residencia_no_reconocidos']}")
    else:
        print("[OK] Todos los códigos ISO2 de Pais_Residencia están dentro "
              "del set reconocido.")
    print()
    print(f"[INFO] Nulos en columnas clave: {metricas['nulos_columnas_clave']}")
    print()
    print(f"[INFO] Orden temporal correcto: {metricas['orden_temporal_correcto']}")
    print(f"[INFO] Timestamp es datetime: {metricas['timestamp_es_datetime']}")
    print()
    print("[INFO] Distribución Ground Truth:")
    for valor, conteo in gt_counts.items():
        print(f"       Is Account Takeover = {valor}: {conteo:,} "
              f"({gt_pct.get(valor, 0):.2f}%)")
    print()
    print("[INFO] Dataset final:")
    print(f"       Filas: {len(df_final):,}")
    print(f"       Columnas: {df_final.shape[1]}")
    print()
    print("[OK] No se ejecutó entrenamiento de Machine Learning.")
    print("[OK] No se ejecutó SMOTE ni balanceo de clases.")
    print("[OK] No se realizó train_test_split.")
    print("[OK] No se realizaron predicciones.")
    print("[OK] 'Is Account Takeover' fue retirado físicamente del DataFrame "
          "antes de construir features y reincorporado solo para validación/"
          "exportación (barrera estructural anti-leakage).")
    print("[OK] Fase 03 (arquitectura modular, Etapa 1) finalizada.")
    print()
    print("Archivo generado:")
    print(config.OUT_DATASET_FINAL)
    print()
    print("=" * 60)
