# Diseño previo a la ejecución

Solo train, sin consultar target hasta congelar algoritmo, K y etiquetas. Se reutiliza la fábrica aprobada de transformación, ajustada de nuevo sin y: mediana, log1p y StandardScaler en tres numéricas; binaria sin escalar; One-Hot sin escalar en Device Type y Country. La reconstrucción es idéntica a X_train_distancias_fase04.npy (46305 × 62).

Contribución esperada a distancia euclídea al cuadrado entre dos eventos independientes: numéricas 6, binaria 0,06672, dispositivo 1,08076, país 0,74478. Las 54 categorías de país no multiplican arbitrariamente su peso: cada bloque nominal aporta como máximo 2. No añadimos pesos. Las dos cuentas de fallos correlacionadas pueden enfatizar actividad; se declara como limitación.

KMeans: K de 2 a 8; init k-means++, n_init=10, max_iter=300, algoritmo Lloyd, semillas 42, 43, 44 para estabilidad. Se conserva 42 como ejecución principal. Silhouette sobre 2000 eventos uniformes fijos (42); DB y CH sobre toda la población ajustada. Selección posterior sin target, combinando codo, índices, tamaños e interpretabilidad; no optimización por ATO.

Jerárquico: muestra uniforme sin reemplazo de 4000 eventos, semilla 42, sin target ni estratificación; Ward y average con euclídea, K 2–8. Distancias condensadas completas: 8,58 GB; cuadradas: 17,15 GB, sin temporales. Muestra: 64 MB condensadas, 128 MB cuadradas. La memoria libre observada era aproximadamente 11,3 GiB; no es prudente ajustar jerárquico completo. Complejidad cuadrática; el tiempo se medirá, no se presenta una estimación de segundos sin benchmark. Comparación con KMeans en los mismos eventos mediante ARI, sin equivalencia de poblaciones de ajuste.

Tras congelación se permite evaluación externa descriptiva ATO. Ningún cluster será llamado malicioso. La actualización visual supervisada solo utiliza CSV OOF y métricas históricas, sin entrenar estimadores. PNG 300 DPI y SVG. Los hashes históricos se verifican; test únicamente por metadatos, sin leer contenido.
