"""
comparar_pipelines_colab.py
===========================
Herramienta de VERIFICACIÓN (no forma parte de la arquitectura de
fase03/ — es un script de diagnóstico independiente, pensado para
correr una sola vez en Colab con los archivos reales).

QUÉ HACE
--------
Toma tu rba_2000_users.csv real, genera empleados + resuelve IP +
construye features TANTO con el pipeline monolítico
(tests/legacy/fase03_pipeline_v4.py) COMO con la arquitectura modular
(fase03/), y compara ambos resultados en 7 dimensiones distintas —
no solo un booleano de equals():

  1. Forma (filas, columnas)
  2. Nombres y ORDEN de columnas
  3. Dtypes por columna
  4. Igualdad exacta de valores (pd.testing.assert_frame_equal)
  5. Conteo de nulos por columna
  6. Distribución de cada feature (describe() para numéricas,
     value_counts() para binarias/categóricas)
  7. Distribución del target (Is Account Takeover)

Además, compara ambos resultados contra tu empleados.csv YA EXISTENTE
(el de tu corrida real anterior), para detectar si algo cambió incluso
antes de comparar monolito vs modular (deriva de entorno/versión de
librerías entre corridas).

CÓMO SE EJECUTA (ver instrucciones completas en el mensaje de Claude)
----------------------------------------------------------------------
python comparar_pipelines_colab.py \
    --rba-2000 /ruta/a/rba_2000_users.csv \
    --ipinfo /ruta/a/country_asn.csv \
    --empleados-existente /ruta/a/empleados.csv \
    --legacy-script /ruta/a/tests/legacy/fase03_pipeline_v4.py \
    --fase03-path /ruta/a/fase03_refactor

Al finalizar imprime un REPORTE FINAL con veredicto explícito
(EQUIVALENTE / NO EQUIVALENTE) y el detalle exacto de cualquier
diferencia encontrada. Copia esa salida completa de vuelta a Claude.
"""
import argparse
import importlib.util
import sys

import numpy as np
import pandas as pd


def cargar_modulo_legacy(ruta_script):
    spec = importlib.util.spec_from_file_location("fase03_pipeline_v4_legacy", ruta_script)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def separador(titulo):
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)


def comparar_forma(df_legacy, df_modular, reporte):
    separador("1. FORMA (filas, columnas)")
    ok = df_legacy.shape == df_modular.shape
    print(f"  Legacy:  {df_legacy.shape}")
    print(f"  Modular: {df_modular.shape}")
    print(f"  {'[OK]' if ok else '[DIFERENTE]'} misma forma: {ok}")
    reporte["forma_identica"] = ok
    return ok


def comparar_columnas(df_legacy, df_modular, reporte):
    separador("2. NOMBRES Y ORDEN DE COLUMNAS")
    cols_legacy = list(df_legacy.columns)
    cols_modular = list(df_modular.columns)
    ok = cols_legacy == cols_modular
    if ok:
        print(f"  [OK] {len(cols_legacy)} columnas, mismo nombre y mismo orden.")
    else:
        solo_legacy = [c for c in cols_legacy if c not in cols_modular]
        solo_modular = [c for c in cols_modular if c not in cols_legacy]
        print(f"  [DIFERENTE] Columnas solo en legacy: {solo_legacy}")
        print(f"  [DIFERENTE] Columnas solo en modular: {solo_modular}")
        if set(cols_legacy) == set(cols_modular) and cols_legacy != cols_modular:
            print("  [ATENCIÓN] Mismas columnas mismo set, pero DISTINTO ORDEN.")
    reporte["columnas_identicas"] = ok
    return ok


def comparar_dtypes(df_legacy, df_modular, reporte):
    separador("3. DTYPES POR COLUMNA")
    columnas_comunes = [c for c in df_legacy.columns if c in df_modular.columns]
    diferencias = []
    for col in columnas_comunes:
        dt_l, dt_m = df_legacy[col].dtype, df_modular[col].dtype
        if dt_l != dt_m:
            diferencias.append((col, dt_l, dt_m))
    if not diferencias:
        print(f"  [OK] Los {len(columnas_comunes)} dtypes coinciden exactamente.")
    else:
        print(f"  [DIFERENTE] {len(diferencias)} columnas con dtype distinto:")
        for col, dt_l, dt_m in diferencias:
            print(f"    - {col}: legacy={dt_l}  modular={dt_m}")
    reporte["dtypes_identicos"] = not diferencias
    reporte["dtypes_diferencias"] = diferencias
    return not diferencias


