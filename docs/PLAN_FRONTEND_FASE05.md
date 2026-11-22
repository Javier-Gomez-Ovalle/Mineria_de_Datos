# Fase 5: auditoría y planificación del frontend académico ATO

Fecha: 22 de noviembre de 2026. Estado: propuesta para revisión, no implementación. Solo se creó este informe; no se modificaron archivos existentes, no se instalaron dependencias ni se ejecutaron modelos, evaluación, commit o push. No se accedió al dataset test ni a sus predicciones individuales. Las referencias a su evaluación proceden exclusivamente de documentación histórica.

## 1. Estado verificado

El repositorio contiene una implementación Python modular: `fase03_refactor/`, `fase04_preparacion/`, `fase04_modelado/`, `fase04_clustering/` y `fase04_metodos_numericos/`. También existen `docs/`, `data/`, `tests/`, `tools/`, informes raíz y dependencias. Hay archivos históricos y datasets locales excluidos de la publicación: la existencia física de un archivo no autoriza a servirlo en una web.

No se encontraron package.json, lockfiles frontend, HTML, JSX/TSX, CSS ni configuración Vite en la inspección del árbol de trabajo, excluyendo metadatos internos de Git. No hay frontend existente que debamos migrar. Node local: 20.19.5; npm: 11.17.0. Son herramientas presentes, no dependencias fijadas del proyecto. La rama actual es main, con modificaciones previas en .gitignore y `fase04_metodos_numericos/` sin rastrear. No se comprobó en esta tarea el estado remoto mediante red ni se afirma un despliegue web existente.

Dependencias declaradas: Python 3.12.7 para referencia, NumPy 2.3.4, pandas 2.3.3, scikit-learn 1.7.2, SciPy 1.16.3, joblib 1.5.2, imbalanced-learn 0.14.2, matplotlib 3.10.7, Pillow 12.0.0, psutil 7.1.3, threadpoolctl 3.6.0 y pytest 9.1.1. Faker figura como dependencia histórica opcional sin versión acreditada. Ninguna necesita trasladarse al navegador.

Se identificaron 220 archivos gráficos PNG/SVG: 200 en modelado, 14 en clustering y 6 en métodos numéricos, aproximadamente 30,13 MB en total. Hay pares PNG/SVG de una misma figura: no son 220 análisis distintos. Las comparaciones CSV de CV1 y CV2 tienen seis variantes cada una y campos de TP/FP/TN/FN, Precision, Recall, F1, AP, media/desviación por fold, tiempos y parámetros. La tabla anidada contiene 14 filas por modelo/regla; la extensión controlada, 18. No se deben confundir esas filas con algoritmos distintos.

### Cinco algoritmos y extensión

La presentación principal debe identificar Árbol de Decisión, GaussianNB, KNN, KMeans y clustering jerárquico. Los tres primeros son supervisados; los dos últimos son exploratorios. Las variantes baseline, ponderadas y KNN+ROS permanecen visibles. Random Forest ponderado existe como extensión controlada y debe tener un apartado adicional, no desaparecer para forzar el número cinco. El profesor podrá recorrer los cinco métodos principales y consultar también la evidencia de la extensión.

## 2. Tecnología recomendada — decisión propuesta

**Vite + TypeScript sin framework de interfaz, HTML semántico y CSS propio.** La aplicación será un sitio estático de resultados, no un servicio de inferencia. La ausencia de frontend previo permite elegir una base pequeña, sin migraciones. TypeScript facilita contratos de datos, constructores, clases y sustitución de una fuente en pruebas. Vite proporciona desarrollo y empaquetado estático; no es un framework visual.

