import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { validar_catalogo } from '../.tests/datos/contratos.js';
import { RepositorioResultadosJson } from '../.tests/datos/repositorio_resultados.js';
const catalogo = JSON.parse(await readFile(new URL('../public/contenido/catalogo.json', import.meta.url), 'utf8'));
test('Catálogo real satisface contrato', () => assert.equal(validar_catalogo(catalogo), catalogo));
for (const [nombre,mutar] of [
  ['versión',c=>c.version_esquema=2],
  ['observación individual',c=>c.resultados[0].valores.user_id='privado'],
  ['NaN',c=>c.resultados[0].valores.f1=NaN],
  ['escala',c=>c.resultados[0].valores.recall=99],
  ['protocolo mezclado',c=>c.resultados[0].ambito='test_documentado'],
  ['métrica faltante',c=>delete c.resultados[0].valores.tp],
  ['duplicado',c=>c.resultados.push(c.resultados[0])],
  ['intervalo',c=>c.metodos_numericos.interpolacion.intervalo_km=[5,1]],
  ['objetivo omitido',c=>c.narrativa.objetivos_especificos.pop()],
]) test('Rechaza '+nombre,()=>{const c=structuredClone(catalogo);mutar(c);assert.throws(()=>validar_catalogo(c));});
test('Fuente JSON admite lector inyectado',async()=>{
  const fuente=new RepositorioResultadosJson('memoria',async()=>new Response(JSON.stringify(catalogo)));
  assert.deepEqual(await fuente.cargar_catalogo(),catalogo);
});
test('Fuente propaga error HTTP y contrato',async()=>{
  await assert.rejects(new RepositorioResultadosJson('memoria',async()=>new Response('',{status:404})).cargar_catalogo());
  await assert.rejects(new RepositorioResultadosJson('memoria',async()=>new Response('{}')).cargar_catalogo());
});
