# Base documental del frontend ATO

**Corrección de carga verificada en navegador:** consultar `REPORTE_CORRECCION_CARGA.md`. El fetch nativo se invoca sobre globalThis; el fallo Illegal invocation se reprodujo y corrigió. Hay capturas reales en `verificacion_navegador/` y una suite explícita `tests/navegador.test.mjs`. Los informes anteriores describen el estado previo a esta corrección.

Aplicación académica local con seis secciones, tablas, filtros y 58 figuras históricas. Sin despliegue ni servicio de inferencia. PowerPoint central: 12 diapositivas, 9 minutos previstos, máximo 10. Validación automatizada aprobada; revisión visual manual pendiente.

## Ejecutar

Node 20.19+ o 22.12+, npm y Python estándar. Desde esta carpeta:

```powershell
npm ci --ignore-scripts
python -B scripts/preparar_contenido.py
npm test
npm run build
python -B -m unittest discover -s tests -p test_contenido.py -v
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Vite 7.2.2 y TypeScript 5.9.3 fijados, con package-lock.json. La preparación requiere las fuentes históricas autorizadas del repositorio; el runtime solo necesita el catálogo generado. Python no requiere pandas, sklearn ni acceso a datasets. La extracción inicial de objetivos del PDF se hizo con pypdf en carpeta temporal; no es dependencia del generador.

## Responsabilidades

- `contenido/narrativa.json`: transcripción original de objetivos con página y hash del PDF, normalización de espacios documentada.
- `scripts/fuentes_permitidas.json`: archivos CSV agregados y campos públicos explícitos. Ninguna ruta de datasets ni predicciones.
- `scripts/preparar_contenido.py`: extracción determinista, sin cálculo de métricas ni importación de módulos experimentales. Rechaza fuentes no autorizadas y valores no finitos. Escribe el catálogo y copia las figuras de `scripts/figuras_permitidas.json` byte a byte a `public/figuras/`. Para revisar la aplicación existente no es necesario regenerarlos.
- `contenido/documentacion.json`: explicaciones editoriales con referencias explícitas a fuentes verificadas; sus hashes se incorporan al catálogo.
- `src/datos/contratos.ts`: contrato y validación runtime; rechaza campos individuales, protocolos mezclados, valores no finitos y métricas inválidas.
- `src/datos/repositorio_resultados.ts`: interfaz FuenteResultados y repositorio JSON con lector inyectable.
- `src/main.ts`: composición de AplicacionAcademica con FuenteResultados; carga de estilos.
- `src/aplicacion.ts`: coordina carga, navegación por fragmentos, foco, menú móvil y recuperación de errores. No calcula métricas.
- `src/componentes/estructura.ts`: encabezado, índice, pie, avisos y escape de texto.
- `src/presentacion/secciones.ts`: catálogo de navegación y resolución de rutas desconocidas hacia contexto.
- `src/presentacion/vistas.ts` y `analiticas.ts`: introducción y vistas completas, con protocolo, ámbito y procedencia visibles.
- `src/presentacion/consulta.ts`: filtros puros por protocolo, modelo, regla, ámbito y fold individual; no recalcula métricas.
- `src/componentes/evidencia.ts`: tablas, matrices documentadas, figuras, avisos y formato de lectura.
- `src/analiticas.css`: tablas desplazables, filtros, galerías y visor de figuras adaptable.
- `src/estilos.css`: identidad visual y adaptación a escritorio/móvil, foco visible y soporte de movimiento reducido.
- `tests/`: equivalencia de cada celda extraída, integridad y reproducibilidad; contrato positivo/negativo y errores de carga.

## Semántica

`cv1`, `cv2`, `anidada` y `extension_rf` separan protocolos. `oof_global` conserva métricas concatenadas; `fold` conserva el fold; sufijos `_media_folds`/`_sd_folds` son estadísticas históricas diferentes. `seleccion_referencia/seleccion_oof` no es evaluación independiente. `evaluacion_final_documentada/test_documentado` transcribe el informe cerrado; no lee el dataset test. `clustering` conserva todos los candidatos y evaluación externa descriptiva agregada, sin convertir grupos en clases.

En CSV, `fila_agregada` es el número de línea de una tabla de resultados (cabecera en 1), nunca un índice del dataset. En JSON/Markdown es 0; campos identificados en el script. El mapa `fuentes` almacena hashes de documentación/resultados agregados; no contiene un hash calculado del test. TP/FP/TN/FN pasan a snake_case; se preservan sus valores.

Los campos ausentes permanecen ausentes. AP no está informada para algunos selectores OOF globales por mezcla de familias; mostrar «no informada», jamás cero. Todos los modelos y variantes permanecen en las tablas, incluidos resultados desfavorables. Precisión numérica preservada al convertir representaciones decimales a IEEE-754; no se redondea en extracción.

El catálogo excluye registros individuales, identificadores, predicciones, modelos serializados y el voluminoso `frontend.json` de métodos numéricos. Para interpolación incluye coeficientes e intervalo, sin filas subyacentes. Se distribuyen 58 imágenes históricas autorizadas; las de métodos numéricos conservan puntos de dispersión y nodos como evidencia gráfica, sin identificadores. Véase la salvedad de alcance en `REPORTE_VALIDACION_INTEGRACION.md`. Las unidades están en el contrato documental: métricas de clasificación 0–1 y conteos en eventos. Las duraciones conservan la unidad especificada por cada variable; time_since_previous_login_hours utiliza horas y los tiempos de cómputo se expresan en segundos.

Fuente principal de narrativa y relación diapositiva/sección: `../docs/GUIÓN_PRESENTACION_ACADEMICA.md`. Alcance, incidencias y validaciones: `../docs/REPORTE_ETAPA_INICIAL_FASE05.md`. El plan original se conserva, con su secuencia reemplazada por las 12 diapositivas aprobadas.

La implementación visual posterior se documenta en `REPORTE_ESTRUCTURA_VISUAL.md`; el informe de etapa inicial se conserva como evidencia histórica. Para navegar se utilizan enlaces de fragmento (por ejemplo, `#clustering`), compatibles con acceso directo y el historial del navegador. En móvil, el botón Secciones abre/cierra el índice y Escape lo cierra. Los objetivos específicos se despliegan con un control nativo. La navegación actualiza título de documento, estado activo y foco del encabezado. Los errores de carga ofrecen Reintentar carga.

