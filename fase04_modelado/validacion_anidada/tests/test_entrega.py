"""Configuración congelada, referencia histórica y gráficos reales."""
import json
from pathlib import Path
from PIL import Image
from fase04_modelado.validacion_anidada.auditoria import RESULTADOS
from fase04_modelado.modelos import crear_modelo

def test_configuracion_y_referencia_historica():
    c=json.loads((RESULTADOS/'configuracion_congelada.json').read_text(encoding='utf-8'));assert (c['externos'],c['internos'],c['semilla'])==(5,3,42)
    assert not c['calibracion'] and not c['optimizacion_hiperparametros']
    audits=json.loads((RESULTADOS/'auditoria_ajustes.json').read_text());assert sum(a['nivel']=='interno' for a in audits)==90 and sum(a['nivel']=='externo' for a in audits)==30
    for a in audits:assert a['parametros']==crear_modelo(a['modelo'])[1].get_params()
    referencias=json.loads((RESULTADOS/'comparacion_referencia_cv2.json').read_text());assert len(referencias)==6 and all(v['referencia_cv2_coincide'] for v in referencias)

def test_graficas_png_svg():
    catalogo=json.loads((RESULTADOS/'catalogo_graficas.json').read_text(encoding='utf-8'));assert len(catalogo)==13
    for g in catalogo:
        with Image.open(g['png']) as im:assert min(im.info['dpi'])>=299 and min(im.size)>1000
        assert '<svg' in Path(g['svg']).read_text(encoding='utf-8')
    assert sum('confusion' in g['nombre'] for g in catalogo)==7
