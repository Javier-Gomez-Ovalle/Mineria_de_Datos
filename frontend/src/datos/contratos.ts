export type Protocolo = 'cv1' | 'cv2' | 'anidada' | 'extension_rf' | 'clustering' | 'evaluacion_final_documentada' | 'seleccion_referencia';
export interface ResultadoAgregado {
  protocolo: Protocolo;
  ambito: string;
  fuente: string;
  fila_agregada: number;
  valores: Record<string, number | string>;
}
export interface AjusteLineal {
  n: number; pendiente: number; intercepto: number; correlacion: number; r2: number; mse: number; rmse: number;
}
export interface BloqueDocumental {id: string; titulo: string; texto: string; fuentes: string[]}
export interface FiguraHistorica {
  id: string; protocolo: string; modelo: string; regla: string; fuente: string; titulo: string;
  descripcion: string; url: string; ancho: number; alto: number;
}
export interface CatalogoResultados {
  version_esquema: 1;
  narrativa: { fuente: string; pagina: number; sha256: string; normalizacion: string;
    objetivo_general: string; objetivos_especificos: string[]; alcance: string;
    despliegue: {repositorio: string; frontend: string} };
  resultados: ResultadoAgregado[];
  metodos_numericos: {regresion: AjusteLineal; sensibilidad: AjusteLineal;
    interpolacion: {coeficientes_x_ascendentes: number[]; intervalo_km: number[]; error_maximo_nodos_kmh: number};
    pares_cero: number; fuente_principal: string; fuente_sensibilidad: string; unidades: Record<string,string>};
  fuentes: Record<string,string>;
  advertencias: string[];
  documentacion: BloqueDocumental[];
  figuras: FiguraHistorica[];
}

