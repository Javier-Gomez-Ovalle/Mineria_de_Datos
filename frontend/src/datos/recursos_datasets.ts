/** Publicación académica autorizada; no contiene observaciones individuales. */
const repositorio = 'https://huggingface.co/datasets/Sirius6661/ato-academico-fase04';
const revision = 'f58b487642da42fd591f4e37a1c558a0804812c8';

export interface RecursoDataset {
  titulo: string;
  url: string;
}

export const dataset_entrenamiento = {
  repositorio,
  revision,
  registros: 46305,
  usuarios: 1600,
  columnas: 35,
  eventos_ato: 36,
  visor: `${repositorio}/viewer/train_definitivo/train`,
  iframe: `${repositorio}/embed/viewer/train_definitivo/train`,
  csv: `${repositorio}/resolve/${revision}/data/train/dataset_train_fase04.csv?download=true`,
} as const;

export const recursos_dataset: readonly RecursoDataset[] = [
  {titulo: 'Documentación y archivos publicados', url: repositorio},
  {titulo: 'Diccionario de variables', url: `${repositorio}/blob/${revision}/docs/diccionario_variables.md`},
  {titulo: 'Procedencia de los datos', url: `${repositorio}/blob/${revision}/docs/procedencia.md`},
  {titulo: 'Licencias y condiciones de uso', url: `${repositorio}/blob/${revision}/LICENSES.md`},
  {titulo: 'Manifiesto de la publicación', url: `${repositorio}/resolve/${revision}/manifest.json`},
  {titulo: 'Hashes SHA-256 de los archivos', url: `${repositorio}/resolve/${revision}/SHA256SUMS`},
];
