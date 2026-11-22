import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {secciones} from '../.tests/presentacion/secciones.js';
import {renderizar_contexto,renderizar_seccion,renderizar_error} from '../.tests/presentacion/vistas.js';
import {estado_inicial,actualizar_consulta,consultar_resultados,modelos_disponibles,nombres_protocolos} from '../.tests/presentacion/consulta.js';
import {tabla_resultados,vacio,formato} from '../.tests/componentes/evidencia.js';
import {validar_catalogo} from '../.tests/datos/contratos.js';
const c=validar_catalogo(JSON.parse(await readFile(new URL('../public/contenido/catalogo.json',import.meta.url),'utf8')));

test('Las seis vistas completas se renderizan sin estados de error o pendiente',()=>{
  for(const s of secciones){
    const html=s.id==='contexto'?renderizar_contexto(c):renderizar_seccion(s,c);
    assert.match(html,/id="titulo_seccion"/);
    assert.doesNotMatch(html,/Contenido analítico pendiente|id="reintentar"|undefined|NaN/);
    assert.ok(html.length>2000);
  }
});
test('Filtros: cada protocolo, modelo, regla y fold coincide con las filas originales del catálogo',()=>{
  for(const protocolo of Object.keys(nombres_protocolos)){
    for(const modelo of ['todos',...modelos_disponibles(c,protocolo)]){
      for(const regla of ['aprendido','fijo_05']) for(const ambito of ['oof_global','fold']) for(const fold of ['todos','1','2','3','4','5']){
        const estado={...estado_inicial(),protocolo,modelo,regla,ambito,fold};
        const esperado=c.resultados.filter(f=>f.protocolo===protocolo&&f.ambito===ambito&&
          (modelo==='todos'||f.valores.modelo===modelo)&&(!f.valores.regla||f.valores.regla===regla)&&
          (ambito!=='fold'||fold==='todos'||String(f.valores.fold??f.valores.fold_externo)===fold));
        const actual=consultar_resultados(c,estado);
        assert.deepEqual(actual,esperado);
        assert.ok(actual.length>0,JSON.stringify(estado));
        if(ambito==='fold'&&fold!=='todos'&&modelo!=='todos') assert.equal(actual.length,1);
      }
    }
  }
});
test('Cambio de protocolo elimina modelo incompatible y rechaza filtros inválidos',()=>{
  let estado={...estado_inicial(),protocolo:'extension_rf',modelo:'random_forest'};
  estado=actualizar_consulta(estado,'protocolo','cv1',c);
  assert.equal(estado.modelo,'todos');
  assert.deepEqual(actualizar_consulta(estado,'protocolo','__proto__',c),estado);
  assert.deepEqual(actualizar_consulta(estado,'fold','6',c),estado);
  assert.equal(actualizar_consulta(estado,'fold','3',c).fold,'3');
});
test('Tablas preservan conteos y métricas; ausencia AP no se convierte en cero',()=>{
  for(const fila of c.resultados.filter(f=>f.protocolo!=='clustering')){
    const html=tabla_resultados([fila],'Verificación',fila.ambito==='fold');
    for(const k of ['tp','fp','tn','fn','precision','recall','f1','average_precision']) {
      assert.ok(html.includes('title="'+String(fila.valores[k]??'No informada')+'"'));
      assert.ok(html.includes(formato(fila.valores[k])));
    }
  }
});
test('Todas las figuras son alcanzables en su protocolo y etiquetadas con su ámbito',()=>{
  const htmls=[];
  for(const protocolo of Object.keys(nombres_protocolos)) for(const regla of ['aprendido','fijo_05']) {
    const html=renderizar_seccion(secciones[2],c,{...estado_inicial(),protocolo,regla});htmls.push(html);
    for(const id of html.matchAll(/data-figura="([^"]+)"/g)) {
      const figura=c.figuras.find(f=>f.id===id[1]);
      assert.equal(figura.protocolo,protocolo);
      assert.ok(figura.regla==='todas'||figura.regla===regla);
    }
  }
  for(const agrupacion of ['kmeans','ward','average']) htmls.push(renderizar_seccion(secciones[3],c,{...estado_inicial(),agrupacion}));
  htmls.push(renderizar_seccion(secciones[5],c));
  for(const f of c.figuras) assert.ok(htmls.some(h=>h.includes('data-figura="'+f.id+'"')),f.id);
});
test('Controles fold y estados vacíos son distintos de un fallo de carga',()=>{
  const html=renderizar_seccion(secciones[2],c,{...estado_inicial(),ambito:'fold',fold:'3'});
  assert.match(html,/data-campo="fold"/);assert.match(html,/Fold 3/);
  assert.doesNotMatch(vacio('Sin filas'),/role="alert"|reintentar/);
  assert.match(renderizar_error(),/role="alert"/);assert.match(renderizar_error(),/id="reintentar"/);
});
test('Métodos numéricos preservan unidades e independencia del diagnóstico',()=>{
  const html=renderizar_seccion(secciones[5],c);
  for(const t of ['km/h','km','h⁻¹','(km/h)²','sensibilidad','Intervalo cerrado','sin capacidad predictiva general']) assert.ok(html.includes(t),t);
  assert.match(html,/5[.,]662/);assert.match(html,/29/);
  assert.ok(c.metodos_numericos.regresion.n!==c.metodos_numericos.sensibilidad.n);
});
