"""Solo fuentes agregadas autorizadas; ninguna lectura de datasets."""
import csv
import hashlib
import importlib.util
import json
import re
import struct
import zlib
from pathlib import Path
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/preparar_contenido.py'
spec = importlib.util.spec_from_file_location('contenido', SCRIPT)
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)


class ContratosContenido(unittest.TestCase):
    def test_figuras_identidad_integridad_png_y_etiquetado(self):
        catalogo=modulo.construir_catalogo()
        figuras=catalogo['figuras']
        self.assertEqual(len(figuras),58)
        for campo in ['id','url','fuente']:
            self.assertEqual(len({f[campo] for f in figuras}),58)
        hashes=set()
        carpetas={'cv1':'fase04_modelado/resultados/', 'cv2':'fase04_modelado/resultados_cv_usuario/',
          'anidada':'fase04_modelado/validacion_anidada/', 'extension_rf':'fase04_modelado/mejora_controlada/',
          'clustering':'fase04_clustering/', 'numericos':'fase04_metodos_numericos/'}
        for f in figuras:
            original=modulo.leer(f['fuente'])
            publico=(modulo.FRONTEND/'public'/f['url']).read_bytes()
            self.assertEqual(original,publico)
            self.assertEqual(publico,(modulo.FRONTEND/'dist'/f['url']).read_bytes())
            sha=hashlib.sha256(publico).hexdigest()
            self.assertNotIn(sha,hashes);hashes.add(sha)
            self.assertEqual(sha,catalogo['fuentes'][f['fuente']])
            self.assertTrue(f['fuente'].startswith(carpetas[f['protocolo']]))
            self.assertEqual(struct.unpack('>II',publico[16:24]),(f['ancho'],f['alto']))
            posicion=8
            tipos=[]
            while posicion<len(publico):
                longitud=struct.unpack('>I',publico[posicion:posicion+4])[0]
                bloque=publico[posicion+4:posicion+8+longitud]
                crc=struct.unpack('>I',publico[posicion+8+longitud:posicion+12+longitud])[0]
                self.assertEqual(zlib.crc32(bloque)&0xffffffff,crc)
                tipos.append(bloque[:4]);posicion+=longitud+12
            self.assertEqual(tipos[0],b'IHDR');self.assertEqual(tipos[-1],b'IEND')
            if 'confusion_' in f['id']: self.assertIn(f['modelo'],f['fuente'])
            if f['protocolo']=='extension_rf': self.assertEqual(f['regla'],'aprendido')

    def test_superficie_publica_solo_catalogo_y_figuras(self):
        c=modulo.construir_catalogo()
        esperados={'contenido/catalogo.json'}|{f['url'] for f in c['figuras']}
        inventario=json.loads((modulo.FRONTEND/'public/descargas/inventario.json').read_text(encoding='utf-8'))
        esperados|={'recursos.html','descargas/inventario.json'}|{'descargas/'+f['archivo'] for f in inventario}
        presentacion=modulo.FRONTEND/'public/presentacion/ATO_PRESENTACION_ACADEMICA.pptx'
        if presentacion.exists(): esperados.add('presentacion/ATO_PRESENTACION_ACADEMICA.pptx')
        reales={p.relative_to(modulo.FRONTEND/'public').as_posix() for p in (modulo.FRONTEND/'public').rglob('*') if p.is_file()}
        self.assertEqual(reales,esperados)
        for r in c['resultados']:
            self.assertIn(r['ambito'],['oof_global','fold','candidatos','evaluacion_externa_kmeans_2','evaluacion_externa_ward_2','test_documentado','seleccion_oof'])
        self.assertIsNone(re.search(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])',json.dumps(c,ensure_ascii=False)))

    def test_guion_doce_diapositivas_nueve_minutos(self):
        texto=(modulo.RAIZ/'docs/GUIÓN_PRESENTACION_ACADEMICA.md').read_text(encoding='utf-8')
        self.assertEqual(re.findall(r'^## (\d+)\.',texto,re.M),[str(i) for i in range(1,13)])
        tiempos=re.findall(r'^\| \d+\..*?\|.*?\| (\d+) \|',texto,re.M)
        self.assertEqual(len(tiempos),12)
        self.assertEqual(sum(map(int,tiempos)),540)
        objetivos=json.loads(modulo.leer('frontend/contenido/narrativa.json'))
        for objetivo in [objetivos['objetivo_general'],*objetivos['objetivos_especificos']]:
            self.assertIn(objetivo,texto)

    def test_equivalencia_cada_celda_csv(self):
        catalogo = modulo.construir_catalogo()
        for fuente in modulo.CONFIG:
            filas = list(csv.DictReader(modulo.leer(fuente['ruta']).decode('utf-8-sig').splitlines()))
            exportadas = [x for x in catalogo['resultados'] if x['fuente'] == fuente['ruta']]
            self.assertEqual(len(filas), len(exportadas))
            for original, publica in zip(filas, exportadas):
                for campo in fuente['campos']:
                    if original.get(campo, '') != '':
                        esperado = original[campo] if campo in ('modelo','regla','algoritmo') else float(original[campo])
                        self.assertEqual(esperado, publica['valores'][campo.lower()])

    def test_cifras_documentadas_y_separacion(self):
        c = modulo.construir_catalogo()
        final = [r for r in c['resultados'] if r['ambito']=='test_documentado']
        self.assertEqual(len(final),1)
        self.assertEqual([final[0]['valores'][k] for k in ['tp','fp','tn','fn']], [1,12,11094,8])
        self.assertEqual(c['metodos_numericos']['regresion']['n'],5662)
        self.assertEqual(c['metodos_numericos']['sensibilidad']['n'],29)
        referencia=json.loads(modulo.leer(modulo.REFERENCIA))
        seleccion=next(r['valores'] for r in c['resultados'] if r['protocolo']=='seleccion_referencia')
        self.assertEqual(seleccion['umbral'],referencia['umbral'])
        for k in ['TP','FP','TN','FN','precision','recall','f1','average_precision']:
            self.assertEqual(seleccion[k.lower()],referencia['metricas_oof_historicas_no_recalculadas'][k])
        for protocolo, cantidad in [('cv1',6),('cv2',6),('anidada',14),('extension_rf',18)]:
            self.assertEqual(sum(r['protocolo']==protocolo and r['ambito']=='oof_global' for r in c['resultados']),cantidad)
        a=json.loads(modulo.leer(modulo.NUMERICOS))
        b=json.loads(modulo.leer(modulo.SENSIBILIDAD))
        for k,v in c['metodos_numericos']['regresion'].items(): self.assertEqual(v,a['regresion'][k])
        for k,v in c['metodos_numericos']['sensibilidad'].items(): self.assertEqual(v,b['diagnostico_distancia_positiva'][k])
        for k,v in c['metodos_numericos']['interpolacion'].items(): self.assertEqual(v,a['interpolacion'][k])

    def test_integridad_determinismo_y_catalogo_actual(self):
        antes={p:hashlib.sha256(modulo.leer(p)).hexdigest() for p in modulo.PERMITIDAS}
        a=modulo.serializar(modulo.construir_catalogo())
        self.assertEqual(a,modulo.serializar(modulo.construir_catalogo()))
        self.assertEqual(a,(modulo.FRONTEND/'public/contenido/catalogo.json').read_text(encoding='utf-8'))
        self.assertEqual(antes,{p:hashlib.sha256(modulo.leer(p)).hexdigest() for p in modulo.PERMITIDAS})

    def test_guardia_lecturas(self):
        original=Path.read_bytes
        accesos=[]
        def vigilada(p):
            relativo=p.relative_to(modulo.RAIZ).as_posix()
            self.assertIn(relativo,modulo.PERMITIDAS)
            accesos.append(relativo)
            return original(p)
        with patch.object(Path,'read_bytes',vigilada): modulo.construir_catalogo()
        self.assertTrue(accesos)
        with self.assertRaises(ValueError): modulo.leer('dataset_test_fase04.csv')
        with self.assertRaises(ValueError): modulo.leer('../otro.csv')

    def test_no_exporta_identificadores_ni_arrays_individuales(self):
        c=modulo.construir_catalogo()
        prohibidas={'user_id','ip_address','login_timestamp','fila_train_0','puntos','predicciones','sha256_train'}
        def revisar(x):
            if isinstance(x,dict):
                self.assertFalse(prohibidas.intersection(x))
                for v in x.values(): revisar(v)
            elif isinstance(x,list):
                for v in x: revisar(v)
        revisar(c)
        for valor in ['NaN','Infinity','-Infinity']:
            with self.assertRaises(ValueError): modulo.numero(valor)


if __name__=='__main__': unittest.main()
