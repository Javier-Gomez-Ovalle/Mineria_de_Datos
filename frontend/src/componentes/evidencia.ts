import type { CatalogoResultados, FiguraHistorica, ResultadoAgregado } from '../datos/contratos.js';
import { escapar_html as e } from './estructura.js';
import { nombres_modelos } from '../presentacion/consulta.js';

const titulos_documentales: Record<string,string> = {
  'docs/PROCEDENCIA_Y_LICENCIAS.md':'fuentes documentales, procedencia y licencias',
  'INFORME_CLUSTERING_FASE04.md':'análisis de clustering',
  'INFORME_CORRECCION_TARGET_FASE03.md':'corrección y reconciliación del target ATO',
  'INFORME_DECISION_MODELO_FASE04.md':'decisión sobre el modelo de referencia',
  'INFORME_DIAGNOSTICO_CAPACIDAD_PREDICTIVA_FASE04.md':'diagnóstico de capacidad predictiva',
  'INFORME_MODELADO_SUPERVISADO_FASE04.md':'modelado supervisado y primera validación cruzada',
  'INFORME_PARTICION_FASE04.md':'partición de entrenamiento y prueba por usuario',
  'INFORME_PREPROCESAMIENTO_FASE04.md':'preprocesamiento y selección de predictores',
  'INFORME_REVISION_IMPOSSIBLE_TRAVEL_FASE04.md':'revisión de la señal Impossible Travel',
  'INFORME_SEGUNDA_VALIDACION_FASE04.md':'segunda validación cruzada por usuario',
  'INFORME_VALIDACION_ANIDADA_FASE04.md':'validación anidada y selección interna',
  'fase04_clustering/ejecutar.py':'código de ejecución del análisis de clustering',
  'fase04_metodos_numericos/resultados/INFORME_REGRESION_INTERPOLACION_FASE04.md':'informe de regresión lineal e interpolación',
  'fase04_metodos_numericos/revision_complementaria/INFORME_REVISION_COMPLEMENTARIA.md':'revisión complementaria y sensibilidad de la regresión',
  'fase04_modelado/evaluacion_final_test_20261122/INFORME_EVALUACION_FINAL_TEST_FASE04.md':'informe de evaluación final documentada',
  'fase04_modelado/mejora_controlada/ajuste.py':'código de ajuste de Random Forest',
  'fase04_modelado/mejora_controlada/contratos.py':'contratos y configuraciones de la extensión controlada',
  'fase04_modelado/recuperacion_referencia_v1_20261122/INFORME_RECUPERACION_TECNICA_FASE04.md':'recuperación técnica del modelo de referencia',
};

