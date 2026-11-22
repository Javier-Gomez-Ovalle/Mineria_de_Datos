"""Carga de predictores sin target; trazabilidad separada."""
import numpy as np
import pandas as pd
from fase04_preparacion.seleccion import PREDICTORES, CLAVE, seleccionar_predictores
from fase04_preparacion.transformaciones import crear_preprocesador, ajustar_train

class PreparadorDatos:
    def __init__(self, origen='dataset_train_fase04.csv'):
        self.origen = origen

    def cargar(self):
        self.x = seleccionar_predictores(pd.read_csv(self.origen, usecols=PREDICTORES))
        self.claves = pd.read_csv(self.origen, usecols=CLAVE)
        assert not self.claves.duplicated(CLAVE).any()
        self.preprocesador = crear_preprocesador('distancias')
        self.matriz = ajustar_train(self.preprocesador, self.x)
        historica = np.load('artefactos_preprocesamiento_fase04/X_train_distancias_fase04.npy')
        np.testing.assert_array_equal(self.matriz, historica)
        return self
