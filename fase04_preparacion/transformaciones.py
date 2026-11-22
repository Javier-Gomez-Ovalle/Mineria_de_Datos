"""Fabricas de transformadores sin estado compartido ni acceso a etiquetas."""
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from .seleccion import NUMERICAS, CATEGORICAS, BINARIAS

REPRESENTACIONES = ('arbol', 'gaussian_nb', 'distancias')


def crear_preprocesador(representacion):
    if representacion not in REPRESENTACIONES:
        raise ValueError(f'Representacion desconocida: {representacion}')
    pasos = [('imputar', SimpleImputer(strategy='median', keep_empty_features=True))]
    if representacion != 'arbol':
        pasos.append(('log1p', FunctionTransformer(np.log1p, feature_names_out='one-to-one')))
    if representacion == 'distancias':
        pasos.append(('escalar', StandardScaler()))
    categorias = Pipeline([
        ('imputar', SimpleImputer(strategy='constant', fill_value='Desconocido')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
    ])
    return ColumnTransformer([
        ('num', Pipeline(pasos), NUMERICAS),
        ('bin', 'passthrough', BINARIAS),
        ('cat', categorias, CATEGORICAS),
    ], remainder='drop', verbose_feature_names_out=True)


def ajustar_train(preprocesador, x_train):
    """La API de ajuste no acepta test ni etiquetas."""
    if x_train[NUMERICAS].notna().sum().eq(0).any():
        raise ValueError('No es posible aprender una mediana sin observaciones')
    resultado = preprocesador.fit_transform(x_train)
    validar_matriz(resultado, len(x_train))
    return resultado


def transformar(preprocesador, x):
    resultado = preprocesador.transform(x)
    validar_matriz(resultado, len(x))
    return resultado


def validar_matriz(matriz, filas):
    if matriz.ndim != 2 or matriz.shape[0] != filas or not np.isfinite(matriz).all():
        raise ValueError('Matriz transformada invalida')
