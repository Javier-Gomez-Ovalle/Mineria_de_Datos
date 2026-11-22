"""Persistencia exclusiva, configuración y selección determinista."""
from pathlib import Path
from fractions import Fraction
import json
import numpy as np
import pandas as pd
from fase04_modelado.validacion_anidada.auditoria import sha, hash_indices, activar_guardia

BASE = Path('fase04_modelado/mejora_controlada')
OUT = BASE / 'resultados'
HIST = Path('fase04_modelado/validacion_anidada/resultados')
CONFIGS = [dict(max_depth=d, min_samples_leaf=l) for d in [8, None] for l in [1, 10]]

def json_nuevo(path, data):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)

def csv_nuevo(path, data):
    with Path(path).open('x', encoding='utf-8', newline='') as f:
        data.to_csv(f, index=False, float_format='%.17g')

def texto_nuevo(path, text):
    with Path(path).open('x', encoding='utf-8') as f: f.write(text)

def verificar_integridad():
    baseline = json.loads((BASE/'inventario_previo.json').read_text(encoding='utf-8'))
    for name, v in baseline.items():
        p=Path(name)
        assert p.stat().st_size==v['size'] and str(p.stat().st_mtime_ns)==v['mtime_ns'] and sha(p)==v['sha256'],name
    return len(baseline)

def seleccionar(y, score):
    """Mismos estados y desempates históricos, con conteo acumulado O(n log n)."""
    y=np.asarray(y, int);s=np.asarray(score, float)
    assert set(y)=={0,1} and len(y)==len(s) and np.isfinite(s).all() and ((s>=0)&(s<=1)).all()
    order=np.argsort(s, kind='stable');ss=s[order];yy=y[order]
    thresholds=np.unique(np.r_[ss,0.,.5,np.nextafter(1.,np.inf)])
    cuts=np.searchsorted(ss,thresholds,side='left')
    tp=int(y.sum())-np.r_[0,np.cumsum(yy)][cuts]
    fp=len(y)-cuts-tp;fn=int(y.sum())-tp;tn=len(y)-int(y.sum())-fp
    den=2*tp+fp+fn
    ratios=[Fraction(int(a),int(b)) for a,b in zip(2*tp,den)]
    best=max(ratios);tied=[i for i,v in enumerate(ratios) if v==best]
    chosen=min(tied,key=lambda i:(abs(thresholds[i]-.5),-thresholds[i]))
    table=pd.DataFrame(dict(umbral=thresholds,TP=tp,FP=fp,TN=tn,FN=fn,f1=2*tp/den))
    table['seleccionado']=np.arange(len(table))==chosen
    decision=dict(umbral=float(thresholds[chosen]),f1=float(best),numerador=best.numerator,denominador=best.denominator,empates=len(tied))
    return decision,table

def fraccion(d):return Fraction(d['numerador'],d['denominador'])

def verificar_particiones(parts, usuarios, n):
    coverage=np.zeros(n,int)
    for p in parts:
        a=np.asarray(p['ajuste']);b=np.asarray(p['validacion'])
        assert not set(usuarios.iloc[a])&set(usuarios.iloc[b])
        assert not set(a)&set(b) and set(a)|set(b)==set(range(n))
        coverage[b]+=1;inner={int(i):0 for i in a}
        for q in p['internas']:
            c=q['ajuste'];d=q['validacion']
            assert not set(usuarios.iloc[c])&set(usuarios.iloc[d])
            assert not set(c)&set(d) and set(c)|set(d)==set(a)
            for i in d:inner[i]+=1
        assert set(inner.values())=={1}
    assert (coverage==1).all()
