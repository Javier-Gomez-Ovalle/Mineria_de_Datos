import type { CatalogoResultados } from '../datos/contratos.js';
import { crear_aviso, escapar_html } from '../componentes/estructura.js';
import { secciones, type SeccionAcademica } from './secciones.js';
import type { EstadoConsulta } from './consulta.js';
import { estado_inicial } from './consulta.js';
import { renderizar_metodologia, renderizar_supervisados, renderizar_clustering, renderizar_referencia, renderizar_numericos } from './analiticas.js';

export function renderizar_contexto(catalogo: CatalogoResultados): string {
  return `<div class="ruta">Proyecto / Contexto</div>
    <section class="introduccion" aria-labelledby="titulo_seccion">
      <div><p class="etiqueta_seccion">Autenticación y suplantación de identidad</p>
      <h1 id="titulo_seccion" tabindex="-1">Una credencial válida.<br>¿La persona correcta?</h1>
      <p class="entradilla">Un proyecto académico sobre detección de Account Takeover: del comportamiento de inicio de sesión a una lectura crítica de los resultados.</p>
      <a class="enlace_principal" href="#metodologia">Explorar la metodología</a></div>
      <div class="panel_pregunta"><span class="icono_acceso" aria-hidden="true">↳</span><h2>El problema de fondo</h2><p>¿Cómo distinguir un acceso legítimo de un intento de suplantación cuando se utilizan credenciales válidas?</p><div class="contexto_caso">Contexto hospitalario simulado</div></div>
    </section>
    <section class="contexto_detalle" aria-labelledby="titulo_contexto"><div><h2 id="titulo_contexto">Detectar sin perder de vista<br>las falsas alarmas.</h2><p>La actividad inusual no siempre es un ataque. Este estudio plantea el problema en un entorno hospitalario simulado, donde los turnos y la actividad continua exigen interpretar el contexto de cada acceso.</p></div><div class="alcance"><h3>Alcance académico</h3><p>${escapar_html(catalogo.narrativa.alcance)}</p><p>La aplicación ayuda a recorrer la metodología y sus evidencias. No es un detector operativo.</p></div></section>
    <section class="objetivos" aria-labelledby="titulo_objetivo"><h2 id="titulo_objetivo">La pregunta se convierte en un objetivo</h2><blockquote>${escapar_html(catalogo.narrativa.objetivo_general)}</blockquote><details><summary>Consultar los objetivos específicos originales</summary><ol>${catalogo.narrativa.objetivos_especificos.map(objetivo=>`<li>${escapar_html(objetivo)}</li>`).join('')}</ol><p class="fuente">Fuente: ${escapar_html(catalogo.narrativa.fuente)}, página ${catalogo.narrativa.pagina}. Formulación original: expresa propósitos, no garantías de resultados alcanzados.</p></details></section>
    ${crear_aviso('Una lectura guiada de la evidencia','Consulta la metodología, compara los procedimientos dentro de cada protocolo y explora sus limitaciones. El PowerPoint mantiene el hilo de la sustentación; esta aplicación amplía la evidencia.')}`;
}

export function renderizar_seccion(seccion: SeccionAcademica, catalogo?:CatalogoResultados, estado:EstadoConsulta=estado_inicial()): string {
  const indice=secciones.indexOf(seccion);
  const anterior=secciones[indice-1];
  const siguiente=secciones[indice+1];
  const vistas: Record<string,()=>string> = {
    metodologia:()=>renderizar_metodologia(catalogo!),supervisados:()=>renderizar_supervisados(catalogo!,estado),
    clustering:()=>renderizar_clustering(catalogo!,estado),comparacion:()=>renderizar_referencia(catalogo!),metodos_numericos:()=>renderizar_numericos(catalogo!),
  };
  const analitica=catalogo && vistas[seccion.id];
  return `<div class="ruta">Proyecto / ${escapar_html(seccion.titulo)}</div>
    <section class="cabecera_seccion"><p class="etiqueta_seccion">${escapar_html(seccion.alcance)}</p><h1 id="titulo_seccion" tabindex="-1">${escapar_html(seccion.titulo)}</h1><p class="entradilla">${escapar_html(seccion.descripcion)}</p></section>
    ${analitica?analitica():crear_aviso('Contenido analítico pendiente','Esta sección está preparada para ampliar la sustentación. Aún no se muestran gráficas, tablas de métricas ni análisis completos.')}
    <nav class="navegacion_recorrido" aria-label="Continuar el recorrido">${anterior?`<a href="#${anterior.id}"><span>Anterior</span>${escapar_html(anterior.titulo)}</a>`:''}${siguiente?`<a href="#${siguiente.id}"><span>Siguiente</span>${escapar_html(siguiente.titulo)}</a>`:'<a href="#contexto"><span>Volver al inicio</span>Contexto del proyecto</a>'}</nav>`;
}

export function renderizar_error(): string {
  return `<h1 id="titulo_seccion" tabindex="-1">El contenido no está disponible</h1><p role="alert">No se pudo cargar o validar la fuente de resultados. Comprueba la conexión y vuelve a intentarlo.</p><button class="enlace_principal" id="reintentar" type="button">Reintentar carga</button>`;
}