La documentación oficial ofrece plantilla vanilla-ts y exige Node 20.19+ o 22.12+; el ejecutable observado cumple el primer mínimo. Antes de instalar se fijarán versiones compatibles y un lockfile, sin asumir que la combinación local Node/npm ya está validada para la nueva aplicación. No se instala nada durante esta auditoría. Fuente: [guía oficial Vite](https://vite.dev/guide/).

React/Vue serían razonables si aparecieran formularios complejos, muchas vistas con estado compartido o una integración operativa. Hoy añadirían conceptos sin resolver una necesidad de esta presentación. HTML/JS sin herramienta sería más simple inicialmente, pero ofrece menos ayuda con contratos y compilación. Streamlit aprovecharía Python, aunque requeriría servidor y acercaría la presentación a scripts experimentales que no deben ejecutarse. No se propone backend, base de datos, autenticación ni motor de modelos para este alcance.

Gráficas iniciales: imágenes existentes y tablas accesibles, sin Plotly/Chart.js ni dependencias nuevas de gráficos. Interacción: elegir protocolo/variante, desplegar explicaciones, ampliar figuras y navegar. No ofrecer controles para cambiar umbral, recalcular ajuste, entrenar o evaluar. Las fórmulas se presentan como texto matemático accesible; una biblioteca de composición matemática solo se justificaría si las expresiones finales no se leen bien.

## 3. Arquitectura y responsabilidades propuestas

Flujo: archivos históricos permitidos → preparación documental determinista → catálogo JSON público reducido y figuras seleccionadas → repositorio de lectura → vistas. La preparación solo copia valores y valida esquemas; no calcula métricas ni ejecuta módulos de experimentos.

- `preparar_contenido.py`: herramienta fuera del runtime web, lista explícita de entradas permitidas, extracción de tablas agregadas y secciones documentales, verificación de correspondencia con origen. Reutiliza pandas/JSON existentes si hacen falta. Prohibición de glob indiscriminado o importación de motores experimentales. No habrá lectura de datasets ni de predicciones OOF/test.
- `FuenteResultados`: contrato pequeño con `cargar_catalogo()`. El catálogo contiene secciones, protocolos, variantes, valores, unidades y procedencia.
- `RepositorioResultadosJson`: constructor con URL base y función de lectura inyectada; método `cargar_catalogo()`; comprueba versión de esquema y errores de carga.
- `AplicacionAcademica`: constructor con elemento raíz y FuenteResultados; `iniciar()` coordina carga, navegación y vistas.
- Vistas y funciones puras: `renderizar_tabla_metricas`, `formatear_numero`, `crear_figura`, `renderizar_metodos_numericos`. No hace falta una clase por párrafo o indicador.
- Un solo estado de presentación pequeño: sección, protocolo y variante seleccionados. No duplicar las métricas en componentes ni crear un almacén global adicional.

Identificadores propios y campos JSON en snake_case; clases e interfaces en PascalCase. Conservar API nativa del navegador y nombres impuestos por librerías. No renombrar módulos Python ni archivos de resultados.

### SOLID como criterio verificable, no afirmación anticipada

| Principio | Aplicación propuesta | Comprobación futura |
|---|---|---|
| SRP | Fuente carga, validador comprueba contrato, funciones formatean, vistas presentan | Cambiar el diseño no altera extracción ni métricas |
| OCP | Catálogo declarativo de protocolos y variantes; vistas reutilizables | Incorporar una variante documentada sin duplicar la tabla |
| LSP | Fuente JSON y fuente en memoria satisfacen el mismo contrato | Pruebas comunes de respuesta y errores; no basta la firma |
| ISP | Fuente de resultados no expone métodos de entrenamiento, archivos o credenciales | Consumidores dependen solo de cargar catálogo |
| DIP | AplicacionAcademica recibe FuenteResultados por constructor | Pruebas sin red ni acceso al filesystem histórico |

Estas son decisiones futuras. No existe aún ese código y no se certifica cumplimiento SOLID de un frontend no implementado.

## 4. Estructura sugerida, todavía no creada

```text
frontend/
  index.html
  package.json
  package-lock.json
  tsconfig.json
  vite.config.ts
  scripts/
    preparar_contenido.py
    fuentes_permitidas.json
  public/
    contenido/catalogo.json
    figuras/                 # Solo las figuras elegidas
  src/
    main.ts
    aplicacion.ts
    datos/contratos.ts
    datos/repositorio_resultados.ts
    vistas/proyecto.ts
    vistas/modelos.ts
    vistas/clustering.ts
    vistas/metodos_numericos.ts
    componentes/tabla_metricas.ts
    componentes/figura_academica.ts
    formato.ts
    estilos.css
  tests/
    contratos.test.ts
    presentacion.test.ts
  README.md
```

Es un límite inicial de responsabilidades, no una obligación de crear archivos vacíos. Ajustar el número de vistas a la implementación real. No copiar Python, CSV de datos, modelos o repositorios enteros a public/. `dist/` será el único artefacto a desplegar. Cualquier configuración futura de .gitignore se hará tras autorización: la lista positiva actual no admite automáticamente frontend/ ni este informe nuevo.

## 5. Contenido y fuentes exactas

Todas las rutas siguientes son relativas a la raíz del repositorio. Son fuentes de lectura para preparar la presentación; no todas deben enviarse íntegramente al navegador.

| Sección, en orden de navegación | Fuente principal | Componente y tratamiento |
|---|---|---|
| 1. Problema y objetivos | `README.md`; `INFORME_FINAL_FASE04_CRISP_DM.md`, introducción | Apertura narrativa: qué es ATO, pregunta académica y alcance; sin cifras de incidentes inventadas |
| 2. CRISP-DM | `INFORME_FINAL_FASE04_CRISP_DM.md`; `docs/METODOLOGIA_Y_RESULTADOS.md` | Recorrido de etapas con enlaces. Diferenciar cierre académico de despliegue productivo; la etiqueta local Fase 5 no demuestra validación operativa |
| 3. Preparación y corrección | `INFORME_CORRECCION_TARGET_FASE03.md`; `INFORME_PARTICION_FASE04.md` | Diagrama de asociación por clave, corrección de 90 etiquetas, partición por usuarios; cifras ya documentadas |
| 4. Predictores y exclusiones | `INFORME_PREPROCESAMIENTO_FASE04.md`; `INFORME_REVISION_IMPOSSIBLE_TRAVEL_FASE04.md`; `fase04_preparacion/seleccion.py` | Seis predictores, unidades, motivos de exclusión y prevención de fuga; inspección del código sin ejecutarlo |
| 5. Supervisados CV1 | `fase04_modelado/resultados/comparacion_modelos.csv`; `fase04_modelado/resultados/metricas_por_fold.csv`; `INFORME_MODELADO_SUPERVISADO_FASE04.md` | Tabla de seis variantes, métricas globales separadas de medias/desviaciones por fold |
| 6. Supervisados CV2 y contraste | `fase04_modelado/resultados_cv_usuario/comparacion_modelos.csv`; `metricas_por_fold.csv` y `comparacion_protocolos.csv` en esa carpeta; `INFORME_SEGUNDA_VALIDACION_FASE04.md` | Selector de protocolo explícito; comparación apareada de protocolos sin atribuir mejoras al algoritmo |
| 7. Anidada, extensión y selección | `fase04_modelado/validacion_anidada/resultados/metricas_globales.csv`; `metricas_por_fold.csv` en esa carpeta; `fase04_modelado/mejora_controlada/resultados/comparacion_global.csv`; `INFORME_COMPARATIVO_ALGORITMOS_FASE04.md`; `INFORME_DECISION_MODELO_FASE04.md` | Separar regla a 0,5, umbral interno y selectores. Mostrar Random Forest como extensión, no ganador automático por AP |
| 8. Referencia y evaluación final histórica | `fase04_modelado/recuperacion_referencia_v1_20261122/MANIFIESTO_MODELO_FINAL.json`; `fase04_modelado/evaluacion_final_test_20261122/INFORME_EVALUACION_FINAL_TEST_FASE04.md`; `MANIFIESTO_EVALUACION_TEST.json` en esa carpeta | Metadatos de referencia, umbral congelado y métricas transcritas del informe. El manifiesto de evaluación acredita cierre pero no sustituye la tabla de métricas del informe. No abrir dataset ni predicciones |
| 9. Clustering | `INFORME_CLUSTERING_FASE04.md`; `fase04_clustering/resultados/candidatos.csv`; `seleccion_congelada.json`; `perfil_numerico_kmeans_2.csv`, `perfil_numerico_ward_2.csv`, `perfil_categorico_kmeans_2.csv`, `perfil_categorico_ward_2.csv` en esa carpeta | KMeans y Ward: perfiles, índices internos y tamaños. Ward usa una submuestra de 4.000; no comparar tamaños como misma población que KMeans. La evaluación externa existente es descriptiva |
| 10. Diagnóstico y conclusiones | `INFORME_DIAGNOSTICO_CAPACIDAD_PREDICTIVA_FASE04.md`; `RESUMEN_EJECUTIVO_SUSTENTACION_FASE04.md`; informe final | Limitaciones, pocos usuarios positivos, inestabilidad y baja sensibilidad; no promesa productiva |
| 11. Regresión lineal | `fase04_metodos_numericos/resultados/resultados.json`; `INFORME_REGRESION_INTERPOLACION_FASE04.md` en esa carpeta | 5.662 pares, ecuación, R² y RMSE originales; gráfica principal intacta |
| 11a. Sensibilidad diagnóstica | `fase04_metodos_numericos/revision_complementaria/resultados_sensibilidad.json`; `INFORME_REVISION_COMPLEMENTARIA.md` en esa carpeta | Diagnóstico de 29 pares separado visual y semánticamente; no sustituye el ajuste principal |
| 12. Interpolación de Lagrange | `fase04_metodos_numericos/resultados/resultados.json`, campos interpolacion y puntos; informe de métodos | Tres puntos reales, polinomio, intervalo y límites. Última sección analítica, después de regresión |
| Fuentes y arquitectura (enlaces auxiliares) | `docs/PROCEDENCIA_Y_LICENCIAS.md`; `docs/ARQUITECTURA_Y_SOLID.md`; `docs/REPRODUCCION.md` | Atribuciones y explicación del código; fuera de la secuencia de resultados para mantener métodos numéricos al final |

### Verificación de cifras de métodos numéricos

Se consultaron los resultados existentes, sin volver a ajustar: n=5662, pendiente=2.641194034102526, intercepto=−7.007984832855932, R²=0.1671342031613564 y RMSE=2371.4695834312506 km/h. Sensibilidad X>0: n=29, pendiente=3.0670091056491695, intercepto=−3179.051792809627, R²=0.10468363069087849 y RMSE=33070.897901032666 km/h. Los ceros representan 99.48781349346521%; el RMSE principal evaluado sobre los mismos 29 pares es 33136.11629210919 km/h. Presentar este último contraste para no confundir cambio de población con mejora del ajuste.

Polinomio existente, coeficientes ascendentes: [−646.473854098942, 0.778670072678091, −0.00008883950954572797]. Intervalo [931.5694204688522, 7821.982499064356] km. Los puntos son (931.5694204688522 km, 1.814530244066689 km/h), (5093.044534302813 km, 1014.9103480167564 km/h) y (7821.982499064356 km, 8.765671039133261 km/h). Se recomienda mostrar redondeo legible conservando precisión original en el catálogo. No añadir slider que evalúe fuera del intervalo; para la primera versión basta la figura existente.

## 6. Gráficas y contrato público

Fuentes verificadas:

- CV1: `fase04_modelado/resultados/graficas/`: comparacion_metricas, confusion por variante, curvas_precision_recall, estabilidad_folds, falsos_positivos_negativos y variabilidad_folds, en PNG/SVG.
- CV2: `fase04_modelado/resultados_cv_usuario/graficas/`, con los mismos temas y comparacion_protocolos.
- Anidada: `fase04_modelado/validacion_anidada/resultados/graficas/`.
- Extensión: `fase04_modelado/mejora_controlada/resultados/graficas/`, incluido confusion_random_forest.svg y bosque_por_fold.svg.
- Clustering: `fase04_clustering/resultados/graficas/seleccion_interna.svg`, dendrograma_ward.svg, perfiles_kmeans_2.svg, perfiles_ward_2.svg, estabilidad_kmeans.svg, externa_kmeans_2.svg y externa_ward_2.svg.
- Métodos: `fase04_metodos_numericos/resultados/graficas/regresion_lineal.png` e interpolacion_lagrange.png, con sus SVG; sensibilidad en `fase04_metodos_numericos/revision_complementaria/comparacion_ceros_extremos.png` y SVG.

El catálogo futuro debe incluir id_figura, protocolo, variante, título, ruta relativa, texto alternativo, explicación de unidades y ruta de procedencia. Seleccionar una variante de formato por vista, no cargar PNG y SVG simultáneamente. SVG local revisado mediante img, no inyección de XML con innerHTML; PNG como alternativa. Revisar scripts/enlaces externos antes de copiar SVG. Vista de ampliación con teclado y texto explicativo. Carga diferida y dimensiones reservadas para evitar saltos.

No enviar las 220 imágenes en la carga inicial. Propuesta de presupuesto, todavía no medido: contenido inicial menor de 1 MB transferido; figuras bajo demanda. No regenerar gráficas históricas para cambiar colores; adaptar el contenedor y la tipografía de la web.

Contrato para métricas: protocolo, modelo, variante, regla, población, n, unidad, valor original y fuente. Validar con contratos antes de renderizar; valor ausente se muestra como «No disponible», nunca como cero inventado. AP es Average Precision guardada, no área trapezoidal nueva. R² no es accuracy. No mezclar medias de folds y OOF globales. Formatear con locale español, sin redondear el dato almacenado ni convertir sin aviso una proporción a porcentaje.

`fase04_metodos_numericos/resultados/frontend.json` pesa 481.994 bytes y contiene 5.662 observaciones e índices técnicos. **No copiarlo íntegro a public/** pese a su nombre. Para esta etapa, extraer solo métricas, coeficientes, tres nodos como resultados y metadatos de intervalo; usar la imagen para la nube de puntos. No distribuir CSV de entrenamiento, empleados, observaciones individuales, OOF, etiquetas de clusters, predicciones de test, joblib o inventarios del equipo.

## 7. Diseño visual y navegación propuestos

Concepto: cuaderno de evidencia académica, centrado en la pregunta «¿Qué muestran realmente los resultados sobre detectar ATO?». Apertura narrativa con acceso a metodología y resultados; sin una alarma simulada, semáforo de riesgo o indicador que sugiera detección en tiempo real.

Paleta propuesta: fondo #F6F8FC, superficies #FFFFFF, texto #18324B, acento #176B87, diagnóstico #7856A8 y advertencias #9B432D. Contraste debe verificarse al implementar, no se da por aprobado por elegir hexadecimales. Tipografía: Segoe UI o equivalente del sistema para lectura y títulos, números tabulares para métricas; no depende de una fuente remota. Ancho de texto aproximado 65–75 caracteres. Párrafos y tablas alineados a izquierda; números a derecha.

Escritorio: índice lateral persistente y contenido central amplio. Móvil: índice desplegable, títulos anclables y tablas con desplazamiento horizontal rotulado. Navegación por anclas, sin router SPA ni rutas que fallen al recargar. Ubicación visible de sección y protocolo. Un selector explícito CV1/CV2/anidada/extensión; evaluación final en bloque separado, nunca en la misma tabla como competidor usado para escoger ganador.

Esquema conceptual:

```text
Proyecto ATO                           Metodología | Resultados | Fuentes
Índice lateral       Pregunta, alcance y conclusión honesta
                     Explicación breve de la etapa
                     [Protocolo] [Variante]
                     Tabla accesible + figura ampliable
                     Qué significa / qué no permite concluir
                     Fuente exacta del resultado
```

Regresión e interpolación cierran el recorrido. Etiqueta visible «Ejercicio matemático complementario». La sensibilidad lleva «Diagnóstico con 29 pares», manteniendo la principal siempre disponible. Navegación por teclado, foco visible, enlace saltar al contenido, alt significativo, color no exclusivo para diferenciar curvas, movimiento reducido y sin animaciones automáticas de gráficas.

## 8. Riesgos y medidas

| Riesgo verificado o previsto | Medida propuesta |
|---|---|
| Datasets históricos siguen en el disco | Servir solo frontend/dist, nunca `python -m http.server` en la raíz. Lista positiva de fuentes y activos, no copiar árboles completos |
| Nombre frontend.json induce a distribuir observaciones | Extracción selectiva de resultados; no exportación de registros |
| Múltiples protocolos y etapas | Identidad compuesta protocolo/modelo/regla, leyenda y población siempre visibles |
| Estado de recuperación SIN_EVALUAR_TEST frente a evaluación posterior cerrada | Mostrar secuencia histórica; mantener manifiestos intactos y usar informe posterior como autoridad del resultado final |
| Cinco métodos principales más Random Forest | Separar extensión y variantes; no omitir evidencia desfavorable ni clasificar clustering como supervisado |
| Rutas con mayúsculas/minúsculas, espacios y subruta GitHub Pages | Validar en build con rutas exactas y Linux; resolver desde base de Vite; no usar rutas absolutas del computador |
| Publicación estática bajo nombre de repositorio | Si se autoriza GitHub Pages, base `/Mineria_de_Datos/`; la guía oficial exige base acorde a la URL. No configurar despliegue ahora |
| Figuras voluminosas | Catálogo selectivo, carga diferida, ampliación voluntaria; no recrear resultados |
| Licencias distintas y edición IPinfo incompleta | Atribuciones separadas, limitación visible; sin redistribuir datasets mediante la web |
| Texto/JSON ausente, inválido o codificación dañada | Validación previa y error explícito; no valores por defecto que inventen resultados |
| Riesgo de HTML/SVG activo | TextContent o plantillas controladas; no Markdown arbitrario con HTML sin saneamiento; imágenes locales revisadas |
| Resultados no equivalen a detector productivo | Sin formularios de scoring ni API de inferencia; advertencias semánticas en referencia y métodos numéricos |

Fuente técnica de despliegue propuesto: [Vite, despliegue estático y GitHub Pages](https://vite.dev/guide/static-deploy.html#github-pages). Publicar la web requerirá una autorización posterior independiente.

## 9. Etapas pequeñas con criterios de aceptación

1. **Aprobar alcance y catálogo.** Confirmar estructura narrativa, cinco métodos y extensión; inventario explícito de fuentes. Aceptación: cada sección enlaza a un resultado existente y ninguna entrada requiere abrir datasets/test.
2. **Preparar contrato público.** Implementar extracción de resultados y activos seleccionados en frontend/, sin modificar fuentes. Aceptación: equivalencia de cada valor con origen, ausencia de registros individuales, rutas personales y artefactos ejecutables de ML.
3. **Crear estructura visual.** Vite/TypeScript, navegación, estados de carga/error y dos componentes reutilizables. Aceptación: build reproducible, escritorio/móvil/teclado, sin backend ni inferencia.
4. **Integrar contenido académico.** Preparación, seis variantes, protocolos, extensión, referencia histórica y clustering. Aceptación: todos los modelos visibles, ceros reales conservados y separación clara entre métricas globales/folds/test histórico.
5. **Añadir métodos numéricos al final.** Figuras y cifras principales, sensibilidad separada e intervalo de Lagrange. Aceptación: unidades completas, ningún control extrapola o recalcula, ninguna sustitución de resultados.
6. **Verificar y entregar localmente.** Pruebas de contratos, redondeo de presentación, navegación, rutas bajo subdirectorio y accesibilidad visual. Inspeccionar únicamente dist/ para asegurar ausencia de CSV de datos, modelos y predicciones. Comprobar fuentes intactas sin acceder al test. Aceptación: reporte de revisión y autorización solicitada antes de cualquier publicación.

Pruebas propuestas: fuente en memoria vs JSON (LSP), selector que no mezcla protocolos, ausencia de métrica distinta de cero no rellenada artificialmente, texto de unidades e intervalos, integridad de activos copiados y recorrido manual del sitio. Los dobles de prueba se identifican como fixtures y no se distribuyen como resultados. No ejecutar suites históricas que entrenen o evalúen para validar el frontend.

## Dictamen

Existe evidencia suficiente para implementar una presentación académica estática sin tocar datos ni modelos. El trabajo pendiente es seleccionar, estructurar y presentar resultados ya obtenidos. Se recomienda aprobar Vite + TypeScript sin framework de interfaz, catálogo público reducido, gráficas existentes y navegación narrativa con métodos numéricos al final. Esta tarea termina en planificación; implementación y publicación quedan pendientes de autorización.
