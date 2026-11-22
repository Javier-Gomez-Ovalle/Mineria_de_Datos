"""Regresión de asociación evento-etiqueta; sin E/S de datos ni pipeline completo."""
import ast
from pathlib import Path

import pandas as pd
import pytest

from fase03.asociacion_target import (
    CLAVE_EVENTO, capturar_asociacion_target, verificar_asociacion_target,
)
from fase03.config import ConfiguracionPipeline
from fase03.features import (
    crear_features_temporales, crear_feature_impossible_travel,
    crear_feature_turnos, crear_features_negocio,
)


TARGET = "Is Account Takeover"


@pytest.fixture
def eventos():
    return pd.DataFrame({
        "event_id": ["evento_c", "evento_a", "evento_b"],
        "User ID": [2, 1, 2],
        "Login Timestamp": ["2020-02-04 12:00:00", "2020-02-03 10:00:00", "2020-02-04 10:00:00"],
        "IP Address": ["1.1.1.3", "1.1.1.1", "1.1.1.2"],
        "Login Successful": [True, False, False],
        "Country": ["US", "CO", "CO"],
        "Pais_Residencia": ["CO", "CO", "CO"],
        "ip_country_code": ["US", "CO", "CO"],
        "Estado_Cuenta": ["Activo"] * 3,
        "Turno_Asignado": ["Diurno"] * 3,
        TARGET: [True, False, False],
    })


def _etapa_real_de_features(df):
    """Ejecuta solo el bloque corregido del orquestador, leído de su AST.

No importa los servicios de lectura/generación (Faker no está instalado),
ni ejecuta ejecutar(), split, preprocesamiento, resampling o exportaciones.
Los cálculos de features y las guardas sí son las funciones reales.
"""
    ruta = Path(__file__).parents[1] / "fase03" / "pipeline.py"
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    clase = next(n for n in arbol.body if isinstance(n, ast.ClassDef) and n.name == "PipelineFase03")
    metodo = next(n for n in clase.body if isinstance(n, ast.FunctionDef) and n.name == "ejecutar")
    inicio = next(i for i, n in enumerate(metodo.body) if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "referencia_target" for t in n.targets))
    fin = next(i for i, n in enumerate(metodo.body) if isinstance(n, ast.Delete)
               and any(isinstance(t, ast.Name) and t.id == "referencia_target" for t in n.targets))
    bloque = ast.Module(body=metodo.body[inicio:fin + 1], type_ignores=[])
    espacio = {"df_integrado": df.copy(deep=True), "config": ConfiguracionPipeline()}
    for funcion in [capturar_asociacion_target, verificar_asociacion_target,
                    crear_features_temporales, crear_feature_impossible_travel,
                    crear_feature_turnos, crear_features_negocio]:
        espacio[funcion.__name__] = funcion
    exec(compile(bloque, str(ruta), "exec"), espacio)
    return espacio["df_integrado"]


def test_regresion_reproduce_fallo_original_y_aprueba_correccion(eventos):
    referencia = capturar_asociacion_target(eventos)
    roto = eventos.copy()
    serie = roto.pop(TARGET)
    roto = roto.sort_values(["User ID", "Login Timestamp"]).reset_index(drop=True)
    roto[TARGET] = serie
    assert roto[TARGET].sum() == eventos[TARGET].sum()
    with pytest.raises(ValueError, match="Desalineación"):
        verificar_asociacion_target(roto, referencia)
    correcto = _etapa_real_de_features(eventos)
    verificar_asociacion_target(correcto, referencia)
    assert correcto.set_index("event_id")[TARGET].to_dict() == eventos.set_index("event_id")[TARGET].to_dict()
    assert correcto["event_id"].tolist() == ["evento_a", "evento_b", "evento_c"]


def test_independiente_de_indices_repetidos_y_reinicio(eventos):
    eventos.index = [90, 90, -7]
    referencia = capturar_asociacion_target(eventos)
    resultado = _etapa_real_de_features(eventos)
    verificar_asociacion_target(resultado, referencia)


def test_features_no_dependen_del_target(eventos):
    cambiado = eventos.copy()
    cambiado[TARGET] = ~cambiado[TARGET]
    a, b = _etapa_real_de_features(eventos), _etapa_real_de_features(cambiado)
    pd.testing.assert_frame_equal(a.drop(columns=TARGET), b.drop(columns=TARGET), check_exact=True)


@pytest.mark.parametrize("valor", [None, float("nan"), "", "ATO", 2, -1])
def test_rechaza_etiquetas_invalidas_antes_y_despues(eventos, valor):
    referencia = capturar_asociacion_target(eventos)
    invalido = eventos.astype({TARGET: object})
    invalido.loc[0, TARGET] = valor
    with pytest.raises(ValueError):
        capturar_asociacion_target(invalido)
    with pytest.raises(ValueError):
        verificar_asociacion_target(invalido, referencia)


def test_rechaza_perdida_de_columna_target(eventos):
    referencia = capturar_asociacion_target(eventos)
    with pytest.raises(ValueError, match="Faltan columnas"):
        verificar_asociacion_target(eventos.drop(columns=TARGET), referencia)


def test_rechaza_perdida_de_filas(eventos):
    with pytest.raises(ValueError, match="número de filas"):
        verificar_asociacion_target(eventos.iloc[1:], capturar_asociacion_target(eventos))


def test_rechaza_fila_nueva(eventos):
    nueva = eventos.iloc[[0]].copy()
    nueva["IP Address"] = "9.9.9.9"
    with pytest.raises(ValueError, match="número de filas"):
        verificar_asociacion_target(pd.concat([eventos, nueva]), capturar_asociacion_target(eventos))


def test_rechaza_duplicados_antes_y_despues(eventos):
    duplicado = pd.concat([eventos, eventos.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicada"):
        capturar_asociacion_target(duplicado)
    with pytest.raises(ValueError, match="duplicada"):
        verificar_asociacion_target(duplicado, capturar_asociacion_target(eventos))


def test_rechaza_sustitucion_de_evento_con_mismo_numero_de_filas(eventos):
    modificado = eventos.copy()
    modificado.loc[0, "IP Address"] = "9.9.9.9"
    with pytest.raises(ValueError, match="identidad"):
        verificar_asociacion_target(modificado, capturar_asociacion_target(eventos))


@pytest.mark.parametrize("columna", CLAVE_EVENTO)
def test_rechaza_claves_nulas(eventos, columna):
    invalido = eventos.astype({columna: object})
    invalido.loc[0, columna] = None
    with pytest.raises(ValueError, match="Clave de evento"):
        capturar_asociacion_target(invalido)


def test_clave_canonica_admite_epoch_a_datetime(eventos):
    eventos["Login Timestamp"] = pd.to_datetime(eventos["Login Timestamp"]).astype("int64") // 10**9
    referencia = capturar_asociacion_target(eventos)
    verificar_asociacion_target(_etapa_real_de_features(eventos), referencia)


def test_guardas_no_modifican_entrada(eventos):
    copia = eventos.copy(deep=True)
    referencia = capturar_asociacion_target(eventos)
    verificar_asociacion_target(eventos, referencia)
    pd.testing.assert_frame_equal(eventos, copia, check_exact=True)


def test_rechaza_columnas_duplicadas(eventos):
    invalido = pd.concat([eventos, eventos[[TARGET]]], axis=1)
    with pytest.raises(ValueError, match="Columnas duplicadas"):
        capturar_asociacion_target(invalido)
