# Integración de datasets en Hugging Face

Fecha: 22 de noviembre de 2026. Implementación y verificación locales; sin commit, push ni despliegue.

## Funcionalidad y arquitectura

La nueva ruta `#datasets`, «Datasets y exploración de datos», se incorpora al índice existente. Métodos numéricos permanece al final del recorrido. Se muestran las cifras autorizadas del entrenamiento: 46.305 registros, 1.600 usuarios, 35 columnas y 36 eventos ATO.

`src/datos/recursos_datasets.ts` centraliza las referencias públicas tipadas y la revisión `f58b487642da42fd591f4e37a1c558a0804812c8`. `src/presentacion/datasets.ts` genera la vista; `src/datasets.css` limita los estilos a esta sección. Se reutilizan el escape de HTML, la navegación y la inicialización existentes. No se modifica el catálogo ni su contrato, ni se añaden dependencias.

El iframe utiliza el [formato oficial de Hugging Face](https://huggingface.co/docs/hub/datasets-viewer-embed), con configuración `train_definitivo` y split `train`. Tiene altura de 560 px en escritorio y 500 px en móvil. La aplicación no solicita el CSV completo ni incorpora registros a su catálogo; el proveedor gestiona la consulta dentro del iframe remoto.

Los ocho enlaces incluyen visor, descarga CSV, portada/documentación, diccionario, procedencia, licencias, manifiesto y SHA256SUMS. Los archivos y documentos apuntan a la revisión autorizada; portada y visor apuntan a la versión vigente. Se evita duplicar el contenido documental en la aplicación.

El enlace externo permanece visible incluso si falla la inserción. No se declara automáticamente éxito a partir del evento `load`: las restricciones entre dominios impiden detectar de forma fiable todos los errores del proveedor. Los enlaces abren una pestaña nueva con `noopener noreferrer` y una indicación accesible.

## Archivos

- Nuevos: `src/datos/recursos_datasets.ts`, `src/presentacion/datasets.ts`, `src/datasets.css`, `tests/datasets_navegador.test.mjs` y este informe.
- Modificados: `src/main.ts`, `src/presentacion/secciones.ts`, `src/presentacion/vistas.ts`, `tests/presentacion.test.mjs`, `tests/integracion.test.mjs`, `tests/navegador.test.mjs` y `README.md`.
- Generados localmente: build `dist/`, compilación de pruebas `.tests/` y evidencias en `verificacion_navegador/` (no destinadas al contenido publicado).

## Verificaciones ejecutadas

| Comprobación | Resultado final |
|---|---|
| `npm test` | 27 aprobadas, 0 fallidas, 0 omitidas |
| `python -B -m unittest discover -s tests -p 'test_*.py' -v` | 9 aprobadas, 0 fallidas, 0 omitidas; equivalencia de fuentes agregadas y 58 figuras |
| `npm run build` | Correcto; TypeScript y Vite |
| `node --test tests/datasets_navegador.test.mjs` | 6 aprobadas (5 comprobaciones y su contenedor), 0 fallidas, 0 omitidas |
| `node --test tests/navegador.test.mjs` | 8 aprobadas (7 comprobaciones y su contenedor), 0 fallidas, 0 omitidas |

Chromium real verificó la navegación local, contenido visible del iframe, escritorio de 1440 × 1000, móvil de 390 × 844 y ausencia de desbordamiento horizontal de la página. El visor conserva su desplazamiento interno para recorrer las columnas. Se revisaron visualmente las capturas.

Los ocho destinos respondieron HTTP 200 mediante HEAD, sin descargar el CSV. Se comprobó que las URL renderizadas coinciden con las referencias definidas. El bloqueo simulado de la petición del iframe mantiene la alternativa visible; al activarla con Enter se abre el visor correcto. El build se sirvió bajo `/Mineria_de_Datos/` y cargó catálogo, recursos y sección sin errores JavaScript. Las seis secciones anteriores, filtros, imágenes y recuperación de errores también pasaron la comprobación real.

En la primera ejecución fallaron dos pruebas por depender de la antigua posición numérica de Métodos numéricos: ahora lo localizan por su identificador estable. La prueba histórica de navegador tenía comprobaciones anticipadas al evento de navegación; se añadieron esperas por el estado activo y el cierre del menú. Se ejecutaron nuevamente y pasaron. No se cambió el comportamiento de esas vistas.

Evidencias locales:

- `verificacion_navegador/datasets_escritorio.png`
- `verificacion_navegador/datasets_movil.png`
- `verificacion_navegador/datasets_verificacion.json` (URL y estado de los ocho enlaces, sin registros individuales).

Para repetir las pruebas de navegador, definir `PLAYWRIGHT_CORE` y `CHROMIUM_PATH` con las rutas de las instalaciones disponibles. `ATO_URL` es opcional; por defecto utiliza `http://127.0.0.1:5173/`. Ejecutar antes `npm test` y `npm run build`.

## Alcance y límites

Vista local: `http://127.0.0.1:5173/#datasets`. Inicio: `npm run dev -- --host 127.0.0.1`, desde `frontend/`.

La disponibilidad futura del iframe depende de Hugging Face y del navegador del visitante. El respaldo externo es permanente. La nueva sección todavía no está publicada en GitHub Pages; su compatibilidad se verificó localmente bajo la misma subruta. La publicación requerirá una etapa posterior autorizada.

No se accedió al dataset test ni a sus predicciones. No se modificaron CSV, revisión de Hugging Face, modelos, umbrales, resultados históricos, Fase 3, métodos numéricos ni presentación.
