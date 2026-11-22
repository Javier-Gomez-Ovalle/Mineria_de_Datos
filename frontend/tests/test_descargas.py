"""Contrasta las descargas públicas con el catálogo, nunca con datasets."""
import csv
import hashlib
import json
import unittest
from pathlib import Path

PUBLICO = Path(__file__).resolve().parents[1] / 'public'


class Descargas(unittest.TestCase):
    def test_equivalencia_e_integridad(self):
        catalogo = json.loads((PUBLICO/'contenido/catalogo.json').read_text(encoding='utf-8'))
        inventario = json.loads((PUBLICO/'descargas/inventario.json').read_text(encoding='utf-8'))
        grupos = {}
        for fila in catalogo['resultados']:
            grupos.setdefault(fila['protocolo']+'_'+fila['ambito'], []).append(fila['valores'])
        grupos['regresion_principal_y_sensibilidad'] = [dict(ajuste=k, **catalogo['metodos_numericos'][k]) for k in ['regresion','sensibilidad']]
        i = catalogo['metodos_numericos']['interpolacion']
        grupos['interpolacion_coeficientes_intervalo'] = [dict(coeficiente_constante=i['coeficientes_x_ascendentes'][0],coeficiente_lineal=i['coeficientes_x_ascendentes'][1],coeficiente_cuadratico=i['coeficientes_x_ascendentes'][2],minimo_km=i['intervalo_km'][0],maximo_km=i['intervalo_km'][1],error_maximo_nodos_kmh=i['error_maximo_nodos_kmh'])]
        self.assertEqual(len(inventario),15)
        self.assertEqual({x['archivo'] for x in inventario},{k+'.csv' for k in grupos})
        for entrada in inventario:
            with self.subTest(archivo=entrada['archivo']):
                datos=(PUBLICO/'descargas'/entrada['archivo']).read_bytes()
                self.assertEqual(len(datos),entrada['bytes'])
                self.assertEqual(hashlib.sha256(datos).hexdigest(),entrada['sha256'])
                filas=list(csv.DictReader(datos.decode('utf-8').splitlines()))
                esperadas=grupos[entrada['archivo'][:-4]]
                self.assertEqual(len(filas),len(esperadas))
                for real,esperada in zip(filas,esperadas):
                    self.assertEqual(real,{k:'' if esperada.get(k) is None else str(esperada[k]) for k in entrada['columnas']})


if __name__=='__main__': unittest.main()
