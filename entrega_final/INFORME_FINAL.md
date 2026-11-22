# Entrega académica pública ATO

Fecha: 22 de noviembre de 2026. Se publica una aplicación estática de consulta de evidencia académica; no un detector productivo, backend de inferencia o base de datos operativa.

## Acceso

- [Aplicación pública](https://javier-gomez-ovalle.github.io/Mineria_de_Datos/).
- [PowerPoint](https://javier-gomez-ovalle.github.io/Mineria_de_Datos/presentacion/ATO_PRESENTACION_ACADEMICA.pptx).
- [CSV agregados e inventario de descargas](https://javier-gomez-ovalle.github.io/Mineria_de_Datos/recursos.html).
- [Repositorio](https://github.com/Javier-Gomez-Ovalle/Mineria_de_Datos).
- [Guion aprobado](../docs/GUIÓN_PRESENTACION_ACADEMICA.md).
- [Procedencia y licencias](../docs/PROCEDENCIA_Y_LICENCIAS.md).

## Presentación

`ATO_PRESENTACION_ACADEMICA.pptx`: 12 diapositivas editables, 540 segundos (15, 35, 50, 55, 20, 45, 40, 40, 40, 40, 90, 70). Las notas incluyen las fuentes y el guion completo de cada diapositiva. Se renderizaron las 12 en Microsoft PowerPoint y se revisaron visualmente. La diapositiva 5 muestra Pages y los componentes realmente publicados. La 11 distingue comparación histórica, selección interna y evaluación final documentada. La 12 conserva regresión principal e interpolación, unidades e intervalo; el diagnóstico de 29 pares no sustituye a los 5.662 pares principales.

SHA-256 y validación estructural: `VALIDACION_PRESENTACION.json`. Copia pública idéntica en `frontend/public/presentacion/`. Las figuras originales se incorporan sin alterar sus bytes. No se genera información institucional que no esté confirmada.

Reproducción: instalar `requirements-presentacion.txt` en un entorno aislado y ejecutar desde la raíz `python -B entrega_final/generar_presentacion.py`. Requiere el catálogo público, el guion y las figuras autorizadas incluidos. `estado_despliegue.json` registra la URL comprobada. PowerPoint se utilizó únicamente como renderizador de la presentación nueva. La generación no ajusta modelos ni recalcula métricas; el empaquetado ZIP puede variar de hash entre ejecuciones.

## CSV y protección

`INVENTARIO_CSV.json` clasifica 114 CSV originales: 11 fuentes con proyección agregada autorizada y 103 excluidas de esta nueva distribución. Contiene rutas, procedencia, finalidad, cabeceras y tamaños disponibles, licencia/condición y justificación. Los archivos protegidos se excluyeron antes de abrirlos o hashearlos: sus campos desconocidos permanecen vacíos, no se inventaron.

Se ofrecen 15 CSV: CV1 y CV2 globales y por fold; validación anidada global y por fold; extensión RF global y por fold; candidatos de clustering y dos evaluaciones externas agregadas; selección interna del umbral; evaluación final ya documentada; regresión principal/sensibilidad; coeficientes e intervalo de interpolación. El manifiesto público `descargas/inventario.json` conserva filas, columnas, tamaños y SHA-256 de cada descarga. Los valores proceden del catálogo autorizado, sin volver a calcular métricas. El nombre `test_documentado` designa una tabla agregada del informe cerrado, nunca el dataset o sus predicciones.

No se publican nuevos datasets de eventos, índices individuales ni supuestas versiones anonimizadas. Los CSV no permiten reentrenar y no se presentan como sustitutos de los datos originales. No se inventa una licencia general para los resultados propios: se registra la autorización de publicación; las condiciones de RBA/IPinfo están en su documentación. Las imágenes históricas autorizadas conservan sus dispersiones y nodos, sin identificadores.

Hallazgo preexistente: `main` ya contenía train, empleados y tablas por usuario antes de esta entrega. No se vuelven a copiar a Pages ni se modifican o reescribe su historia. Por ello, no se certifica que todo el historial del repositorio esté libre de registros individuales. Retirar esa exposición histórica requiere una decisión y operación separadas. El test y sus predicciones no fueron abiertos, procesados, copiados, hasheados ni publicados en esta ejecución.

## Implementación y verificaciones

- Vite con base relativa, compatible con `/Mineria_de_Datos/`; Pages publica únicamente el build estático desde `gh-pages`. Tamaño del build: 10.202.494 bytes, muy inferior al límite de 1 GB del sitio. Ningún archivo se acerca a 100 MiB; LFS no es necesario. Límites y referencias en `AUDITORIA_INICIAL.md`.
- 25 pruebas JavaScript aprobadas; 0 fallidas, 0 omitidas.
- 9 pruebas Python aprobadas; 0 fallidas, 0 omitidas. Incluyen equivalencia de fuentes, integridad de 58 figuras, guion y equivalencia exacta de 15 descargas con el catálogo.
- `npm run build`: aprobado.
- Chromium sobre la URL pública: 8 casos aprobados (prueba padre y 7 subpruebas), 0 fallos, 0 omisiones. Comprueba carga nativa, seis vistas, filtros, 58 imágenes, visor, móvil, fallo/reintento y ausencia de excepciones JavaScript.
- Verificación externa adicional: 1 prueba aprobada, 0 fallos y 0 omisiones. Se expandieron las fuentes en las seis secciones; los 18 destinos existen. Once respondieron HTTP 200 en la interfaz GitHub; siete se verificaron mediante su contenido público raw tras respuestas temporales 429/503. No se afirma que esos siete respondieran 200 en la interfaz durante esta comprobación. Se descargaron realmente los 15 CSV en Chromium y se verificaron tamaños y SHA-256; el PPTX público es idéntico a la copia validada. Pages informa build `47511f096014a9d1d967251fa92645c36dae4564` terminado sin errores.

La nueva prueba externa necesitó corregir selectores de desplegables anidados y esperar la vista activa. Tras esas correcciones se ejecutó y pasó; los fallos iniciales no se ocultaron ni se contabilizan como pruebas aprobadas.

No se usó el test para estas comprobaciones. Las pruebas de contenido consultan una lista explícita de informes y agregados autorizados.

## Incidencias resueltas y alcance

Se ajustó la base relativa para el subdirectorio de Pages y se mantuvo la corrección previa de `fetch` nativo. Dos informes numéricos contienen índices de filas; se preservan localmente y se enlazan resúmenes públicos nuevos y expresamente rotulados en `docs/publicacion/`, sin identificadores. No se sustituyeron las fuentes históricas ni se alteraron resultados.

Las pruebas de extracción histórica completa requieren el archivo académico local autorizado, que incluye material deliberadamente no redistribuido. La copia pública permite construir y probar el frontend con su catálogo incluido, exportar los agregados y reproducir la presentación. Esta distinción evita prometer reproducibilidad de experimentos sin sus datos. No se garantiza disponibilidad indefinida de Pages ni conformidad exhaustiva WCAG: se verificó accesibilidad básica, teclado y disposición móvil.

El árbol ponderado sigue siendo un procedimiento de referencia con rendimiento limitado. No se declara superioridad robusta ni capacidad clínica/productiva. No se entrenaron clasificadores ni se modificaron Fase 3, métricas, umbral, modelos o manifiestos congelados.

## Estado de publicación

Se publicó el contenido autorizado en main (`babe98d`) y el sitio en gh-pages (`47511f0`), sin force push ni reescritura. El cierre documental y la prueba externa corregida quedan en un commit posterior. La carpeta local preexistente `fase04_metodos_numericos/` permanece sin añadir; contiene material que no pertenece a la distribución pública. No se eliminaron archivos ni se incluyeron herramientas locales, cachés o credenciales.
