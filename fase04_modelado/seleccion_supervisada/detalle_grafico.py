"""Vista adicional de FP sin el extremo trivial t=0; conserva vista completa."""
from .graficas import plt,COLORES,NOTA
from .auditoria import RAIZ,NOMBRES,activar_guardia
import pandas as pd

def main():
    activar_guardia();t=pd.read_csv(RAIZ/'resultados/umbrales_globales.csv',float_precision='round_trip')
    fig,axes=plt.subplots(3,2,figsize=(15,13),layout='constrained')
    for ax,(nombre,titulo) in zip(axes.flat,NOMBRES.items()):
        for j,protocolo in enumerate(['CV1','CV2']):
            q=t[t.modelo.eq(nombre)&t.protocolo.eq(protocolo)&t.umbral.gt(0)&t.umbral.le(1)].sort_values('umbral')
            ax.step(q.umbral,q.FP,where='pre',label=protocolo,color=COLORES[j]);ax.scatter(q.umbral,q.FP,s=20,color=COLORES[j])
            ref=q[q.umbral.eq(.4)].iloc[0];ax.text(.98,.88-j*.13,f'{protocolo} t=0,4: {int(ref.FP):,} FP',transform=ax.transAxes,ha='right',color=COLORES[j],fontsize=11)
        ax.set(title=titulo,xlabel='Umbral positivo t (score ≥ t)',ylabel='Eventos FP',xlim=(0,1));ax.set_ylim(bottom=0);ax.grid(alpha=.2);ax.legend(loc='lower left')
    fig.suptitle('Falsas alarmas · detalle para t>0 | Escala vertical propia por panel\n'+NOTA+'\nSe excluye solo t=0 (46.269 FP); las vistas completas se conservan.')
    for extension in ['png','svg']:
        ruta=RAIZ/'graficas'/f'08_detalle_fp_umbrales_positivos.{extension}'
        if ruta.exists():raise FileExistsError(ruta)
        fig.savefig(ruta,dpi=300,bbox_inches='tight')
    plt.close(fig)

if __name__=='__main__':main()
