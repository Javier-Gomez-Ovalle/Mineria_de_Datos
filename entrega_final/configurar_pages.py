"""Configura Pages usando credenciales de Git solo en memoria; nunca las imprime."""
import json
import subprocess
import urllib.request
import urllib.error

REPO='Javier-Gomez-Ovalle/Mineria_de_Datos'


def api(metodo,ruta,datos=None):
    p=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,check=True)
    cred=dict(l.split('=',1) for l in p.stdout.splitlines() if '=' in l)
    solicitud=urllib.request.Request('https://api.github.com/repos/'+REPO+ruta,
        data=json.dumps(datos).encode() if datos is not None else None,method=metodo,
        headers={'Authorization':'Bearer '+cred['password'],'Accept':'application/vnd.github+json','User-Agent':'ATO-entrega','Content-Type':'application/json'})
    with urllib.request.urlopen(solicitud,timeout=30) as r:
        contenido=r.read()
        return json.loads(contenido) if contenido else {}


if __name__=='__main__':
    try:
        estado=api('GET','/pages')
        assert estado['source']=={'branch':'gh-pages','path':'/'},'Pages ya existe con otra fuente: no se cambia silenciosamente'
    except urllib.error.HTTPError as error:
        if error.code!=404: raise
        estado=api('POST','/pages',{'source':{'branch':'gh-pages','path':'/'},'build_type':'legacy'})
    print(json.dumps({k:estado.get(k) for k in ['html_url','status','build_type','source']},indent=2))
