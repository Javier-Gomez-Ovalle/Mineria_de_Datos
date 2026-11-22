"""Manifiesto final: hashes autorizados sin tocar archivos de test."""
from pathlib import Path
from .auditoria import RAIZ,RESULTADOS,activar_guardia,verificar_historicos,guardar_json,sha

def main():
    activar_guardia();n=verificar_historicos()
    archivos=[p for p in RAIZ.rglob('*') if p.is_file() and 'cache_graficas' not in p.parts]+[Path('INFORME_VALIDACION_ANIDADA_FASE04.md')]
    guardar_json(RESULTADOS/'manifiesto_entrega.json',dict(historicos_verificados=n,historicos_intactos=True,test_abierto=False,test_inspeccionado=False,test_hash_calculado=False,git_ejecutado=False,modelo_final_entrenado=False,experimento_ajustes=120,pruebas_ajustes_pequenos=12,sha256_entregables={p.as_posix():sha(p) for p in archivos}))
    print('Integridad histórica confirmada:',n,'archivos autorizados; test excluido')

if __name__=='__main__':main()
