import io
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
from fase04_preparacion.seleccion import seleccionar_predictores, separar_datos, TARGET, NUMERICAS
from fase04_preparacion.transformaciones import crear_preprocesador, ajustar_train, transformar, REPRESENTACIONES
from fase04_preparacion.ejecutar import ejecutar


def datos():
    return pd.DataFrame({
        'User ID': [1, 1, 2, 2], 'Login Timestamp': ['a', 'b', 'c', 'd'],
        'IP Address': ['ip'] * 4, TARGET: [False, True, False, False],
        'Device Type': ['desktop', 'mobile', 'desktop', 'desktop'],
        'Country': ['NO', 'US', 'NO', 'NO'],
        'failed_attempts_15min': [0., 1., 0., 2.],
        'failed_attempts_1h': [0., 2., 0., 3.],
        'time_since_previous_login_hours': [np.nan, 2., np.nan, 4.],
        'has_previous_login': [0, 1, 0, 1],
    })


@pytest.mark.parametrize('nombre', REPRESENTACIONES)
def test_target_identidad_y_orden_no_afectan_predictores(nombre):
    d = datos()
    x, y, claves = separar_datos(d)
    cambiado = d.copy()
    cambiado[TARGET] = ~cambiado[TARGET]
    cambiado['User ID'] = [100, 100, 200, 200]
    cambiado['IP Address'] = 'otro'
    cambiado['Is Attack IP'] = True
    otro = seleccionar_predictores(cambiado)
    pd.testing.assert_frame_equal(x, otro)
    a = ajustar_train(crear_preprocesador(nombre), x)
    b = ajustar_train(crear_preprocesador(nombre), otro)
    np.testing.assert_array_equal(a, b)
    assert TARGET not in x and 'User ID' not in x
    assert y.tolist() == [0, 1, 0, 0]
    assert claves['Login Timestamp'].tolist() == ['a', 'b', 'c', 'd']


@pytest.mark.parametrize('nombre', REPRESENTACIONES)
def test_test_extremo_y_categoria_nueva_no_aprenden(nombre):
    x = seleccionar_predictores(datos())
    p = crear_preprocesador(nombre)
    ajustar_train(p, x)
    antes = joblib.hash(p)
    t = x.iloc[[1]].copy()
    t['Country'] = 'NUNCA_VISTO'
    t[NUMERICAS] = 1e8
    resultado = transformar(p, t)
    assert joblib.hash(p) == antes
    encoder = p.named_transformers_['cat'].named_steps['onehot']
    assert 'NUNCA_VISTO' not in encoder.categories_[1]
    columnas = p.get_feature_names_out()
    assert (resultado[:, [i for i, c in enumerate(columnas) if c.startswith('cat__Country_')]] == 0).all()
    np.testing.assert_allclose(p.named_transformers_['num'].named_steps['imputar'].statistics_, [0.5, 1., 3.])
    if nombre == 'distancias':
        esperado = np.array([[0,0,3],[1,2,2],[0,0,3],[2,3,4]])
        np.testing.assert_allclose(p.named_transformers_['num'].named_steps['escalar'].mean_, np.log1p(esperado).mean(axis=0))


@pytest.mark.parametrize('nombre', REPRESENTACIONES)
def test_ausencias_serializacion_y_reordenamiento(nombre):
    x = seleccionar_predictores(datos())
    x.loc[0, 'Country'] = np.nan
    p = crear_preprocesador(nombre)
    a = ajustar_train(p, x)
    assert np.isfinite(a).all()
    assert 'Desconocido' in p.named_transformers_['cat'].named_steps['onehot'].categories_[1]
    buffer = io.BytesIO()
    joblib.dump(p, buffer)
    buffer.seek(0)
    np.testing.assert_array_equal(transformar(joblib.load(buffer), x), a)
    np.testing.assert_array_equal(transformar(p, x.iloc[::-1]), a[::-1])


def test_controles_bloqueantes():
    d = datos()
    d[TARGET] = d[TARGET].astype(object)
    d.loc[0, TARGET] = None
    with pytest.raises(ValueError, match='Target'):
        separar_datos(d)
    d = datos()
    d.loc[0, 'time_since_previous_login_hours'] = 0
    with pytest.raises(ValueError, match='historial'):
        seleccionar_predictores(d)
    d = datos()
    d.loc[0, 'failed_attempts_1h'] = -1
    with pytest.raises(ValueError, match='Magnitud'):
        seleccionar_predictores(d)
    with pytest.raises(FileExistsError):
        ejecutar(salida=Path(__file__).parent)


def test_artefactos_reales_si_existen():
    raiz = Path(__file__).resolve().parents[2]
    salida = raiz / 'artefactos_preprocesamiento_fase04'
    if not salida.exists():
        pytest.skip('Ejecutar primero la generacion para esta prueba de integracion')
    for s, filas, positivos in [('train', 46305, 36), ('test', 11115, 9)]:
        d = pd.read_csv(raiz / f'dataset_{s}_fase04.csv')
        x, y, claves = separar_datos(d)
        np.testing.assert_array_equal(np.load(salida / f'y_{s}_fase04.npy'), y)
        assert y.sum() == positivos
        trazas = pd.read_csv(salida / f'trazabilidad_{s}_fase04.csv')
        pd.testing.assert_frame_equal(trazas.drop(columns='fila_matriz'), claves)
        np.testing.assert_array_equal(trazas['fila_matriz'], np.arange(filas))
        for nombre in REPRESENTACIONES:
            p = joblib.load(salida / f'preprocesador_{nombre}_fase04.joblib')
            guardado = np.load(salida / f'X_{s}_{nombre}_fase04.npy')
            np.testing.assert_array_equal(guardado, transformar(p, x))
            assert guardado.shape == (filas, len(p.get_feature_names_out()))
