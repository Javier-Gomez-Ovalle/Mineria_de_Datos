"""Contratos de reconciliación y preservación del CSV, íntegramente en memoria."""
import pandas as pd
import pytest

from fase03.reconciliacion_target import (
    ATRIBUTOS_ORIGINALES, reconciliar_eventos, preparar_csv_corregido,
)


TARGET = "Is Account Takeover"


@pytest.fixture
def fuentes():
    original = pd.DataFrame({
        "User ID": [2, 1], "Login Timestamp": ["2020-01-01", "2020-01-02"],
        "IP Address": ["1.1.1.2", "1.1.1.1"], TARGET: [True, False],
        "_fila_original": [100, 200],
    })
    for col in ATRIBUTOS_ORIGINALES:
        original[col] = "valor"
    enriquecido = original.iloc[::-1].drop(columns="_fila_original").reset_index(drop=True)
    enriquecido[TARGET] = [True, False]  # desalineación con conteo conservado
    return enriquecido, original


def test_reconciliacion_recupera_por_clave_no_por_indice(fuentes):
    enriquecido, original = fuentes
    etiquetas, info = reconciliar_eventos(enriquecido, original.iloc[::-1])
    assert etiquetas.tolist() == [False, True]
    assert info["discrepancias_antes"] == 2
    assert info["errores_inversion"] == 0
    assert info["correspondencias_unicas"] == 2


@pytest.mark.parametrize("lado", [0, 1])
def test_reconciliacion_rechaza_clave_duplicada(fuentes, lado):
    fuentes = list(fuentes)
    fuentes[lado] = pd.concat([fuentes[lado], fuentes[lado].iloc[[0]]])
    with pytest.raises(ValueError, match="duplicada"):
        reconciliar_eventos(*fuentes)


@pytest.mark.parametrize("lado", [0, 1])
def test_reconciliacion_rechaza_ausentes_y_adicionales(fuentes, lado):
    fuentes = list(fuentes)
    fuentes[lado] = fuentes[lado].iloc[:1]
    with pytest.raises(ValueError, match="incompleta"):
        reconciliar_eventos(*fuentes)


def test_reconciliacion_rechaza_atributos_distintos(fuentes):
    enriquecido, original = fuentes
    original.loc[0, "Country"] = "otro"
    with pytest.raises(ValueError, match="atributos originales"):
        reconciliar_eventos(enriquecido, original)


def test_reconciliacion_rechaza_target_original_nulo(fuentes):
    enriquecido, original = fuentes
    original = original.astype({TARGET: object})
    original.loc[0, TARGET] = None
    with pytest.raises(ValueError):
        reconciliar_eventos(enriquecido, original)


def test_csv_conserva_bytes_precision_nulos_comillas_y_orden():
    contenido = ('nombre,numero,ausente,Is Account Takeover\r\n'
                 '"Bogotá, CO",0.12345678901234567890,,True\r\n'
                 'Medellín,1.00000000000000000000,,False\r\n').encode("utf-8")
    resultado, info = preparar_csv_corregido(contenido, [False, True])
    esperado = contenido.replace(b',True\r\n', b',CAMBIO\r\n').replace(b',False\r\n', b',True\r\n').replace(b',CAMBIO\r\n', b',False\r\n')
    assert resultado == esperado
    assert info["etiquetas_modificadas"] == 2
    assert info["diferencias_features"] == 0
    assert info["nulos_preservados"]


def test_csv_rechaza_numero_incorrecto_de_etiquetas():
    with pytest.raises(ValueError, match="Dimensiones"):
        preparar_csv_corregido(b"x,Is Account Takeover\n1,True\n", [])


def test_csv_rechaza_registros_multilinea():
    with pytest.raises(ValueError, match="multilínea"):
        preparar_csv_corregido(b'x,Is Account Takeover\n"a\nb",True\n', [False])


def test_csv_identico_si_etiqueta_ya_correcta():
    contenido = b"x,Is Account Takeover\n1,True\n"
    resultado, info = preparar_csv_corregido(contenido, [True])
    assert contenido == resultado
    assert info["etiquetas_modificadas"] == 0
