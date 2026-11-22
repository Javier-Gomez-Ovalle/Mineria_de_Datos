import { validar_catalogo, type CatalogoResultados } from './contratos.js';

export interface FuenteResultados {
  cargar_catalogo(): Promise<CatalogoResultados>;
}

export class RepositorioResultadosJson implements FuenteResultados {
  // El fetch nativo debe invocarse sobre globalThis, no como método del repositorio.
  constructor(private readonly url: string, private readonly leer: typeof fetch = (...argumentos) => globalThis.fetch(...argumentos)) {}
  async cargar_catalogo(): Promise<CatalogoResultados> {
    const respuesta = await this.leer(this.url);
    if (!respuesta.ok) throw new Error(`Carga fallida: ${respuesta.status}`);
    return validar_catalogo(await respuesta.json());
  }
}
