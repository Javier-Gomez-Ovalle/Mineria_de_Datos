# Reporte de implementación inicial — Fase 5

Fecha: 22 de noviembre de 2026. Alcance terminado: guion para revisión y base documental/contrato de frontend. Sin PPTX, pantallas analíticas completas ni despliegue.

## Entregables

- docs/GUIÓN_PRESENTACION_ACADEMICA.md: exactamente 12 diapositivas, 540 segundos, estructura obligatoria, fuentes exactas, mensajes, cifras, visuales y explicaciones orales. Incluye tabla sección frontend ↔ diapositiva ↔ fuente.
- frontend/contenido/narrativa.json: objetivos originales de Fases 1–2, página 7, texto completo y SHA-256 de su fuente.
- frontend/scripts/fuentes_permitidas.json y preparar_contenido.py: lista explícita de fuentes/campos y extracción determinista.
- frontend/public/contenido/catalogo.json: 291 registros agregados, 180.213 bytes; no observaciones ni predicciones individuales.
- frontend/src/datos/contratos.ts: contratos y validación runtime.
- frontend/src/datos/repositorio_resultados.ts: FuenteResultados y RepositorioResultadosJson con lectura inyectable.
- frontend/src/main.ts e index.html: comprobación mínima de carga; no pantallas completas.
- frontend/package.json, package-lock.json, tsconfig.json, tsconfig.tests.json: base Vite + TypeScript reproducible.
- frontend/tests/contratos.test.mjs y test_contenido.py: contratos/equivalencia y trazabilidad.
- frontend/README.md: instrucciones y semántica de cada protocolo.

Solo se amplió .gitignore entre los archivos existentes: permite los entregables frontend y documentos de esta etapa; excluye node_modules, dist, .tests y cachés. Se preservó la modificación previa de métodos numéricos. El plan anterior queda intacto como historial: la secuencia definitiva es la del nuevo guion.

## Evidencia contenida

CV1/CV2 conservan seis variantes cada uno, métricas OOF, por fold, medias/desviaciones y tiempos disponibles. La validación anidada conserva 14 reglas/modelos globales y la extensión 18, más sus folds. Se añaden todos los candidatos de clustering y evaluaciones externas descriptivas por grupo, referencia OOF de selección, evaluación final documentada y ambos métodos numéricos.

Cada variante histórica permanece, incluso con F1 cero o falsas alarmas elevadas. Las métricas por fold no se confunden con las globales. AP ausente en selectores globales permanece ausente por mezcla de familias; nunca se rellena con cero. Regresión principal y sensibilidad son objetos separados; no se exportan los tres registros de interpolación, solo coeficientes e intervalo.

Los hashes de 16 fuentes documentales/agregadas están dentro de `fuentes`; no son hashes nuevos del test. El PDF original tiene su hash en narrativa. Las fuentes CSV son tablas de resultados, nunca datasets.

## Verificaciones ejecutadas

| Verificación | Resultado |
|---|---|
| npm test | 12 pruebas correctas |
| python -B -m unittest discover -s tests -p test_contenido.py -v, desde frontend | 6 pruebas correctas |
| npm run build | TypeScript estricto y compilación Vite correctos |
| Equivalencia | Cada campo público de cada fila agregada CSV coincide con su fuente |
| Métodos numéricos y referencia | Coeficientes/métricas/umbral iguales a JSON históricos, sin recalcular |
| Guion | Numeración 1–12, 540 s y objetivos originales completos comprobados |
| Reproducibilidad | Dos generaciones serializadas idénticas al catálogo guardado |
| Integridad | Fuentes permitidas con hashes idénticos antes/después de la extracción |
| Protección de lectura | Guardia de lista positiva; ruta test rechazada antes de cualquier apertura |
| Contrato runtime | Rechaza campos individuales, protocolo incompatible, duplicados, NaN, escala inválida, métrica faltante e intervalo invertido |
| Fuente JSON | Lector inyectado, error HTTP y respuesta incompatible verificados |
| Exclusiones Git | node_modules, dist y .tests efectivamente ignorados |

Node 20.19.5 / npm 11.17.0. Dependencias locales fijadas: Vite 7.2.2 y TypeScript 5.9.3. Compatibilidad Node consultada con npm view; instalación local con --ignore-scripts. pypdf se instaló exclusivamente en una carpeta temporal para leer documentación PDF original; no se cambió requirements ni se añadió dependencia Python al runtime. La preparación usa biblioteca estándar.

## Incidencias resueltas en código nuevo

La primera extracción rechazó filas Markdown por terminadores CRLF; se normalizan únicamente saltos de línea de la copia en memoria. No se modificó el informe histórico.

La primera validación runtime exigía AP también a selectores que deliberadamente no tienen AP global. Se permite su ausencia solo para los selectores identificados en ámbito OOF global. No se fabrica ningún valor. Todas las pruebas finales pasan.

## Confirmaciones académicas y límites

Los objetivos proceden del PDF original, no del resumen actualizado del README. La frase original sobre garantizar alta efectividad se conserva como intención: no se presenta como logro. Los cinco métodos principales tienen diapositiva propia; Random Forest se conserva como extensión comparativa en la 11 y con resultados completos en catálogo.

La evaluación cerrada reporta TP=1, FP=12, TN=11094, FN=8. Se transcribe documentación existente; no se accedió al dataset test, sus predicciones ni se calculó su hash. No se ejecutó ningún experimento o entrenamiento.

Se verificó lectura remota de main mediante git ls-remote: 17e2c72051092217aaea972fa08a8220207fa4d8. Esto acredita referencia GitHub, no aplicación web. No existe despliegue realizado por esta etapa.

Pendientes de confirmación editorial: autores, institución/asignatura y fecha final de sustentación. La edición exacta del catálogo IPinfo sigue sin acreditarse según docs/PROCEDENCIA_Y_LICENCIAS.md; no se inventa fecha o versión. El tiempo se basa en asignación de 540 segundos; deberá ensayarse oralmente. Las figuras referenciadas se componen y revisan a tamaño de diapositiva solo al autorizar el PPTX. No se afirma una revisión visual del PPT inexistente.

No se copiaron figuras ni resultados individuales a public; la única salida pública preparada es el catálogo reducido. No se tocaron datasets, código de Fase 3, resultados históricos, modelo, preprocesador, umbral o manifiestos congelados. No hubo commit, push ni despliegue. Se detiene la implementación para revisión del contenido y autorización de la siguiente etapa.
