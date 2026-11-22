"""
test_fase03.py
==============
Suite de regresión de la Etapa 1 (refactor arquitectónico sin cambios
metodológicos). Cuatro capas, según lo acordado:

  CAPA A — equivalencia end-to-end (modular vs. monolito v4) sobre
           datos REALES (rba_2000_users.csv + catálogo IPinfo).
           Requiere archivos que solo existen en el Colab de Javier;
           se omite automáticamente si no están presentes (ver
           conftest.py), en vez de fingir que pasó.
  CAPA B — reproducibilidad de empleados.csv (mismos seeds -> mismo
           resultado, y equivalencia contra el monolito cuando hay
           fixture real).
  CAPA C — casos límite sintéticos (ISO2, centroides, country_mismatch,
           has_previous_login, edge case de un solo grupo en el
           rolling, fix de dtype de merge_asof).
  CAPA D — prueba de no-leakage: barajar 'Is Account Takeover' no debe
           cambiar ninguna feature calculada.

Además: un smoke test end-to-end con datos 100% sintéticos (no
requiere ningún archivo externo), que prueba que PipelineFase03 corre
de principio a fin sin errores.

Cuando una comparación falla, se usa pd.testing.assert_frame_equal con
check_exact=True, que reporta explícitamente qué columna y qué valores
difieren — nunca un booleano mudo de .equals().
"""
import importlib.util
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fase03.config import ConfiguracionPipeline
from fase03.muestreo import MuestreoAleatorioSimple
from fase03.empleados import GeneradorEmpleados
from fase03.ip_resolver import ResolutorIPinfo
from fase03.features import (
    calcular_rolling_retrospectivo,
    crear_features_temporales,
    crear_feature_impossible_travel,
    crear_feature_turnos,
    crear_features_negocio,
)
from fase03.pipeline import PipelineFase03

from .conftest import requiere_fixture_real, ruta_fixture_rba_2000, ruta_fixture_ipinfo


