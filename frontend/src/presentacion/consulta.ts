import type { CatalogoResultados, ResultadoAgregado } from '../datos/contratos.js';

export const nombres_modelos: Record<string,string> = {
  arbol_baseline:'Árbol baseline', arbol_ponderado:'Árbol ponderado', gnb_baseline:'GaussianNB baseline',
  gnb_ponderado:'GaussianNB ponderado', knn_baseline:'KNN baseline',knn_ros:'KNN + Random Oversampling',
  random_forest:'Random Forest',selector_conjunto:'Selector conjunto',selector_historico:'Selector histórico',selector_ampliado:'Selector ampliado',
};
export const nombres_protocolos: Record<string,string> = {
  cv1:'CV1 · grupos, estratificación por evento',cv2:'CV2 · estratificación por usuario',
  anidada:'Validación anidada 5 × 3',extension_rf:'Extensión controlada con Random Forest',
};
export interface EstadoConsulta {protocolo:string; modelo:string; regla:string; ambito:string; agrupacion:string; fold:string}
export function estado_inicial(): EstadoConsulta {return {protocolo:'cv2',modelo:'todos',regla:'aprendido',ambito:'oof_global',agrupacion:'kmeans',fold:'todos'};}
export function consultar_resultados(catalogo:CatalogoResultados, estado:EstadoConsulta): ResultadoAgregado[] {
  return catalogo.resultados.filter(fila=>fila.protocolo===estado.protocolo && fila.ambito===estado.ambito &&
    (estado.modelo==='todos'||fila.valores.modelo===estado.modelo) &&
    (!fila.valores.regla||fila.valores.regla===estado.regla) &&
    (estado.ambito!=='fold'||estado.fold==='todos'||String(fila.valores.fold??fila.valores.fold_externo)===estado.fold));
}
export function modelos_disponibles(catalogo:CatalogoResultados, protocolo:string): string[] {
  return [...new Set(catalogo.resultados.filter(f=>f.protocolo===protocolo && f.ambito==='oof_global').map(f=>String(f.valores.modelo)))];
}
export function actualizar_consulta(estado:EstadoConsulta, campo:string, valor:string, catalogo:CatalogoResultados): EstadoConsulta {
  const nuevo={...estado};
  if(campo==='protocolo' && Object.hasOwn(nombres_protocolos,valor)) {
    nuevo.protocolo=valor;
    if(!modelos_disponibles(catalogo,valor).includes(nuevo.modelo)) nuevo.modelo='todos';
  }
  if(campo==='modelo' && (valor==='todos'||modelos_disponibles(catalogo,nuevo.protocolo).includes(valor))) nuevo.modelo=valor;
  if(campo==='regla' && ['aprendido','fijo_05'].includes(valor)) nuevo.regla=valor;
  if(campo==='ambito' && ['oof_global','fold'].includes(valor)) nuevo.ambito=valor;
  if(campo==='fold' && ['todos','1','2','3','4','5'].includes(valor)) nuevo.fold=valor;
  if(campo==='agrupacion' && ['kmeans','ward','average'].includes(valor)) nuevo.agrupacion=valor;
  return nuevo;
}
