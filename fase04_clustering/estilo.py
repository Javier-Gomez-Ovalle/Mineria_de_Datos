"""Estilo compartido y exportación académica PNG 300 DPI/SVG."""
import os
from pathlib import Path
os.environ['MPLCONFIGDIR']=str(Path('fase04_clustering/cache_graficas').resolve())
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

COLORES=['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,'figure.titlesize':16,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})

def guardar(fig,carpeta,nombre):
    carpeta=Path(carpeta);carpeta.mkdir(parents=True,exist_ok=True)
    for extension in ('png','svg'):
        ruta=carpeta/f'{nombre}.{extension}'
        if ruta.exists():raise FileExistsError(ruta)
        fig.savefig(ruta,dpi=300,bbox_inches='tight')
    plt.close(fig)