export function formato(valor:unknown, digitos=6): string {
  if(valor===undefined || valor===null) return 'No informada';
  if(typeof valor==='number') return new Intl.NumberFormat('es-CO',{maximumFractionDigits:digitos}).format(valor);
  return e(String(valor));
}
export function fuente(ruta:string): string {
  if (Object.hasOwn(titulos_documentales,ruta)) {
    const versiones_publicas: Record<string,string> = {
      'fase04_metodos_numericos/resultados/INFORME_REGRESION_INTERPOLACION_FASE04.md':'docs/publicacion/REGRESION_INTERPOLACION.md',
      'fase04_metodos_numericos/revision_complementaria/INFORME_REVISION_COMPLEMENTARIA.md':'docs/publicacion/SENSIBILIDAD_NUMERICA.md',
    };
    const destino=versiones_publicas[ruta]??ruta;
    const url='https://github.com/Javier-Gomez-Ovalle/Mineria_de_Datos/blob/main/'+destino.split('/').map(encodeURIComponent).join('/');
    return `<a class="fuente" href="${url}" target="_blank" rel="noopener noreferrer">Consultar ${e(titulos_documentales[ruta])}${versiones_publicas[ruta]?' (versión pública sin registros individuales)':''} <span aria-hidden="true">↗</span><span class="solo_lector"> (abre en una pestaña nueva)</span></a>`;
  }
  return `<span class="fuente">${e(ruta)}</span>`;
}
export function bloque(catalogo:CatalogoResultados,id:string):string {
  const documento=catalogo.documentacion.find(d=>d.id===id);
  if(!documento) return vacio('No hay documentación autorizada disponible para este apartado.');
  return `<article class="bloque_documental"><h2>${e(documento.titulo)}</h2><p>${e(documento.texto)}</p><details class="procedencia"><summary>Fuentes documentales</summary>${documento.fuentes.map(f=>`<p>${fuente(f)}</p>`).join('')}</details></article>`;
}
export function vacio(mensaje:string): string {return `<div class="estado_vacio" role="status"><strong>Sin resultados para esta selección</strong><p>${e(mensaje)}</p></div>`;}
export function selector(campo:string,titulo:string,opciones:Record<string,string>,actual:string):string {
  return `<label class="control" for="filtro_${campo}">${e(titulo)}<select id="filtro_${campo}" data-campo="${campo}">${Object.entries(opciones).map(([valor,etiqueta])=>`<option value="${e(valor)}"${valor===actual?' selected':''}>${e(etiqueta)}</option>`).join('')}</select></label>`;
}
export function tabla(titulo:string, columnas:[string,string][],filas:Record<string,unknown>[]): string {
  if(!filas.length) return vacio('No se han documentado filas para este ámbito. Cambia los filtros para consultar otra evidencia.');
  return `<div class="tabla_desplazable" role="region" aria-label="${e(titulo)}" tabindex="0"><table><caption>${e(titulo)}</caption><thead><tr>${columnas.map(([,t])=>`<th scope="col">${e(t)}</th>`).join('')}</tr></thead><tbody>${filas.map(f=>`<tr>${columnas.map(([k],i)=>`<${i===0?'th scope="row"':'td'} title="${e(String(f[k]??'No informada'))}">${formato(k==='modelo'?nombres_modelos[String(f[k])]??f[k]:f[k])}</${i===0?'th':'td'}>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
export const columnas_metricas:[string,string][]=[['modelo','Procedimiento'],['tp','TP (eventos)'],['fp','FP (eventos)'],['tn','TN (eventos)'],['fn','FN (eventos)'],['precision','Precision'],['recall','Recall'],['f1','F1'],['average_precision','AP']];
export function tabla_resultados(filas:ResultadoAgregado[],titulo:string,fold=false):string {
  const columnas=[...columnas_metricas]; if(fold) columnas.splice(1,0,['fold_visible','Fold']);
  return tabla(titulo,columnas,filas.map(f=>({...f.valores,fold_visible:f.valores.fold??f.valores.fold_externo})))+
    `<p class="nota_tabla">Tasas en escala 0–1; AP es Average Precision. «No informada» no equivale a cero. Valores redondeados solo para lectura; pasa sobre una celda para ver el valor original. Desplaza horizontalmente para consultar todas las columnas.</p>`;
}
export function matriz(fila:ResultadoAgregado,titulo:string):string {
  const v=fila.valores;
  return `<section class="matriz"><h3>${e(titulo)}</h3><table><caption>Conteos absolutos en eventos</caption><thead><tr><th scope="col">Real / predicción</th><th scope="col">No ATO</th><th scope="col">ATO</th></tr></thead><tbody><tr><th scope="row">No ATO</th><td>TN ${formato(v.tn)}</td><td class="error_matriz">FP ${formato(v.fp)}</td></tr><tr><th scope="row">ATO</th><td class="error_matriz">FN ${formato(v.fn)}</td><td>TP ${formato(v.tp)}</td></tr></tbody></table></section>`;
}
export function figura(f:FiguraHistorica):string {
  return `<figure class="figura"><button class="ampliar_figura" data-figura="${e(f.id)}" aria-label="Ampliar: ${e(f.titulo)}"><img src="./${e(f.url)}" width="${f.ancho}" height="${f.alto}" loading="lazy" decoding="async" alt="${e(f.titulo+'. '+f.descripcion)}"><span>Ampliar figura</span></button><figcaption><strong>${e(f.titulo)}</strong><p>${e(f.descripcion)}</p><details class="procedencia"><summary>Fuente de la figura</summary>${fuente(f.fuente)}</details></figcaption></figure>`;
}
export function galeria(figuras:FiguraHistorica[]):string {
  if(!figuras.length) return vacio('No hay una figura histórica específica para estos filtros; la tabla conserva los resultados disponibles.');
  return `<div class="galeria">${figuras.map(figura).join('')}</div>`;
}
