"""Primera etapa: candidatos y etiquetas, sin leer target."""
from pathlib import Path
import hashlib, platform
import numpy as np
import pandas as pd
import sklearn,scipy
from threadpoolctl import threadpool_limits
from .datos import PreparadorDatos
from .experimentos import ExperimentoKMeans,ExperimentoJerarquico
from .exportacion import guardar_csv,guardar_json

def main():
    r=Path('fase04_clustering/resultados');r.mkdir()
    d=PreparadorDatos().cargar()
    with threadpool_limits(limits=2):
        km=ExperimentoKMeans(d.matriz);filas=km.ejecutar()
        h=ExperimentoJerarquico(d.matriz);filas+=h.ejecutar()
    guardar_csv(r/'candidatos.csv',pd.DataFrame(filas))
    datos={f'kmeans_{k}':v for k,v in km.etiquetas.items()}
    datos.update({f'{m}_{k}':v for (m,k),v in h.etiquetas.items()})
    datos.update({f'enlace_{m}':v for m,v in h.enlaces.items()});datos['indices_muestra']=h.indices
    with (r/'candidatos.npz').open('xb') as f:np.savez_compressed(f,**datos)
    guardar_json(r/'auditoria_interna.json',dict(train_sha256=hashlib.sha256(Path(d.origen).read_bytes()).hexdigest(),forma=list(d.matriz.shape),predictores=list(d.x.columns),columnas=d.preprocesador.get_feature_names_out().tolist(),identidad_matriz_historica=True,semilla=42,semillas_estabilidad=[42,43,44],n_init=10,max_iter=300,silhouette_muestra=2000,jerarquico_muestra=4000,usuarios_muestra=int(d.claves.iloc[h.indices]['User ID'].nunique()),contribuciones_distancia=[float(2*d.matriz[:,s].var(axis=0).sum()) for s in (slice(0,3),slice(3,4),slice(4,8),slice(8,None))],versiones=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,scipy=scipy.__version__)))

if __name__=='__main__':main()
