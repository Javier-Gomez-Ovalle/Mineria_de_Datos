import type { FuenteResultados } from './datos/repositorio_resultados.js';
import type { CatalogoResultados } from './datos/contratos.js';
import { crear_estructura } from './componentes/estructura.js';
import { resolver_seccion } from './presentacion/secciones.js';
import { renderizar_contexto, renderizar_error, renderizar_seccion } from './presentacion/vistas.js';
import { estado_inicial, actualizar_consulta } from './presentacion/consulta.js';
import { escapar_html } from './componentes/estructura.js';

export class AplicacionAcademica {
  private catalogo?: CatalogoResultados;
  private estado=estado_inicial();
  private origen_figura?:HTMLElement;
  constructor(private readonly raiz: HTMLElement, private readonly fuente: FuenteResultados) {}

  async iniciar(): Promise<void> {
    this.raiz.innerHTML=crear_estructura();
    this.raiz.insertAdjacentHTML('beforeend','<dialog class="visor_figura" aria-labelledby="titulo_figura"><button type="button" class="cerrar_visor">Cerrar figura</button><div id="contenido_figura"></div></dialog>');
    const visor=this.raiz.querySelector<HTMLDialogElement>('dialog')!;
    visor.querySelector('.cerrar_visor')!.addEventListener('click',()=>visor.close());
    visor.addEventListener('close',()=>this.origen_figura?.focus());
    const menu=this.raiz.querySelector<HTMLButtonElement>('.boton_menu')!;
    menu.addEventListener('click',()=>{
      const abierto=menu.getAttribute('aria-expanded')!=='true';
      menu.setAttribute('aria-expanded',String(abierto));
      this.raiz.querySelector('#indice')!.classList.toggle('abierto',abierto);
    });
    this.raiz.addEventListener('keydown',evento=>{
      if (evento.key==='Escape' && menu.getAttribute('aria-expanded')==='true') {
        this.cerrar_menu(); menu.focus();
      }
    });
    window.addEventListener('hashchange',()=>this.navegar(true));
    this.raiz.addEventListener('click',evento=>{
      const objetivo=evento.target as HTMLElement;
      const figura=objetivo.closest<HTMLElement>('[data-figura]');
      if(figura) {
        const dato=this.catalogo?.figuras.find(f=>f.id===figura.dataset.figura);
        if(dato) {
          this.origen_figura=figura;
          this.raiz.querySelector('#contenido_figura')!.innerHTML=`<h2 id="titulo_figura">${escapar_html(dato.titulo)}</h2><p>${escapar_html(dato.descripcion)}</p><img src="./${dato.url}" alt="${escapar_html(dato.titulo)}" width="${dato.ancho}" height="${dato.alto}"><a href="./${dato.url}" target="_blank" rel="noopener noreferrer">Abrir original en otra pestaña</a>`;
          visor.showModal();
        }
      }
      const enlace=objetivo.closest<HTMLAnchorElement>('a[data_seccion]');
      if (enlace && enlace.hash===window.location.hash) {this.cerrar_menu(); this.navegar(true);}
    });
    this.raiz.addEventListener('change',evento=>{
      const control=evento.target as HTMLSelectElement;
      if(!control.dataset.campo || !this.catalogo) return;
      this.estado=actualizar_consulta(this.estado,control.dataset.campo,control.value,this.catalogo);
      const id=control.id; this.navegar(false);
      this.raiz.querySelector<HTMLElement>('#'+id)?.focus({preventScroll:true});
    });
    this.raiz.addEventListener('error',evento=>{
      const imagen=evento.target;
      if(imagen instanceof HTMLImageElement) {
        imagen.hidden=true;
        const aviso=document.createElement('p'); aviso.className='error_figura'; aviso.setAttribute('role','status');
        aviso.textContent='No se pudo cargar esta figura histórica. La tabla y la referencia de origen siguen disponibles.';
        imagen.after(aviso);
      }
    },true);
    await this.cargar();
  }

  private cerrar_menu(): void {
    this.raiz.querySelector('.boton_menu')!.setAttribute('aria-expanded','false');
    this.raiz.querySelector('#indice')!.classList.remove('abierto');
  }

  private async cargar(): Promise<void> {
    const contenido=this.raiz.querySelector<HTMLElement>('#contenido')!;
    contenido.setAttribute('aria-busy','true');
    try {
      this.catalogo=await this.fuente.cargar_catalogo();
    } catch {
      contenido.innerHTML=renderizar_error();
      contenido.querySelector('#reintentar')!.addEventListener('click',()=>void this.cargar());
      return;
    } finally {contenido.setAttribute('aria-busy','false');}
    this.navegar(false);
  }

  private navegar(enfocar: boolean): void {
    if (!this.catalogo || (enfocar && window.location.hash==='#contenido')) return;
    const seccion=resolver_seccion(window.location.hash);
    const contenido=this.raiz.querySelector<HTMLElement>('#contenido')!;
    contenido.innerHTML=seccion.id==='contexto'?renderizar_contexto(this.catalogo):renderizar_seccion(seccion,this.catalogo,this.estado);
    this.raiz.querySelectorAll<HTMLAnchorElement>('[data_seccion]').forEach(enlace=>{
      if (enlace.getAttribute('data_seccion')===seccion.id) enlace.setAttribute('aria-current','page');
      else enlace.removeAttribute('aria-current');
    });
    document.title=seccion.titulo+' | ATO';
    this.cerrar_menu();
    if (enfocar) {
      contenido.querySelector<HTMLElement>('#titulo_seccion')!.focus({preventScroll:true});
      window.scrollTo({top:0,behavior:'instant'});
    }
  }
}
