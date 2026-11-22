# Verificación de enlaces documentales

Se encontraron 18 fuentes únicas en 23 referencias de 14 bloques documentales. Las 18 se presentan como enlaces descriptivos a sus rutas exactas en la rama main, sin mostrar rutas técnicas como texto del enlace. Se conservan details/summary, clase visual fuente, target=_blank, rel=noopener noreferrer y aviso accesible de nueva pestaña.

Se activaron individualmente los 18 enlaces desde la aplicación local en Chromium real. Los 18 abrieron una pestaña nueva hacia la URL esperada; 16 mostraron el archivo correcto. Los dos informes numéricos no están publicados en main: página File not found y contenido raw HTTP 404. No se inventó una ruta alternativa ni se publicó ningún archivo. Dos respuestas transitorias Unicorn de GitHub se reintentaron desde la aplicación y después mostraron los documentos correctos.

Archivo de implementación: src/componentes/evidencia.ts. Mapeo explícito de títulos únicamente para las fuentes realmente utilizadas. Otras referencias no incluidas en esta lista conservan su presentación previa.

npm test: 25 aprobadas, 0 fallidas, 0 omitidas. npm run build: correcto. Evidencia individual: verificacion_navegador/fuentes_documentales.json.

| Fuente exacta | Resultado |
|---|---|
| docs/PROCEDENCIA_Y_LICENCIAS.md | Documento verificado desde aplicación local |
| INFORME_CORRECCION_TARGET_FASE03.md | Documento verificado desde aplicación local |
| INFORME_PARTICION_FASE04.md | Documento verificado desde aplicación local |
| INFORME_PREPROCESAMIENTO_FASE04.md | Documento verificado desde aplicación local |
| INFORME_REVISION_IMPOSSIBLE_TRAVEL_FASE04.md | Documento verificado desde aplicación local |
| INFORME_MODELADO_SUPERVISADO_FASE04.md | Documento verificado desde aplicación local |
| INFORME_SEGUNDA_VALIDACION_FASE04.md | Documento verificado desde aplicación local |
| INFORME_VALIDACION_ANIDADA_FASE04.md | Documento verificado desde aplicación local |
| INFORME_DECISION_MODELO_FASE04.md | Documento verificado desde aplicación local |
| fase04_modelado/mejora_controlada/ajuste.py | Documento verificado desde aplicación local |
| fase04_modelado/mejora_controlada/contratos.py | Documento verificado desde aplicación local |
| INFORME_CLUSTERING_FASE04.md | Documento verificado desde aplicación local |
| fase04_clustering/ejecutar.py | Documento verificado desde aplicación local |
| fase04_modelado/recuperacion_referencia_v1_20261122/INFORME_RECUPERACION_TECNICA_FASE04.md | Documento verificado desde aplicación local |
| fase04_modelado/evaluacion_final_test_20261122/INFORME_EVALUACION_FINAL_TEST_FASE04.md | Documento verificado desde aplicación local |
| INFORME_DIAGNOSTICO_CAPACIDAD_PREDICTIVA_FASE04.md | Documento verificado desde aplicación local |
| fase04_metodos_numericos/resultados/INFORME_REGRESION_INTERPOLACION_FASE04.md | No publicado en main; GitHub 404 |
| fase04_metodos_numericos/revision_complementaria/INFORME_REVISION_COMPLEMENTARIA.md | No publicado en main; GitHub 404 |

Pendiente: publicar los dos informes numéricos mediante un procedimiento autorizado independiente para que sus enlaces exactos puedan resolver. Esta tarea no incluye commit, push ni despliegue. No se modificaron documentos originales, catálogo, figuras, resultados o artefactos congelados ni se accedió al test.
