import type { CatalogoResultados, AjusteLineal } from '../datos/contratos.js';
import { crear_aviso, escapar_html as e } from '../componentes/estructura.js';
import { bloque, selector, tabla_resultados, tabla, matriz, galeria, formato, fuente } from '../componentes/evidencia.js';
import { consultar_resultados, modelos_disponibles, nombres_modelos, nombres_protocolos, type EstadoConsulta } from './consulta.js';

export function renderizar_metodologia(c:CatalogoResultados):string {
  const pasos=[['Comprensión del negocio','Caso hospitalario simulado y abuso de credenciales.'],['Comprensión de datos','Procedencia, desbalance y limitaciones geográficas.'],['Preparación','Asociación estable del target, limpieza y seis predictores.'],['Modelado','Comparaciones supervisadas y exploración no supervisada.'],['Evaluación','Protocolos separados y evaluación final documentada.'],['Despliegue académico','Aplicación local de consulta. Sin servicio predictivo productivo.']];
  return `<ol class="proceso">${pasos.map(([t,d])=>`<li><h2>${t}</h2><p>${d}</p></li>`).join('')}</ol>`+
    ['datos','preparacion','predictores'].map(id=>bloque(c,id)).join('')+
    `<h2 class="titulo_grupo">Protocolos que no deben mezclarse</h2>`+['cv1','cv2','anidada','extension_rf'].map(id=>bloque(c,id)).join('')+
    crear_aviso('Interpretar cada evidencia en su ámbito','OOF global concatena predicciones de folds diferentes; no es la media de sus métricas. La AP global puede mezclar escalas de scores de estimadores distintos. La selección OOF del umbral no estima rendimiento independiente.');
}

export function renderizar_supervisados(c:CatalogoResultados,s:EstadoConsulta):string {
  const opciones={todos:'Todos los procedimientos',...Object.fromEntries(modelos_disponibles(c,s.protocolo).map(m=>[m,nombres_modelos[m]??m]))};
  const usa_reglas=['anidada','extension_rf'].includes(s.protocolo);
  const filas=consultar_resultados(c,s);
  const figuras=c.figuras.filter(f=>f.protocolo===s.protocolo && (f.modelo==='todos'||s.modelo==='todos'||f.modelo===s.modelo) &&
    (f.regla==='todas'||f.regla===s.regla));
  const identidad=nombres_protocolos[s.protocolo]+(usa_reglas?' · '+(s.regla==='aprendido'?'regla aprendida internamente':'umbral fijo 0,5'):' · umbral 0,5');
  const modelos=s.modelo==='todos'?['arbol','gnb','knn',...(s.protocolo==='extension_rf'?['extension_rf']:[])]:[s.modelo.startsWith('arbol')?'arbol':s.modelo.startsWith('gnb')?'gnb':s.modelo.startsWith('knn')?'knn':s.modelo==='random_forest'?'extension_rf':'anidada'];
  return `<div class="controles" aria-label="Filtros de resultados">${selector('protocolo','Protocolo',nombres_protocolos,s.protocolo)}${selector('modelo','Modelo o variante',opciones,s.modelo)}${selector('ambito','Ámbito',{'oof_global':'OOF global','fold':'Resultados por fold'},s.ambito)}${usa_reglas?selector('regla','Regla de decisión',{'aprendido':'Aprendida internamente','fijo_05':'Fija a 0,5'},s.regla):''}</div>
    ${s.ambito==='fold'?`<div class="controles">${selector('fold','Fold de validación',{'todos':'Todos los folds','1':'Fold 1','2':'Fold 2','3':'Fold 3','4':'Fold 4','5':'Fold 5'},s.fold)}</div>`:''}
    <p class="seleccion_actual" role="status">${e(identidad)} · ${s.ambito==='fold'?(s.fold==='todos'?'Todos los folds':'Fold '+e(s.fold)):'Global'} · ${filas.length} filas</p>
    ${bloque(c,s.protocolo)}
    ${tabla_resultados(filas,identidad,s.ambito==='fold')}
    ${s.ambito==='oof_global' && ['cv1','cv2'].includes(s.protocolo)?`<details class="detalle_evidencia"><summary>Medias y desviaciones entre folds</summary>${tabla('Estadísticas históricas entre folds', [['modelo','Procedimiento'],...['precision','recall','f1','average_precision'].flatMap(m=>[[m+'_media_folds',m+' · media'],[m+'_sd_folds',m+' · DE']] as [string,string][])],filas.map(f=>f.valores))}</details>`:''}
    ${['cv1','cv2'].includes(s.protocolo)?`<details class="detalle_evidencia"><summary>Tiempos documentados (segundos)</summary>${tabla('Coste computacional histórico', [['modelo','Procedimiento'],...(s.ambito==='fold'?[['fold','Fold'] as [string,string]]:[]),['preprocesamiento_s','Preprocesamiento (s)'],['sobremuestreo_s','ROS (s)'],['entrenamiento_s','Entrenamiento (s)'],['prediccion_s','Predicción (s)']],filas.map(f=>f.valores))}<p>Los tiempos globales son los acumulados históricos; dependen del equipo. No se ejecuta ningún entrenamiento desde la aplicación.</p></details>`:''}
    <details class="detalle_evidencia"><summary>Configuración, funcionamiento e interpretación</summary>${[...new Set(modelos)].map(id=>bloque(c,id)).join('')}</details>
    <details class="procedencia"><summary>Fuentes de las filas mostradas</summary>${[...new Set(filas.map(f=>f.fuente))].map(f=>`<p>${fuente(f)}</p>`).join('')}</details>
    <h2 class="titulo_grupo">Evidencia visual histórica</h2><p>Las figuras identifican su propio ámbito. Cambiar a resultados por fold no convierte una matriz global en una matriz de un fold. Las figuras anidadas comparan ambas reglas explícitamente.</p>${galeria(figuras)}
    ${crear_aviso('Comparar sin forzar un ganador','Cambiar la distribución de folds cambia la evidencia, no el algoritmo. Un recall alto puede acompañarse de muchas falsas alarmas; AP mide ranking y no garantiza detecciones al umbral elegido.')}`;
}

