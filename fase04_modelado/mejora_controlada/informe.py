"""Informe de decisión construido desde resultados, sin selección retrospectiva."""
import json
import pandas as pd
from .contratos import *
from .diagnostico import tabla

def main():
    activar_guardia();n=verificar_integridad()
    gm=pd.read_csv(OUT/'comparacion_global.csv');fm=pd.read_csv(OUT/'metricas_por_fold.csv');sm=pd.read_csv(OUT/'resumen_folds.csv');run=json.loads((OUT/'ejecucion.json').read_text(encoding='utf-8'))
    a=pd.DataFrame(json.loads((OUT/'auditoria_ajustes.json').read_text(encoding='utf-8')))
    costs=a.groupby('nivel')[['preprocesamiento_s','entrenamiento_s','prediccion_s']].sum().reset_index();csv_nuevo(OUT/'tiempos.csv',costs)
    details=[]
    for f in range(1,6):
        d=json.loads((OUT/f'decision_congelada_{f}.json').read_text(encoding='utf-8'));config=CONFIGS[d['elegida']];external=fm[(fm.modelo=='random_forest')&(fm.regla=='aprendido')&(fm.fold==f)].iloc[0]
        details.append(dict(fold=f,configuracion=d['elegida'],max_depth=str(config['max_depth']),min_samples_leaf=config['min_samples_leaf'],umbral=d['umbral'],f1_interno=d['configuraciones'][d['elegida']]['f1'],f1_externo=external.f1,selector=d['selector_ampliado']))
    details=pd.DataFrame(details);csv_nuevo(OUT/'transferencia_seleccion.csv',details)
    refs=pd.read_csv(OUT/'referencias_cv1_cv2.csv');cat=json.loads((OUT/'catalogo_graficas.json').read_text(encoding='utf-8'))
    root='fase04_modelado/mejora_controlada/resultados/'
    figure_text='\n'.join(f"- [{v['archivo']}]({root+v['archivo']}): {v['descripcion']} SVG en `{root+v['vector']}`." for v in cat)
    report='''# Decisión de modelado — Fase 4

Fecha: 2026-11-21. **Escenario B: no se recomienda un modelo como detector suficientemente respaldado.** La conclusión se limita a estos predictores, muestra y procedimientos evaluados; no demuestra que ningún algoritmo pueda resolver ATO. Fase 4 continúa abierta y test permanece cerrado.

## Qué se probó y qué se preservó

La auditoría y el diagnóstico precedieron a los ajustes nuevos. Se evaluó una sola familia adicional: Random Forest ponderado, cuatro configuraciones de profundidad/hoja, 100 árboles, semilla 42. Se ejecutaron 60 ajustes internos y cinco externos en las particiones anidadas históricas. Se reutilizaron las OOF internas/externas históricas tras verificar hashes y correspondencia; no se repitieron los 120 ajustes anteriores. La selección conjunta de configuración y umbral usa exclusivamente los internos. La propuesta y configuración se guardaron antes de ajustar.

La oportunidad era reducir varianza frente al árbol sin poda mediante agregación y regularización. Se mantuvieron los seis predictores aprobados y sus exclusiones, sin ROS nuevo ni artefactos de preprocesamiento global. Este diseño evalúa una extensión de un procedimiento; el bosque dispone de cuatro configuraciones frente a una por variante histórica. Esa mayor flexibilidad es parte del procedimiento, no una comparación de complejidad idéntica. No se añaden más modelos al observar el desenlace.

## Comparación completa de clasificación externa

Umbrales aprendidos internamente. AP concatenada únicamente para cada variante; no se interpreta como probabilidad calibrada ni como media entre folds. `nan` en selectores significa deliberadamente no calculada.

'''+tabla(gm[gm.regla.eq('aprendido')][['modelo','TP','FP','TN','FN','precision','recall','f1','f2','average_precision','FPR']])+'''
El árbol ponderado tiene el mayor F1 agregado (0,1053) y Precision (0,0847) entre estas reglas aprendidas, pero detecta cinco ATO y omite 31; **no se lo eleva retrospectivamente a ganador**. GaussianNB tiene mayor recall (0,8611), a cambio de 38.839 falsas alarmas. KNN baseline detecta seis, con 122 falsas alarmas. El bosque no mejora este equilibrio: cuatro aciertos con 158 FP y 32 FN. El selector ampliado eligió bosque en los cinco internos, por lo que coincide con él externamente; eso no demuestra que la elección fuera útil.

El selector histórico tiene los mismos cuatro aciertos agregados y solo 72 FP: 86 falsas alarmas menos que el ampliado, con igual recall agregado. No implica que acierte exactamente los mismos eventos ni que domine cada fold. Las predicciones preservadas permiten verificar las diferencias por evento. Esta comparación no usa el resultado externo para cambiar selección o umbral.

## Estabilidad y AP: magnitudes diferentes

'''+tabla(sm[sm.regla.eq('aprendido')][['modelo','f1_mean','f1_std','average_precision_mean','average_precision_std','recall_mean','recall_std']])+'''
Random Forest presenta AP concatenada 0,06021 y AP media por fold 0,09858 ± 0,06549. KNN baseline tiene 0,04316 y 0,05545 ± 0,04295 respectivamente. Hay señal de ranking relativa, pero no demostración de mejora significativa o utilidad operativa. La AP por fold del bosque va de 0,00927 a 0,17539; el peor fold está lejos del mejor. Las puntuaciones proceden de estimadores y configuraciones diferentes, sin calibración común. Los selectores tienen AP solo por fold; no se concatena su mezcla de familias.

GaussianNB tiene menor dispersión absoluta de F1, pero alrededor de un resultado casi nulo: estabilidad no equivale a calidad. No existe un vencedor global combinando recall, falsas alarmas, estabilidad y coste. El bosque tampoco queda recomendado por encabezar AP.

## Transferencia de decisiones y umbrales

'''+tabla(details)+'''
'''+tabla(fm[(fm.modelo=='random_forest')&(fm.regla=='aprendido')][['fold','TP','FP','FN','precision','recall','f1','average_precision','usuarios_ato_detectados']])+'''
Los umbrales del bosque oscilan entre 0,6093 y 0,8408; se utilizan las cuatro configuraciones en algún fold. F1 interno mejora, pero externo cae: especialmente fold 4, de 0,2264 interno a 0,0139 externo, con 135 FP (85,4% de todos los FP del bosque). El fold 2 no detecta ningún ATO. Una evaluación sin separación interna/externa habría ocultado esta fragilidad.

Referencia fija 0,5, prevista antes del experimento:

'''+tabla(gm[(gm.modelo=='random_forest')][['regla','TP','FP','FN','precision','recall','f1','f2','usuarios_ato_detectados','usuarios_sin_ato_con_alerta']])+'''
Con 0,5 se detectan 16 ATO, pero se generan 1.474 FP (aproximadamente 92 por acierto). Con umbrales aprendidos son 158/4 = 39,5 FP por acierto y 97,53% de alertas falsas. La regla interna de F1 sacrifica recuperación para reducir alertas y no transfiere bien. No se ha escogido otro umbral mirando estos resultados. Las veinte tablas umbrales_internos_{fold}_{configuracion}.csv conservan todos los estados internos, incluidos alertar a todos o a ninguno. F1 no representa costes universales; falta capacidad de revisión humana y coste relativo de omisiones/falsas alarmas para decidir un criterio operativo defendible.

## Eventos y usuarios

'''+tabla(gm[gm.regla.eq('aprendido')][['modelo','usuarios_ato','usuarios_ato_detectados','usuarios_ato_omitidos','recall_usuarios','usuarios_sin_ato_con_alerta','usuarios_con_fp']])+'''
Se define usuario ATO detectado como aquel con al menos un **evento ATO correctamente alertado**, no simplemente una alerta en cualquier login. El bosque detecta 4/34 usuarios positivos (11,76%), omite 30 y genera FP en 140 usuarios; 126 son usuarios sin ATO. Los 158 FP no se concentran únicamente en un sujeto: máximo siete en un usuario, 28 entre los diez con más FP. Todos los cuatro aciertos del bosque están en RO; allí omite once ATO. NO aporta 122 FP y cinco FN. Este contraste descriptivo tiene denominadores por perfil en los CSV y no autoriza a crear reglas por país o memorizar usuarios.

La métrica por evento da más peso a usuarios activos; por usuario cambia la unidad. Con solo 34 usuarios positivos, los intervalos de generalización serían amplios y la independencia entre eventos no es defendible. No se calculan pruebas de significación que traten los cinco folds solapados como réplicas independientes.

## CV1, CV2 y cinco modelos académicos

Los seis experimentos supervisados históricos siguen completos, también los desfavorables. Las siguientes métricas corresponden a umbral 0,5; cambiar la distribución de folds no cambia el algoritmo ni constituye una mejora causal:

'''+tabla(refs[['protocolo','modelo','TP','FP','FN','precision','recall','f1','average_precision']])+'''
Los cinco modelos exigidos por el curso siguen documentados: árbol, GaussianNB, KNN, KMeans y jerárquico (con sus variantes). Random Forest es una extensión adicional. KMeans/jerárquico son segmentaciones exploratorias y no reciben TP/FP ni se venden como detectores sin una regla supervisada válida. KMeans k=2: silhouette 0,6060, grupos 41.296/5.009; Ward k=2 sobre 4.000 observaciones: silhouette 0,5978, grupos 3.534/466. Las prevalencias KMeans 32/41.296 y 4/5.009 son similares; separar geometría no demuestra separar ATO. Sus resultados y limitaciones permanecen en [INFORME_CLUSTERING_FASE04.md](INFORME_CLUSTERING_FASE04.md).

Para presentación académica se conservan íntegros `fase04_modelado/resultados/`, `resultados_cv_usuario/`, `resultados_presentacion_supervisado/`, `seleccion_supervisada/resultados/`, `validacion_anidada/resultados/` y `fase04_clustering/resultados/`: métricas por fold, matrices, PR, análisis de umbrales, errores y gráficas. Este informe añade una conclusión; no reemplaza resultados individuales. CV1, CV2, anidada y extensión reutilizan train; no son experimentos independientes.

## Coste y pruebas

'''+tabla(costs)+f'''
Tiempo total del experimento: {run['segundos']:.3f} s, 65 ajustes y 6.500 árboles; máximo RSS observado al final de un fold {max(run['rss_muestreado_bytes'])/1048576:.2f} MiB. Es muestreo de RSS, no pico continuo ni consumo exclusivo del modelo. Tiempos históricos se conservan en sus informes y CSV; no se equipara tiempo de búsqueda de 65 ajustes con un único ajuste histórico. No se instaló ni actualizó ningún paquete.

**15 tests ejecutados y aprobados en 7,87 s**, una pasada. Incluyen dos ajustes sintéticos adicionales, no parte de los 65 experimentales. Se comprobaron particiones reproducibles, separación de usuarios, cobertura OOF interna/externa, clave natural/target, medianas/categorías locales de los 65 ajustes, inmutabilidad de validación, ausencia de ROS nuevo, selección y desempates frente al algoritmo exhaustivo histórico, recálculo de métricas globales/por fold, hashes, configuración y 14 pares PNG/SVG. El test de guardia simula el intento prohibido antes de acceso al archivo. No se repitió el experimento completo para demostrar igualdad bit a bit: reproducibilidad de entrenamiento comprobada con datos sintéticos, semillas y selección real reproducibles.

Integridad comprobada: {n} archivos históricos con SHA-256, tamaño y mtime iguales al inventario previo. Test no se leyó, inspeccionó ni hasheó. No se ejecutó Git, no se modificaron datasets, Fase 3 ni preprocesamiento aprobado. No hay modelo final entrenado. Los tests validan implementación; no demuestran validez científica por sí solos.

## Gráficas y datos reproducibles

'''+figure_text+'''

Tablas y predicciones nuevas en `fase04_modelado/mejora_controlada/resultados/`: comparacion_global.csv (ambas reglas), metricas_por_fold.csv, resumen_folds.csv (DE muestral), metricas_por_usuario.csv, errores_por_perfil.csv, referencias_cv1_cv2.csv, tiempos.csv, transferencia_seleccion.csv, predicciones_externas_rf.csv, predicciones_selector_ampliado.csv, cinco OOF internas, veinte tablas de umbrales, cinco decisiones congeladas, configuracion_congelada.json, auditoria_ajustes.json, ejecucion.json y pruebas.txt. Las claves/índices originales permiten trazabilidad; no son predictores. Todas las figuras incluyen las variantes desfavorables. Se inspeccionó visualmente la comparación principal; validación automática de formato/tamaño de todas las figuras.

## Decisión y próximos pasos

No hay candidato con equilibrio suficientemente respaldado para recomendarlo como detector útil. El árbol ponderado es una referencia descriptiva por F1, el bosque/KNN referencias por ranking, y GaussianNB por recuperación extrema; ninguno reúne de manera estable los objetivos. El criterio de descarte del nuevo experimento se cumple: mayor AP no se traduce en recuperación/falsas alarmas consistentes, y ampliar la selección empeora FP agregados sin aumentar aciertos.

La evidencia respalda limitaciones de esta muestra y representación, no imposibilidad universal ni una atribución causal exclusiva al desbalance. Hay ocho positivos indistinguibles de negativos por X, redundancia, pocos sujetos positivos, señales temporales escasas y geografía sintética. Excluir variables semánticamente inválidas no se revierte porque otros modelos rindan poco. Ni más algoritmos indiscriminados ni elegir el mejor umbral externo corrigen ese problema.

Se recomienda cerrar esta búsqueda exploratoria y acordar con el responsable académico si se presentará el resultado negativo comparativo o se solicitarán más usuarios ATO y señales preautenticación verificadas. Para completar evaluación final habrá que aprobar un **procedimiento de referencia explícito** (sin afirmar que es bueno), fijar su selección/configuración/preprocesamiento/umbral usando solo train, y pedir autorización independiente antes de abrir test. No se usa test para desempatar. Si se amplía la muestra o representación, será un protocolo nuevo y documentado. No se declara terminada Fase 4.
'''
    texto_nuevo('INFORME_DECISION_MODELO_FASE04.md',report)
    readme='''# Estado de Fase 4

Fecha: 2026-11-21. **Fase 4 abierta; sin modelo final aprobado y test cerrado.**

Se completó auditoría, diagnóstico y una extensión controlada de Random Forest: cuatro configuraciones seleccionadas dentro de 5×3 folds por usuario, 65 ajustes. Se reutilizaron resultados históricos verificados, no sus transformadores ajustados. El bosque detecta 4/36 ATO, omite 32 y produce 158 FP; 4/34 usuarios ATO detectados. No se recomienda ganador. AP más alta no resolvió clasificación ni estabilidad.

## Entregables nuevos

- [Diagnóstico](INFORME_DIAGNOSTICO_CAPACIDAD_PREDICTIVA_FASE04.md).
- [Propuesta previa a ejecución](PROPUESTA_EXPERIMENTOS_MEJORA_FASE04.md).
- [Decisión y comparación completa](INFORME_DECISION_MODELO_FASE04.md).
- `fase04_modelado/mejora_controlada/`: contratos.py, ajuste.py, diagnostico.py, ejecutar.py, evaluar.py, graficas.py, informe.py y tests/test_contratos.py. Responsabilidades separadas y reutilización de fábricas históricas de solo lectura; sin refactor general.
- `fase04_modelado/mejora_controlada/resultados/`: diagnóstico, OOF internas/externas, decisiones, métricas/errores por evento/perfil/usuario, tiempos, configuración, logs de auditoría, pruebas y 14 figuras PNG/SVG a 300 dpi. Índice en catalogo_graficas.json.
- inventario_previo.json y manifiesto_entrega.json: integridad histórica y hashes nuevos.

## Comprobaciones ejecutadas

`python -B -m pytest -p no:cacheprovider -q fase04_modelado/mejora_controlada/tests`

15 casos aprobados, cero fallos, 7,87 s; dos ajustes sintéticos adicionales. Contratos de selección, partición reproducible, ajuste local, no contaminación de validación, cobertura/alineación OOF, métricas desde predicciones, configuración, gráficas e integridad. No equivalen a demostración de generalización. Las 20 pruebas anidadas históricas se referencian, no se cuentan como ejecutadas nuevamente.

Se verificaron 406 históricos por SHA-256/tamaño/mtime. Test fue excluido del inventario y bloqueado por guardia para los procesos de análisis/modelado: no se leyó ni hasheó. No se modificaron datos, etiquetas, particiones, código Fase 3, preprocesamiento ni informes previos. No se ejecutó Git ni se instalaron paquetes.

## Historial académico preservado

Los cinco modelos exigidos por el curso (árbol, GaussianNB, KNN, KMeans y jerárquico) y todas sus variantes se conservan con CV1, CV2, selección/umbrales y anidada. Bosque es una extensión adicional. Consulte los informes históricos y sus carpetas indicadas en el informe de decisión; clustering no se interpreta como detector.

## Reproducción y pendientes

Orden lógico ejecutado: diagnostico → ejecutar → evaluar → graficas → tests → informe. Cada módulo se invoca con `python -B -m fase04_modelado.mejora_controlada.<modulo>`. Persistencia exclusiva: **no volver a ejecutar sobre estas salidas**; para una réplica se requiere un destino nuevo y los mismos hashes/particiones/semillas/versiones. Los archivos fallan si ya existen; no sobrescriben resultados.

Los 65 ajustes completos no se repitieron; selección y particiones reales se reconstruyeron, y entrenamiento se comprobó reproducible con datos sintéticos. No se entrenó sobre todo train. El siguiente paso requiere decisión académica: aceptar comparación negativa o preparar un protocolo nuevo con mejores datos. Antes de una evaluación final deben aprobarse y congelarse procedimiento, configuración y umbral; abrir test requiere autorización independiente. No realizar más búsqueda para perseguir un resultado favorable.
'''
    texto_nuevo('README_ESTADO_FASE04.md',readme)
    print('Informes generados; historicos verificados:',n)

if __name__=='__main__':main()