def comparar_valores_exactos(df_legacy, df_modular, reporte):
    separador("4. IGUALDAD EXACTA DE VALORES (pd.testing.assert_frame_equal)")
    try:
        pd.testing.assert_frame_equal(
            df_legacy.reset_index(drop=True),
            df_modular.reset_index(drop=True),
            check_exact=True,
            check_dtype=True,
        )
        print("  [OK] assert_frame_equal PASÓ — valores idénticos fila por fila, "
              "columna por columna, con los mismos dtypes.")
        reporte["valores_identicos"] = True
    except AssertionError as e:
        print("  [DIFERENTE] assert_frame_equal FALLÓ. Detalle:")
        print(str(e))
        reporte["valores_identicos"] = False
        reporte["detalle_assert_frame_equal"] = str(e)
    return reporte["valores_identicos"]


def comparar_nulos(df_legacy, df_modular, reporte):
    separador("5. CONTEO DE NULOS POR COLUMNA")
    columnas_comunes = [c for c in df_legacy.columns if c in df_modular.columns]
    nulos_legacy = df_legacy[columnas_comunes].isna().sum()
    nulos_modular = df_modular[columnas_comunes].isna().sum()
    tabla = pd.DataFrame({"legacy": nulos_legacy, "modular": nulos_modular})
    tabla["diferencia"] = tabla["legacy"] - tabla["modular"]
    diferencias = tabla[tabla["diferencia"] != 0]
    if diferencias.empty:
        print("  [OK] Conteo de nulos idéntico en todas las columnas.")
    else:
        print("  [DIFERENTE] Columnas con distinto conteo de nulos:")
        print(diferencias.to_string())
    reporte["nulos_identicos"] = diferencias.empty
    return diferencias.empty


def comparar_distribuciones(df_legacy, df_modular, reporte):
    separador("6. DISTRIBUCIÓN DE FEATURES")
    columnas_features = [
        "failed_attempts_15min", "failed_attempts_1h", "has_previous_login",
        "distance_previous_km", "required_speed_kmh", "impossible_travel",
        "is_outside_shift", "country_mismatch", "inactive_account_success",
    ]
    columnas_features = [c for c in columnas_features if c in df_legacy.columns and c in df_modular.columns]
    todas_iguales = True
    for col in columnas_features:
        desc_legacy = df_legacy[col].describe()
        desc_modular = df_modular[col].describe()
        diff = (desc_legacy - desc_modular).abs()
        max_diff = diff.max() if not diff.empty else 0
        iguales = pd.isna(max_diff) or max_diff < 1e-9
        estado = "[OK]" if iguales else "[DIFERENTE]"
        print(f"  {estado} {col}: max diff en describe() = {max_diff}")
        if not iguales:
            todas_iguales = False
            print(f"      legacy:  {desc_legacy.to_dict()}")
            print(f"      modular: {desc_modular.to_dict()}")
    reporte["distribuciones_identicas"] = todas_iguales
    return todas_iguales


def comparar_target(df_legacy, df_modular, reporte):
    separador("7. DISTRIBUCIÓN DEL TARGET (Is Account Takeover)")
    vc_legacy = df_legacy["Is Account Takeover"].value_counts(dropna=False).sort_index()
    vc_modular = df_modular["Is Account Takeover"].value_counts(dropna=False).sort_index()
    ok = vc_legacy.equals(vc_modular)
    print(f"  Legacy:\n{vc_legacy.to_string()}")
    print(f"  Modular:\n{vc_modular.to_string()}")
    print(f"  {'[OK]' if ok else '[DIFERENTE]'} distribución del target idéntica: {ok}")
    reporte["target_identico"] = ok
    return ok


