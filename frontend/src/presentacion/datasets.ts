import { escapar_html } from '../componentes/estructura.js';
import { dataset_entrenamiento, recursos_dataset } from '../datos/recursos_datasets.js';

function enlace_externo(url: string, titulo: string, clase = ''): string {
  return `<a class="${clase}" href="${escapar_html(url)}" target="_blank" rel="noopener noreferrer">${escapar_html(titulo)} <span aria-hidden="true">↗</span><span class="solo_lector"> (abre en una pestaña nueva)</span></a>`;
}

export function renderizar_datasets(): string {
  const datos = dataset_entrenamiento;
  const formato = new Intl.NumberFormat('es-CO');
  return `<section class="dataset_resumen" aria-labelledby="titulo_dataset">
    <h2 id="titulo_dataset">Entrenamiento definitivo de Fase 4</h2>
    <p>Consulta los registros del conjunto de entrenamiento utilizado en el proyecto ATO. La publicación académica en Hugging Face reúne el CSV original, su versión Parquet, archivos complementarios de resultados y auditoría y la documentación de procedencia.</p>
    <dl class="dataset_cifras">${[[datos.registros,'Registros'],[datos.usuarios,'Usuarios'],[datos.columnas,'Columnas'],[datos.eventos_ato,'Eventos ATO']].map(([valor,etiqueta])=>`<div><dt>${etiqueta}</dt><dd>${formato.format(Number(valor))}</dd></div>`).join('')}</dl>
    <p>El visor muestra exclusivamente el conjunto de entrenamiento de Fase 4 (<code>train_definitivo / train</code>). Esta sección no incorpora el conjunto de test ni sus predicciones.</p>
  </section>
  <section class="dataset_exploracion" aria-labelledby="titulo_visor">
    <h2 id="titulo_visor">Explorar los datos en Hugging Face</h2>
    <p>El visor se carga desde Hugging Face. Puedes recorrer sus columnas y consultar los registros sin descargar el CSV completo en esta aplicación.</p>
    <div class="dataset_alternativa" id="alternativa_visor">
      ${enlace_externo(datos.visor,'Abrir el visor en Hugging Face','enlace_principal')}
      <p>Si el visor no aparece, tarda en cargar o tu navegador bloquea la inserción, utiliza este enlace para consultarlo directamente.</p>
    </div>
    <iframe class="dataset_visor" src="${datos.iframe}" title="Visor de Hugging Face: entrenamiento definitivo de Fase 4" aria-describedby="alternativa_visor" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" width="100%" height="560"></iframe>
  </section>
  <section class="dataset_recursos" aria-labelledby="titulo_recursos_dataset">
    <h2 id="titulo_recursos_dataset">Descarga, documentación y trazabilidad</h2>
    ${enlace_externo(datos.csv,'Descargar el CSV original de entrenamiento','enlace_principal')}
    <p>El CSV, el manifiesto, los hashes y los documentos enlazados están fijados a la revisión publicada. El visor y la portada de Hugging Face muestran la versión vigente del repositorio.</p>
    <ul>${recursos_dataset.map(recurso=>`<li>${enlace_externo(recurso.url,recurso.titulo)}</li>`).join('')}</ul>
    <p class="fuente">Revisión de los archivos: <code>${datos.revision}</code>. Consulta las condiciones de cada fuente antes de reutilizar los datos. Los resultados agregados y sus evidencias permanecen en las secciones analíticas de esta aplicación.</p>
  </section>`;
}
