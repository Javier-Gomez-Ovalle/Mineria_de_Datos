"""Informe fiel a decisiones internas, sin elegir ganador a partir del exterior."""
from pathlib import Path
import json
import pandas as pd
from .auditoria import RESULTADOS,RAIZ,activar_guardia

def tabla(df):
    def fmt(v):
        if pd.isna(v):return 'No procede'
        return f'{v:.7g}' if isinstance(v,float) else str(v)
    return '| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(v) for v in fila)+' |' for fila in df.itertuples(index=False,name=None))

def leer(nombre):return pd.read_csv(RESULTADOS/f'{nombre}.csv',float_precision='round_trip')

def main():
    activar_guardia();g=leer('metricas_globales');f=leer('metricas_por_fold');s=leer('selecciones');d=leer('distribucion_folds');res=leer('resumen_folds');ti=leer('tiempos');es=leer('estabilidad');tr=leer('transferencia');c=json.loads((RESULTADOS/'configuracion_congelada.json').read_text(encoding='utf-8'));ej=json.loads((RESULTADOS/'ejecucion.json').read_text(encoding='utf-8'));catalogo=json.loads((RESULTADOS/'catalogo_graficas.json').read_text(encoding='utf-8'))
    empates=[]
    for k in range(1,6):
        decision=json.loads((RESULTADOS/f'decisiones_congeladas_{k}.json').read_text(encoding='utf-8'))
        for nombre,v in decision['decisiones'].items():empates.append(dict(fold=k,modelo=nombre,umbral=v['umbral'],umbrales_maximo_f1=str(v['umbrales_empatados']),variantes_maximo_f1=str(decision['selector']['variantes_empatadas'])))
    texto=f'''# Informe de validación anidada — Fase 4

Fecha: 2026-11-21. Diseño autorizado 5×3, seis variantes, F1 interno agrupado por evento, semilla 42. **No se entrenó modelo final ni se accedió a test.**

## 1. Dictamen

Se completaron 90 ajustes internos y 30 reajustes externos. Las cinco decisiones se guardaron antes de calcular cualquier métrica externa. El selector conjunto eligió árbol ponderado en el fold 1, KNN+ROS en 2, 4 y 5, y KNN baseline en 3. Sus decisiones externas detectaron **4 de 36 ATO**, omitieron **32** y produjeron **72 falsas alarmas**: precision 5,2632%, recall 11,1111%, F1 0,071429, 76 alertas (0,16413% de los eventos).

Esto no demuestra un ganador estable ni autoriza convertir la variante con mejor métrica externa en un ganador retrospectivo. El selector y los umbrales cambian entre folds. La validación anidada evalúa el procedimiento predefinido, no garantiza robustez con 34 usuarios positivos ni independencia respecto a la exploración histórica de estos mismos datos. No se declara terminada Fase 4.

## 2. Especificación, auditoría y fuentes

Especificación: [PROPUESTA_VALIDACION_ANIDADA_FASE04.md](PROPUESTA_VALIDACION_ANIDADA_FASE04.md), SHA-256 `{c['especificacion_sha256']}`. Se aplicaron las decisiones explícitas de la autorización: F1 agrupado, score >= umbral, desempate por distancia a 0,5 y luego mayor, y orden histórico entre variantes. No se colapsaron candidatos con decisiones equivalentes para evitar perder el desempate autorizado; se registraron todos los empates.

Train: 46.305 eventos, 1.600 usuarios, 36 eventos ATO de 34 usuarios. SHA-256 `{c['train_sha256']}`. Datos de entrenamiento: únicamente `dataset_train_fase04.csv`. Las lecturas de otros artefactos históricos en el registro de accesos son comprobaciones de integridad o referencias históricas; no se reutilizaron matrices ajustadas ni preprocesadores.

Se preservaron fábricas de modelos, selección de seis predictores y preprocesamiento específico de cada familia. Predictores: Device Type, Country, failed_attempts_15min, failed_attempts_1h, time_since_previous_login_hours y has_previous_login. IDs y etiqueta no están en X. Se mantuvieron exclusiones Impossible Travel y todos los hiperparámetros históricos. No se añadió calibración ni búsqueda de hiperparámetros.

La guardia de aperturas bloquea CSV/NPY/joblib de test antes de abrirlos. Test se excluye también del inventario: **no se abrió, inspeccionó, cargó ni calculó su hash o metadatos**. Se comprobaron {ej['historicos_intactos']} archivos históricos permitidos antes/después de ejecutar. La verificación final y hashes de entregables se guardan en `manifiesto_entrega.json`. No hubo instalaciones ni operaciones Git.

## 3. Particiones externas e internas

Se construye una tabla ordenada por User ID con max(ATO), se aplica StratifiedKFold con shuffle y semilla 42 a usuarios, y se expanden todos sus eventos. Cinco folds externos; dentro de cada entrenamiento externo se construye una tabla nueva y tres folds internos. Los índices internos son relativos a su población y se traducen explícitamente a evento_id global. Ningún usuario se comparte entre ajuste y validación en ninguno de los niveles; cada evento recibe una OOF interna dentro de cada población externa en que participa y una externa por variante.

{tabla(d)}

Las etiquetas externas se usaron para estratificación y conteos de la partición, nunca para seleccionar umbrales, variantes o desempates. Los folds de validación externa coinciden con CV2 por diseño, no por búsqueda de métricas favorables. No se modificó la semilla.

## 4. Ajuste, selección y congelación

Cada ajuste crea un preprocesador nuevo: mediana y categorías One-Hot aprendidas solo con ajuste; log1p según familia; StandardScaler en KNN. Se verifica que transform no modifica estado, medianas/categorías coincidan con filas autorizadas y matrices sean finitas. GaussianNB ponderado calcula sample_weight local; árbol ponderado conserva class_weight='balanced', calculado por sklearn con etiquetas locales. ROS solo se aplica a entrenamiento transformado, con índices verificados como remuestreo del subtrain, nunca a validaciones.

Para cada variante se concatenaron las OOF de sus tres validaciones internas. Se enumeraron scores únicos, referencia 0,5, política todos (umbral 0) y ninguno (siguiente float mayor que 1, registrado explícitamente). Las decisiones usan >=, incluidos empates. F1 se compara mediante la fracción exacta 2TP/(2TP+FP+FN), evitando falsas desigualdades de coma flotante. Entre máximos se elige el candidato más próximo a 0,5 y luego el mayor; entre variantes se usa el orden histórico. No se inventaron costes o restricciones FP/FN.

Cada `decisiones_congeladas_N.json` contiene umbrales, todos los empates y selector, con hash de OOF internas. Se escribe antes de los seis reajustes externos y se verifica que permanezca intacto. La función de ajuste recibe X/y de entrenamiento y solo X de validación. Las etiquetas externas se adjuntan al resultado después de congelar las decisiones de los cinco folds. Las métricas externas se calculan en un módulo posterior, sin correcciones de umbral.

```text
Por cada fold externo:
    construir tres particiones nuevas solo dentro de su entrenamiento
    generar seis OOF internas con preprocesamiento local
    elegir umbral por variante y variante del selector por F1 interno
    guardar decisiones y hashes inmutables
    reajustar seis variantes en entrenamiento externo
    guardar scores externos originales, decisiones aprendidas y a 0,5
Después de congelar los cinco folds:
    adjuntar etiquetas externas, auditar y evaluar
```

### Umbrales y selecciones reales

{tabla(s)}

### Empates registrados

{tabla(pd.DataFrame(empates))}

No hubo empates del máximo entre variantes en los cinco selectores conjuntos; sí entre umbrales en varias variantes. Las tablas de candidatos guardan también hashes de decisiones, permitiendo identificar equivalencias aunque los umbrales numéricos difieran.

## 5. Transferencia OOF interna → reajuste

El umbral interno se aplicó sin cambios al estimador reajustado con todo el entrenamiento externo. No se afirma que su escala o rendimiento se conserve: esa transferencia forma parte del procedimiento evaluado. Los scores externos originales se mantienen en `predicciones_externas.csv`; no se calibraron ni transformaron para mejorar resultados.

Todos los scores externos y decisiones a 0,5 reproducen CV2, dentro de tolerancia numérica 1e-12 relativa / 1e-15 absoluta para scores. Esto verifica que el cambio principal es el procedimiento de selección de umbral, no una alteración silenciosa del ajuste histórico. La comprobación se realizó después de congelar decisiones; CV2 no eligió umbrales.

`distribucion_scores_transferencia.csv` registra scores distintos, proporciones 0/1, media, mediana, percentil 99 y máximo internos/externos. `transferencia.csv` compara F1 interno elegido con resultado externo. Sus diferencias no aíslan causalmente transferencia de escala: también cambia población y tamaño de ajuste, y F1 interno es optimizado, por lo que no debe interpretarse como rendimiento independiente.

{tabla(tr[['fold_externo','modelo','umbral','f1_interno','f1','diferencia_f1_externo_interno']])}

## 6. Resultados completos agrupados por evento

Aprendido significa un umbral seleccionado por fold; no un único umbral global. Fijo_05 usa los mismos scores externos con umbral 0,5. La referencia del selector conserva las variantes seleccionadas internamente mediante F1 con umbral aprendido, pero aplica 0,5; **no es otro selector entrenado para elegir por F1 a 0,5**.

{tabla(g[['modelo','regla','TP','FP','TN','FN','precision','recall','f1','average_precision','alertas','porcentaje_alertas','sin_predicciones_positivas']])}

Precision=TP/(TP+FP); recall=TP/(TP+FN); F1=2TP/(2TP+FP+FN). Cuando no hay alertas se informa precision=0 por convención, acompañada por bandera explícita. AP se calcula a partir del ranking de scores y no cambia al modificar el umbral. La AP global de cada variante concatena scores de cinco estimadores, con escalas no necesariamente comparables; se conserva con esa limitación.

La AP global del selector se deja **sin calcular** porque combina familias distintas. No se trata el NaN del CSV como cero ni se ordena el selector mediante esa AP. Su AP se presenta solo por fold, con la familia correspondiente, y como media/DE descriptiva de esos valores locales.

## 7. Resultados individuales por fold

{tabla(f[['modelo','regla','fold_externo','TP','FP','TN','FN','precision','recall','f1','average_precision','alertas','porcentaje_alertas']])}

### Media no ponderada y DE descriptiva

{tabla(res[['modelo','regla','precision_mean','precision_std','recall_mean','recall_std','f1_mean','f1_std','average_precision_mean','average_precision_std']])}

La media por fold no pondera por eventos; las métricas globales agrupan todos los eventos. DE utiliza ddof=1. No son intervalos de confianza: los conjuntos de entrenamiento se solapan. El selector omite todos los ATO de los folds 2 y 3; su resultado agregado no oculta esos ceros.

## 8. Métricas por usuario y errores

Un usuario ATO es detectado cuando al menos uno de sus **eventos ATO** genera alerta. Omitido significa que ninguno de sus ATO se detecta, aunque pudiera tener una alerta falsa en otro evento. Usuarios sin ATO con alerta se refiere a usuarios cuyos eventos son todos negativos. Usuarios con FP incluye también usuarios ATO que sufren falsas alarmas en eventos negativos; son conceptos diferentes.

{tabla(g[['modelo','regla','usuarios','usuarios_ato','usuarios_ato_detectados','usuarios_ato_omitidos','usuarios_sin_ato_con_alerta','usuarios_con_fp']])}

Los detalles de FP/FN por evento, usuario, fold, variante y regla están en `errores_externos.csv`. Predicciones completas permiten reconstruir cualquier confusión sin volver a entrenar. Los IDs se conservan como enteros; no se agregan métricas de usuario a los conteos de eventos.

## 9. Estabilidad e interpretación de las seis variantes

{tabla(es)}

- **Árbol baseline:** 0,25 en tres folds y 0,5 en dos. Conserva 3 TP externos, con 64 FP frente a 61 a 0,5; no hay beneficio global en detección.
- **Árbol ponderado:** umbrales próximos a 1, incluido 1 en un fold. Reduce FP de 675 a 54, pero TP cae de 9 a 5. F1 externo mayor no lo convierte retrospectivamente en ganador independiente del selector. Pequeñas diferencias numéricas de umbral pueden atravesar bloques grandes de scores de hojas.
- **GaussianNB baseline y ponderado:** ambos eligen todos en el fold 2 y 0,5 en los restantes. Esa política maximiza F1 interno en ese fold, aunque su valor absoluto sea muy bajo. En el exterior añade falsas alarmas sin aumentar los 31 TP agregados. Las dos variantes siguen visibles; no se corrige una decisión válida por ser desfavorable. Es evidencia de las limitaciones de optimizar F1 bajo scores poco discriminativos, no un fallo de la regla.
- **KNN baseline:** elige 0,2 en cuatro folds y 0,4 en uno. Obtiene 6 TP y 122 FP; la referencia 0,5 tiene cero TP y un FP. No se conserva un 0,4 universal por el buen aspecto de su exploración anterior.
- **KNN + ROS:** umbrales 0,4 u 0,8. Se elige en tres folds, pero su resultado global con umbral aprendido es 5 TP y 104 FP, frente a 5 TP y 99 FP a 0,5. Ser seleccionado más veces no demuestra superioridad.

El selector mejora F1 frente a su propia referencia 0,5 (0,07143 vs 0,04184), reduce FP (72 vs 198) y pierde una detección (4 vs 5). Es un compromiso observado, no una mejora universal ni evidencia de un coste FP/FN que el usuario no haya fijado. No se utilizaron estos resultados para cambiar variantes, criterios o umbrales.

## 10. Coste, contratos y reproducibilidad

Tiempo de ejecución registrado para la fase experimental: {ej['segundos']:.2f} s, con 120 ajustes y escritura de artefactos; excluye pruebas, gráficos y elaboración de este informe. RSS máximo muestreado al cerrar folds: {ej['rss_observado_bytes']/1048576:.2f} MiB, no un pico continuo medido. Dos hilos, lotes de predicción de 512 y working_memory=256 MiB.

{tabla(ti)}

Versiones: `{json.dumps(c['versiones'])}`. La reproducción exige estas versiones, datos y orden de filas; tiempos no deterministas. No se guardó un modelo final entrenado con todo train.

Arquitectura en `fase04_modelado/validacion_anidada/`: `particiones.py`, `oof_internas.py`, `seleccion_umbral.py`, `seleccion_variante.py`, `ajuste.py`, `ejecutar.py`, `evaluacion.py`, `diagnosticos.py`, `auditoria.py`, `graficas.py`, `informe.py` y `verificar_entrega.py`. Clases AjustadorVariante y ExportadorFiguras separan responsabilidades; funciones snake_case. Se reutiliza código histórico en lectura, sin refactorización general.

Orden para reproducir en un destino nuevo: `python -B -m fase04_modelado.validacion_anidada.ejecutar`, luego módulos `evaluacion`, `diagnosticos`, `graficas`, pruebas y `informe`. Las rutas actuales rechazan sobrescritura. No borrar artefactos históricos para repetir una ejecución. Test permanece bloqueado.

## 11. Pruebas y auditoría de entrega

Resultado real final: **20/20 pruebas aprobadas en 12,28 segundos**. La primera pasada, anterior a añadir las comprobaciones gráficas, aprobó 18/18 en 12,69 segundos. No hubo fallos ni se repitió el experimento completo.

El registro real está en `fase04_modelado/validacion_anidada/resultados/pruebas.txt`. Comando: `python -B -m pytest -p no:cacheprovider -q fase04_modelado/validacion_anidada/tests`.

Se comprueban separación en ambos niveles, reproducción de particiones, cobertura interna/externa, correspondencia de claves y etiquetas, predictores permitidos, estadísticas de preprocesamiento local, índices de ajuste, ROS local, pesos locales, reglas >=, desempates, métricas sin alertas, invariancia de selección al alterar etiquetas externas manteniendo splits, integridad histórica, bloqueo efectivo de aperturas de test y gráficos PNG/SVG. La prueba de invariancia usa un doble determinista de ajuste para aislar la frontera de selección; los artefactos reales se verifican por separado. Cada ejecución de pruebas realiza seis ajustes pequeños, uno por variante: se ejecutaron dos pasadas, doce ajustes pequeños en total, distintos de los 120 experimentales; ninguno usa todo train ni test.

La verificación independiente de los registros se apoya en hashes, reconstrucción de índices y estadísticas; no constituye una auditoría de un tercero. La capa de integridad no toca test, ni siquiera sus metadatos. Los intentos de apertura en la prueba de bloqueo se rechazan antes del acceso al archivo.

## 12. Figuras y archivos

13 figuras, cada una PNG a 300 DPI y SVG. Siete figuras contienen las 14 matrices absolutas de seis variantes y selector frente a la referencia. Se conservan curvas/visualizaciones históricas sin sobrescribirlas.

'''
    for item in catalogo:texto+=f'- [{item["nombre"]} · PNG]({item["png"]}) / [SVG]({item["svg"]}): {item["descripcion"]}\n'
    texto+='''
Artefactos en `fase04_modelado/validacion_anidada/resultados/`: configuración congelada; particiones y distribución; cinco OOF internas y tablas de candidatos; cinco decisiones congeladas; predicciones externas completas y selector; auditoría de 120 ajustes; métricas globales/por fold y resumen; errores; estabilidad y transferencia; tiempos; comparación de referencia CV2; catálogo de figuras; pruebas y manifiesto final. Los hashes de fuentes permitidas anteriores están en `inventario_previo.json`; los de entregables en `manifiesto_entrega.json`.

## 13. Limitaciones y cierre

Solo 36 ATO de 34 usuarios: un acierto cambia recall global 2,78 puntos porcentuales. La estratificación mejora soporte por fold, no crea evidencia independiente. Eventos de un usuario pueden estar correlacionados; los folds de ajuste se solapan. Tres folds internos dejan unos 18–19 usuarios positivos por ajuste interno. El umbral optimizado en OOF de modelos pequeños puede comportarse distinto al reajustar; el resultado externo incluye ese efecto y la variabilidad poblacional.

Los datos y resultados CV1/CV2 ya habían sido explorados. Este procedimiento congelado reduce fuga directa de la selección interna, pero no borra la adaptación histórica del diseño. F1 fue una decisión académica autorizada, no una equivalencia económica FP/FN ni una garantía de alta detección. La muestra y geografía sintéticas, seis predictores limitados y ausencia de validación temporal restringen extrapolación.

No se elige retrospectivamente al árbol ponderado por su F1 externo ni a KNN+ROS por frecuencia de selección. El resultado del selector es la evidencia del procedimiento autorizado y su cobertura de ATO es baja. El dictamen es **selección inestable y evidencia insuficiente para declarar un ganador definitivo o un umbral universal**. Una siguiente decisión necesita valorar este compromiso y la suficiencia estadística; no se añade una nueva optimización silenciosa.

KMeans y Ward permanecen documentados por separado en [INFORME_CLUSTERING_FASE04.md](INFORME_CLUSTERING_FASE04.md). No participan en selección supervisada ni se convierten en etiquetas de ataque. Se conserva la entrega académica de cinco algoritmos y todas las variantes de CV1/CV2.

**Test permaneció cerrado. No se entrenó un modelo final con todo train, no hubo operaciones Git ni cambios históricos. Fase 4 no está terminada.**
'''
    with Path('INFORME_VALIDACION_ANIDADA_FASE04.md').open('x',encoding='utf-8') as archivo:archivo.write(texto)

if __name__=='__main__':main()
