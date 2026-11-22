import { secciones } from '../presentacion/secciones.js';

export function escapar_html(texto: string): string {
  return texto.replace(/[&<>"']/g, caracter => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[caracter]!));
}

export function crear_estructura(): string {
  return `<a class="saltar_contenido" href="#contenido">Saltar al contenido</a>
    <header class="encabezado">
      <a class="marca" href="#contexto" aria-label="ATO, inicio"><span class="simbolo" aria-hidden="true">A</span><span>ATO<span class="marca_detalle">Minería de datos</span></span></a>
      <p class="encabezado_descripcion">Detección de Account Takeover</p>
      <span class="etiqueta_academica">Proyecto académico</span>
      <button class="boton_menu" type="button" aria-expanded="false" aria-controls="indice">Secciones</button>
    </header>
    <div class="estructura">
      <aside class="lateral" id="indice">
        <p class="titulo_indice">Explorar el proyecto</p>
        <nav aria-label="Secciones del proyecto">${secciones.map(seccion => `<a href="#${seccion.id}" data_seccion="${seccion.id}">${escapar_html(seccion.titulo)}</a>`).join('')}</nav>
        <div class="nota_indice"><span class="marca_nota" aria-hidden="true"></span><p>De la pregunta inicial<br>a los límites de la evidencia.</p></div>
        <p class="nota_presentacion">Apoyo interactivo para la sustentación. El PowerPoint es el instrumento central.</p>
      </aside>
      <div class="zona_contenido">
        <main id="contenido" tabindex="-1" aria-busy="true"><p role="status">Cargando el contenido académico…</p></main>
        <footer class="pie"><p>ATO · Proyecto académico de minería de datos<br><span>Resultados documentados. Sin inferencia en tiempo real.</span></p><a href="./recursos.html">CSV y presentación</a><a href="https://github.com/Javier-Gomez-Ovalle/Mineria_de_Datos" target="_blank" rel="noopener noreferrer">Repositorio en GitHub <span class="solo_lector">(abre otra pestaña)</span></a></footer>
      </div>
    </div>`;
}

export function crear_aviso(titulo: string, mensaje: string): string {
  return `<aside class="aviso"><strong>${escapar_html(titulo)}</strong><p>${escapar_html(mensaje)}</p></aside>`;
}