export function renderizar_clustering(c:CatalogoResultados,s:EstadoConsulta):string {
  const candidatos=c.resultados.filter(f=>f.protocolo==='clustering' && f.ambito==='candidatos' && f.valores.algoritmo===s.agrupacion);
  const externos=c.resultados.filter(f=>f.ambito==='evaluacion_externa_'+s.agrupacion+'_2');
  const nombre={kmeans:'K-Means',ward:'Ward',average:'Average · contraste exploratorio'}[s.agrupacion]??s.agrupacion;
  return bloque(c,'clustering')+`<div class="controles">${selector('agrupacion','Procedimiento',{'kmeans':'K-Means','ward':'Ward · jerárquico principal','average':'Average · contraste exploratorio'},s.agrupacion)}</div>
    <p class="seleccion_actual" role="status">${e(nombre)} · índices internos, no clasificación</p>
    ${tabla('Candidatos históricos de '+nombre,[['k','K'],['silhouette','Silhouette'],['davies_bouldin','Davies–Bouldin'],['calinski_harabasz','Calinski–Harabasz'],['minimo','Grupo mínimo (eventos)'],['maximo','Grupo máximo (eventos)'],['ari_min','ARI mínimo'],['ari_media','ARI medio'],['segundos','Tiempo (s)']],candidatos.map(f=>f.valores))}
    <p>Silhouette y Calinski–Harabasz: mayor suele favorecer separación; Davies–Bouldin: menor. ARI mide acuerdo entre agrupaciones. No son tasas de detección de ataques. En jerárquico, el tiempo de enlace se repite por K: no debe sumarse como ajustes independientes.</p>
    ${externos.length?tabla('Descripción posterior al agrupamiento · K=2',[['cluster','Grupo'],['eventos','Eventos'],['eventos_ato','ATO'],['eventos_no_ato','No ATO'],['prevalencia','Prevalencia (0–1)'],['usuarios','Usuarios'],['usuarios_con_ato','Usuarios con ATO']],externos.map(f=>f.valores)):crear_aviso('Average se conserva como contraste','Su silhouette elevada no compensa por sí sola la segmentación extrema. No se le asignan métricas de clasificación ni se inventa una evaluación externa.')}
    ${galeria(c.figuras.filter(f=>f.protocolo==='clustering' && (f.modelo==='todos'||f.modelo===s.agrupacion)))}
    ${crear_aviso('Poblaciones diferentes','K-Means utiliza train completo y Ward una submuestra de 4.000 eventos. La descripción del target se realiza después de elegir los grupos; no demuestra separación predictiva de ATO.')}`;
}