function objeto(valor: unknown): asserts valor is Record<string, unknown> {
  if (!valor || typeof valor !== 'object' || Array.isArray(valor)) throw new Error('Objeto requerido');
}
function claves(valor: Record<string, unknown>, esperadas: string[]) {
  if (Object.keys(valor).sort().join('|') !== [...esperadas].sort().join('|')) throw new Error('Campos inesperados o ausentes');
}
function texto(valor: unknown): asserts valor is string {
  if (typeof valor !== 'string' || !valor.length) throw new Error('Texto requerido');
}
function numero(valor: unknown): asserts valor is number {
  if (typeof valor !== 'number' || !Number.isFinite(valor)) throw new Error('Número finito requerido');
}
function lista_texto(valor: unknown): asserts valor is string[] {
  if (!Array.isArray(valor) || !valor.length) throw new Error('Lista requerida');
  valor.forEach(texto);
}
export function validar_catalogo(valor: unknown): CatalogoResultados {
  objeto(valor);
  claves(valor,['version_esquema','narrativa','resultados','metodos_numericos','fuentes','advertencias','documentacion','figuras']);
  if (valor.version_esquema !== 1) throw new Error('Versión incompatible');
  objeto(valor.narrativa);
  claves(valor.narrativa,['fuente','pagina','sha256','normalizacion','objetivo_general','objetivos_especificos','alcance','despliegue']);
  for (const campo of ['fuente','sha256','normalizacion','objetivo_general','alcance']) texto(valor.narrativa[campo]);
  numero(valor.narrativa.pagina); lista_texto(valor.narrativa.objetivos_especificos);
  if (valor.narrativa.objetivos_especificos.length !== 4) throw new Error('Cuatro objetivos originales requeridos');
  objeto(valor.narrativa.despliegue); claves(valor.narrativa.despliegue,['repositorio','frontend']);
  Object.values(valor.narrativa.despliegue).forEach(texto);
  lista_texto(valor.advertencias); objeto(valor.fuentes);
  for (const hash of Object.values(valor.fuentes)) { texto(hash); if (!/^[a-f0-9]{64}$/.test(hash)) throw new Error('Hash inválido'); }
  const protocolos: Record<string, string[]> = {
    cv1:['oof_global','fold'],cv2:['oof_global','fold'],anidada:['oof_global','fold'],extension_rf:['oof_global','fold'],
    clustering:['candidatos','evaluacion_externa_kmeans_2','evaluacion_externa_ward_2'], evaluacion_final_documentada:['test_documentado'], seleccion_referencia:['seleccion_oof']};
  const campos = new Set(['modelo','regla','fold','fold_externo','tp','fp','tn','fn','precision','recall','f1','average_precision','umbral',
    'preprocesamiento_s','sobremuestreo_s','entrenamiento_s','prediccion_s','algoritmo','k','cluster','eventos','eventos_ato','eventos_no_ato','prevalencia',
    'usuarios','usuarios_con_ato','silhouette','davies_bouldin','calinski_harabasz','ari_min','ari_media','minimo','maximo','inercia','segundos',
    'roc_auc','f2','especificidad','fpr','alertas',
    ...['precision','recall','f1','average_precision'].flatMap(m=>['media','sd'].map(s=>m+'_'+s+'_folds'))]);
  if (!Array.isArray(valor.resultados) || !valor.resultados.length) throw new Error('Resultados requeridos');
  const identidades = new Set<string>();
  for (const fila of valor.resultados) {
    objeto(fila); claves(fila,['protocolo','ambito','fuente','fila_agregada','valores']);
    texto(fila.protocolo); texto(fila.ambito); texto(fila.fuente); numero(fila.fila_agregada);
    if (!protocolos[fila.protocolo]?.includes(fila.ambito) || !valor.fuentes[fila.fuente]) throw new Error('Procedencia incompatible');
    const id = fila.fuente+':'+fila.fila_agregada;
    if (identidades.has(id)) throw new Error('Resultado duplicado'); identidades.add(id);
    objeto(fila.valores);
    for (const [campo,dato] of Object.entries(fila.valores)) {
      if (!campos.has(campo)) throw new Error('Campo no público');
      if (['modelo','regla','algoritmo'].includes(campo)) texto(dato); else numero(dato);
      if (['precision','recall','f1','average_precision'].includes(campo) && (Number(dato)<0 || Number(dato)>1)) throw new Error('Métrica fuera de escala');
    }
    if (fila.protocolo !== 'clustering') for (const campo of ['tp','fp','tn','fn','precision','recall','f1','average_precision']) {
      // Selectores globales históricos no publican AP; ausencia no equivale a cero.
      if (campo === 'average_precision' && !(campo in fila.valores) && fila.ambito === 'oof_global' &&
          ['selector_conjunto','selector_historico','selector_ampliado'].includes(String(fila.valores.modelo))) continue;
      numero(fila.valores[campo]);
      if (['tp','fp','tn','fn'].includes(campo) && (!Number.isInteger(fila.valores[campo]) || Number(fila.valores[campo])<0)) throw new Error('Conteo inválido');
    }
    if (fila.ambito === 'fold' && !('fold' in fila.valores || 'fold_externo' in fila.valores)) throw new Error('Falta fold');
  }
  objeto(valor.metodos_numericos);
  claves(valor.metodos_numericos,['regresion','sensibilidad','interpolacion','pares_cero','fuente_principal','fuente_sensibilidad','unidades']);
  for (const campo of ['regresion','sensibilidad']) {
    const ajuste=valor.metodos_numericos[campo]; objeto(ajuste);
    claves(ajuste,['n','pendiente','intercepto','correlacion','r2','mse','rmse']); Object.values(ajuste).forEach(numero);
  }
  numero(valor.metodos_numericos.pares_cero);
  for (const campo of ['fuente_principal','fuente_sensibilidad']) { texto(valor.metodos_numericos[campo]); if (!valor.fuentes[valor.metodos_numericos[campo]]) throw new Error('Falta fuente numérica'); }
  objeto(valor.metodos_numericos.unidades); Object.values(valor.metodos_numericos.unidades).forEach(texto);
  const interpolacion=valor.metodos_numericos.interpolacion; objeto(interpolacion);
  claves(interpolacion,['coeficientes_x_ascendentes','intervalo_km','error_maximo_nodos_kmh']);
  for (const [campo,longitud] of [['coeficientes_x_ascendentes',3],['intervalo_km',2]] as const) {
    if (!Array.isArray(interpolacion[campo]) || interpolacion[campo].length !== longitud) throw new Error('Dimensión inválida');
    interpolacion[campo].forEach(numero);
  }
  const intervalo = interpolacion.intervalo_km as number[];
  if (intervalo[0]>=intervalo[1]) throw new Error('Intervalo inválido');
  numero(interpolacion.error_maximo_nodos_kmh);
  if (!Array.isArray(valor.documentacion) || !Array.isArray(valor.figuras)) throw new Error('Contenido ampliado requerido');
  const ids = new Set<string>();
  for (const bloque of valor.documentacion) {
    objeto(bloque); claves(bloque,['id','titulo','texto','fuentes']);
    texto(bloque.id); texto(bloque.titulo); texto(bloque.texto); lista_texto(bloque.fuentes);
    if (ids.has(bloque.id)) throw new Error('Documento duplicado'); ids.add(bloque.id);
    for (const fuente of bloque.fuentes) if (!valor.fuentes[fuente]) throw new Error('Fuente documental ausente');
  }
  const figuras_ids=new Set<string>();
  for (const figura of valor.figuras) {
    objeto(figura); claves(figura,['id','protocolo','modelo','regla','fuente','titulo','descripcion','url','ancho','alto']);
    for (const campo of ['id','protocolo','modelo','regla','fuente','titulo','descripcion','url']) texto(figura[campo]);
    const id=String(figura.id);
    if (figuras_ids.has(id)) throw new Error('Figura duplicada'); figuras_ids.add(id);
    if (!/^figuras\/[a-z0-9_]+\.png$/.test(String(figura.url)) || !valor.fuentes[String(figura.fuente)]) throw new Error('Figura no autorizada');
    if (![...Object.keys(protocolos),'numericos'].includes(String(figura.protocolo))) throw new Error('Protocolo de figura inválido');
    for (const campo of ['ancho','alto']) {numero(figura[campo]); if (!Number.isInteger(figura[campo]) || Number(figura[campo])<=0) throw new Error('Dimensión inválida');}
  }
  return valor as unknown as CatalogoResultados;
}
