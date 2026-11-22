# Resumen ejecutivo para sustentación — Fase 4

Fecha: 22 de noviembre de 2026. Lectura prevista: aproximadamente cinco minutos.

## ¿Qué hicimosí

En esta fase comparamos formas de detectar eventos de toma de control de cuentas, conocidos como ATO. Trabajamos con un dataset corregido de 57.420 eventos y 2.000 usuarios. Había solo 45 eventos ATO, por lo que encontrar la clase positiva era difícil y medir el desempeño requería cuidado.

Dividimos los datos por usuario: 46.305 eventos quedaron en entrenamiento y 11.115 en test. Ningún usuario aparece en ambos conjuntos. Esto evita evaluar un modelo con eventos de una cuenta cuyo historial ya estaba en el ajuste. En train había 36 ATO de 34 usuarios; en test, nueve ATO de nueve usuarios.

Antes de modelar se corrigió un problema de asociación de etiquetas en Fase 3. La evidencia previa comprobó 90 etiquetas cambiadas y conservación de las otras columnas. No cambiamos etiquetas para mejorar resultados. Usamos seis variables: dispositivo, país, fallos previos en dos ventanas, tiempo desde el acceso anterior y existencia de historial. Excluimos resultados del login actual, datos simulados y señales geográficas sin fiabilidad suficiente.

## ¿Qué algoritmos probamosí

Comparamos árbol de decisión y GaussianNB, cada uno sin ponderación y con ponderación de clases; KNN sin sobremuestreo y con RandomOverSampler; y un Random Forest ponderado. Son siete variantes supervisadas. También usamos KMeans y clustering jerárquico para explorar grupos sin la etiqueta ATO.

Cada método planteaba algo distinto: reglas en árboles, combinación probabilística en Naive Bayes y vecinos similares en KNN. La ponderación y el sobremuestreo buscaban dar más atención a los pocos positivos. El bosque intentó reducir la variabilidad de un árbol individual.

## ¿Qué diferencias encontramosí

No hubo un ganador en todo. En CV1 destacó el árbol baseline por F1 a umbral 0,5. Al repartir los usuarios de otra manera en CV2 destacó KNN con sobremuestreo. Ambos protocolos usaron el mismo train; no son dos experimentos independientes que prueben una superioridad.

Después usamos validación anidada: dentro de cada fold se eligió el umbral y fuera se evaluó su transferencia a otros usuarios. Esta tabla resume sus resultados externos; Random Forest es una extensión con las mismas particiones y selección interna de configuración.

| Variante | ATO detectados | Falsas alarmas | ATO omitidos | F1 |
|---|---:|---:|---:|---:|
| Árbol baseline | 3 | 64 | 33 | 0,0583 |
| Árbol ponderado | 5 | 54 | 31 | 0,1053 |
| GaussianNB baseline | 31 | 38.839 | 5 | 0,0016 |
| GaussianNB ponderado | 31 | 38.839 | 5 | 0,0016 |
| KNN baseline | 6 | 122 | 30 | 0,0732 |
| KNN + ROS | 5 | 104 | 31 | 0,0690 |
| Random Forest ponderado | 4 | 158 | 32 | 0,0404 |

GaussianNB recuperó muchos ATO, pero produjo demasiadas alertas falsas. KNN tuvo un ranking interesante según Average Precision, aunque eso no se convirtió siempre en buenas decisiones. Random Forest también mejoró el ranking relativo, pero no el equilibrio al aplicar su umbral. Una AP mayor no significa automáticamente un F1 mayor: una mide ordenamiento de scores y la otra depende de la frontera de clasificación.

## ¿Por qué elegimos el árbol ponderado?

Lo elegimos como **referencia académica por su mayor F1 agregado en esa comparación anidada**. Con cinco aciertos y 54 falsas alarmas obtuvo un compromiso mejor según F1 que las alternativas mostradas.

Eso no significa que fuera eficiente: omitió 31 de los 36 ATO y 29 de los 34 usuarios positivos. Tampoco fue elegido en todos los folds por el selector conjunto. La decisión de fijarlo se tomó después de revisar los resultados y se reconoce como una elección retrospectiva, no como superioridad universal.

Conviene separar tres ideas: ser la mejor referencia relativa, tener un modelo final guardado y tener un detector apto para producción. Cumplimos las dos primeras; no demostramos la tercera.

## ¿Qué mostró el clustering?

KMeans y Ward separaron principalmente accesos con poco historial reciente de fallos y accesos próximos con más fallos. KMeans formó grupos de 41.296 y 5.009 eventos. Sus prevalencias de ATO fueron casi iguales: 0,07749 % y 0,07986 %.

Por tanto, encontramos perfiles de comportamiento, pero no grupos que pudieran llamarse “atacantes”. El jerárquico se limitó a 4.000 eventos por memoria y su muestra contenía solo un ATO. No usamos Precision, Recall o F1 para convertir esos grupos en clasificadores.

## ¿Cómo se comportó la referencia en testá

Primero fijamos el procedimiento, entrenamos la referencia y conservamos un umbral de 0.9976439543869569. El F1 OOF 0,173913 se usó para seleccionar ese umbral; no era una evaluación independiente.

La evaluación final de test se autorizó y ejecutó una sola vez, sin reajustar nada después:

| Resultado independiente | Valor |
|---|---:|
| ATO detectados | 1 de 9 |
| ATO omitidos | 8 |
| Falsas alarmas | 12 |
| Negativos correctos | 11.094 |
| Precision | 7,69 % |
| Recall | 11,11 % |
| F1 | 0,090909 |
| Average Precision | 0,009267 |

Detectó un usuario positivo y omitió ocho. Hubo falsas alarmas en siete usuarios, seis sin ATO y uno que también tuvo ATO. De 13 alertas, solo una correspondió a un ATO real.

## ¿Qué aprendimos y cuáles son los límitesí

El desbalance no se arregla solamente repitiendo positivos o dando más peso a la clase minoritaria. También importan las variables, su significado y la diversidad de usuarios. Ocho ATO compartían exactamente los seis predictores con 621 negativos; con esas entradas es difícil distinguirlos individualmente.

Hay mucha incertidumbre: en test un solo acierto cambia el recall en unos 11,11 puntos porcentuales. El resultado describe esta partición, no garantiza lo que pasaría en otros usuarios o fechas. Los datos sintéticos y la limitada información temporal/contextual también restringen la interpretación.

Como trabajo futuro en otros estudios, serían útiles más ATO representativos, mejores variables disponibles en el momento del acceso, geografía fiable y validaciones externas o temporales. No garantizan una mejora y no se ejecutarán sobre este test ya utilizado.

**Conclusión:** logramos comparar algoritmos, justificar una referencia y evaluarla de manera controlada. No obtuvimos evidencia suficiente de un detector eficiente para producción. Identificar esa limitación con resultados trazables es una conclusión académica válida. La experimentación y evaluación están cerradas; aquí se completa su documentación, sin certificar otros requisitos del profesor.

Informe completo: [INFORME_FINAL_FASE04_CRISP_DM.md](INFORME_FINAL_FASE04_CRISP_DM.md).