export function renderizar_referencia(c:CatalogoResultados):string {
  const seleccion=c.resultados.filter(f=>f.protocolo==='seleccion_referencia');
  const final=c.resultados.filter(f=>f.protocolo==='evaluacion_final_documentada');
  const comparacion=c.resultados.filter(f=>f.protocolo==='extension_rf' && f.ambito==='oof_global' && f.valores.regla==='aprendido');
  return bloque(c,'referencia')+`<div class="referencia_destacada"><span>Procedimiento congelado</span><h2>Árbol de decisión ponderado</h2><p>Umbral: <strong>${e(String(seleccion[0]?.valores.umbral??'No informado'))}</strong><br>Regla: score de clase ATO ≥ umbral.</p><p>Gini, splitter=best, sin límite de profundidad, min_samples_split=2, min_samples_leaf=1, class_weight=balanced y random_state=42. El preprocesador final conserva 62 columnas transformadas.</p></div>
    <h2 class="titulo_grupo">Comparación histórica: extensión controlada</h2><p>Solo reglas aprendidas y OOF externas del mismo protocolo. Random Forest es una extensión, no un reemplazo de los cinco algoritmos principales.</p>
    ${tabla_resultados(comparacion,'Comparación OOF externa · reglas aprendidas')}
    <p>El árbol ponderado ofrece aquí un compromiso retrospectivo de F1 y falsas alarmas. GaussianNB prioriza recall con muchas alertas falsas; KNN y Random Forest muestran señales de ranking que no aseguran un mejor equilibrio. No se declara superioridad estadística.</p>
    <h2 class="titulo_grupo">Selección OOF del umbral</h2>${tabla_resultados(seleccion.map(f=>({...f,valores:{...f.valores,modelo:'arbol_ponderado'}})),'OOF utilizadas para seleccionar el umbral')}
    ${crear_aviso('No es una estimación independiente','Se maximizó F1 en OOF de tres estimadores; el ajuste final usa todo train. La transferencia de sus probabilidades y del umbral no está garantizada. No confundir el F1 de selección con rendimiento final.')}
    <h2 class="titulo_grupo">Evaluación final documentada</h2><p>Transcripción de la evaluación única ya cerrada. La aplicación no abre el dataset reservado ni sus predicciones.</p>
    ${tabla_resultados(final.map(f=>({...f,valores:{...f.valores,modelo:'arbol_ponderado'}})),'Evaluación final · evidencia agregada cerrada')}${final[0]?matriz(final[0],'Matriz final documentada'):''}
    ${bloque(c,'conclusiones')}${bloque(c,'extension_rf')}
    <details class="procedencia"><summary>Procedencia de selección y evaluación final</summary>${[...seleccion,...final].map(f=>`<p>${fuente(f.fuente)}</p>`).join('')}</details>
    <a class="enlace_principal" href="#supervisados">Consultar variantes, protocolos y folds</a>`;
}

function fila_regresion(nombre:string,a:AjusteLineal):Record<string,unknown>{return {ajuste:nombre,...a};}
export function renderizar_numericos(c:CatalogoResultados):string {
  const n=c.metodos_numericos; const a=n.regresion; const b=n.sensibilidad; const p=n.interpolacion;
  const coef=p.coeficientes_x_ascendentes;
  return bloque(c,'numericos')+`<h2 class="titulo_grupo">Regresión principal</h2><p>${formato(a.n)} pares válidos; ${formato(n.pares_cero)} pares en (0 km, 0 km/h). Todos se conservan en el ajuste principal.</p>
    <div class="ecuacion">ŷ = ${formato(a.pendiente,12)} x ${a.intercepto<0?'−':'+'} ${formato(Math.abs(a.intercepto),12)}<small>x: distancia (km) · ŷ: velocidad (km/h) · pendiente: h⁻¹ · intercepto: km/h</small></div>
    ${tabla('Principal frente a sensibilidad diagnóstica',[['ajuste','Ajuste'],['n','Pares'],['pendiente','Pendiente (h⁻¹)'],['intercepto','Intercepto (km/h)'],['correlacion','r'],['r2','R²'],['mse','MSE ((km/h)²)'],['rmse','RMSE (km/h)']],[fila_regresion('Principal',a),fila_regresion('Diagnóstico x > 0 km',b)])}
    <p>El ajuste de ${formato(b.n)} pares se presenta exclusivamente como sensibilidad. Sus errores corresponden a una población distinta; no debe interpretarse la diferencia de RMSE como una mejora o empeoramiento directamente comparable. La concentración en cero y los valores extremos condicionan la recta.</p>
    ${galeria(c.figuras.filter(f=>f.id==='numericos_regresion_lineal'))}
    <details class="detalle_evidencia"><summary>Sensibilidad diagnóstica y concentración en cero</summary>${galeria(c.figuras.filter(f=>f.id==='numericos_comparacion_ceros_extremos'))}</details>
    <h2 class="titulo_grupo">Interpolación de Lagrange</h2><div class="ecuacion">P(x) = ${formato(coef[0],12)} + ${formato(coef[1],12)} x − ${formato(Math.abs(coef[2]),15)} x²<small>P(x) en km/h; x en km. Coeficientes: km/h, h⁻¹ y km⁻¹ h⁻¹, respectivamente.</small></div>
    <p>Intervalo cerrado: [${formato(p.intervalo_km[0],12)}; ${formato(p.intervalo_km[1],12)}] km. Error máximo en nodos: ${e(p.error_maximo_nodos_kmh.toExponential(6))} km/h.</p>
    ${galeria(c.figuras.filter(f=>f.id==='numericos_interpolacion_lagrange'))}
    ${crear_aviso('Interpolación, no modelo predictivo general','Los tres nodos históricos fijan un polinomio de grado dos. Reproducirlos no valida su comportamiento fuera del intervalo ni demuestra causalidad. No se ofrece extrapolación ni se recalcula el ajuste.')}
    <details class="procedencia"><summary>Fuentes numéricas</summary><p>${fuente(n.fuente_principal)}</p><p>${fuente(n.fuente_sensibilidad)}</p></details>`;
}
