# Auditoría inicial de entrega final

Rama main, HEAD 17e2c72; remoto GitHub Javier-Gomez-Ovalle/Mineria_de_Datos. Cambios previos: .gitignore, frontend/, métodos numéricos y documentación Fase 5. No se descartan ni sobrescriben. Fase 3, preparación y resultados históricos se mantienen intactos.

Frontend Vite/TypeScript con catálogo agregado y 58 figuras. Pruebas de contrato, equivalencia, integridad e integración y navegador disponibles. Guion aprobado: 12 diapositivas, 540 segundos. Excluir node_modules, dist intermedio, .tests, cachés, herramientas locales, capturas/diagnósticos con rutas del equipo, CSV de eventos, predicciones y archivos test. Solo se publicará una lista explícita.

CSV inventariados en INVENTARIO_CSV.json. Los archivos test y los conjuntos que pueden contener sus usuarios se excluyen antes de abrirlos o calcular hashes; su estructura/tamaño se dejan sin inspeccionar. Para los demás se leyeron únicamente cabeceras y metadatos. Los recursos CSV de esta entrega serán proyecciones de resultados agregados ya existentes, no datasets ni una supuesta anonimización.

Hallazgo preexistente: main ya rastrea dataset_train_fase04.csv, empleados.csv y tablas por usuario. No se vuelven a copiar al sitio público. No se reescribe historia ni se eliminan archivos físicos. La restricción de esta entrega no equivale a retirar las publicaciones históricas, que requieren una decisión separada si se desea eliminarlas del remoto.

Destino previsto: GitHub Pages estático con rutas relativas, documentación fuente en main y CSV agregados descargables. Sin backend de inferencia ni base de datos operativa: no son necesarios para consultar la evidencia y no se inventará su despliegue. Límites consultados en documentación oficial: sitio 1 GB, ancho de banda orientativo 100 GB/mes; Git bloquea archivos mayores de 100 MiB. Se comprobará el tamaño final; no se justifica LFS ni almacenamiento externo.

La herramienta de presentaciones disponible no expone creación/exportación de Spaces ni runtime Artifact Tool en esta sesión. Se generará un PPTX local reproducible para el repositorio y se validará con un renderizador disponible, manteniendo el guion y la identidad visual aprobados.

Referencias: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits y https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