def comparar_contra_empleados_existente(ruta_empleados_modular_csv, ruta_empleados_existente, reporte):
    """IMPORTANTE: compara CSV contra CSV (ambos releídos desde disco),
    nunca un DataFrame en memoria contra uno releído. Comparar en-memoria
    vs. releído genera falsos positivos de diferencia de dtype en
    columnas de fecha (Fecha_Ingreso pasa de datetime.date en memoria a
    string tras el round-trip por CSV) — eso NO es una diferencia real
    del refactor, es un artefacto de serialización."""
    separador("EXTRA — Comparación contra tu empleados.csv YA EXISTENTE (corrida real anterior)")
    try:
        df_existente = pd.read_csv(ruta_empleados_existente)
    except FileNotFoundError:
        print(f"  [OMITIDO] No se encontró {ruta_empleados_existente} — se omite esta comparación extra.")
        reporte["coincide_con_empleados_historico"] = None
        return None

    df_modular_releido = pd.read_csv(ruta_empleados_modular_csv)

    try:
        pd.testing.assert_frame_equal(
            df_existente.reset_index(drop=True),
            df_modular_releido.reset_index(drop=True),
            check_exact=True,
        )
        print("  [OK] El empleados.csv regenerado HOY (modular) es IDÉNTICO al que ya "
              "tenías guardado de tu corrida real anterior. No hay deriva de entorno "
              "ni de versión de librerías entre corridas.")
        reporte["coincide_con_empleados_historico"] = True
    except AssertionError as e:
        print("  [ATENCIÓN] El empleados.csv regenerado HOY difiere del que ya tenías "
              "guardado. Esto NO necesariamente es un bug del refactor — puede indicar "
              "que Faker/numpy cambiaron de versión entre tu corrida original y hoy. "
              "Detalle:")
        print(str(e))
        reporte["coincide_con_empleados_historico"] = False
    return reporte["coincide_con_empleados_historico"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rba-2000", required=True, help="Ruta a rba_2000_users.csv")
    parser.add_argument("--ipinfo", required=True, help="Ruta al catálogo IPinfo (country_asn.csv)")
    parser.add_argument("--empleados-existente", required=False, default=None,
                         help="Ruta a tu empleados.csv ya generado (opcional, comparación extra)")
    parser.add_argument("--legacy-script", required=True,
                         help="Ruta a tests/legacy/fase03_pipeline_v4.py")
    parser.add_argument("--fase03-path", required=True,
                         help="Ruta a la carpeta que contiene el paquete fase03/ (para importarlo)")
    parser.add_argument("--out-dir", default="/content/comparacion_tmp",
                         help="Carpeta de trabajo para archivos intermedios")
    args = parser.parse_args()

    sys.path.insert(0, args.fase03_path)
    from fase03.config import ConfiguracionPipeline
    from fase03.empleados import GeneradorEmpleados
    from fase03.ip_resolver import ResolutorIPinfo
    from fase03.features import (
        crear_features_temporales,
        crear_feature_impossible_travel,
        crear_feature_turnos,
        crear_features_negocio,
    )
    from fase03.exportacion import exportar_dataset_final

    import os
    os.makedirs(args.out_dir, exist_ok=True)

    legacy = cargar_modulo_legacy(args.legacy_script)

    separador("CARGANDO rba_2000_users.csv REAL")
    df_2000 = pd.read_csv(args.rba_2000)
    usuarios_seleccionados = sorted(df_2000["User ID"].unique().tolist())
    print(f"  Filas: {len(df_2000):,}  |  Usuarios distintos: {len(usuarios_seleccionados):,}")

    # --- Pipeline LEGACY (monolítico) ---
    separador("EJECUTANDO PIPELINE LEGACY (monolítico v4)")
    config_legacy = legacy.configurar_entorno()
    config_legacy["IPINFO_PATH"] = args.ipinfo
    config_legacy["N_USUARIOS"] = len(usuarios_seleccionados)
    config_legacy["OUT_EMPLEADOS"] = os.path.join(args.out_dir, "empleados_legacy.csv")
    config_legacy["OUT_DATASET_FINAL"] = os.path.join(args.out_dir, "dataset_legacy.csv")

    df_emp_legacy = legacy.generar_empleados(usuarios_seleccionados, config_legacy)
    df_int_legacy = df_2000.merge(df_emp_legacy, on="User ID", how="inner")
    df_int_legacy, _ = legacy.resolver_ips(df_int_legacy, config_legacy)
    df_int_legacy, _ = legacy.crear_features_temporales(df_int_legacy, config_legacy)
    df_int_legacy, _ = legacy.crear_feature_impossible_travel(df_int_legacy, config_legacy)
    df_int_legacy = legacy.crear_feature_turnos(df_int_legacy)
    df_int_legacy = legacy.crear_features_negocio(df_int_legacy)
    df_final_legacy = legacy.exportar_dataset_final(df_int_legacy, config_legacy)

    # --- Pipeline MODULAR ---
    separador("EJECUTANDO PIPELINE MODULAR (fase03/)")
    config_modular = ConfiguracionPipeline(
        IPINFO_PATH=args.ipinfo,
        N_USUARIOS=len(usuarios_seleccionados),
        OUT_EMPLEADOS=os.path.join(args.out_dir, "empleados_modular.csv"),
        OUT_DATASET_FINAL=os.path.join(args.out_dir, "dataset_modular.csv"),
    )
    df_emp_modular = GeneradorEmpleados(config_modular).generar(usuarios_seleccionados)
    df_int_modular = df_2000.merge(df_emp_modular, on="User ID", how="inner")
    df_int_modular, _ = ResolutorIPinfo(config_modular).resolver(df_int_modular)
    serie_target = df_int_modular.pop("Is Account Takeover")
    df_int_modular, _ = crear_features_temporales(df_int_modular, config_modular)
    df_int_modular, _ = crear_feature_impossible_travel(df_int_modular, config_modular)
    df_int_modular = crear_feature_turnos(df_int_modular)
    df_int_modular = crear_features_negocio(df_int_modular)
    df_int_modular["Is Account Takeover"] = serie_target
    df_final_modular = exportar_dataset_final(df_int_modular, config_modular)

    # --- Comparaciones ---
    reporte = {}
    comparar_forma(df_final_legacy, df_final_modular, reporte)
    comparar_columnas(df_final_legacy, df_final_modular, reporte)
    comparar_dtypes(df_final_legacy, df_final_modular, reporte)
    comparar_valores_exactos(df_final_legacy, df_final_modular, reporte)
    comparar_nulos(df_final_legacy, df_final_modular, reporte)
    comparar_distribuciones(df_final_legacy, df_final_modular, reporte)
    comparar_target(df_final_legacy, df_final_modular, reporte)
    if args.empleados_existente:
        comparar_contra_empleados_existente(
            config_modular.OUT_EMPLEADOS, args.empleados_existente, reporte
        )

    # --- Veredicto final ---
    separador("REPORTE FINAL")
    claves_criticas = [
        "forma_identica", "columnas_identicas", "dtypes_identicos",
        "valores_identicos", "nulos_identicos", "distribuciones_identicas",
        "target_identico",
    ]
    equivalente = all(reporte.get(k) for k in claves_criticas)
    for k in claves_criticas:
        print(f"  {k}: {reporte.get(k)}")
    if "coincide_con_empleados_historico" in reporte and reporte["coincide_con_empleados_historico"] is not None:
        print(f"  coincide_con_empleados_historico: {reporte['coincide_con_empleados_historico']}")

    print()
    if equivalente:
        print("VEREDICTO: EQUIVALENTE — el refactor modular produce EXACTAMENTE el "
              "mismo dataset_final_modelo.csv que el pipeline monolítico v4, con "
              "los mismos datos reales.")
    else:
        print("VEREDICTO: NO EQUIVALENTE — hay al menos una diferencia real entre "
              "el monolito y el modular. Revisa el detalle impreso arriba antes de "
              "aprobar la Etapa 1 con datos reales.")

    print()
    print("Copia TODA esta salida de consola de vuelta a Claude para decidir si "
          "se aprueba el paso a la Etapa 2.")


if __name__ == "__main__":
    main()
