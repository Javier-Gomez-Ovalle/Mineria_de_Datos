export interface SeccionAcademica {
  id: string;
  titulo: string;
  descripcion: string;
  alcance: string;
  temas: string[];
}

export const secciones: readonly SeccionAcademica[] = [
  {id:'contexto', titulo:'Contexto del proyecto', descripcion:'Comprender el problema antes de interpretar los resultados.',
    alcance:'Introducción', temas:[]},
  {id:'metodologia', titulo:'Metodología', descripcion:'Del problema de negocio a una evaluación documentada y reproducible.',
    alcance:'Proceso CRISP-DM', temas:['Comprensión del problema y de los datos','Preparación y selección de características','Protocolos de validación separados por usuario']},
  {id:'supervisados', titulo:'Modelos supervisados', descripcion:'Distintas formas de aprender a distinguir eventos de autenticación.',
    alcance:'Árbol de decisión, GaussianNB y KNN', temas:['Baseline y variantes experimentales','Métricas globales y resultados por fold','Resultados desfavorables y límites de interpretación']},
  {id:'clustering', titulo:'Clustering', descripcion:'Explorar la estructura de los datos sin convertir los grupos en etiquetas de ataque.',
    alcance:'K-Means y clustering jerárquico', temas:['K-Means: segmentación por centroides','Ward: estructura jerárquica; Average como contraste exploratorio','Índices internos y perfiles de los grupos']},
  {id:'comparacion', titulo:'Modelo de referencia', descripcion:'Comprender la selección del árbol ponderado y los límites de sus resultados.',
    alcance:'Comparación y evaluación documentada', temas:['Alternativas y extensión con Random Forest','Selección del umbral y evaluación independiente: evidencias distintas','Resultados y limitaciones; sin garantía de utilidad productiva']},
  {id:'metodos_numericos', titulo:'Métodos numéricos', descripcion:'Dos ejercicios complementarios para describir relaciones y explorar interpolación.',
    alcance:'Regresión lineal e interpolación de Lagrange', temas:['Regresión principal y sensibilidad diagnóstica separadas','Interpolación dentro del intervalo seleccionado','Unidades explícitas, sin causalidad ni extrapolación']},
];

export function resolver_seccion(fragmento: string): SeccionAcademica {
  const id = fragmento.replace(/^#/, '');
  return secciones.find(seccion => seccion.id === id) ?? secciones[0];
}