def _cargar_monolito_v4():
    """Carga tests/legacy/fase03_pipeline_v4.py como módulo importable,
    para comparar su salida contra la arquitectura modular."""
    ruta = os.path.join(os.path.dirname(__file__), "legacy", "fase03_pipeline_v4.py")
    spec = importlib.util.spec_from_file_location("fase03_pipeline_v4_legacy", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# ============================================================================
# CAPA A — Equivalencia end-to-end contra el pipeline monolítico (datos reales)
# ============================================================================

@requiere_fixture_real
def test_capa_a_equivalencia_end_to_end_contra_monolito(tmp_path):
    """Corre el monolito v4 y la arquitectura modular a partir del
    MISMO rba_2000_users.csv real, con el mismo config, y compara el
    dataset_final_modelo.csv resultante columna por columna."""
    legacy = _cargar_monolito_v4()

    df_2000 = pd.read_csv(ruta_fixture_rba_2000())
    usuarios_seleccionados = sorted(df_2000["User ID"].unique().tolist())

    # --- Config legacy (dict) ---
    config_legacy = legacy.configurar_entorno()
    config_legacy["IPINFO_PATH"] = ruta_fixture_ipinfo()
    config_legacy["N_USUARIOS"] = len(usuarios_seleccionados)
    config_legacy["OUT_EMPLEADOS"] = str(tmp_path / "empleados_legacy.csv")
    config_legacy["OUT_DATASET_FINAL"] = str(tmp_path / "dataset_legacy.csv")

    df_emp_legacy = legacy.generar_empleados(usuarios_seleccionados, config_legacy)
    df_int_legacy = df_2000.merge(df_emp_legacy, on="User ID", how="inner")
    df_int_legacy, _ = legacy.resolver_ips(df_int_legacy, config_legacy)
    df_int_legacy, _ = legacy.crear_features_temporales(df_int_legacy, config_legacy)
    df_int_legacy, _ = legacy.crear_feature_impossible_travel(df_int_legacy, config_legacy)
    df_int_legacy = legacy.crear_feature_turnos(df_int_legacy)
    df_int_legacy = legacy.crear_features_negocio(df_int_legacy)
    df_final_legacy = legacy.exportar_dataset_final(df_int_legacy, config_legacy)

    # --- Config modular (dataclass) ---
    config_modular = ConfiguracionPipeline(
        IPINFO_PATH=ruta_fixture_ipinfo(),
        N_USUARIOS=len(usuarios_seleccionados),
        OUT_EMPLEADOS=str(tmp_path / "empleados_modular.csv"),
        OUT_DATASET_FINAL=str(tmp_path / "dataset_modular.csv"),
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
    from fase03.exportacion import exportar_dataset_final
    df_final_modular = exportar_dataset_final(df_int_modular, config_modular)

    pd.testing.assert_frame_equal(
        df_final_legacy.reset_index(drop=True),
        df_final_modular.reset_index(drop=True),
        check_exact=True,
        check_dtype=True,
    )


# ============================================================================
# CAPA B — Reproducibilidad de empleados.csv
# ============================================================================

def test_capa_b_empleados_reproducible_mismos_seeds():
    """Mismos RANDOM_STATE/FAKER_SEED + mismos usuarios -> mismo
    empleados.csv, byte a byte (columna a columna)."""
    config = ConfiguracionPipeline(N_USUARIOS=10)
    usuarios = list(range(1, 11))

    config.OUT_EMPLEADOS = "/tmp/empleados_run1.csv"
    df1 = GeneradorEmpleados(config).generar(usuarios)

    config.OUT_EMPLEADOS = "/tmp/empleados_run2.csv"
    df2 = GeneradorEmpleados(config).generar(usuarios)

    pd.testing.assert_frame_equal(df1, df2, check_exact=True)


@requiere_fixture_real
def test_capa_b_empleados_equivalente_a_monolito(tmp_path):
    """empleados.csv generado por la clase modular debe ser idéntico
    al generado por generar_empleados() del monolito, con el mismo
    config y la misma lista de usuarios reales."""
    legacy = _cargar_monolito_v4()

    df_2000 = pd.read_csv(ruta_fixture_rba_2000())
    usuarios_seleccionados = sorted(df_2000["User ID"].unique().tolist())

    config_legacy = legacy.configurar_entorno()
    config_legacy["N_USUARIOS"] = len(usuarios_seleccionados)
    config_legacy["OUT_EMPLEADOS"] = str(tmp_path / "empleados_legacy.csv")
    df_emp_legacy = legacy.generar_empleados(usuarios_seleccionados, config_legacy)

    config_modular = ConfiguracionPipeline(
        N_USUARIOS=len(usuarios_seleccionados),
        OUT_EMPLEADOS=str(tmp_path / "empleados_modular.csv"),
    )
    df_emp_modular = GeneradorEmpleados(config_modular).generar(usuarios_seleccionados)

    pd.testing.assert_frame_equal(
        df_emp_legacy.reset_index(drop=True),
        df_emp_modular.reset_index(drop=True),
        check_exact=True,
    )


# ============================================================================
# CAPA C — Casos límite sintéticos
# ============================================================================

def test_capa_c_pais_residencia_es_iso2():
    config = ConfiguracionPipeline(N_USUARIOS=5, OUT_EMPLEADOS="/tmp/empleados_c1.csv")
    df_emp = GeneradorEmpleados(config).generar([1, 2, 3, 4, 5])
    assert set(df_emp["Pais_Residencia"].unique()).issubset(config.ISO2_RECONOCIDOS)


def test_capa_c_centroides_usan_iso2_no_nombres_espanol():
    from fase03.config import CENTROIDES_GEOGRAFICOS
    assert "CO" in CENTROIDES_GEOGRAFICOS
    assert "Colombia" not in CENTROIDES_GEOGRAFICOS


def test_capa_c_country_mismatch_iso2_vs_iso2_y_nan_cuando_falta_info():
    df = pd.DataFrame({
        "Pais_Residencia": ["CO", "ES", "MX", None],
        "ip_country_code": ["CO", "US", "MX", "US"],
        "Estado_Cuenta": ["Activo", "Activo", "Inactivo", "Activo"],
        "login_exitoso_normalizado": [True, True, True, True],
    })
    df = crear_features_negocio(df)
    assert df.loc[0, "country_mismatch"] == 0
    assert df.loc[1, "country_mismatch"] == 1
    assert df.loc[2, "country_mismatch"] == 0
    assert pd.isna(df.loc[3, "country_mismatch"])


def test_capa_c_has_previous_login_y_nan_forzado_en_impossible_travel():
    config = ConfiguracionPipeline()
    df = pd.DataFrame({
        "User ID": [1, 1, 1],
        "IP Address": ["1.1.1.1", "1.1.1.2", "1.1.1.3"],
        "Login Timestamp": [1580000000, 1580000900, 1580100000],
        "Login Successful": [True, False, True],
        "Country": ["CO", "CO", "US"],
    })
    df, _ = crear_features_temporales(df, config)
    assert df.loc[0, "has_previous_login"] == 0
    assert df.loc[1, "has_previous_login"] == 1
    assert df.loc[2, "has_previous_login"] == 1

    df, _ = crear_feature_impossible_travel(df, config)
    assert pd.isna(df.loc[0, "distance_previous_km"])
    assert pd.isna(df.loc[0, "required_speed_kmh"])
    # CO -> US SÍ debe resolver distancia (centroides ISO2 alineados con
    # el formato nativo de RBA "Country"; antes, con nombres en español,
    # este lookup fallaba silenciosamente).
    assert not pd.isna(df.loc[2, "distance_previous_km"])


def test_capa_c_rolling_retrospectivo_con_un_solo_usuario():
    """Edge case de pandas >= 3.0: groupby().apply() puede devolver un
    DataFrame en vez de una Series concatenada cuando hay un único
    grupo. calcular_rolling_retrospectivo() debe ser robusto a esto."""
    df = pd.DataFrame({
        "User ID": [1, 1, 1],
        "Login Timestamp": pd.to_datetime([1580000000, 1580000900, 1580100000], unit="s"),
        "is_failed": [0, 1, 0],
    })
    resultado = calcular_rolling_retrospectivo(df, "is_failed", "15min")
    assert isinstance(resultado, pd.Series)
    assert pd.isna(resultado.iloc[0])
    assert resultado.iloc[1] == 0.0


def test_capa_c_merge_asof_dtype_fix_reproduce_escenario_real():
    """Reproduce el escenario exacto que causó el MergeError original:
    RBA con IPv6 mezclada (fuerza float64 en ip_int) vs. catálogo
    IPinfo 100% IPv4 (nace int64 nativamente)."""
    config = ConfiguracionPipeline(IPINFO_PATH="/tmp/ipinfo_mini_capa_c.csv")

    df_logs = pd.DataFrame({
        "IP Address": ["8.8.8.8", "1.1.1.1", "2001:db8::1", "9.9.9.9"],
    })
    from fase03.ip_utils import clasificar_ip
    clasif = df_logs["IP Address"].apply(clasificar_ip)
    df_logs["ip_int"] = clasif.apply(lambda t: t[0])
    df_logs["ip_version"] = clasif.apply(lambda t: t[1])
    assert df_logs["ip_int"].dtype == np.float64  # confirma que se reprodujo el escenario

    df_ipinfo_mini = pd.DataFrame({
        "start_ip": ["1.0.0.0", "8.0.0.0", "9.0.0.0"],
        "end_ip": ["1.255.255.255", "8.255.255.255", "9.255.255.255"],
        "country": ["US", "US", "US"],
        "country_name": ["United States", "United States", "United States"],
        "asn": ["AS1", "AS2", "AS3"],
        "as_name": ["A", "B", "C"],
        "as_domain": ["a.com", "b.com", "c.com"],
    })
    df_ipinfo_mini.to_csv(config.IPINFO_PATH, index=False)

    # No debe lanzar MergeError.
    df_resultado, diagnostico = ResolutorIPinfo(config).resolver(df_logs)
    assert diagnostico["ipv4_unicas_resueltas"] == 3


# ============================================================================
# CAPA D — Prueba de no-leakage
# ============================================================================

def _df_integrado_sintetico(n_usuarios=3, eventos_por_usuario=5, seed=0):
    rng = np.random.default_rng(seed)
    filas = []
    paises = ["CO", "US", "ES"]
    for uid in range(1, n_usuarios + 1):
        base_ts = 1580000000
        for i in range(eventos_por_usuario):
            filas.append({
                "User ID": uid,
                "IP Address": f"1.1.1.{uid}",
                "Login Timestamp": base_ts + i * 1000,
                "Login Successful": bool(rng.integers(0, 2)),
                "Country": paises[uid % len(paises)],
                "Pais_Residencia": paises[(uid + 1) % len(paises)],
                "ip_country_code": paises[uid % len(paises)],
                "Estado_Cuenta": "Activo" if uid % 2 == 0 else "Inactivo",
                "Turno_Asignado": "Diurno",
            })
    return pd.DataFrame(filas)


def _construir_todas_las_features(df, config):
    df, _ = crear_features_temporales(df, config)
    df, _ = crear_feature_impossible_travel(df, config)
    df = crear_feature_turnos(df)
    df = crear_features_negocio(df)
    return df


def test_capa_d_no_leakage_barajar_target_no_cambia_ninguna_feature():
    """Construye el mismo DataFrame base dos veces, cambiando
    ÚNICAMENTE los valores de 'Is Account Takeover' (barajados
    aleatoriamente), y confirma que TODAS las columnas de features
    calculadas son idénticas entre ambas corridas."""
    config = ConfiguracionPipeline()
    rng = np.random.default_rng(1)

    base = _df_integrado_sintetico()
    target_a = rng.integers(0, 2, size=len(base)).astype(bool)
    target_b = rng.permutation(target_a)  # mismos valores, orden barajado

    df_a = base.copy()
    df_a["Is Account Takeover"] = target_a
    df_b = base.copy()
    df_b["Is Account Takeover"] = target_b

    # Barrera real del pipeline: se retira ANTES de construir features.
    df_a.pop("Is Account Takeover")
    df_b.pop("Is Account Takeover")

    df_a = _construir_todas_las_features(df_a, config)
    df_b = _construir_todas_las_features(df_b, config)

    columnas_features = [
        "failed_attempts_15min", "failed_attempts_1h", "has_previous_login",
        "distance_previous_km", "required_speed_kmh", "impossible_travel",
        "is_outside_shift", "country_mismatch", "inactive_account_success",
    ]
    pd.testing.assert_frame_equal(
        df_a[columnas_features].reset_index(drop=True),
        df_b[columnas_features].reset_index(drop=True),
        check_exact=True,
    )


def test_capa_d_features_py_no_menciona_is_account_takeover():
    """Garantía estructural adicional: el código fuente de features.py
    no debe contener ninguna referencia textual a 'Is Account
    Takeover'. Si alguien la agregara por descuido, este test la
    detecta sin necesidad de ejecutar nada."""
    ruta_features = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "fase03", "features.py"
    )
    contenido = open(ruta_features, encoding="utf-8").read()
    assert "Is Account Takeover" not in contenido


# ============================================================================
# SMOKE TEST — pipeline completo con datos 100% sintéticos (sin
# depender de ningún archivo externo). No es una de las 4 capas
# acordadas, mide únicamente que el cableado (imports, orquestación,
# inyección de dependencia) funciona de principio a fin.
# ============================================================================

def _generar_rba_sintetico(ruta, n_usuarios=8, eventos_por_usuario=16, seed=7):
    rng = np.random.default_rng(seed)
    filas = []
    ts_base = 1_580_000_000
    for uid in range(1, n_usuarios + 1):
        for i in range(eventos_por_usuario):
            filas.append({
                "User ID": uid,
                "IP Address": f"8.8.8.{(uid * 3 + i) % 255}",
                "Login Timestamp": ts_base + i * 900 + uid * 10,
                "Login Successful": bool(rng.integers(0, 2)),
                "Device Type": "Desktop",
                "Is Attack IP": False,
                "Is Account Takeover": bool(i == 0 and uid == 1),
                "Country": "CO" if uid % 2 == 0 else "US",
                "Region": "N/A",
                "City": "N/A",
                "ASN": "AS1",
                "Round-Trip Time [ms]": 50,
            })
    pd.DataFrame(filas).to_csv(ruta, index=False)


def _generar_ipinfo_sintetico(ruta):
    df = pd.DataFrame({
        "start_ip": ["8.8.8.0"],
        "end_ip": ["8.8.8.255"],
        "country": ["US"],
        "country_name": ["United States"],
        "asn": ["AS15169"],
        "as_name": ["Google"],
        "as_domain": ["google.com"],
    })
    df.to_csv(ruta, index=False)


def test_smoke_pipeline_completo_end_to_end_sintetico(tmp_path):
    rba_path = tmp_path / "rba_mini.csv"
    ipinfo_path = tmp_path / "ipinfo_mini.csv"
    _generar_rba_sintetico(str(rba_path))
    _generar_ipinfo_sintetico(str(ipinfo_path))

    config = ConfiguracionPipeline(
        RBA_PATH=str(rba_path),
        IPINFO_PATH=str(ipinfo_path),
        OUT_RBA_2000=str(tmp_path / "rba_seleccionados.csv"),
        OUT_EMPLEADOS=str(tmp_path / "empleados.csv"),
        OUT_DATASET_FINAL=str(tmp_path / "dataset_final_modelo.csv"),
        N_USUARIOS=5,
        MIN_EVENTOS_USUARIO=10,
        CHUNKSIZE_PASADA_1=1000,
        CHUNKSIZE_PASADA_2=1000,
    )
    estrategia = MuestreoAleatorioSimple(config)
    pipeline = PipelineFase03(config, estrategia)

    df_final = pipeline.ejecutar()

    assert len(df_final) > 0
    assert df_final["User ID"].nunique() == 5
    assert "Is Account Takeover" in df_final.columns
    assert "has_previous_login" in df_final.columns
    assert "country_mismatch" in df_final.columns
    assert os.path.exists(config.OUT_DATASET_FINAL)

# ============================================================================
# ETAPA 2 — muestreo ATO, split por usuario, X/y, preprocesamiento,
# remuestreo solo TRAIN, leakage. Datos 100% sintéticos.
# ============================================================================
from collections import Counter

from fase03.rba_reader import AnalizadorRBA
from fase03.muestreo import MuestreoEstratificadoPorTarget
from fase03.split import dividir_train_test_por_usuario
from fase03.preprocessing import (
    COLUMNAS_FEATURES,
    separar_x_y,
    preprocesar_train_test,
    escalar_train_test_experimental,
    evaluar_pca_experimental,
)
from fase03.resampling import remuestrear_train


def _df_modelado_sintetico(n_usuarios=40, eventos_por_usuario=10,
                           usuarios_ato=(1, 2, 3, 4, 5, 6), seed=0):
    rng = np.random.default_rng(seed)
    filas = []
    for uid in range(1, n_usuarios + 1):
        for i in range(eventos_por_usuario):
            es_ato = (uid in usuarios_ato) and (i == 3)
            filas.append({
                "User ID": uid,
                "Is Account Takeover": bool(es_ato),
                "Device Type": str(rng.choice(["Desktop", "Mobile"])),
                "Rol_Hospitalario": str(rng.choice(["Enfermero/a", "Médico General"])),
                "Pais_Residencia": str(rng.choice(["CO", "US"])),
                "Ciudad_Base": str(rng.choice(["Bogotá", "Cali"])),
                "Turno_Asignado": str(rng.choice(["Diurno", "Nocturno"])),
                "Estado_Cuenta": str(rng.choice(["Activo", "Inactivo"])),
                "Is Attack IP": bool(rng.integers(0, 2)),
                "login_exitoso_normalizado": bool(rng.integers(0, 2)),
                "has_previous_login": int(i > 0),
                "impossible_travel": 0,
                "is_outside_shift": int(rng.integers(0, 2)),
                "country_mismatch": float(rng.integers(0, 2)) if rng.random() > 0.2 else np.nan,
                "inactive_account_success": int(rng.integers(0, 2)),
                "failed_attempts_15min": float(rng.integers(0, 4)),
                "failed_attempts_1h": float(rng.integers(0, 6)),
                "time_since_previous_login_hours": np.nan if i == 0 else float(rng.random() * 10 + 0.1),
                "distance_previous_km": np.nan if i == 0 else float(rng.random() * 500),
                "required_speed_kmh": np.nan if i == 0 else float(rng.random() * 100),
                "IP Address": f"1.1.1.{uid}",
                "Nombre_Completo": f"Persona {uid}",
            })
    return pd.DataFrame(filas)


def _train_test_preparados():
    df = _df_modelado_sintetico()
    config = ConfiguracionPipeline()
    df_train, df_test, _ = dividir_train_test_por_usuario(df, config)
    X_train, y_train = separar_x_y(df_train)
    X_test, y_test = separar_x_y(df_test)
    return config, df_train, df_test, X_train, y_train, X_test, y_test


# ---------------------------- Muestreo ATO ----------------------------------

def test_etapa2_primera_pasada_devuelve_contador_ato(tmp_path):
    ruta = tmp_path / "rba.csv"
    _generar_rba_sintetico(str(ruta))          # 8 usuarios x 16 eventos; ATO solo usuario 1
    config = ConfiguracionPipeline(RBA_PATH=str(ruta), CHUNKSIZE_PASADA_1=25)
    contador, contador_ato, diag = AnalizadorRBA(config).primera_pasada()
    assert sum(contador.values()) == 8 * 16
    assert dict(contador_ato) == {1: 1}
    assert diag["total_ips"] == 8 * 16


def test_etapa2_muestreo_estratificado_incluye_ato_elegibles_y_es_reproducible():
    contador = Counter({uid: 20 for uid in range(1, 101)})
    contador[500] = 5                              # usuario ATO con pocos eventos
    contador_ato = Counter({3: 1, 7: 2, 500: 1})
    config = ConfiguracionPipeline(N_USUARIOS=10, MIN_EVENTOS_USUARIO=15)

    res = MuestreoEstratificadoPorTarget(config).seleccionar(contador, contador_ato)
    assert len(res.usuarios) == 10 == len(set(res.usuarios))
    assert {3, 7} <= set(res.usuarios)
    assert 500 not in res.usuarios                 # ATO no elegible: nunca entra
    assert all(contador[u] >= 15 for u in res.usuarios)
    assert res.origen[3] == "ato_elegible"
    negativos = [u for u in res.usuarios if res.origen[u] == "aleatorio_no_ato"]
    assert len(negativos) == 8
    assert not (set(negativos) & set(contador_ato.keys()))

    res2 = MuestreoEstratificadoPorTarget(config).seleccionar(contador, contador_ato)
    assert res.usuarios == res2.usuarios


def test_etapa2_muestreo_estratificado_falla_sin_ato_elegibles_o_sin_contador():
    contador = Counter({uid: 20 for uid in range(1, 51)})
    contador[500] = 5
    config = ConfiguracionPipeline(N_USUARIOS=10, MIN_EVENTOS_USUARIO=15)
    estrategia = MuestreoEstratificadoPorTarget(config)
    with pytest.raises(ValueError):
        estrategia.seleccionar(contador, Counter({500: 1}))
    with pytest.raises(ValueError):
        estrategia.seleccionar(contador, None)


def test_etapa2_muestreo_aleatorio_ignora_contador_ato():
    contador = Counter({uid: 20 for uid in range(1, 101)})
    config = ConfiguracionPipeline(N_USUARIOS=10, MIN_EVENTOS_USUARIO=15)
    a = MuestreoAleatorioSimple(config).seleccionar(contador, None)
    b = MuestreoAleatorioSimple(config).seleccionar(contador, Counter({3: 1}))
    assert a.usuarios == b.usuarios


# ------------------------------- Split --------------------------------------

def test_etapa2_split_por_usuario_sin_solapamiento_y_usuarios_completos():
    df = _df_modelado_sintetico()
    df_train, df_test, info = dividir_train_test_por_usuario(df, ConfiguracionPipeline())
    u_train, u_test = set(df_train["User ID"]), set(df_test["User ID"])
    assert u_train.isdisjoint(u_test)
    assert (u_train | u_test) == set(df["User ID"])
    assert len(df_train) + len(df_test) == len(df)
    assert info["solapamiento_usuarios"] == 0
    por_usuario = df.groupby("User ID").size()
    parcial = df_train.groupby("User ID").size()
    pd.testing.assert_series_equal(parcial, por_usuario.loc[parcial.index], check_names=False)


def test_etapa2_split_positivos_en_train_y_test():
    df = _df_modelado_sintetico()
    df_train, df_test, info = dividir_train_test_por_usuario(df, ConfiguracionPipeline())
    assert int(df_train["Is Account Takeover"].sum()) >= 1
    assert int(df_test["Is Account Takeover"].sum()) >= 1
    assert info["train"]["ato_usuarios"] >= 1 and info["test"]["ato_usuarios"] >= 1


def test_etapa2_split_se_detiene_con_menos_de_2_usuarios_ato():
    df = _df_modelado_sintetico(usuarios_ato=(1,))
    with pytest.raises(ValueError):
        dividir_train_test_por_usuario(df, ConfiguracionPipeline())


# ------------------------------- X / y --------------------------------------

def test_etapa2_separar_x_y_excluye_target_e_identificadores():
    df = _df_modelado_sintetico()
    X, y = separar_x_y(df)
    assert "Is Account Takeover" not in X.columns
    assert "User ID" not in X.columns
    assert "IP Address" not in X.columns and "Nombre_Completo" not in X.columns
    assert list(X.columns) == COLUMNAS_FEATURES
    assert set(y.unique()) <= {0, 1}
    assert len(X) == len(y)
    pd.testing.assert_series_equal(
        X["distance_previous_km_faltante"],
        X["distance_previous_km"].isna().astype("float64"),
        check_names=False,
    )


def test_etapa2_separar_x_y_target_con_nulos_se_detiene():
    df = _df_modelado_sintetico()
    df["Is Account Takeover"] = df["Is Account Takeover"].astype(object)
    df.loc[0, "Is Account Takeover"] = np.nan
    with pytest.raises(ValueError):
        separar_x_y(df)


# ------------------------ Preprocesamiento (fit solo TRAIN) -----------------

def test_etapa2_categoria_desconocida_en_test_no_falla_ni_crea_columnas():
    _, _, _, X_train, _, X_test, _ = _train_test_preparados()
    X_test = X_test.copy()
    X_test.loc[X_test.index[0], "Ciudad_Base"] = "CiudadInexistente"
    _, Xt_train, Xt_test = preprocesar_train_test(X_train, X_test)
    assert list(Xt_train.columns) == list(Xt_test.columns)
    # Si el encoder se hubiera ajustado con TRAIN+TEST, existiría esta columna.
    assert not any("CiudadInexistente" in c for c in Xt_train.columns)


def test_etapa2_preprocesamiento_sin_nan_ni_infinitos():
    _, _, _, X_train, _, X_test, _ = _train_test_preparados()
    _, Xt_train, Xt_test = preprocesar_train_test(X_train, X_test)
    for Xt in (Xt_train, Xt_test):
        assert not Xt.isna().any().any()
        assert np.isfinite(Xt.to_numpy(dtype="float64")).all()


def test_etapa2_imputador_usa_mediana_de_train_no_de_train_mas_test():
    _, _, _, X_train, _, X_test, _ = _train_test_preparados()
    X_train, X_test = X_train.copy(), X_test.copy()
    X_train["distance_previous_km"] = 10.0
    X_test["distance_previous_km"] = 1000.0
    X_train.iloc[0, X_train.columns.get_loc("distance_previous_km")] = np.nan
    X_test.iloc[0, X_test.columns.get_loc("distance_previous_km")] = np.nan
    _, Xt_train, Xt_test = preprocesar_train_test(X_train, X_test)
    # Mediana TRAIN = 10. Con fit(train+test) sería distinta (~505 o más).
    assert Xt_test["num__distance_previous_km"].iloc[0] == pytest.approx(10.0)
    assert Xt_test["num__distance_previous_km"].iloc[1] == pytest.approx(1000.0)


def test_etapa2_barajar_target_no_cambia_el_preprocesamiento():
    config, df_train, df_test, _, _, X_test, _ = _train_test_preparados()
    X1, _ = separar_x_y(df_train)
    df_b = df_train.copy()
    rng = np.random.default_rng(3)
    df_b["Is Account Takeover"] = rng.permutation(df_b["Is Account Takeover"].to_numpy())
    X2, _ = separar_x_y(df_b)
    _, A1, B1 = preprocesar_train_test(X1, X_test)
    _, A2, B2 = preprocesar_train_test(X2, X_test)
    pd.testing.assert_frame_equal(A1, A2)
    pd.testing.assert_frame_equal(B1, B2)


# ----------------------- Remuestreo (solo TRAIN) ----------------------------

def test_etapa2_remuestreo_solo_train_test_intacto_sin_filas_nuevas():
    config, df_train, df_test, X_train, y_train, X_test, y_test = _train_test_preparados()
    _, Xt_train, Xt_test = preprocesar_train_test(X_train, X_test)
    Xt_test_antes, y_test_antes = Xt_test.copy(), y_test.copy()
    pos_antes = int(y_train.sum())
    neg_antes = int((y_train == 0).sum())

    X_res, y_res, info = remuestrear_train(Xt_train, y_train, config)

    assert int(y_res.sum()) > pos_antes                    # positivos aumentan en TRAIN
    assert int((y_res == 0).sum()) == neg_antes            # negativos no cambian
    assert int(y_res.sum()) == int((y_res == 0).sum())     # ratio 1.0
    assert info["despues"][1] > info["antes"][1]
    # TEST: intacto, sin duplicados, positivos iguales a los eventos ATO originales
    pd.testing.assert_frame_equal(Xt_test, Xt_test_antes)
    pd.testing.assert_series_equal(y_test, y_test_antes)
    assert len(Xt_test) == len(df_test)
    assert int(y_test.sum()) == int(df_test["Is Account Takeover"].sum())
    # Solo duplicación de filas reales de TRAIN (no se inventan filas)
    filas_res = set(map(tuple, X_res.to_numpy()))
    filas_train = set(map(tuple, Xt_train.to_numpy()))
    assert filas_res <= filas_train


def test_etapa2_remuestreo_se_detiene_si_train_no_tiene_ambas_clases():
    config = ConfiguracionPipeline()
    X = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
    y = pd.Series([0, 0, 0], name="Is Account Takeover")
    with pytest.raises(ValueError):
        remuestrear_train(X, y, config)


# ------------------ Scaling / PCA: SOLO experimentales ----------------------

def test_etapa2_scaler_experimental_ajustado_solo_con_train():
    _, _, _, X_train, _, X_test, _ = _train_test_preparados()
    X_train, X_test = X_train.copy(), X_test.copy()
    X_train["distance_previous_km"] = 10.0
    X_test["distance_previous_km"] = 1000.0
    _, Xt_train, Xt_test = preprocesar_train_test(X_train, X_test)
    _, Xe_train, Xe_test = escalar_train_test_experimental(Xt_train, Xt_test)
    col = "num__distance_previous_km"
    assert Xe_train[col].abs().max() == pytest.approx(0.0)      # mediana TRAIN = 10
    assert Xe_test[col].iloc[0] == pytest.approx(990.0)          # (1000-10)/1, sin refit


def test_etapa2_pca_experimental_solo_train_y_dimensionalidad_coherente():
    _, _, _, X_train, _, X_test, _ = _train_test_preparados()
    _, Xt_train, _ = preprocesar_train_test(X_train, X_test)
    r = evaluar_pca_experimental(Xt_train)
    n90, n95, n99 = (r["n_componentes"][k] for k in ("90%", "95%", "99%"))
    assert 1 <= n90 <= n95 <= n99 <= r["n_features"] == Xt_train.shape[1]
    assert r["varianza_acumulada"][-1] == pytest.approx(1.0)
    assert r["ajustado_con"] == "TRAIN unicamente"


# --------------------------- Integración ------------------------------------

def test_etapa2_pipeline_completo_estratificado_y_modelado_sintetico(tmp_path):
    rba_path = tmp_path / "rba_mini.csv"
    ipinfo_path = tmp_path / "ipinfo_mini.csv"
    _generar_rba_sintetico(str(rba_path), n_usuarios=30, eventos_por_usuario=16)
    _generar_ipinfo_sintetico(str(ipinfo_path))

    df = pd.read_csv(rba_path)
    primera_fila = df.drop_duplicates(subset="User ID").index
    idx_ato = [i for i in primera_fila if int(df.loc[i, "User ID"]) in {1, 2, 3, 4, 5, 6}]
    df.loc[idx_ato, "Is Account Takeover"] = True
    df.to_csv(rba_path, index=False)

    config = ConfiguracionPipeline(
        RBA_PATH=str(rba_path), IPINFO_PATH=str(ipinfo_path),
        OUT_RBA_2000=str(tmp_path / "rba_sel.csv"),
        OUT_EMPLEADOS=str(tmp_path / "empleados.csv"),
        OUT_DATASET_FINAL=str(tmp_path / "dataset_final_modelo.csv"),
        OUT_TRAIN_PREPARED=str(tmp_path / "train_prepared.csv"),
        OUT_TEST_PREPARED=str(tmp_path / "test_prepared.csv"),
        OUT_PREPROCESSOR=str(tmp_path / "preprocessor.joblib"),
        N_USUARIOS=20, MIN_EVENTOS_USUARIO=10,
        CHUNKSIZE_PASADA_1=100, CHUNKSIZE_PASADA_2=100,
    )
    pipeline = PipelineFase03(config, MuestreoEstratificadoPorTarget(config))
    df_final = pipeline.ejecutar()
    assert df_final["User ID"].nunique() == 20
    assert int(df_final["Is Account Takeover"].sum()) >= 6   # los 6 usuarios ATO entraron

    res = pipeline.preparar_datasets_modelado(df_final)
    assert "Is Account Takeover" not in res["X_train"].columns
    assert list(res["X_train"].columns) == list(res["X_test"].columns)
    assert int(res["y_train"].sum()) == int((res["y_train"] == 0).sum())
    assert int(res["y_test"].sum()) >= 1
    assert res["info_split"]["solapamiento_usuarios"] == 0
    for ruta in (config.OUT_TRAIN_PREPARED, config.OUT_TEST_PREPARED, config.OUT_PREPROCESSOR):
        assert os.path.exists(ruta)