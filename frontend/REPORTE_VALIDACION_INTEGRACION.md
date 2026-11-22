# Validación pendiente completada: pruebas e integración

Estado: validación automatizada aprobada; revisión visual manual pendiente. No se declara cierre visual de la aplicación.

## Ejecuciones reales

Primera repetición solicitada: npm test 18/18 y Python 6/6, sin fallos u omisiones; npm run build correcto. La prueba de presentación corregida se ejecutó y pasó, no se dio por válida mediante inspección de su código.

Después de ampliar las comprobaciones y completar el selector de fold individual se repitieron las pruebas y la compilación:

| Comando desde frontend/ | Aprobadas | Fallidas | Omitidas |
|---|---:|---:|---:|
| npm test | 25 | 0 | 0 |
| python -B -m unittest discover -s tests -p test_contenido.py -v | 8 | 0 | 0 |
| Total de pruebas finales | 33 | 0 | 0 |

`npm run build`: correcto, TypeScript y Vite sin errores. La compilación no se cuenta como prueba adicional. Cero pruebas canceladas. Los totales de las ejecuciones inicial y final no se suman, porque repiten pruebas.

## Integración comprobada

- Las seis vistas generan HTML completo usando el catálogo real, sin excepciones, valores undefined/NaN ni mensajes predeterminados de carga fallida o contenido pendiente.
- Combinaciones de protocolo, modelo, regla, ámbito y fold contrastadas contra las filas originales del catálogo. Selección de un modelo y un fold devuelve una fila por regla/protocolo. El cambio de protocolo restablece un modelo incompatible y los valores de filtro inválidos se rechazan.
- Antes de esta revisión existía el ámbito «Resultados por fold», pero no un selector individual. Se incorporó Fold 1–5/Todos y se ejecutaron pruebas de esa funcionalidad. No se recalculó ninguna métrica.
- Las celdas de las tablas conservan los valores originales en su atributo title y presentan redondeo únicamente para lectura. AP ausente permanece «No informada», no cero. Conteos y métricas coinciden con el catálogo y este con sus fuentes CSV/JSON/Markdown autorizadas.
- Las 58 figuras tienen 58 IDs, 58 URLs y 58 fuentes distintas; no existen duplicados binarios. Copias públicas y de dist coinciden byte a byte con los originales. Se verificaron hashes, dimensiones PNG, estructura y CRC de sus bloques. No se regeneraron ni editaron figuras históricas.
- Etiquetado comprobado por carpeta de protocolo, modelo en nombre de matriz y regla: las figuras de extensión RF corresponden a reglas aprendidas. Las figuras anidadas muestran ambas reglas expresamente; cambiar el ámbito de una tabla no convierte una matriz global en una matriz de fold. Las 58 figuras son alcanzables desde sus vistas y filtros pertinentes.
- 65 rutas HTTP locales respondieron 200: entrada, catálogo, módulos/estilos seleccionados y 58 figuras. Los bytes HTTP del catálogo y las imágenes coinciden con public/.
- Estados vacíos y errores diferenciados: sin filas/figuras autorizadas se muestra un mensaje informativo; el fallo real de fuente usa role=alert y Reintentar carga. El repositorio tiene pruebas de carga válida, error HTTP y respuesta incompatible.

Estas comprobaciones prueban funciones de presentación/consulta, contrato y transporte HTTP. No certifican por sí solas ejecución de eventos DOM, diseño responsive o interacción real en un navegador.

## Metodología y unidades

CV1, CV2, anidada, extensión RF, selección OOF y evaluación final documentada permanecen separadas. AP es Average Precision, no accuracy; métricas de clasificación 0–1 y conteos en eventos. Intervalos entre accesos en horas; cómputo en segundos. Regresión: distancia en km, velocidad/intercepto/RMSE en km/h, pendiente en h⁻¹, MSE en (km/h)². Principal y sensibilidad tienen poblaciones separadas. Interpolación conserva coeficientes e intervalo, sin extrapolación.

Ward es el procedimiento jerárquico principal y Average un contraste; clustering no se presenta como clasificación supervisada. El árbol ponderado se describe como referencia, no ganador robusto ni detector productivo. Las figuras conservan títulos, ejes, escalas y leyendas históricas. Su legibilidad al tamaño real de pantalla sigue pendiente de revisión visual.

## Protección y alcance de la confirmación

La superficie public/ contiene exactamente el catálogo agregado y las 58 imágenes autorizadas. No contiene CSV, joblib, datasets, registros tabulares individuales, predicciones individuales ni claves de eventos. Se verificaron campos restringidos, ausencia de direcciones IPv4 en el JSON, listas explícitas de fuentes/campos y rechazo de rutas no autorizadas antes de abrirlas. Las fuentes autorizadas permanecieron idénticas por hash antes/después de las verificaciones.

No se abrió, leyó, copió, procesó, hasheó ni evaluó el dataset test o sus predicciones. La tabla final contiene cifras agregadas transcritas del informe cerrado. No se recalcularon resultados ni se modificaron fuentes históricas, Fase 3, modelo, preprocesador, umbral o manifiestos.

**Salvedad sobre las figuras numéricas:** las imágenes históricas autorizadas de regresión/sensibilidad muestran puntos de dispersión y la de interpolación muestra tres nodos con coordenadas. Se conservan como evidencia gráfica solicitada, sin IDs ni exportación de registros subyacentes. No sería correcto certificar «ausencia absoluta de representaciones de observaciones» en esas imágenes. Si se pretende prohibir también esa representación visual, se necesita resolver ese alcance antes de publicar; esta validación no ha alterado las figuras para ocultarlo.

SHA-256 del catálogo verificado, sin regenerarlo en esta revisión:

`336798b8a1fb8125676811c6591c96d7c43c36fd80965a07de98acf163ae4546`

## Revisión manual local

Servidor local comprobado en http://127.0.0.1:5173/ y dejado disponible. No es despliegue. No se utilizó Computer Use ni Edge durante esta revisión.

Si el proceso ya no está activo, desde la raíz:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Si el puerto está ocupado por el servidor ya abierto, utilizar la dirección existente; no iniciar otra instancia. Para detener la instancia propia, Ctrl+C en su terminal.

Revisar manualmente:

1. Recorrer las seis secciones y usar atrás/adelante del navegador.
2. En Supervisados, cambiar protocolo, modelo, regla, ámbito y fold; comprobar las etiquetas y la tabla.
3. Ampliar/cerrar figuras, recorrer con Tab y cerrar el visor con Escape; comprobar legibilidad de ejes y leyendas.
4. En ancho móvil, abrir/cerrar el índice, verificar foco y desplazamiento horizontal de tablas sin desbordar la página.
5. Revisar contexto, objetivos, comparación final y las unidades de métodos numéricos.

No se generaron capturas: la comprobación visual fue dejada expresamente al usuario. No hay fallos automatizados pendientes. Pendientes reales: revisión visual/interactiva en navegador, confirmación editorial final y, si se exige una prohibición visual más amplia, la salvedad de los gráficos numéricos. Sin PPTX, entrenamiento, commit, push o despliegue.

## Cambios de esta revisión

Solo frontend: consulta.ts y analiticas.ts para fold individual; tests/integracion.test.mjs nuevo; test_contenido.py ampliado; package.json incorpora la suite nueva; README actualizado y este reporte. Compilados locales .tests/ y dist/ regenerados. Catálogo, figuras públicas y fuentes históricas no modificados.
