"""Extracción documental explícita. Nunca importa pipelines ni abre datasets."""
from pathlib import Path
import csv
import hashlib
import json
import math
import re
import struct

RAIZ = Path(__file__).resolve().parents[2]
FRONTEND = RAIZ / 'frontend'
FINAL = 'fase04_modelado/evaluacion_final_test_20261122/INFORME_EVALUACION_FINAL_TEST_FASE04.md'
NUMERICOS = 'fase04_metodos_numericos/resultados/resultados.json'
SENSIBILIDAD = 'fase04_metodos_numericos/revision_complementaria/resultados_sensibilidad.json'
REFERENCIA = 'fase04_modelado/recuperacion_referencia_v1_20261122/MANIFIESTO_MODELO_FINAL.json'
CONFIG = json.loads((FRONTEND / 'scripts/fuentes_permitidas.json').read_text(encoding='utf-8'))
FIGURAS = json.loads((FRONTEND / 'scripts/figuras_permitidas.json').read_text(encoding='utf-8'))
DOCUMENTACION = json.loads((FRONTEND / 'contenido/documentacion.json').read_text(encoding='utf-8'))
PERMITIDAS = frozenset([x['ruta'] for x in CONFIG] + [FINAL, NUMERICOS, SENSIBILIDAD, REFERENCIA,
    'frontend/contenido/narrativa.json', 'Fase-1-y-2-MINERIA-DE-DATOS.pdf',
    'frontend/contenido/documentacion.json'] + [x['fuente'] for x in FIGURAS] +
    [p for d in DOCUMENTACION for p in d['fuentes']])


def leer(ruta):
    if ruta not in PERMITIDAS:
        raise ValueError('Fuente no autorizada: ' + ruta)
    return (RAIZ / ruta).read_bytes()


def numero(valor):
    n = float(valor)
    if not math.isfinite(n):
        raise ValueError('Valor no finito')
    return n


def construir_catalogo():
    registros = []
    fuentes = {}
    def obtener(ruta):
        datos = leer(ruta)
        fuentes[ruta] = hashlib.sha256(datos).hexdigest()
        return datos.decode('utf-8-sig')
    for fuente in CONFIG:
        for fila, original in enumerate(csv.DictReader(obtener(fuente['ruta']).splitlines()), 2):
            valores = {}
            for campo in fuente['campos']:
                valor = original.get(campo, '')
                if valor != '':
                    valores[campo.lower()] = valor if campo in ('modelo', 'regla', 'algoritmo') else numero(valor)
            registros.append({'protocolo': fuente['protocolo'], 'ambito': fuente['ambito'],
                              'fuente': fuente['ruta'], 'fila_agregada': fila, 'valores': valores})
    informe = obtener(FINAL).replace('\r\n', '\n')
    claves = ['TP','FP','TN','FN','precision','recall','f1','average_precision','roc_auc','f2','especificidad','FPR','alertas']
    final = {}
    for clave in claves:
        coincidencias = re.findall(r'^\| '+re.escape(clave)+r' \| ([0-9.eE+-]+) \|$', informe, re.M)
        if len(coincidencias) != 1:
            raise ValueError('Métrica final ausente/ambigua: '+clave)
        final[clave.lower()] = numero(coincidencias[0])
    registros.append({'protocolo':'evaluacion_final_documentada','ambito':'test_documentado',
                      'fuente':FINAL,'fila_agregada':0,'valores':final})
    referencia = json.loads(obtener(REFERENCIA))
    seleccion = {k.lower(): referencia['metricas_oof_historicas_no_recalculadas'][k]
                 for k in ['TP','FP','TN','FN','precision','recall','f1','average_precision']}
    seleccion['umbral'] = referencia['umbral']
    seleccion['modelo'] = 'arbol_ponderado'
    registros.append({'protocolo':'seleccion_referencia','ambito':'seleccion_oof',
                      'fuente':REFERENCIA,'fila_agregada':0,'valores':seleccion})
    principal = json.loads(obtener(NUMERICOS))
    sensibilidad = json.loads(obtener(SENSIBILIDAD))
    campos = ['n','pendiente','intercepto','correlacion','r2','mse','rmse']
    numericos = {
        'regresion': {k: principal['regresion'][k] for k in campos},
        'sensibilidad': {k: sensibilidad['diagnostico_distancia_positiva'][k] for k in campos},
        'interpolacion': {k: principal['interpolacion'][k] for k in ['coeficientes_x_ascendentes','intervalo_km','error_maximo_nodos_kmh']},
        'pares_cero': principal['auditoria']['pares_cero'],
        'fuente_principal':NUMERICOS,'fuente_sensibilidad':SENSIBILIDAD,
        'unidades': {'x':'km','y':'km/h','pendiente':'h^-1','intercepto':'km/h','mse':'(km/h)^2','rmse':'km/h','r2':'adimensional','correlacion':'adimensional'}}
    narrativa = json.loads(obtener('frontend/contenido/narrativa.json'))
    if hashlib.sha256(leer(narrativa['fuente'])).hexdigest() != narrativa['sha256']:
        raise ValueError('La fuente original de objetivos ha cambiado')
    documentacion = json.loads(obtener('frontend/contenido/documentacion.json'))
    for bloque in documentacion:
        for ruta in bloque['fuentes']:
            fuentes[ruta] = hashlib.sha256(leer(ruta)).hexdigest()
    figuras = []
    for figura in FIGURAS:
        datos = leer(figura['fuente'])
        if datos[:8] != b'\x89PNG\r\n\x1a\n':
            raise ValueError('Figura PNG inválida')
        ancho, alto = struct.unpack('>II', datos[16:24])
        fuentes[figura['fuente']] = hashlib.sha256(datos).hexdigest()
        figuras.append({**figura, 'url':'figuras/'+figura['id']+'.png', 'ancho':ancho, 'alto':alto})
    return {'version_esquema':1,'narrativa':narrativa,'resultados':registros,'metodos_numericos':numericos,
            'documentacion':documentacion, 'figuras':figuras,
            'fuentes':fuentes,'advertencias':[
                'AP es Average Precision, no accuracy. Métricas de clasificación en escala 0–1; conteos en eventos. Duraciones en la unidad de cada variable: horas para intervalos entre accesos y segundos para cómputo.',
                'OOF global no es media por fold. AP global concatena scores de estimadores distintos.',
                'AP ausente en selectores globales se conserva ausente, nunca se interpreta como cero.',
                'El F1 OOF de selección del umbral no estima rendimiento independiente; probabilidades de tres árboles no necesariamente equivalentes al ajuste final.',
                'Clustering es exploratorio. KMeans: train completo; Ward: submuestra de 4000.',
                'Evaluación final transcrita de informe cerrado; no se accede al dataset test.',
                'Regresión descriptiva sin causalidad; sensibilidad separada. Interpolación únicamente dentro del intervalo.',
                'No hay garantía productiva ni ganador universal entre protocolos.']}


def serializar(catalogo):
    return json.dumps(catalogo, ensure_ascii=False, indent=2, allow_nan=False)+'\n'


if __name__ == '__main__':
    catalogo = construir_catalogo()
    (FRONTEND / 'public/figuras').mkdir(exist_ok=True)
    for figura in catalogo['figuras']:
        (FRONTEND / 'public' / figura['url']).write_bytes(leer(figura['fuente']))
    destino = FRONTEND / 'public/contenido/catalogo.json'
    destino.write_text(serializar(catalogo), encoding='utf-8')
    print('Catálogo agregado preparado:', destino)
