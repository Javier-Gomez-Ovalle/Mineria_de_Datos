"""Análisis exploratorio global, por fold y por evento; nunca entrena."""
import numpy as np
import pandas as pd
from .auditoria import RAIZ,AuditorResultados,activar_guardia,guardar_csv,guardar_json,NOMBRES
from .umbrales import calcular,rejilla,frontera

def main():
    activar_guardia();a=AuditorResultados().verificar();r=RAIZ/'resultados';r.mkdir()
    guardar_json(r/'auditoria_fuentes.json',dict(hashes=a.hashes,protocolos=2,variantes=6,eventos_por_variante=46305,usuarios=1600,positivos=36,usuarios_positivos=34,correspondencia=True,metricas_globales_y_folds=True,usuarios_disjuntos=True,test_leido=False))
    globales=[];folds=[];distribuciones=[];errores=[];usuarios=[];historicos=[];historicos_fold=[];dist_fold=[]
    for protocolo,(o,c,f,d) in a.fuentes.items():
        historicos.append(c.assign(protocolo=protocolo));historicos_fold.append(f.assign(protocolo=protocolo));dist_fold.append(d.assign(protocolo=protocolo))
        for nombre,g in o.groupby('modelo',sort=False):
            # Misma rejilla por variante en CV1 y CV2: permite comparar decisiones idénticas.
            scores=np.concatenate([v[0].loc[v[0].modelo.eq(nombre),'score'].to_numpy() for v in a.fuentes.values()]);umbrales=rejilla(scores)
            for umbral in umbrales:
                globales.append(dict(protocolo=protocolo,modelo=nombre,**calcular(g.y_true,g.score,umbral)))
                for fold,q in g.groupby('fold'):folds.append(dict(protocolo=protocolo,modelo=nombre,fold=fold,**calcular(q.y_true,q.score,umbral)))
                # Errores identificables en las referencias comunes, sin copias de X.
                if umbral in [.2,.4,.5]:
                    pred=(g.score>=umbral).astype(int);e=g.loc[pred.ne(g.y_true)].copy();e['tipo_error']=np.where(e.y_true.eq(1),'FN','FP');e['umbral']=umbral;e['protocolo']=protocolo;e['y_pred']=pred.loc[e.index];errores.append(e)
                    aciertos=g.loc[g.y_true.eq(1)&pred.eq(1),'User ID'].nunique();fp_usuarios=g.loc[g.y_true.eq(0)&pred.eq(1),'User ID'].nunique()
                    usuarios.append(dict(protocolo=protocolo,modelo=nombre,umbral=umbral,usuarios_ato_detectados=aciertos,usuarios_con_fp=fp_usuarios))
            for score,q in g.groupby('score'):
                distribuciones.append(dict(protocolo=protocolo,modelo=nombre,score=score,eventos=len(q),eventos_ato=int(q.y_true.sum()),eventos_no_ato=int((1-q.y_true).sum())))
    glob=pd.DataFrame(globales);porfold=pd.DataFrame(folds)
    glob['pareto_dentro_variante']=False;glob['pareto_entre_variantes']=False
    for _,t in glob.groupby(['protocolo','modelo']):glob.loc[t.index,'pareto_dentro_variante']=frontera(t)
    for _,t in glob.groupby('protocolo'):glob.loc[t.index,'pareto_entre_variantes']=frontera(t)
    resumen=porfold.groupby(['protocolo','modelo','umbral'])[['precision','recall','f1','average_precision','TP','FP','FN']].agg(['mean','std','min','max']);resumen.columns=['_'.join(c) for c in resumen.columns]
    for nombre,t in [('umbrales_globales',glob),('umbrales_por_fold',porfold),('resumen_folds',resumen.reset_index()),('distribucion_scores',pd.DataFrame(distribuciones)),('errores_eventos_referencias',pd.concat(errores)),('errores_usuarios_referencias',pd.DataFrame(usuarios)),('historicos_globales',pd.concat(historicos)),('historicos_por_fold',pd.concat(historicos_fold)),('distribucion_folds',pd.concat(dist_fold))]:guardar_csv(r/f'{nombre}.csv',t)
    # Comparar cada evento entre protocolos sin confundirlos ni tratarlos como réplicas independientes.
    cambios=[]
    for nombre in NOMBRES:
        uno=a.fuentes['CV1'][0].query('modelo==@nombre').sort_values('evento_id');dos=a.fuentes['CV2'][0].query('modelo==@nombre').sort_values('evento_id')
        for umbral in [.2,.4,.5]:
            p=uno.score.to_numpy()>=umbral;q=dos.score.to_numpy()>=umbral;y=uno.y_true.to_numpy()
            cambios.append(dict(modelo=nombre,umbral=umbral,ato_detectados_ambos=int(((y==1)&p&q).sum()),ato_solo_cv1=int(((y==1)&p&~q).sum()),ato_solo_cv2=int(((y==1)&~p&q).sum()),ato_omitidos_ambos=int(((y==1)&~p&~q).sum()),decisiones_distintas=int((p!=q).sum())))
    guardar_csv(r/'concordancia_protocolos.csv',pd.DataFrame(cambios))
    print(glob[glob.modelo.eq('knn_baseline')&glob.umbral.isin([.2,.4,.5])].to_string(index=False))

if __name__=='__main__':main()
