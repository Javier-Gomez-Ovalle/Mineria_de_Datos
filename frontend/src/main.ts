import { RepositorioResultadosJson } from './datos/repositorio_resultados.js';
import { AplicacionAcademica } from './aplicacion.js';
import './estilos.css';
import './analiticas.css';

const raiz=document.querySelector<HTMLElement>('#aplicacion')!;
void new AplicacionAcademica(raiz,new RepositorioResultadosJson('./contenido/catalogo.json')).iniciar();
