# Estructura visual y navegación — Fase 5

## Alcance

Implementación exclusivamente dentro de frontend. No se modificó el catálogo, los contratos ni el repositorio de resultados. Sin dependencias adicionales, gráficas, pantallas analíticas completas, PPTX o despliegue. No se accedió a datasets ni predicciones de test.

## Diseño

Índice lateral de consulta académica y espacio principal de lectura. Paleta: azul #183d59, texto #20364a, fondo #f4f7fa, turquesa #126e70, líneas #d8e2e9 y blanco. Georgia para el titular, Segoe UI/Arial para lectura y controles, sin fuentes remotas. El protagonismo recae en la pregunta de autenticación; no en métricas decorativas o un dashboard operativo. El panel de contexto aporta jerarquía sin usar tarjetas idénticas para todo.

Escritorio: encabezado / índice lateral / contenido y pie. Móvil: encabezado / botón de secciones / contenido. Breakpoints de 1050 y 700 px; columnas colapsables, párrafos de ancho limitado y foco visible. Sin animación automática. No se inventan autores o datos institucionales.

## Arquitectura

- main.ts compone la aplicación con la fuente JSON existente.
- AplicacionAcademica coordina carga, navegación y eventos; depende de FuenteResultados, no del mecanismo concreto de lectura.
- secciones.ts declara destinos y resuelve fragmentos; vistas.ts presenta contexto y espacios de contenido futuro.
- estructura.ts reutiliza encabezado, navegación, pie y avisos; escapa valores de texto antes de insertarlos en HTML.
- estilos.css mantiene presentación separada. Contratos, datos y cálculos no se mezclan con los componentes.

Identificadores propios en snake_case y clases/interfaces PascalCase; API nativa de DOM sin renombrar. No se añadió framework ni enrutador externo.

## Funcionalidades

Seis destinos: contexto, metodología, supervisados, clustering, modelo de referencia y métodos numéricos. Fragmentos de URL, estado activo con aria-current, título de documento, foco tras navegación, enlaces anterior/siguiente y retorno al inicio. Menú móvil con aria-expanded y cierre mediante Escape. Enlace para saltar al contenido. Objetivos originales plegables; texto original recuperado del catálogo. Carga con aria-busy y error con reintento. Enlace externo GitHub con aviso de nueva pestaña y rel seguro.

Ward sigue siendo protagonista y Average contraste exploratorio. Árbol ponderado es procedimiento de referencia, sin garantía productiva. Las secciones pendientes se identifican expresamente; no se muestran resultados simulados.

## Archivos

Creados: src/aplicacion.ts, src/componentes/estructura.ts, src/presentacion/secciones.ts, src/presentacion/vistas.ts, src/estilos.css, tests/presentacion.test.mjs y este reporte.

Modificados: src/main.ts, index.html, tsconfig.tests.json, package.json y README.md. package-lock.json y las dependencias no cambiaron. dist/ y .tests/ se regeneran localmente y permanecen excluidos del seguimiento.

## Verificación y límites

Pruebas de contrato existentes, navegación declarativa, componentes, escape HTML, conservación de objetivos, rutas válidas, estados pendientes y recuperación de errores. Pruebas Python existentes de equivalencia, integridad y guion ejecutadas sin regenerar contenido. Compilación TypeScript/Vite correcta.

Resultados: `npm test`, 18/18 aprobadas (12 existentes y 6 nuevas); `python -B -m unittest discover -s tests -p test_contenido.py -v`, 6/6 aprobadas; `npm run build`, completado sin errores. Total: 24 pruebas aprobadas. El servidor local se detuvo después de la comprobación; para revisar manualmente, ejecutar `npm run dev` desde frontend.

Se inició Vite limitado a 127.0.0.1 para intentar inspección visual. La herramienta de navegador respondió «The browser access host is unavailable». Por ello no se entregan capturas ni se afirma validación visual real de escritorio/móvil. La adaptación está implementada en CSS, pero queda pendiente comprobarla en un navegador disponible, junto con interacción real de teclado, historial y menú móvil. Las pruebas unitarias no sustituyen esta revisión.

No hubo entrenamiento, experimentos, acceso al dataset test, modificación de evidencia congelada, commit, push ni despliegue. La siguiente etapa requiere revisión del usuario.
