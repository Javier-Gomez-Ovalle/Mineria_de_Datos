from pathlib import Path
import json
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from fase04_modelado.metricas import calcular_metricas,METRICAS
from fase04_modelado.auditoria import verificar_oof
from fase04_modelado.modelos import NOMBRES
from fase04_preparacion.seleccion import separar_datos

R=Path('fase04_modelado/resultados')


def test_resultados_oof_completos_y_metricas():
    d=pd.read_csv('dataset_train_fase04.csv');_,y,claves=separar_datos(d)
    o=pd.read_csv(R/'predicciones_oof.csv');c=pd.read_csv(R/'comparacion_modelos.csv').set_index('modelo');f=pd.read_csv(R/'metricas_por_fold.csv')
    verificar_oof(o,y,claves,NOMBRES)
    assert len(o)==46305*6 and len(f)==30
    for nombre in NOMBRES:
        a=o[o.modelo==nombre];m=calcular_metricas(a.y_true,a.score)
        for k in ['TP','FP','TN','FN',*METRICAS]:np.testing.assert_allclose(c.loc[nombre,k],m[k])
        for fold in range(1,6):
            b=a[a.fold==fold];r=f[(f.modelo==nombre)&(f.fold==fold)].iloc[0]
            for k,v in calcular_metricas(b.y_true,b.score).items():np.testing.assert_allclose(r[k],v)
        for k in METRICAS:
            np.testing.assert_allclose(c.loc[nombre,k+'_media_folds'],f[f.modelo==nombre][k].mean())
            np.testing.assert_allclose(c.loc[nombre,k+'_sd_folds'],f[f.modelo==nombre][k].std(ddof=1))


def test_todos_modelos_comparten_fold_y_grupos():
    o=pd.read_csv(R/'predicciones_oof.csv')
    assert o.groupby('evento_id').fold.nunique().eq(1).all()
    assert o.groupby('User ID').fold.nunique().eq(1).all()
    assert o.groupby('evento_id').y_true.nunique().eq(1).all()


def test_auditoria_treinta_ajustes_y_ros():
    a=json.loads((R/'configuracion_auditoria.json').read_text())
    assert a['test_leido'] is False
    assert len(a['auditoria_folds'])==30
    for x in a['auditoria_folds']:
        assert x['controles']=='OK'
        assert all('User ID' not in c and 'Is Account Takeover' not in c for c in x['columnas'])
        if x['modelo']=='knn_ros':assert x['remuestreo_indices_solo_subtrain'] is True
        if x['modelo']=='gnb_ponderado':assert x['pesos_clase']['1']>x['pesos_clase']['0']


def test_xlsx_numeros_contra_csv():
    ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(R/'comparacion_modelos.xlsx') as z:
        assert z.testzip() is None
        root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        cells={c.attrib['r']:c for c in root.findall('.//x:sheetData/x:row/x:c',ns)}
        c=pd.read_csv(R/'comparacion_modelos.csv')
        for i,row in c.iterrows():
            for letra,col in zip('CDEFGHIJ',['TP','FP','TN','FN','precision','recall','f1','average_precision']):
                cell=cells[f'{letra}{i+6}'];v=float(cell.find('x:v',ns).text)
                np.testing.assert_allclose(v,row[col],rtol=1e-12,atol=1e-15)
        assert len(ET.fromstring(z.read('xl/workbook.xml')).findall('x:sheets/x:sheet',ns))==4
