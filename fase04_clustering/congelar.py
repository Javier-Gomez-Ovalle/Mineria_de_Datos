"""Congelación explícita anterior al acceso al target."""
from pathlib import Path
import hashlib
import numpy as np
from .exportacion import guardar_json,guardar_csv
from .datos import PreparadorDatos

def main():
    r=Path('fase04_clustering/resultados');a=np.load(r/'candidatos.npz');d=PreparadorDatos().cargar()
    seleccion={}
    for nombre in ('kmeans_2','ward_2'):
        indices=np.arange(len(d.x)) if nombre.startswith('kmeans') else a['indices_muestra']
        tabla=d.claves.iloc[indices].copy();tabla.insert(0,'evento_id',indices);tabla['cluster']=a[nombre]
        ruta=r/f'etiquetas_{nombre}.csv';guardar_csv(ruta,tabla)
        seleccion[nombre]=dict(k=2,sha256=hashlib.sha256(ruta.read_bytes()).hexdigest())
    guardar_json(r/'seleccion_congelada.json',dict(seleccion=seleccion,target_consultado=False,justificacion='KMeans K=2: silhouette 0.606, DB mínimo y CH máximo del rango, ARI=1 entre semillas, grupos 41296/5009 y perfiles de fallos/intervalos interpretables. Codo gradual: no prueba un K verdadero. Ward K=2: mejores tres índices dentro de Ward, grupos 3534/466. Average K=2 se descarta como representación principal pese a silhouette 0.785 por división 3983/17 (0.425% en grupo menor). K=7/8 KMeans es menos estable. Selección descriptiva parsimoniosa, no óptimo universal.',corte_ward=float(a['enlace_ward'][-2:,2].mean())))

if __name__=='__main__':main()
