# Corrección del fallo real de carga

## Causa reproducida

El servidor Vite activo escuchaba en 127.0.0.1:5173 y su proceso ejecutaba el Vite de este directorio frontend. Se comprobó el módulo TypeScript transformado que servía, no solo el archivo en disco.

En Chromium aislado, al abrir http://127.0.0.1:5173/ apareció exactamente «El contenido no está disponible / No se pudo cargar o validar la fuente de resultados». Los módulos de la aplicación sí se descargaban, pero **no había ninguna solicitud al catálogo**.

Al invocar el repositorio real en el mismo navegador se obtuvo:

```text
TypeError: Failed to execute 'fetch' on 'Window': Illegal invocation
at RepositorioResultadosJson.cargar_catalogo
http://127.0.0.1:5173/src/datos/repositorio_resultados.ts:8:34
```

La línea corresponde al módulo transformado servido por Vite. En el archivo fuente, el constructor guardaba `fetch` directamente como propiedad `leer`; cargar_catalogo lo llamaba con `this.leer(this.url)`. El receptor de esa llamada era la instancia RepositorioResultadosJson. El fetch nativo de Chromium exige el receptor apropiado del navegador, por lo que rechazaba la invocación antes de emitir tráfico HTTP. La promesa rechazada quedaba capturada por AplicacionAcademica.cargar y se traducía al mensaje genérico; no aparecía como excepción no gestionada.

No era un problema del contenido JSON, del puerto, de rutas relativas ni de importaciones. El fallo se encontraba en el contexto de ejecución de fetch.

## Cambio mínimo

Archivo: src/datos/repositorio_resultados.ts, constructor de RepositorioResultadosJson.

```typescript
// Antes
private readonly leer: typeof fetch = fetch
// Después
private readonly leer: typeof fetch = (...argumentos) => globalThis.fetch(...argumentos)
```

Se conserva la inyección de una función de lectura para pruebas, pero el valor predeterminado llama a fetch sobre globalThis. No se modificaron inicialización, resultados, catálogo, figuras ni fuentes históricas para resolverlo.

## Por qué las pruebas anteriores no lo detectaron

Las pruebas del repositorio inyectaban funciones JavaScript que devolvían Response. Esas funciones no exigen el receptor Window. Las pruebas de vistas generaban HTML directamente, sin ejecutar el arranque completo con fetch nativo en navegador. Las comprobaciones HTTP solicitaban el JSON por separado, evitando la llamada defectuosa. Por tanto, pasar aquellas pruebas no demostraba que funcionara la aplicación abierta: el reporte anterior tenía ese límite y no debía interpretarse como validación del arranque real.

## Evidencia posterior en navegador real

Se utilizó Chromium headless ya instalado, en un proceso aislado y con Playwright Core existente. No se controló la ventana de Edge del usuario ni se usó Computer Use. No se instalaron dependencias ni se cambió el lockfile. Se ejecutó la aplicación real servida por Vite, con su JavaScript, DOM y peticiones de red.

- Arranque: GET /contenido/catalogo.json, respuesta 200 y contenido exactamente igual al catálogo autorizado. Se muestra el encabezado de contexto y no existe el botón Reintentar.
- Navegación real por clics: las seis secciones presentan contenido específico y aria-current correcto. Capturas en verificacion_navegador/.
- Filtros reales: protocolo anidada, árbol ponderado, resultados por fold y fold 3. Una fila visible; TP contrastado contra el catálogo.
- Las 58 imágenes se cargan y decodifican con dimensiones originales. Visor abierto por clic y cerrado con Escape.
- Móvil a 390 × 844: apertura del índice, navegación y cierre; sin desbordamiento horizontal del documento. Captura completa del contexto.
- Error controlado: se intercepta el catálogo con HTTP 503, aparece el mensaje de error, se restaura la respuesta real y Reintentar vuelve a presentar contexto.
- Cero excepciones JavaScript no gestionadas. El 503 registrado es exclusivamente el fallo inducido para comprobar recuperación.

Registro de solicitudes, respuestas y versión del navegador: verificacion_navegador/ejecucion.json. Capturas: contexto_escritorio.png, metodologia_escritorio.png, supervisados_escritorio.png, clustering_escritorio.png, comparacion_escritorio.png, metodos_numericos_escritorio.png y contexto_movil.png. Se inspeccionaron visualmente las capturas de contexto escritorio/móvil y supervisados. Las demás capturas y sus comprobaciones de contenido quedan disponibles; no se afirma una revisión exhaustiva de todos los píxeles o dispositivos.

## Pruebas ejecutadas después de corregir

| Ejecución | Aprobadas | Fallidas | Omitidas |
|---|---:|---:|---:|
| npm test | 25 | 0 | 0 |
| Python equivalencia/integridad | 8 | 0 | 0 |
| node --test tests/navegador.test.mjs | 8 | 0 | 0 |
| Total informado por los ejecutores | 41 | 0 | 0 |

La suite de navegador contiene siete subpruebas y una prueba contenedora, ambas contadas por node:test. npm run build pasó después del cambio. No se cuentan las repeticiones como pruebas adicionales.

Para repetir la prueba de navegador: configurar PLAYWRIGHT_CORE con la ruta al index.mjs de una instalación de playwright-core y CHROMIUM_PATH con el ejecutable Chromium disponible; mantener Vite en ejecución y ejecutar `node --test tests/navegador.test.mjs` desde frontend. ATO_URL permite indicar otra URL local. La suite falla si faltan esas herramientas; no las omite silenciosamente.

## Estado y límites

El fallo de carga está reproducido y corregido con evidencia de ejecución y renderizado reales. El servidor continúa en http://127.0.0.1:5173/. Recargar esa URL permite recibir el módulo corregido; Ctrl+F5 si la pestaña conserva el estado de error anterior.

No queda pendiente la comprobación básica de renderizado: se hizo en Chromium real y se revisaron capturas. Sí queda al usuario confirmar su pestaña/perfil concreto de Edge y realizar la revisión académica integral. No se accedió al test ni sus predicciones, no se modificaron figuras, métricas ni artefactos congelados, y no hubo entrenamiento, PPTX, commit, push o despliegue.