Publicar únicamente `dist/` en una etapa autorizada. No servir la raíz del repositorio: contiene material excluido del catálogo. El servidor de desarrollo no constituye un despliegue público.

Validación actual: `REPORTE_VALIDACION_INTEGRACION.md`. 25 pruebas JavaScript y 8 Python aprobadas, sin fallos ni omisiones; compilación correcta. La suite Python verifica también las copias en dist, por eso se ejecuta después de build. Dirección local: http://127.0.0.1:5173/. Los controles e imágenes requieren todavía inspección manual en navegador; no se han tomado capturas en esta revisión.

## Publicaci?n final (22 de noviembre de 2026)

Sitio: https://javier-gomez-ovalle.github.io/Mineria_de_Datos/ . Descargas: `recursos.html`. GitHub Pages sirve exclusivamente el build est?tico, con base relativa. No hay backend de inferencia.

Se conservan los reportes anteriores como hist?ricos. La revisi?n final ejecut? 25 pruebas JS, 9 Python y la prueba real de Chromium sobre la URL p?blica (8 casos, incluidos padre y 7 subcasos). El informe actualizado est? en `../entrega_final/INFORME_FINAL.md`.

Para una copia p?blica: `npm ci`, `npm test`, `npm run build` y `npm run dev`. El cat?logo y las figuras ya est?n incluidos: no es necesario regenerarlos. `python -B scripts/preparar_descargas.py` vuelve a exportar los 15 CSV agregados sin ajustar modelos. La extracci?n/equivalencia hist?rica completa requiere el archivo acad?mico local autorizado, cuyos informes num?ricos contienen referencias individuales y no se distribuyen. En la copia p?blica puede ejecutarse `python -B -m unittest discover -s tests -p test_descargas.py -v` sin ese archivo.

La generaci?n de PowerPoint se documenta en `../entrega_final/INFORME_FINAL.md`. Las dos fuentes de m?todos num?ricos enlazan res?menes p?blicos expresamente rotulados; no reemplazan los informes hist?ricos originales.

## Integración de Hugging Face

La ruta [`#datasets`](https://javier-gomez-ovalle.github.io/Mineria_de_Datos/#datasets) incorpora el visor remoto del entrenamiento y enlaces a sus archivos y documentación. No añade observaciones al catálogo local. Arquitectura, límites y validación previa a la publicación: [REPORTE_INTEGRACION_HUGGINGFACE.md](REPORTE_INTEGRACION_HUGGINGFACE.md). Las capturas y los registros de ejecución permanecen locales. El despliegue conserva GitHub Pages desde la raíz de `gh-pages`; en `main` se incluyen únicamente fuentes, pruebas y documentación de esta integración.
